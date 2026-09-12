#!/usr/bin/env python3
"""Play a video (or webcam) as colored ASCII art in the terminal, with synced audio."""

import argparse
import os
import shutil
import subprocess
import sys
import time

import cv2
import numpy as np

RAMP = " .:-=+*#%@"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CURSOR_HOME = "\x1b[H"
RESET = "\x1b[0m"
CLEAR = "\x1b[2J"

# Terminal character cells are roughly twice as tall as they are wide.
CHAR_ASPECT = 2.0

# Round colors to this many levels per channel to create longer runs of
# identical escape codes, so far fewer ANSI codes need to be emitted per frame.
COLOR_BUCKET = 16


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", nargs="?", help="Path to a video file")
    p.add_argument("--webcam", action="store_true", help="Use the webcam instead of a file")
    p.add_argument("--camera-index", type=int, default=0, help="Webcam index (default 0)")
    p.add_argument("--width", type=int, default=None, help="Output width in columns (default: terminal width)")
    p.add_argument("--no-audio", action="store_true", help="Disable audio playback")
    p.add_argument("--loop", action="store_true", help="Loop the video file forever")
    p.add_argument("--fps", type=float, default=None, help="Override playback fps")
    return p.parse_args()


def frame_to_ansi(frame_bgr, ramp=RAMP):
    """Convert a BGR frame (numpy array) into a colored ASCII string with a trailing reset."""
    h, w, _ = frame_bgr.shape

    # Luminance -> ramp character index.
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    idx = (gray.astype(np.uint16) * (len(ramp) - 1) // 255).astype(np.uint8)
    chars = np.array(list(ramp))[idx]

    # Quantize colors so consecutive cells collapse into single ANSI runs.
    rgb = frame_bgr[:, :, ::-1].astype(np.int32)
    rgb = (rgb // COLOR_BUCKET * COLOR_BUCKET).astype(np.uint8)

    lines = []
    for y in range(h):
        parts = _row_to_ansi(chars[y], rgb[y])
        lines.append("".join(parts))
    return "\n".join(lines) + RESET


def _row_to_ansi(row_chars, row_colors):
    parts = []
    colors_tuples = [tuple(c) for c in row_colors.tolist()]
    start = 0
    n = len(colors_tuples)
    while start < n:
        color = colors_tuples[start]
        end = start + 1
        while end < n and colors_tuples[end] == color:
            end += 1
        run_chars = "".join(row_chars[start:end])
        r, g, b = color
        parts.append(f"\x1b[38;2;{r};{g};{b}m{run_chars}")
        start = end
    return parts


def compute_target_size(frame_w, frame_h, out_width):
    aspect = frame_h / frame_w
    out_height = max(1, int(out_width * aspect / CHAR_ASPECT))
    return out_width, out_height


def get_output_width(requested):
    if requested:
        return requested
    size = shutil.get_terminal_size(fallback=(80, 24))
    return max(10, size.columns)


def start_audio(path):
    if shutil.which("ffplay") is None:
        print("ffplay (ffmpeg) not found, playing without audio.", file=sys.stderr)
        return None
    return subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def play(source, use_webcam, camera_index, width_arg, no_audio, loop, fps_override):
    capture_target = camera_index if use_webcam else source
    cap = cv2.VideoCapture(capture_target)
    if not cap.isOpened():
        print(f"Could not open video source: {capture_target}", file=sys.stderr)
        return 1

    fps = fps_override or cap.get(cv2.CAP_PROP_FPS) or 25.0
    if fps <= 0 or fps > 120:
        fps = 25.0

    audio_proc = None
    if not use_webcam and not no_audio and os.path.isfile(source):
        audio_proc = start_audio(source)

    sys.stdout.write(HIDE_CURSOR + CLEAR)
    sys.stdout.flush()

    frame_index = 0
    start_time = time.time()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if loop and not use_webcam:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_index = 0
                    start_time = time.time()
                    if audio_proc:
                        audio_proc.terminate()
                        audio_proc = start_audio(source) if not no_audio else None
                    continue
                break

            out_width = get_output_width(width_arg)
            target_w, target_h = compute_target_size(frame.shape[1], frame.shape[0], out_width)
            small = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

            ansi_frame = frame_to_ansi(small)
            sys.stdout.write(CURSOR_HOME + ansi_frame)
            sys.stdout.flush()

            frame_index += 1
            if not use_webcam:
                target_time = frame_index / fps
                elapsed = time.time() - start_time
                sleep_for = target_time - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)
                elif sleep_for < -1.0 / fps * 3:
                    # Falling behind: drop frames to catch back up with the audio.
                    frames_to_skip = int(-sleep_for * fps)
                    for _ in range(frames_to_skip):
                        cap.grab()
                    frame_index += frames_to_skip
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        if audio_proc:
            audio_proc.terminate()
        sys.stdout.write(RESET + SHOW_CURSOR + "\n")
        sys.stdout.flush()

    return 0


def main():
    args = parse_args()
    if not args.webcam and not args.source:
        print("Provide a video file path or use --webcam.", file=sys.stderr)
        return 1
    return play(
        source=args.source,
        use_webcam=args.webcam,
        camera_index=args.camera_index,
        width_arg=args.width,
        no_audio=args.no_audio,
        loop=args.loop,
        fps_override=args.fps,
    )


if __name__ == "__main__":
    sys.exit(main())
