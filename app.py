import streamlit as st
import requests
import tempfile
import traceback
import os
import json
from groq import Groq

# IMAGE / OCR IMPORTS
from PIL import Image
import pytesseract
import cv2
import numpy as np

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(page_title="Rahul AI", layout="centered")
st.title("Rahul AI")
st.write("Ask any technical question using voice, text, or images.")

# --------------------------
# MEMORY FILE
# --------------------------
MEMORY_FILE = "rahul_memory.json"

# --------------------------
# SESSION STATE
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = False

if "image_text" not in st.session_state:
    st.session_state.image_text = None

if "persistent_memory" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            st.session_state.persistent_memory = json.load(f)
    else:
        st.session_state.persistent_memory = []

# --------------------------
# SECRETS
# --------------------------
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
MODEL_ID = st.secrets.get("GROQ_MODEL")

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# MEMORY HELPERS
# --------------------------
def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(st.session_state.persistent_memory, f, indent=2)

def should_remember(text):
    keywords = [
        "i am", "i'm", "my project", "working on",
        "i prefer", "remember", "my goal", "my aim"
    ]
    t = text.lower()
    return any(k in t for k in keywords)

# --------------------------
# SYSTEM PROMPT (HIDDEN)
# --------------------------
memory_context = "\n".join(st.session_state.persistent_memory)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Rahul, a highly intelligent technical assistant.\n"
        "Your name is Rahul.\n"
        "If asked who you are, reply exactly: My name is Rahul.\n"
        "Never mention model names or providers.\n\n"
        "Long-term memory about the user:\n"
        f"{memory_context}"
    )
}

if not st.session_state.messages:
    st.session_state.messages.append(SYSTEM_PROMPT)

# --------------------------
# SIDEBAR MEMORY CONTROL
# --------------------------
st.sidebar.markdown("### 🧠 Rahul Memory")
if st.sidebar.button("Clear Memory"):
    st.session_state.persistent_memory = []
    save_memory()
    st.sidebar.success("Memory cleared")

# --------------------------
# SHOW CHAT HISTORY (HIDE SYSTEM)
# --------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --------------------------
# INTENT DETECTION
# --------------------------
def detect_intent(text):
    t = text.lower()
    if any(w in t for w in ["calculate", "+", "-", "*", "/"]):
        return "calculator"
    if any(w in t for w in ["print", "for", "while", "range"]):
        return "code"
    return "chat"

# --------------------------
# TOOLS
# --------------------------
def calculator(expr):
    try:
        allowed = "0123456789+-*/(). "
        if not all(c in allowed for c in expr):
            return "Invalid characters."
        return f"Result: {eval(expr)}"
    except Exception as e:
        return f"Calculation error: {e}"

def run_python(code):
    try:
        safe_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "sum": sum,
                "min": min,
                "max": max
            }
        }
        exec(code, safe_globals, {})
        return "Code executed successfully."
    except Exception as e:
        return f"Code error: {e}"

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
    return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]

# --------------------------
# DEEPGRAM TTS
# --------------------------
def deepgram_tts(text):
    url = "https://api.deepgram.com/v1/speak?model=aura-orion-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }

    def split_text(t, n=700):
        out = []
        while len(t) > n:
            i = t.rfind(" ", 0, n)
            if i == -1:
                i = n
            out.append(t[:i])
            t = t[i:].strip()
        out.append(t)
        return out

    audio = b""
    for chunk in split_text(text):
        r = requests.post(url, headers=headers, json={"text": chunk})
        r.raise_for_status()
        audio += r.content
    return audio

# --------------------------
# IMAGE OCR
# --------------------------
def extract_text_from_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray).strip()

# --------------------------
# IMAGE UPLOAD
# --------------------------
st.markdown("### 🖼️ Upload Image")
uploaded_image = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, use_column_width=True)
    st.session_state.image_text = extract_text_from_image(image)

# --------------------------
# AUDIO INPUT
# --------------------------
audio = st.audio_input("Speak your question")
user_text = None

if audio and not st.session_state.audio_processed:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
    with open(tmp.name, "rb") as f:
        user_text = deepgram_transcribe(f.read())
    st.session_state.audio_processed = True

# --------------------------
# TEXT INPUT
# --------------------------
typed_text = st.chat_input("Type your question")
if typed_text:
    user_text = typed_text
    st.session_state.audio_processed = False

if not user_text:
    st.session_state.audio_processed = False
    st.stop()

# --------------------------
# STORE MEMORY
# --------------------------
if should_remember(user_text):
    st.session_state.persistent_memory.append(user_text)
    save_memory()

# --------------------------
# USER MESSAGE
# --------------------------
st.session_state.messages.append({"role": "user", "content": user_text})
with st.chat_message("user"):
    st.write(user_text)

# --------------------------
# RESPONSE
# --------------------------
if st.session_state.image_text:
    prompt = (
        "Explain the following image:\n\n"
        f"{st.session_state.image_text}\n\n"
        f"User question: {user_text}"
    )
    r = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )
    answer = r.choices[0].message.content
    st.session_state.image_text = None
else:
    intent = detect_intent(user_text)
    if intent == "calculator":
        answer = calculator(user_text.replace("calculate", "").strip())
    elif intent == "code":
        answer = run_python(user_text)
    else:
        r = groq_client.chat.completions.create(
            model=MODEL_ID,
            messages=st.session_state.messages,
            max_tokens=700
        )
        answer = r.choices[0].message.content

# --------------------------
# ASSISTANT MESSAGE
# --------------------------
st.session_state.messages.append({"role": "assistant", "content": answer})
with st.chat_message("assistant"):
    st.write(answer)

# --------------------------
# READ ALOUD
# --------------------------
if st.checkbox("Read aloud", value=True):
    try:
        st.audio(deepgram_tts(answer), format="audio/mp3")
    except Exception:
        st.warning("TTS failed")

st.session_state.audio_processed = False
