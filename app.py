# app.py — Rahul AI (Duplicate-safe GPT-style assistant)

import streamlit as st
import requests
import json
import tempfile
import traceback

# --------------------------
# Lazy Groq import
# --------------------------
try:
    from groq import Groq
except Exception:
    Groq = None

# --------------------------
# UI CONFIG
# --------------------------
st.set_page_config(page_title="Rahul AI", layout="centered")
st.title(" Rahul AI")
st.write(
    "Ask any technical question. I can help with AI, ML, DL, NLP, "
    "Data Science, Algorithms, and Programming."
)

# --------------------------
# SESSION STATE INIT
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_input" not in st.session_state:
    st.session_state.last_input = None

# --------------------------
# SECRETS CHECK
# --------------------------
if "GROQ_API_KEY" not in st.secrets or "DEEPGRAM_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY or DEEPGRAM_API_KEY.")
    st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
MODEL_ID = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# --------------------------
# INIT GROQ CLIENT
# --------------------------
if Groq is None:
    st.error("Groq SDK not installed. Run: pip install groq")
    st.stop()

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# SYSTEM PROMPT (CORE BRAIN)
# --------------------------
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are Rahul, a highly intelligent technical assistant.

Identity:
- Your name is Rahul.
- If asked who you are, reply exactly: "My name is Rahul."

Capabilities:
- Artificial Intelligence
- Machine Learning
- Deep Learning
- Natural Language Processing
- Data Science
- Algorithms
- Statistics
- Programming

Rules:
- Automatically infer the technical domain.
- Explain concepts clearly and step by step.
- Use examples where helpful.
- Never mention model names, Groq, or LLaMA.
"""
}

if not st.session_state.messages:
    st.session_state.messages.append(SYSTEM_PROMPT)

# --------------------------
# INPUT UI
# --------------------------
audio = st.audio_input("🎙️ Speak")

with st.form(key="text_form", clear_on_submit=True):
    text_input = st.text_input(" Or type your question")
    submitted = st.form_submit_button("Send")

# --------------------------
# DEEPGRAM STT
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
# GET USER INPUT (SAFE)
# --------------------------
user_text = None

if audio:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    with open(audio_path, "rb") as f:
        user_text = deepgram_transcribe(f)

elif submitted and text_input.strip():
    user_text = text_input.strip()

# --------------------------
# DUPLICATE PREVENTION
# --------------------------
if not user_text or user_text == st.session_state.last_input:
    st.stop()

st.session_state.last_input = user_text

# --------------------------
# DISPLAY USER MESSAGE
# --------------------------
st.markdown("###  You")
st.write(user_text)

st.session_state.messages.append(
    {"role": "user", "content": user_text}
)

# --------------------------
# GROQ COMPLETION
# --------------------------
try:
    response = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=st.session_state.messages,
        max_tokens=700
    )
    answer = response.choices[0].message.content
except Exception:
    st.error("Groq API error")
    st.text(traceback.format_exc())
    st.stop()

st.session_state.messages.append(
    {"role": "assistant", "content": answer}
)

# --------------------------
# DISPLAY ANSWER
# --------------------------
st.markdown("###  Rahul")
st.write(answer)

# --------------------------
# DEEPGRAM TTS
# --------------------------
if st.checkbox(" Read aloud", value=True):
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
# MEMORY VIEW
# --------------------------
with st.expander(" Conversation Memory"):
    for msg in st.session_state.messages:
        role = "You" if msg["role"] == "user" else "Rahul"
        st.markdown(f"**{role}:** {msg['content']}")
