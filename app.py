import streamlit as st
import requests
import tempfile
import traceback
from groq import Groq

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(page_title="Rahul AI", layout="centered")
st.title("Rahul AI")
st.write("Ask any technical question using text or voice.")

# --------------------------
# SECRETS
# --------------------------
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
MODEL_ID = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# SYSTEM PROMPT (HIDDEN)
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

# --------------------------
# SESSION STATE
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [SYSTEM_PROMPT]

if "audio_used" not in st.session_state:
    st.session_state.audio_used = False

# --------------------------
# SIDEBAR
# --------------------------
st.sidebar.markdown("### Controls")

if st.sidebar.button(" Clear Conversation"):
    st.session_state.messages = [SYSTEM_PROMPT]
    st.sidebar.success("Conversation cleared")

# --------------------------
# DISPLAY CHAT (HIDE SYSTEM)
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
    if any(x in t for x in ["calculate", "+", "-", "*", "/", "%"]):
        return "calculator"
    if any(x in t for x in ["code", "python", "java", "sql", "program"]):
        return "code"
    return "chat"

# --------------------------
# CALCULATOR
# --------------------------
def calculator(expr):
    try:
        expr = expr.replace("calculate", "").strip()
        allowed = "0123456789+-*/(). %"
        if not all(c in allowed for c in expr):
            return "Invalid characters."
        return f"Result: {eval(expr)}"
    except Exception as e:
        return f"Calculation error: {e}"

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
# DEEPGRAM TTS (INDIAN-FRIENDLY MALE)
# --------------------------
def deepgram_tts(text):
    url = "https://api.deepgram.com/v1/speak?model=aura-orion-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }

    def split_text(t, n=700):
        chunks = []
        while len(t) > n:
            i = t.rfind(" ", 0, n)
            if i == -1:
                i = n
            chunks.append(t[:i])
            t = t[i:].strip()
        chunks.append(t)
        return chunks

    audio = b""
    for chunk in split_text(text):
        r = requests.post(url, headers=headers, json={"text": chunk})
        r.raise_for_status()
        audio += r.content

    return audio

# --------------------------
# AUDIO INPUT
# --------------------------
audio = st.audio_input("Speak your question")
user_text = None

if audio and not st.session_state.audio_used:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
    with open(tmp.name, "rb") as f:
        user_text = deepgram_transcribe(f.read())
    st.session_state.audio_used = True

# --------------------------
# TEXT INPUT
# --------------------------
typed_text = st.chat_input("Type your question and press Enter")

if typed_text:
    user_text = typed_text
    st.session_state.audio_used = False

if not user_text:
    st.stop()

# --------------------------
# USER MESSAGE
# --------------------------
st.session_state.messages.append({"role": "user", "content": user_text})

with st.chat_message("user"):
    st.write(user_text)

# --------------------------
# RESPONSE
# --------------------------
intent = detect_intent(user_text)

try:
    if intent == "calculator":
        answer = calculator(user_text)

    elif intent == "code":
        r = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "Return clean, correct code only."},
                {"role": "user", "content": user_text}
            ],
            max_tokens=600
        )
        answer = r.choices[0].message.content

    else:
        r = client.chat.completions.create(
            model=MODEL_ID,
            messages=st.session_state.messages[-6:],
            max_tokens=500
        )
        answer = r.choices[0].message.content

except Exception:
    st.error("Groq API Error")
    st.text(traceback.format_exc())
    st.stop()

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

# --------------------------
# RESET
# --------------------------
st.session_state.audio_used = False
