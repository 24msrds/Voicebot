# app.py — Rahul AI (Intent Detection + Voice, FINAL)

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
required_keys = [
    "GROQ_API_KEY",
    "DEEPGRAM_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
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

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# SYSTEM PROMPT (BASE IDENTITY)
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
    response = requests.post(url, headers=headers, data=audio_file)
    response.raise_for_status()
    return response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]

# --------------------------
# ELEVENLABS TTS (TRAINED / INDIAN VOICE)
# --------------------------
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
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.content

# --------------------------
# INTENT DETECTION (MINIMAL)
# --------------------------
def detect_intent(user_text):
    prompt = (
        "Classify the user question into ONE of these intents:\n"
        "explanation, how_to, comparison, coding, calculation, general.\n\n"
        f"Question: \"{user_text}\"\n\n"
        "Reply with ONLY the intent."
    )

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        intent = response.choices[0].message.content.strip().lower()
        allowed = {
            "explanation",
            "how_to",
            "comparison",
            "coding",
            "calculation",
            "general",
        }
        return intent if intent in allowed else "general"
    except Exception:
        return "general"

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

if not user_text:
    st.stop()

# --------------------------
# DISPLAY USER MESSAGE
# --------------------------
st.session_state.messages.append({"role": "user", "content": user_text})
with st.chat_message("user"):
    st.write(user_text)

# --------------------------
# INTENT-AWARE RESPONSE
# --------------------------
intent = detect_intent(user_text)

guided_system_prompt = {
    "role": "system",
    "content": (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"The user's intent is: {intent}.\n"
        "Respond as follows:\n"
        "- explanation: clear, structured explanation\n"
        "- how_to: step-by-step guidance\n"
        "- comparison: concise comparison (table or bullets)\n"
        "- coding: correct code with brief explanation\n"
        "- calculation: short, direct answer\n"
        "- general: normal helpful response\n"
        "Never mention intent explicitly."
    ),
}

messages = [
    guided_system_prompt,
    {"role": "user", "content": user_text},
]

try:
    response = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        max_tokens=700,
    )
    answer = response.choices[0].message.content
except Exception:
    st.error("LLM error")
    st.text(traceback.format_exc())
    st.stop()

st.session_state.messages.append({"role": "assistant", "content": answer})

with st.chat_message("assistant"):
    st.write(answer)

# --------------------------
# READ ALOUD (OPTIONAL)
# --------------------------
if st.checkbox("Read aloud", value=True):
    try:
        audio_bytes = elevenlabs_tts(answer)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception:
        st.error("TTS failed")
        st.text(traceback.format_exc())
