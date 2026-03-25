from groq import Groq
from rag_advanced import retrieve


def _validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key:
        return False
    api_key = api_key.strip()
    # Groq API keys typically start with 'gsk_' and are 40+ characters
    if len(api_key) < 20:
        return False
    return True


def send_query_get_response(api_key: str, user_question: str, _unused_assistant_id: str = ""):
    # Validate and clean API key
    if not api_key or not api_key.strip():
        return "Error: API key is required. Please enter your Groq API key in the sidebar."
    
    api_key = api_key.strip()
    
    if not _validate_api_key(api_key):
        return "Error: Invalid API key format. Please check your Groq API key."
    
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        return f"Error initializing Groq client: {str(e)}"

    # Retrieve top context
    try:
        top_chunks = retrieve(api_key, user_question, k=5)
        context_lines = []
        for c in top_chunks:
            context_lines.append(f"- Source: {c['file']} (p.{c['page']}) | score={c['score']:.3f}\n{c['text'][:1000]}")
        retrieved_context = "\n".join(context_lines)
    except Exception as e:
        # If index missing or retrieval fails, continue without RAG
        retrieved_context = f"[No retrieval context available: {e}]"

    # Try different Groq models
    candidate_models = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]

    last_err = None
    response = None
    
    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI tutor. Use the context below to answer the question. Cite the file name and page when relevant. If context is insufficient, say so and answer from general knowledge."
                    },
                    {
                        "role": "user", 
                        "content": f"Context:\n{retrieved_context}\n\nQuestion:\n{user_question}"
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            last_err = None
            break
        except Exception as e:
            last_err = e
            # Check for specific error types
            error_str = str(e)
            if "invalid_api_key" in error_str or "401" in error_str or "Invalid API Key" in error_str:
                return "❌ Error: Invalid Groq API Key. Please check your API key in the sidebar. Get a new key from https://console.groq.com/"
            continue

    if response is None:
        error_msg = str(last_err) if last_err else "Unknown error"
        if "invalid_api_key" in error_msg or "401" in error_msg:
            return "❌ Error: Invalid Groq API Key. Please check your API key in the sidebar. Get a new key from https://console.groq.com/"
        return f"❌ Error contacting Groq: {error_msg}"

    try:
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error parsing response: {e}"