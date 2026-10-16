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
import subprocess
import sys
from pathlib import Path

subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35", "transformers", "accelerate",
     "peft", "ftfy", "imageio", "imageio-ffmpeg"],
    check=True,
)

import imageio.v3 as iio  # noqa: E402
import torch  # noqa: E402
from diffusers import AutoencoderKLWan, UniPCMultistepScheduler, WanPipeline, WanVACEPipeline  # noqa: E402
from diffusers.utils import export_to_video  # noqa: E402
from huggingface_hub import hf_hub_download  # noqa: E402
from PIL import Image  # noqa: E402

T2V = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
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
        pipe.load_lora_weights(hf_hub_download(*LORA), adapter_name="causvid")
        pipe.set_adapters(["causvid"], [0.95 if cls is WanPipeline else 0.7])
        pipe.fuse_lora()
        fast = True
    except Exception as exc:  # LoRA incompatible : génération classique, plus lente
        print(f"LoRA CausVid non chargé ({exc}), génération en 25 étapes", flush=True)
        fast = False
    pipe.enable_model_cpu_offload()
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
for shot in sorted(SHOTS, key=lambda s: "ref" in s):
    cls = WanVACEPipeline if "ref" in shot else WanPipeline
    if current is None or current[0] is not cls:
        current = None
        gc.collect()
        torch.cuda.empty_cache()
        current = (cls, *load(cls, VACE if cls is WanVACEPipeline else T2V, 3.0 if cls is WanVACEPipeline else 8.0))
    _, pipe, fast = current
    print(f"Génération de {shot['out']}{' (avec référence)' if 'ref' in shot else ''}…", flush=True)
    args = dict(
        prompt=shot["prompt"], negative_prompt=NEGATIVE, height=HEIGHT, width=WIDTH, num_frames=FRAMES,
        num_inference_steps=6 if fast else 25, guidance_scale=1.0 if fast else 5.0,
        generator=torch.Generator("cuda").manual_seed(int(shot.get("seed", 42))),
    )
    if "ref" in shot:
        args["video"] = depth_frames(shot)
        args["conditioning_scale"] = float(shot.get("force", 0.8))
        if fast:
            args["num_inference_steps"] = 8
    frames = pipe(**args).frames[0]
    export_to_video(frames, str(OUT / shot["out"]), fps=16)
    print(f"{shot['out']} prêt", flush=True)
