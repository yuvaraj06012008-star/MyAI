import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader


# =========================================================
# API KEY
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Streamlit Cloud uses st.secrets
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        st.error("GEMINI_API_KEY not found in Streamlit Secrets.")
        st.stop()

client = genai.Client(api_key=api_key)


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="MyAI Learning Assistant",
    page_icon="🤖",
    layout="wide"
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "chats": {"New Chat": []},
    "current_chat": "New Chat",
    "tool": "Chat",
    "quiz_questions": [],
    "quiz_answers": {},
    "quiz_submitted": False,
    "pdf_text": "",
    "pdf_name": "",
    "pdf_quiz_questions": [],
    "pdf_quiz_answers": {},
    "pdf_quiz_submitted": False,
    "pdf_output": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# FUNCTIONS
# =========================================================

def create_new_chat():

    number = len(st.session_state.chats) + 1

    name = f"New Chat {number}"

    st.session_state.chats[name] = []

    st.session_state.current_chat = name


def create_chat_title(text):

    words = text.split()

    if len(words) <= 5:
        return text

    return " ".join(words[:5]) + "..."


def generate_ai(prompt):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


def clean_json_response(text):

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def generate_quiz_from_text(pdf_text, number=5):

    prompt = f"""
You are MyAI, an AI Learning Assistant.

Create exactly {number} multiple-choice questions
using ONLY the information in the provided PDF.

Every question must have exactly 4 options.

Make sure:
- Only one option is correct.
- Questions are directly based on the PDF.
- Do not invent information.
- Include important dates, concepts, activities and facts.
- Make the questions clear for a college student.

Return ONLY valid JSON.

Format:

[
  {{
    "question": "Question",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": 0,
    "explanation": "Explanation"
  }}
]

Answer:
0 = A
1 = B
2 = C
3 = D

PDF:

{pdf_text}
"""

    answer = generate_ai(prompt)

    answer = clean_json_response(answer)

    questions = json.loads(answer)

    return questions


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📚 MyAI")

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        create_new_chat()

        st.session_state.tool = "Chat"

        st.rerun()

    st.divider()

    st.subheader("💬 Your Chats")

    for chat_name in list(st.session_state.chats.keys()):

        if st.button(
            chat_name,
            key=f"chat_{chat_name}",
            use_container_width=True
        ):

            st.session_state.current_chat = chat_name

            st.session_state.tool = "Chat"

            st.rerun()

    st.divider()

    st.subheader("🎓 Learning Tools")

    if st.button(
        "📝 Generate Notes",
        use_container_width=True
    ):

        st.session_state.tool = "Notes"

        st.rerun()

    if st.button(
        "❓ Generate Quiz",
        use_container_width=True
    ):

        st.session_state.tool = "Quiz"

        st.rerun()

    if st.button(
        "📄 PDF Study Assistant",
        use_container_width=True
    ):

        st.session_state.tool = "Document"

        st.rerun()

    if st.button(
        "📅 Study Plan",
        use_container_width=True
    ):

        st.session_state.tool = "Study Plan"

        st.rerun()


# =========================================================
# NOTES
# =========================================================

if st.session_state.tool == "Notes":

    st.title("📝 AI Notes Generator")

    st.write(
        "Enter any subject or topic and MyAI will create "
        "easy-to-understand study notes."
    )

    topic = st.text_input(
        "📚 Enter your topic",
        placeholder="Example: Python"
    )

    level = st.selectbox(
        "🎓 Select your level",
        [
            "School Student",
            "College Student",
            "Beginner",
            "Advanced"
        ]
    )

    style = st.selectbox(
        "📝 Notes style",
        [
            "Short Notes",
            "Detailed Notes",
            "Exam Preparation Notes"
        ]
    )

    if st.button(
        "✨ Generate Notes",
        type="primary"
    ):

        if not topic:

            st.warning(
                "Please enter a topic."
            )

        else:

            prompt = f"""
You are MyAI, an AI Learning Assistant.

Create {style} for a {level} student.

Topic: {topic}

Use simple language and clear headings.

Include:

1. Introduction
2. Definition
3. Important Concepts
4. Main Points
5. Examples
6. Advantages / Importance
7. Exam Quick Revision

Make the answer accurate and easy to study.
"""

            with st.spinner(
                "Creating notes..."
            ):

                try:

                    answer = generate_ai(prompt)

                    st.markdown(answer)

                except Exception as e:

                    st.error(
                        f"Something went wrong: {e}"
                    )


# =========================================================
# GENERAL QUIZ
# =========================================================

elif st.session_state.tool == "Quiz":

    st.title("❓ AI Quiz Generator")

    st.write(
        "Create an interactive quiz from any topic."
    )

    topic = st.text_input(
        "📚 Enter quiz topic",
        placeholder="Example: Python"
    )

    difficulty = st.selectbox(
        "🎯 Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    number = st.selectbox(
        "🔢 Number of questions",
        [5, 10, 15]
    )

    if st.button(
        "✨ Generate Quiz",
        type="primary"
    ):

        if not topic:

            st.warning(
                "Please enter a topic."
            )

        else:

            prompt = f"""
Create a {difficulty} multiple-choice quiz
about {topic}.

Create exactly {number} questions.

Return ONLY valid JSON.

Format:

[
  {{
    "question": "Question",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": 0,
    "explanation": "Explanation"
  }}
]

Answer:
0 = A
1 = B
2 = C
3 = D
"""

            with st.spinner(
                "Creating quiz..."
            ):

                try:

                    answer = generate_ai(prompt)

                    answer = clean_json_response(answer)

                    questions = json.loads(
                        answer
                    )

                    st.session_state.quiz_questions = questions

                    st.session_state.quiz_answers = {}

                    st.session_state.quiz_submitted = False

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Quiz error: {e}"
                    )


    if st.session_state.quiz_questions:

        st.divider()

        st.subheader(
            "🧠 Answer the questions"
        )

        for i, q in enumerate(
            st.session_state.quiz_questions
        ):

            st.markdown(
                f"### Q{i + 1}. {q['question']}"
            )

            answer = st.radio(
                "Choose your answer:",
                q["options"],
                key=f"quiz_{i}"
            )

            st.session_state.quiz_answers[i] = answer

        if not st.session_state.quiz_submitted:

            if st.button(
                "🏆 Submit Quiz",
                type="primary"
            ):

                st.session_state.quiz_submitted = True

                st.rerun()

        else:

            score = 0

            for i, q in enumerate(
                st.session_state.quiz_questions
            ):

                correct = q["options"][
                    q["answer"]
                ]

                selected = (
                    st.session_state.quiz_answers.get(i)
                )

                if selected == correct:
                    score += 1

            total = len(
                st.session_state.quiz_questions
            )

            percentage = (
                score / total
            ) * 100

            st.success(
                f"🏆 Your Score: {score} / {total}"
            )

            st.metric(
                "Percentage",
                f"{percentage:.0f}%"
            )

            if percentage >= 80:

                st.balloons()

                st.success(
                    "🎉 Excellent work!"
                )

            elif percentage >= 50:

                st.info(
                    "👍 Good job! Keep practicing."
                )

            else:

                st.warning(
                    "📚 Keep studying and try again!"
                )

            st.divider()

            st.subheader(
                "📖 Answer Review"
            )

            for i, q in enumerate(
                st.session_state.quiz_questions
            ):

                selected = (
                    st.session_state.quiz_answers.get(i)
                )

                correct = q["options"][
                    q["answer"]
                ]

                st.markdown(
                    f"### Q{i + 1}. {q['question']}"
                )

                if selected == correct:

                    st.success(
                        f"✅ Correct: {correct}"
                    )

                else:

                    st.error(
                        f"❌ Your answer: {selected}"
                    )

                    st.success(
                        f"✅ Correct answer: {correct}"
                    )

                st.info(
                    "💡 " + q["explanation"]
                )


# =========================================================
# PDF STUDY ASSISTANT
# =========================================================

elif st.session_state.tool == "Document":

    st.title("📄 PDF Study Assistant")

    st.write(
        "Upload your study PDF and MyAI will read it."
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"]
    )

    if uploaded_file:

        try:

            reader = PdfReader(
                uploaded_file
            )

            extracted_text = ""

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:

                    extracted_text += (
                        page_text + "\n"
                    )

            st.session_state.pdf_text = extracted_text

            st.session_state.pdf_name = (
                uploaded_file.name
            )

            st.success(
                f"✅ PDF loaded: {uploaded_file.name}"
            )

            st.info(
                f"📄 Pages: {len(reader.pages)}"
            )

            st.info(
                f"📝 Extracted characters: "
                f"{len(extracted_text):,}"
            )

            with st.expander(
                "👀 Preview extracted text"
            ):

                st.text(
                    extracted_text[:5000]
                )

        except Exception as e:

            st.error(
                f"PDF error: {e}"
            )


    # =====================================================
    # PDF QUESTIONS
    # =====================================================

    if st.session_state.pdf_text:

        st.divider()

        st.subheader(
            "💬 Ask a Question About Your PDF"
        )

        question = st.text_area(
            "What do you want to know?",
            placeholder=(
                "Example: What is the main "
                "objective of the internship?"
            ),
            height=100
        )

        if st.button(
            "🔍 Ask MyAI",
            type="primary"
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                pdf_text = st.session_state.pdf_text

                if len(pdf_text) > 100000:

                    pdf_text = pdf_text[:100000]

                prompt = f"""
You are MyAI, an AI Learning Assistant.

Answer the question using ONLY information
from the uploaded PDF.

Do not invent facts.

PDF:

{pdf_text}

Question:

{question}

Give a clear and simple answer.
"""

                with st.spinner(
                    "🤖 MyAI is reading your PDF..."
                ):

                    try:

                        answer = generate_ai(
                            prompt
                        )

                        st.subheader(
                            "🤖 MyAI Answer"
                        )

                        st.markdown(
                            answer
                        )

                    except Exception as e:

                        st.error(
                            f"Something went wrong: {e}"
                        )


        # =================================================
        # PDF LEARNING TOOLS
        # =================================================

        st.divider()

        st.subheader(
            "📚 PDF Learning Tools"
        )


        # =================================================
        # SUMMARY
        # =================================================

        if st.button(
            "📝 Summarize PDF"
        ):

            pdf_text = st.session_state.pdf_text

            if len(pdf_text) > 100000:
                pdf_text = pdf_text[:100000]

            prompt = f"""
Create a clear study summary of this PDF.

Use:

# 📚 PDF Summary

## 1. Overview

## 2. Main Topics

## 3. Important Points

## 4. Key Learning

## 5. Final Summary

Use simple language.

PDF:

{pdf_text}
"""

            with st.spinner(
                "📝 Creating PDF summary..."
            ):

                try:

                    answer = generate_ai(
                        prompt
                    )

                    st.markdown(answer)

                except Exception as e:

                    st.error(
                        f"Summary error: {e}"
                    )


        # =================================================
        # IMPORTANT POINTS
        # =================================================

        if st.button(
            "⭐ Important Points"
        ):

            pdf_text = st.session_state.pdf_text

            if len(pdf_text) > 100000:
                pdf_text = pdf_text[:100000]

            prompt = f"""
Read this PDF carefully.

Create the most important study points.

Use:

# ⭐ Important Points

Number the points clearly.

Focus on:
- Important facts
- Important dates
- Definitions
- Concepts
- Activities
- Conclusions

Do not invent information.

PDF:

{pdf_text}
"""

            with st.spinner(
                "⭐ Finding important points..."
            ):

                try:

                    answer = generate_ai(
                        prompt
                    )

                    st.markdown(answer)

                except Exception as e:

                    st.error(
                        f"Important points error: {e}"
                    )


        # =================================================
        # 2 MARK QUESTIONS
        # =================================================

        if st.button(
            "📝 Generate 2-Mark Questions"
        ):

            pdf_text = st.session_state.pdf_text

            if len(pdf_text) > 100000:
                pdf_text = pdf_text[:100000]

            prompt = f"""
Read the uploaded PDF.

Create 10 important 2-mark questions
with answers.

Use this format:

# 📝 2-Mark Questions

### Q1. Question
**Answer:** Short answer.

### Q2. Question
**Answer:** Short answer.

Continue until Q10.

Questions and answers must be based
only on the PDF.

PDF:

{pdf_text}
"""

            with st.spinner(
                "📝 Creating 2-mark questions..."
            ):

                try:

                    answer = generate_ai(
                        prompt
                    )

                    st.markdown(answer)

                except Exception as e:

                    st.error(
                        f"2-mark error: {e}"
                    )


        # =================================================
        # 5 MARK QUESTIONS
        # =================================================

        if st.button(
            "📖 Generate 5-Mark Questions"
        ):

            pdf_text = st.session_state.pdf_text

            if len(pdf_text) > 100000:
                pdf_text = pdf_text[:100000]

            prompt = f"""
Read the uploaded PDF.

Create 5 important 5-mark questions
with detailed answers.

Use:

# 📖 5-Mark Questions

### Q1. Question

**Answer:**

Give a well-structured answer
with suitable points.

Create 5 questions.

Answers must be based only on
the PDF.

PDF:

{pdf_text}
"""

            with st.spinner(
                "📖 Creating 5-mark questions..."
            ):

                try:

                    answer = generate_ai(
                        prompt
                    )

                    st.markdown(answer)

                except Exception as e:

                    st.error(
                        f"5-mark error: {e}"
                    )


        # =================================================
        # 10 MARK QUESTIONS
        # =================================================

        if st.button(
            "🏆 Generate 10-Mark Questions"
        ):

            pdf_text = st.session_state.pdf_text

            if len(pdf_text) > 100000:
                pdf_text = pdf_text[:100000]

            prompt = f"""
Read the uploaded PDF carefully.

Create 5 important 10-mark exam questions
with detailed answers.

Use:

# 🏆 10-Mark Questions

### Q1. Question

**Answer:**

Introduction

Main points

Explanation

Conclusion

Create 5 questions.

Answers must be based only on
the uploaded PDF.

PDF:

{pdf_text}
"""

            with st.spinner(
                "🏆 Creating 10-mark questions..."
            ):

                try:

                    answer = generate_ai(
                        prompt
                    )

                    st.markdown(answer)

                except Exception as e:

                    st.error(
                        f"10-mark error: {e}"
                    )


        # =================================================
        # QUIZ FROM PDF
        # =================================================

        if st.button(
            "❓ Generate Quiz From PDF",
            type="primary"
        ):

            pdf_text = st.session_state.pdf_text

            if len(pdf_text) > 100000:
                pdf_text = pdf_text[:100000]

            with st.spinner(
                "❓ Creating quiz from PDF..."
            ):

                try:

                    questions = generate_quiz_from_text(
                        pdf_text,
                        5
                    )

                    st.session_state.pdf_quiz_questions = questions

                    st.session_state.pdf_quiz_answers = {}

                    st.session_state.pdf_quiz_submitted = False

                    st.success(
                        "✅ Quiz created from your PDF!"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"PDF quiz error: {e}"
                    )


        # =================================================
        # SHOW PDF QUIZ
        # =================================================

        if st.session_state.pdf_quiz_questions:

            st.divider()

            st.subheader(
                "🧠 Answer the questions"
            )

            for i, q in enumerate(
                st.session_state.pdf_quiz_questions
            ):

                st.markdown(
                    f"### Q{i + 1}. {q['question']}"
                )

                answer = st.radio(
                    "Choose your answer:",
                    q["options"],
                    key=f"pdf_quiz_{i}"
                )

                st.session_state.pdf_quiz_answers[i] = answer

            if not st.session_state.pdf_quiz_submitted:

                if st.button(
                    "🏆 Submit PDF Quiz",
                    type="primary"
                ):

                    st.session_state.pdf_quiz_submitted = True

                    st.rerun()

            else:

                score = 0

                for i, q in enumerate(
                    st.session_state.pdf_quiz_questions
                ):

                    correct = q["options"][
                        q["answer"]
                    ]

                    selected = (
                        st.session_state.pdf_quiz_answers.get(i)
                    )

                    if selected == correct:

                        score += 1

                total = len(
                    st.session_state.pdf_quiz_questions
                )

                percentage = (
                    score / total
                ) * 100

                st.success(
                    f"🏆 Your Score: {score} / {total}"
                )

                st.metric(
                    "Percentage",
                    f"{percentage:.0f}%"
                )

                if percentage >= 80:

                    st.balloons()

                    st.success(
                        "🎉 Excellent work!"
                    )

                elif percentage >= 50:

                    st.info(
                        "👍 Good job! Keep practicing."
                    )

                else:

                    st.warning(
                        "📚 Keep studying and try again!"
                    )

                st.divider()

                st.subheader(
                    "📖 Answer Review"
                )

                for i, q in enumerate(
                    st.session_state.pdf_quiz_questions
                ):

                    selected = (
                        st.session_state.pdf_quiz_answers.get(i)
                    )

                    correct = q["options"][
                        q["answer"]
                    ]

                    st.markdown(
                        f"### Q{i + 1}. {q['question']}"
                    )

                    if selected == correct:

                        st.success(
                            f"✅ Correct: {correct}"
                        )

                    else:

                        st.error(
                            f"❌ Your answer: {selected}"
                        )

                        st.success(
                            f"✅ Correct answer: {correct}"
                        )

                    st.info(
                        "💡 " + q["explanation"]
                    )


# =========================================================
# STUDY PLAN
# =========================================================

elif st.session_state.tool == "Study Plan":

    st.title("📅 AI Study Planner")

    st.info(
        "Personalized Study Planner will be added next."
    )


# =========================================================
# CHAT
# =========================================================

else:

    current_chat = (
        st.session_state.current_chat
    )

    messages = st.session_state.chats[
        current_chat
    ]

    st.title(
        "🤖 MyAI Learning Assistant"
    )

    st.caption(
        "Your personal AI-powered learning companion"
    )

    st.divider()

    for message in messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    prompt = st.chat_input(
        "Ask me anything about your studies..."
    )

    if prompt:

        messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        if current_chat.startswith(
            "New Chat"
        ):

            title = create_chat_title(
                prompt
            )

            if title not in st.session_state.chats:

                st.session_state.chats[
                    title
                ] = messages

                del st.session_state.chats[
                    current_chat
                ]

                st.session_state.current_chat = title

                current_chat = title

        with st.chat_message("user"):

            st.markdown(prompt)

        conversation = ""

        for message in messages:

            conversation += (
                message["role"]
                + ": "
                + message["content"]
                + "\n"
            )

        with st.chat_message("assistant"):

            try:

                response = client.models.generate_content_stream(
                    model="gemini-3.6-flash",
                    contents=conversation
                )

                answer = ""

                placeholder = st.empty()

                for chunk in response:

                    if chunk.text:

                        answer += chunk.text

                        placeholder.markdown(
                            answer + "▌"
                        )

                placeholder.markdown(
                    answer
                )

            except Exception as e:

                answer = (
                    "Sorry, something went wrong: "
                    + str(e)
                )

                st.error(answer)

        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.session_state.chats[
            current_chat
        ] = messages
