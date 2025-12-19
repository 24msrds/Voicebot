# app.py — Rahul AI (Clean version without symbols)

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
st.title("Rahul AI")
st.write(
    "Ask any technical question. I can help with AI, ML, DL, NLP, "
    "Data Science, Algorithms, and Programming."
)

# --------------------------
# SESSION STATE INIT
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

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
    st.error("Groq SDK not installed. Run pip install groq")
    st.stop()

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# SYSTEM PROMPT
# --------------------------
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are Rahul, a highly intelligent technical assistant.

Identity:
- Your name is Rahul.
- If asked who you are, reply exactly: My name is Rahul.

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
# DISPLAY CHAT HISTORY
# --------------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# --------------------------
# VOICE INPUT
# --------------------------
audio = st.audio_input("Speak")

def deepgram_transcribe(audio_file):
    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm"
    }
    response = requests.post(url, headers=headers, data=audio_file)
    data = response.json()
    return data["results"]["channels"][0]["alternatives"][0]["transcript"]

user_text = None

if audio:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    with open(audio_path, "rb") as f:
        user_text = deepgram_transcribe(f)

# --------------------------
# TEXT INPUT
# --------------------------
typed_text = st.chat_input("Type your question and press Enter")

if typed_text:
    user_text = typed_text

if not user_text:
    st.stop()

# --------------------------
# ADD USER MESSAGE
# --------------------------
st.session_state.messages.append(
    {"role": "user", "content": user_text}
)

with st.chat_message("user"):
    st.write(user_text)

# --------------------------
# GROQ RESPONSE
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

with st.chat_message("assistant"):
    st.write(answer)

# --------------------------
# DEEPGRAM TEXT TO SPEECH
# --------------------------
read_aloud = st.checkbox("Read aloud", value=True)

if read_aloud:
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
