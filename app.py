import streamlit as st
import requests
import tempfile
import traceback
import os
import json
import base64
from groq import Groq
from PIL import Image

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

if "image_b64" not in st.session_state:
    st.session_state.image_b64 = None

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
    return any(k in text.lower() for k in keywords)

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
st.sidebar.markdown("### Rahul Memory")
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
# IMAGE → BASE64
# --------------------------
def image_to_base64(image):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image.save(tmp.name)
        with open(tmp.name, "rb") as f:
            return base64.b64encode(f.read()).decode()

# --------------------------
# IMAGE UPLOAD
# --------------------------
st.markdown("### Upload Image (certificate, diagram, screenshot)")
uploaded_image = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, use_column_width=True)
    st.session_state.image_b64 = image_to_base64(image)

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

    audio = b""
    for i in range(0, len(text), 600):
        chunk = text[i:i+600]
        r = requests.post(url, headers=headers, json={"text": chunk})
        r.raise_for_status()
        audio += r.content
    return audio

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
# IMAGE-AWARE RESPONSE
# --------------------------
if st.session_state.image_b64:
    r = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Explain this image clearly and professionally."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{st.session_state.image_b64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=700
    )
    answer = r.choices[0].message.content
    st.session_state.image_b64 = None

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
