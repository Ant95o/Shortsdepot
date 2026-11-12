"""Monte un projet (openmontage-projets/<nom>/projet.yaml) avec le compositeur Remotion d'OpenMontage.

  python openmontage-projets/monter.py openmontage-projets/angel/projet.yaml SORTIE.mp4

Plans vidéo enchaînés (composition « Explainer », 1080x1920, 30 i/s), texte à l'écran en
sous-titres mot par mot (mot courant surligné, façon TikTok) et musique avec fondus.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[1]
COMPOSER = RACINE / "openmontage" / "remotion-composer"


def main(fiche: Path, sortie: Path) -> None:
    projet = yaml.safe_load(fiche.read_text(encoding="utf-8"))
    public = COMPOSER / "public" / "sp" / projet["nom"]
    shutil.rmtree(public, ignore_errors=True)
    public.mkdir(parents=True)
    cuts, captions, t = [], [], 0.0
    for i, plan in enumerate(projet["plans"]):
        src = RACINE / plan["source"]
        nom = f"{i:02d}-{src.name}"
        shutil.copy(src, public / nom)
        duree = float(plan["duree"])
        cuts.append({"id": f"plan{i + 1}", "source": f"sp/{projet['nom']}/{nom}",
                     "source_in_seconds": float(plan.get("debut", 0)),
                     "in_seconds": round(t, 3), "out_seconds": round(t + duree, 3)})
        if plan.get("texte"):
            mots = plan["texte"].split()
            pas = min(0.35, duree / len(mots))  # les mots apparaissent un par un, puis la phrase reste
            for k, mot in enumerate(mots):
                captions.append({"word": mot, "startMs": round((t + k * pas) * 1000),
                                 "endMs": round((t + (k + 1) * pas if k < len(mots) - 1 else t + duree) * 1000),
                                 "pageBreakAfter": k == len(mots) - 1})
        t += duree
    props = {"theme": projet.get("theme", "flat-motion-graphics"), "cuts": cuts, "overlays": [],
             "captions": captions, "tailPaddingSeconds": 0,
             "captionStyle": {"wordsPerPage": 5, "fontSize": 78, "bottomOffset": 1350}}
    if projet.get("musique"):
        m = projet["musique"]
        shutil.copy(RACINE / m["src"], public / "musique.mp3")
        props["audio"] = {"music": {"src": f"sp/{projet['nom']}/musique.mp3", "offsetSeconds": m.get("debut", 0),
                                    "volume": m.get("volume", 0.7), "fadeInSeconds": 0.3, "fadeOutSeconds": 1.0}}
    props_path = public / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["npx", "remotion", "render", "src/index.tsx", "Explainer", str(sortie.resolve()),
                    "--props", str(props_path), "--codec", "h264", "--width", "1080", "--height", "1920"],
                   cwd=COMPOSER, check=True)
    print(f"{sortie} : {t:.1f} s, {len(cuts)} plans")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
