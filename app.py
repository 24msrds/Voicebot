# --- Debug / auth-check block (add right after reading st.secrets) ---
import traceback
from groq import Groq
import groq as groq_pkg   # to reference exceptions

# Masked info (safe to show)
def mask_key(k: str):
    if not k: return "<missing>"
    return k[:4] + "…" + k[-4:] + f" (len={len(k)})"

st.write("**Debug:** checking secrets (masked):")
st.write(f"GROQ_API_KEY = {mask_key(st.secrets.get('GROQ_API_KEY',''))}")
st.write(f"DEEPGRAM_API_KEY = {mask_key(st.secrets.get('DEEPGRAM_API_KEY',''))}")

# Quick existence check
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Streamlit secrets. Add it in the app settings.")
    st.stop()

# Initialize client with try/except
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    st.write("Groq client created successfully.")
except Exception as e:
    st.error("Failed to initialize Groq client.")
    st.exception(e)
    st.stop()

# Optional: run a tiny sanity call to validate auth (wrapped)
st.write("Attempting a lightweight Groq auth test...")

try:
    # Here we attempt a small chat call with a trivial prompt & short model to test auth.
    # If your account doesn't have model access, this will show the response text/status.
    test_reply = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role":"user","content":"Say hello briefly."}],
        max_tokens=1
    )
    st.success("Test chat call succeeded — authentication OK.")
    st.write("Test reply (truncated):")
    st.write(str(test_reply)[:800])
except Exception as e:
    st.error("Groq test call failed — authentication or permissions issue.")
    # Try to show more info about the response if available
    try:
        # Many SDK exceptions include a `.response` attribute with status/text
        resp = getattr(e, "response", None)
        if resp is not None:
            st.write("HTTP status:", getattr(resp, "status_code", "<unknown>"))
            # Avoid printing secrets — show only the beginning of the text body
            text = getattr(resp, "text", "")
            st.write("Response snippet:", text[:1000])
        else:
            st.write("Exception type:", type(e).__name__)
            st.write("Exception args:", e.args)
            st.text(traceback.format_exc())
    except Exception:
        st.exception(e)
    st.stop()
# --- end debug block ---
