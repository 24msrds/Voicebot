# app.py — Rahul AI Bot (GPT-style NLP Assistant)

import streamlit as st
import requests
import json
import tempfile
import traceback

# --------------------------
# Lazy Groq import (SAME)
# --------------------------
try:
    from groq import Groq
except Exception:
    Groq = None

# --------------------------
# UI CONFIG
# --------------------------
st.set_page_config(page_title="Rahul AI Bot", layout="centered")
st.title("🧠 Rahul AI Bot")
st.write("Voice + Text AI assistant for NLP tasks (GPT-style)")

# --------------------------
# SESSION MEMORY (GPT CONTEXT)
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------
# SECRETS CHECK (SAME)
# --------------------------
if "GROQ_API_KEY" not in st.secrets or "DEEPGRAM_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY or DEEPGRAM_API_KEY in secrets.")
    st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
MODEL_ID = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# --------------------------
# INIT GROQ CLIENT (SAME)
# --------------------------
if Groq is None:
    st.error("Groq SDK not installed. Run: pip install groq")
    st.stop()

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# NLP TASK SELECTOR
# --------------------------
task = st.selectbox(
    "🛠 Select NLP Task",
    [
        "General Chat / Text Generation",
        "Text Summarization",
        "Sentiment Analysis",
        "Grammar Correction",
        "Text Rewriting",
        "Keyword Extraction",
        "Explain in Simple Terms"
    ]
)

# --------------------------
# CREATIVITY CONTROL
# --------------------------
temperature = st.slider("🎨 Creativity", 0.1, 1.2, 0.7)

# --------------------------
# INPUT (VOICE + TEXT)
# --------------------------
audio = st.audio_input("🎙️ Speak")
text_input = st.text_area("✍️ Or type text")

# --------------------------
# PROMPT ENGINE (GPT CORE)
# --------------------------
def build_prompt(task, text):
    if task == "General Chat / Text Generation":
        return text

    if task == "Text Summarization":
        return f"Summarize the following text clearly:\n{text}"

    if task == "Sentiment Analysis":
        return f"""
Analyze the sentiment of the text.
Return:
- Sentiment (Positive / Negative / Neutral)
- Confidence %
- Short explanation

Text:
{text}
"""

    if task == "Grammar Correction":
        return f"Correct grammar and improve clarity:\n{text}"

    if task == "Text Rewriting":
        return f"Rewrite the text in a professional way:\n{text}"

    if task == "Keyword Extraction":
        return f"Extract key important words:\n{text}"

    if task == "Explain in Simple Terms":
        return f"Explain this in very simple terms:\n{text}"

# --------------------------
# DEEPGRAM SPEECH → TEXT (SAME)
# --------------------------
def deepgram_transcribe(audio_file):
    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm"
    }
    response = requests.post(url, headers=headers, data=audio_file)
    data = response.json()
    return data["results"]["channels"][0]["alternatives"][0]["transcript"]

# --------------------------
# GET USER TEXT
# --------------------------
user_text = ""

if audio:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    with open(audio_path, "rb") as f:
        user_text = deepgram_transcribe(f)

elif text_input.strip():
    user_text = text_input.strip()

if not user_text:
    st.stop()

st.markdown("### 🧑 You")
st.write(user_text)

# --------------------------
# BUILD GPT MESSAGE
# --------------------------
prompt = build_prompt(task, user_text)

st.session_state.messages.append(
    {"role": "user", "content": prompt}
)

# --------------------------
# GROQ CHAT COMPLETION (SAME)
# --------------------------
try:
    response = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=st.session_state.messages,
        temperature=temperature,
        max_tokens=600
    )
    answer = response.choices[0].message.content
except Exception:
    st.error("Groq API Error")
    st.text(traceback.format_exc())
    st.stop()

st.session_state.messages.append(
    {"role": "assistant", "content": answer}
)

# --------------------------
# OUTPUT
# --------------------------
st.markdown("### 🤖 Rahul AI Bot")
st.write(answer)

# --------------------------
# DEEPGRAM TEXT → SPEECH (SAME)
# --------------------------
if st.checkbox("🔊 Read aloud", value=True):
    tts_url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    tts_response = requests.post(
        tts_url,
        headers={
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps({"text": answer})
    )
    if tts_response.status_code == 200:
        st.audio(tts_response.content, format="audio/mp3")

# --------------------------
# CONVERSATION MEMORY VIEW
# --------------------------
with st.expander("📝 Conversation Memory"):
    for msg in st.session_state.messages:
        role = "You" if msg["role"] == "user" else "Rahul AI"
        st.markdown(f"**{role}:** {msg['content']}")
