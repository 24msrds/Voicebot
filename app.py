import streamlit as st
import requests
import tempfile
import json

# Load API Keys
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

st.set_page_config(page_title="Ragul's Voice Bot", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot (FREE Version)")
st.write("Ask me any interview-style question. I will answer as **Ragul B**.")

# Record voice
audio = st.audio_input("🎙️ Ask your question:")

if audio:
    st.audio(audio)

    # Save audio to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    # --------------------------
    # 🔊 STEP 1 → Deepgram STT
    # --------------------------
    with open(audio_path, "rb") as f:
        dg_response = requests.post(
            "https://api.deepgram.com/v1/listen",
            headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
            files={"audio": f}
        )

    user_text = dg_response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    st.write("### **You asked:**", user_text)

    # --------------------------
    # 🧠 STEP 2 → GROQ Llama3 Chat
    # --------------------------
    groq_payload = {
        "model": "llama3-70b",
        "messages": [
            {
                "role": "user",
                "content": f"""
                Answer the following question as if you are Ragul B.
                Speak confidently in first person.

                Question: {user_text}
                """
            }
        ]
    }

    groq_response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json=groq_payload
    )

    answer = groq_response.json()["choices"][0]["message"]["content"]

    st.write("### **My Answer:**")
    st.write(answer)
