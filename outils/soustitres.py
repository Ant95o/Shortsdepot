"""Sous-titres FR mot à mot, calés sur la voix, avec WhisperX (repli : faster-whisper).

- Si le texte exact de la voix off est fourni (`--texte`), on ne transcrit pas : WhisperX aligne
  ce texte sur l'audio (zéro faute d'orthographe, timing au mot près).
- Sinon : transcription Whisper (modèle `small` par défaut, CPU) puis alignement mot à mot.

Sorties : .srt (classique), .ass (style AI Story : gros texte blanc contouré, mot prononcé en jaune,
2-4 mots à la fois) et, si `--video` est donnée, la vidéo avec sous-titres incrustés.

Usage : python -m outils.soustitres voix.wav --texte "..." --video plan.mp4 --sortie /tmp/sortie/st
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def _wav16k(src: Path, dst: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(dst)],
                   check=True)


def _duree(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout)


def mots_whisperx(audio: Path, texte: str | None, modele: str) -> list[dict]:
    import whisperx

    wav = whisperx.load_audio(str(audio))
    if texte:
        segments = [{"text": texte, "start": 0.0, "end": len(wav) / 16000}]
    else:
        m = whisperx.load_model(modele, "cpu", compute_type="int8", language="fr")
        segments = m.transcribe(wav, batch_size=4, language="fr")["segments"]
    align, meta = whisperx.load_align_model(language_code="fr", device="cpu")
    res = whisperx.align(segments, align, meta, wav, "cpu", return_char_alignments=False)
    mots = [w for s in res["segments"] for w in s.get("words", [])]
    # un mot sans horodatage (nombre, sigle) prend la place entre ses voisins
    for i, w in enumerate(mots):
        if "start" not in w:
            w["start"] = mots[i - 1]["end"] if i else 0.0
            nxt = next((x["start"] for x in mots[i + 1:] if "start" in x), w["start"] + 0.3)
            w["end"] = max(w["start"] + 0.1, nxt)
    return [{"mot": w["word"].strip(), "debut": float(w["start"]), "fin": float(w["end"])} for w in mots]


def mots_faster_whisper(audio: Path, modele: str) -> list[dict]:
    from faster_whisper import WhisperModel

    m = WhisperModel(modele, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(audio), language="fr", word_timestamps=True)
    return [{"mot": w.word.strip(), "debut": w.start, "fin": w.end} for s in segs for w in s.words]


def _groupes(mots: list[dict], max_mots: int = 3, max_car: int = 16) -> list[list[dict]]:
    groupes, cur = [], []
    for w in mots:
        texte = " ".join(x["mot"] for x in cur + [w])
        pause = cur and w["debut"] - cur[-1]["fin"] > 0.35
        if cur and (len(cur) >= max_mots or len(texte) > max_car or pause):
            groupes.append(cur)
            cur = []
        cur.append(w)
        if w["mot"][-1:] in ".!?…":
            groupes.append(cur)
            cur = []
    if cur:
        groupes.append(cur)
    return groupes


def _t_srt(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _t_ass(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ecrire_srt(mots: list[dict], dst: Path) -> None:
    blocs = []
    for i, g in enumerate(_groupes(mots, 5, 32), 1):
        blocs.append(f"{i}\n{_t_srt(g[0]['debut'])} --> {_t_srt(g[-1]['fin'])}\n" + " ".join(w["mot"] for w in g))
    dst.write_text("\n\n".join(blocs) + "\n")


ASS_ENTETE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: AIStory,DejaVu Sans,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ecrire_ass(mots: list[dict], dst: Path) -> None:
    """Groupe de 2-3 mots affiché, le mot prononcé passe en jaune."""
    lignes = []
    for g in _groupes(mots):
        for j, w in enumerate(g):
            fin = g[j + 1]["debut"] if j + 1 < len(g) else w["fin"] + 0.15
            texte = " ".join(("{\\c&H00FFFF&}" + x["mot"].upper() + "{\\c&HFFFFFF&}") if k == j
                             else x["mot"].upper() for k, x in enumerate(g))
            lignes.append(f"Dialogue: 0,{_t_ass(w['debut'])},{_t_ass(fin)},AIStory,,0,0,0,,{texte}")
    dst.write_text(ASS_ENTETE + "\n".join(lignes) + "\n")


def incruster(video: Path, ass: Path, audio: Path | None, dst: Path) -> None:
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video)]
    if audio:
        cmd += ["-i", str(audio), "-map", "0:v", "-map", "1:a", "-shortest"]
    cmd += ["-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass={ass}",
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", str(dst)]
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", help="voix off (wav/mp3) ou vidéo avec son")
    ap.add_argument("--texte", help="texte exact de la voix off (alignement sans transcription)")
    ap.add_argument("--modele", default="small")
    ap.add_argument("--video", help="vidéo sur laquelle incruster les sous-titres")
    ap.add_argument("--sortie", default="sortie-soustitres")
    a = ap.parse_args()
    out = Path(a.sortie)
    out.mkdir(parents=True, exist_ok=True)
    nom = Path(a.audio).stem
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "a.wav"
        _wav16k(Path(a.audio), wav)
        try:
            mots, moteur = mots_whisperx(wav, a.texte, a.modele), "whisperx"
        except Exception as exc:  # bascule
            print(f"WhisperX indisponible ({exc}), repli sur faster-whisper")
            mots, moteur = mots_faster_whisper(wav, a.modele), "faster-whisper"
    (out / f"{nom}-mots.json").write_text(json.dumps(mots, ensure_ascii=False, indent=1))
    ecrire_srt(mots, out / f"{nom}.srt")
    ecrire_ass(mots, out / f"{nom}.ass")
    if a.video:
        incruster(Path(a.video), out / f"{nom}.ass", Path(a.audio), out / f"{nom}-soustitre.mp4")
    print(f"{len(mots)} mots ({moteur}) : " + " ".join(f"{w['mot']}@{w['debut']:.2f}" for w in mots[:12]))


if __name__ == "__main__":
    main()
