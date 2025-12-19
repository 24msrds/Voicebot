# Updated app.py
# Uploaded file (for reference): /mnt/data/1f46c8d6-47d3-463e-8ad1-d021c6c6de48.png

import streamlit as st
import requests
import json
import tempfile
import traceback

# Groq SDK import is lazy so app won't crash immediately if missing locally
try:
    from groq import Groq
except Exception:
    Groq = None

# --------------------------
# Streamlit UI setup
# --------------------------
st.set_page_config(page_title="Ragul's Interview Voice Bot (FREE)", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot (FREE)")
st.write("Ask any interview-style question. I'll answer like **Ragul B**.")

# --------------------------
# Helpers
# --------------------------

def mask_key(k: str):
    if not k:
        return "<missing>"
    return k[:4] + "…" + k[-4:] + f" (len={len(k)})"

# --------------------------
# Debug / secrets check (safe — masks keys)
# --------------------------
st.write("**Debug:** checking secrets (masked):")
st.write(f"GROQ_API_KEY = {mask_key(st.secrets.get('GROQ_API_KEY',''))}")
st.write(f"DEEPGRAM_API_KEY = {mask_key(st.secrets.get('DEEPGRAM_API_KEY',''))}")
# Optional configurable model via secrets
MODEL_ID = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")
st.write(f"GROQ_MODEL = {MODEL_ID}")

# Ensure needed secrets exist
if "GROQ_API_KEY" not in st.secrets or "DEEPGRAM_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY and/or DEEPGRAM_API_KEY in Streamlit secrets. Add them and restart the app.")
    st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

# --------------------------
# Initialize Groq client (if SDK available)
# --------------------------
if Groq is None:
    st.error("Groq SDK not installed in the environment. Locally run: pip install groq")
    st.stop()

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    st.write("Groq client created.")
except Exception as e:
    st.error("Failed to initialize Groq client. Check GROQ_API_KEY.")
    st.exception(e)
    st.stop()

# --------------------------
# Optional lightweight auth + model sanity test
# --------------------------
try:
    test_reply = groq_client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": "Ping"}],
        max_tokens=1
    )
    st.success("Groq test call succeeded (auth & model access OK).")
except Exception as e:
    st.error("Groq test call failed — this likely means authentication / model permissions problem.")
    resp = getattr(e, "response", None)
    if resp is not None:
        st.write("HTTP status:", getattr(resp, "status_code", "<unknown>"))
        text = getattr(resp, "text", "")
        st.write("Response snippet:", text[:1000])
    else:
        st.write("Exception type:", type(e).__name__)
        st.text(traceback.format_exc())
    st.stop()

# --------------------------
# Main UI: accept audio input
# --------------------------
audio = st.audio_input("🎙️ Speak your interview question:")

if audio:
    st.audio(audio)

    # Save audio as WEBM (Streamlit format)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        audio_path = tmp.name

    # --------------------------
    # STEP 1 — Deepgram Transcription
    # --------------------------
    deepgram_url = "https://api.deepgram.com/v1/listen"
    try:
        with open(audio_path, "rb") as f:
            dg_response = requests.post(
                deepgram_url,
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "audio/webm"
                },
                data=f
            )
        # Handle non-200 from Deepgram
        if dg_response.status_code != 200:
            st.error(f"Deepgram returned status {dg_response.status_code}")
            st.write(dg_response.text[:1000])
            st.stop()
        dg_data = dg_response.json()
    except Exception as e:
        st.error("Network or Deepgram request failed.")
        st.exception(e)
        st.stop()

    # Extract transcript safely
    user_text = ""
    try:
        user_text = dg_data["results"]["channels"][0]["alternatives"][0]["transcript"]
    except Exception:
        st.error("❌ Deepgram could not read your audio. Try speaking clearly.")
        st.subheader("Deepgram Debug Response:")
        st.json(dg_data)
        st.stop()

    st.write("### **You asked:**", user_text)

    # --------------------------
    # STEP 2 — Groq Chat Completion
    # --------------------------
    prompt = f"""
    Answer the following question as if you are Ragul B.
    Speak in first person, confident and interview-friendly.

    Question: {user_text}
    """

    try:
        chat_reply = groq_client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512
        )
        # Extract answer safely
        answer = chat_reply.choices[0].message.content
    except Exception as e:
        st.error("Groq API error (model or permissions). See debug below.")
        resp = getattr(e, "response", None)
        if resp is not None:
            st.write("HTTP status:", getattr(resp, "status_code", "<unknown>"))
            st.write("Response snippet:", getattr(resp, "text", "")[:1200])
        else:
            st.exception(e)
        st.stop()

    st.write("### **My Answer:**")
    st.write(answer)

    # --------------------------
    # STEP 3 — Deepgram TTS (text → speech)
    # --------------------------
    tts_url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    try:
        tts_response = requests.post(
            tts_url,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({"text": answer})
        )
        if tts_response.status_code == 200:
            st.audio(tts_response.content, format="audio/mp3")
        else:
            st.error("Deepgram TTS failed.")
            st.write(tts_response.status_code)
            st.write(tts_response.text[:1000])
    except Exception as e:
        st.error("Deepgram TTS request failed.")
        st.exception(e)

