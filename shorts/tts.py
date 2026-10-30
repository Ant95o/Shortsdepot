"""Synthèse vocale avec bascule automatique entre fournisseurs.

Chaque fournisseur écrit un fichier WAV mono 48 kHz. Si un fournisseur échoue
(quota, réseau, paquet absent), le suivant de la liste est essayé.
"""

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

from .media import audio_duration, run_ffmpeg

DEFAULT_PROVIDERS = ["edge", "espeak"]


class TTSError(RuntimeError):
    pass


def _to_wav(src: Path, dst: Path) -> None:
    run_ffmpeg(["-i", str(src), "-ac", "1", "-ar", "48000", str(dst)])


def _edge(text: str, voice: dict, dst: Path) -> None:
    import edge_tts

    async def go(tmp: Path) -> None:
        communicate = edge_tts.Communicate(
            text, voice["edge"], rate=voice.get("rate", "+0%"), pitch=voice.get("pitch", "+0Hz")
        )
        await communicate.save(str(tmp))

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "edge.mp3"
        asyncio.run(go(tmp))
        if not tmp.exists() or tmp.stat().st_size == 0:
            raise TTSError("edge-tts n'a rien renvoyé")
        _to_wav(tmp, dst)


def _espeak(text: str, voice: dict, dst: Path) -> None:
    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary:
        raise TTSError("espeak-ng n'est pas installé")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "espeak.wav"
        subprocess.run(
            [binary, "-v", voice.get("espeak", "fr"), "-s", "165", "-w", str(tmp), text],
            check=True,
            capture_output=True,
        )
        _to_wav(tmp, dst)


def _silent(text: str, voice: dict, dst: Path) -> None:
    """Silence de durée réaliste, pour tester le montage sans réseau."""
    seconds = 0.35 + 0.36 * len(text.split())
    run_ffmpeg(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{seconds:.2f}", str(dst)])


PROVIDERS = {"edge": _edge, "espeak": _espeak, "silent": _silent}


def synthesize(text: str, voice: dict, dst: Path, providers: list[str]) -> tuple[float, str]:
    """Écrit la voix dans `dst` et renvoie (durée en secondes, fournisseur utilisé)."""
    errors = []
    for name in providers:
        try:
            PROVIDERS[name](text, voice, dst)
            return audio_duration(dst), name
        except Exception as exc:  # on bascule sur le fournisseur suivant
            errors.append(f"{name}: {exc}")
    raise TTSError("Aucun fournisseur de voix n'a fonctionné : " + " | ".join(errors))
