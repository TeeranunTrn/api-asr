#!/usr/bin/env python3

import os
import subprocess

import aiofiles
import uvicorn
from fastapi import FastAPI, File, UploadFile

import json
import logging
import wave
from typing import Any, Dict, Optional, List

from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(0)

class VoskTranscriber:

    def __init__(self, model_path: str) -> None:
        self.model_path: str = model_path
        # sanity check model path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Cannot find model path: `{model_path}`")
        self.model: Model = Model(model_path)

    def transcribe(self, wav_path: str) -> Dict[str, Any]:
        wf: Any = wave.open(wav_path, "rb")

        # check file eligibility
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise OSError(f"Cannot read wav file: `{wav_path}`. Make sure your audio file is in .wav format and mono channel")

        rec: KaldiRecognizer = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)

        while True:
            data: Any = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                logging.debug(rec.Result())
            else:
                logging.debug(rec.PartialResult())

        return json.loads(rec.FinalResult())


app = FastAPI()
model_path: str = "mymodel"  # change this if neccessary
transcriber = VoskTranscriber(model_path)


def clear_audio(audio_paths: List[str]) -> None:
    for f in audio_paths:
        os.remove(f)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy"}


@app.post("/transcribe")
async def transcribe(audios: List[UploadFile] = File(...)):
    # save files
    audio_paths = []
    for audio in audios:
        if not os.path.exists('tmp'):
            os.makedirs('tmp')
        # save tmp audio file
        tmp_name = f'tmp/{audio.filename}.tmp'
        save_name = f'tmp/{audio.filename}'.replace('.mp3', '.wav')

        async with aiofiles.open(tmp_name, "wb") as f:
            content = await audio.read()
            await f.write(content)

        # convert to mono, 16k sampling rate
        cmd = ['ffmpeg', '-i', tmp_name, '-ac', '1', '-ar', '16000', save_name]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        audio_paths.append(save_name)
        os.path.exists(save_name)

    # inference
    result = {
        wav: transcriber.transcribe(wav)
        for wav in audio_paths
    }

    clear_audio(audio_paths)
    return result, 200
    
if __name__ == "__main__":
    uvicorn.run(app, debug=True)
