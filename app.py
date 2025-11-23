import streamlit as st
import requests
import json
from groq import Groq
import tempfile

# Load API keys
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Ragul Voice Bot", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot")
st.write("Ask your question — I will answer like **Ragul B**.")

# Mic input
audio = st.audio_input("🎙️ Speak your interview question:")

if audio:
    st.audio(audio)

    # Save audio to a temporary WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    # ---- STEP 1: Deepgram Transcription ----
    deepgram_url = "https://api.deepgram.com/v1/listen"

    with open(audio_path, "rb") as f:
        dg_response = requests.post(
            deepgram_url,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav"
            },
            data=f
        )

    dg_data = dg_response.json()

    # Check if transcript exists
    try:
        user_text = dg_data["results"]["channels"][0]["alternatives"][0]["transcript"]
    except:
        st.error("❌ Could not transcribe audio. Please speak clearly and try again.")
        st.json(dg_data)
        st.stop()

    st.write("### **You asked:**", user_text)

    # ---- STEP 2: Generate Answer (Groq) ----
    prompt = f"""
    Answer the following question as if you are Ragul B.
    Speak in first person, confidently and interview-friendly.

    Question: {user_text}
    """

    chat_completion = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = chat_completion.choices[0].message["content"]
    st.write("### **My Answer:**")
    st.write(answer)

    # ---- STEP 3: Text → Speech using Deepgram ----
    tts_url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"

    tts_response = requests.post(
        tts_url,
        headers={
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps({"text": answer})
    )

    st.audio(tts_response.content, format="audio/mp3")
