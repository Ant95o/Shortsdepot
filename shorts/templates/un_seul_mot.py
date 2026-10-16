"""Gabarit « Réponds en un seul mot » : une conversation avec une IA qui ne répond qu'en un mot.

Déroulé : accroche lue en voix off, puis pour chaque question une bulle bleue
(lue par le narrateur), trois points qui s'animent, et la réponse en un mot
(lue par une seconde voix). Fin sur un appel à commenter.
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from ..media import FPS, HEIGHT, WIDTH, encoder, mix_clips
from ..style import ease_out, font, vertical_gradient, wrap
from ..tts import synthesize

BG_TOP, BG_BOTTOM = (13, 15, 20), (22, 26, 36)
YELLOW, WHITE, BLUE, GREY = (255, 212, 59), (255, 255, 255), (47, 107, 255), (38, 42, 51)

# Zone sûre : l'interface TikTok/Reels couvre le bas (~350 px) et la droite (~110 px).
LEFT, RIGHT = 70, WIDTH - 110
CHAT_TOP, CHAT_BOTTOM = 480, 1500
AVATAR = 84
GAP = 34
POP = 0.2
SCROLL = 0.3


@dataclass
class Bubble:
    image: Image.Image
    x: int
    y: int  # position dans le fil, avant défilement
    appear: float


def _bubble(lines: list[str], fnt, fill, text_fill, pad_x=38, pad_y=26, radius=44) -> Image.Image:
    line_h = int(fnt.size * 1.18)
    w = int(max(fnt.getlength(l) for l in lines)) + 2 * pad_x
    h = line_h * len(lines) + 2 * pad_y
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=fill)
    for i, line in enumerate(lines):
        d.text((pad_x, pad_y + i * line_h + (line_h - fnt.size) // 2 - 4), line, font=fnt, fill=text_fill)
    return img


def _avatar() -> Image.Image:
    img = Image.new("RGBA", (AVATAR, AVATAR), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, AVATAR - 1, AVATAR - 1), fill=YELLOW)
    d.text((AVATAR / 2, AVATAR / 2), "IA", font=font("black", 36), fill=BG_TOP, anchor="mm")
    return img


def _typing(t: float) -> Image.Image:
    img = Image.new("RGBA", (190, 104), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, 189, 103), radius=44, fill=GREY)
    for i in range(3):
        phase = (t * 2.2 - i * 0.22) % 1.0
        lift = 10 * max(0.0, 1 - abs(phase - 0.25) * 4)
        alpha = int(140 + 115 * (lift / 10))
        cx, cy = 52 + i * 43, 52 - lift
        d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=(200, 205, 215, alpha))
    return img


def _paste_pop(layer: Image.Image, img: Image.Image, x: int, y: int, age: float) -> None:
    """Colle une bulle avec une petite animation d'apparition (zoom + fondu)."""
    if age < 0:
        return
    k = ease_out(min(1.0, age / POP))
    if k < 1:
        scale = 0.85 + 0.15 * k
        w, h = max(1, int(img.width * scale)), max(1, int(img.height * scale))
        small = img.resize((w, h), Image.BILINEAR)
        alpha = small.getchannel("A").point(lambda a: int(a * k))
        small.putalpha(alpha)
        img, x, y = small, x + (img.width - w) // 2, y + (img.height - h) // 2
    layer.alpha_composite(img, (int(x), int(y)))


def render(spec: dict, workdir: Path, out: Path, providers: list[str]) -> dict:
    voices = spec["voix"]
    clips, log = [], []

    def say(key: str, text: str, start: float) -> float:
        path = workdir / f"voix_{len(clips):02d}.wav"
        duration, provider = synthesize(text, voices[key], path, providers)
        clips.append((start, path))
        log.append(provider)
        return duration

    # 1. Voix et minutage
    t = 0.25
    hook_end = t + say("narrateur", spec["accroche"], t)
    t = hook_end + 0.35
    events = []
    for item in spec["questions"]:
        q_start = t
        dq = say("narrateur", item["question"], q_start)
        typing_start = q_start + dq + 0.1
        a_start = typing_start + 0.65
        da = say("ia", item["reponse"], a_start)
        events.append((item, q_start, typing_start, a_start))
        t = a_start + da + 0.5
    cta_start = t + 0.2
    total = cta_start + say("narrateur", spec["appel"], cta_start) + 1.4

    audio = workdir / "voix.wav"
    mix_clips(clips, total, audio)

    # 2. Bulles pré-dessinées et positions dans le fil
    q_font, a_font = font("semibold", 62), font("black", 96)
    bubbles, typings, y = [], [], CHAT_TOP
    max_q = 780 - 76
    for item, q_start, typing_start, a_start in events:
        q_img = _bubble(wrap(item["question"], q_font, max_q), q_font, BLUE, WHITE)
        bubbles.append(Bubble(q_img, RIGHT - q_img.width, y, q_start))
        y += q_img.height + GAP
        a_img = _bubble([item["reponse"]], a_font, GREY, WHITE, pad_y=22)
        a_x = LEFT + AVATAR + 20
        typings.append((a_x, y, typing_start, a_start))
        bubbles.append(Bubble(a_img, a_x, y, a_start))
        y += a_img.height + GAP

    # Défilement : la dernière bulle apparue reste au-dessus de CHAT_BOTTOM.
    scroll_events, prev = [], 0.0
    for b in bubbles:
        target = max(0.0, b.y + b.image.height - CHAT_BOTTOM)
        if target > prev:
            scroll_events.append((b.appear, prev, target))
            prev = target

    def offset(now: float) -> float:
        value = 0.0
        for start, frm, to in scroll_events:
            if now >= start:
                value = frm + (to - frm) * ease_out(min(1.0, (now - start) / SCROLL))
        return value

    # 3. Éléments fixes
    background = vertical_gradient(WIDTH, HEIGHT, BG_TOP, BG_BOTTOM).convert("RGBA")
    d = ImageDraw.Draw(background)
    d.text((WIDTH / 2, 215), "RÉPONDS EN", font=font("black", 92), fill=WHITE, anchor="mm")
    d.text((WIDTH / 2, 325), "UN SEUL MOT", font=font("black", 124), fill=YELLOW, anchor="mm")
    avatar = _avatar()
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle((0, CHAT_TOP, WIDTH, CHAT_BOTTOM + 60), fill=255)
    for i in range(70):  # fondu en haut du fil quand ça défile
        md.line((0, CHAT_TOP - 70 + i, WIDTH, CHAT_TOP - 70 + i), fill=int(255 * i / 70))

    hook_font = font("bold", 76)
    hook_lines = wrap(spec["accroche"], hook_font, 860)
    cta_font = font("black", 78)
    cta_lines = wrap(spec["appel"], cta_font, 860)

    def centered_block(layer, lines, fnt, alpha, center_y, fill=WHITE):
        dl = ImageDraw.Draw(layer)
        lh = int(fnt.size * 1.22)
        top = center_y - lh * len(lines) / 2
        for i, line in enumerate(lines):
            dl.text((WIDTH / 2, top + i * lh + lh / 2), line, font=fnt, fill=(*fill, alpha), anchor="mm")

    # 4. Rendu image par image
    proc = encoder(audio, out)
    frames = int(total * FPS)
    for n in range(frames):
        now = n / FPS
        frame = background.copy()
        chat = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        off = offset(now)
        for x, ty, t_start, t_end in typings:
            if t_start <= now < t_end:
                chat.alpha_composite(_typing(now - t_start), (x, int(ty - off)))
        for b in bubbles:
            if now >= b.appear:
                yy = b.y - off
                if yy + b.image.height > CHAT_TOP - 80 and yy < HEIGHT:
                    _paste_pop(chat, b.image, b.x, yy, now - b.appear)
                    if b.x != RIGHT - b.image.width:  # bulle de l'IA : avatar à gauche
                        _paste_pop(chat, avatar, LEFT, yy + (b.image.height - AVATAR) // 2, now - b.appear)
        chat.putalpha(ImageChops.multiply(chat.getchannel("A"), mask))
        frame.alpha_composite(chat)

        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        if now < events[0][1] + 0.25:  # accroche, effacée quand la première question arrive
            fade = min(1.0, now / 0.3) * (1 - min(1.0, max(0.0, now - events[0][1]) / 0.25))
            centered_block(overlay, hook_lines, hook_font, int(255 * fade), 900)
        if now >= cta_start:
            k = ease_out(min(1.0, (now - cta_start) / 0.35))
            od = ImageDraw.Draw(overlay)
            od.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0, int(150 * k)))
            card_h = int(cta_font.size * 1.22) * len(cta_lines) + 120
            od.rounded_rectangle((LEFT, 1000 - card_h / 2, WIDTH - LEFT, 1000 + card_h / 2), radius=48,
                                 fill=(*BG_TOP, int(240 * k)), outline=(*YELLOW, int(255 * k)), width=5)
            centered_block(overlay, cta_lines, cta_font, int(255 * k), 1000, fill=YELLOW)
        frame.alpha_composite(overlay)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("L'encodage FFmpeg a échoué")

    return {"duree_s": round(total, 2), "voix": sorted(set(log))}
