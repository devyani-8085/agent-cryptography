# AI Solution Architect Agent — Document Intelligence & RAG Upgrade

## 🌟 Product Overview
The **AI Solution Architect Agent** is an autonomous, agentic enterprise AI platform that transforms client business problems and RFP/BRD documents into structured, trustworthy AI solution proposals and actionable implementation blueprints.

### Key Capabilities
- **Document Intelligence & RAG Retrieval**: Ingests PDF, DOCX, and TXT client documents into a chunked vector store for page-aware source evidence.
- **Transparent Stage Completion Summaries**: Generates human-readable progress summaries after every agent graph step (Requirement Analysis, Planning, Tool Selection, Solution Generation, Costing, Architecture, Matrix, and Recommendation).
- **Source Traceability & Trust Tags**: Visual indicators categorizing all extracted insights (`SOURCE-BACKED`, `INFERRED`, `NOT SPECIFIED`, `ASSUMPTION`).
- **3 Dynamic AI Solution Options**: Creates domain-tailored strategic solutions respecting budget and timeline constraints.
- **Human-in-the-Loop (HITL) Gate**: Pause node allowing explicit **Approve**, **Revise** (with feedback re-injection), or **Reject**.
- **Interactive Post-Approval Implementation Blueprint**: Visual architecture node flow, interactive component cards, step-by-step implementation phases, and downloadable Markdown proposal export.

---

## 🏗 System Architecture & Workflow

```
               [ Client Requirement Form / Document Upload ]
                                    ↓
            [ Document Processor (PDF/DOCX/TXT) & Chunking ]
                                    ↓
                  [ Vector Indexing & RAG Retriever ]
                                    ↓
            [ Step 1: Requirement Analysis + Stage Summary ]
                                    ↓
                 [ Step 2: Agent Planning + Stage Summary ]
                                    ↓
                 [ Step 3: Tool Dispatcher + Stage Summary ]
                                    ↓
         [ Step 4: 3 AI Solution Generation + Stage Summary ]
                                    ↓
          [ Step 5: Cost & Architecture Flow + Stage Summaries ]
                                    ↓
       [ Step 6: 7-Factor Decision Matrix + Stage Summary ]
                                    ↓
          [ Step 7: AI Decision Recommender + Stage Summary ]
                                    ↓
    [ Step 8: Human Approval Gate ] → [ Revise ] (Feedback Loop)
                 ↓                    → [ Reject ] (Terminates Run)
           [ Approve ]
                                    ↓
 [ Step 9: Post-Approval Blueprint & Proposal Package Export ]
```

---

## 📂 Project Structure

```
Agentic AI/
├── backend/                  ← FastAPI + SQLite + LangGraph State Machine
│   ├── app/
│   │   ├── main.py           (API Endpoints & Document Upload)
│   │   ├── agent.py          (State graph runner & Stage Summaries)
│   │   ├── tools.py          (Requirement, Solution, Cost & Architecture tools)
│   │   ├── document_processor.py (PDF, DOCX, TXT multi-format parser)
│   │   ├── rag_engine.py     (Chunker, TF-IDF Cosine Similarity & Vector store)
│   │   ├── llm.py            (OpenAI / Gemini / Anthropic multi-provider)
│   │   ├── models.py         (SQLAlchemy DB models: Project, AgentRun, SolutionOption, Approval, Proposal, Document, DocumentChunk, RequirementEvidence, StageSummary)
│   │   ├── schemas.py        (Pydantic request/response models)
│   │   └── database.py       (SQLite connection setup)
│   ├── venv/                 (Python virtual environment)
│   └── requirements.txt
└── frontend/                 ← React + Vite + Tailwind CSS
    ├── src/
    │   ├── App.jsx           (Multi-view UI: Landing, Form + Document Upload, Live Execution Timeline & Stage Summaries, 3-Solution Comparison Matrix, HITL Gate, Implementation Blueprint)
    │   └── index.css         (Tailwind CSS + custom dark styles)
    ├── package.json
    └── vite.config.js
```

---

## 🚀 How to Run

### Terminal 1 — Start Backend API
```powershell
cd "c:\Users\devka\OneDrive\Desktop\Agentic AI\backend"
.\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Server: **http://127.0.0.1:8000**
- OpenAPI Docs: **http://127.0.0.1:8000/docs**

### Terminal 2 — Start Frontend Dev Server
```powershell
cd "c:\Users\devka\OneDrive\Desktop\Agentic AI\frontend"
npm run dev
```
- Web UI: **http://localhost:5173**

---

## 🎯 Demo & Verification Flow

1. Open **http://localhost:5173**.
2. Click a **preset scenario** (e.g. "College Student Support Automator" or "Predictive Machine Breakdown").
3. (Optional) Drag & Drop a document file (`.pdf`, `.docx`, or `.txt`).
4. Click **Run Solution Graph**.
5. Watch the live **Stage Completion Summaries Timeline** update step-by-step with key findings, source chips, and trust tags (`SOURCE-BACKED`, `INFERRED`, `NOT SPECIFIED`, `ASSUMPTION`).
6. Review the **3 AI solution options** and the **7-factor comparison matrix**.
7. Click **Approve Solution** to generate the **Interactive Implementation Blueprint**.
8. Explore the clickable visual architecture node cards and phase breakdowns.
9. Click **Download Markdown Proposal** to save the complete proposal package.
