import subprocess

result = subprocess.run(
            ['ffmpeg', '-i', ten.mp4, '-ac 1', '-ar 16000', ten.mp3],
            stdout=subprocess.PIPE, shell=True
        )