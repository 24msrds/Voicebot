import streamlit as st
import requests
import json
import tempfile
from groq import Groq

# --- Load secrets (set these in Streamlit Secrets) ---
# In Streamlit secrets: 
# GROQ_API_KEY = "gsk_...."
# DEEPGRAM_API_KEY = "dg_...."
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
DEEPGRAM_API_KEY = st.secrets.get("DEEPGRAM_API_KEY")

if not GROQ_API_KEY or not DEEPGRAM_API_KEY:
    st.error("Missing API keys. Add GROQ_API_KEY and DEEPGRAM_API_KEY to Streamlit Secrets.")
    st.stop()

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Ragul Voice Bot", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot (FREE)")
st.write("Ask any interview-style question. I'll answer like **Ragul B**.")

# Record audio from microphone
audio = st.audio_input("🎙️ Speak your interview question:")

if not audio:
    st.info("Press the microphone and record your question. Then press Stop.")
    st.stop()

# Play back the recorded audio for confirmation
st.audio(audio)

# Save audio to temporary file for Deepgram
with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
    tmp.write(audio.read())
    tmp_path = tmp.name

# -------------- STEP 1 — Deepgram Transcription --------------
def transcribe_with_deepgram(file_path, deepgram_key):
    url = "https://api.deepgram.com/v1/listen"
    headers = {"Authorization": f"Token {deepgram_key}"}
    with open(file_path, "rb") as f:
        files = {"file": f}
        resp = requests.post(url, headers=headers, files=files, timeout=30)
    return resp

try:
    dg_resp = transcribe_with_deepgram(tmp_path, DEEPGRAM_API_KEY)
except Exception as e:
    st.error("Network error when contacting Deepgram.")
    st.exception(e)
    st.stop()

# parse Deepgram result safely
try:
    dg_json = dg_resp.json()
except Exception:
    st.error("Deepgram returned a non-JSON response. See raw text below.")
    st.code(dg_resp.text)
    st.stop()

# Make sure transcript exists
user_text = None
try:
    user_text = dg_json["results"]["channels"][0]["alternatives"][0]["transcript"]
except Exception:
    st.error("Could not extract transcript from Deepgram response. See full response below for debugging.")
    st.json(dg_json)
    st.stop()

if not user_text or user_text.strip() == "":
    st.error("No speech detected in the recording. Please speak clearly and try again.")
    st.stop()

st.write("### **You asked:**")
st.write(user_text)

# -------------- STEP 2 — GROQ Llama Chat --------------
prompt = f"""
Answer the following question as if you are Ragul B.
Speak in first person, confidently and interview-friendly.

Question: {user_text}
"""

# Try a safe model name; if it errors, show GROQ response for debugging
model_candidates = ["llama3-8b", "llama3-70b"]
answer = None

for model_name in model_candidates:
    try:
        chat_completion = groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = chat_completion.choices[0].message["content"]
        break
    except Exception as e:
        # Show the first API error in the app logs (developer message)
        # but continue to try next model
        try:
            err_text = e.response.text
        except Exception:
            err_text = str(e)
        st.warning(f"Model {model_name} returned an error (trying next model).")
        st.text(err_text[:1000])  # show up to first 1000 chars
        continue

if answer is None:
    st.error("All GROQ model calls failed. See messages above.")
    st.stop()

st.write("### **My Answer:**")
st.write(answer)

# -------------- STEP 3 — Text-to-Speech (Deepgram TTS) --------------
# Note: Deepgram TTS endpoint may differ based on account; here's a common endpoint.
tts_url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
tts_headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": "application/json"}

try:
    tts_resp = requests.post(tts_url, headers=tts_headers, data=json.dumps({"text": answer}), timeout=30)
    if tts_resp.status_code == 200:
        st.audio(tts_resp.content, format="audio/mp3")
    else:
        st.warning("TTS failed — showing server response (you'll still see the text answer).")
        st.code(tts_resp.text)
except Exception as e:
    st.error("Network error when requesting TTS.")
    st.exception(e)

# ----- Done -----
