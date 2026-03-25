## AI Tutor – Technical Overview and Main Logic

### 1. High‑Level Architecture

- **Frontend (Web App)**:  
  - Built with `streamlit` (`app_simplified.py`).  
  - Provides UI for: API key input, RAG index management, document upload, chat interface, and quiz generation.

- **Backend / API Layer**:  
  - Built with `FastAPI` (`api_server.py`).  
  - Exposes REST endpoints for chat, RAG indexing/retrieval, quiz generation/grading, file upload, and health checks.  
  - Can be used by any external frontend (e.g., React, plain HTML/JS).

- **AI & RAG Engine**:  
  - Uses **Groq** LLMs via `groq` SDK (`api_handler.py`).  
  - Retrieval‑Augmented Generation implemented in `rag_advanced.py` with a custom lightweight vector index.  
  - Quiz logic in `quiz_generator.py`.

- **Storage**:  
  - File system folders: `pdf/`, `uploads/`, and `.rag_index/`.  
  - Index data stored as compressed NumPy arrays + JSON metadata.

---

### 2. Core Modules and Responsibilities

#### 2.1 `app_simplified.py` (Streamlit Frontend)

- **Page Setup**
  - Configures Streamlit page, dark theme CSS, logos.
  - Clears Streamlit caches on first load to avoid stale RAG data.

- **Main Entry (`main()`):**
  - Creates a `QuizGenerator` instance.
  - Builds sidebar:
    - Groq API key input and model selection.
    - RAG index management:
      - **Build/Refresh Index** → calls `build_index(api_key)` from `rag_advanced.py`.
      - **Clear & Rebuild** → deletes `.rag_index/`, clears caches and session state, then rebuilds index.
    - Subject filter dropdown using `get_available_subjects()` + `get_subject_stats()`.
    - Document upload (PDF/DOCX/TXT) into `uploads/` and `pdf/`.
    - Export chat history button (JSON/TXT/Markdown via `export_chat_history()`).
  - Main content: two tabs
    - **💬 Chat** → `chat_interface(api_key, model)`.
    - **🧠 Quiz Generator** → `quiz_interface(quiz_generator, api_key)`.

- **Chat Flow (`chat_interface`)**
  - Manages topic/session name and “New Session” button (clears `st.session_state.chat_history`).
  - Renders past messages with custom HTML/CSS bubbles for user and AI.
  - For each AI message, optionally displays retrieved source chunks (file, page, score, excerpt).
  - Accepts user question text and buttons:
    - **Send** → `process_user_input(api_key, model, user_input, topic)`.
    - **Clear Chat** → reset session history.
    - **Save Chat** → marks as saved (UI only).
    - **Refresh Index** → quick index rebuild (clears `.rag_index/` then `build_index`).

- **Chat Logic (`process_user_input`)**
  - Appends user message to `chat_history` with timestamp.
  - Retrieves RAG context:
    - Uses `retrieve(api_key, user_input, k=3, subject_filter=selected_subject)` from `rag_advanced.py`.
    - Builds a `context` string: “Source: <file> (Page <page>) – Subject: <subject>\n<chunk>”.
    - Constructs `enhanced_prompt = "Context ...\n\nUser question: ..."` if sources exist; otherwise falls back to plain question.
  - Calls `send_query_get_response(api_key, enhanced_prompt, "")` from `api_handler.py`.
  - Appends AI response + sources to `chat_history` and triggers `st.rerun()` so UI refreshes cleanly.

- **Quiz Flow (`quiz_interface`)**
  - UI controls:
    - `num_questions` slider (1–20), `difficulty` select, `quiz_type` select.
    - Text area for study content.
  - On **Generate Quiz**:
    - Calls `quiz_generator.generate_quiz(content, num_questions, difficulty, api_key)`.
    - Stores result in `st.session_state.current_quiz`.
  - Renders quiz questions:
    - Multiple choice → radio options.
    - True/False → boolean radio.
    - Short answer / Essay → text areas.
  - On **Submit Quiz**:
    - Collects user answers into a dict `{question_id: answer}`.
    - Calls `quiz_generator.grade_quiz(quiz, answers)`.
    - Displays overall metrics (score, correct count, grade) and per‑question explanations.

---

#### 2.2 `api_server.py` (FastAPI REST API)

- Initializes FastAPI app with CORS enabled.
- Reuses the same core logic as the Streamlit app, but exposes it via JSON endpoints.
- Main models:
  - `ChatRequest` / `ChatResponse`
  - `BuildIndexRequest` / `BuildIndexResponse`
  - `RetrieveRequest` / `RetrieveResponse`
  - `QuizGenerateRequest` / `QuizGenerateResponse`
  - `QuizGradeRequest` / `QuizGradeResponse`

- **Key Endpoints:**
  - `POST /api/chat`
    - Uses `retrieve()` from `rag_advanced.py` to get context.
    - Builds enhanced prompt and calls `api_handler.send_query_get_response`.
    - Returns AI answer + list of source chunks.
  - `POST /api/build-index`
    - Calls `build_index(api_key, pdf_dir, upload_dir)`.
    - Returns meta info (chunk count, embedding dimension, subjects, stats).
  - `POST /api/retrieve`
    - Directly exposes `retrieve()` for debugging / inspection.
  - `GET /api/subjects` and `GET /api/subject-stats`
    - Expose subject list and statistics from `rag_advanced.py`.
  - `POST /api/quiz/generate` and `POST /api/quiz/grade`
    - Wrap `QuizGenerator.generate_quiz` and `QuizGenerator.grade_quiz`.
  - `POST /api/upload`
    - Validates file type.
    - Saves to `uploads/` and, for PDFs, also to `pdf/`.
  - `DELETE /api/index/clear`
    - Deletes `.rag_index/` folder to reset the RAG index.

---

#### 2.3 `api_handler.py` (LLM Integration)

- Wraps the **Groq** client and centralizes LLM calls.
- **RAG‑aware request flow:**
  1. Attempts to call `retrieve(api_key, user_question, k=5)` to get top chunks.
  2. Builds a `retrieved_context` string summarizing each source (`file`, `page`, score, first ~1000 chars).
  3. If retrieval fails, uses a fallback “[No retrieval context available: ...]” so the LLM can still answer.
  4. Tries a list of models in order:
     - `"llama-3.1-70b-versatile"`
     - `"llama-3.1-8b-instant"`
     - `"mixtral-8x7b-32768"`
  5. For each model:
     - Calls `client.chat.completions.create()` with:
       - System prompt: “You are an AI tutor. Use the context below to answer the question…”.
       - User content: `Context:\n{retrieved_context}\n\nQuestion:\n{user_question}`.
     - On first success, returns the response; otherwise continues to next model.
  6. If all models fail, returns an error message string.

This design **centralizes AI calls** and **decouples** the UI from the LLM provider.

---

#### 2.4 `rag_advanced.py` (RAG Engine)

This module implements a **simple, lightweight vector index** without external vector DBs.

- **Index Files:**
  - `.rag_index/index.npz` – NumPy array of embeddings (shape: `N x 128`).
  - `.rag_index/meta.json` – List of metadata dicts:
    - `{"file": ..., "page": ..., "text": ..., "subject": ...}`.
  - `.rag_index/subjects.json` – Aggregated statistics per subject.

- **Document Ingestion (core logic):**
  1. Scan `pdf/` and `uploads/` for `.pdf`, `.docx`, `.doc`, `.txt`.
  2. For each file:
     - Extract text:
       - PDF: `PdfReader` per page.
       - DOCX: iterate over paragraphs.
       - TXT: full file read.
     - Infer subject from filename (e.g., “NLP_Unit1.pdf” → `computer_science`/`general` depending on keywords).
     - Chunk the text using `_chunk_text`:
       - Sliding window over words, up to ~450 tokens with ~60 token overlap.
     - For each chunk, store `(file_name, page_number, chunk_text, subject)`.
  3. Compute embeddings:
     - `_simple_embed(text)` creates a 128‑dim vector by hashing words into positions and normalizing (TF‑IDF‑like).
     - Stack all embeddings into one `N x 128` NumPy array.
  4. Save embeddings and metadata to disk.

- **Retrieval (`retrieve`)**:
  1. Load embeddings and metadata (`_load_index()`).
  2. Optional **subject filter**:
     - If `subject_filter != "all"`, select only chunks with that subject.
  3. Embed the query with `_embed_texts([query])`.
  4. Compute cosine similarities with `_cosine_sim`.
  5. Take top‑`k` indices and return the corresponding meta entries plus a `score` field.

This gives **fast local semantic search** without external services, and the **subject filter** lets the user focus on a single course or topic.

---

#### 2.5 `quiz_generator.py` (Quiz Logic)

- Provides `QuizGenerator` class with:
  - `generate_quiz(content, num_questions, difficulty, api_key)`:
    - If `api_key` present:
      - Builds an AI prompt (JSON schema for questions).
      - Sends it to Groq via `api_handler.send_query_get_response`.
      - Tries to parse AI output as JSON; if that fails, falls back to `_parse_ai_response`.
    - If no API key or AI fails:
      - Uses `_generate_fallback_quiz` (rule‑based).
  - `_generate_fallback_quiz`:
    - Extracts “topics” from content using `_extract_topics`.
    - Randomly chooses question types: multiple choice, true/false, short answer, essay.
    - Builds generic but topic‑aware questions and explanations.
  - `grade_quiz(quiz, answers)`:
    - Iterates questions, checks correctness via `_check_answer`.
    - Computes `score_percentage` and letter grade (`A`–`F`).
    - Returns per‑question breakdown + summary.

This allows the project to **work even without AI**, while still taking advantage of Groq when available.

---

### 3. Data Flow: End‑to‑End Example

#### 3.1 Chat with RAG
1. User uploads PDFs/notes via sidebar.
2. User clicks **Build/Refresh RAG Index**:
   - `build_index()` reads documents, chunks, embeds, and saves `.rag_index`.
3. User asks a question in the Chat tab.
4. `process_user_input()`:
   - Adds message to `chat_history`.
   - Calls `retrieve()` to get top relevant chunks.
   - Builds an enhanced prompt containing these chunks.
   - Calls Groq LLM via `send_query_get_response()`.
5. Response and source citations are rendered in the UI.

#### 3.2 Quiz Generation
1. User pastes study material in Quiz tab.
2. User selects number of questions and difficulty.
3. On **Generate Quiz**:
   - `QuizGenerator.generate_quiz()` uses AI or fallback to build a structured quiz object.
4. User answers through Streamlit form.
5. On **Submit Quiz**:
   - `QuizGenerator.grade_quiz()` scores answers and returns detailed results.

---

### 4. Key Technical Strengths (Talking Points for Presentation)

- **RAG‑enabled tutor**: Answers are grounded in your uploaded course materials, not just generic LLM knowledge.
- **Lightweight custom vector store**: No external DB; embeddings and metadata stored as compact files.
- **Model‑agnostic AI layer**: `api_handler.py` centralizes calls and supports multiple Groq models with automatic fallback.
- **Dual interface**:  
  - Streamlit web app for quick use and demos.  
  - FastAPI backend to integrate with any custom frontend or mobile app.
- **Robust quiz engine**: Works with or without AI, supports multiple question types and auto‑grading.
- **Explainability**: Each answer can show source files, page numbers, relevance scores, and content snippets.

This document can be directly converted to PDF and used as a **technical explanation** of the project in presentations, reports, or viva exams.


