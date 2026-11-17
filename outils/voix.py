"""Voix off française gratuite, en local (sur GitHub Actions, sans clé) : Kokoro et Piper.

- Kokoro 82M (hexgrad/Kokoro-82M) : voix « ff_siwis » (femme), langue 'f'. Naturelle, rapide sur CPU.
- Piper (rhasspy/piper-voices) : fr_FR-siwis-medium (femme), fr_FR-tom-medium (homme),
  fr_FR-upmc-medium (pierre / jessica), fr_FR-gilles-low (homme). Très rapide.

Usage : python -m outils.voix "Texte" --moteur kokoro --voix ff_siwis --vitesse 1.0 -o voix.wav
"""

from __future__ import annotations

import argparse
import subprocess
import urllib.request
from pathlib import Path

CACHE = Path.home() / ".cache" / "aistory-voix"
PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR"


def kokoro(texte: str, dst: Path, voix: str = "ff_siwis", vitesse: float = 1.0) -> None:
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="f", repo_id="hexgrad/Kokoro-82M")
    morceaux = [audio for _, _, audio in pipe(texte, voice=voix, speed=vitesse)]
    sf.write(str(dst), np.concatenate(morceaux), 24000)


def _piper_modele(voix: str) -> Path:
    nom, qualite = voix.rsplit("-", 1)  # fr_FR-siwis-medium -> fr_FR-siwis / medium
    locuteur = nom.split("-", 1)[1]
    CACHE.mkdir(parents=True, exist_ok=True)
    onnx = CACHE / f"{voix}.onnx"
    for suffixe in (".onnx", ".onnx.json"):
        f = CACHE / f"{voix}{suffixe}"
        if not f.exists():
            urllib.request.urlretrieve(f"{PIPER_BASE}/{locuteur}/{qualite}/{voix}{suffixe}", f)
    return onnx


def piper(texte: str, dst: Path, voix: str = "fr_FR-siwis-medium", vitesse: float = 1.0,
          locuteur: int | None = None) -> None:
    modele = _piper_modele(voix)
    cmd = ["piper", "-m", str(modele), "-f", str(dst), "--length-scale", f"{1 / vitesse:.3f}"]
    if locuteur is not None:
        cmd += ["--speaker", str(locuteur)]
    subprocess.run(cmd, input=texte.encode(), check=True, capture_output=True)


MOTEURS = {"kokoro": kokoro, "piper": piper}


def synthese(texte: str, dst: Path, moteur: str, voix: str | None = None, vitesse: float = 1.0) -> Path:
    kwargs = {"vitesse": vitesse}
    if voix:
        if moteur == "piper" and ":" in voix:  # fr_FR-upmc-medium:1 -> locuteur 1 (pierre)
            voix, loc = voix.split(":")
            kwargs["locuteur"] = int(loc)
        kwargs["voix"] = voix
    MOTEURS[moteur](texte, dst, **kwargs)
    return dst


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("texte")
    ap.add_argument("--moteur", choices=list(MOTEURS), default="kokoro")
    ap.add_argument("--voix")
    ap.add_argument("--vitesse", type=float, default=1.0)
    ap.add_argument("-o", "--sortie", default="voix.wav")
    a = ap.parse_args()
    print(synthese(a.texte, Path(a.sortie), a.moteur, a.voix, a.vitesse))


if __name__ == "__main__":
    main()
