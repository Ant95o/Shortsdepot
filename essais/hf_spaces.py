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


if __name__ == "__main__":
    {"api": api, "generer": generer, "cles": cles}[sys.argv[1]]()
