import streamlit as st
import os
from datetime import datetime
from PIL import Image
import json

# Local modules
import api_handler
from api_handler import send_query_get_response
from rag_advanced import build_index, retrieve, get_available_subjects, get_subject_stats
from quiz_generator import QuizGenerator

# Page configuration
st.set_page_config(
    page_title="AI Tutor - Simplified",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clear all caches on startup
if "cache_cleared" not in st.session_state:
    st.session_state.cache_cleared = True
    st.cache_data.clear()
    st.cache_resource.clear()

# Load logos
try:
    logo = Image.open('logo.png')
    sb_logo = Image.open('sb_logo.png')
except:
    logo = None
    sb_logo = None

# Custom CSS
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --dark-bg: #1e1e1e;
        --card-bg: #2d2d2d;
        --text-primary: #ffffff;
        --text-secondary: #b0b0b0;
        --border-color: #404040;
    }
    
    /* Global dark theme */
    .stApp {
        background-color: var(--dark-bg) !important;
        color: var(--text-primary) !important;
    }
    
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 15px;
        max-width: 80%;
        word-wrap: break-word;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border: none;
    }
    
    .user-message {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        margin-left: 20%;
        border-bottom-right-radius: 5px;
    }
    
    .ai-message {
        background: linear-gradient(135deg, var(--card-bg) 0%, #3d3d3d 100%);
        color: var(--text-primary);
        margin-right: 20%;
        border: 1px solid var(--border-color);
        border-bottom-left-radius: 5px;
    }
    
    .ai-message strong {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    .sources-section {
        background: linear-gradient(135deg, #2a4a6b 0%, #1e3a5f 100%);
        padding: 0.8rem;
        margin-top: 0.5rem;
        border-radius: 10px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        color: var(--text-primary);
    }
    
    .sources-section strong {
        color: #64b5f6;
    }
    
    /* Input fields styling */
    .stTextInput > div > div > input {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    
    .stTextArea > div > div > textarea {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox > div > div:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--card-bg) !important;
    }
    
    .css-1d391kg .stMarkdown {
        color: var(--text-primary) !important;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        background: var(--card-bg) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--primary-color) !important;
    }
    
    /* Remove white overlays */
    .stMarkdown {
        margin-bottom: 0;
        background: transparent !important;
    }
    
    .stExpander {
        background: transparent !important;
        border: none !important;
    }
    
    .stExpander > div {
        background: transparent !important;
        border: none !important;
    }
    
    .stExpander > div > div {
        background: transparent !important;
        border: none !important;
    }
    
    .streamlit-expanderHeader {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    .streamlit-expanderContent {
        background: transparent !important;
        border: none !important;
    }
    
    /* Tab styling */
    .stTabs > div > div > div > div {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    
    .stTabs > div > div > div > div[aria-selected="true"] {
        background: var(--primary-color) !important;
        color: white !important;
    }
    
    /* Labels and text */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: var(--text-primary) !important;
    }
    
    .stMarkdown label {
        color: var(--text-primary) !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize components
    quiz_generator = QuizGenerator()
    
    # Header
    st.markdown('<div class="main-header"><h1>🎓 AI Tutor - Simplified</h1><p>Your Intelligent Learning Companion</p></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        if logo:
            st.image(logo, width=200)
        else:
            st.write("🎓 AI Tutor")
        
        # API Key Management
        st.subheader("🔑 API Configuration")
        api_key = st.text_input(
            "Enter your Groq API Key",
            type="password",
            value=st.secrets.get("GROQ_API_KEY", ""),
            help="Get your API key from https://console.groq.com/"
        )
        
        # Validate API key format
        if api_key:
            api_key = api_key.strip()
            if len(api_key) < 20:
                st.error("❌ API key seems too short. Please check your Groq API key.")
            elif not api_key.startswith("gsk_"):
                st.info("💡 Tip: Groq API keys usually start with 'gsk_'. Make sure you copied the full key.")
        
        if not api_key or not api_key.strip():
            st.warning("⚠️ Please enter your Groq API key to use the AI Tutor")
            st.info("📝 Get your free API key from: https://console.groq.com/keys")
            return
        
        # Store cleaned API key
        api_key = api_key.strip()
        
        # Model Selection
        st.subheader("🤖 AI Model")
        model = st.selectbox(
            "Choose AI Model",
            ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            index=0,
            help="Different models have different strengths"
        )
        
        # RAG Index Management
        st.subheader("📚 Knowledge Base")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔧 Build/Refresh RAG Index", type="primary"):
                with st.spinner("Building RAG index..."):
                    try:
                        result = build_index(api_key)
                        st.success(f"✅ Index built successfully! {result['chunks']} chunks processed")
                        if 'subjects' in result:
                            st.info(f"📚 Subjects found: {', '.join(result['subjects'])}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Index build failed: {str(e)}")
        
        with col2:
            if st.button("🔄 Clear & Rebuild", help="Clear old index and rebuild with current files"):
                with st.spinner("Clearing old index and rebuilding..."):
                    try:
                        # Clear old index
                        import shutil
                        import os
                        if os.path.exists('.rag_index'):
                            shutil.rmtree('.rag_index')
                        
                        # Clear all caches
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        
                        # Clear session state
                        if "chat_history" in st.session_state:
                            del st.session_state.chat_history
                        
                        st.success("🗑️ Old index and caches cleared!")
                        
                        # Rebuild with current files
                        result = build_index(api_key)
                        st.success(f"✅ Fresh index built! {result['chunks']} chunks processed")
                        if 'subjects' in result:
                            st.info(f"📚 Subjects found: {', '.join(result['subjects'])}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Rebuild failed: {str(e)}")
        
        # Subject Filter
        try:
            subjects = get_available_subjects()
            if subjects:
                st.subheader("🎯 Subject Filter")
                selected_subject = st.selectbox(
                    "Filter by subject",
                    ["all"] + subjects,
                    help="Choose a specific subject to focus your questions on"
                )
                st.session_state.selected_subject = selected_subject
                
                # Show subject statistics
                subject_stats = get_subject_stats()
                if subject_stats:
                    st.write("📊 **Subject Statistics:**")
                    for subject, stats in subject_stats.items():
                        st.write(f"• **{subject.title()}**: {stats['chunks']} chunks, {stats['files']} files")
            else:
                st.session_state.selected_subject = "all"
        except:
            st.session_state.selected_subject = "all"
        
        # Document Upload
        st.subheader("📄 Document Upload")
        uploaded_files = st.file_uploader(
            "Upload documents",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Upload PDF, DOCX, or TXT files to add to your knowledge base"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    # Save to both uploads and pdf folders for RAG processing
                    upload_path = f"uploads/{uploaded_file.name}"
                    pdf_path = f"pdf/{uploaded_file.name}"
                    
                    # Save to uploads folder
                    with open(upload_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Also save to pdf folder for RAG processing
                    with open(pdf_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    st.success(f"✅ {uploaded_file.name} uploaded and ready for indexing")
                    st.write(f"📊 Size: {uploaded_file.size} bytes")
                    st.info("💡 Click 'Build/Refresh RAG Index' to process this document")
                    
                except Exception as e:
                    st.error(f"❌ Error uploading {uploaded_file.name}: {str(e)}")
        
        # Export Options
        st.subheader("📤 Export")
        if st.button("💾 Export Chat History"):
            export_chat_history()
    
    # Main content area
    tab1, tab2 = st.tabs(["💬 Chat", "🧠 Quiz Generator"])
    
    with tab1:
        chat_interface(api_key, model)
    
    with tab2:
        quiz_interface(quiz_generator, api_key)

def chat_interface(api_key: str, model: str):
    """Main chat interface"""
    st.subheader("💬 Chat with AI Tutor")
    
    # Topic selection
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("📝 Topic/Session Name", value="General Discussion", help="Name your current study session")
    with col2:
        if st.button("🔄 New Session"):
            if "chat_history" in st.session_state:
                del st.session_state.chat_history
            st.rerun()
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat history display
    chat_history = st.session_state.chat_history
    if chat_history:
        st.markdown("### 💭 Conversation History")
        for message in chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            else:
                # Format AI response with better styling
                ai_content = message["content"].replace('\n', '<br>')
                st.markdown(f'<div class="chat-message ai-message"><strong>🤖 AI Tutor:</strong><br><br>{ai_content}</div>', unsafe_allow_html=True)
                
                # Show sources if available
                if message.get("sources"):
                    st.markdown("### 📚 Sources & References")
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(f"""
                        <div class="sources-section">
                            <strong>📄 Source {i}:</strong> {source.get('file', 'Unknown')} (Page {source.get('page', 'N/A')})<br>
                            <strong>🎯 Relevance:</strong> {source.get('score', 0):.3f}<br>
                            <strong>📝 Content:</strong> {source.get('text', '')[:300]}...
                        </div>
                        """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.text_area("💬 Ask a question:", height=100, placeholder="Type your question here...")
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("🚀 Send", type="primary"):
            if user_input:
                process_user_input(api_key, model, user_input, topic)
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    with col3:
        if st.button("💾 Save Chat"):
            st.success("✅ Chat saved successfully!")
    with col4:
        if st.button("🔄 Refresh Index", help="Quick refresh of knowledge base"):
            with st.spinner("Refreshing knowledge base..."):
                try:
                    import shutil
                    import os
                    if os.path.exists('.rag_index'):
                        shutil.rmtree('.rag_index')
                    result = build_index(api_key)
                    st.success(f"✅ Knowledge base refreshed! {result['chunks']} chunks processed")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Refresh failed: {str(e)}")

def process_user_input(api_key: str, model: str, user_input: str, topic: str):
    """Process user input and generate response"""
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Get RAG context with subject filtering
    try:
        selected_subject = st.session_state.get("selected_subject", "all")
        sources = retrieve(api_key, user_input, k=3, subject_filter=selected_subject)
        
        if sources:
            context = "\n\n".join([f"Source: {s['file']} (Page {s['page']}) - Subject: {s.get('subject', 'general')}\n{s['text']}" for s in sources])
            enhanced_prompt = f"Context from documents (Subject: {selected_subject}):\n{context}\n\nUser question: {user_input}"
        else:
            enhanced_prompt = user_input
            sources = []
    except Exception as e:
        st.warning(f"⚠️ Could not retrieve context: {str(e)}")
        enhanced_prompt = user_input
        sources = []
    
    # Generate response
    with st.spinner("🤔 Thinking..."):
        try:
            response = send_query_get_response(api_key, enhanced_prompt, "")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sources": sources
            })
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")

def quiz_interface(quiz_generator, api_key: str = ""):
    """Quiz generation interface"""
    st.subheader("🧠 Quiz Generator")
    
    # Quiz settings
    col1, col2, col3 = st.columns(3)
    with col1:
        num_questions = st.slider("Number of Questions", 1, 20, 5)
    with col2:
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    with col3:
        quiz_type = st.selectbox("Quiz Type", ["Mixed", "Multiple Choice", "True/False", "Short Answer", "Essay"])
    
    # Content source selection
    content_source = st.radio(
        "📚 Content Source:",
        ["Manual Input", "From PDF Documents (RAG)"],
        help="Choose to paste content manually or generate from your uploaded PDFs"
    )
    
    content = ""
    
    if content_source == "Manual Input":
        # Content input
        content = st.text_area("📝 Enter content to generate quiz from:", height=200, 
                              placeholder="Paste your study material here...")
    else:
        # Generate from RAG
        try:
            from rag_advanced import get_available_subjects
            subjects = get_available_subjects()
            if subjects:
                selected_subject = st.selectbox(
                    "Select subject to generate quiz from:",
                    ["all"] + subjects,
                    help="Choose a specific subject or 'all' to use all documents"
                )
                
                # Get sample content from RAG
                if st.button("🔍 Load Content from Documents", help="Retrieve content from your indexed documents"):
                    try:
                        from rag_advanced import retrieve
                        # Use a general query to get content
                        sample_query = "main concepts and key topics"
                        chunks = retrieve(api_key, sample_query, k=5, subject_filter=selected_subject if selected_subject != "all" else None)
                        
                        if chunks:
                            # Combine chunks into content
                            content = "\n\n".join([
                                f"[From {chunk.get('file', 'Unknown')}, Page {chunk.get('page', 'N/A')}]\n{chunk.get('text', '')}"
                                for chunk in chunks
                            ])
                            st.success(f"✅ Loaded content from {len(chunks)} document chunks!")
                            st.text_area("📄 Retrieved Content:", content, height=200, key="rag_content_display")
                        else:
                            st.warning("⚠️ No content found. Please build the RAG index first from the sidebar.")
                    except Exception as e:
                        st.error(f"❌ Error loading content: {str(e)}")
            else:
                st.warning("⚠️ No documents indexed. Please upload documents and build the RAG index from the sidebar.")
        except Exception as e:
            st.warning(f"⚠️ RAG not available: {str(e)}")
            content_source = "Manual Input"
            content = st.text_area("📝 Enter content to generate quiz from:", height=200, 
                                  placeholder="Paste your study material here...")
    
    # Generate quiz button
    if st.button("🎯 Generate Quiz", type="primary"):
        if content and len(content.strip()) > 50:
            with st.spinner("🤖 AI is generating your quiz from the content..."):
                try:
                    # Store API key in session state for quiz generation
                    st.session_state.api_key = api_key
                    quiz = quiz_generator.generate_quiz(content, num_questions, difficulty, api_key)
                    st.session_state.current_quiz = quiz
                    st.success("✅ Quiz generated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error generating quiz: {str(e)}")
        else:
            st.warning("⚠️ Please enter sufficient content (at least 50 characters) to generate quiz from")
    
    # Display quiz
    if "current_quiz" in st.session_state:
        quiz = st.session_state.current_quiz
        st.markdown(f"### 📋 {quiz['title']}")
        
        # Show quiz info
        st.info(f"📊 {quiz['total_questions']} questions • {quiz['difficulty'].title()} difficulty")
        
        # Quiz form
        with st.form("quiz_form"):
            answers = {}
            for i, question in enumerate(quiz["questions"]):
                st.markdown(f"**Question {i+1}:** {question['question']}")
                
                if question["type"] == "multiple_choice":
                    answer = st.radio("Choose an answer:", question["options"], key=f"q{i}")
                    answers[question["id"]] = question["options"].index(answer)
                elif question["type"] == "true_false":
                    answer = st.radio("True or False:", [True, False], key=f"q{i}")
                    answers[question["id"]] = answer
                else:
                    answer = st.text_area("Your answer:", key=f"q{i}")
                    answers[question["id"]] = answer
                
                st.markdown("---")
            
            if st.form_submit_button("📊 Submit Quiz"):
                results = quiz_generator.grade_quiz(quiz, answers)
                st.session_state.quiz_results = results
                st.success(f"Quiz completed! Score: {results['score_percentage']:.1f}% ({results['grade']})")
        
        # Display results
        if "quiz_results" in st.session_state:
            results = st.session_state.quiz_results
            st.markdown("### 📊 Quiz Results")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{results['score_percentage']:.1f}%")
            with col2:
                st.metric("Correct", f"{results['correct_answers']}/{results['total_questions']}")
            with col3:
                st.metric("Grade", results['grade'])
            
            # Detailed results
            for result in results['detailed_results']:
                with st.expander(f"Question {result['question_id']}"):
                    st.write(f"**Question:** {result['question']}")
                    st.write(f"**Your Answer:** {result['user_answer']}")
                    st.write(f"**Correct Answer:** {result['correct_answer']}")
                    st.write(f"**Result:** {'✅ Correct' if result['is_correct'] else '❌ Incorrect'}")
                    st.write(f"**Explanation:** {result['explanation']}")
    
    # Show debug info if no quiz generated
    elif content and st.button("🔍 Debug Quiz Generation"):
        st.write("**Debug Info:**")
        st.write(f"Content length: {len(content)} characters")
        st.write(f"API Key available: {'Yes' if api_key else 'No'}")
        st.write(f"Quiz generator initialized: {'Yes' if quiz_generator else 'No'}")
        
        # Try to generate quiz with debug
        try:
            st.write("**Attempting quiz generation...**")
            quiz = quiz_generator.generate_quiz(content, 3, "medium", api_key)
            st.write(f"Generated quiz: {quiz}")
            st.session_state.current_quiz = quiz
            st.success("Quiz generated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

def export_chat_history():
    """Export current chat history"""
    if "chat_history" in st.session_state and st.session_state.chat_history:
        # Export as JSON
        export_data = {
            "chat_history": st.session_state.chat_history,
            "exported_at": datetime.now().isoformat(),
            "session_id": st.session_state.get("session_id", "unknown")
        }
        
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Export as TXT
        txt_data = f"Chat History Export\n"
        txt_data += f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        txt_data += f"Session ID: {st.session_state.get('session_id', 'unknown')}\n"
        txt_data += "=" * 50 + "\n\n"
        
        for msg in st.session_state.chat_history:
            role = msg["role"].upper()
            content = msg["content"]
            timestamp = msg.get("timestamp", "Unknown")
            txt_data += f"[{timestamp}] {role}: {content}\n\n"
        
        # Export as Markdown
        md_data = f"# Chat History Export\n\n"
        md_data += f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md_data += f"**Session ID:** {st.session_state.get('session_id', 'unknown')}\n\n"
        md_data += "---\n\n"
        
        for msg in st.session_state.chat_history:
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", "Unknown")
            
            if role == "user":
                md_data += f"**You:** {content}\n\n"
            else:
                md_data += f"**AI Tutor:** {content}\n\n"
        
        # Show export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "💾 Download JSON",
                json_data,
                "chat_history.json",
                "application/json"
            )
        
        with col2:
            st.download_button(
                "📄 Download TXT",
                txt_data,
                "chat_history.txt",
                "text/plain"
            )
        
        with col3:
            st.download_button(
                "📝 Download Markdown",
                md_data,
                "chat_history.md",
                "text/markdown"
            )
        
        st.success("✅ Chat history exported successfully!")
    else:
        st.warning("⚠️ No chat history to export")

if __name__ == "__main__":
    main()
