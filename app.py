import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
import openai
from openai import RateLimitError, AuthenticationError, APIError

# Load .env and API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Voice Assistant Demo", page_icon="🎤")
st.title("📞 AI Voice Assistant Demo")
st.markdown("🎙️ Speak your message, and the assistant will respond in a natural voice (supports French & English).")

# Voice Input
audio_file = st.audio_input("Press and record your voice")

if audio_file:
    st.info("Transcribing...")

    # Save temp audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_file.read())
        temp_path = temp_audio.name

    # Transcribe using Whisper
    try:
        with open(temp_path, "rb") as af:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=af,
                response_format="text"
            ).strip()
        os.remove(temp_path)
    except RateLimitError:
        st.error("Rate limit hit. Please wait a bit.")
        st.stop()
    except AuthenticationError:
        st.error("Invalid API Key.")
        st.stop()
    except APIError as e:
        st.error(f"OpenAI API error: {str(e)}")
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        st.stop()

    # Generate response
    st.info("Thinking...")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a polite and helpful phone receptionist. Respond clearly in the user's language."
                },
                {"role": "user", "content": transcript}
            ],
            max_tokens=200
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Failed to generate response: {str(e)}")
        st.stop()

    # Text-to-Speech
    st.info("Generating voice...")
    try:
        tts = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=reply
        )
        audio_path = os.path.join(tempfile.gettempdir(), "reply.mp3")
        with open(audio_path, "wb") as f:
            f.write(tts.content)
        st.audio(audio_path, format="audio/mp3", autoplay=True)
        st.success("Reply ready!")
    except Exception as e:
        st.error(f"TTS failed: {str(e)}")

    # Optional: Show reply & transcript
    with st.expander("Transcript and Reply", expanded=False):
        st.markdown("**You said:**")
        st.write(transcript)
        st.markdown("**Assistant replied:**")
        st.write(reply)

# Footer
st.markdown("---")
st.caption("🤖 Built by Muhammad Shakeel | GPT-4o + Whisper + TTS")
