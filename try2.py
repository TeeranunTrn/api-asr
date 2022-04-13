import subprocess

cmd = ['ffmpeg', '-i', './ten.mp4', '-ac', '1', '-ar', '16000', './ten.mp3']
result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
