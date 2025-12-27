# app.py — Rahul AI (Deepgram STT + TTS, Intent-Aware)

import streamlit as st
import requests
import json
import tempfile
import traceback
from groq import Groq

# --------------------------
# UI
# --------------------------
st.set_page_config(page_title="Rahul AI", layout="centered")
st.title("Rahul AI")
st.write("Ask any question using voice or text.")

# --------------------------
# SESSION STATE
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = False

# --------------------------
# SECRETS
# --------------------------
if "GROQ_API_KEY" not in st.secrets or "DEEPGRAM_API_KEY" not in st.secrets:
    st.error("Missing API keys")
    st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
MODEL_ID = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# SYSTEM PROMPT
# --------------------------
BASE_SYSTEM_PROMPT = (
    "You are Rahul, a highly intelligent AI assistant. "
    "Your name is Rahul. "
    "If asked who you are, reply exactly: My name is Rahul. "
    "Never mention model names or providers."
)

# --------------------------
# SHOW CHAT HISTORY
# --------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --------------------------
# DEEPGRAM STT
# --------------------------
def deepgram_transcribe(audio_file):
    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm",
    }
    r = requests.post(url, headers=headers, data=audio_file)
    r.raise_for_status()
    return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]

# --------------------------
# DEEPGRAM TTS (FREE)
# --------------------------
def deepgram_tts(text):
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"text": text}
    r = requests.post(url, headers=headers, data=json.dumps(payload))
    r.raise_for_status()
    return r.content

# --------------------------
# INTENT DETECTION (MINIMAL)
# --------------------------
def detect_intent(user_text):
    prompt = (
        "Classify the user question into ONE intent:\n"
        "explanation, how_to, comparison, coding, calculation, general.\n\n"
        f"Question: \"{user_text}\"\n\n"
        "Reply with ONLY the intent."
    )

    try:
        r = groq_client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        intent = r.choices[0].message.content.strip().lower()
        return intent if intent in {
            "explanation", "how_to", "comparison",
            "coding", "calculation", "general"
        } else "general"
    except Exception:
        return "general"

# --------------------------
# AUDIO INPUT
# --------------------------
audio = st.audio_input("Speak your question")
user_text = None

if audio and not st.session_state.audio_processed:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    with open(audio_path, "rb") as f:
        user_text = deepgram_transcribe(f)

    st.session_state.audio_processed = True

# --------------------------
# TEXT INPUT
# --------------------------
typed_text = st.chat_input("Type your question and press Enter")

if typed_text:
    user_text = typed_text
    st.session_state.audio_processed = False

if not user_text:
    st.stop()

# --------------------------
# USER MESSAGE
# --------------------------
st.session_state.messages.append({"role": "user", "content": user_text})
with st.chat_message("user"):
    st.write(user_text)

# --------------------------
# INTENT-AWARE RESPONSE
# --------------------------
intent = detect_intent(user_text)

system_prompt = {
    "role": "system",
    "content": (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"The user's intent is: {intent}.\n"
        "Answer accordingly and clearly."
    ),
}

messages = [system_prompt, {"role": "user", "content": user_text}]

try:
    r = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        max_tokens=700,
    )
    answer = r.choices[0].message.content
except Exception:
    st.error("LLM error")
    st.text(traceback.format_exc())
    st.stop()

st.session_state.messages.append({"role": "assistant", "content": answer})
with st.chat_message("assistant"):
    st.write(answer)

# --------------------------
# READ ALOUD
# --------------------------
if st.checkbox("Read aloud", value=True):
    try:
        audio_bytes = deepgram_tts(answer)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception:
        st.error("TTS failed")
        st.text(traceback.format_exc())
