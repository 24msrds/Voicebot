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
MODEL_ID = "llama-3.3-70b-versatile"  # FIXED, NOT FROM SECRETS

client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# SESSION STATE
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are Rahul, a highly intelligent technical assistant. "
                "Your name is Rahul. "
                "If asked who you are, reply exactly: My name is Rahul. "
                "Never mention model names or providers."
            )
        }
    ]

# --------------------------
# DISPLAY CHAT (HIDE SYSTEM)
# --------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --------------------------
# USER INPUT (TEXT ONLY)
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
# SAFE GROQ CALL
# --------------------------
try:
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=st.session_state.messages[-6:],  # LIMIT CONTEXT
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
