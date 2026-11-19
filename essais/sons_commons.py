"""Cherche des sons ou vidéos libres (domaine public / CC) sur Wikimedia Commons et les télécharge.

  python essais/sons_commons.py   → essais/sons/*.(ogg|mp3|wav|flac) + essais/sons/liste.json
"""

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
OUT = Path("essais/sons")
UA = {"User-Agent": "Shortsdepot/1.0 (https://github.com/Ant95o/Shortsdepot)"}
LIBRES = ("public domain", "cc0", "pd", "cc by", "cc-by")
RECHERCHES = {
    "musique_ukulele": "ukulele happy",
    "musique_joyeuse": "cheerful music",
    "musique_comique": "comedy music light",
}
TYPE = "audio"  # « audio » pour les sons


def api(**params) -> dict:
    url = API + "?" + urllib.parse.urlencode({"format": "json", **params})
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def chercher(cle: str, texte: str, n: int = 6) -> list[dict]:
    res = api(action="query", generator="search", gsrsearch=f"{texte} filetype:{TYPE}", gsrnamespace=6,
              gsrlimit=40, prop="imageinfo", iiprop="url|size|mime|extmetadata")
    trouves = []
    for page in (res.get("query", {}).get("pages", {}) or {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licence = meta.get("LicenseShortName", {}).get("value", "")
        if not any(l in licence.lower() for l in LIBRES) or "nc" in licence.lower().split():
            continue
        if info.get("size", 0) > 60_000_000:
            continue
        auteur = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:120]
        trouves.append({"cle": cle, "titre": page["title"], "url": info["url"], "licence": licence,
                        "auteur": auteur, "duree": meta.get("Length", {}).get("value", "")})
    return trouves[:n]


OUT.mkdir(parents=True, exist_ok=True)
liste = []
for cle, texte in RECHERCHES.items():
    for i, s in enumerate(chercher(cle, texte)):
        ext = Path(urllib.parse.urlparse(s["url"]).path).suffix.lower()
        nom = f"{cle}{i}{ext}"
        try:
            with urllib.request.urlopen(urllib.request.Request(s["url"], headers=UA), timeout=120) as r:
                (OUT / nom).write_bytes(r.read())
        except Exception as exc:
            print(f"{nom} : échec ({exc})")
            continue
        s["fichier"] = nom
        liste.append(s)
        print(f"{nom} ← {s['titre']} [{s['licence']}]")
(OUT / "liste.json").write_text(json.dumps(liste, ensure_ascii=False, indent=2), encoding="utf-8")
