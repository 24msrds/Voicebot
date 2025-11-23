import streamlit as st
from openai import OpenAI

# Page config
st.set_page_config(page_title="Ragul's Voice Bot", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot")

# Client with API key from secrets.toml
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.write("Speak any interview-type question. I will answer as **Ragul B**.")

# Audio input (microphone)
audio = st.audio_input("🎙️ Ask your question:")

if audio:
    # Play recorded audio
    st.audio(audio)

    # Convert speech → text
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio
    )
    
    user_text = transcription.text
    st.write("### **You asked:**", user_text)

    # Create prompt that answers as YOU (Ragul B)
    prompt = f"""
    Answer the following question as if you are Ragul B, speaking in the first person.
    Keep the tone confident, clear, and interview-friendly.

    Question: {user_text}
    """

    # Generate answer text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content

    st.write("### **My Answer:**")
    st.write(answer)

    # Convert bot answer → audio
    audio_reply = client.audio.speech.create(
        model="gpt-4o-mini-speech",
        voice="alloy",
        input=answer
    )

    # Play audio output
    st.audio(audio_reply, format="audio/mp3")
