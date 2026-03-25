"""
Quick API Test Script
Run this to test all API endpoints
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000"
API_KEY = "YOUR_GROQ_API_KEY"  # Replace with your actual API key

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """Test health endpoint"""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to API server.")
        print("   Make sure the server is running: python api_server.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_build_index():
    """Test build index endpoint"""
    print_section("2. Build RAG Index")
    if API_KEY == "YOUR_GROQ_API_KEY":
        print("⚠️  SKIPPED: Please set your API_KEY in the script")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/api/build-index",
            json={"api_key": API_KEY},
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            print(f"✅ Success!")
            print(f"   Chunks: {data.get('chunks', 0)}")
            print(f"   Subjects: {', '.join(data.get('subjects', []))}")
        else:
            print(f"❌ Error: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_chat():
    """Test chat endpoint"""
    print_section("3. Chat with AI Tutor")
    if API_KEY == "YOUR_GROQ_API_KEY":
        print("⚠️  SKIPPED: Please set your API_KEY in the script")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/api/chat",
            json={
                "api_key": API_KEY,
                "question": "What is natural language processing?",
                "subject_filter": "all",
                "k": 5
            },
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            print(f"✅ Success!")
            print(f"   Response: {data.get('response', '')[:200]}...")
            print(f"   Sources: {len(data.get('sources', []))} documents found")
        else:
            print(f"❌ Error: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_retrieve():
    """Test retrieve endpoint"""
    print_section("4. Retrieve Documents")
    if API_KEY == "YOUR_GROQ_API_KEY":
        print("⚠️  SKIPPED: Please set your API_KEY in the script")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/api/retrieve",
            json={
                "api_key": API_KEY,
                "query": "natural language processing",
                "k": 5
            },
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            results = data.get('results', [])
            print(f"✅ Success! Found {len(results)} results")
            if results:
                print(f"   First result: {results[0].get('file', 'Unknown')} (page {results[0].get('page', 'N/A')})")
        else:
            print(f"❌ Error: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_subjects():
    """Test subjects endpoint"""
    print_section("5. Get Available Subjects")
    try:
        response = requests.get(f"{API_BASE}/api/subjects", timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            subjects = data.get('subjects', [])
            print(f"✅ Success! Found {len(subjects)} subjects")
            if subjects:
                print(f"   Subjects: {', '.join(subjects)}")
            else:
                print("   No subjects found. Build index first.")
        else:
            print(f"❌ Error: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_subject_stats():
    """Test subject stats endpoint"""
    print_section("6. Get Subject Statistics")
    try:
        response = requests.get(f"{API_BASE}/api/subject-stats", timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            if data:
                print(f"✅ Success!")
                for subject, stats in data.items():
                    print(f"   {subject}: {stats.get('chunks', 0)} chunks, {stats.get('files', 0)} files")
            else:
                print("   No statistics available. Build index first.")
        else:
            print(f"❌ Error: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_generate_quiz():
    """Test quiz generation"""
    print_section("7. Generate Quiz")
    if API_KEY == "YOUR_GROQ_API_KEY":
        print("⚠️  SKIPPED: Please set your API_KEY in the script")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/api/quiz/generate",
            json={
                "api_key": API_KEY,
                "content": "Natural language processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language. NLP draws from many disciplines, including computer science and computational linguistics.",
                "num_questions": 3,
                "difficulty": "medium"
            },
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200 and data.get('success'):
            quiz = data.get('quiz', {})
            print(f"✅ Success!")
            print(f"   Quiz: {quiz.get('title', 'Unknown')}")
            print(f"   Questions: {quiz.get('total_questions', 0)}")
        else:
            print(f"❌ Error: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_clear_index():
    """Test clear index endpoint"""
    print_section("8. Clear Index")
    try:
        response = requests.delete(f"{API_BASE}/api/index/clear", timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            print(f"✅ Success! {data.get('message', 'Index cleared')}")
        else:
            print(f"❌ Error: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  AI Tutor API Test Suite")
    print("=" * 60)
    
    if API_KEY == "YOUR_GROQ_API_KEY":
        print("\n⚠️  WARNING: API_KEY not set. Some tests will be skipped.")
        print("   Edit test_api.py and set API_KEY = 'your_actual_api_key'")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    
    # Only run API key dependent tests if key is set
    if API_KEY != "YOUR_GROQ_API_KEY":
        results.append(("Build Index", test_build_index()))
        results.append(("Chat", test_chat()))
        results.append(("Retrieve", test_retrieve()))
        results.append(("Generate Quiz", test_generate_quiz()))
    
    # These don't require API key
    results.append(("Get Subjects", test_subjects()))
    results.append(("Subject Stats", test_subject_stats()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("=" * 60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

