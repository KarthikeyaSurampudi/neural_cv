# NeuralCV: AI-Powered Resume Scoring & Candidate Ranking

NeuralCV is an automated resume screening platform that uses Large Language Models (LLMs) to perform deep analysis of candidate fit against job requirements. The system is designed to handle high volumes of resumes while maintaining high-quality candidate justifications and ranking.

## System Capabilities

### Two-Stage Intelligent Analysis

1. **Stage 1: Bulk Parsing & Scoring:** Every candidate resume is extracted (PDF/DOCX/TXT) and scored across three primary metrics: **Technical Skills**, **Experience Relevance**, and **Education Alignment**. This stage normalizes scores to a 0.0-1.0 range.
2. **Stage 2: Expert Multi-Candidate Ranking:** Candidates scoring 80% or higher are automatically sent to the Stage 2 expert ranking. The LLM performs a comparative analysis of the top-tier pool, assigning a global rank and generating a detailed justification (min. 100 words) covering fit/gap analysis.

### Performance & Cost Optimization

* **Resume-Level Caching:** SHA-256 hashing is used to identify resumes that have been previously processed against the same Job Description (JD), skipping the LLM call and cloning historical scoring data.
* **Analysis-Level Caching:** Detects identical analysis runs (same JD + same resume set) to prevent database duplication.
* **Concurrency Control:** Uses `asyncio.Semaphore` to manage parallel LLM requests, ensuring the application remains responsive without hitting rate limits.

### Application Architecture

* **Persistent Auth:** JWT-based session management integrated with file-based persistence (using UUIDs) to maintain user state across browser refreshes and application restarts.
* **Robust Error Handling:** Fault-tolerant processing ensures that a single malformed resume or API failure does not crash the entire analysis run. Errors are logged and displayed in the UI while other files continue processing.
* **Resource Management:** Implements automatic cleanup of temporary upload directories for every analysis session to ensure zero data bloat on the server.

## Tech Stack & Core Libraries

* **Front-end:** Streamlit (v1.30+)
* **Models:** Cohere (Command series) or OpenRouter (GPT-4/Claude via completion)
* **Data Layer:** SQLAlchemy (Async) with PostgreSQL
* **Security:** JWT, Bcrypt password hashing
* **Parsing:** PyPDF2, python-docx, pydantic (Validation)

## Getting Started

### 1. Install Dependencies

Download and install required packages from the project root:

```powershell
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the root directory. Required variables:

* `COHERE_API_KEY`: For primary parsing/scoring
* `JWT_SECRET_KEY`: Used to sign persistent session tokens
* `DATABASE_URL=postgresql+asyncpg://resdb_chqu_user:yWppCmyXMl8LGJAaYbbzSh5RUYPQSGjW@dpg-d6amt9gboq4c73dgdr20-a.oregon-postgres.render.com/resdb_chqu`: PostgreSQL deployment path

### 3. Database Initialization

Run the specialized admin utility to initialize all tables and create the default superuser:

```powershell
python -m utils.initial_db_admin
```

* **Default Username:** `admin`
* **Default Password:** `Admin123`

### 4. Run Application

Launch the main application via Streamlit:

```powershell
streamlit run app/streamlit_app.py
```

## Maintenance & Logs

* **Logs:** Standard application logs are found in `logs/app.log`.
* **LLM Debugging:** Full prompt/response history for debugging LLM behavior is stored in `logs/debug_llm.txt`.
* **Versioning:** Refer to `CHANGELOG.txt` for the full 27-point version history.
* **Structure:** Refer to `PROJECT_DOCUMENTATION.txt` for technical folder/file insights.
