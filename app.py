import streamlit as st
import traceback
from groq import Groq

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(page_title="Rahul AI", layout="centered")
st.title("Rahul AI")
st.write("Ask any technical question using text.")

# --------------------------
# SECRETS (STRICT)
# --------------------------
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MODEL_ID = "llama-3.3-70b-versatile"  # FIXED

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

# --------------------------
# SIDEBAR CONTROLS
# --------------------------
st.sidebar.markdown("### 🧠 Controls")

if st.sidebar.button("🗑️ Clear Conversation"):
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
    if any(x in t for x in ["code", "python", "java", "c++", "sql", "program"]):
        return "code"
    return "chat"

# --------------------------
# CALCULATOR (SAFE)
# --------------------------
def calculator(expr):
    try:
        expr = expr.replace("calculate", "").strip()
        allowed = "0123456789+-*/(). %"
        if not all(c in allowed for c in expr):
            return "❌ Invalid characters in expression."
        return f"✅ Result: {eval(expr)}"
    except Exception as e:
        return f"❌ Calculation error: {e}"

# --------------------------
# USER INPUT
# --------------------------
user_text = st.chat_input("Type your question and press Enter")

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
# ROUTING LOGIC
# --------------------------
intent = detect_intent(user_text)

try:
    if intent == "calculator":
        answer = calculator(user_text)

    elif intent == "code":
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior software engineer. "
                        "Return clean, correct, well-formatted code only. "
                        "Add brief comments where necessary."
                    )
                },
                {"role": "user", "content": user_text}
            ],
            max_tokens=600
        )
        answer = response.choices[0].message.content

    else:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=st.session_state.messages[-6:],  # safe context window
            max_tokens=500
        )
        answer = response.choices[0].message.content

except Exception:
    st.error("Groq API Error")
    st.text(traceback.format_exc())
    st.stop()

# --------------------------
# ASSISTANT MESSAGE
# --------------------------
st.session_state.messages.append(
    {"role": "assistant", "content": answer}
)

with st.chat_message("assistant"):
    st.write(answer)
