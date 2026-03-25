# API Testing Commands

## Prerequisites
1. Start the API server first:
```bash
cd AI_Tutor
python api_server.py
```

2. Replace `YOUR_GROQ_API_KEY` with your actual Groq API key in all commands below.

---

## Windows PowerShell Commands

### 1. Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET
```

### 2. Build RAG Index
```powershell
$body = @{
    api_key = "YOUR_GROQ_API_KEY"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/build-index" -Method POST -Body $body -ContentType "application/json"
```

### 3. Chat with AI Tutor
```powershell
$body = @{
    api_key = "YOUR_GROQ_API_KEY"
    question = "What is natural language processing?"
    subject_filter = "all"
    k = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json"
```

### 4. Retrieve Documents
```powershell
$body = @{
    api_key = "YOUR_GROQ_API_KEY"
    query = "natural language processing"
    k = 5
    subject_filter = "all"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/retrieve" -Method POST -Body $body -ContentType "application/json"
```

### 5. Get Available Subjects
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/subjects" -Method GET
```

### 6. Get Subject Statistics
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/subject-stats" -Method GET
```

### 7. Generate Quiz
```powershell
$body = @{
    api_key = "YOUR_GROQ_API_KEY"
    content = "Natural language processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language."
    num_questions = 5
    difficulty = "medium"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/quiz/generate" -Method POST -Body $body -ContentType "application/json"
```

### 8. Grade Quiz
```powershell
$body = @{
    quiz = @{
        title = "Test Quiz"
        difficulty = "medium"
        questions = @(
            @{
                id = 1
                type = "multiple_choice"
                question = "What is NLP?"
                options = @("Option A", "Option B", "Option C", "Option D")
                correct_answer = 0
            }
        )
        total_questions = 1
    }
    answers = @{
        "1" = 0
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/quiz/grade" -Method POST -Body $body -ContentType "application/json"
```

### 9. Upload Document
```powershell
$filePath = "path\to\your\file.pdf"
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileName = [System.IO.Path]::GetFileName($filePath)

$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
    "Content-Type: application/pdf",
    "",
    [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes),
    "--$boundary",
    "Content-Disposition: form-data; name=`"api_key`"",
    "",
    "YOUR_GROQ_API_KEY",
    "--$boundary--"
) -join $LF

Invoke-RestMethod -Uri "http://localhost:8000/api/upload" -Method POST -Body ([System.Text.Encoding]::GetEncoding("iso-8859-1").GetBytes($bodyLines)) -ContentType "multipart/form-data; boundary=$boundary"
```

### 10. Clear Index
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/index/clear" -Method DELETE
```

---

## Linux/Mac/Git Bash Commands (cURL)

### 1. Health Check
```bash
curl -X GET http://localhost:8000/api/health
```

### 2. Build RAG Index
```bash
curl -X POST http://localhost:8000/api/build-index \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_GROQ_API_KEY"}'
```

### 3. Chat with AI Tutor
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_GROQ_API_KEY",
    "question": "What is natural language processing?",
    "subject_filter": "all",
    "k": 5
  }'
```

### 4. Retrieve Documents
```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_GROQ_API_KEY",
    "query": "natural language processing",
    "k": 5,
    "subject_filter": "all"
  }'
```

### 5. Get Available Subjects
```bash
curl -X GET http://localhost:8000/api/subjects
```

### 6. Get Subject Statistics
```bash
curl -X GET http://localhost:8000/api/subject-stats
```

### 7. Generate Quiz
```bash
curl -X POST http://localhost:8000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_GROQ_API_KEY",
    "content": "Natural language processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language.",
    "num_questions": 5,
    "difficulty": "medium"
  }'
```

### 8. Grade Quiz
```bash
curl -X POST http://localhost:8000/api/quiz/grade \
  -H "Content-Type: application/json" \
  -d '{
    "quiz": {
      "title": "Test Quiz",
      "difficulty": "medium",
      "questions": [
        {
          "id": 1,
          "type": "multiple_choice",
          "question": "What is NLP?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_answer": 0
        }
      ],
      "total_questions": 1
    },
    "answers": {
      "1": 0
    }
  }'
```

### 9. Upload Document
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/your/file.pdf" \
  -F "api_key=YOUR_GROQ_API_KEY"
```

### 10. Clear Index
```bash
curl -X DELETE http://localhost:8000/api/index/clear
```

---

## Python Test Script

Save this as `test_api.py`:

```python
import requests
import json

API_BASE = "http://localhost:8000"
API_KEY = "YOUR_GROQ_API_KEY"  # Replace with your actual API key

def test_health():
    """Test health endpoint"""
    print("1. Testing Health Check...")
    response = requests.get(f"{API_BASE}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_build_index():
    """Test build index endpoint"""
    print("2. Testing Build Index...")
    response = requests.post(
        f"{API_BASE}/api/build-index",
        json={"api_key": API_KEY}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_chat():
    """Test chat endpoint"""
    print("3. Testing Chat...")
    response = requests.post(
        f"{API_BASE}/api/chat",
        json={
            "api_key": API_KEY,
            "question": "What is natural language processing?",
            "subject_filter": "all",
            "k": 5
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data.get('response', 'No response')[:200]}...\n")

def test_retrieve():
    """Test retrieve endpoint"""
    print("4. Testing Retrieve...")
    response = requests.post(
        f"{API_BASE}/api/retrieve",
        json={
            "api_key": API_KEY,
            "query": "natural language processing",
            "k": 5
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Found {len(response.json().get('results', []))} results\n")

def test_subjects():
    """Test subjects endpoint"""
    print("5. Testing Get Subjects...")
    response = requests.get(f"{API_BASE}/api/subjects")
    print(f"Status: {response.status_code}")
    print(f"Subjects: {response.json().get('subjects', [])}\n")

def test_subject_stats():
    """Test subject stats endpoint"""
    print("6. Testing Subject Stats...")
    response = requests.get(f"{API_BASE}/api/subject-stats")
    print(f"Status: {response.status_code}")
    print(f"Stats: {json.dumps(response.json(), indent=2)}\n")

def test_generate_quiz():
    """Test quiz generation"""
    print("7. Testing Generate Quiz...")
    response = requests.post(
        f"{API_BASE}/api/quiz/generate",
        json={
            "api_key": API_KEY,
            "content": "Natural language processing (NLP) is a branch of artificial intelligence.",
            "num_questions": 3,
            "difficulty": "medium"
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    if data.get('success'):
        print(f"Generated quiz with {data['quiz']['total_questions']} questions\n")
    else:
        print(f"Error: {data}\n")

def test_clear_index():
    """Test clear index endpoint"""
    print("8. Testing Clear Index...")
    response = requests.delete(f"{API_BASE}/api/index/clear")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

if __name__ == "__main__":
    print("=" * 50)
    print("AI Tutor API Test Suite")
    print("=" * 50)
    print()
    
    # Run tests
    test_health()
    # test_build_index()  # Uncomment after setting API_KEY
    # test_chat()  # Uncomment after setting API_KEY
    # test_retrieve()  # Uncomment after setting API_KEY
    test_subjects()
    test_subject_stats()
    # test_generate_quiz()  # Uncomment after setting API_KEY
    # test_clear_index()  # Uncomment if needed
    
    print("=" * 50)
    print("Tests completed!")
    print("=" * 50)
```

Run with:
```bash
python test_api.py
```

---

## Quick Test Commands (Copy-Paste Ready)

### Windows PowerShell - Quick Test
```powershell
# Set your API key
$API_KEY = "YOUR_GROQ_API_KEY"

# Health check
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET

# Build index
$body = @{api_key = $API_KEY} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/build-index" -Method POST -Body $body -ContentType "application/json"

# Chat
$body = @{
    api_key = $API_KEY
    question = "What is NLP?"
    subject_filter = "all"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json"
```

### Linux/Mac - Quick Test
```bash
# Set your API key
export API_KEY="YOUR_GROQ_API_KEY"

# Health check
curl http://localhost:8000/api/health

# Build index
curl -X POST http://localhost:8000/api/build-index \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$API_KEY\"}"

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$API_KEY\", \"question\": \"What is NLP?\", \"subject_filter\": \"all\"}"
```

