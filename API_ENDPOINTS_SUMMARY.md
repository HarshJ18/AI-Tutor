# API Endpoints Summary

## Quick Reference

### Base URL
```
http://localhost:8000
```

### All Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/chat` | Chat with AI tutor |
| POST | `/api/build-index` | Build RAG index |
| POST | `/api/retrieve` | Retrieve documents |
| GET | `/api/subjects` | Get available subjects |
| GET | `/api/subject-stats` | Get subject statistics |
| POST | `/api/quiz/generate` | Generate quiz |
| POST | `/api/quiz/grade` | Grade quiz |
| POST | `/api/upload` | Upload document |
| DELETE | `/api/index/clear` | Clear index |

---

## Request/Response Formats

### 1. POST `/api/chat`
**Request:**
```json
{
  "api_key": "string",
  "question": "string",
  "model": "string (optional)",
  "subject_filter": "string (optional)",
  "k": 5
}
```

**Response:**
```json
{
  "response": "string",
  "sources": [{"file": "string", "page": 1, "text": "string", "score": 0.85}],
  "model_used": "string"
}
```

---

### 2. POST `/api/build-index`
**Request:**
```json
{
  "api_key": "string",
  "pdf_dir": "string (optional)",
  "upload_dir": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "chunks": 150,
  "dim": 128,
  "subjects": ["string"],
  "subject_stats": {},
  "message": "string"
}
```

---

### 3. POST `/api/retrieve`
**Request:**
```json
{
  "api_key": "string",
  "query": "string",
  "k": 5,
  "subject_filter": "string (optional)"
}
```

**Response:**
```json
{
  "results": [{"file": "string", "page": 1, "text": "string", "score": 0.85}]
}
```

---

### 4. GET `/api/subjects`
**Response:**
```json
{
  "subjects": ["string"],
  "count": 3
}
```

---

### 5. GET `/api/subject-stats`
**Response:**
```json
{
  "subject_name": {
    "chunks": 100,
    "files": 5
  }
}
```

---

### 6. POST `/api/quiz/generate`
**Request:**
```json
{
  "api_key": "string",
  "content": "string",
  "num_questions": 5,
  "difficulty": "easy|medium|hard",
  "quiz_type": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "quiz": {
    "title": "string",
    "difficulty": "string",
    "questions": [],
    "total_questions": 5
  },
  "message": "string"
}
```

---

### 7. POST `/api/quiz/grade`
**Request:**
```json
{
  "quiz": {},
  "answers": {
    "question_id": "answer_value"
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
    "detailed_results": []
  },
  "message": "string"
}
```

---

### 8. POST `/api/upload`
**Request:** `multipart/form-data`
- `file`: File (PDF, DOCX, TXT)
- `api_key`: String

**Response:**
```json
{
  "success": true,
  "filename": "string",
  "size": 1024000,
  "message": "string",
  "path": "string"
}
```

---

### 9. DELETE `/api/index/clear`
**Response:**
```json
{
  "success": true,
  "message": "string"
}
```

---

## Frontend Integration Examples

### JavaScript/TypeScript

```typescript
const API_BASE = 'http://localhost:8000';

// Chat
async function chat(apiKey: string, question: string) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: apiKey,
      question: question,
      subject_filter: 'all'
    })
  });
  return await response.json();
}

// Build Index
async function buildIndex(apiKey: string) {
  const response = await fetch(`${API_BASE}/api/build-index`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey })
  });
  return await response.json();
}

// Upload File
async function uploadFile(apiKey: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('api_key', apiKey);
  
  const response = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData
  });
  return await response.json();
}

// Generate Quiz
async function generateQuiz(apiKey: string, content: string, numQuestions: number = 5) {
  const response = await fetch(`${API_BASE}/api/quiz/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: apiKey,
      content: content,
      num_questions: numQuestions,
      difficulty: 'medium'
    })
  });
  return await response.json();
}
```

### React Example

```jsx
import { useState } from 'react';

function ChatComponent() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const API_KEY = 'your_groq_api_key';

  const handleSend = async () => {
    const result = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: API_KEY,
        question: message,
        subject_filter: 'all'
      })
    });
    const data = await result.json();
    setResponse(data.response);
  };

  return (
    <div>
      <input value={message} onChange={(e) => setMessage(e.target.value)} />
      <button onClick={handleSend}>Send</button>
      <div>{response}</div>
    </div>
  );
}
```

---

## Error Handling

All endpoints return errors in this format:
```json
{
  "detail": "Error message"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad Request
- `500` - Internal Server Error

Example error handling:
```javascript
try {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: API_KEY, question: 'test' })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  const data = await response.json();
  return data;
} catch (error) {
  console.error('API Error:', error.message);
  throw error;
}
```

