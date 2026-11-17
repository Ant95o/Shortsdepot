"""Veille trends avec Firecrawl (palier gratuit sans clé, ou clé gratuite FIRECRAWL_API_KEY).

Lance une série de recherches web et actualités de la semaine (TikTok, Reels, Shorts, sons viraux),
puis croise les résultats : un son ou un format n'est retenu comme « candidat » que s'il est cité par
au moins 2 sites différents (règle d'AntoineS : ≥ 2 sources indépendantes).

Sorties : veille/AAAA-MM-JJ.md (candidats croisés + toutes les sources) et veille/AAAA-MM-JJ.json.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

REQUETES = [
    ("trending TikTok sounds this week", "web", "US"),
    ("TikTok trends this week", "news", "US"),
    ("trending Instagram Reels audio this week", "web", "US"),
    ("viral TikTok trend cat dog video", "news", "US"),
    ("YouTube Shorts trends this week", "web", "US"),
    ("tendance TikTok de la semaine", "web", "FR"),
    ("trend TikTok virale son", "news", "FR"),
    ("AI animal video viral TikTok", "news", "US"),
]

# Noms de chansons / sons entre guillemets ou après « song », « sound », « audio »
MOTIF = re.compile(r"[\"“«]([^\"”»]{3,40})[\"”»]|(?:song|sound|audio|trend|son)\s*[:\-–]\s*([A-Z][\w' ]{2,35})")


def chercher(q: str, source: str, pays: str) -> list[dict]:
    cmd = ["firecrawl", "search", q, "--limit", "8", "--tbs", "qdr:w", "--sources", source,
           "--country", pays, "--json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode:
        print(f"Échec « {q} » : {r.stderr.strip()[:200]}")
        return []
    data = json.loads(r.stdout or "{}")
    data = data.get("data", data)
    items = []
    for cle in ("web", "news"):
        for it in (data.get(cle) or []) if isinstance(data, dict) else []:
            texte = " ".join(str(it.get(k) or "") for k in ("title", "description", "snippet"))
            for h in it.get("highlights") or []:
                texte += " " + (h if isinstance(h, str) else h.get("text", ""))
            items.append({"requete": q, "url": it.get("url", ""), "titre": it.get("title", ""), "texte": texte,
                          "date": it.get("date", "")})
    return items


def main(dossier: str = "veille") -> None:
    jour = dt.date.today().isoformat()
    out = Path(dossier)
    out.mkdir(exist_ok=True)
    tous = [it for q, s, p in REQUETES for it in chercher(q, s, p)]
    cites = collections.defaultdict(set)
    for it in tous:
        dom = urllib.parse.urlparse(it["url"]).netloc.removeprefix("www.")
        for m in MOTIF.finditer(it["texte"]):
            nom = (m.group(1) or m.group(2) or "").strip(" .,!?").lower()
            if 3 <= len(nom) <= 40 and len(nom.split()) <= 6:
                cites[nom].add(dom)
    candidats = sorted(((n, d) for n, d in cites.items() if len(d) >= 2), key=lambda x: -len(x[1]))
    md = [f"# Veille trends du {jour} (Firecrawl, résultats de moins de 7 jours)", "",
          "## Candidats cités par au moins 2 sites différents", ""]
    md += [f"- **{n}** : {len(d)} sites ({', '.join(sorted(d))})" for n, d in candidats[:25]] or ["- aucun"]
    md += ["", "À vérifier ensuite sur TikTok et Instagram (nombre de vidéos, vidéos d'exemple) avant de proposer.",
           "", "## Toutes les sources", ""]
    vus = set()
    for it in tous:
        if it["url"] in vus:
            continue
        vus.add(it["url"])
        md.append(f"- [{it['titre'] or it['url']}]({it['url']}) {it['date']} — « {it['requete']} »")
    (out / f"{jour}.md").write_text("\n".join(md) + "\n")
    (out / f"{jour}.json").write_text(json.dumps(tous, ensure_ascii=False, indent=1))
    print("\n".join(md[:40]))


if __name__ == "__main__":
    main(*sys.argv[1:])
