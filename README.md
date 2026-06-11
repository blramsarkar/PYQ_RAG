# PYQ Intelligence

RAG-powered previous year question bank with exam prediction and practice mode.

## Stack
- **LLM**: Groq (llama3-70b) — PDF parsing, practice feedback  
- **Embeddings**: `all-MiniLM-L6-v2` (sentence-transformers, runs locally)  
- **Vector DB**: ChromaDB (persistent, local)  
- **UI**: Streamlit

---

## Setup & Run

```bash
# 1. Clone / enter the project folder
cd pyq_rag

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Groq API key (or paste it in the sidebar at runtime)
cp .env.example .env
# Edit .env and add your key: GROQ_API_KEY=gsk_...

# 5. Run the app
streamlit run app.py
```

App opens at http://localhost:8501

---

## Usage

1. **Sidebar** → paste Groq API key → upload one or more PYQ PDFs → click **Process PDFs**  
2. **Question Bank** tab → search/filter questions by subject, exam type, topic, difficulty  
3. **Exam Predictor** tab → see topic frequency chart, year distribution, and gap-based predictions  
4. **Practice Mode** tab → pick filters → generate a set → write answers → get AI feedback  

The vector DB persists in `./data/chroma_db/`. Re-run the app anytime; indexed data is retained.

---
