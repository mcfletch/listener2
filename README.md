# DeepSpeech-in-docker IBus Engine

## Testing bits out...

Sending audio to the daemon
```
./ffmpeg-audio.sh hw:1,1
./ffmpeg-sample.sh /path/to/some.wav
```
Viewing the raw transcripts from the daemon
```
nc -U /tmp/dspipe/events
```
Running the ibus engine interactively:
```
./ibusengine.py
```
