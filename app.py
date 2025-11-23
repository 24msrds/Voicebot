import streamlit as st
import openai

# Set API Key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Page config
st.set_page_config(page_title="Ragul's Voice Bot", layout="centered")
st.title("🎤 Ragul's Interview Voice Bot")

st.write("Speak any interview-type question. I will answer as **Ragul B**.")

# Audio input (microphone)
audio = st.audio_input("🎙️ Ask your question:")

if audio:
    # Play the audio user recorded
    st.audio(audio)

    # Convert speech → text
    transcription = openai.Audio.transcribe(
        model="gpt-4o-transcribe",
        file=audio
    )

    user_text = transcription["text"]
    st.write("### **You asked:**", user_text)

    # Create prompt: Answer questions as Ragul B
    prompt = f"""
    Answer the following question as if you are Ragul B.
    Speak in first person, confident, clear, and interview-friendly.

    Question: {user_text}
    """

    # Generate answer text
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response["choices"][0]["message"]["content"]

    st.write("### **My Answer:**")
    st.write(answer)

    # Convert answer → audio  
    tts_audio = openai.Audio.create(
        model="gpt-4o-mini-speech",
        voice="alloy",
        input=answer
    )

    # Play the generated voice response
    st.audio(tts_audio, format="audio/mp3")
