# video-in-terminal

Play a video (or your webcam) as colored ASCII art directly in the terminal,
with synced audio.

Each frame is downscaled to fit your terminal, converted to grayscale to pick
an ASCII character by brightness (`" .:-=+*#%@"`), and colored per-cell with
24-bit ANSI escape codes using the original pixel color. Audio is played in
parallel via `ffplay`, synced to the video's frame timing.

<video autoplay src="demo/arab-idol.mp4" controls muted loop playsinline width="700">
  Your viewer doesn't support inline video — see demo/demo.mp4.
</video>

## Setup

Installs `ffmpeg` (for audio) and the Python dependencies (`opencv-python`,
`numpy`).

```
./setup.sh
```

Requires a truecolor-capable terminal (iTerm2, Kitty, Alacritty, Windows
Terminal, most modern terminals) for correct colors.

## Usage

Play a video file:
```
python3 play.py your_video.mp4
```

Loop it forever:
```
python3 play.py your_video.mp4 --loop
```

Stream your webcam (no audio):
```
python3 play.py --webcam
```

Force an output width (columns), instead of auto-detecting the terminal size:
```
python3 play.py your_video.mp4 --width 100
```

Disable audio:
```
python3 play.py your_video.mp4 --no-audio
```

Press `Ctrl+C` to stop at any time.

## Options

| Flag | Description |
|---|---|
| `source` | Path to a video file (omit when using `--webcam`) |
| `--webcam` | Use the webcam instead of a file |
| `--camera-index` | Webcam index, default `0` |
| `--width` | Output width in columns (default: current terminal width) |
| `--no-audio` | Disable audio playback |
| `--loop` | Loop the video file forever |
| `--fps` | Override playback fps |

## Notes

- Performance depends on terminal width and video resolution — reduce
  `--width` if playback lags behind the audio (dropped frames catch it back
  up, but very large frames slow rendering).
- Without `ffmpeg`/`ffplay` installed, playback continues without audio.
