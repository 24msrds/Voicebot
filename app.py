# app.py — Rahul AI (FINAL STABLE VERSION)

import streamlit as st
import requests
import json
import tempfile
import traceback

try:
    from groq import Groq
except Exception:
    Groq = None

# --------------------------
# UI
# --------------------------
st.set_page_config(page_title="Rahul AI", layout="centered")
st.title("Rahul AI")
st.write("Ask any technical question using voice or text.")

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
required_keys = [
    "GROQ_API_KEY",
    "DEEPGRAM_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID"
]

for key in required_keys:
    if key not in st.secrets:
        st.error(f"Missing secret: {key}")
        st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = st.secrets["ELEVENLABS_VOICE_ID"]

MODEL_ID = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# --------------------------
# INIT GROQ
# --------------------------
if Groq is None:
    st.error("Groq SDK not installed")
    st.stop()

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# SYSTEM PROMPT
# --------------------------
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
# DEEPGRAM STT (VOICE INPUT)
# --------------------------
def deepgram_transcribe(audio_file):
    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm"
    }
    response = requests.post(url, headers=headers, data=audio_file)
    response.raise_for_status()
    data = response.json()
    return data["results"]["channels"][0]["alternatives"][0]["transcript"]

# --------------------------
# ELEVENLABS CLASSIC TTS (VOICE OUTPUT)
# --------------------------
def elevenlabs_tts(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.7
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.content  # raw MP3 bytes

# --------------------------
# AUDIO INPUT (MIC)
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

# --------------------------
# STOP IF NO INPUT
# --------------------------
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
# READ ALOUD (YOUR VOICE)
# --------------------------
if st.checkbox("Read aloud", value=True):
    try:
        audio_bytes = elevenlabs_tts(answer)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception:
        st.error("TTS failed")
        st.text(traceback.format_exc())
