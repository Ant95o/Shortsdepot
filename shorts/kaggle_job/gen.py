"""Script exécuté sur Kaggle (GPU gratuit) : génère les plans vidéo avec Wan 2.1 (1.3B).

Le LoRA CausVid permet de générer en quelques étapes au lieu de 30 à 50, ce qui
ramène un plan de 5 s à quelques minutes sur un T4. Les plans à générer sont
insérés dans ce script par shorts.kaggle avant l'envoi.
"""

import json
import subprocess
import sys
from pathlib import Path

subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.33", "transformers", "accelerate",
     "peft", "ftfy", "imageio", "imageio-ffmpeg"],
    check=True,
)

import torch  # noqa: E402
from diffusers import AutoencoderKLWan, UniPCMultistepScheduler, WanPipeline  # noqa: E402
from diffusers.utils import export_to_video  # noqa: E402
from huggingface_hub import hf_hub_download  # noqa: E402

MODEL = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
LORA = ("Kijai/WanVideo_comfy", "Wan21_CausVid_bidirect2_T2V_1_3B_lora_rank32.safetensors")
NEGATIVE = "logos, text, watermark, extra legs, deformed paws, blurry, low quality, static, human players"
OUT = Path("/kaggle/working")

# Remplacé par shorts.kaggle au moment de l'envoi (Kaggle n'envoie que ce fichier).
SHOTS = json.loads(r"""__SHOTS__""")

# Le T4 (Turing) ne gère pas le bfloat16 nativement : float16 dans ce cas.
major, _ = torch.cuda.get_device_capability()
dtype = torch.bfloat16 if major >= 8 else torch.float16
print(f"GPU : {torch.cuda.get_device_name()} ; précision : {dtype}", flush=True)

vae = AutoencoderKLWan.from_pretrained(MODEL, subfolder="vae", torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(MODEL, vae=vae, torch_dtype=dtype)
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=8.0)
pipe.load_lora_weights(hf_hub_download(*LORA), adapter_name="causvid")
pipe.set_adapters(["causvid"], [0.95])
pipe.fuse_lora()
pipe.enable_model_cpu_offload()

for shot in SHOTS:
    print(f"Génération de {shot['out']}…", flush=True)
    frames = pipe(
        prompt=shot["prompt"],
        negative_prompt=NEGATIVE,
        height=832,
        width=480,
        num_frames=81,  # 5 s à 16 i/s, la cadence native de Wan
        num_inference_steps=6,
        guidance_scale=1.0,
        generator=torch.Generator("cuda").manual_seed(int(shot.get("seed", 42))),
    ).frames[0]
    export_to_video(frames, str(OUT / shot["out"]), fps=16)
    print(f"{shot['out']} prêt", flush=True)
