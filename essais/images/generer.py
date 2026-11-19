"""Génère les images d'une fiche (liste de prompts) sans compte : Pollinations (FLUX), puis HF FLUX schnell en secours.

Usage : python essais/images/generer.py essais/images/gateau.yaml
Sorties : essais/sortie/images/<fiche>/<n>.jpg
"""
import os, sys, time, urllib.parse, urllib.request
from pathlib import Path
import yaml

fiche = Path(sys.argv[1])
data = yaml.safe_load(fiche.read_text(encoding="utf-8"))
style = data.get("style", "")
out = Path("essais/sortie/images") / fiche.stem
out.mkdir(parents=True, exist_ok=True)
seuls = {int(x) for x in os.environ.get("SEULS", "").split(",") if x.strip()}


def pollinations(prompt, seed, modele):
    q = urllib.parse.quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{q}?width=768&height=1344&seed={seed}"
           f"&model={modele}&nologo=true&private=true&enhance=false")
    req = urllib.request.Request(url, headers={"User-Agent": "shortsdepot"})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read()
        if not r.headers.get("Content-Type", "").startswith("image/") or len(body) < 20000:
            raise RuntimeError(f"réponse inattendue {r.headers.get('Content-Type')} {len(body)} o")
        return body


def hf_flux(prompt, seed):
    from gradio_client import Client
    c = Client("black-forest-labs/FLUX.1-schnell", hf_token=os.environ.get("HF_TOKEN") or None)
    res = c.predict(prompt=prompt, seed=seed, randomize_seed=False, width=768, height=1344,
                    num_inference_steps=4, api_name="/infer")
    return Path(res[0]).read_bytes()


ok = 0
for i, p in enumerate(data["images"], 1):
    if seuls and i not in seuls:
        continue
    prompt = f"{p['prompt']} {style}".strip()
    seed = int(p.get("graine", data.get("graine", 42)))
    img = None
    for essai in range(3):
        try:
            img = pollinations(prompt, seed, data.get("modele", "flux"))
            src = "pollinations"
            break
        except Exception as exc:
            print(f"image {i} : Pollinations essai {essai + 1} raté ({exc})", flush=True)
            time.sleep(10 * (essai + 1))
    if img is None:
        try:
            img, src = hf_flux(prompt, seed), "hf-flux"
        except Exception as exc:
            print(f"image {i} : FLUX Hugging Face raté aussi ({exc})", flush=True)
            continue
    (out / f"{i}.jpg").write_bytes(img)
    ok += 1
    print(f"image {i} prête ({src}, {len(img) // 1000} ko)", flush=True)
    time.sleep(3)
print(f"{ok} image(s) générée(s)")
sys.exit(0 if ok else 1)
