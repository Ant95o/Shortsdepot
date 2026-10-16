"""Petites fonctions autour de FFmpeg."""

import json
import subprocess
from pathlib import Path

WIDTH, HEIGHT, FPS = 1080, 1920, 30
SAMPLE_RATE = 48000


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def mix_clips(clips: list[tuple[float, Path]], total: float, dst: Path) -> None:
    """Place chaque clip audio à son instant de départ sur une piste de `total` secondes."""
    args = ["-f", "lavfi", "-t", f"{total:.3f}", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=stereo"]
    filters = []
    for i, (start, path) in enumerate(clips, start=1):
        args += ["-i", str(path)]
        ms = int(start * 1000)
        filters.append(f"[{i}:a]aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{i}]")
    inputs = "[0:a]" + "".join(f"[a{i}]" for i in range(1, len(clips) + 1))
    # Volume ramené à -14 LUFS, le niveau visé par TikTok, Instagram et YouTube.
    filters.append(f"{inputs}amix=inputs={len(clips) + 1}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    run_ffmpeg([*args, "-filter_complex", ";".join(filters), "-map", "[out]", "-ar", str(SAMPLE_RATE), str(dst)])


def encoder(audio: Path, dst: Path) -> subprocess.Popen:
    """Encodeur H.264/AAC aux specs Reels/Shorts/TikTok, qui lit des images RGB sur stdin."""
    return subprocess.Popen(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
            "-i", str(audio),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-g", str(FPS * 2), "-keyint_min", str(FPS * 2), "-sc_threshold", "0",
            "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-ac", "2",
            "-movflags", "+faststart", "-shortest", str(dst),
        ],
        stdin=subprocess.PIPE,
    )
