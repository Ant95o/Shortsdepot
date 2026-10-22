"""Script exécuté sur Kaggle (GPU gratuit) : génère les plans vidéo avec Wan 2.1 (1.3B).

Deux modes, choisis plan par plan :
- texte seul : Wan 2.1 T2V, accéléré par le LoRA CausVid (6 étapes au lieu de 30 à 50) ;
- avec vidéo de référence : Wan 2.1 VACE. La carte de profondeur de la référence
  (Depth Anything V2) guide les mouvements et le cadrage, le prompt décide de qui
  joue (des chats à la place des joueurs, par exemple).

Les plans sont insérés dans ce script par shorts.kaggle avant l'envoi, les
références y sont jointes en base64 (Kaggle n'envoie que ce fichier).
"""

import base64
import gc
import json
import os
import subprocess
import sys
from pathlib import Path

subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35", "transformers", "accelerate",
     "peft", "ftfy", "imageio", "imageio-ffmpeg"],
    check=True,
)

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import imageio.v3 as iio  # noqa: E402
import torch  # noqa: E402
from diffusers import AutoencoderKLWan, UniPCMultistepScheduler, WanPipeline, WanVACEPipeline  # noqa: E402
from diffusers.utils import export_to_video  # noqa: E402
from huggingface_hub import hf_hub_download  # noqa: E402
from PIL import Image  # noqa: E402

T2V = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
TI2V = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"  # Wan 2.2 5B, plus net ; plans avec « modele: wan22-5b »
VACE = "Wan-AI/Wan2.1-VACE-1.3B-diffusers"
DEPTH = "depth-anything/Depth-Anything-V2-Small-hf"
LORA = ("Kijai/WanVideo_comfy", "Wan21_CausVid_bidirect2_T2V_1_3B_lora_rank32.safetensors")
NEGATIVE = ("logos, text, watermark, extra legs, deformed paws, blurry, low quality, static, "
            "human players, human faces")
WIDTH, HEIGHT, FRAMES = 480, 832, 81  # 5 s à 16 i/s, la cadence native de Wan
OUT = Path("/kaggle/working")

# Remplacé par shorts.kaggle au moment de l'envoi.
SHOTS = json.loads(r"""__SHOTS__""")

# Le T4 (Turing) ne gère pas le bfloat16 nativement : float16 dans ce cas.
major, _ = torch.cuda.get_device_capability()
dtype = torch.bfloat16 if major >= 8 else torch.float16
print(f"GPU : {torch.cuda.get_device_name()} ; précision : {dtype}", flush=True)


def load(cls, model: str, flow_shift: float):
    vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
    pipe = cls.from_pretrained(model, vae=vae, torch_dtype=dtype)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=flow_shift)
    try:
        if model == TI2V:
            raise ValueError("pas de LoRA CausVid pour Wan 2.2")
        pipe.load_lora_weights(hf_hub_download(*LORA), adapter_name="causvid")
        pipe.set_adapters(["causvid"], [0.95 if cls is WanPipeline else 0.7])
        pipe.fuse_lora()
        fast = True
    except Exception as exc:  # LoRA incompatible : génération classique, plus lente
        print(f"LoRA CausVid non chargé ({exc}), génération sans accélération", flush=True)
        fast = False
    pipe.enable_model_cpu_offload()
    try:
        pipe.vae.enable_tiling()  # l'encodage de la vidéo de contrôle tient alors sur le T4
    except Exception:
        pass
    return pipe, fast


def depth_frames(shot: dict) -> list[Image.Image]:
    """Décode la référence jointe et la transforme en carte de profondeur image par image."""
    from transformers import pipeline as hf_pipeline

    ref = OUT / f"ref_{shot['out']}"
    ref.write_bytes(base64.b64decode(shot["ref"]))
    frames = [Image.fromarray(f).convert("RGB").resize((WIDTH, HEIGHT)) for f in iio.imread(ref)][:FRAMES]
    frames += [frames[-1]] * (FRAMES - len(frames))
    estimator = hf_pipeline("depth-estimation", model=DEPTH, device=0)
    depth = [estimator(f)["depth"].convert("RGB").resize((WIDTH, HEIGHT)) for f in frames]
    del estimator
    torch.cuda.empty_cache()
    export_to_video([d for d in depth], str(OUT / f"profondeur_{shot['out']}"), fps=16)
    return depth


current = None  # (classe, pipeline, rapide) : un seul modèle en mémoire à la fois
def first_frame(shot: dict) -> tuple[list[Image.Image], list[Image.Image]]:
    """Prolonge un plan : la première image est imposée, Wan invente les 80 suivantes."""
    if "suite" in shot:  # dernière image du plan précédent, généré plus haut dans ce script
        start = Image.fromarray(iio.imread(OUT / shot["suite"])[-1]).convert("RGB").resize((WIDTH, HEIGHT))
    else:
        path = OUT / f"depart_{shot['out']}.jpg"
        path.write_bytes(base64.b64decode(shot["depart"]))
        start = Image.open(path).convert("RGB").resize((WIDTH, HEIGHT))
    grey = Image.new("RGB", (WIDTH, HEIGHT), (127, 127, 127))
    video = [start] + [grey] * (FRAMES - 1)
    mask = [Image.new("L", (WIDTH, HEIGHT), 0)] + [Image.new("L", (WIDTH, HEIGHT), 255)] * (FRAMES - 1)
    return video, mask


VACE_KEYS = ("ref", "depart", "suite")
# Tri stable : l'ordre des prolongements (plan puis sa suite) est conservé.
for shot in sorted(SHOTS, key=lambda s: any(k in s for k in VACE_KEYS)):
    wan22 = shot.get("modele") == "wan22-5b"
    cls = WanVACEPipeline if any(k in shot for k in VACE_KEYS) else WanPipeline
    model = TI2V if wan22 else VACE if cls is WanVACEPipeline else T2V
    if current is None or current[:2] != (cls, model):
        current = None
        gc.collect()
        torch.cuda.empty_cache()
        current = (cls, model, *load(cls, model, 5.0 if wan22 else 3.0 if cls is WanVACEPipeline else 8.0))
    _, _, pipe, fast = current
    print(f"Génération de {shot['out']}{' (avec référence)' if 'ref' in shot else ''}…", flush=True)
    # Le texte est encodé à part puis l'encodeur (11 Go) est renvoyé en RAM : sinon il reste
    # sur le GPU pendant l'encodage de la vidéo de contrôle et le T4 (15 Go) déborde.
    with torch.no_grad():
        embeds, negative = pipe.encode_prompt(shot["prompt"], NEGATIVE, do_classifier_free_guidance=not fast,
                                              max_sequence_length=512, device="cuda", dtype=dtype)
    pipe.text_encoder.to("cpu")
    gc.collect()
    torch.cuda.empty_cache()
    args = dict(
        prompt_embeds=embeds, negative_prompt_embeds=negative, height=HEIGHT, width=WIDTH, num_frames=FRAMES,
        num_inference_steps=6 if fast else 25, guidance_scale=1.0 if fast else 5.0,
        generator=torch.Generator("cuda").manual_seed(int(shot.get("seed", 42))),
    )
    if wan22:  # 5 s à 24 i/s, la cadence native de Wan 2.2 ; dimensions multiples de 32
        args.update(height=960, width=544, num_frames=121, num_inference_steps=30)
    if "ref" in shot:
        args["video"] = depth_frames(shot)
        args["conditioning_scale"] = float(shot.get("force", 0.8))
        if fast:
            args["num_inference_steps"] = 8
    elif "depart" in shot or "suite" in shot:
        args["video"], args["mask"] = first_frame(shot)
        if fast:
            args["num_inference_steps"] = 8
    if wan22:
        # Le décodage VAE de 121 images fait déborder les 30 Go de RAM tant que le transformeur
        # et l'encodeur de texte sont chargés : on sort les latents, on les libère, puis on décode.
        args["output_type"] = "latent"
        latents = pipe(**args).frames
        vae, processor = pipe.vae, pipe.video_processor
        current = pipe = None
        gc.collect()
        torch.cuda.empty_cache()
        with torch.no_grad():
            latents = latents.to("cuda", vae.dtype)
            z = vae.config.z_dim
            mean = torch.tensor(vae.config.latents_mean).view(1, z, 1, 1, 1).to(latents)
            std = torch.tensor(vae.config.latents_std).view(1, z, 1, 1, 1).to(latents)
            try:
                vae.to("cuda")
            except Exception:  # le crochet d'offload s'en charge alors au décodage
                pass
            video = vae.decode(latents * std + mean, return_dict=False)[0]
        frames = processor.postprocess_video(video.cpu(), output_type="np")[0]
        del vae, latents, video
    else:
        frames = pipe(**args).frames[0]
    export_to_video(frames, str(OUT / shot["out"]), fps=24 if wan22 else 16)
    print(f"{shot['out']} prêt", flush=True)
    # Libère la RAM entre deux plans : sans ça, le 2e plan Wan 2.2 5B dépasse les 30 Go de Kaggle.
    del frames, args, embeds, negative
    gc.collect()
    torch.cuda.empty_cache()
