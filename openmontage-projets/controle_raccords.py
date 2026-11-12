"""Contrôle des raccords (méthode OpenMontage « AI clip chaining » : inspecter la fin du plan N
contre le début du plan N+1) AVANT de livrer, et dès les images Gemini AVANT d'animer.

  python openmontage-projets/controle_raccords.py images SORTIE.jpg img1.jpg img2.jpg …
  python openmontage-projets/controle_raccords.py clips  SORTIE.jpg clip1.mp4:48 clip2.mp4:48 …   (:N = images gardées)

Produit une planche : une ligne par raccord, « fin N | début N+1 », numérotée. Grille de lecture :
openmontage-projets/controle-raccords.md.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

L, H = 270, 480  # vignette 9:16


def image(src: str, dst: Path, seek: str | None = None, fin: int | None = None) -> None:
    args = ["ffmpeg", "-v", "error", "-y"]
    if fin is not None:  # dernière image gardée au montage
        args += ["-i", src, "-vf", f"select=eq(n\\,{fin - 1}),scale={L}:{H}:force_original_aspect_ratio=increase,crop={L}:{H}"]
    else:
        args += ["-i", src, "-vf", f"scale={L}:{H}:force_original_aspect_ratio=increase,crop={L}:{H}"]
    subprocess.run(args + ["-frames:v", "1", "-q:v", "3", str(dst)], check=True)


def main(mode: str, sortie: str, items: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        debuts, fins = [], []
        for i, it in enumerate(items):
            src, _, n = it.partition(":")
            d, f = tmp / f"d{i}.jpg", tmp / f"f{i}.jpg"
            image(src, d)
            if mode == "clips":
                image(src, f, fin=int(n) if n else int(subprocess.check_output(
                    ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                     "stream=nb_read_frames", "-of", "csv=p=0", src]).strip()))
            else:
                f = d
            debuts.append(d)
            fins.append(f)
        lignes = []
        for i in range(len(items) - 1):
            ligne = tmp / f"l{i}.jpg"
            txt = f"drawtext=text='{i + 1} → {i + 2}':fontcolor=yellow:fontsize=34:borderw=3:x=10:y=10"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(fins[i]), "-i", str(debuts[i + 1]),
                            "-filter_complex", f"[0][1]hstack=inputs=2,pad=iw+20:ih+10:10:5:gray,{txt}",
                            "-q:v", "3", str(ligne)], check=True)
            lignes.append(ligne)
        # deux raccords par rangée pour rester lisible sur téléphone
        entrees = sum([["-i", str(p)] for p in lignes], [])
        n = len(lignes)
        cols = 2
        rangs = (n + cols - 1) // cols
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entrees, "-filter_complex",
                        "".join(f"[{i}]" for i in range(n)) + f"xstack=inputs={n}:layout=" +
                        "|".join(f"{(i % cols) * (2 * L + 20)}_{(i // cols) * (H + 10)}" for i in range(n)) +
                        ":fill=gray" if n > 1 else "null", "-q:v", "3", sortie], check=True)
        print(f"{sortie} : {n} raccords sur {rangs} rangées")


if __name__ == "__main__":
    if len(sys.argv) < 5 or sys.argv[1] not in ("images", "clips"):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
