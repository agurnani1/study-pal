import json
import os
import re

import streamlit as st
from google import genai
from PyPDF2 import PdfReader

# -----------------------------------------------------------------
# Helper Functions (Testable)
# -----------------------------------------------------------------

def clean_text(text: str) -> str:
    """Remove excessive spaces and newlines from text."""
    return re.sub(r'\s+', ' ', text.strip())


def normalize_answer(answer: str) -> str:
    """Normalize answer to uppercase letter A-D."""
    if not answer:
        return ""
    match = re.match(r'([A-Da-d])', answer.strip())
    return match.group(1).upper() if match else ""


def calculate_score(user_answers: list, correct_answers: list) -> int:
    """Calculate number of correct answers."""
    return sum(ua == ca for ua, ca in zip(user_answers, correct_answers))


def call_gemini_api(prompt: str, client) -> str:
    """Call Gemini and return the text response."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return getattr(response, 'text', '')
    except Exception as e:
        st.error(f"API Error: {e}")
        return ""


def read_pdf(file):
    """Read text from a PDF file."""
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text


def extract_json(ai_response: str):
    """Extract JSON array from AI response even if extra text exists."""
    try:
        match = re.search(r'\[.*\]', ai_response, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        st.error(f"JSON parsing error: {e}")
    return None


def build_chat_prompt(question: str, context: str = "") -> str:
    prompt = "Answer the user's question clearly and concisely."
    if context:
        prompt += f"\nContext: {context}\n"
    prompt += f"\nQuestion: {question}\nResponse:"
    return prompt


def build_summary_prompt(notes: str) -> str:
    return (
        "Read the following study notes or PDF text and provide a clear summary. "
        "Include a short overview and a few bullet points with the most important concepts. "
        "Do not add unrelated commentary.\n\n"
        f"Notes:\n{notes}"
    )


def build_quiz_prompt(notes: str, num_questions: int = 5) -> str:
    return (
        "Create a quiz from the study notes below. Return only valid JSON containing an array of quiz questions. "
        "Each item must have a question, four answer choices labeled A through D, and the correct answer letter. "
        "Do not include any additional text before or after the JSON array.\n\n"
        "Example format:\n"
        "[{\n  \"question\": \"...\",\n  \"choices\": {\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\"},\n  \"answer\": \"A\"\n}]\n\n"
        f"Number of questions: {num_questions}\n\n"
        f"Notes:\n{notes}"
    )


def generate_quiz(notes: str, client, num_questions: int = 5):
    prompt = build_quiz_prompt(notes, num_questions)
    response = call_gemini_api(prompt, client)
    quiz = extract_json(response)
    if not quiz or not isinstance(quiz, list):
        st.error("Unable to parse quiz. Try simplifying the input or use shorter notes.")
        st.write("AI response:")
        st.code(response)
        return []

    parsed = []
    for item in quiz:
        if not isinstance(item, dict):
            continue
        question = item.get("question", "")
        choices = item.get("choices", {})
        answer = normalize_answer(item.get("answer", ""))
        if question and isinstance(choices, dict) and answer in {"A", "B", "C", "D"}:
            parsed.append({
                "question": clean_text(question),
                "choices": {k: clean_text(v) for k, v in choices.items() if k in {"A", "B", "C", "D"}},
                "answer": answer,
            })
    return parsed


def render_quiz(quiz):
    if not quiz:
        st.info("Generate a quiz first using study notes or a PDF.")
        return

    st.subheader("Quiz")
    user_answers = []
    correct_answers = []

    for index, item in enumerate(quiz, start=1):
        st.write(f"**{index}. {item['question']}**")
        option_keys = sorted(item['choices'].keys())
        options = [f"{letter}. {item['choices'][letter]}" for letter in option_keys]
        selected = st.radio("Choose an answer", options, key=f"quiz_answer_{index}")
        user_answers.append(normalize_answer(selected.split('.', 1)[0] if selected else ""))
        correct_answers.append(item['answer'])
        st.markdown("---")

    if st.button("Submit Quiz"):
        score = calculate_score(user_answers, correct_answers)
        st.success(f"You scored {score} out of {len(correct_answers)}.")
        for index, item in enumerate(quiz, start=1):
            user = user_answers[index - 1]
            correct = item["answer"]
            status = "✅ Correct" if user == correct else "❌ Incorrect"
            st.write(f"**{index}.** {status} — correct answer: {correct}. {item['choices'].get(correct, '')}")

#-------------------------------
#Prompt user to input their own Google API key
#-------------------------------
import streamlit as st
from google import genai

# 1. Sidebar interface for the API key
with st.sidebar:
    st.title("🔑 Authentication")
    user_key = st.text_input(
        "Enter your Gemini API Key", 
        type="password",
        placeholder="AIzaSy..."
    )
    
    # Visual reassurance for the user
    if user_key:
        st.info("💡 Your key is held temporarily in session memory. Simply refresh the page to completely remove it.")
    else:
        st.caption("If you leave this blank, the app will attempt to use the developer's default key.")

# 2. Key Resolution Logic
api_key = None

if user_key:
    # Use the key the user just typed
    api_key = user_key
elif "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
    # Fall back to your secret manager key if it exists
    api_key = st.secrets["GEMINI_API_KEY"]

# 3. Initialize the modern Google GenAI client
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize client: {e}")
else:
    st.warning("⚠️ Please enter a valid Gemini API key in the sidebar to begin.")
    st.stop() # Stops the rest of the app from running and crashing

#-------------------------------
# Main Logic
#-------------------------------
def main():
    st.set_page_config(page_title="AI Study Buddy",
                       page_icon="🤖", layout="wide")

    API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if not API_KEY:
        try:
            API_KEY = st.secrets["GEMINI_API_KEY"]
        except Exception:
            API_KEY = ""

    if not API_KEY:
        st.error(
            "⚠️ A Gemini API key not found! Please add it to .streamlit/secrets.toml or set the GEMINI_API_KEY environment variable."
        )
        st.stop()

    client = genai.Client(api_key=API_KEY)

    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", width=140)
    st.sidebar.title("🤖 AI Study Buddy")
    page = st.sidebar.radio(
        "Go to:", ["💬 Chat", "📄 Summarize Notes", "🎯 Quiz Me"]
    )

    if page == "💬 Chat":
        st.header("Chat with AI")
        question = st.text_area("Ask a question", height=180)
        context = st.text_area("Optional context", help="Add background material or topic details.")

        if st.button("Send"):
            if not question.strip():
                st.warning("Please enter a question before sending.")
            else:
                prompt = build_chat_prompt(question, context)
                with st.spinner("Thinking..."):
                    answer = call_gemini_api(prompt, client)
                if answer:
                    st.markdown("### Answer")
                    st.write(answer)

    elif page == "📄 Summarize Notes":
        st.header("Summarize Notes")
        input_type = st.selectbox("Input type", ["Text", "PDF"])
        text_input = ""

        if input_type == "Text":
            text_input = st.text_area("Paste your notes here", height=240)
        else:
            pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])
            if pdf_file is not None:
                text_input = read_pdf(pdf_file)
                if text_input:
                    st.success("PDF text extracted successfully.")

        if st.button("Summarize"):
            if not text_input.strip():
                st.warning("Please provide study notes or upload a PDF.")
            else:
                with st.spinner("Summarizing..."):
                    prompt = build_summary_prompt(clean_text(text_input))
                    summary = call_gemini_api(prompt, client)
                if summary:
                    st.subheader("Summary")
                    st.write(summary)

    else:
        st.header("Quiz Me")
        input_type = st.selectbox("Input type", ["Text", "PDF"])
        notes = ""
        quiz_count = st.slider("Number of questions", min_value=3, max_value=10, value=5)

        if input_type == "Text":
            notes = st.text_area("Paste your study notes here", height=220)
        else:
            pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])
            if pdf_file is not None:
                notes = read_pdf(pdf_file)
                if notes:
                    st.success("PDF text extracted successfully.")

        if st.button("Generate Quiz"):
            if not notes.strip():
                st.warning("Please provide notes or upload a PDF to generate a quiz.")
            else:
                with st.spinner("Generating quiz..."):
                    quiz_questions = generate_quiz(clean_text(notes), client, num_questions=quiz_count)
                st.session_state["generated_quiz"] = quiz_questions

        quiz = st.session_state.get("generated_quiz", [])
        render_quiz(quiz)

if __name__ == "__main__":
    main()
