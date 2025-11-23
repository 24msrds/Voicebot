import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Page config
st.set_page_config(page_title="Ragul's Voice Bot", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot")
st.write("Speak any interview-type question. I will answer as **Ragul B**.")

# Mic input
audio = st.audio_input("🎙️ Ask your question:")

if audio:
    st.audio(audio)

    # Speech → Text
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio  # RAW audio file
    )

    user_text = transcription.text
    st.write("### **You asked:**", user_text)

    # Answer as Ragul B
    prompt = f"""
    Answer the following question as if you are Ragul B.
    Speak in first person, confidently and interview-friendly.

    Question: {user_text}
    """

    # Chat Response (New API)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message["content"]

    st.write("### **My Answer:**")
    st.write(answer)

    # Text → Speech (New API)
    audio_reply = client.audio.speech.create(
        model="gpt-4o-mini-speech",
        voice="alloy",
        input=answer
    )

    st.audio(audio_reply.read(), format="audio/mp3")
