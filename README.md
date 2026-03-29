# ✈️ Swiss Airlines AI Assistant
### ET AI Hackathon 2026 — Problem Statement 2: Agentic AI for Autonomous Enterprise Workflows
**Team:** mohdtoheed786k | **Solo Submission**

---

## What This Is

A multi-agent AI system that autonomously handles the full airline customer service workflow — flight search, hotel booking, car rentals, excursions, and policy queries — without human involvement at each step. The system detects user intent, routes to the correct specialist agent, executes real bookings, and maintains an auditable trail of every action in the database.

---

## Agent Architecture

```
User Input (Streamlit)
        │
        ▼
Intent Classifier (OpenAI GPT-4o-mini)
        │
        ├── flight_search   → Flight Agent → search_flights()
        ├── hotel_search    → Hotel Agent  → search_hotels()
        ├── car_search      → Car Agent    → search_cars()
        ├── excursion_search→ Primary Agent → search_excursions()
        ├── booking_action  → Booking Simulator → book_flight() → JSON DB
        └── policy_query    → RAG Agent (FAISS + OpenAI Embeddings)
                │
                ▼
        DeepSeek R1 (Ollama) — Natural language response
                │
                ▼
        Gemini Flash — Optional response refinement
```

**Agents:**
- `primary_assistant.py` — Orchestrator, intent routing, location parsing, booking execution
- `flight_booking.py` — Flight search + ticket update specialist
- `hotel_booking.py` — Hotel search + booking specialist
- `car_rental.py` — Car rental specialist
- `excursion_booking.py` — Excursion specialist
- `intent_classifier.py` — LLM-powered intent + parameter extraction (zero keyword matching)

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Intent Classification | OpenAI GPT-4o-mini (tool calling) |
| Conversational AI | Ollama + DeepSeek R1 (1.5b / 7b) |
| Response Refinement | Google Gemini 1.5 Flash |
| Policy RAG | FAISS + OpenAI text-embedding-3-small |
| Web Search | Tavily API |
| Location Parsing | Custom IATA resolver with fuzzy matching |
| Database | JSON flat-file database |
| Workflow | Custom state machine (`run_graph_v4`) |

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js (optional, for doc generation)
- [Ollama](https://ollama.ai) installed locally
- API keys: OpenAI, Tavily (optional), Gemini (optional)

### 1. Clone the repo
```bash
git clone https://github.com/mohdtoheed786k/swiss-airlines-ai
cd swiss-airlines-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Create a `.env` file in the root:
```env
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here       # optional
GEMINI_API_KEY=your_gemini_key_here       # optional
OLLAMA_MODEL=deepseek-r1:1.5b             # or deepseek-r1:7b for better quality
```

### 4. Start Ollama and pull the model
```bash
ollama serve
ollama pull deepseek-r1:1.5b
```

### 5. Initialize the database
```bash
python backend/database/populate_json_db.py
```

### 6. Launch the app
```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501` in your browser.

---

## Usage

Talk to the assistant in plain English:

```
"Flights from Zurich to New York"
"ok book a flight"
"id 42"                          ← any ID works, auto-registered
"Hotels in Paris"
"Rent a car in London"
"What is the baggage allowance?"
```

**To book:** any passenger ID works — existing users (1, 2, 3) or any new ID you provide. Unknown IDs are automatically registered.

---

## Project Structure

```
swiss-airlines-ai/
├── frontend/
│   └── app.py                    # Streamlit UI
├── backend/
│   ├── agents/
│   │   ├── primary_assistant.py  # Orchestrator agent
│   │   ├── intent_classifier.py  # LLM intent routing
│   │   ├── flight_booking.py     # Flight specialist
│   │   ├── hotel_booking.py      # Hotel specialist
│   │   ├── car_rental.py         # Car rental specialist
│   │   └── excursion_booking.py  # Excursion specialist
│   ├── tools/
│   │   ├── flights.py            # Flight search + booking
│   │   ├── hotels.py             # Hotel search + booking
│   │   ├── car_rentals.py        # Car rental search + booking
│   │   ├── excursions.py         # Excursion search + booking
│   │   ├── policy.py             # RAG policy lookup
│   │   ├── utilities.py          # User info + web search
│   │   ├── booking_simulator.py  # Booking engine
│   │   └── location_parser.py    # IATA + city resolver
│   ├── database/
│   │   ├── json_handler.py       # JSON DB interface
│   │   └── populate_json_db.py   # DB seeder
│   └── graph/
│       └── workflow.py           # State machine + agent orchestration
└── data/
    └── db_dump.json              # Live database
```

---

## Key Features

- **Zero keyword routing** — all intent detection via LLM, no if/else chains
- **Any passenger ID** — unknown IDs auto-registered, no authentication wall
- **Real DB writes** — every booking saved to `db_dump.json` with ticket number
- **Multi-agent coordination** — specialist agents for each domain
- **Policy RAG** — semantic search over airline FAQ using FAISS + embeddings
- **Location intelligence** — resolves city names, aliases, and IATA codes ("New York" → JFK)
- **State persistence** — conversation context maintained across messages

---

## Demo Flow

1. Ask about flights → Intent classifier routes to Flight Agent → Results shown
2. Say "ok book a flight" → Booking agent activated, asks for passenger ID
3. Type any ID (e.g. "id 42") → Auto-registered, flight booked, ticket generated
4. Check `data/db_dump.json` → New booking entry with ticket number confirmed

---

## Notes

- This is a prototype system. No real payments or airline systems are connected.
- DeepSeek R1 runs locally via Ollama — no data leaves your machine for the LLM step.
- OpenAI is used only for intent classification and policy embeddings.
