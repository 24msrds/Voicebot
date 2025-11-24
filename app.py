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
        st.writ
