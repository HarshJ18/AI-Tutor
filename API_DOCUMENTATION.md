# AI Tutor API Documentation

## Base URL
```
http://localhost:8000
```

## API Endpoints

### 1. Health Check
**GET** `/api/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "AI Tutor API is running",
  "version": "1.0.0"
}
```

---

### 2. Chat with AI Tutor
**POST** `/api/chat`

Send a question to the AI tutor and get a response with RAG context.

**Request Body:**
```json
{
  "api_key": "your_groq_api_key",
  "question": "What is natural language processing?",
  "model": "llama-3.1-70b-versatile",  // optional
  "subject_filter": "all",              // optional: "all" or specific subject
  "k": 5                                // optional: number of context chunks
}
```

**Response:**
```json
{
  "response": "Natural language processing (NLP) is...",
  "sources": [
    {
      "file": "NLP_Unit_1.pdf",
      "page": 1,
      "text": "Context text from document...",
      "score": 0.85,
      "subject": "computer_science"
    }
  ],
  "model_used": "llama-3.1-70b-versatile"
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    api_key: 'your_groq_api_key',
    question: 'What is natural language processing?',
    subject_filter: 'all',
    k: 5
  })
});

const data = await response.json();
console.log(data.response); // AI response
console.log(data.sources);  // Source documents
```

---

### 3. Build RAG Index
**POST** `/api/build-index`

Build or refresh the RAG index from documents in `pdf/` and `uploads/` folders.

**Request Body:**
```json
{
  "api_key": "your_groq_api_key",
  "pdf_dir": "pdf",        // optional, default: "pdf"
  "upload_dir": "uploads"   // optional, default: "uploads"
}
```

**Response:**
```json
{
  "success": true,
  "chunks": 150,
  "dim": 128,
  "subjects": ["computer_science", "general"],
  "subject_stats": {
    "computer_science": {
      "chunks": 100,
      "files": 5
    },
    "general": {
      "chunks": 50,
      "files": 2
    }
  },
  "message": "Index built successfully with 150 chunks"
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/build-index', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    api_key: 'your_groq_api_key',
    pdf_dir: 'pdf',
    upload_dir: 'uploads'
  })
});

const data = await response.json();
if (data.success) {
  console.log(`Index built with ${data.chunks} chunks`);
  console.log(`Subjects: ${data.subjects.join(', ')}`);
}
```

---

### 4. Retrieve Documents
**POST** `/api/retrieve`

Retrieve relevant document chunks for a query.

**Request Body:**
```json
{
  "api_key": "your_groq_api_key",
  "query": "natural language processing",
  "k": 5,                  // optional: number of results
  "subject_filter": "all"   // optional: filter by subject
}
```

**Response:**
```json
{
  "results": [
    {
      "file": "NLP_Unit_1.pdf",
      "page": 1,
      "text": "Relevant text chunk...",
      "score": 0.85,
      "subject": "computer_science"
    }
  ]
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/retrieve', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    api_key: 'your_groq_api_key',
    query: 'natural language processing',
    k: 5,
    subject_filter: 'all'
  })
});

const data = await response.json();
data.results.forEach(result => {
  console.log(`${result.file} (page ${result.page}): ${result.text}`);
});
```

---

### 5. Get Available Subjects
**GET** `/api/subjects`

Get list of available subjects in the index.

**Response:**
```json
{
  "subjects": ["computer_science", "mathematics", "physics"],
  "count": 3
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/subjects');
const data = await response.json();
console.log(`Available subjects: ${data.subjects.join(', ')}`);
```

---

### 6. Get Subject Statistics
**GET** `/api/subject-stats`

Get statistics about subjects in the index.

**Response:**
```json
{
  "computer_science": {
    "chunks": 100,
    "files": 5
  },
  "mathematics": {
    "chunks": 50,
    "files": 2
  }
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/subject-stats');
const data = await response.json();
Object.keys(data).forEach(subject => {
  console.log(`${subject}: ${data[subject].chunks} chunks, ${data[subject].files} files`);
});
```

---

### 7. Generate Quiz
**POST** `/api/quiz/generate`

Generate a quiz from content.

**Request Body:**
```json
{
  "api_key": "your_groq_api_key",
  "content": "Study material text here...",
  "num_questions": 5,        // optional, default: 5
  "difficulty": "medium",    // optional: "easy", "medium", "hard"
  "quiz_type": "Mixed"      // optional: "Mixed", "Multiple Choice", etc.
}
```

**Response:**
```json
{
  "success": true,
  "quiz": {
    "title": "Quiz - Medium Difficulty",
    "difficulty": "medium",
    "questions": [
      {
        "id": 1,
        "type": "multiple_choice",
        "question": "What is NLP?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "NLP stands for Natural Language Processing..."
      }
    ],
    "total_questions": 5
  },
  "message": "Quiz generated successfully"
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/quiz/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    api_key: 'your_groq_api_key',
    content: 'Your study material here...',
    num_questions: 5,
    difficulty: 'medium'
  })
});

const data = await response.json();
if (data.success) {
  data.quiz.questions.forEach((q, i) => {
    console.log(`Q${i+1}: ${q.question}`);
  });
}
```

---

### 8. Grade Quiz
**POST** `/api/quiz/grade`

Grade a completed quiz.

**Request Body:**
```json
{
  "quiz": {
    "title": "Quiz - Medium Difficulty",
    "questions": [
      {
        "id": 1,
        "type": "multiple_choice",
        "question": "What is NLP?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0
      }
    ]
  },
  "answers": {
    "1": 0,        // question_id: answer_index
    "2": true,     // for true/false
    "3": "text"    // for short answer
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "total_questions": 5,
    "correct_answers": 4,
    "score_percentage": 80.0,
    "grade": "B",
    "detailed_results": [
      {
        "question_id": 1,
        "question": "What is NLP?",
        "user_answer": 0,
        "correct_answer": 0,
        "is_correct": true,
        "explanation": "Explanation here..."
      }
    ]
  },
  "message": "Quiz graded successfully"
}
```

**Frontend Example:**
```javascript
const answers = {
  1: 0,    // User selected option 0 for question 1
  2: true, // User answered true for question 2
  3: "Natural Language Processing" // User's text answer
};

const response = await fetch('http://localhost:8000/api/quiz/grade', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    quiz: quizObject, // The quiz object from generate endpoint
    answers: answers
  })
});

const data = await response.json();
if (data.success) {
  console.log(`Score: ${data.results.score_percentage}% (${data.results.grade})`);
  console.log(`Correct: ${data.results.correct_answers}/${data.results.total_questions}`);
}
```

---

### 9. Upload Document
**POST** `/api/upload`

Upload a document (PDF, DOCX, or TXT).

**Request:** `multipart/form-data`
- `file`: The document file
- `api_key`: Your Groq API key

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "size": 1024000,
  "message": "File uploaded successfully",
  "path": "uploads/document.pdf"
}
```

**Frontend Example:**
```javascript
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);
formData.append('api_key', 'your_groq_api_key');

const response = await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
if (data.success) {
  console.log(`File uploaded: ${data.filename} (${data.size} bytes)`);
}
```

---

### 10. Clear Index
**DELETE** `/api/index/clear`

Clear the RAG index.

**Response:**
```json
{
  "success": true,
  "message": "Index cleared successfully"
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/index/clear', {
  method: 'DELETE'
});

const data = await response.json();
if (data.success) {
  console.log('Index cleared');
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `500` - Internal Server Error

---

## Complete Frontend Integration Example

```javascript
// API Configuration
const API_BASE = 'http://localhost:8000';
const API_KEY = 'your_groq_api_key';

// Helper function
async function apiCall(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: {}
  };

  if (body) {
    if (body instanceof FormData) {
      options.body = body;
    } else {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, options);
  return await response.json();
}

// Example: Complete workflow
async function completeWorkflow() {
  // 1. Build index
  const indexResult = await apiCall('/api/build-index', 'POST', {
    api_key: API_KEY
  });
  console.log('Index built:', indexResult);

  // 2. Get subjects
  const subjects = await apiCall('/api/subjects');
  console.log('Subjects:', subjects);

  // 3. Send chat message
  const chatResult = await apiCall('/api/chat', 'POST', {
    api_key: API_KEY,
    question: 'What is NLP?',
    subject_filter: 'all'
  });
  console.log('AI Response:', chatResult.response);

  // 4. Generate quiz
  const quizResult = await apiCall('/api/quiz/generate', 'POST', {
    api_key: API_KEY,
    content: 'Your study material...',
    num_questions: 5,
    difficulty: 'medium'
  });
  console.log('Quiz:', quizResult.quiz);
}
```

---

## Testing

1. Start the API server:
```bash
cd AI_Tutor
python api_server.py
```

2. Open `test_frontend.html` in your browser

3. Enter your Groq API key and test all endpoints

4. Or use the interactive API docs at: `http://localhost:8000/docs`

