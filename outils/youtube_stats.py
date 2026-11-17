"""Statistiques publiques de la chaîne YouTube AI Story (YouTube Data API v3, clé gratuite, sans carte).

Lit toutes les vidéos de la chaîne (vues, j'aime, commentaires, durée, date) et écrit :
- stats/historique.csv : une ligne par vidéo et par jour (pour suivre la progression) ;
- stats/classement.md  : classement des vidéos, vues par jour depuis la mise en ligne, gain sur 24 h.

Coût : ~3 unités de quota par jour (quota gratuit : 10 000 / jour).
Variables : YOUTUBE_API_KEY (secret GitHub), YOUTUBE_CHAINE (@pseudo ou identifiant UC…).
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://www.googleapis.com/youtube/v3/"


def _get(ressource: str, **params) -> dict:
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    with urllib.request.urlopen(API + ressource + "?" + urllib.parse.urlencode(params), timeout=30) as r:
        return json.load(r)


def chaine(ref: str) -> dict:
    ref = ref.strip().rstrip("/").split("/")[-1]
    params = {"id": ref} if ref.startswith("UC") else {"forHandle": ref if ref.startswith("@") else "@" + ref}
    items = _get("channels", part="snippet,contentDetails,statistics", **params).get("items")
    if not items:
        sys.exit(f"Chaîne introuvable : {ref}")
    return items[0]


def videos(uploads: str) -> list[dict]:
    ids, page = [], None
    while True:
        r = _get("playlistItems", part="contentDetails", playlistId=uploads, maxResults=50,
                 **({"pageToken": page} if page else {}))
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        page = r.get("nextPageToken")
        if not page:
            break
    out = []
    for k in range(0, len(ids), 50):
        out += _get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50]))["items"]
    return out


def _secondes(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def main(dossier: str = "stats") -> None:
    d = Path(dossier)
    d.mkdir(exist_ok=True)
    c = chaine(os.environ["YOUTUBE_CHAINE"])
    vids = videos(c["contentDetails"]["relatedPlaylists"]["uploads"])
    aujourd_hui = dt.date.today().isoformat()
    hist = d / "historique.csv"
    anciennes = list(csv.DictReader(hist.open())) if hist.exists() else []
    veille = {}
    for row in anciennes:
        if row["date"] < aujourd_hui:
            veille[row["id"]] = int(row["vues"])  # la dernière ligne avant aujourd'hui l'emporte
    lignes = [r for r in anciennes if r["date"] != aujourd_hui]
    maintenant = dt.datetime.now(dt.timezone.utc)
    tableau = []
    for v in vids:
        s, sn = v["statistics"], v["snippet"]
        pub = dt.datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
        jours = max((maintenant - pub).total_seconds() / 86400, 0.04)
        vues = int(s.get("viewCount", 0))
        row = {"date": aujourd_hui, "id": v["id"], "titre": sn["title"], "publiee": sn["publishedAt"][:10],
               "duree_s": _secondes(v["contentDetails"]["duration"]), "vues": vues,
               "jaime": int(s.get("likeCount", 0)), "commentaires": int(s.get("commentCount", 0))}
        lignes.append(row)
        tableau.append((row, vues / jours, vues - veille.get(v["id"], vues)))
    with hist.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()) if lignes else ["date"])
        w.writeheader()
        w.writerows(lignes)
    tableau.sort(key=lambda t: t[0]["vues"], reverse=True)
    st = c["statistics"]
    md = [f"# Stats YouTube : {c['snippet']['title']} ({aujourd_hui})", "",
          f"Abonnés : {st.get('subscriberCount', '?')} · Vues totales : {st.get('viewCount', '?')} · "
          f"Vidéos : {st.get('videoCount', '?')}", "",
          "| # | Vidéo | Publiée | Vues | Vues/jour | +24 h | J'aime | Comm. | Taux j'aime |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i, (r, vj, gain) in enumerate(tableau, 1):
        taux = f"{100 * r['jaime'] / r['vues']:.1f} %" if r["vues"] else "-"
        md.append(f"| {i} | [{r['titre']}](https://youtu.be/{r['id']}) | {r['publiee']} | {r['vues']} | "
                  f"{vj:.0f} | +{gain} | {r['jaime']} | {r['commentaires']} | {taux} |")
    (d / "classement.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main(*sys.argv[1:])
