"""Repère automatiquement les plans figés ou ratés avant le montage.

Pour chaque clip, on mesure image par image :
- le mouvement (différence moyenne avec l'image précédente, en niveaux de gris réduits) ;
- la netteté (variance du laplacien) ;
- les coupures internes (PySceneDetect si installé, sinon saut brutal de différence).

Verdicts (sévères : un fondu ou un morphing = échec) :
- FIGÉ      : au moins `fige_min` secondes quasi immobiles, ou mouvement moyen trop faible ;
- COUPURE   : changement de plan à l'intérieur d'un clip généré (l'IA a « sauté ») ;
- FONDU     : plusieurs images d'affilée qui se mélangent (forte différence étalée + baisse de netteté) ;
- FLOU      : netteté qui chute nettement sous la médiane du clip (bouillie, flou de mouvement) ;
- OK        : rien de détecté (à confirmer quand même à l'œil sur la planche).

Usage : python -m outils.plans clips/gateau/*.mp4 --sortie /tmp/sortie/plans [--couper]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

W, H = 72, 128  # analyse en basse résolution (format vertical)


@dataclass
class Rapport:
    clip: str
    duree: float
    fps: float
    mouvement_moyen: float
    verdicts: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    moments: list[float] = field(default_factory=list)  # instants à regarder sur la planche

    @property
    def ok(self) -> bool:
        return not self.verdicts


def _fps(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout.strip()
    num, _, den = out.partition("/")
    return float(num) / float(den or 1)


def _images(path: Path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)


def _nettete(frames: np.ndarray) -> np.ndarray:
    lap = (-4 * frames[:, 1:-1, 1:-1] + frames[:, :-2, 1:-1] + frames[:, 2:, 1:-1]
           + frames[:, 1:-1, :-2] + frames[:, 1:-1, 2:])
    return lap.reshape(len(frames), -1).var(axis=1)


def _coupures_scenedetect(path: Path) -> list[float] | None:
    try:
        from scenedetect import ContentDetector, detect
    except ImportError:
        return None
    scenes = detect(str(path), ContentDetector(threshold=27.0, min_scene_len=8))
    return [s[0].get_seconds() for s in scenes[1:]]


def _segments(masque: np.ndarray, min_len: int) -> list[tuple[int, int]]:
    segs, debut = [], None
    for i, v in enumerate(list(masque) + [False]):
        if v and debut is None:
            debut = i
        elif not v and debut is not None:
            if i - debut >= min_len:
                segs.append((debut, i))
            debut = None
    return segs


def analyser(path: Path, fige_min: float = 0.8, seuil_fige: float = 0.35) -> Rapport:
    fps = _fps(path)
    frames = _images(path)
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))  # 0-255
    net = _nettete(frames)
    r = Rapport(path.as_posix(), round(len(frames) / fps, 2), round(fps, 2), round(float(diff.mean()), 2))

    # FIGÉ : mouvement quasi nul pendant fige_min secondes, ou clip globalement immobile
    figes = _segments(diff < seuil_fige, max(2, int(fige_min * fps)))
    if figes:
        total = sum(b - a for a, b in figes) / fps
        r.verdicts.append("FIGÉ")
        r.details.append(f"{total:.1f} s immobiles ("
                         + ", ".join(f"{a / fps:.1f}-{b / fps:.1f} s" for a, b in figes) + ")")
        r.moments += [a / fps for a, _ in figes]
    elif diff.mean() < 0.6:
        r.verdicts.append("FIGÉ")
        r.details.append(f"presque aucun mouvement sur tout le plan (moyenne {diff.mean():.2f})")

    # COUPURE : saut isolé très au-dessus du mouvement habituel
    med = float(np.median(diff)) + 0.3
    coupures = _coupures_scenedetect(path)
    if coupures is None:
        coupures = [(i + 1) / fps for i in np.where(diff > max(18.0, 8 * med))[0]]
    if coupures:
        r.verdicts.append("COUPURE")
        r.details.append("changement de plan à " + ", ".join(f"{t:.1f} s" for t in coupures))
        r.moments += coupures

    # FONDU : différence élevée étalée sur plusieurs images + netteté en baisse au même moment
    net_med = float(np.median(net)) or 1.0
    fondu = (diff > max(4.0, 3 * med)) & (net[1:] < 0.75 * net_med)
    segs = _segments(fondu, max(3, int(0.15 * fps)))
    if segs:
        r.verdicts.append("FONDU")
        r.details.append("mélange d'images à " + ", ".join(f"{a / fps:.1f}-{b / fps:.1f} s" for a, b in segs))
        r.moments += [a / fps for a, _ in segs]

    # FLOU : netteté qui s'effondre (bouillie, morphing) pendant au moins 0,3 s
    flous = _segments(net < 0.45 * net_med, max(3, int(0.3 * fps)))
    if flous:
        r.verdicts.append("FLOU")
        r.details.append("netteté qui chute à " + ", ".join(f"{a / fps:.1f}-{b / fps:.1f} s" for a, b in flous))
        r.moments += [a / fps for a, _ in flous]
    return r


def planche(path: Path, dst: Path, moments: list[float], duree: float) -> None:
    """Planche de 12 images réparties sur le clip, plus les moments suspects."""
    ts = sorted(set([round(duree * i / 12, 2) for i in range(12)] + [round(t, 2) for t in moments]))[:20]
    tmp = dst.with_suffix("")
    tmp.mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(ts):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", str(path), "-frames:v", "1",
                        "-vf", f"scale=180:-2,drawtext=text='{t:.1f}s':x=4:y=4:fontsize=18:fontcolor=yellow"
                        ":box=1:boxcolor=black@0.6", str(tmp / f"{i:02d}.jpg")], check=False)
    cols = min(len(ts), 10)
    rows = (len(ts) + cols - 1) // cols
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", str(tmp / "%02d.jpg"),
                    "-vf", f"tile={cols}x{rows}:padding=4:color=black", "-frames:v", "1", str(dst)], check=False)
    shutil.rmtree(tmp, ignore_errors=True)


def couper(path: Path, dst: Path) -> bool:
    """Retire les passages immobiles avec auto-editor (si installé)."""
    exe = shutil.which("auto-editor")
    if not exe:
        return False
    res = subprocess.run([exe, str(path), "--edit", "motion:threshold=0.02", "--margin", "0.2s",
                          "--no-open", "-o", str(dst)], capture_output=True, text=True)
    return res.returncode == 0 and dst.exists()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--sortie", default="sortie-plans")
    ap.add_argument("--couper", action="store_true", help="version raccourcie sans passages figés (auto-editor)")
    ap.add_argument("--sans-planche", action="store_true")
    a = ap.parse_args()
    out = Path(a.sortie)
    out.mkdir(parents=True, exist_ok=True)
    rapports = []
    for c in a.clips:
        p = Path(c)
        r = analyser(p)
        rapports.append(r)
        if not a.sans_planche:
            planche(p, out / f"{p.stem}-planche.jpg", r.moments, r.duree)
        if a.couper and "FIGÉ" in r.verdicts and couper(p, out / f"{p.stem}-coupe.mp4"):
            r.details.append(f"version sans passage figé : {p.stem}-coupe.mp4")
    lignes = ["# Contrôle automatique des plans", "",
              "Sévère : un fondu, un flou ou une coupure dans un plan = à régénérer. "
              "« OK » veut seulement dire que rien n'a été détecté : regarder quand même la planche.", "",
              "| Plan | Durée | Mouvement | Verdict | Détail |", "|---|---|---|---|---|"]
    for r in rapports:
        lignes.append(f"| {Path(r.clip).name} | {r.duree} s | {r.mouvement_moyen} | "
                      f"{'OK' if r.ok else ' + '.join(r.verdicts)} | {'; '.join(r.details)} |")
    (out / "rapport.md").write_text("\n".join(lignes) + "\n")
    (out / "rapport.json").write_text(json.dumps([r.__dict__ for r in rapports], ensure_ascii=False, indent=1))
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
