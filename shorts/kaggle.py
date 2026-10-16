"""Préparation et récupération des générations vidéo faites sur Kaggle.

  python -m shorts.kaggle a-generer                      # fiches dont des plans manquent
  python -m shorts.kaggle preparer DOSSIER UTILISATEUR FICHES…
  python -m shorts.kaggle recuperer DOSSIER_SORTIE FICHES…

Une fiche demande une génération avec une section :
  generation:
    plans:
      - {fichier: clips/xxx/plan1.mp4, prompt: "…", graine: 42}
"""

import json
import shutil
import sys
from pathlib import Path

import yaml

SLUG = "shortsdepot-generation"
TEMPLATE = Path(__file__).parent / "kaggle_job" / "gen.py"


def _missing_shots(spec_path: Path) -> list[dict]:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    plans = (spec.get("generation") or {}).get("plans", [])
    return [p for p in plans if not Path(p["fichier"]).exists()]


def _shots(specs: list[Path]) -> list[dict]:
    shots = []
    for spec in specs:
        for plan in _missing_shots(spec):
            shots.append({"out": f"plan_{len(shots):02d}.mp4", "fichier": plan["fichier"],
                          "prompt": plan["prompt"], "seed": plan.get("graine", 42)})
    return shots


def a_generer() -> None:
    for spec in sorted(Path("specs").glob("*.yaml")):
        if _missing_shots(spec):
            print(spec)


def preparer(folder: Path, user: str, specs: list[Path]) -> None:
    shots = _shots(specs)
    folder.mkdir(parents=True, exist_ok=True)
    payload = json.dumps([{k: s[k] for k in ("out", "prompt", "seed")} for s in shots], ensure_ascii=False)
    (folder / "gen.py").write_text(TEMPLATE.read_text(encoding="utf-8").replace("__SHOTS__", payload), encoding="utf-8")
    (folder / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{SLUG}", "title": SLUG, "code_file": "gen.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": [],
    }, indent=2))
    (folder / "plans.json").write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(shots)} plan(s) à générer")


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
    elif cmd == "recuperer":
        recuperer(Path(rest[0]), [Path(s) for s in rest[1:]])
    else:
        sys.exit(__doc__)
