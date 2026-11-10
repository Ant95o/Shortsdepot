"""Prépare un essai du labo (repos open source sur Kaggle).

  python labo/labo.py preparer FICHE UTILISATEUR   # build/labo-donnees (jeu de données) et build/labo-kernel

Les fichiers d'entrée (vidéos, images) voyagent dans un jeu de données Kaggle privé,
« shortsdepot-labo-entrees » : pas de limite de 1 Mo comme pour le script.
"""

import json
import shutil
import sys
from pathlib import Path

import yaml

DONNEES, KERNEL = Path("build/labo-donnees"), Path("build/labo-kernel")
SLUG_DONNEES, SLUG_KERNEL = "shortsdepot-labo-entrees", "shortsdepot-labo"


def preparer(fiche: Path, user: str) -> None:
    taches = yaml.safe_load(fiche.read_text(encoding="utf-8"))["taches"]
    shutil.rmtree(DONNEES, ignore_errors=True)
    DONNEES.mkdir(parents=True)
    for t in taches:
        for cle in ("entree", "debut", "fin"):
            if cle in t:
                src = Path(t[cle])
                nom = src.as_posix().replace("/", "__")
                shutil.copy(src, DONNEES / nom)
                t[cle] = nom
    (DONNEES / "taches.json").write_text(json.dumps(taches, ensure_ascii=False, indent=2), encoding="utf-8")
    (DONNEES / "dataset-metadata.json").write_text(json.dumps({
        "title": SLUG_DONNEES, "id": f"{user}/{SLUG_DONNEES}", "licenses": [{"name": "CC0-1.0"}]}, indent=2))
    shutil.rmtree(KERNEL, ignore_errors=True)
    KERNEL.mkdir(parents=True)
    shutil.copy(Path(__file__).with_name("job.py"), KERNEL / "job.py")
    (KERNEL / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{SLUG_KERNEL}", "title": SLUG_KERNEL, "code_file": "job.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [f"{user}/{SLUG_DONNEES}"], "competition_sources": [], "kernel_sources": [],
    }, indent=2))
    print(f"{len(taches)} tâche(s) ; entrées : {', '.join(p.name for p in DONNEES.iterdir())}")


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "preparer":
        sys.exit(__doc__)
    preparer(Path(sys.argv[2]), sys.argv[3])
