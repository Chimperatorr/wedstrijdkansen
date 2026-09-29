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
_ap.add_argument("--nl-main", default=None, help="pad naar model/current-JSON: zet b365/nl.txt (Nations League, bet365.com) in odds.bet365 en stop")
ARGS = _ap.parse_args()
OPENLIGA = ARGS.openliga

META = {
  "en1": {"name": "Premier League", "country": "Engeland", "of": "en.1", "tz": 1, "up": None, "down": "en.2"},
  "en2": {"name": "Championship", "country": "Engeland", "of": "en.2", "tz": 1, "up": "en.1", "down": None},
  "it1": {"name": "Serie A", "country": "Italië", "of": "it.1", "tz": 0, "up": None, "down": "it.2"},
  "es1": {"name": "La Liga", "country": "Spanje", "of": "es.1", "tz": 0, "up": None, "down": "es.2"},
  "de1": {"name": "Bundesliga", "country": "Duitsland", "of": "de.1", "tz": 0, "up": None, "down": "de.2"},
  "de2": {"name": "2. Bundesliga", "country": "Duitsland", "openliga": True, "prevof": "de.2", "tz": 0, "up": "de.1", "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt"},
  "fr2": {"name": "Ligue 2", "country": "Frankrijk", "fc": "fr2", "prevof": "fr.2", "tz": 0, "up": "fr.1", "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "es2": {"name": "LaLiga 2", "country": "Spanje", "fc": "es2", "prevof": "es.2", "tz": 0, "up": "es.1", "down": None, "osrc": "sportytrader.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "it2": {"name": "Serie B", "country": "Italië", "fc": "it2", "prevof": "it.2", "tz": 0, "up": "it.1", "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "dk1": {"name": "Superliga", "country": "Denemarken", "fc": "dk1", "tz": 0, "up": None, "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "se1": {"name": "Allsvenskan", "country": "Zweden", "fc": "se1", "tz": 0, "up": None, "down": None, "osrc": "sportytrader.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com", "season": "2026"},
  "pl1": {"name": "Ekstraklasa", "country": "Polen", "fc": "pl1", "tz": 0, "up": None, "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "no1": {"name": "Eliteserien", "country": "Noorwegen", "fc": "no1", "tz": 0, "up": None, "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com", "season": "2026"},
  "at1": {"name": "Bundesliga", "country": "Oostenrijk", "fc": "at1", "tz": 0, "up": None, "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "tr1": {"name": "Süper Lig", "country": "Turkije", "fc": "tr1", "tz": 0, "up": None, "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "ch1": {"name": "Super League", "country": "Zwitserland", "fc": "ch1", "tz": 0, "up": None, "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt", "src": "betexplorer.com"},
  "fr1": {"name": "Ligue 1", "country": "Frankrijk", "of": "fr.1", "tz": 0, "up": None, "down": "fr.2"},
  "pt1": {"name": "Liga Portugal", "country": "Portugal", "of": "pt.1", "tz": 1, "up": None, "down": None, "osrc": "sportytrader.com (hoogste prijs)", "olabel": "markt"},
  "nl2": {"name": "Keuken Kampioen Divisie", "country": "Nederland", "fc": "nl.2", "tz": 0, "up": "ere", "down": None, "osrc": "oddschecker.com (hoogste prijs)", "olabel": "markt"},
  "be1": {"name": "Pro League", "country": "België", "fc": "be.1", "prevof": "be.1", "tz": 0, "up": None, "down": None, "osrc": "sportytrader.com (hoogste prijs)", "olabel": "markt"},
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
  "AJ Auxerre": "Auxerre", "Paris FC": "Paris FC",
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
  # Ligue 2 / LaLiga 2 / Serie B (openfootball vorig seizoen + BetExplorer)
  "AS Nancy Lorraine": "Nancy", "AS Saint-Étienne": "Saint-Étienne", "St Etienne": "Saint-Étienne", "Clermont Foot 63": "Clermont",
  "EA Guingamp": "Guingamp", "Grenoble Foot 38": "Grenoble", "Montpellier HSC": "Montpellier", "Rodez AF": "Rodez", "Stade Lavallois": "Laval",
  "Stade de Reims": "Reims", "US Boulogne": "Boulogne", "USL Dunkerque": "Dunkerque", "ESTAC Troyes": "Troyes", "Amiens SC": "Amiens", "SC Bastia": "Bastia",
  "UD Almería": "Almería", "Almeria": "Almería", "SD Eibar": "Eibar", "CD Castellón": "Castellón", "Castellon": "Castellón", "AD Ceuta": "Ceuta",
  "Gijon": "Sporting Gijón", "Burgos CF": "Burgos", "Cordoba": "Córdoba", "Leganes": "Leganés", "Cadiz CF": "Cádiz", "Valladolid": "Real Valladolid",
  "Oviedo": "Real Oviedo", "Granada CF": "Granada", "SD Huesca": "Huesca", "CD Mirandés": "Mirandés", "Real Zaragoza": "Zaragoza",
  "Calcio Padova": "Padova", "Carrarese Calcio": "Carrarese", "Mantova 1911 SSD": "Mantova", "US Avellino": "Avellino", "US Catanzaro": "Catanzaro",
  "Verona": "Hellas Verona", "Sudtirol": "Südtirol", "Entella": "Virtus Entella", "L.R. Vicenza": "Vicenza", "AC Reggiana 1919": "Reggiana",
  "Delfino Pescara": "Pescara", "SSC Bari": "Bari", "Spezia Calcio": "Spezia",
  # Denemarken / Zweden (BetExplorer-namen)
  "FC Copenhagen": "FC København", "Brondby": "Brøndby", "Midtjylland": "FC Midtjylland", "Nordsjaelland": "FC Nordsjælland",
  "Aarhus": "AGF", "Odense": "OB", "Horsens": "AC Horsens", "Sonderjyske": "SønderjyskE",
  "Goteborg": "Göteborg", "Hacken": "Häcken", "Malmo FF": "Malmö FF", "Djurgarden": "Djurgården", "Mjallby": "Mjällby",
  "Vasteras SK": "Västerås SK", "Orgryte": "Örgryte",
  # Polen / Oostenrijk / Noorwegen / Turkije / Zwitserland (BetExplorer-namen)
  "Legia": "Legia Warszawa", "Wisla": "Wisła Kraków", "Wisla Plock": "Wisła Płock", "Widzew Lodz": "Widzew Łódź", "Lech Poznan": "Lech Poznań",
  "Gornik Zabrze": "Górnik Zabrze", "Slask Wroclaw": "Śląsk Wrocław", "Pogon Szczecin": "Pogoń Szczecin", "Rakow": "Raków Częstochowa",
  "Zaglebie": "Zagłębie Lubin", "Wieczysta Krakow": "Wieczysta Kraków", "Jagiellonia": "Jagiellonia Białystok",
  "A. Lustenau": "Austria Lustenau", "Austria Vienna": "Austria Wien", "SK Rapid": "Rapid Wien", "Salzburg": "RB Salzburg", "Tirol": "WSG Tirol", "Ried": "SV Ried",
  "Bodo/Glimt": "Bodø/Glimt", "Valerenga": "Vålerenga", "Tromso": "Tromsø", "Lillestrom": "Lillestrøm",
  "Besiktas": "Beşiktaş", "Fenerbahce": "Fenerbahçe", "Basaksehir": "Başakşehir", "Kasimpasa": "Kasımpaşa", "Goztepe": "Göztepe",
  "Genclerbirligi": "Gençlerbirliği", "Eyupspor": "Eyüpspor", "Corum": "Çorum FK", "Rizespor": "Çaykur Rizespor", "Gaziantep": "Gaziantep FK",
  "Zurich": "FC Zürich",
  "Termalica B-B.": "Bruk-Bet Termalica", "Lechia Gdansk": "Lechia Gdańsk", "Karagumruk": "Fatih Karagümrük", "Stromsgodset": "Strømsgodset",
  "Norrkoping": "Norrköping", "Varnamo": "Värnamo", "Oster": "Öster",
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

def prevbx_load(code):
    """Vorig seizoen uit prevbx/<code>.txt (BetExplorer: 'DD.MM.[YYYY] | thuis | uit | h-a'; zonder jaar = 2026)."""
    p = f"{HERE}/prevbx/{code}.txt"
    if not os.path.exists(p): return None
    out, seen = [], set()
    for line in open(p, encoding="utf-8"):
        q = [x.strip() for x in line.split("|")]
        if len(q) != 4: continue
        m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})?", q[0]); sc = re.match(r"^(\d+)[-:](\d+)$", q[3])
        if not m or not sc: continue
        h, a = nm(q[1]), nm(q[2])
        if (h, a) in seen: continue
        seen.add((h, a))
        out.append([f"{m.group(3) or '2026'}-{m.group(2)}-{m.group(1)}", h, a, int(sc.group(1)), int(sc.group(2))])
    return sorted(out) or None

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
    s = s.replace("ı", "i").replace("ł", "l").replace("Ł", "L").replace("æ", "ae").replace("Æ", "Ae").replace("ø", "o").replace("Ø", "O")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("man utd", "manchester united").replace("man city", "manchester city").replace("nottm", "nottingham")
    s = s.replace("inter milan", "inter").replace("m'gladbach", "monchengladbach").replace("borussia monchengladbach", "monchengladbach")
    s = s.replace("sheff utd", "sheffield united").replace("sheff wed", "sheffield wednesday").replace("wolverhampton", "wolves")
    s = s.replace("maastricht", "mvv").replace("venlo", "vvv").replace("bruges", "brugge").replace("st. truidense", "sint truiden").replace("st truidense", "sint truiden")
    s = s.replace("standard liege", "standard luik").replace("union saint-gilloise", "union sg").replace("oud-heverlee leuven", "oh leuven").replace("royal antwerp", "antwerp")
    s = s.replace("sporting lisbon", "sporting cp").replace("benfica lisbon", "benfica").replace("vitoria sc guimaraes", "vitoria guimaraes").replace("hertha bsc berlin", "hertha")
    s = s.replace("fc copenhagen", "fc kobenhavn").replace("copenhagen", "kobenhavn").replace("agf aarhus", "agf").replace("vasteraas", "vasteras").replace("malmo ff", "malmo").replace("sonderjyske", "sonderjyske")
    s = s.replace("alto adige", "sudtirol").replace("nancy-lorraine", "nancy").replace("red star 93", "red star").replace("real sociedad san sebastian b", "real sociedad b").replace("clermont foot", "clermont")
    s = s.replace("vienna", "wien").replace("lask linz", "lask").replace("wsg swarovski tirol", "wsg tirol").replace("kristiansund bk", "kristiansund").replace("sk brann", "brann").replace("sk sturm", "sturm")
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

def price(x):
    """Decimale (1.85) of Engelse fractionele (11/10, EVS) notatie naar decimaal."""
    x = x.strip().upper()
    if x in ("EVS", "EVENS"): return 2.0
    try:
        if "/" in x:
            a, b = x.split("/"); v = 1 + float(a) / float(b)
        else: v = float(x.replace(",", "."))
    except (ValueError, ZeroDivisionError): return None
    return round(v, 3) if v > 1 else None

def pdate(s):
    """'YYYY-MM-DD ...' of 'DD/MM/YY ...' (bet365.com) naar YYYY-MM-DD."""
    s = s.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m: return m.group(0)
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})", s)
    if m:
        y = int(m.group(3)); y = y + 2000 if y < 100 else y
        return f"{y:04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return None

def b365_load(code, fixtures):
    path = f"{HERE}/b365/{code}.txt"
    out = {}
    if not os.path.exists(path): return out
    for line in open(path, encoding="utf-8"):
        p = [x.strip() for x in line.split("|")]
        if len(p) != 6: continue
        o = [price(x) for x in p[3:6]]
        if None in o: continue
        d = pdate(p[0])
        if not d: continue
        dd = datetime.date.fromisoformat(d)
        near = {(dd + datetime.timedelta(days=k)).isoformat() for k in (-3, -2, -1, 0, 1, 2, 3)}
        best, bs = None, 0
        for f in fixtures:
            if f[0] not in near: continue
            s = sim(p[1], f[1]) + sim(p[2], f[2])
            if s > bs: best, bs = f, s
        if best and bs >= 1.4:
            if abs((datetime.date.fromisoformat(best[0]) - dd).days) > 1:
                best[0] = d; best[3] = ""   # bron had een voorlopige datum: neem de datum van de bookmaker over
            out[f"{best[0]}|{best[1]}|{best[2]}"] = o
        else:
            print("  geen match voor bet365:", line.strip(), file=sys.stderr)
    return out

EN = {"Spain":"Spanje","England":"Engeland","France":"Frankrijk","Portugal":"Portugal","Belgium":"België","Netherlands":"Nederland","Holland":"Nederland",
 "Switzerland":"Zwitserland","Norway":"Noorwegen","Croatia":"Kroatië","Germany":"Duitsland","Denmark":"Denemarken","Austria":"Oostenrijk","Turkey":"Turkije","Turkiye":"Turkije",
 "Italy":"Italië","Ukraine":"Oekraïne","Greece":"Griekenland","Scotland":"Schotland","Sweden":"Zweden","Rep of Ireland":"Ierland","Republic of Ireland":"Ierland","Ireland":"Ierland",
 "Kosovo":"Kosovo","Poland":"Polen","Serbia":"Servië","Hungary":"Hongarije","Slovenia":"Slovenië","Wales":"Wales","Czechia":"Tsjechië","Czech Republic":"Tsjechië",
 "Northern Ireland":"Noord-Ierland","Romania":"Roemenië","Georgia":"Georgië","Bosnia-Herzegovina":"Bosnië en Herzegovina","Bosnia and Herzegovina":"Bosnië en Herzegovina","Bosnia":"Bosnië en Herzegovina",
 "Israel":"Israël","North Macedonia":"Noord-Macedonië","Slovakia":"Slowakije","Albania":"Albanië","Iceland":"IJsland","Finland":"Finland","Belarus":"Wit-Rusland",
 "Luxembourg":"Luxemburg","Montenegro":"Montenegro","Bulgaria":"Bulgarije","Kazakhstan":"Kazachstan","Armenia":"Armenië","Faroe Islands":"Faeröer","Estonia":"Estland",
 "Azerbaijan":"Azerbeidzjan","Cyprus":"Cyprus","Lithuania":"Litouwen","Latvia":"Letland","Malta":"Malta","Moldova":"Moldavië","Andorra":"Andorra","Gibraltar":"Gibraltar",
 "Liechtenstein":"Liechtenstein","San Marino":"San Marino"}

def nl_odds(path):
    D = json.load(open(path, encoding="utf-8"))
    fx = D["nl"]["fixtures"]
    odds = D.setdefault("odds", {}).setdefault("bet365", {})
    n = miss = 0
    src = f"{HERE}/b365/nl.txt"
    if not os.path.exists(src): print("geen b365/nl.txt"); return
    for line in open(src, encoding="utf-8"):
        p = [x.strip() for x in line.split("|")]
        if len(p) != 6: continue
        d = pdate(p[0]); o = [price(x) for x in p[3:6]]
        h, a = EN.get(p[1]), EN.get(p[2])
        if not d or None in o or not h or not a: print("  overgeslagen (naam/prijs onbekend):", line.strip(), file=sys.stderr); miss += 1; continue
        dd = datetime.date.fromisoformat(d); near = {(dd + datetime.timedelta(days=k)).isoformat() for k in (-1, 0, 1)}
        f = next((f for f in fx if f[0] in near and f[1] == h and f[2] == a), None)
        if not f: print("  geen fixture:", d, h, a, file=sys.stderr); miss += 1; continue
        odds[f"{f[0]}|{f[1]}|{f[2]}"] = o; n += 1
    today = datetime.date.today().isoformat()
    D["odds"]["bet365"] = {k: v for k, v in odds.items() if k[:10] >= today}
    json.dump(D, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("Nations League-quoteringen:", n, "gezet,", miss, "overgeslagen")

def main():
    if ARGS.nl_main:
        nl_odds(ARGS.nl_main); return
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
            if not prevm and prevbx_load(code):   # nieuw toegevoegd vorig seizoen
                prevm = prevbx_load(code)
                old = dict(old, prev=prev_table(prevm))
            prev = {t: v for t, v in (old.get("prev") or {}).items() if t in teams}
            rel = [t for t in (old.get("rel") or []) if t in teams]
            unknown = [t for t in teams if t not in old.get("teams", [])]
            if unknown: print(f"  LET OP {code}: onbekende teamnamen {unknown} (naam-mapping in NAMES aanvullen)", file=sys.stderr)
        else:
            prevm = of_prev(prevcode) if prevcode else prevbx_load(code)
            prev = {t: v for t, v in prev_table(prevm).items() if t in teams} if prevm else {}
            up = prev_sets.get(M["up"], set()) if M.get("up") else set()
            rel = [t for t in teams if t not in prev and t in up]
        missing = [t for t in teams if t not in prev and t not in rel]
        fx = [f for f in fx if f[0] >= TODAY]
        fx.sort(key=lambda f: (f[0], f[3]))
        odds = b365_load(code, fx)
        fx.sort(key=lambda f: (f[0], f[3]))
        if not odds and old is not None:   # geen nieuwe quoteringen: oude houden voor nog te spelen duels
            keep = {f"{f[0]}|{f[1]}|{f[2]}" for f in fx}
            odds = {k: v for k, v in (old.get("odds", {}).get("bet365") or {}).items() if k in keep}
        doc = {
            "code": code, "name": M["name"], "country": M["country"], "updated": TODAY,
            "season": M.get("season", "2026/27"), "teams": teams, "prev": prev, "rel": rel, "noPrev": not prevm and not prev,
            "matches": sorted(played), "prevMatches": sorted(prevm or []), "fixtures": fx,
            "absences": [], "noAbs": True,
            "odds": {"bet365": odds, "updated": TODAY if odds else None, "source": M.get("osrc", "bet365"), "label": M.get("olabel", "bet365")},
            "source": (M["src"] if M.get("src") else "openfootball (github.com/openfootball)" if M.get("of") else
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
