from deepgram import Deepgram
import asyncio, json
import os
from dotenv import load_dotenv

load_dotenv()

class Deepgram_STT():
    def __init__(self):
        DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API")
        self.dg = Deepgram(DEEPGRAM_API_KEY)
    
    async def transcribe_from_file(self, temp_file):
        try:
            response = None
            # Set the source
            with open(temp_file, 'rb') as audio:
                audio_buffer = audio.read()
                source = {
                    'buffer': audio_buffer,
                    'mimetype': 'audio/webm'
                }
                print(">>>> transcribing")
                response = await asyncio.create_task(
                    self.dg.transcription.prerecorded(
                    source,
                    {
                        'punctuate': True,
                        'tier': 'base',
                        'model': 'voicemail'
                    }
                    )
                )
                # print(json.dumps(response, indent=4))
            return response['results']['channels'][0]['alternatives'][0]['transcript']
        except Exception as e:
            raise Exception(f'Could not process audio: {e}')
