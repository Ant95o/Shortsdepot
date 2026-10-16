"""Ligne de commande : python -m shorts specs/ma-video.yaml [--voix edge,espeak]"""

import argparse
import json
import tempfile
from pathlib import Path

import yaml

from .templates import clips_commentes, un_seul_mot
from .tts import DEFAULT_PROVIDERS

TEMPLATES = {"un_seul_mot": un_seul_mot.render, "clips_commentes": clips_commentes.render}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fabrique un short 9:16 à partir d'une fiche YAML.")
    parser.add_argument("specs", nargs="+", type=Path, help="fiches YAML (dossier specs/)")
    parser.add_argument("--sortie", type=Path, default=Path("rendus"), help="dossier de sortie")
    parser.add_argument("--voix", default=",".join(DEFAULT_PROVIDERS),
                        help="fournisseurs de voix dans l'ordre de bascule (edge, espeak, silent)")
    args = parser.parse_args()
    args.sortie.mkdir(parents=True, exist_ok=True)

    for path in args.specs:
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        missing = [c for c in spec.get("clips", []) if not Path(c).exists()]
        if missing:
            print(f"{path} : en attente des clips {', '.join(missing)}, rendu sauté")
            continue
        out = args.sortie / f"{path.stem}.mp4"
        with tempfile.TemporaryDirectory() as work:
            info = TEMPLATES[spec["gabarit"]](spec, Path(work), out, args.voix.split(","))
        meta = {"video": out.name, **info, "publication": spec.get("publication", {})}
        out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{out} ({info['duree_s']} s, voix : {', '.join(info['voix'])})")


if __name__ == "__main__":
    main()
