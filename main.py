from flask import Flask, render_template
import asyncio
from aiohttp import web
from aiohttp_wsgi import WSGIHandler
from typing import Dict, Callable

from deepgram import Deepgram
from dotenv import load_dotenv
import os
import gpt3_translator

load_dotenv()

app = Flask(__name__)

dg_client = Deepgram(os.getenv('DEEPGRAM_API_KEY'))

async def process_audio(fast_socket: web.WebSocketResponse):
    async def get_transcript(data: Dict) -> None:
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']
            if transcript:
                """
                    grab translation from gpt3 then sends to websocket
                    four translations are sent to websocket separated by \n
                """
                # translation = gpt3_translator.translate(transcript, first=True)
                # await fast_socket.send_str(translation)
                # print(translation)
                """
                    this just sends the transcript to the websocket w/o translation
                    not sure if transcription and translations can be sent to the same websocket
                """
                await fast_socket.send_str(transcript)
                print(transcript)
    
    deepgram_socket = await connect_to_deepgram(get_transcript)

    return deepgram_socket

async def connect_to_deepgram(transcript_received_handler: Callable[[Dict], None]) -> str:
   try:
       socket = await dg_client.transcription.live({'punctuate': True, 'interim_results': False})
       socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
       socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, transcript_received_handler)

       return socket
   except Exception as e:
       raise Exception(f'Could not open socket: {e}')

async def socket(request): #new
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    deepgram_socket = await process_audio(ws)

    while True:
        data = await ws.receive_bytes() 
        deepgram_socket.send(data)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    aio_app = web.Application()
    wsgi = WSGIHandler(app)
    aio_app.router.add_route('*', '/{path_info: *}', wsgi.handle_request)
    aio_app.router.add_route('GET', '/listen', socket)
    # may need this--not sure if we should use separate websocket for translation
    # aio_app.router.add_route('GET', '/translate', )
    web.run_app(aio_app, port=5000)