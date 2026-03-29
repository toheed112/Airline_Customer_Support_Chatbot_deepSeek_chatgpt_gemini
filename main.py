# main.py - Updated for JSON database system
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ==================== CONFIGURE LOGGING (Windows-safe) ====================
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chatbot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point with JSON database setup."""
    
    logger.info("=" * 60)
    logger.info("Swiss Airlines Chatbot - JSON System Startup")
    logger.info("=" * 60)
    
    # Load environment
    load_dotenv()
    logger.info("[1/5] Environment variables loaded")
    
    # Check/create JSON database
    json_path = PROJECT_ROOT / "data" / "db_dump.json"
    if not json_path.exists():
        logger.warning("[2/5] JSON database not found - creating...")
        try:
            from backend.database.populate_json_db import create_enhanced_json_database
            create_enhanced_json_database()
            logger.info("[2/5] ✅ JSON database created successfully")
        except Exception as e:
            logger.error(f"[2/5] ❌ Failed to create JSON database: {e}")
            return 1
    else:
        logger.info(f"[2/5] ✅ JSON database found: {json_path.name}")
    
    # Test JSON database
    try:
        from backend.database.json_handler import db
        stats = {
            'airports': len(db.get_all('airports')),
            'routes': len(db.get_all('routes')),
            'users': len(db.get_all('users'))
        }
        logger.info(f"[3/5] ✅ JSON database loaded: {stats['airports']} airports, {stats['routes']} routes")
    except Exception as e:
        logger.error(f"[3/5] ❌ JSON database error: {e}")
        return 1
    
    # Check Ollama
    model_name = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
    try:
        import ollama
        try:
            ollama.list()
            logger.info(f"[4/5] ✅ Ollama connected (model: {model_name})")
        except:
            logger.warning("[4/5] ⚠️  Ollama connection issue - will retry when needed")
    except ImportError:
        logger.error("[4/5] ❌ Ollama not installed - run: pip install ollama")
        return 1
    
    # Check OpenAI
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key.startswith("sk-"):
        logger.info("[5/5] ✅ OpenAI API key configured")
    else:
        logger.error("[5/5] ❌ Missing OPENAI_API_KEY in .env file")
        return 1
    
    # Success summary
    logger.info("=" * 60)
    logger.info("✅ Setup complete! System ready.")
    logger.info("=" * 60)
    logger.info("")
    logger.info("🔧 System Configuration:")
    logger.info(f"   - Database: JSON ({stats['airports']} airports, {stats['routes']} routes)")
    logger.info(f"   - LLM: Ollama ({model_name})")
    logger.info("   - Intent Classification: OpenAI GPT-4")
    logger.info("   - Embeddings: OpenAI (for policy RAG)")
    logger.info("")
    logger.info("🚀 To launch the chatbot:")
    logger.info("   streamlit run frontend/app.py")
    logger.info("")
    
    # Ask to launch
    try:
        response = input("Launch chatbot now? (y/n): ").strip().lower()
        if response == 'y':
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/app.py"])
    except KeyboardInterrupt:
        print("\n")
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
