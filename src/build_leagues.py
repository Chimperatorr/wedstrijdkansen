"""Bouwt per competitie een data-document (leagues.json) uit openfootball, openliga en fcupdate.
Gebruik: python3 build_leagues.py [pad-naar-openliga-2026-27_de.2.txt]
"""
import json, re, sys, difflib, unicodedata, datetime, os, glob

TODAY = datetime.date.today().isoformat()
HERE = os.path.dirname(os.path.abspath(__file__))
import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("openliga", nargs="?", help="pad naar openliga 2026-27_de.2.txt")
_ap.add_argument("--update", help="map met bestaande league-docs (<code>.json); historie wordt daaruit overgenomen")
_ap.add_argument("--out", default=None, help="map om per competitie <code>.json te schrijven")
ARGS = _ap.parse_args()
OPENLIGA = ARGS.openliga

META = {
  "en1": {"name": "Premier League", "country": "Engeland", "of": "en.1", "tz": 1, "up": None, "down": "en.2"},
  "en2": {"name": "Championship", "country": "Engeland", "of": "en.2", "tz": 1, "up": "en.1", "down": None},
  "it1": {"name": "Serie A", "country": "Italië", "of": "it.1", "tz": 0, "up": None, "down": "it.2"},
  "es1": {"name": "La Liga", "country": "Spanje", "of": "es.1", "tz": 0, "up": None, "down": "es.2"},
  "de1": {"name": "Bundesliga", "country": "Duitsland", "of": "de.1", "tz": 0, "up": None, "down": "de.2"},
  "de2": {"name": "2. Bundesliga", "country": "Duitsland", "openliga": True, "prevof": "de.2", "tz": 0, "up": "de.1", "down": None},
  "fr1": {"name": "Ligue 1", "country": "Frankrijk", "of": "fr.1", "tz": 0, "up": None, "down": "fr.2"},
  "pt1": {"name": "Liga Portugal", "country": "Portugal", "of": "pt.1", "tz": 1, "up": None, "down": None},
  "nl2": {"name": "Keuken Kampioen Divisie", "country": "Nederland", "fc": "nl.2", "tz": 0, "up": "ere", "down": None},
  "be1": {"name": "Pro League", "country": "België", "fc": "be.1", "prevof": "be.1", "tz": 0, "up": None, "down": None},
}

NAMES = {
  # Engeland
  "AFC Bournemouth": "Bournemouth", "Brighton & Hove Albion FC": "Brighton", "Tottenham Hotspur FC": "Tottenham",
  "Wolverhampton Wanderers FC": "Wolves", "Newcastle United FC": "Newcastle", "West Ham United FC": "West Ham",
  "Queens Park Rangers FC": "QPR", "West Bromwich Albion FC": "West Brom", "Preston North End FC": "Preston",
  "Hull City AFC": "Hull City", "Leeds United FC": "Leeds United", "Ipswich Town FC": "Ipswich Town",
  # Duitsland
  "FC Bayern München": "Bayern München", "Bayer 04 Leverkusen": "Bayer Leverkusen", "1. FSV Mainz 05": "Mainz 05",
  "1. FC Union Berlin": "Union Berlin", "SV Werder Bremen": "Werder Bremen", "TSG 1899 Hoffenheim": "Hoffenheim",
  "Borussia Mönchengladbach": "Mönchengladbach", "SC Paderborn 07": "Paderborn", "SV 07 Elversberg": "Elversberg",
  "1. FC Heidenheim 1846": "Heidenheim", "DSC Arminia Bielefeld": "Arminia Bielefeld", "SpVgg Greuther Fürth": "Greuther Fürth",
  "SV Darmstadt 98": "Darmstadt 98", "VfL Wolfsburg": "Wolfsburg", "VfL Bochum": "Bochum", "VfL Osnabrück": "Osnabrück", "FC St. Pauli 1910": "St. Pauli", "FC St. Pauli": "St. Pauli",
  "1. FC Köln": "1. FC Köln", "1. FC Kaiserslautern": "Kaiserslautern", "1. FC Magdeburg": "Magdeburg", "1. FC Nürnberg": "Nürnberg",
  "Energie Cottbus": "Energie Cottbus", "FC Energie Cottbus": "Energie Cottbus",
  # Spanje
  "Club Atlético de Madrid": "Atlético Madrid", "Rayo Vallecano de Madrid": "Rayo Vallecano", "RCD Espanyol de Barcelona": "Espanyol",
  "Real Betis Balompié": "Real Betis", "Real Madrid CF": "Real Madrid", "Real Racing Club de Santander": "Racing Santander",
  "Real Sociedad de Fútbol": "Real Sociedad", "RC Celta de Vigo": "Celta Vigo", "RC Deportivo La Coruña": "Deportivo La Coruña",
  "CA Osasuna": "Osasuna", "Levante UD": "Levante", "Deportivo Alavés": "Alavés", "Athletic Club": "Athletic Bilbao",
  "Málaga CF": "Málaga", "RCD Mallorca": "Mallorca", "UD Las Palmas": "Las Palmas", "Real Valladolid CF": "Real Valladolid",
  "Real Oviedo": "Real Oviedo", "Girona FC": "Girona", "CD Leganés": "Leganés",
  # Italië
  "ACF Fiorentina": "Fiorentina", "FC Internazionale Milano": "Inter", "Genoa CFC": "Genoa", "Parma Calcio 1913": "Parma",
  "SSC Napoli": "Napoli", "Frosinone Calcio": "Frosinone", "Cagliari Calcio": "Cagliari", "Udinese Calcio": "Udinese",
  "US Sassuolo Calcio": "Sassuolo", "US Lecce": "Lecce", "SS Lazio": "Lazio", "Atalanta BC": "Atalanta",
  "Bologna FC 1909": "Bologna", "Juventus FC": "Juventus", "Torino FC": "Torino", "Venezia FC": "Venezia", "AC Monza": "Monza",
  "Como 1907": "Como", "Hellas Verona FC": "Hellas Verona", "AC Pisa 1909": "Pisa", "US Cremonese": "Cremonese",
  # Frankrijk
  "AS Monaco FC": "Monaco", "Angers SCO": "Angers", "ES Troyes AC": "Troyes", "Le Havre AC": "Le Havre", "Lille OSC": "Lille",
  "OGC Nice": "Nice", "Olympique Lyonnais": "Lyon", "Olympique de Marseille": "Marseille", "Paris Saint-Germain FC": "Paris SG",
  "RC Strasbourg Alsace": "Strasbourg", "Racing Club de Lens": "Lens", "Stade Brestois 29": "Brest", "Stade Rennais FC 1901": "Rennes",
  "AJ Auxerre": "Auxerre",
  # Portugal
  "Sport Lisboa e Benfica": "Benfica", "Sporting Clube de Portugal": "Sporting CP", "Sporting Clube de Braga": "Braga",
  "GD Estoril Praia": "Estoril", "Casa Pia AC": "Casa Pia", "CD Santa Clara": "Santa Clara", "CD Nacional": "Nacional",
  "CF Estrela da Amadora": "Estrela Amadora", "CS Marítimo": "Marítimo", "Académico de Viseu FC": "Académico Viseu",
  "CD Tondela": "Tondela", "AVS Futebol SAD": "AVS", "Vitória SC": "Vitória Guimarães",
  # België (openfootball vorig seizoen -> fcupdate-namen)
  "Club Brugge KV": "Club Brugge", "KAA Gent": "Gent", "KRC Genk": "Genk", "KV Mechelen": "Mechelen", "KVC Westerlo": "Westerlo",
  "Oud-Heverlee Leuven": "OH Leuven", "RAAL La Louviére": "La Louvière", "RSC Anderlecht": "Anderlecht", "Royal Antwerp FC": "Antwerp",
  "SV Zulte Waregem": "Zulte Waregem", "Sint-Truidense VV": "Sint-Truiden", "Sporting Charleroi": "Charleroi",
  "Standard Liège": "Standard Luik", "Union Saint-Gilloise": "Union SG", "FCV Dender EH": "Dender",
  # fcupdate-afkortingen
  "OHL": "OH Leuven", "R. Union SG": "Union SG", "WB": "Beveren", "ZW": "Zulte Waregem", "Standard": "Standard Luik",
  # Eredivisie vorig seizoen (voor degradanten KKD)
  "Heracles Almelo": "Heracles", "NAC Breda": "NAC", "FC Volendam": "Volendam",
}

def nm(s):
    s = s.strip()
    if s in NAMES: return NAMES[s]
    for suf in (" AFC", " FC", " CF"):
        if s.endswith(suf): s = s[: -len(suf)]
    for pre in ("AFC ", "FC "):
        if s.startswith(pre) and len(s) > len(pre) + 3: s = s[len(pre):]
    return NAMES.get(s, s)

def shift(t, h):
    if not t or not h: return t or ""
    H, M = map(int, t.split(":"))
    return f"{(H + h) % 24:02d}:{M:02d}"

def of_load(path, tz):
    d = json.load(open(path))
    played, fx = [], []
    for m in d["matches"]:
        sc = m.get("score") if isinstance(m.get("score"), dict) else None
        h, a = nm(m["team1"]), nm(m["team2"])
        if sc and sc.get("ft"):
            played.append([m["date"], h, a, sc["ft"][0], sc["ft"][1]])
        else:
            fx.append([m["date"], h, a, shift(m.get("time", ""), tz)])
    return played, fx

MON = {m: i for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1)}
def openliga_load(path):
    played, fx = [], []
    date, time, year = None, "", 2026
    rx = re.compile(r"^\s+(?:(\d\d:\d\d)\s+)?(\S.*?)\s+v\s+(\S.*?)(?:\s+(\d+)-(\d+)(?:\s+\(.*\))?)?\s*$")
    for line in open(path, encoding="utf-8"):
        dm = re.match(r"^\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\w{3}) (\d+)(?: (\d{4}))?\s*$", line)
        if dm:
            mo = MON[dm.group(2)]
            year = int(dm.group(4)) if dm.group(4) else (2026 if mo >= 7 else 2027)
            date = f"{year}-{mo:02d}-{int(dm.group(3)):02d}"; time = ""
            continue
        if line.lstrip().startswith("(") or line.startswith("▪") or line.startswith("#") or line.startswith("="):
            continue
        m = rx.match(line)
        if not m or not date: continue
        if m.group(1): time = m.group(1)
        h, a = nm(m.group(2)), nm(m.group(3))
        if m.group(4) is not None:
            played.append([date, h, a, int(m.group(4)), int(m.group(5))])
        else:
            fx.append([date, h, a, time])
    return played, fx

def fc_load(path):
    played, fx = [], []
    for line in open(path, encoding="utf-8"):
        p = [x.strip() for x in line.split("|")]
        if len(p) != 4: continue
        d, h, mid, a = p
        h, a = nm(h), nm(a)
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", mid)
        if m: played.append([d, h, a, int(m.group(1)), int(m.group(2))])
        else: fx.append([d, h, a, "" if mid in ("01:00", "", "-") else mid])
    return played, fx

def prev_table(matches):
    t = {}
    for d, h, a, hg, ag in matches:
        for team, f, g in ((h, hg, ag), (a, ag, hg)):
            r = t.setdefault(team, [0, 0, 0]); r[0] += 1; r[1] += f; r[2] += g
    return t

def of_prev(code):
    p = f"{HERE}/of/prev/{code}.json"
    if not os.path.exists(p): return None
    pl, _ = of_load(p, 0)
    return pl

# ---------- bet365 ----------
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("man utd", "manchester united").replace("man city", "manchester city").replace("nottm", "nottingham")
    s = s.replace("inter milan", "inter").replace("m'gladbach", "monchengladbach").replace("borussia monchengladbach", "monchengladbach")
    s = s.replace("psg", "paris sg").replace("paris saint-germain", "paris sg").replace("a coruna", "la coruna")
    s = re.sub(r"\b(fc|afc|cf|sc|ac|as|club|de|calcio|tsg|vfl|vfb|sv|1\.|the)\b", " ", s)
    return re.sub(r"[^a-z ]", " ", s).split()

def sim(a, b):
    A, B = " ".join(norm(a)), " ".join(norm(b))
    if not A or not B: return 0
    r = difflib.SequenceMatcher(None, A, B).ratio()
    if A in B or B in A: r = max(r, 0.9)
    if set(A.split()) & set(B.split()): r = max(r, 0.75)
    return r

def b365_load(code, fixtures):
    path = f"{HERE}/b365/{code}.txt"
    out = {}
    if not os.path.exists(path): return out
    for line in open(path, encoding="utf-8"):
        p = [x.strip() for x in line.split("|")]
        if len(p) != 6: continue
        try: o = [float(x) for x in p[3:6]]
        except ValueError: continue
        d = p[0][:10]
        dd = datetime.date.fromisoformat(d)
        near = {(dd + datetime.timedelta(days=k)).isoformat() for k in (-1, 0, 1)}
        best, bs = None, 0
        for f in fixtures:
            if f[0] not in near: continue
            s = sim(p[1], f[1]) + sim(p[2], f[2])
            if s > bs: best, bs = f, s
        if best and bs >= 1.4:
            out[f"{best[0]}|{best[1]}|{best[2]}"] = o
        else:
            print("  geen match voor bet365:", line.strip(), file=sys.stderr)
    return out

def main():
    prev_sets = {}
    for c in ("en.1", "en.2", "de.1", "de.2", "es.1", "es.2", "it.1", "it.2", "fr.1", "fr.2", "pt.1", "be.1"):
        pl = of_prev(c)
        if pl: prev_sets[c] = set(prev_table(pl))
    if of_prev("nl.1"): prev_sets["ere"] = set(prev_table(of_prev("nl.1")))
    out = {}
    for code, M in META.items():
        if M.get("of"):
            played, fx = of_load(f"{HERE}/of/{M['of']}.json", M["tz"])
            prevcode = M["of"]
        elif M.get("openliga"):
            played, fx = openliga_load(OPENLIGA)
            prevcode = M.get("prevof")
        else:
            played, fx = fc_load(f"{HERE}/fc/{M['fc']}.txt")
            prevcode = M.get("prevof")
        xp = f"{HERE}/extra/{code}.txt"
        if os.path.exists(xp):
            xpl, _ = fc_load(xp)
            have = {(m[1], m[2]) for m in played}
            for m in xpl:
                if (m[1], m[2]) not in have: played.append(m)
            done = {(m[1], m[2]) for m in played}
            fx = [f for f in fx if (f[1], f[2]) not in done]
        teams = sorted({m[1] for m in played + fx} | {m[2] for m in played + fx})
        old = None
        if ARGS.update and os.path.exists(f"{ARGS.update}/{code}.json"):
            old = json.load(open(f"{ARGS.update}/{code}.json"))
        if old is not None:
            prevm = old.get("prevMatches") or None
            prev = {t: v for t, v in (old.get("prev") or {}).items() if t in teams}
            rel = [t for t in (old.get("rel") or []) if t in teams]
            unknown = [t for t in teams if t not in old.get("teams", [])]
            if unknown: print(f"  LET OP {code}: onbekende teamnamen {unknown} (naam-mapping in NAMES aanvullen)", file=sys.stderr)
        else:
            prevm = of_prev(prevcode) if prevcode else None
            prev = {t: v for t, v in prev_table(prevm).items() if t in teams} if prevm else {}
            up = prev_sets.get(M["up"], set()) if M.get("up") else set()
            rel = [t for t in teams if t not in prev and t in up]
        missing = [t for t in teams if t not in prev and t not in rel]
        fx = [f for f in fx if f[0] >= TODAY]
        fx.sort(key=lambda f: (f[0], f[3]))
        odds = b365_load(code, fx)
        if not odds and old is not None:   # geen nieuwe quoteringen: oude houden voor nog te spelen duels
            keep = {f"{f[0]}|{f[1]}|{f[2]}" for f in fx}
            odds = {k: v for k, v in (old.get("odds", {}).get("bet365") or {}).items() if k in keep}
        doc = {
            "code": code, "name": M["name"], "country": M["country"], "updated": TODAY,
            "season": "2026/27", "teams": teams, "prev": prev, "rel": rel, "noPrev": not prevm,
            "matches": sorted(played), "prevMatches": sorted(prevm or []), "fixtures": fx,
            "absences": [], "noAbs": True,
            "odds": {"bet365": odds, "updated": TODAY if odds else None, "source": "bet365.nl"},
            "source": ("openfootball (github.com/openfootball)" if M.get("of") else
                        "openfootball/openligadb" if M.get("openliga") else "fcupdate.nl"),
        }
        out[code] = doc
        s = len(json.dumps(doc, ensure_ascii=False).encode())
        print(f"{code}: {len(teams)} teams, {len(played)} gespeeld, {len(fx)} te spelen, prev {len(prev)}, rel {rel}, zonder historie {missing if prevm else 'alle'}, odds {len(odds)}, {s//1024} KB")
    json.dump(out, open(f"{HERE}/leagues.json", "w"), ensure_ascii=False, separators=(",", ":"))
    if ARGS.out:
        os.makedirs(ARGS.out, exist_ok=True)
        for k, v in out.items():
            json.dump(v, open(f"{ARGS.out}/{k}.json", "w"), ensure_ascii=False, separators=(",", ":"))

if __name__ == "__main__":
    main()
