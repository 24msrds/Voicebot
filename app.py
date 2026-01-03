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

if not st.session_state.messages:
    st.session_state.messages.append(SYSTEM_PROMPT)

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
    if any(w in t for w in ["how", "steps", "procedure"]):
        return "step_by_step"
    if any(w in t for w in ["define", "what is", "meaning"]):
        return "definition"
    return "general_chat"

# --------------------------
# TOOL: CALCULATOR
# --------------------------
def calculator(expr):
    try:
        allowed = "0123456789+-*/(). "
        if not all(c in allowed for c in expr):
            return "Invalid characters in expression."
        return f"Result: {eval(expr)}"
    except Exception as e:
        return f"Calculation error: {e}"

# --------------------------
# TOOL: SAFE PYTHON EXECUTION
# --------------------------
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
        safe_locals = {}
        exec(code, safe_globals, safe_locals)
        return "Code executed successfully."
    except Exception as e:
        return f"Code execution error: {e}"

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
# DEEPGRAM TTS (CHUNK SAFE)
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
typed_text = st.chat_input("Type your question and press Enter")
if typed_text:
    user_text = typed_text
    st.session_state.audio_processed = False

if not user_text:
    st.session_state.audio_processed = False
    st.stop()

# --------------------------
# USER MESSAGE
# --------------------------
intent = detect_intent(user_text)
st.session_state.messages.append({"role": "user", "content": user_text})

with st.chat_message("user"):
    st.write(user_text)

# --------------------------
# TOOL ROUTING
# --------------------------
if intent == "calculator":
    answer = calculator(user_text.replace("calculate", "").strip())

elif intent == "code":
    answer = run_python(user_text)

else:
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
st.session_state.audio_processed = False
