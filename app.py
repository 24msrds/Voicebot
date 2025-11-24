# app.py — corrected top portion
import streamlit as st
import requests
import json
from groq import Groq
import tempfile
import traceback

st.set_page_config(page_title="Ragul's Interview Voice Bot (FREE)", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot (FREE)")
st.write("Ask any interview-style question. I'll answer like **Ragul B**.")

# --- Safe secrets check (must be after `import streamlit as st`) ---
def mask_key(k: str):
    if not k: return "<missing>"
    return k[:4] + "…" + k[-4:] + f" (len={len(k)})"

st.write("**Debug:** checking secrets (masked):")
st.write(f"GROQ_API_KEY = {mask_key(st.secrets.get('GROQ_API_KEY',''))}")
st.write(f"DEEPGRAM_API_KEY = {mask_key(st.secrets.get('DEEPGRAM_API_KEY',''))}")

if "GROQ_API_KEY" not in st.secrets or "DEEPGRAM_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY and/or DEEPGRAM_API_KEY in Streamlit secrets. Add them and restart the app.")
    st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

# --- Initialize Groq client (catch errors) ---
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    st.write("Groq client created.")
except Exception as e:
    st.error("Failed to initialize Groq client. Check GROQ_API_KEY.")
    st.exception(e)
    st.stop()

# --- Optional lightweight auth test (safe, truncated output) ---
try:
    test_reply = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role":"user","content":"Ping"}],
        max_tokens=1
    )
    st.success("Groq test call succeeded (auth OK).")
except Exception as e:
    st.error("Groq test call failed — this likely means authentication / permissions problem.")
    resp = getattr(e, "response", None)
    if resp is not None:
        st.write("HTTP status:", getattr(resp, "status_code", "<unknown>"))
        text = getattr(resp, "text", "")
        st.write("Response snippet:", text[:1000])
    else:
        st.write("Exception type:", type(e).__name__)
        st.text(traceback.format_exc())
    st.stop()
