"""Exécute une fiche outils/fiches/*.yaml (voix, sous-titres, contrôle des plans) sur GitHub Actions.

Exemple de fiche :

    voix:
      texte: "Ce chat n'a peur de rien. Enfin, presque."
      essais:                      # une ou plusieurs voix à écouter
        - {moteur: kokoro, voix: ff_siwis}
        - {moteur: piper, voix: fr_FR-tom-medium}
    soustitres:
      audio: voix                  # « voix » = premier essai de voix ci-dessus, sinon chemin d'un fichier
      texte: "..."                 # facultatif (sinon reprend le texte de la voix)
      video: clips/gateau/plan1-gateau-g42.mp4   # facultatif : vidéo à sous-titrer
    plans:
      clips: ["clips/gateau/*.mp4"]
      couper: false
"""

from __future__ import annotations

import glob
import subprocess
import sys
from pathlib import Path

import yaml


def main(fiche: str, sortie: str) -> None:
    f = yaml.safe_load(Path(fiche).read_text())
    out = Path(sortie)
    out.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    premiere_voix = None

    if v := f.get("voix"):
        from outils.voix import synthese

        dv = out / "voix"
        dv.mkdir(exist_ok=True)
        for e in v.get("essais", [{"moteur": "kokoro"}]):
            nom = f"{e['moteur']}-{(e.get('voix') or 'defaut').replace(':', '-')}"
            try:
                p = synthese(v["texte"], dv / f"{nom}.wav", e["moteur"], e.get("voix"), e.get("vitesse", 1.0))
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-b:a", "128k", str(p.with_suffix(".mp3"))])
                premiere_voix = premiere_voix or p
                print("voix OK :", nom)
            except Exception as exc:
                print("voix ÉCHEC :", nom, exc)

    if s := f.get("soustitres"):
        audio = premiere_voix if s.get("audio", "voix") == "voix" else Path(s["audio"])
        texte = s.get("texte") or (v or {}).get("texte") if s.get("audio", "voix") == "voix" else s.get("texte")
        cmd = [py, "-m", "outils.soustitres", str(audio), "--sortie", str(out / "soustitres")]
        if texte:
            cmd += ["--texte", texte]
        if s.get("video"):
            cmd += ["--video", s["video"]]
        if s.get("modele"):
            cmd += ["--modele", s["modele"]]
        subprocess.run(cmd, check=True)

    if p := f.get("plans"):
        clips = sorted({c for motif in p["clips"] for c in glob.glob(motif)})
        cmd = [py, "-m", "outils.plans", *clips, "--sortie", str(out / "plans")]
        if p.get("couper"):
            cmd.append("--couper")
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
