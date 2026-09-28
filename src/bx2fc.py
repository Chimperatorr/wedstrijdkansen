"""Zet BetExplorer-lijsten (bx/<code>_res.txt en _fix.txt) om naar fcupdate-formaat fc/<code>.txt. Tijden +1 uur (BetExplorer toont UK-tijd)."""
import sys, re, os
H = os.path.dirname(os.path.abspath(__file__))
for code in sys.argv[1:]:
    out = []
    for kind in ("res", "fix"):
        p = f"{H}/bx/{code}_{kind}.txt"
        if not os.path.exists(p): continue
        seen = set()
        for line in open(p, encoding="utf-8"):
            q = [x.strip() for x in line.split("|")]
            if len(q) < 3: continue
            m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})(?:\s+(\d{2}):(\d{2}))?", q[0])
            if not m: continue
            d = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            if kind == "res" and len(q) >= 4 and re.match(r"^\d+-\d+$", q[3]):
                if (q[1], q[2]) in seen: continue
                seen.add((q[1], q[2])); out.append(f"{d} | {q[1]} | {q[3]} | {q[2]}")
            elif kind == "fix":
                t = f"{(int(m.group(4)) + 1) % 24:02d}:{m.group(5)}" if m.group(4) else ""
                out.append(f"{d} | {q[1]} | {t} | {q[2]}")
    open(f"{H}/fc/{code}.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(code, len(out))
