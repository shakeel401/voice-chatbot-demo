import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
import openai

# Load API key securely from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Voice Chatbot Demo", page_icon="🎤")
st.title("🎤 Voice Chatbot Demo")
st.markdown("Upload or record your voice message. The bot will understand and respond with a natural-sounding voice.")

audio_file = st.file_uploader("Upload your voice (MP3/WAV)", type=["mp3", "wav"])

if audio_file:
    st.audio(audio_file, format='audio/mp3')
    st.info("Transcribing your voice...")

    # Save temporary audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(audio_file.read())
        temp_path = temp_audio.name

    # Transcription using Whisper (auto-detects language)
    with open(temp_path, "rb") as af:
        transcript_response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=af,
            response_format="text"
        )
    transcript = transcript_response.strip()

    st.success("Transcription complete!")
    st.subheader("📝 Transcript")
    st.write(transcript)

    # GPT-4 reply (language auto-handled by GPT)
    st.info("Generating reply with GPT-4o...")

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a polite and helpful virtual phone receptionist. "
                    "Understand the user query, and respond briefly in the same language they spoke."
                )
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
        max_tokens=200
    )

    reply = response.choices[0].message.content.strip()
    st.success("Response generated!")
    st.subheader("💬 Chatbot Reply")
    st.write(reply)

    # Detect action
    st.subheader("📍 Detected Action")
    lowered = transcript.lower()
    if any(word in lowered for word in ["appointment", "rendez-vous", "meeting", "book", "réserver"]):
        st.markdown("✅ **Intent: Appointment Booking**")
    elif "urgent" in lowered:
        st.markdown("🚨 **Intent: Forward to Human**")
    else:
        st.markdown("📝 **Intent: General Info / FAQ**")

    # Convert reply to speech
    st.info("Converting reply to voice...")
    tts_response = openai.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=reply
    )

    audio_output_path = os.path.join(tempfile.gettempdir(), "response.mp3")
    with open(audio_output_path, "wb") as f:
        f.write(tts_response.content)

    st.audio(audio_output_path, format="audio/mp3")

    # Clean up temp files
    try:
        os.remove(temp_path)
    except:
        pass

    st.success("✅ Voice reply ready!")
