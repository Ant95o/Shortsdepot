"""Essai des Spaces Hugging Face gratuits (ZeroGPU) qui font tourner Wan 2.2 14B.

Lancé par .github/workflows/essai-hf.yml. Étape « api » : affiche les paramètres de
chaque Space. Étape « generer » : produit un plan de test dans essais/sortie/.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import inspect
import os

from gradio_client import Client as _Client, handle_file

SPACES = {
    "animate": "alexnasa/Wan2.2-Animate-ZEROGPU",
    "i2v": "Saravutw/WAN2.2_I2V_LIGHTNING_4-8step_custom",
    "image": "black-forest-labs/FLUX.1-schnell",
    "image_dev": "black-forest-labs/FLUX.1-dev",
    "retouche": "black-forest-labs/FLUX.1-Kontext-Dev",
    "profondeur": "black-forest-labs/FLUX.1-Depth-dev",
}
OUT = Path("essais/sortie")


def Client(space):
    """Client Gradio, avec le jeton du compte Hugging Face gratuit s'il existe (quota GPU plus grand)."""
    jeton = os.environ.get("HF_TOKEN") or None
    nom = "token" if "token" in inspect.signature(_Client.__init__).parameters else "hf_token"
    return _Client(space, **{nom: jeton})


def api() -> None:
    for nom, space in SPACES.items():
        print(f"===== {nom} : {space}", flush=True)
        try:
            Client(space).view_api(print_info=True)
        except Exception as exc:
            print(f"indisponible : {exc}", flush=True)


def copier(resultat, nom: str) -> None:
    """Copie le ou les fichiers renvoyés par un Space dans essais/sortie/."""
    OUT.mkdir(parents=True, exist_ok=True)
    fichiers = []

    def chercher(x):
        if isinstance(x, str) and Path(x).is_file():
            fichiers.append(Path(x))
        elif isinstance(x, dict):
            for v in x.values():
                chercher(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                chercher(v)

    chercher(resultat)
    print(f"{nom} : {resultat}", flush=True)
    for i, f in enumerate(fichiers):
        shutil.copy(f, OUT / f"{nom}{'' if i == 0 else i}{f.suffix}")


CHAT = ("Full body photo of an anthropomorphic ginger tabby cat football player standing upright on two legs, "
        "wearing a plain red football shirt with white sleeves, white shorts, red socks and boots, "
        "realistic fur, confident expression, night stadium background, cinematic lighting, vertical framing")
SCENE = ("Low angle TV broadcast shot of a night football match in a packed stadium. In the foreground an "
         "anthropomorphic ginger tabby cat in a red shirt with white sleeves dribbles the ball toward goal. "
         "In the background a golden retriever dog goalkeeper wearing green gloves and a green jersey runs out of "
         "his goal, and two dog defenders, a bulldog and a German shepherd in green jerseys, chase on four paws. "
         "Every player is an animal, the only humans are tiny blurry spectators in the stands. Realistic fur, "
         "cinematic floodlights, sharp details, vertical framing")
MOUVEMENT = ("The ginger cat sprints with the ball and softly chips it over the golden retriever goalkeeper who "
             "dives with his paws, the ball loops into the net, the dog defenders stop and stare, the crowd erupts. "
             "All players stay animals, smooth realistic motion, TV broadcast camera follows the action, sharp details")
NEGATIF = "human players, human legs, human body, people on the pitch, man, woman, human faces, extra legs, deformed paws, blurry, low quality, text, watermark, logos"


def essai(nom, fn):
    """Lance un essai sans arrêter les suivants si le Space refuse (quota, file d'attente…)."""
    print(f"===== {nom}", flush=True)
    try:
        return fn()
    except Exception as exc:
        print(f"{nom} : échec : {exc}", flush=True)


def image(prompt, nom):
    try:  # FLUX.1-dev suit mieux le prompt (aucun humain sur le terrain) ; schnell en secours
        res = Client(SPACES["image_dev"]).predict(prompt=prompt, seed=7, randomize_seed=False, width=576, height=1024,
                                                  guidance_scale=3.5, num_inference_steps=28, api_name="/infer")
    except Exception as exc:
        print(f"FLUX.1-dev indisponible ({exc}), FLUX.1-schnell à la place", flush=True)
        res = Client(SPACES["image"]).predict(prompt=prompt, seed=7, randomize_seed=False, width=576, height=1024,
                                              num_inference_steps=4, api_name="/infer")
    copier(res, nom)
    return next(OUT.glob(f"{nom}.*"))


def generer() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chat = essai("image du chat", lambda: image(CHAT, "chat")) if "animate" in sys.argv[2:] else None
    scene = essai("image de la scène", lambda: image(SCENE, "scene"))
    # 20/10 : Animate garde le joueur humain (visage brouillé), il ne sait pas le changer en chat.
    if chat and "animate" in sys.argv[2:]:
        # Remplacement du joueur par le chat sur le lob (0,5 à 5 s de la référence Kling).
        extrait = OUT / "reference_lob.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.5", "-t", "4.5", "-i", "refs/ozil-but.mp4",
                        "-an", str(extrait)], check=True)
        for duree in (4, 2):
            ok = essai(f"animate {duree} s", lambda: copier(Client(SPACES["animate"]).predict(
                input_video=handle_file(str(extrait)), max_duration_s=duree, edited_frame=handle_file(str(chat)),
                rc_str="Character Swap", resolution_choice="Low Res", api_name="/animate_scene"), f"animate_{duree}s") or True)
            if ok:
                break
    if scene:
        essai("i2v", lambda: copier(Client(SPACES["i2v"]).predict(
            input_image=handle_file(str(scene)), last_image=None, prompt=MOUVEMENT, steps=8, negative_prompt=NEGATIF,
            duration_seconds=5, guidance_scale=1, guidance_scale_2=1, seed=42, randomize_seed=False, quality=10,
            scheduler="UniPCMultistep", flow_shift=3.0, frame_multiplier=16, safe_mode=False, video_component=True,
            api_name="/generate_video"), "i2v"))


# Images clés de la référence (secondes) et mouvement attendu entre deux clés : la vidéo générée
# part de l'une et arrive sur la suivante, donc elle suit les positions de l'original.
CLES = [0.5, 2.75, 5.0]
MOUVEMENTS = [
    "The ginger cat runs with the ball and softly chips it over the golden retriever goalkeeper who rushes out "
    "and dives, same camera movement as a TV broadcast, smooth realistic motion",
    "The golden retriever goalkeeper falls on the grass while the ball loops high over him, the ginger cat keeps "
    "running and watches the ball, same camera movement as a TV broadcast, smooth realistic motion",
]
# Kontext recompose la scène si on lui demande de tout changer : un joueur à la fois.
RETOUCHES = [
    "Change only the player in the yellow shirt into an anthropomorphic ginger tabby cat wearing a red shirt with "
    "white sleeves and white shorts. Keep his exact pose, position and size. Do not change anything else.",
    "Change only the goalkeeper into an anthropomorphic golden retriever dog goalkeeper in a green jersey with "
    "gloves. Keep his exact pose, position and size. Do not change anything else.",
]
# Le modèle « profondeur » redessine toute l'image en suivant la silhouette exacte de l'originale.
PROFONDEUR = ("TV broadcast shot of a night football match in a packed stadium. The attacker is an anthropomorphic "
              "ginger tabby cat in a red shirt with white sleeves, the goalkeeper is an anthropomorphic golden "
              "retriever dog in a green jersey and gloves. Realistic fur, cinematic floodlights, sharp details")


def retoucher(brute: Path, nom: str) -> Path:
    """Redessine l'image clé en chats contre chiens en suivant la profondeur (donc les poses) de l'originale.

    20/10 : Kontext (retouche) recadre en gros plan et perd le lob, même joueur par joueur ;
    FLUX.1-Depth garde la pose (plongeon du gardien). Un seul appel par image pour ménager le quota.
    """
    res = Client(SPACES["profondeur"]).predict(control_image=handle_file(str(brute)), prompt=PROFONDEUR, seed=7,
                                               randomize_seed=False, width=576, height=1024, guidance_scale=10,
                                               num_inference_steps=28, api_name="/infer")
    copier(res, nom)
    return next(OUT.glob(f"{nom}.*"))


def cles() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    images = []
    for i, t in enumerate(CLES):
        brute = OUT / f"cle{i}_ref.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", "refs/ozil-but.mp4",
                        "-frames:v", "1", str(brute)], check=True)
        images.append(retoucher(brute, f"cle{i}"))
    if "images" in sys.argv[2:]:
        return
    for i, mouvement in enumerate(MOUVEMENTS):
        duree = CLES[i + 1] - CLES[i]
        essai(f"segment {i}", lambda: copier(Client(SPACES["i2v"]).predict(
            input_image=handle_file(str(images[i])), last_image=handle_file(str(images[i + 1])), prompt=mouvement,
            steps=8, negative_prompt=NEGATIF, duration_seconds=duree, guidance_scale=1, guidance_scale_2=1, seed=42,
            randomize_seed=False, quality=10, scheduler="UniPCMultistep", flow_shift=3.0, frame_multiplier=16,
            safe_mode=False, video_component=True, api_name="/generate_video"), f"segment{i}"))


# Plans des trends du 21/10 : image de départ (FLUX) puis animation (Wan 2.2 14B).
PLANS_TRENDS = [
    ("ramalama",
     "Low angle shot at floor level in a dark gothic hallway lit by candles, an anthropomorphic ginger tabby cat "
     "dressed as Dracula with a long black and red cape walks toward the camera on two legs, only its paws, legs "
     "and the bottom of the cape are visible in the lower part of the frame, realistic fur, cinematic, vertical framing",
     "The cat struts confidently toward the camera to the beat, the camera slowly tilts up from the paws to reveal "
     "the whole cat dressed as Dracula, who stops, swirls his cape and shows his little vampire fangs, "
     "smooth realistic motion, cinematic lighting", 5),
    ("saxo",
     "Cozy living room at dusk, a fluffy ginger tabby cat sits on a wooden shelf next to a fragile blue ceramic "
     "vase standing right at the edge, the cat stares straight at the camera with a mischievous look, realistic "
     "fur, cinematic, vertical framing",
     "Slow dramatic push-in on the cat, the cat keeps staring at the camera, then slowly raises one paw toward "
     "the vase, the vase starts to wobble at the edge of the shelf, tension builds, smooth realistic motion", 4),
]


def trends() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for nom, prompt_image, mouvement, duree in PLANS_TRENDS:
        if [a for a in sys.argv[2:] if a != nom and a in {p[0] for p in PLANS_TRENDS}]:
            continue
        depart = essai(f"image {nom}", lambda: image(prompt_image, f"{nom}_depart"))
        if not depart:
            continue
        essai(f"vidéo {nom}", lambda: copier(Client(SPACES["i2v"]).predict(
            input_image=handle_file(str(depart)), last_image=None, prompt=mouvement, steps=6, negative_prompt=NEGATIF,
            duration_seconds=duree, guidance_scale=1, guidance_scale_2=1, seed=42, randomize_seed=False, quality=10,
            scheduler="UniPCMultistep", flow_shift=3.0, frame_multiplier=16, safe_mode=False, video_component=True,
            api_name="/generate_video"), nom))


# Chat Dracula v2 (22/10) : rendu « vidéo de téléphone » dans un vrai couloir d'appartement, plutôt
# qu'un château de cinéma ; un seul plan continu prolongé depuis sa dernière image (même modèle partout).
DRACULA_IMAGE = (
    "Smartphone photo, vertical, taken at floor level in a real apartment hallway at night, warm ceiling lights, "
    "wooden floor, a real ginger tabby cat wearing a small black Dracula cape with a red lining and a stand-up "
    "collar, standing on four paws at the far end of the hallway looking at the camera, natural colors, sharp focus, "
    "photorealistic, no text")
DRACULA_PLANS = [
    ("dracula_a", "Handheld phone footage at floor level: the cat in the Dracula cape walks slowly and confidently "
     "straight toward the camera along the hallway, like a model on a runway, the cape gently bouncing, "
     "realistic natural cat walk, smooth motion, sharp details"),
    ("dracula_b", "Handheld phone footage: the cat in the Dracula cape stops right in front of the camera, looks up "
     "into the lens, then opens its mouth wide and hisses, showing its sharp little fangs, ears flattening back, "
     "realistic cat hissing, smooth motion, sharp details"),
]


def derniere_image(video: Path) -> Path:
    sortie = video.with_name(video.stem + "_fin.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", str(video), "-frames:v", "1", str(sortie)],
                   check=True)
    return sortie


# Trend « Goo Goo Muck » (23/10) : la déco d'Halloween qui prend vie, en vidéo de téléphone réaliste.
SQUELETTE_IMAGE = (
    "Smartphone photo, vertical, taken at night from the front path of a real suburban house, a wooden front porch "
    "decorated for Halloween with a life-size plastic skeleton sitting on a rocking chair, three glowing carved "
    "jack-o'-lanterns on the steps, warm porch light, a real ginger tabby cat on the left of the porch floor, "
    "natural colors, sharp focus, photorealistic, no text")
SQUELETTE_PLANS = [
    ("squelette_a", "Handheld phone footage at night, static framing: the ginger cat walks slowly along the porch floor "
     "and sits down calmly right in front of the seated skeleton; behind it, the skeleton's skull slowly turns "
     "sideways and tilts down to look at the cat, the rest of the skeleton stays perfectly still, realistic, "
     "smooth motion, sharp details"),
    ("squelette_b", "Handheld phone footage at night, static framing: the sitting ginger cat slowly turns its head and "
     "looks up at the skeleton, then freezes, fur puffing up and ears flattening back, staying in place, while the "
     "skeleton's skull stays tilted down staring at the cat, realistic cat reaction, smooth motion, sharp details"),
]


# Variante « ça bouge » (demandée le 23/10) : le squelette se lève et danse comme Mercredi, le chat le regarde.
DANSE_PLANS = [
    ("danse_a", "Handheld phone footage at night, static framing: the plastic skeleton suddenly stands up from the "
     "rocking chair and starts dancing on the porch, jerky robotic arm moves and head tilts like a creepy gothic "
     "dance, while the ginger cat sitting on the path watches it, realistic, smooth motion, sharp details"),
    ("danse_b", "Handheld phone footage at night, static framing: the skeleton keeps dancing energetically on the "
     "porch, swinging its arms and kicking its legs to the beat, the ginger cat jumps back in surprise, realistic, "
     "smooth motion, sharp details"),
]


def danse() -> None:
    histoire(SQUELETTE_IMAGE, DANSE_PLANS, "danse")


def squelette() -> None:
    histoire(SQUELETTE_IMAGE, SQUELETTE_PLANS, "squelette")


def dracula() -> None:
    histoire(DRACULA_IMAGE, DRACULA_PLANS, "dracula")


def histoire(texte_image: str, plans: list[tuple[str, str]], nom_image: str) -> None:
    """Image de départ FLUX puis plans image→vidéo enchaînés, chacun partant de la dernière image du précédent."""
    OUT.mkdir(parents=True, exist_ok=True)
    depart = essai(f"image {nom_image}", lambda: image(texte_image, f"{nom_image}_depart"))
    for nom, mouvement in plans:
        if not depart:
            return
        essai(f"vidéo {nom}", lambda: copier(Client(SPACES["i2v"]).predict(
            input_image=handle_file(str(depart)), last_image=None, prompt=mouvement, steps=8, negative_prompt=NEGATIF,
            duration_seconds=5, guidance_scale=1, guidance_scale_2=1, seed=42, randomize_seed=False, quality=10,
            scheduler="UniPCMultistep", flow_shift=3.0, frame_multiplier=16, safe_mode=False, video_component=True,
            api_name="/generate_video"), nom))
        video = OUT / f"{nom}.mp4"
        depart = derniere_image(video) if video.exists() else None


if __name__ == "__main__":
    {"api": api, "generer": generer, "cles": cles, "trends": trends, "dracula": dracula, "squelette": squelette, "danse": danse}[sys.argv[1]]()
