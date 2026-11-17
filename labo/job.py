"""Script exécuté sur Kaggle (GPU T4 gratuit) : essais de repos open source sur nos plans.

Tâches (lues dans taches.json, joint au jeu de données Kaggle « shortsdepot-labo-entrees ») :
- fluidite : RIFE v4.26 (lib ccvfi) crée les images intermédiaires pour passer à `fps`
  (16 → 30 i/s pour un plan HF), puis Real-ESRGAN (x2 ou x4) agrandit en 1080x1920 ;
- transition : LTX-Video (Lightricks, 2B) anime le passage d'une image de départ à une
  image d'arrivée (images clés), pour les raccords entre deux plans.

Chaque tâche est indépendante : un échec est noté dans le journal et n'arrête pas les autres.
"""

import gc
import json
import math
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ccvfi", "spandrel", "av", "imageio", "imageio-ffmpeg",
                "diffusers>=0.35", "transformers", "accelerate", "sentencepiece", "ftfy"], check=True)
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import imageio.v3 as iio  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from huggingface_hub import hf_hub_download  # noqa: E402
from PIL import Image  # noqa: E402

OUT = Path("/kaggle/working")
ENTREES = next(Path("/kaggle/input").rglob("taches.json")).parent
TACHES = json.loads((ENTREES / "taches.json").read_text(encoding="utf-8"))
major, _ = torch.cuda.get_device_capability()
DTYPE = torch.bfloat16 if major >= 8 else torch.float16  # le T4 (Turing) n'a pas de bfloat16 natif
print(f"GPU : {torch.cuda.get_device_name()} ; entrées : {ENTREES}", flush=True)


def lire(nom: str) -> tuple[list[np.ndarray], float]:
    path = ENTREES / nom
    fps = float(iio.immeta(path, plugin="pyav").get("fps", 16) or 16)
    frames = [f for f in iio.imiter(path, plugin="pyav")]
    return frames, fps


def ecrire(frames: list[np.ndarray], fps: float, nom: str) -> None:
    import imageio_ffmpeg
    h, w = frames[0].shape[:2]
    proc = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-",
                             "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
                             "-movflags", "+faststart", str(OUT / nom)], stdin=subprocess.PIPE)
    for f in frames:
        proc.stdin.write(np.ascontiguousarray(f, dtype=np.uint8).tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError(f"ffmpeg a échoué pour {nom}")
    print(f"{nom} : {len(frames)} images {w}x{h} à {fps:g} i/s", flush=True)


def interpoler(frames: list[np.ndarray], fps_in: float, fps_out: float) -> list[np.ndarray]:
    """RIFE : pour chaque instant de sortie, image intermédiaire entre les deux images source voisines."""
    from ccvfi import AutoModel, ConfigType

    model = AutoModel.from_pretrained(pretrained_model_name=ConfigType.RIFE_IFNet_v426_heavy, fp16=True)
    duree = (len(frames) - 1) / fps_in
    n = int(math.floor(duree * fps_out + 1e-6)) + 1
    tens = [torch.from_numpy(f).permute(2, 0, 1)[None].half().cuda() / 255 for f in frames]
    out = []
    with torch.inference_mode():
        for k in range(n):
            pos = k * fps_in / fps_out
            i = min(int(pos), len(frames) - 2)
            t = pos - i
            if t < 1e-3:
                out.append(frames[i])
                continue
            if t > 1 - 1e-3:
                out.append(frames[i + 1])
                continue
            y = model.inference(torch.stack([tens[i], tens[i + 1]], dim=1), timestep=t, scale=1.0)
            out.append((y[0].float().clamp(0, 1).permute(1, 2, 0).cpu().numpy() * 255).round().astype(np.uint8))
    del model, tens
    torch.cuda.empty_cache()
    return out


def agrandir(frames: list[np.ndarray], facteur: int) -> list[np.ndarray]:
    """Real-ESRGAN (poids ai-forever, via spandrel) image par image."""
    from spandrel import ModelLoader

    model = ModelLoader().load_from_file(hf_hub_download("ai-forever/Real-ESRGAN", f"RealESRGAN_x{facteur}.pth"))
    model = model.model.half().cuda().eval()
    out = []
    with torch.no_grad():
        for f in frames:
            x = torch.from_numpy(np.ascontiguousarray(f)).permute(2, 0, 1)[None].half().cuda() / 255
            y = model(x).clamp(0, 1)[0].permute(1, 2, 0).float().cpu().numpy()
            out.append((y * 255).round().astype(np.uint8))
    del model
    torch.cuda.empty_cache()
    return out


def cadrer(frames: list[np.ndarray], w: int = 1080, h: int = 1920) -> list[np.ndarray]:
    """Remplit le 9:16 (recadrage centré) avec un redimensionnement Lanczos."""
    out = []
    for f in frames:
        im = Image.fromarray(f)
        s = max(w / im.width, h / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        x, y = (im.width - w) // 2, (im.height - h) // 2
        out.append(np.asarray(im.crop((x, y, x + w, y + h))))
    return out


def fluidite(t: dict) -> None:
    frames, fps = lire(t["entree"])
    if t.get("reduire"):  # repart d'une résolution plus basse (ex. plan Kaggle déjà agrandi x2)
        w, h = t["reduire"]
        frames = [np.asarray(Image.fromarray(f).resize((w, h), Image.LANCZOS)) for f in frames]
    print(f"{t['entree']} : {len(frames)} images {frames[0].shape[1]}x{frames[0].shape[0]} à {fps:g} i/s", flush=True)
    debut = time.time()
    fps_out = float(t.get("fps", 30))
    if fps_out != fps:
        frames = interpoler(frames, fps, fps_out)
        print(f"RIFE : {len(frames)} images en {time.time() - debut:.0f} s", flush=True)
    if t.get("agrandir"):
        debut = time.time()
        frames = agrandir(frames, int(t["agrandir"]))
        print(f"Real-ESRGAN x{t['agrandir']} en {time.time() - debut:.0f} s", flush=True)
    ecrire(cadrer(frames), fps_out, f"{t['sortie']}.mp4")


def transition(t: dict) -> None:
    from diffusers import LTXConditionPipeline
    from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition

    w, h, n = int(t.get("largeur", 512)), int(t.get("hauteur", 896)), int(t.get("images", 97))
    debut = Image.open(ENTREES / t["debut"]).convert("RGB")
    fin = Image.open(ENTREES / t["fin"]).convert("RGB")
    debut, fin = [Image.fromarray(cadrer([np.asarray(i)], w, h)[0]) for i in (debut, fin)]
    pipe = LTXConditionPipeline.from_pretrained(t.get("modele", "Lightricks/LTX-Video-0.9.5"), torch_dtype=DTYPE)
    pipe.vae.to(torch.float32)  # VAE en float32 : en float16 il risque de saturer (images noires)
    decode = pipe.vae.decode
    pipe.vae.decode = lambda z, temb=None, **k: decode(  # le pipeline lui passe des latents en float16
        z.float(), temb.float() if torch.is_tensor(temb) else temb, **k)
    # T5 (9,5 Go) et transformeur ne tiennent pas ensemble sur le T4 : on encode le texte d'abord,
    # puis on jette l'encodeur avant de monter le transformeur et le VAE sur le GPU.
    neg = "worst quality, blurry, jittery, distorted, deformed paws, extra legs, morphing, text, watermark"
    pipe.text_encoder.to("cuda")
    with torch.no_grad():
        pe, pm, ne, nm = pipe.encode_prompt(t["prompt"], neg, do_classifier_free_guidance=True,
                                            max_sequence_length=256, device="cuda", dtype=DTYPE)
    pipe.text_encoder = None
    gc.collect()
    torch.cuda.empty_cache()
    pipe.transformer.to("cuda")
    pipe.vae.to("cuda")
    pipe.vae.enable_tiling()
    conditions = [LTXVideoCondition(image=debut, frame_index=0), LTXVideoCondition(image=fin, frame_index=n - 1)]
    chrono = time.time()
    frames = pipe(
        conditions=conditions, prompt_embeds=pe, prompt_attention_mask=pm,
        negative_prompt_embeds=ne, negative_prompt_attention_mask=nm,
        width=w, height=h, num_frames=n, frame_rate=24, num_inference_steps=int(t.get("etapes", 40)), guidance_scale=3.0,
        decode_timestep=0.05, decode_noise_scale=0.025,
        generator=torch.Generator("cuda").manual_seed(int(t.get("graine", 42))), output_type="np",
    ).frames[0]
    print(f"LTX-Video : {len(frames)} images en {time.time() - chrono:.0f} s", flush=True)
    del pipe
    gc.collect()
    torch.cuda.empty_cache()
    frames = [(np.clip(f, 0, 1) * 255).round().astype(np.uint8) for f in frames]
    ecrire(frames, 24, f"{t['sortie']}-brut.mp4")
    if t.get("agrandir"):
        ecrire(cadrer(agrandir(frames, int(t["agrandir"]))), 24, f"{t['sortie']}.mp4")


def _hf(repo: str, motif: str, dossier: Path) -> str:
    """Télécharge le premier fichier du dépôt HF dont le chemin contient tous les mots de `motif`."""
    from huggingface_hub import list_repo_files

    mots = motif.lower().split()
    nom = next(f for f in sorted(list_repo_files(repo)) if all(m in f.lower() for m in mots))
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = hf_hub_download(repo, nom, local_dir="/tmp/hf")
    cible = dossier / Path(nom).name
    if not cible.exists():
        cible.symlink_to(chemin)
    print(f"{repo} : {nom}", flush=True)
    return cible.name


def comfyui(t: dict) -> None:
    """ComfyUI sans interface : Wan 2.2 14B image→vidéo (GGUF Q4, LoRA lightx2v 4 étapes), le même modèle
    que le Space HF mais sans quota, puis RIFE + Real-ESRGAN dans la foulée si `fluidite` est demandé."""
    import urllib.request

    racine = Path("/tmp/ComfyUI")
    if not racine.exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", "https://github.com/comfyanonymous/ComfyUI", str(racine)], check=True)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "https://github.com/city96/ComfyUI-GGUF",
                        str(racine / "custom_nodes" / "ComfyUI-GGUF")], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(racine / "requirements.txt"),
                        "gguf", "av"], check=True)
    m = racine / "models"
    quant = t.get("quant", "Q4_K_S")
    haut = _hf("QuantStack/Wan2.2-I2V-A14B-GGUF", f"high {quant}.gguf", m / "unet")
    bas = _hf("QuantStack/Wan2.2-I2V-A14B-GGUF", f"low {quant}.gguf", m / "unet")
    rep = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged"
    clip = _hf(rep, "text_encoders umt5 fp8", m / "text_encoders")
    vae = _hf(rep, "vae wan_2.1_vae", m / "vae")
    lora_h = _hf(rep, "loras i2v lightx2v 4steps high", m / "loras")
    lora_b = _hf(rep, "loras i2v lightx2v 4steps low", m / "loras")
    (racine / "input").mkdir(exist_ok=True)
    img = "depart-" + Path(t["debut"]).name
    w, h = int(t.get("largeur", 480)), int(t.get("hauteur", 832))
    Image.fromarray(cadrer([np.asarray(Image.open(ENTREES / t["debut"]).convert("RGB"))], w, h)[0]).save(racine / "input" / img)

    serveur = subprocess.Popen([sys.executable, "main.py", "--listen", "127.0.0.1", "--port", "8188",
                                "--lowvram", "--disable-auto-launch"], cwd=racine)
    for _ in range(120):
        try:
            urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2)
            break
        except Exception:
            time.sleep(2)
    etapes, graine = int(t.get("etapes", 4)), int(t.get("graine", 42))
    neg = ("blurry, morphing, crossfade, distorted, deformed paws, extra legs, extra hands, human hands, "
           "text, watermark, static, frozen, low quality")
    g = {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": haut}},
        "2": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": bas}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": lora_h, "strength_model": 1.0}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": lora_b, "strength_model": 1.0}},
        "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 5.0}},
        "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 5.0}},
        "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip, "type": "wan", "device": "cpu"}},
        "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": t["prompt"]}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": neg}},
        "10": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "11": {"class_type": "LoadImage", "inputs": {"image": img}},
        "12": {"class_type": "WanImageToVideo", "inputs": {
            "positive": ["8", 0], "negative": ["9", 0], "vae": ["10", 0], "start_image": ["11", 0],
            "width": w, "height": h, "length": int(t.get("images", 81)), "batch_size": 1}},
        "13": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["5", 0], "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["12", 2],
            "add_noise": "enable", "noise_seed": graine, "steps": etapes, "cfg": 1.0, "sampler_name": "euler",
            "scheduler": "simple", "start_at_step": 0, "end_at_step": etapes // 2, "return_with_leftover_noise": "enable"}},
        "14": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["6", 0], "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["13", 0],
            "add_noise": "disable", "noise_seed": graine, "steps": etapes, "cfg": 1.0, "sampler_name": "euler",
            "scheduler": "simple", "start_at_step": etapes // 2, "end_at_step": 10000, "return_with_leftover_noise": "disable"}},
        "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["10", 0]}},
        "16": {"class_type": "SaveImage", "inputs": {"images": ["15", 0], "filename_prefix": t["sortie"]}},
    }
    chrono = time.time()
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=json.dumps({"prompt": g}).encode(),
                                 headers={"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
    while True:
        time.sleep(10)
        hist = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}").read())
        if pid in hist and hist[pid].get("status", {}).get("completed") is not None:
            break
        if serveur.poll() is not None:
            raise RuntimeError("ComfyUI s'est arrêté")
    statut = hist[pid]["status"]
    if statut.get("status_str") != "success":
        raise RuntimeError(f"ComfyUI : {json.dumps(statut.get('messages', []))[-1500:]}")
    images = sorted((racine / "output").glob(f"{t['sortie']}_*.png"))
    print(f"ComfyUI Wan 2.2 14B : {len(images)} images en {time.time() - chrono:.0f} s", flush=True)
    serveur.terminate()
    serveur.wait(timeout=60)
    torch.cuda.empty_cache()
    frames = [np.asarray(Image.open(p).convert("RGB")) for p in images]
    ecrire(frames, 16, f"{t['sortie']}-brut.mp4")
    if t.get("fluidite"):
        frames = interpoler(frames, 16, 30)
        frames = agrandir(frames, int(t.get("agrandir", 4)))
        ecrire(cadrer(frames), 30, f"{t['sortie']}.mp4")


bilan = {}
for tache in TACHES:
    print(f"=== {tache['type']} → {tache['sortie']}", flush=True)
    try:
        {"fluidite": fluidite, "transition": transition, "comfyui": comfyui}[tache["type"]](tache)
        bilan[tache["sortie"]] = "ok"
    except Exception as exc:
        traceback.print_exc()
        bilan[tache["sortie"]] = f"échec : {exc}"
    gc.collect()
    torch.cuda.empty_cache()
(OUT / "bilan.json").write_text(json.dumps(bilan, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(bilan, ensure_ascii=False, indent=2), flush=True)
