import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
import openai
from openai import OpenAIError, RateLimitError, AuthenticationError, APIError

# Load API key securely from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Voice Chatbot Demo", page_icon="🎤")
st.title("🎤 Voice Chatbot Demo")
st.markdown("🎙️ Record your voice message. The assistant will understand and respond with a natural-sounding voice.")

# Use Streamlit's built-in voice input (audio recording)
audio_file = st.audio_input("Press to record your voice (French/English)")

if audio_file:
    st.info("🔄 Transcribing your voice...")

    # Save temporary audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_file.read())
        temp_path = temp_audio.name

    # --- Transcription ---
    try:
        with open(temp_path, "rb") as af:
            transcript_response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=af,
                response_format="text"
            )
        transcript = transcript_response.strip()
        st.success("✅ Transcription complete!")
        st.subheader("📝 Transcript")
        st.write(transcript)
    except RateLimitError:
        st.error("🚫 Too many requests. Please wait a moment and try again.")
        st.stop()
    except AuthenticationError:
        st.error("🔑 Invalid API key. Please check your credentials.")
        st.stop()
    except APIError as e:
        st.error(f"❌ OpenAI API error: {str(e)}")
        st.stop()
    except Exception as e:
        st.error(f"❗ An unexpected error occurred during transcription: {str(e)}")
        st.stop()

    # --- GPT-4o reply ---
    st.info("🤖 Generating reply using GPT-4o...")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
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
        st.success("✅ Response generated!")
        st.subheader("💬 Chatbot Reply")
        st.write(reply)
    except Exception as e:
        st.error(f"❗ Failed to generate reply: {str(e)}")
        st.stop()

    # --- Intent Detection ---
    st.subheader("📍 Detected Action")
    lowered = transcript.lower()
    if any(word in lowered for word in ["appointment", "rendez-vous", "meeting", "book", "réserver"]):
        st.markdown("✅ **Intent: Appointment Booking**")
    elif "urgent" in lowered:
        st.markdown("🚨 **Intent: Forward to Human**")
    else:
        st.markdown("📝 **Intent: General Info / FAQ**")

    # --- TTS Output ---
    st.info("🔊 Converting reply to voice...")
    try:
        tts_response = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=reply
        )

        audio_output_path = os.path.join(tempfile.gettempdir(), "response.mp3")
        with open(audio_output_path, "wb") as f:
            f.write(tts_response.content)

        st.audio(audio_output_path, format="audio/mp3",autoplay=True)
        st.success("🎉 Voice reply ready!")

    except Exception as e:
        st.error(f"❗ Text-to-speech conversion failed: {str(e)}")

    # --- Cleanup ---
    try:
        os.remove(temp_path)
    except:
        pass
