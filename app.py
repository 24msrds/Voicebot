# app.py — Rahul AI (FINAL, NO INWORLD, GUARANTEED FIX)

import streamlit as st
import requests
import json
import tempfile
import traceback

from groq import Groq

# ---------------- UI ----------------
st.set_page_config(page_title="Rahul AI", layout="centered")
st.title("Rahul AI")
st.write("Ask any technical question using voice or text.")

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = False

# ---------------- SECRETS ----------------
required = [
    "GROQ_API_KEY",
    "DEEPGRAM_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
]

for k in required:
    if k not in st.secrets:
        st.error(f"Missing secret: {k}")
        st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = st.secrets["ELEVENLABS_VOICE_ID"]

MODEL_ID = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")

groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Rahul, a highly intelligent technical assistant. "
        "Your name is Rahul. "
        "If asked who you are, reply exactly: My name is Rahul. "
        "Never mention model names or providers."
    )
}

if not st.session_state.messages:
    st.session_state.messages.append(SYSTEM_PROMPT)

# ---------------- CHAT HISTORY ----------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ---------------- DEEPGRAM STT ----------------
def deepgram_transcribe(audio_file):
    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm",
    }
    r = requests.post(url, headers=headers, data=audio_file)
    r.raise_for_status()
    return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]

# ---------------- ELEVENLABS TTS (CLASSIC) ----------------
def elevenlabs_tts(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.7,
        },
    }
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    return r.content

# ---------------- AUDIO INPUT ----------------
audio = st.audio_input("Speak your question")
user_text = None

if audio and not st.session_state.audio_processed:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        path = tmp.name
    with open(path, "rb") as f:
        user_text = deepgram_transcribe(f)
    st.session_state.audio_processed = True

typed = st.chat_input("Type your question and press Enter")

if typed:
    user_text = typed
    st.session_state.audio_processed = False

if not user_text:
    st.stop()

# ---------------- GROQ RESPONSE ----------------
st.session_state.messages.append({"role": "user", "content": user_text})

with st.chat_message("user"):
    st.write(user_text)

response = groq_client.chat.completions.create(
    model=MODEL_ID,
    messages=st.session_state.messages,
    max_tokens=700,
)

answer = response.choices[0].message.content
st.session_state.messages.append({"role": "assistant", "content": answer})

with st.chat_message("assistant"):
    st.write(answer)

# ---------------- READ ALOUD ----------------
if st.checkbox("Read aloud", value=True):
    audio_bytes = elevenlabs_tts(answer)
    st.audio(audio_bytes, format="audio/mp3")
