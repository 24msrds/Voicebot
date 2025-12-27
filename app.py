import streamlit as st
import requests
import json
import tempfile
import traceback
from groq import Groq

# --------------------------
# PAGE CONFIG
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
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
MODEL_ID = st.secrets.get("GROQ_MODEL")

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
# SHOW CHAT HISTORY
# --------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --------------------------
# INTENT DETECTION
# --------------------------
def detect_intent(text):
    text = text.lower()
    if any(w in text for w in ["how", "steps", "procedure", "workflow"]):
        return "step_by_step"
    if any(w in text for w in ["define", "what is", "meaning"]):
        return "definition"
    if any(w in text for w in ["code", "error", "bug", "exception"]):
        return "code_help"
    if any(w in text for w in ["explain", "describe", "elaborate"]):
        return "technical_explanation"
    return "general_chat"

# --------------------------
# MEMORY SUMMARIZATION
# --------------------------
def summarize_memory(messages):
    convo = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in messages[-8:]
        if m["role"] != "system"
    )

    r = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": "Summarize briefly for memory."},
            {"role": "user", "content": convo}
        ],
        max_tokens=120
    )
    return r.choices[0].message.content

# --------------------------
# DEEPGRAM STT
# --------------------------
def deepgram_transcribe(audio_bytes):
    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm"
    }
    r = requests.post(url, headers=headers, data=audio_bytes)
    r.raise_for_status()
    data = r.json()
    return data["results"]["channels"][0]["alternatives"][0]["transcript"]

# --------------------------
# DEEPGRAM TTS (INDIAN MALE + CHUNK SAFE)
# --------------------------
def deepgram_tts(text):
    url = "https://api.deepgram.com/v1/speak?model=aura-orion-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }

    def split_text(txt, max_len=700):
        chunks = []
        while len(txt) > max_len:
            split_at = txt.rfind(" ", 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(txt[:split_at])
            txt = txt[split_at:].strip()
        chunks.append(txt)
        return chunks

    audio_bytes = b""

    for chunk in split_text(text):
        payload = {"text": chunk}
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        audio_bytes += r.content

    return audio_bytes

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
        user_text = deepgram_transcribe(f.read())

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
intent = detect_intent(user_text)

st.session_state.messages.append({
    "role": "user",
    "content": f"[Intent: {intent}] {user_text}"
})

with st.chat_message("user"):
    st.write(user_text)

# --------------------------
# MEMORY COMPRESSION
# --------------------------
if len(st.session_state.messages) > 12:
    memory = summarize_memory(st.session_state.messages)
    st.session_state.messages = [
        SYSTEM_PROMPT,
        {"role": "system", "content": f"Conversation memory: {memory}"}
    ]

# --------------------------
# GROQ RESPONSE
# --------------------------
try:
    r = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=st.session_state.messages,
        max_tokens=700
    )
    answer = r.choices[0].message.content
except Exception:
    st.error("LLM error")
    st.text(traceback.format_exc())
    st.stop()

st.session_state.messages.append(
    {"role": "assistant", "content": answer}
)

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
        st.warning("TTS failed")
        st.text(traceback.format_exc())
