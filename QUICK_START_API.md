# Quick Start Guide - AI Tutor API

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API Server

1. Start the FastAPI server:
```bash
cd AI_Tutor
python api_server.py
```

The server will start on `http://localhost:8000`

2. Access interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing the API

### Option 1: Use the Test Frontend

1. Open `test_frontend.html` in your browser
2. Enter your Groq API key
3. Test all endpoints interactively

### Option 2: Use cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Build index
curl -X POST http://localhost:8000/api/build-index \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_groq_api_key"}'

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_groq_api_key",
    "question": "What is NLP?",
    "subject_filter": "all"
  }'
```

### Option 3: Use Python

```python
import requests

API_BASE = "http://localhost:8000"
API_KEY = "your_groq_api_key"

# Build index
response = requests.post(f"{API_BASE}/api/build-index", json={
    "api_key": API_KEY
})
print(response.json())

# Chat
response = requests.post(f"{API_BASE}/api/chat", json={
    "api_key": API_KEY,
    "question": "What is natural language processing?",
    "subject_filter": "all"
})
data = response.json()
print(data["response"])
```

## All Available Endpoints

1. **GET** `/api/health` - Health check
2. **POST** `/api/chat` - Chat with AI tutor
3. **POST** `/api/build-index` - Build RAG index
4. **POST** `/api/retrieve` - Retrieve documents
5. **GET** `/api/subjects` - Get available subjects
6. **GET** `/api/subject-stats` - Get subject statistics
7. **POST** `/api/quiz/generate` - Generate quiz
8. **POST** `/api/quiz/grade` - Grade quiz
9. **POST** `/api/upload` - Upload document
10. **DELETE** `/api/index/clear` - Clear index

See `API_DOCUMENTATION.md` for detailed request/response formats.

## Frontend Integration

See `API_DOCUMENTATION.md` for complete frontend integration examples.

Basic example:
```javascript
const API_BASE = 'http://localhost:8000';
const API_KEY = 'your_groq_api_key';

// Chat endpoint
const response = await fetch(`${API_BASE}/api/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    api_key: API_KEY,
    question: 'What is NLP?',
    subject_filter: 'all'
  })
});

const data = await response.json();
console.log(data.response); // AI response
```

## Troubleshooting

1. **Port already in use**: Change port in `api_server.py`:
   ```python
   uvicorn.run("api_server:app", host="0.0.0.0", port=8001)
   ```

2. **CORS errors**: The API already has CORS enabled for all origins. If you need to restrict it, edit `api_server.py`.

3. **API key errors**: Make sure your Groq API key is valid and has sufficient credits.

4. **Index not found**: Run `/api/build-index` first before using chat or retrieve endpoints.

