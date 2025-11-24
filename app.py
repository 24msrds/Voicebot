import streamlit as st
import requests
import json
from groq import Groq
import tempfile

# --------------------------
# Load API keys
# --------------------------
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------
# Streamlit UI
# --------------------------
st.set_page_config(page_title="Ragul's Interview Voice Bot (FREE)", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot (FREE)")
st.write("Ask any interview-style question. I'll answer like **Ragul B**.")

audio = st.audio_input("🎙️ Speak your interview question:")

if audio:
    st.audio(audio)

    # Save raw uploaded file using correct extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    # --------------------------
    # STEP 1 — Deepgram Transcription (for WEBM)
    # --------------------------
    deepgram_url = "https://api.deepgram.com/v1/listen"

    with open(audio_path, "rb") as f:
        dg_response = requests.post(
            deepgram_url,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/webm"   # IMPORTANT!!
            },
            data=f
        )

    dg_data = dg_response.json()

    # Extract transcript safely
    try:
        user_text = dg_data["results"]["channels"][0]["alternatives"][0]["transcript"]
    except Exception as e:
        st.error("❌ Deepgram could not read your audio. Try speaking clearly.")
        st.subheader("Deepgram Debug Response:")
        st.json(dg_data)
        st.stop()

    st.write("### **You asked:**", user_text)

    # --------------------------
    # STEP 2 — Groq Llama3 Chat Completion
    # --------------------------
    prompt = f"""
    Answer the following question as if you are Ragul B.
    Speak in first person, confident and interview-friendly.

    Question: {user_text}
    """

    # model fix → use simple valid name
   chat_reply = groq_client.chat.completions.create(
    model="llama3-8b-8192",
    messages=[
        {"role": "user", "content": prompt}
    ]
)


    # --------------------------
    # STEP 3 — Deepgram TTS
    # --------------------------
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

