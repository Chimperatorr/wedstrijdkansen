"""Bouwt index.html uit src/*.part en data/*.json. Gebruik: python3 src/build_page.py"""
import json, glob, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
main = open(f"{R}/data/main.json", encoding="utf-8").read()
L = {os.path.basename(p)[:-5]: json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(f"{R}/data/*.json")) if not p.endswith("main.json")}
body = open(f"{R}/src/style.part", encoding="utf-8").read() + open(f"{R}/src/markup.part", encoding="utf-8").read() + "\n" + open(f"{R}/src/chat.part", encoding="utf-8").read()
body = body.replace("__DATA__", main, 1).replace("__LEAGUES__", json.dumps(L, ensure_ascii=False, separators=(",", ":")), 1)
html = '<!doctype html>\n<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' + body.replace("</style>", "</style></head><body>", 1) + "\n</body></html>\n"
open(f"{R}/index.html", "w", encoding="utf-8").write(html)
print(len(html.encode()) // 1024, "KB")
