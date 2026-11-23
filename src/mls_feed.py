"""MLS (code mls): bouwt fc/mls.txt (seizoen YYYY + programma) en prevbx/mls.txt (vorig seizoen) uit fixturedownload.com.
Gebruik (in de werkmap W): python3 mls_feed.py [jaar]   (default: huidig kalenderjaar)
Play-offs staan niet in de feed: zet ze (uit BetExplorer https://www.betexplorer.com/football/usa/mls/results/ en /fixtures/)
in fc/mls_playoffs.txt, formaat "YYYY-MM-DD | thuis | h-a of HH:MM | uit" (Nederlandse tijd, in wintertijd gelijk aan BetExplorer)."""
import json, sys, os, urllib.request, datetime
from zoneinfo import ZoneInfo
Y = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today().year
NAME = {"St. Louis CITY SC": "St. Louis City", "Atlanta": "Atlanta United", "Austin": "Austin FC", "CF Montréal": "CF Montréal", "Montréal": "CF Montréal",
  "Chicago Fire FC": "Chicago Fire", "Chicago": "Chicago Fire", "Charlotte": "Charlotte FC", "Cincinnati": "FC Cincinnati", "Colorado": "Colorado Rapids",
  "Columbus": "Columbus Crew", "D.C.": "D.C. United", "Dallas": "FC Dallas", "Houston Dynamo FC": "Houston Dynamo", "Houston": "Houston Dynamo",
  "Inter Miami CF": "Inter Miami", "Miami": "Inter Miami", "LA": "LA Galaxy", "Los Angeles Football Club": "Los Angeles FC", "LAFC": "Los Angeles FC",
  "Minnesota United FC": "Minnesota United", "Minnesota": "Minnesota United", "Nashville": "Nashville SC", "New England": "New England Revolution",
  "New York City Football Club": "New York City FC", "New York City": "New York City FC", "Orlando": "Orlando City", "Philadelphia": "Philadelphia Union",
  "Portland": "Portland Timbers", "Salt Lake": "Real Salt Lake", "Red Bull New York": "New York Red Bulls", "New York": "New York Red Bulls",
  "San Diego": "San Diego FC", "San Jose": "San Jose Earthquakes", "Seattle Sounders FC": "Seattle Sounders", "Seattle": "Seattle Sounders",
  "Kansas City": "Sporting Kansas City", "St. Louis": "St. Louis City", "Toronto": "Toronto FC", "Vancouver Whitecaps FC": "Vancouver Whitecaps", "Vancouver": "Vancouver Whitecaps"}
n = lambda t: NAME.get(t, t)
def feed(y):
    return json.load(urllib.request.urlopen(urllib.request.Request(f"https://fixturedownload.com/feed/json/mls-{y}", headers={"User-Agent": "Mozilla/5.0"}), timeout=30))
def loc(s): return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).astimezone(ZoneInfo("Europe/Amsterdam"))
os.makedirs("fc", exist_ok=True); os.makedirs("prevbx", exist_ok=True)
lines = []
for m in sorted(feed(Y), key=lambda m: m["DateUtc"]):
    t = loc(m["DateUtc"]); mid = f"{m['HomeTeamScore']}-{m['AwayTeamScore']}" if m["HomeTeamScore"] is not None else t.strftime("%H:%M")
    lines.append(f"{t:%Y-%m-%d} | {n(m['HomeTeam'])} | {mid} | {n(m['AwayTeam'])}")
if os.path.exists("fc/mls_playoffs.txt"): lines += [l.strip() for l in open("fc/mls_playoffs.txt", encoding="utf-8") if l.strip()]
open("fc/mls.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
pl = [f"{loc(m['DateUtc']):%d.%m.%Y} | {n(m['HomeTeam'])} | {n(m['AwayTeam'])} | {m['HomeTeamScore']}-{m['AwayTeamScore']}" for m in feed(Y - 1) if m["HomeTeamScore"] is not None]
open("prevbx/mls.txt", "w", encoding="utf-8").write("\n".join(pl) + "\n")
print(f"mls: {len(lines)} regels fc, {len(pl)} vorig seizoen")
