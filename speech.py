import os
import google.cloud.texttospeech as tts


def synthesize_text(text):    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"gpt-interview-gcp-key.json"
    """Synthesizes speech from the input string of text."""
    client = tts.TextToSpeechClient()

    input_text = tts.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = tts.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-F",
        ssml_gender=tts.SsmlVoiceGender.FEMALE,
    )

    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )
    return response.audio_content

    # stream the response to frontend

    # The response's audio_content is binary.
    # with open("output.mp3", "wb") as out:
    #     out.write(response.audio_content)
    #     print('Audio content written to file "output.mp3"')
