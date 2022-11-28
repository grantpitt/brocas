from google.cloud import speech
from fastapi import FastAPI, WebSocket, Body
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
import uvicorn
import queue
import asyncio
import threading
from gpt3_translator import translate, predict

from time import time

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

speech_client = speech.SpeechClient.from_service_account_json(
    "keys/text-to-speech-key.json"
)

speech_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
    sample_rate_hertz=48000,
    language_code="en-US",
    max_alternatives=1,
    model="latest_long",
    enable_automatic_punctuation=True,
    enable_spoken_punctuation=True,
    # use_enhanced=True,
)

streaming_config = speech.StreamingRecognitionConfig(
    config=speech_config,
    interim_results=True,
    single_utterance=False,
)


async def my_audio_processor_thread(websocket, audio_chunks):
    def generator():
        while True:
            data = []
            chunk = audio_chunks.get()
            if chunk is None:
                return
            data.append(chunk)
            while True:
                try:
                    chunk = audio_chunks.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

    try:
        gen = generator()

        requests = (
            speech.StreamingRecognizeRequest(audio_content=content) for content in gen
        )
        responses = speech_client.streaming_recognize(
            config=streaming_config, requests=requests
        )
        for response in responses:
            results = [
                {
                    "transcript": result.alternatives[0].transcript,
                    "is_final": result.is_final,
                    "stability": result.stability,
                }
                for result in response.results
            ]

            if websocket.client_state == WebSocketState.DISCONNECTED:
                return

            await websocket.send_json(results)
    except Exception as e:
        print(e)
        return


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("connected")

    audio_chunks = queue.Queue()

    # spin off thread that will process audio chunks
    thread = threading.Thread(
        target=asyncio.run, args=(my_audio_processor_thread(websocket, audio_chunks),)
    )
    thread.start()

    try:
        while True:
            if not thread.is_alive():
                raise Exception("thread died (likely gcp text-to-speech timeout (5 min))")
            data = await websocket.receive_bytes()
            audio_chunks.put(data)
    except Exception as e:
        print(e)
    finally:
        audio_chunks.put(None)
        thread.join()
        print("disconnected")


@app.post("/clean")
def clean(rawTranscript: str = Body(..., embed=True)):
    print("raw:", rawTranscript)
    start = time()
    clean_transcripts = translate(rawTranscript, first=True)
    print("cleaned in:", time() - start)
    return {
        "cleaned": clean_transcripts,
    }


@app.post("/predict")
def predict_route(text: str):
    predicted = predict(text)
    print("predicted:", predicted)
    return predicted


if __name__ == "__main__":
    print("Broca server is running on http://localhost:27622")
    uvicorn.run("server:app", host="0.0.0.0", port=27622, log_level="info")