"""Gabarit « clips commentés » : des clips (vidéo IA, rushes libres) montés en 9:16,
avec une voix de commentateur, des sous-titres phrase par phrase, un tableau de
score qui change au moment du but, et une carte de fin.

Les clips sont recadrés pour remplir l'écran vertical ; si le commentaire dure plus
longtemps que les clips, la dernière image est prolongée.
"""

from pathlib import Path

from PIL import Image, ImageDraw

from ..media import FPS, HEIGHT, WIDTH, audio_duration, mix_clips, run_ffmpeg
from ..style import font, wrap
from ..tts import synthesize

YELLOW, WHITE, DARK = (255, 212, 59), (255, 255, 255), (13, 15, 20)
CAPTION_Y = 1330  # au-dessus de la zone couverte par l'interface TikTok/Reels


def _caption(text: str, path: Path) -> None:
    fnt = font("black", 70)
    lines = wrap(text.upper(), fnt, 900)
    lh = int(fnt.size * 1.18)
    img = Image.new("RGBA", (WIDTH, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((WIDTH / 2, 20 + i * lh + lh / 2), line, font=fnt, fill=WHITE, anchor="mm",
               stroke_width=8, stroke_fill=(0, 0, 0))
    img.save(path)


def _scoreboard(left: str, right: str, score: str, minute: str, path: Path, highlight: bool) -> None:
    fnt, sfnt = font("black", 46), font("black", 50)
    text_l, text_r = left.upper(), right.upper()
    w_l, w_r, w_s = fnt.getlength(text_l), fnt.getlength(text_r), sfnt.getlength(score)
    w_m = fnt.getlength(minute)
    pad, gap = 30, 26
    width = int(pad + w_l + gap + w_s + 2 * 24 + gap + w_r + gap + w_m + pad)
    img = Image.new("RGBA", (width, 92), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, width - 1, 91), radius=20, fill=(*DARK, 225))
    x = pad
    d.text((x, 46), text_l, font=fnt, fill=WHITE, anchor="lm")
    x += w_l + gap
    box = (x, 12, x + w_s + 48, 80)
    d.rounded_rectangle(box, radius=12, fill=YELLOW if highlight else WHITE)
    d.text(((box[0] + box[2]) / 2, 46), score, font=sfnt, fill=DARK, anchor="mm")
    x = box[2] + gap
    d.text((x, 46), text_r, font=fnt, fill=WHITE, anchor="lm")
    x += w_r + gap
    d.text((x, 46), minute, font=fnt, fill=YELLOW, anchor="lm")
    img.save(path)


def _end_card(text: str, path: Path) -> None:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 165))
    d = ImageDraw.Draw(img)
    fnt = font("black", 96)
    lines = wrap(text, fnt, 880)
    lh = int(fnt.size * 1.2)
    top = 900 - lh * len(lines) / 2
    for i, line in enumerate(lines):
        d.text((WIDTH / 2, top + i * lh + lh / 2), line, font=fnt, fill=YELLOW, anchor="mm",
               stroke_width=6, stroke_fill=(0, 0, 0))
    img.save(path)


def render(spec: dict, workdir: Path, out: Path, providers: list[str]) -> dict:
    voice = spec["voix"]["commentateur"]

    # 1. Commentaire : chaque réplique démarre à son instant « a », ou juste après la précédente.
    lines, clips, log, t = [], [], [], 0.3
    for i, item in enumerate(spec["commentaire"]):
        start = max(t, float(item.get("a", t)))
        path = workdir / f"voix_{i:02d}.wav"
        duration, provider = synthesize(item["texte"], voice, path, providers)
        log.append(provider)
        clips.append((start, path))
        lines.append((start, start + duration, item))
        t = start + duration + float(item.get("pause", 0.15))

    sources = [Path(c) for c in spec["clips"]]
    clips_total = sum(audio_duration(s) for s in sources)
    end = spec.get("fin", {})
    end_len = float(end.get("duree", 2.5)) if end else 0.0
    body = max(clips_total, t)
    total = body + end_len

    audio = workdir / "voix.wav"
    mix_clips(clips, total, audio)

    # 2. Éléments graphiques
    sb = spec.get("score")
    goal_at = next((s for s, _, item in lines if item.get("but")), None)
    images, overlays = [], []  # overlays : (index d'entrée, x, y, début, fin)

    def add(path: Path, x, y, start: float, stop: float) -> None:
        images.append(path)
        overlays.append((len(images), x, y, start, stop))

    for i, (start, stop, item) in enumerate(lines):
        p = workdir / f"st_{i:02d}.png"
        _caption(item["texte"], p)
        add(p, 0, CAPTION_Y, start, stop + 0.1)
    if sb:
        before, after = workdir / "score_avant.png", workdir / "score_apres.png"
        _scoreboard(sb["gauche"], sb["droite"], sb["avant"], sb.get("minute", ""), before, False)
        _scoreboard(sb["gauche"], sb["droite"], sb["apres"], sb.get("minute", ""), after, True)
        switch = goal_at if goal_at is not None else body
        add(before, "(W-w)/2", 150, 0, switch)
        add(after, "(W-w)/2", 150, switch, body)
    if end:
        card = workdir / "fin.png"
        _end_card(end["texte"], card)
        add(card, 0, 0, body, total + 1)

    # 3. Graphe FFmpeg : clips recadrés en 9:16 et mis bout à bout, image figée jusqu'à la fin,
    #    puis superpositions dans l'ordre.
    n = len(sources)
    args = []
    for s in sources:
        args += ["-i", str(s)]
    for img in images:
        args += ["-loop", "1", "-i", str(img)]
    args += ["-i", str(audio)]
    filters = []
    for i in range(n):
        filters.append(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},fps={FPS},setsar=1,format=yuv420p[c{i}]"
        )
    filters.append("".join(f"[c{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
                   f"tpad=stop_mode=clone:stop_duration={total - clips_total + 1:.2f}[v0]")
    current = "v0"
    for k, (idx, x, y, start, stop) in enumerate(overlays, start=1):
        filters.append(f"[{current}][{n + idx - 1}:v]overlay=x={x}:y={y}:"
                       f"enable='between(t,{start:.2f},{stop:.2f})':shortest=0:eof_action=repeat[v{k}]")
        current = f"v{k}"
    run_ffmpeg([
        *args, "-filter_complex", ";".join(filters),
        "-map", f"[{current}]", "-map", f"{n + len(images)}:a", "-t", f"{total:.2f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2), "-keyint_min", str(FPS * 2), "-sc_threshold", "0",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(out),
    ])
    return {"duree_s": round(total, 2), "voix": sorted(set(log))}
