import json
import random
import re
import hashlib
from typing import List, Dict, Any
from datetime import datetime

import streamlit as st
from groq import Groq

# Import RAG functions to get content from PDFs
try:
    from rag_advanced import retrieve, get_available_subjects
except ImportError:
    retrieve = None
    get_available_subjects = None


class QuizGenerator:
    def __init__(self):
        self.question_types = [
            "multiple_choice",
            "true_false", 
            "short_answer",
            "essay"
        ]
    
    def generate_quiz(self, content: str, num_questions: int = 5, difficulty: str = "medium", api_key: str = "") -> Dict[str, Any]:
        """Generate quiz from content using AI with RAG enhancement"""
        if not api_key or not api_key.strip():
            st.warning("⚠️ API key required for intelligent quiz generation")
            return self._generate_fallback_quiz(content, num_questions, difficulty)
        
        api_key = api_key.strip()
        
        # Basic API key validation
        if len(api_key) < 20:
            st.error("❌ Invalid API key format. Please check your Groq API key.")
            return self._generate_fallback_quiz(content, num_questions, difficulty)
        
        quiz = {
            "title": f"Quiz - {difficulty.title()} Difficulty",
            "difficulty": difficulty,
            "questions": [],
            "total_questions": num_questions,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Enhance content with RAG if available
        enhanced_content = self._enhance_content_with_rag(content, api_key)
        
        # Use AI to generate questions with two-step approach
        try:
            client = Groq(api_key=api_key)
            random_seed = int(datetime.now().timestamp()) % 10000
            
            # STEP 1: Extract key concepts and facts from content
            key_concepts = self._extract_key_concepts_with_ai(client, enhanced_content)
            
            # STEP 2: Generate questions based on extracted concepts
            ai_prompt = self._create_enhanced_quiz_prompt(enhanced_content, key_concepts, num_questions, difficulty, random_seed)
            
            completion = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational quiz generator. You MUST create questions that directly reference specific concepts, terms, and facts from the provided content. Never use generic placeholders. Always return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": ai_prompt,
                    },
                ],
                temperature=0.8,  # Higher temperature for more variety
                max_tokens=4000,
            )

            response = completion.choices[0].message.content

            # Parse AI response as JSON
            quiz_data = self._parse_ai_json_response(response, num_questions)
            
            if quiz_data and quiz_data.get("questions"):
                # Validate and improve questions
                validated_questions = self._validate_questions(quiz_data["questions"], enhanced_content)
                quiz["questions"] = validated_questions[:num_questions]
                quiz["total_questions"] = len(quiz["questions"])
                return quiz
            else:
                # If JSON parsing failed, try to extract questions from text
                return self._parse_ai_text_response(response, enhanced_content, num_questions, difficulty)
            
        except Exception as e:
            error_str = str(e)
            if "invalid_api_key" in error_str or "401" in error_str or "Invalid API Key" in error_str:
                st.error("❌ Invalid Groq API Key. Please check your API key in the sidebar. Get a new key from https://console.groq.com/")
            else:
                st.warning(f"⚠️ AI quiz generation failed: {str(e)}. Using fallback method.")
            return self._generate_fallback_quiz(enhanced_content, num_questions, difficulty)
    
    def _enhance_content_with_rag(self, content: str, api_key: str) -> str:
        """Enhance user content with relevant chunks from RAG index"""
        if not retrieve or len(content.strip()) < 10:
            return content
        
        try:
            # Use the content as a query to find relevant PDF chunks
            relevant_chunks = retrieve(api_key, content, k=3, subject_filter="all")
            
            if relevant_chunks:
                rag_context = "\n\n--- Additional Context from Documents ---\n"
                for i, chunk in enumerate(relevant_chunks, 1):
                    rag_context += f"\n[Source {i}: {chunk.get('file', 'Unknown')}, Page {chunk.get('page', 'N/A')}]\n"
                    rag_context += chunk.get('text', '')[:500] + "\n"
                
                enhanced = content + rag_context
                return enhanced[:6000]  # Limit total size
        except Exception as e:
            # If RAG fails, just use original content
            pass
        
        return content
    
    def _extract_key_concepts_with_ai(self, client, content: str) -> List[str]:
        """Extract key concepts, terms, and facts from content using AI"""
        if len(content) < 100:
            return self._extract_key_concepts(content)
        
        try:
            content_snippet = content[:3000]  # Use first part for concept extraction
            
            extract_prompt = f"""Extract the most important concepts, terms, facts, and key ideas from this study material. 
Return ONLY a JSON array of strings, each representing a specific concept, term, or fact mentioned in the material.

STUDY MATERIAL:
{content_snippet}

Return format (JSON array only, no other text):
["concept 1", "concept 2", "concept 3", ...]

Extract 10-15 specific concepts/terms/facts that are central to understanding this material."""
            
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You extract key concepts from educational content. Return only JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": extract_prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            concepts_text = response.choices[0].message.content.strip()
            
            # Parse JSON array
            if concepts_text.startswith("["):
                concepts = json.loads(concepts_text)
                if isinstance(concepts, list):
                    return [str(c) for c in concepts if len(str(c)) > 2][:15]
        except Exception as e:
            # Silently fall back to local extraction if AI extraction fails
            pass
        
        # Fallback to local extraction
        return self._extract_key_concepts(content)
    
    def _create_enhanced_quiz_prompt(self, content: str, key_concepts: List[str], num_questions: int, difficulty: str, seed: int) -> str:
        """Create an enhanced prompt with extracted concepts"""
        content_snippet = content[:5000]
        concepts_list = "\n".join([f"- {c}" for c in key_concepts[:10]])
        
        prompt = f"""You are creating a {difficulty} difficulty quiz with exactly {num_questions} questions.

STUDY MATERIAL:
{content_snippet}

KEY CONCEPTS IDENTIFIED IN THE MATERIAL:
{concepts_list}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. Each question MUST use actual terms, concepts, or facts from the study material above
2. Reference specific concepts from the KEY CONCEPTS list when possible
3. DO NOT use generic words like "content", "material", "documents", "theory", "concept" without context
4. Instead of "Explain the concept of Theory", use "Explain how Natural Language Processing works" (if NLP is in the content)
5. Questions must be answerable using ONLY the information in the study material
6. Use actual terminology from the material (e.g., if material mentions "tokenization", use "tokenization" in questions)
7. For multiple choice: all options must be plausible and related to the material
8. For true/false: statements must be verifiable from the material
9. Vary question types naturally

EXAMPLES OF GOOD QUESTIONS (use these as style guides):
- "What is the primary purpose of tokenization in Natural Language Processing?"
- "True or False: Statistical models are used in NLP algorithms to understand human language."
- "Explain how machine learning algorithms help computers process human language."
- "Which of the following is a key component of NLP: (a) tokenization, (b) database queries, (c) network protocols, (d) image processing?"

EXAMPLES OF BAD QUESTIONS (DO NOT CREATE THESE):
- "Explain the concept of Theory" (too generic)
- "What is Documents?" (not specific)
- "True or False: Content is important" (meaningless)

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "questions": [
    {{
      "id": 1,
      "type": "multiple_choice",
      "question": "Specific question using actual terms from material",
      "options": ["Real option A", "Real option B", "Real option C", "Real option D"],
      "correct_answer": 0,
      "explanation": "Specific explanation referencing the material"
    }},
    {{
      "id": 2,
      "type": "true_false",
      "question": "Specific verifiable statement using real terms",
      "correct_answer": true,
      "explanation": "Explanation with reference to material"
    }},
    {{
      "id": 3,
      "type": "short_answer",
      "question": "Specific question about actual concepts",
      "correct_answer": "Expected answer from material",
      "explanation": "Explanation"
    }}
  ]
}}

Generate {num_questions} unique questions now. Ensure each question references specific content."""
        
        return prompt
    
    def _validate_questions(self, questions: List[Dict], content: str) -> List[Dict]:
        """Validate that questions reference actual content"""
        content_lower = content.lower()
        validated = []
        
        # Words that indicate generic questions (should be avoided)
        generic_indicators = ["the content", "the material", "the study material", "the text", 
                             "based on the content", "according to the text", "the concept of concept",
                             "the concept of theory", "the concept of documents", "the concept of page"]
        
        for q in questions:
            if not isinstance(q, dict):
                continue
                
            question_text = q.get("question", "").lower()
            
            # Check if question is too generic
            is_generic = any(indicator in question_text for indicator in generic_indicators)
            
            # Check if question references actual content (has words from content)
            question_words = set(question_text.split())
            content_words = set(content_lower.split())
            common_words = question_words.intersection(content_words)
            
            # If question has at least 2 meaningful words from content and isn't generic, it's valid
            meaningful_common = [w for w in common_words if len(w) > 4]
            
            if not is_generic and len(meaningful_common) >= 2:
                validated.append(q)
            elif not is_generic:
                # Try to improve the question
                improved_q = self._improve_question(q, content)
                if improved_q:
                    validated.append(improved_q)
        
        return validated if validated else questions  # Return original if validation removes all
    
    def _improve_question(self, question: Dict, content: str) -> Dict:
        """Try to improve a generic question by adding content-specific terms"""
        concepts = self._extract_key_concepts(content)
        if not concepts:
            return question
        
        question_text = question.get("question", "")
        # Try to replace generic terms with actual concepts
        improved_text = question_text
        
        # Replace "the concept" with an actual concept if possible
        if "the concept" in question_text.lower() and concepts:
            concept = concepts[0]
            improved_text = question_text.replace("the concept", concept).replace("Concept", concept)
        
        if improved_text != question_text:
            question = question.copy()
            question["question"] = improved_text
        
        return question
    
    def _parse_ai_json_response(self, response: str, num_questions: int) -> Dict[str, Any]:
        """Parse AI response as JSON with robust extraction"""
        try:
            # Clean response - remove markdown code blocks if present
            cleaned = response.strip()
            
            # Remove markdown code blocks
            if "```json" in cleaned:
                start = cleaned.find("```json") + 7
                end = cleaned.find("```", start)
                if end != -1:
                    cleaned = cleaned[start:end].strip()
            elif "```" in cleaned:
                start = cleaned.find("```") + 3
                end = cleaned.find("```", start)
                if end != -1:
                    cleaned = cleaned[start:end].strip()
            
            # Find JSON object
            if not cleaned.startswith("{"):
                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                if start != -1 and end > start:
                    cleaned = cleaned[start:end]
            
            # Parse JSON
            quiz_data = json.loads(cleaned)
            return quiz_data
            
        except json.JSONDecodeError as e:
            return None
    
    def _parse_ai_text_response(self, response: str, content: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
        """Parse AI response as text and extract questions"""
        quiz = {
            "title": f"Quiz - {difficulty.title()} Difficulty",
            "difficulty": difficulty,
            "questions": [],
            "total_questions": num_questions,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Try to extract questions from text response
        lines = response.split('\n')
        current_question = None
        question_num = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect question start
            if (line[0].isdigit() and ('.' in line[:3] or ')' in line[:3])) or \
               line.lower().startswith('q:') or \
               line.lower().startswith('question'):
                
                if current_question and question_num <= num_questions:
                    quiz["questions"].append(current_question)
                    question_num += 1
                
                # Extract question text
                question_text = line
                if ':' in question_text:
                    question_text = question_text.split(':', 1)[1].strip()
                elif '.' in question_text:
                    question_text = question_text.split('.', 1)[1].strip()
                
                current_question = {
                    "id": question_num,
                    "type": "short_answer",
                    "question": question_text,
                    "correct_answer": "See explanation",
                    "explanation": "Generated from AI response"
                }
            elif current_question and line and not line.startswith(('A)', 'B)', 'C)', 'D)', 'Answer', 'Explanation')):
                # Append to current question
                current_question["question"] += " " + line
        
        if current_question and question_num <= num_questions:
            quiz["questions"].append(current_question)
        
        # Fill remaining questions if needed
        while len(quiz["questions"]) < num_questions:
            topics = self._extract_key_concepts(content)
            topic = topics[len(quiz["questions"]) % len(topics)] if topics else "key concepts"
            
            quiz["questions"].append({
                "id": len(quiz["questions"]) + 1,
                "type": "short_answer",
                "question": f"Explain the concept of {topic} as described in the material.",
                "correct_answer": f"Explanation of {topic} from the content",
                "explanation": f"This tests understanding of {topic} from the provided material."
            })
        
        return quiz
    
    def _parse_ai_response(self, response: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
        """Parse AI response and create quiz structure"""
        quiz = {
            "title": f"Quiz - {difficulty.title()} Difficulty",
            "difficulty": difficulty,
            "questions": [],
            "total_questions": num_questions,
            "created_at": st.session_state.get("current_time", "Unknown")
        }
        
        # Simple parsing - split by question numbers
        lines = response.split('\n')
        current_question = None
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) or 'Question' in line:
                if current_question:
                    quiz["questions"].append(current_question)
                
                current_question = {
                    "id": len(quiz["questions"]) + 1,
                    "type": "short_answer",
                    "question": line,
                    "correct_answer": "Answer will be provided",
                    "explanation": "Explanation will be provided"
                }
            elif current_question and line:
                current_question["question"] += " " + line
        
        if current_question:
            quiz["questions"].append(current_question)
        
        # Fill remaining questions if needed
        while len(quiz["questions"]) < num_questions:
            topics = self._extract_topics(content)
            topic = topics[len(quiz["questions"]) % len(topics)] if topics else "the content"
            
            quiz["questions"].append({
                "id": len(quiz["questions"]) + 1,
                "type": "short_answer",
                "question": f"Explain the key concepts related to {topic} based on the provided content.",
                "correct_answer": f"Key concepts about {topic} from the content",
                "explanation": f"This question tests your understanding of {topic} from the provided material."
            })
        
        return quiz
    
    def _generate_fallback_quiz(self, content: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
        """Generate quiz without AI (fallback method)"""
        quiz = {
            "title": f"Quiz - {difficulty.title()} Difficulty",
            "difficulty": difficulty,
            "questions": [],
            "total_questions": num_questions,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract key concepts from content
        concepts = self._extract_key_concepts(content)
        
        # Shuffle to ensure different questions each time
        random.shuffle(concepts)
        
        for i in range(num_questions):
            question_type = random.choice(self.question_types)
            concept = concepts[i % len(concepts)] if concepts else "the main topic"
            
            if question_type == "multiple_choice":
                question = self._generate_multiple_choice(content, difficulty, concept)
            elif question_type == "true_false":
                question = self._generate_true_false(content, difficulty, concept)
            elif question_type == "short_answer":
                question = self._generate_short_answer(content, difficulty, concept)
            else:  # essay
                question = self._generate_essay(content, difficulty, concept)
            
            question["id"] = i + 1
            question["type"] = question_type
            quiz["questions"].append(question)
        
        return quiz
    
    def _generate_multiple_choice(self, content: str, difficulty: str, concept: str = None) -> Dict[str, Any]:
        """Generate multiple choice question"""
        concepts = self._extract_key_concepts(content)
        selected_concept = concept or (random.choice(concepts) if concepts else "the main concept")
        
        question = {
            "question": f"What is the primary purpose or definition of {selected_concept} as described in the material?",
            "options": [
                f"A method or approach related to {selected_concept}",
                f"A key principle involving {selected_concept}",
                f"An important application of {selected_concept}",
                f"A characteristic feature of {selected_concept}"
            ],
            "correct_answer": 0,  # Index of correct option
            "explanation": f"This question tests understanding of {selected_concept} as presented in the study material."
        }
        
        return question
    
    def _generate_true_false(self, content: str, difficulty: str, concept: str = None) -> Dict[str, Any]:
        """Generate true/false question"""
        concepts = self._extract_key_concepts(content)
        selected_concept = concept or (random.choice(concepts) if concepts else "the main concept")
        
        question = {
            "question": f"True or False: {selected_concept} is a central concept discussed in the study material.",
            "correct_answer": True,
            "explanation": f"This statement is true because {selected_concept} is mentioned and explained in the provided content."
        }
        
        return question
    
    def _generate_short_answer(self, content: str, difficulty: str, concept: str = None) -> Dict[str, Any]:
        """Generate short answer question"""
        concepts = self._extract_key_concepts(content)
        selected_concept = concept or (random.choice(concepts) if concepts else "the main concept")
        
        question = {
            "question": f"Explain the concept of {selected_concept} as described in the study material.",
            "correct_answer": f"Explanation of {selected_concept} based on the content provided",
            "explanation": f"This question requires demonstrating understanding of {selected_concept} from the study material."
        }
        
        return question
    
    def _generate_essay(self, content: str, difficulty: str, concept: str = None) -> Dict[str, Any]:
        """Generate essay question"""
        concepts = self._extract_key_concepts(content)
        selected_concept = concept or (random.choice(concepts) if concepts else "the main concept")
        
        question = {
            "question": f"Write a detailed essay analyzing {selected_concept} as presented in the study material. Discuss its importance, applications, and key characteristics.",
            "correct_answer": f"Comprehensive analysis of {selected_concept} with examples from the content",
            "explanation": f"This essay question tests the ability to analyze and discuss {selected_concept} comprehensively based on the provided material."
        }
        
        return question
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts and important terms from content"""
        if not content or len(content) < 20:
            return ["key concepts", "main ideas", "important points"]
        
        content_lower = content.lower()
        words = content.split()
        
        # Common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", 
            "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "this", "that", "these", "those", "from", "into", "through", "during",
            "can", "may", "might", "must", "shall", "it", "its", "they", "them"
        }
        
        # Academic and technical terms that are likely important
        important_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized phrases (likely proper nouns/concepts)
        ]
        
        concepts = []
        
        # Find capitalized phrases (likely important concepts)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        concepts.extend([c for c in capitalized if c.lower() not in stop_words and len(c) > 2])
        
        # Find words that appear multiple times (likely important)
        word_freq = {}
        for word in words:
            word_clean = word.lower().strip('.,!?;:()[]{}"\'-')
            if len(word_clean) > 4 and word_clean not in stop_words:
                word_freq[word_clean] = word_freq.get(word_clean, 0) + 1
        
        # Get frequently mentioned terms
        frequent_terms = [word for word, count in word_freq.items() if count >= 2]
        concepts.extend(frequent_terms[:10])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_concepts = []
        for concept in concepts:
            concept_lower = concept.lower()
            if concept_lower not in seen and len(concept) > 2:
                seen.add(concept_lower)
                unique_concepts.append(concept)
        
        # If we don't have enough, add some generic ones
        if len(unique_concepts) < 3:
            unique_concepts.extend(["key concepts", "main ideas", "important principles"])
        
        return unique_concepts[:15]  # Return top 15 concepts
    
    def grade_quiz(self, quiz: Dict[str, Any], answers: Dict[int, Any]) -> Dict[str, Any]:
        """Grade a completed quiz"""
        total_questions = len(quiz["questions"])
        correct_answers = 0
        detailed_results = []
        
        for question in quiz["questions"]:
            question_id = question["id"]
            user_answer = answers.get(question_id, "")
            correct_answer = question["correct_answer"]
            
            is_correct = self._check_answer(question, user_answer)
            if is_correct:
                correct_answers += 1
            
            detailed_results.append({
                "question_id": question_id,
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", "")
            })
        
        score_percentage = (correct_answers / total_questions) * 100
        
        grade = self._calculate_grade(score_percentage)
        
        return {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score_percentage": score_percentage,
            "grade": grade,
            "detailed_results": detailed_results
        }
    
    def _check_answer(self, question: Dict[str, Any], user_answer: Any) -> bool:
        """Check if user answer is correct"""
        question_type = question["type"]
        correct_answer = question["correct_answer"]
        
        if question_type == "multiple_choice":
            return user_answer == correct_answer
        elif question_type == "true_false":
            return user_answer == correct_answer
        elif question_type in ["short_answer", "essay"]:
            # For text answers, do simple keyword matching
            if isinstance(user_answer, str) and isinstance(correct_answer, str):
                user_words = set(user_answer.lower().split())
                correct_words = set(correct_answer.lower().split())
                # Check if there's significant overlap
                overlap = len(user_words.intersection(correct_words))
                return overlap >= len(correct_words) * 0.3  # 30% overlap threshold
            return False
        
        return False
    
    def _calculate_grade(self, score_percentage: float) -> str:
        """Calculate letter grade based on percentage"""
        if score_percentage >= 90:
            return "A"
        elif score_percentage >= 80:
            return "B"
        elif score_percentage >= 70:
            return "C"
        elif score_percentage >= 60:
            return "D"
        else:
            return "F"
