from pathlib import Path
import streamlit as st
import json
import random
import pandas as pd
import matplotlib.pyplot as plt
import os

# Load available exam files
@st.cache_data
def get_available_exams():
    exams = []
    # Check output directory only
    output_dir = Path("output")
    if output_dir.exists():
        for file in sorted(output_dir.glob("*.json")):
            # Use the filename directly as the display name
            name = file.stem
            exams.append({"name": name, "path": str(file)})
    
    return exams

# Load questions from selected exam file
@st.cache_data
def load_questions(exam_path, _file_hash=None):
    try:
        with open(exam_path, 'r') as f:
            data = json.load(f)
            # Handle both formats: direct questions list or nested under 'questions' key
            if isinstance(data, list):
                questions = data
            else:
                questions = data.get('questions', [])
            
            # Filter valid questions and fix structural issues
            valid_questions = []
            for q in questions:
                if q.get('question_number') is not None:
                    # Fix questions with empty answers dict by parsing from question_text
                    if not q.get('answers') or len(q.get('answers', {})) == 0:
                        q = fix_question_structure(q)
                    valid_questions.append(q)
            
            return valid_questions
    except FileNotFoundError:
        st.error(f"Could not find the questions file: {exam_path}")
        return []
    except json.JSONDecodeError:
        st.error(f"Error parsing the JSON file: {exam_path}")
        return []
    except Exception as e:
        st.error(f"An error occurred while loading questions: {str(e)}")
        return []

def fix_question_structure(question):
    """Fix questions where answers are embedded in question_text instead of separate answers dict"""
    import re
    
    question_text = question.get('question_text', '')
    answers = question.get('answers', {})
    
    # If answers dict is empty, try to parse from question_text
    if not answers or len(answers) == 0:
        # Try to split by option patterns like "A.", "B.", "C.", "D."
        # First, remove trailing text like "Reveal Solution Discussion [number]"
        clean_text = re.sub(r'\s*Reveal Solution.*$', '', question_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\s*Discussion\s+\d+\s*$', '', clean_text)
        
        # Split by option letters
        parts = re.split(r'\s+([A-D])\.\s+', clean_text)
        
        if len(parts) > 1:  # If we found splits
            # First part is the question
            clean_question_text = parts[0].strip()
            question['question_text'] = clean_question_text
            
            # Parse the answers
            parsed_answers = {}
            for i in range(1, len(parts), 2):  # Every other item starting from 1
                if i + 1 < len(parts):
                    letter = parts[i]
                    answer_text = parts[i + 1].strip()
                    parsed_answers[letter] = answer_text
            
            if parsed_answers:
                question['answers'] = parsed_answers
    
    return question

# Set page configuration
st.set_page_config(
    page_title="Data Engineer Exam Questions",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
    }
    .stApp {
        color: #333333;
    }
    h1, h2, h3 {
        color: #0f4c81;
    }
    .stButton>button {
        background-color: #0f4c81;
        color: white;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #0d3e6b;
        color: white;
    }
    .question-card {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #0f4c81;
    }
    .correct-answer {
        color: #28a745;
        font-weight: bold;
    }
    .incorrect-answer {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #f5f5f5;
    }
    .progress-bar {
        height: 10px;
        background-color: #e0e0e0;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    .progress-bar-inner {
        height: 100%;
        background-color: #4CAF50;
        border-radius: 5px;
    }
    footer {
        margin-top: 50px;
        text-align: center;
        color: #666;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# Function to display an image from the extracted_images folder
def display_image(image_path):
    try:
        # Check if image_path already contains 'extracted_images' and remove it if needed
        clean_path = image_path
        if 'extracted_images/' in clean_path:
            clean_path = clean_path.replace('extracted_images/', '')
        
        # Try different path combinations
        possible_paths = [
            Path("extracted_images") / clean_path,  # Normal path
            Path("extracted_images") / clean_path.replace('-', '_'),  # Replace hyphens with underscores
            Path("extracted_images") / clean_path.replace('_', '-'),  # Replace underscores with hyphens
            Path(clean_path),  # Direct path
            Path("extracted_images") / f"{clean_path.split('.')[0]}.png"  # Try with png extension
        ]
        
        # Try each path
        image_found = False
        for path in possible_paths:
            if os.path.exists(path):
                st.image(str(path))
                image_found = True
                break
        
        if not image_found:
            st.warning(f"Image not found: {image_path}")
            # Debug info to help find the missing image
            st.write(f"Looked for: {', '.join(str(p) for p in possible_paths)}")
            
            # List available images in extracted_images folder with similar filenames
            image_dir = Path("extracted_images")
            if image_dir.exists() and image_dir.is_dir():
                base_name = clean_path.split('.')[0]
                similar_images = [f for f in os.listdir(image_dir) if base_name in f]
                if similar_images:
                    st.write(f"Similar images found: {', '.join(similar_images)}")
                
    except Exception as e:
        st.error(f"Error displaying image: {str(e)}")

# Function to display an image from the extracted_images folder

def display_single_question(question, in_quiz=False, default_answer=None, answer_key=None):
    """
    Display a single question with answer options
    
    Parameters:
    - question: The question data to display
    - in_quiz: Whether this is being displayed in a quiz (to handle radio/checkbox inputs)
    - default_answer: Default selected answer(s) (for quiz mode)
    - answer_key: Key for the input widgets (for quiz mode)
    
    Returns:
    - The user's selected answer(s) if in quiz mode, otherwise None
    """
    st.markdown(f"""
    <div class="question-card">
        <h3>Question {question.get('question_number', '')}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Question text
    st.markdown(f"<p class='question-text'>{question['question_text']}</p>", unsafe_allow_html=True)
    
    # Get all associated images
    all_images = question.get('images', [])
    question_images = []
    answer_images = {}
    
    if all_images:
        # Sort images into question images and answer images
        for img_path in all_images:
            # Extract the base filename without path
            filename = os.path.basename(img_path) if "/" in img_path else img_path
            base_name = filename.split('.')[0]  # Remove extension
            
            # Check if the filename has a letter suffix (like "44_a")
            if len(base_name) > 2 and base_name[-2] == '_' and base_name[-1].isalpha():
                # This is an answer image
                answer_letter = base_name[-1].upper()  # Extract the letter (a, b, c, etc.)
                if answer_letter not in answer_images:
                    answer_images[answer_letter] = []
                answer_images[answer_letter].append(img_path)
            else:
                # This is a question image
                question_images.append(img_path)
    
    # Display question images first
    if question_images:
        st.write("**Question Images:**")
        for img in question_images:
            display_image(img)

    # For quiz mode, display the appropriate input widget based on whether multiple answers are allowed
    selected_answer = None
    if in_quiz:
        options = list(question.get('answers', {}).keys())
        
        # Check if the correct answer has multiple letters (like "AB" or "BCD")
        correct_answer = question.get('correct_answer', '') or ''
        is_multiple_choice = len(correct_answer) > 1
        
        if is_multiple_choice:
            # For multiple choice questions, use checkboxes
            st.write("**Select all that apply:**")
            
            # Initialize selected options list
            selected_options = []
            
            # Parse default answer if provided (convert "ABC" to ["A", "B", "C"])
            default_selections = []
            if default_answer:
                default_selections = list(default_answer)
            
            # Create a checkbox for each option
            for option in options:
                is_checked = option in default_selections
                if st.checkbox(f"{option}", value=is_checked, key=f"{answer_key}_{option}"):
                    selected_options.append(option)
            
            # Sort the selected options to ensure consistent answer format (e.g., "ABC" instead of "BAC")
            selected_options.sort()
            selected_answer = ''.join(selected_options)
        else:
            # For single choice questions, use radio buttons
            default_index = 0
            if default_answer in options:
                default_index = options.index(default_answer)
                
            selected_answer = st.radio(
                "Select your answer:", 
                options, 
                index=default_index, 
                key=answer_key
            )
    
    # Display answer options
    for option, answer_text in question.get('answers', {}).items():
        # Remove 'Most Voted' tag from answer text for fairness
        clean_answer_text = answer_text.replace(' Most Voted', '').replace('Most Voted', '').strip()
        st.markdown(f"""
        <div class='answer-option'>
            <strong>{option}:</strong> {clean_answer_text}
        </div>
        """, unsafe_allow_html=True)
        
        # Display any images for this answer option
        if option in answer_images and answer_images[option]:
            st.write(f"**Answer {option} Images:**")
            for img in answer_images[option]:
                display_image(img)
    
    # Show correct answer if needed (but not in quiz mode)
    if not in_quiz:
        show_answer = st.checkbox("Show correct answer", key=f"show_answer_{question.get('question_number', '')}")
        if show_answer:
            correct = question.get('correct_answer', '') or ''
            st.markdown(f"<div class='correct-answer'><strong>Correct Answer: {correct}</strong></div>", unsafe_allow_html=True)
            
            # Show community vote distribution if available
            if 'Community vote distribution' in question:
                st.markdown(f"<div class='community-vote'>Community vote: {question['Community vote distribution']}</div>", unsafe_allow_html=True)
    
    return selected_answer

def main():
    # Sidebar
    st.sidebar.title("GCP Exam Prep")
    
    # Get available exams
    available_exams = get_available_exams()
    if not available_exams:
        st.error("No exam files found in output/ or exams/ directories")
        return
        
    # Exam selection
    selected_exam = st.sidebar.selectbox(
        "Select Exam",
        options=available_exams,
        format_func=lambda x: x["name"],
        key="exam_selector"
    )
    
    # Force rerun when exam selection changes
    if "current_exam" not in st.session_state:
        st.session_state.current_exam = selected_exam["name"]
    elif st.session_state.current_exam != selected_exam["name"]:
        st.session_state.current_exam = selected_exam["name"]
        st.cache_data.clear()  # Clear cache when switching exams
        st.rerun()
    
    # Load questions for selected exam
    # Include file path and modification time to ensure proper cache differentiation
    import os
    try:
        file_mtime = os.path.getmtime(selected_exam["path"])
    except:
        file_mtime = 0
    # Use exam name and file path to create unique cache key
    cache_key = f"{selected_exam['name']}_{selected_exam['path']}_{file_mtime}"
    questions = load_questions(selected_exam["path"], _file_hash=cache_key)
    question_count = len(questions)
    st.sidebar.info(f"Selected: {selected_exam['name']}")
    st.sidebar.info(f"Total Questions: {question_count}")
    st.sidebar.info("Case study questions are not included in this exam prep.")
    
    # Add cache clear button for debugging
    if st.sidebar.button("🔄 Clear Cache"):
        st.cache_data.clear()
        st.rerun()
    
    # Navigation
    page = st.sidebar.radio("Navigation", ["Browse Questions", "Practice Quiz", "Statistics", "About"])
    
    if page == "Browse Questions":
        st.title("Browse Questions")
        st.info(f"📚 Currently viewing: **{selected_exam['name']}** ({question_count} questions)")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search in questions", "")
        
        with col2:
            # Get available topics (could be extracted from questions in a real app)
            topics = ["All", "BigQuery", "Database", "Cloud Storage", "Data Processing"]
            selected_topic = st.selectbox("Filter by topic", topics)
        
        # Filter questions based on search term and topic
        filtered_questions = questions
        if search_term:
            filtered_questions = [q for q in filtered_questions if search_term.lower() in q["question_text"].lower()]
        
        if selected_topic != "All":
            # Simplified topic filtering (in real app, would need to extract topics from questions)
            filtered_questions = [q for q in filtered_questions if selected_topic.lower() in q["question_text"].lower()]
        
        st.info(f"Showing {len(filtered_questions)} of {question_count} questions")
        
        # Display questions
        for i, question in enumerate(filtered_questions):
            with st.expander(f"Question {question['question_number']}: {question['question_text'][:100]}...", expanded=False):
                display_single_question(question)

    elif page == "Practice Quiz":
        st.title("Practice Quiz")
        st.info(f"🎯 Quiz using: **{selected_exam['name']}** ({question_count} questions)")
        
        # Quiz settings
        num_questions = st.sidebar.slider("Number of questions", 10, 50, 20)
        quiz_topics = st.sidebar.multiselect("Choose topics (optional)",
                                             ["BigQuery", "Database", "Cloud Storage", "Data Processing"],
                                             [])
        
        # Initialize session state if not already done
        if "quiz_started" not in st.session_state:
            st.session_state.quiz_started = False
        if "quiz_completed" not in st.session_state:
            st.session_state.quiz_completed = False
        if "current_question" not in st.session_state:
            st.session_state.current_question = 0
        if "quiz_questions" not in st.session_state:
            st.session_state.quiz_questions = []
        if "answers" not in st.session_state:
            st.session_state.answers = {}
        
        # Start quiz button
        if st.sidebar.button("Start New Quiz"):
            pool = questions
            if quiz_topics:
                topic_keywords = {
                    "BigQuery": ["bigquery"],
                    "Database": ["database", "sql", "table"],
                    "Cloud Storage": ["storage", "bucket"],
                    "Data Processing": ["dataflow", "dataproc", "processing"],
                }
                kws = [kw for t in quiz_topics for kw in topic_keywords[t]]
                pool = [q for q in questions if any(kw in q["question_text"].lower() for kw in kws)]

            if pool:
                quiz_questions = random.sample(pool, min(num_questions, len(pool)))
                st.session_state.quiz_questions = quiz_questions
                st.session_state.current_question = 0
                st.session_state.answers = {}
                st.session_state.quiz_started = True
                st.session_state.quiz_completed = False
            elif quiz_topics:
                st.sidebar.error("No questions match the selected topics.")
            else:
                st.error("No questions available.")
        
        # Check if quiz has started
        if not st.session_state.quiz_started:
            st.info("Configure your quiz settings in the sidebar and click 'Start New Quiz'.")
            
            # Show a sample question card for illustration
            if question_count > 0:
                st.subheader("Sample Question")
                st.markdown("<div class='question-card'>", unsafe_allow_html=True)
                sample_q = questions[0]
                display_single_question(sample_q)
                st.write("In the real quiz, you'll select an answer and won't see which one is correct until you finish.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Display current question
            current_idx = st.session_state.current_question
            quiz_questions = st.session_state.quiz_questions
            
            if current_idx < len(quiz_questions) and not st.session_state.quiz_completed:
                current_q = quiz_questions[current_idx]
                
                # Progress bar
                progress = (current_idx) / len(quiz_questions)
                st.progress(progress)
                st.write(f"Question {current_idx + 1} of {len(quiz_questions)}")
                
                # Display question with quiz functionality
                default_answer = st.session_state.answers.get(current_idx, None)
                selected_answer = display_single_question(
                    current_q, 
                    in_quiz=True,
                    default_answer=default_answer,
                    answer_key=f"q_{current_idx}"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Previous", disabled=(current_idx == 0)):
                        # Save current answer
                        if selected_answer:
                            st.session_state.answers[current_idx] = selected_answer
                        st.session_state.current_question -= 1
                        st.rerun()
                
                with col2:
                    if current_idx == len(quiz_questions) - 1:
                        button_text = "Finish Quiz"
                    else:
                        button_text = "Next"
                        
                    if st.button(button_text):
                        # Save current answer
                        if selected_answer:
                            st.session_state.answers[current_idx] = selected_answer
                        
                        if current_idx == len(quiz_questions) - 1:
                            # Quiz completed
                            st.session_state.quiz_completed = True
                        else:
                            st.session_state.current_question += 1
                        
                        st.rerun()
            
            # Quiz results
            if st.session_state.quiz_completed:
                st.title("Quiz Results")
                
                # Calculate score
                correct_count = 0
                quiz_questions = st.session_state.quiz_questions
                answers = st.session_state.answers
                
                results_data = []
                
                for idx, question in enumerate(quiz_questions):
                    user_answer = answers.get(idx, "")
                    correct_answer = question.get("correct_answer", '') or ''
                    
                    # Sort the letters in user_answer to ensure consistent comparison for multi-answer questions
                    if user_answer and len(user_answer) > 1:
                        user_answer = ''.join(sorted(user_answer))
                    
                    # Sort the letters in correct_answer to ensure consistent comparison
                    if correct_answer and len(correct_answer) > 1:
                        correct_answer = ''.join(sorted(correct_answer))
                    
                    is_correct = user_answer == correct_answer
                    
                    if is_correct:
                        correct_count += 1
                    
                    results_data.append({
                        "Question": f"Q{idx+1}",
                        "Your Answer": user_answer,
                        "Correct Answer": question["correct_answer"],  # Keep original order for display
                        "Result": "Correct" if is_correct else "Incorrect"
                    })
                
                score_percentage = (correct_count / len(quiz_questions)) * 100 if len(quiz_questions) > 0 else 0
                
                # Show score
                st.markdown(f"<h3>Your Score: {correct_count}/{len(quiz_questions)} ({score_percentage:.1f}%)</h3>", unsafe_allow_html=True)
                
                # Passing threshold visualization
                passing_threshold = 70
                fig, ax = plt.subplots(figsize=(10, 2))
                ax.barh([0], [100], color='lightgray', height=0.5)
                ax.barh([0], [score_percentage], color='green' if score_percentage >= passing_threshold else 'orange', height=0.5)
                ax.axvline(x=passing_threshold, color='red', linestyle='--')
                ax.text(passing_threshold + 1, 0, f'Passing ({passing_threshold}%)', va='center')
                ax.set_yticks([])
                ax.set_xlim(0, 100)
                st.pyplot(fig)
                
                # Results table
                st.write("### Question Details")
                results_df = pd.DataFrame(results_data)
                
                # Color code results
                def highlight_correct(row):
                    color = 'background-color: lightgreen' if row['Result'] == 'Correct' else 'background-color: lightsalmon'
                    return ['' if i != 3 else color for i in range(len(row))]
                
                st.dataframe(results_df.style.apply(highlight_correct, axis=1))
                
                # Review questions
                st.write("### Review Questions")
                for idx, question in enumerate(quiz_questions):
                    user_answer = answers.get(idx, "")
                    correct_answer = question.get("correct_answer", '') or ''
                    
                    # Sort answers for comparison (not for display)
                    user_answer_sorted = ''.join(sorted(user_answer)) if user_answer and len(user_answer) > 1 else user_answer
                    correct_answer_sorted = ''.join(sorted(correct_answer)) if correct_answer and len(correct_answer) > 1 else correct_answer
                    
                    is_correct = user_answer_sorted == correct_answer_sorted
                    
                    with st.expander(f"Question {idx+1}: {'✓' if is_correct else '✗'}"):
                        st.markdown("<div class='question-card'>", unsafe_allow_html=True)
                        
                        # Create a custom display for the review that highlights correct/incorrect answers
                        review_q = question.copy()
                        display_single_question(review_q)
                        
                        # Add explicit feedback about the user's answer
                        if is_correct:
                            st.success(f"You answered correctly with '{user_answer}'")
                        else:
                            st.error(f"You answered '{user_answer}', but the correct answer was '{correct_answer}'")
                            
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Restart button
                if st.button("Start a New Quiz"):
                    for key in ['quiz_started', 'quiz_completed', 'current_question', 'answers', 'quiz_questions']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

    elif page == "Statistics":
        st.title("Question Statistics")
        st.info(f"📊 Statistics for: **{selected_exam['name']}** ({question_count} questions)")
        
        if question_count > 0:
            # Calculate topic distribution
            topics = {
                "BigQuery": 0,
                "Database": 0,
                "Cloud Storage": 0,
                "Data Processing": 0,
                "Other": 0
            }

            # Simplified topic extraction - in real implementation would be more sophisticated
            for q in questions:
                text = q["question_text"].lower()
                if "bigquery" in text:
                    topics["BigQuery"] += 1
                elif "database" in text or "sql" in text or "table" in text:
                    topics["Database"] += 1
                elif "storage" in text or "bucket" in text:
                    topics["Cloud Storage"] += 1
                elif "dataflow" in text or "dataproc" in text or "processing" in text:
                    topics["Data Processing"] += 1
                else:
                    topics["Other"] += 1
            
            # Display topic distribution
            st.write("### Question Topics")
            chart_data = pd.DataFrame({
                'Topic': list(topics.keys()),
                'Count': list(topics.values())
            })
            
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(chart_data['Topic'], chart_data['Count'], color='#0f4c81')
            ax.set_ylabel('Question Count')
            ax.set_title('Question Distribution by Topic')
            
            # Add count labels to the bars
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            st.pyplot(fig)
            
            # Community vote consensus analysis
            st.write("### Community Consensus Analysis")
            
            consensus_data = {
                "Strong Consensus (90-100%)": 0,
                "Moderate Consensus (70-89%)": 0,
                "Split Opinion (50-69%)": 0,
                "Highly Debated (<50%)": 0
            }
            
            # Simple parsing of community vote data
            for q in questions:
                vote_str = q.get("Community vote distribution", "")
                
                # Extract the first percentage if it exists
                import re
                match = re.search(r"(\d+)%", vote_str)
                if match:
                    percentage = int(match.group(1))
                    if percentage >= 90:
                        consensus_data["Strong Consensus (90-100%)"] += 1
                    elif percentage >= 70:
                        consensus_data["Moderate Consensus (70-89%)"] += 1
                    elif percentage >= 50:
                        consensus_data["Split Opinion (50-69%)"] += 1
                    else:
                        consensus_data["Highly Debated (<50%)"] += 1
                else:
                    # If no percentage, count as unknown
                    pass
                    
            # Display consensus data
            consensus_chart = pd.DataFrame({
                'Consensus Level': list(consensus_data.keys()),
                'Count': list(consensus_data.values())
            })
            
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            bars2 = ax2.bar(consensus_chart['Consensus Level'], consensus_chart['Count'], color='#4CAF50')
            ax2.set_ylabel('Question Count')
            ax2.set_title('Community Consensus Levels')
            
            # Add count labels
            for bar in bars2:
                height = bar.get_height()
                ax2.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            st.pyplot(fig2)
            
            # Answer distribution
            st.write("### Answer Distribution")
            
            answer_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "Multiple": 0}
            
            for q in questions:
                correct = q.get("correct_answer", '') or ''
                if len(correct) == 1 and correct in answer_counts:
                    answer_counts[correct] += 1
                else:
                    answer_counts["Multiple"] += 1
            
            # Display answer distribution
            answer_data = pd.DataFrame({
                'Answer': list(answer_counts.keys()),
                'Count': list(answer_counts.values())
            })
            
            fig3, ax3 = plt.subplots(figsize=(8, 8))
            ax3.pie(answer_data['Count'], labels=answer_data['Answer'], autopct='%1.1f%%', 
                   shadow=True, startangle=90, colors=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#C2C2F0'])
            ax3.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            ax3.set_title('Distribution of Correct Answers')
            
            st.pyplot(fig3)
            
            # Image statistics
            st.write("### Questions with Images")
            
            # Count questions with images
            questions_with_images = sum(1 for q in questions if q.get("images") and len(q["images"]) > 0)
            questions_without_images = question_count - questions_with_images
            
            # Create pie chart for image stats
            fig4, ax4 = plt.subplots(figsize=(8, 6))
            ax4.pie(
                [questions_with_images, questions_without_images],
                labels=["With Images", "Without Images"],
                autopct='%1.1f%%',
                startangle=90,
                colors=['#66B2FF', '#FF9999']
            )
            ax4.axis('equal')
            ax4.set_title('Questions with Images')
            st.pyplot(fig4)
            
            st.write(f"**{questions_with_images}** questions ({questions_with_images/question_count:.1%}) have images")
            
        else:
            st.error("No questions available for analysis.")

    elif page == "About":
        st.title("About This App")
        st.write("""
        This app provides a platform to study Data Engineering exam questions. 
        
        Features include:
        - Browse and search through questions
        - Take practice quizzes with customizable settings
        - Review performance and statistics
        
        The questions are loaded from a JSON file that contains multiple-choice questions
        related to data engineering topics including:
        - BigQuery
        - Cloud Storage
        - Database Design
        - Data Processing
        
        Each question includes the question text, multiple answers, the correct answer, 
        and community vote distribution.
        """)
        
        st.write("### How to Use")
        st.write("""
        1. **Browse Questions**: Search and filter questions by topic or keyword
        2. **Practice Quiz**: Take a quiz with a selected number of questions
        3. **Statistics**: View analytical insights about the question dataset
        """)

    # Footer
    st.markdown("""
    <footer>
        <hr>
        <p>Data Engineer Exam Questions App © 2025</p>
    </footer>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 