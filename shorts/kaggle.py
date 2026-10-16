"""Préparation et récupération des générations vidéo faites sur Kaggle.

  python -m shorts.kaggle a-generer                      # fiches dont des plans manquent
  python -m shorts.kaggle preparer DOSSIER UTILISATEUR FICHES…
  python -m shorts.kaggle recuperer DOSSIER_SORTIE FICHES…

Une fiche demande une génération avec une section :
  generation:
    plans:
      - {fichier: clips/xxx/plan1.mp4, prompt: "…", graine: 42}
      # avec une vidéo de référence (mouvements et cadrage repris, 5 s à partir de « debut ») :
      - {fichier: clips/xxx/plan2.mp4, prompt: "…", reference: refs/xxx.mp4, debut: 4.5, force: 0.8}
"""

import base64
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SLUG = "shortsdepot-generation"
TEMPLATE = Path(__file__).parent / "kaggle_job" / "gen.py"


def _missing_shots(spec_path: Path) -> list[dict]:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    plans = (spec.get("generation") or {}).get("plans", [])
    missing = [p for p in plans if not Path(p["fichier"]).exists()]
    for p in missing:
        if p.get("reference") and not Path(p["reference"]).exists():
            print(f"{spec_path} : référence {p['reference']} absente, plan {p['fichier']} en attente", file=sys.stderr)
    return [p for p in missing if not p.get("reference") or Path(p["reference"]).exists()]


def _reference(path: Path, start: float) -> str:
    """Extrait 5 s de la référence au format de Wan (480x832, 16 i/s, 81 images), en base64."""
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "ref.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start}", "-i", str(path),
            "-vf", "fps=16,scale=480:832:force_original_aspect_ratio=increase,crop=480:832,setsar=1",
            "-frames:v", "81", "-an", "-c:v", "libx264", "-crf", "26", "-pix_fmt", "yuv420p", str(clip),
        ], check=True)
        return base64.b64encode(clip.read_bytes()).decode()


def _shots(specs: list[Path]) -> list[dict]:
    shots = []
    for spec in specs:
        for plan in _missing_shots(spec):
            shot = {"out": f"plan_{len(shots):02d}.mp4", "fichier": plan["fichier"],
                    "prompt": plan["prompt"], "seed": plan.get("graine", 42)}
            if plan.get("reference"):
                shot["reference"] = plan["reference"]
                shot["debut"] = float(plan.get("debut", 0))
                shot["force"] = float(plan.get("force", 0.8))
            shots.append(shot)
    return shots


def a_generer() -> None:
    for spec in sorted(Path("specs").glob("*.yaml")):
        if _missing_shots(spec):
            print(spec)


def preparer(folder: Path, user: str, specs: list[Path]) -> None:
    shots = _shots(specs)
    folder.mkdir(parents=True, exist_ok=True)
    jobs = []
    for s in shots:
        job = {k: s[k] for k in ("out", "prompt", "seed")}
        if "reference" in s:
            job["ref"] = _reference(Path(s["reference"]), s["debut"])
            job["force"] = s["force"]
        jobs.append(job)
    payload = json.dumps(jobs, ensure_ascii=False)
    (folder / "gen.py").write_text(TEMPLATE.read_text(encoding="utf-8").replace("__SHOTS__", payload), encoding="utf-8")
    (folder / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{SLUG}", "title": SLUG, "code_file": "gen.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": [],
    }, indent=2))
    (folder / "plans.json").write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(shots)} plan(s) à générer")


def pousser(folder: Path, accelerator: str) -> None:
    """Envoie le notebook sur Kaggle en affichant la raison exacte d'un refus."""
    from kaggle.api.kaggle_api_extended import KaggleApi
    from requests import HTTPError

    api = KaggleApi()
    api.authenticate()
    try:
        api.kernels_push_cli(str(folder), timeout=None, acc=accelerator)
    except HTTPError as exc:
        sys.exit(f"Kaggle a refusé l'envoi : {exc}\n{exc.response.text}")


def recuperer(output: Path, specs: list[Path]) -> None:
    for shot in _shots(specs):
        src = output / shot["out"]
        if not src.exists():
            sys.exit(f"Plan absent de la sortie Kaggle : {shot['out']} ({shot['fichier']})")
        Path(shot["fichier"]).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, shot["fichier"])
        print(f"{shot['fichier']} récupéré")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:]
    if cmd == "a-generer":
        a_generer()
    elif cmd == "preparer":
        preparer(Path(rest[0]), rest[1], [Path(s) for s in rest[2:]])
    elif cmd == "pousser":
        pousser(Path(rest[0]), rest[1])
    elif cmd == "recuperer":
        recuperer(Path(rest[0]), [Path(s) for s in rest[1:]])
    else:
        sys.exit(__doc__)
