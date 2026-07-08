# NutriBot

AI nutrition copilot. React + TanStack Start frontend, Flask + SQLite + Groq backend.

## 1. Backend (Flask)

```
cd backend-flask
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend-flask/.env`:
```
GROQ_API_KEY=your_groq_key_here
DATABASE_URL=sqlite:///nutribot.db
JWT_SECRET=change_me
```

Initialize the user/chat database:
```
python scripts/init_db.py
```

(Optional but recommended) Build the food RAG database. See
`backend-flask/dataset/README.md` for the USDA download step, then:
```
python scripts/data_ingestion.py
```

Run the API:
```
python app.py
```
Default: http://localhost:5000

## 2. Frontend (TanStack Start)

From the project root:
```
npm install
npm run dev
```
Default: http://localhost:5173

The frontend calls the Flask API at `http://localhost:5000`. Override via
`VITE_API_URL` in a `.env` file at the project root.

## Stack

- Frontend: React 19, TanStack Start/Router, Tailwind v4, jsPDF
- Backend: Flask, SQLAlchemy, JWT, Groq (`llama-3.3-70b-versatile` chat,
  `llama-3.1-8b-instant` extraction/summarization)
- Data: USDA FoodData Central CSV bundle ingested into SQLite for RAG
