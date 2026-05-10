import os, sys, time, threading, socket, json
import requests
from datetime import datetime, timezone

if sys.platform == "win32":
    import msvcrt
    def getpass_star(prompt=""):
        sys.stdout.write(prompt); sys.stdout.flush()
        chars = []
        while True:
            c = msvcrt.getch()
            if c in (b"\r", b"\n"):
                sys.stdout.write("\n"); sys.stdout.flush()
                return "".join(chars)
            elif c == b"\x03":
                raise KeyboardInterrupt
            elif c == b"\x08":
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b"); sys.stdout.flush()
            else:
                chars.append(c.decode(errors="replace"))
                sys.stdout.write("*"); sys.stdout.flush()
else:
    import tty, termios
    def getpass_star(prompt=""):
        sys.stdout.write(prompt); sys.stdout.flush()
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        chars = []
        try:
            tty.setraw(fd)
            while True:
                c = sys.stdin.read(1)
                if c in ("\r", "\n"):
                    sys.stdout.write("\n"); sys.stdout.flush()
                    return "".join(chars)
                elif c == "\x03":
                    raise KeyboardInterrupt
                elif c in ("\x7f", "\x08"):
                    if chars:
                        chars.pop()
                        sys.stdout.write("\b \b"); sys.stdout.flush()
                else:
                    chars.append(c)
                    sys.stdout.write("*"); sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

R   = "\033[0m"
W   = "\033[97m"
GR  = "\033[38;5;71m"
RD  = "\033[38;5;203m"
YL  = "\033[38;5;220m"
CY  = "\033[38;5;81m"
MG  = "\033[38;5;141m"
GY  = "\033[38;5;245m"
BLD = "\033[1m"

ACCESS_TOKEN = "@@root-edward"

NOT_FOUND_HINTS = [
    "page not found","user not found","does not exist","no user",
    "account suspended","404 not found","profile not found",
    "sorry, this page","this account doesn't exist",
]

PLATFORMS = {
    "Chess.com":   {"url":"https://api.chess.com/pub/player/{u}",
                    "type":"api","profile":"https://www.chess.com/member/{u}"},
    "Lichess":     {"url":"https://lichess.org/api/user/{u}",
                    "type":"api","profile":"https://lichess.org/@/{u}"},
    "Reddit":      {"url":"https://www.reddit.com/user/{u}/about.json",
                    "type":"api","profile":"https://www.reddit.com/user/{u}",
                    "headers":{"User-Agent":"EPC-OSINT/1.0"}},
    "GitHub":      {"url":"https://api.github.com/users/{u}",
                    "type":"api","profile":"https://github.com/{u}"},
    "GitLab":      {"url":"https://gitlab.com/api/v4/users?username={u}",
                    "type":"api_list","profile":"https://gitlab.com/{u}"},
    "PyPI":        {"url":"https://pypi.org/pypi/{u}/json",
                    "type":"api","profile":"https://pypi.org/user/{u}"},
    "HackerNews":  {"url":"https://hacker-news.firebaseio.com/v0/user/{u}.json",
                    "type":"api","profile":"https://news.ycombinator.com/user?id={u}"},
    "Duolingo":    {"url":"https://www.duolingo.com/2017-06-30/users?username={u}",
                    "type":"api","profile":"https://www.duolingo.com/profile/{u}"},
    "Dev.to":      {"url":"https://dev.to/api/users/by_username?url={u}",
                    "type":"api","profile":"https://dev.to/{u}"},
    "npm":         {"url":"https://registry.npmjs.org/-/user/org.couchdb.user:{u}",
                    "type":"api","profile":"https://www.npmjs.com/~{u}"},
    "Gravatar":    {"url":"https://en.gravatar.com/{u}.json",
                    "type":"api","profile":"https://en.gravatar.com/{u}"},
    "Keybase":     {"url":"https://keybase.io/_/api/1.0/user/lookup.json?username={u}",
                    "type":"api","profile":"https://keybase.io/{u}"},
    "Bitbucket":   {"url":"https://api.bitbucket.org/2.0/users/{u}",
                    "type":"api","profile":"https://bitbucket.org/{u}"},
    "TryHackMe":   {"url":"https://tryhackme.com/api/user/exist/{u}",
                    "type":"api","profile":"https://tryhackme.com/p/{u}"},
    "ProductHunt": {"url":"https://www.producthunt.com/@{u}",
                    "type":"http","profile":"https://www.producthunt.com/@{u}"},
    "Pastebin":    {"url":"https://pastebin.com/u/{u}",
                    "type":"http","profile":"https://pastebin.com/u/{u}"},
    "Codecademy":  {"url":"https://www.codecademy.com/profiles/{u}",
                    "type":"http","profile":"https://www.codecademy.com/profiles/{u}"},
    "Linktree":    {"url":"https://linktr.ee/{u}",
                    "type":"http","profile":"https://linktr.ee/{u}"},
    "Instagram":   {"type":"manual","profile":"https://www.instagram.com/{u}/"},
    "TikTok":      {"type":"manual","profile":"https://www.tiktok.com/@{u}"},
    "Snapchat":    {"type":"manual","profile":"https://www.snapchat.com/add/{u}"},
    "Spotify":     {"type":"manual","profile":"https://open.spotify.com/user/{u}"},
    "Twitter / X": {"type":"manual","profile":"https://twitter.com/{u}"},
    "YouTube":     {"type":"manual","profile":"https://www.youtube.com/@{u}"},
    "Twitch":      {"type":"manual","profile":"https://www.twitch.tv/{u}"},
    "Steam":       {"type":"manual","profile":"https://steamcommunity.com/id/{u}"},
    "Telegram":    {"type":"manual","profile":"https://t.me/{u}"},
    "Medium":      {"type":"manual","profile":"https://medium.com/@{u}"},
    "Pinterest":   {"type":"manual","profile":"https://www.pinterest.com/{u}/"},
    "Roblox":      {"type":"manual","profile":"https://www.roblox.com/users/profile?username={u}"},
    "Replit":      {"type":"manual","profile":"https://replit.com/@{u}"},
}

CARRIER_TABLE = {
    "TR": {
        "name": "Turkey",
        "carriers": [
            {"prefix_hints": ["530","531","532","533","534","535","536","537","538","539"],
             "name": "Turkcell"},
            {"prefix_hints": ["540","541","542","543","544","545","546","547","548","549"],
             "name": "Vodafone TR"},
            {"prefix_hints": ["550","551","552","553","554","555","556","557","558","559"],
             "name": "Turk Telekom (Avea)"},
            {"prefix_hints": ["500","501","502","503","504","505","506","507","508","509"],
             "name": "Turk Telekom (Avea)"},
        ]
    },
    "US": {
        "name": "United States",
        "carriers": [
            {"prefix_hints": ["800","888","877","866","855","844","833"],
             "name": "Toll-Free"},
            {"prefix_hints": ["212","310","415","312","202","404","305"],
             "name": "Regional landline (various)"},
        ]
    },
    "DE": {
        "name": "Germany",
        "carriers": [
            {"prefix_hints": ["151","152","153","154","155","156","157","158","159"],
             "name": "Telekom Deutschland"},
            {"prefix_hints": ["160","161","162","163","164","165","166","167","168","169"],
             "name": "Vodafone DE"},
            {"prefix_hints": ["170","171","172","173","174","175","176","177","178","179"],
             "name": "Telekom / O2"},
        ]
    },
    "GB": {
        "name": "United Kingdom",
        "carriers": [
            {"prefix_hints": ["7911","7912","7913","7914","7915"],
             "name": "Vodafone UK"},
            {"prefix_hints": ["7700","7701","7702","7703","7704","7705"],
             "name": "O2 UK"},
            {"prefix_hints": ["7800","7801","7802","7803","7804","7805"],
             "name": "BT / EE"},
            {"prefix_hints": ["7400","7401","7402","7403","7404","7405"],
             "name": "Three UK"},
        ]
    },
    "FR": {
        "name": "France",
        "carriers": [
            {"prefix_hints": ["601","602","603","604","605","606","607","608","609"],
             "name": "Orange FR"},
            {"prefix_hints": ["611","612","613","614","615","616","617","618","619"],
             "name": "SFR"},
            {"prefix_hints": ["621","622","623","624","625","626","627","628","629"],
             "name": "Bouygues Telecom"},
            {"prefix_hints": ["631","632","633","634","635","636","637","638","639"],
             "name": "Free Mobile"},
        ]
    },
    "RU": {
        "name": "Russia",
        "carriers": [
            {"prefix_hints": ["910","911","912","913","914","915","916","917","918","919"],
             "name": "MTS"},
            {"prefix_hints": ["920","921","922","923","924","925","926","927","928","929"],
             "name": "MegaFon"},
            {"prefix_hints": ["900","901","902","903","904","905","906","907","908","909"],
             "name": "Beeline"},
        ]
    },
    "UA": {
        "name": "Ukraine",
        "carriers": [
            {"prefix_hints": ["630","631","632","633","634","635","636","637","638","639"],
             "name": "Kyivstar"},
            {"prefix_hints": ["660","661","662","663","664","665","666","667","668","669"],
             "name": "Vodafone UA"},
            {"prefix_hints": ["680","681","682","683","684","685","686","687","688","689"],
             "name": "lifecell"},
        ]
    },
    "PL": {
        "name": "Poland",
        "carriers": [
            {"prefix_hints": ["600","601","602","603","604","605","606","607","608","609"],
             "name": "Plus (Polkomtel)"},
            {"prefix_hints": ["500","501","502","503","504","505","506","507","508","509"],
             "name": "Orange PL"},
            {"prefix_hints": ["510","511","512","513","514","515","516","517","518","519"],
             "name": "T-Mobile PL"},
            {"prefix_hints": ["530","531","532","533","534","535","536","537","538","539"],
             "name": "Play"},
        ]
    },
    "NL": {
        "name": "Netherlands",
        "carriers": [
            {"prefix_hints": ["610","611","612","613","614","615","616","617","618","619"],
             "name": "KPN"},
            {"prefix_hints": ["620","621","622","623","624","625","626","627","628","629"],
             "name": "Vodafone NL"},
            {"prefix_hints": ["630","631","632","633","634","635","636","637","638","639"],
             "name": "T-Mobile NL"},
        ]
    },
    "IT": {
        "name": "Italy",
        "carriers": [
            {"prefix_hints": ["320","321","322","323","324","325","326","327","328","329"],
             "name": "Wind Tre"},
            {"prefix_hints": ["330","331","332","333","334","335","336","337","338","339"],
             "name": "Vodafone IT"},
            {"prefix_hints": ["340","341","342","343","344","345","346","347","348","349"],
             "name": "TIM"},
            {"prefix_hints": ["360","361","362","363","364","365","366","367","368","369"],
             "name": "Iliad IT"},
        ]
    },
    "ES": {
        "name": "Spain",
        "carriers": [
            {"prefix_hints": ["600","601","602","603","604","605","606","607","608","609"],
             "name": "Movistar"},
            {"prefix_hints": ["610","611","612","613","614","615","616","617","618","619"],
             "name": "Vodafone ES"},
            {"prefix_hints": ["620","621","622","623","624","625","626","627","628","629"],
             "name": "Orange ES"},
        ]
    },
    "SE": {
        "name": "Sweden",
        "carriers": [
            {"prefix_hints": ["700","701","702","703","704","705","706","707","708","709"],
             "name": "Telia SE"},
            {"prefix_hints": ["720","721","722","723","724","725","726","727","728","729"],
             "name": "Tele2 SE"},
            {"prefix_hints": ["730","731","732","733","734","735","736","737","738","739"],
             "name": "Tre SE"},
        ]
    },
    "CN": {
        "name": "China",
        "carriers": [
            {"prefix_hints": ["134","135","136","137","138","139","150","151","152","158","159","182","183","184","187","188","157","187","188","189"],
             "name": "China Mobile"},
            {"prefix_hints": ["130","131","132","155","156","145","185","186"],
             "name": "China Unicom"},
            {"prefix_hints": ["133","153","177","180","181","189","199"],
             "name": "China Telecom"},
        ]
    },
    "IN": {
        "name": "India",
        "carriers": [
            {"prefix_hints": ["700","701","702","703","704","705","706","707","708","709","710"],
             "name": "Jio"},
            {"prefix_hints": ["900","901","902","903","904","905","906","907","908","909"],
             "name": "Airtel"},
            {"prefix_hints": ["800","801","802","803","804","805","806","807","808","809"],
             "name": "Vi (Vodafone Idea)"},
            {"prefix_hints": ["920","921","922","923","924","925","926","927","928","929"],
             "name": "BSNL"},
        ]
    },
    "BR": {
        "name": "Brazil",
        "carriers": [
            {"prefix_hints": ["11","21","31","41","51","61","71","81","91"],
             "name": "Various (area code based)"},
        ]
    },
    "SA": {
        "name": "Saudi Arabia",
        "carriers": [
            {"prefix_hints": ["50","53","54","55","58"],
             "name": "STC"},
            {"prefix_hints": ["56","57"],
             "name": "Mobily"},
            {"prefix_hints": ["59"],
             "name": "Zain SA"},
        ]
    },
    "AE": {
        "name": "UAE",
        "carriers": [
            {"prefix_hints": ["50","52","55","56"],
             "name": "Etisalat (e&)"},
            {"prefix_hints": ["54","58"],
             "name": "du"},
        ]
    },
    "EG": {
        "name": "Egypt",
        "carriers": [
            {"prefix_hints": ["10","11"],
             "name": "Vodafone EG"},
            {"prefix_hints": ["12"],
             "name": "Orange EG"},
            {"prefix_hints": ["15"],
             "name": "Etisalat EG"},
            {"prefix_hints": ["14"],
             "name": "WE (Telecom Egypt)"},
        ]
    },
    "PK": {
        "name": "Pakistan",
        "carriers": [
            {"prefix_hints": ["300","301","302","303","304","305","306","307","308","309"],
             "name": "Mobilink / Jazz"},
            {"prefix_hints": ["310","311","312","313","314","315","316","317","318","319"],
             "name": "Zong"},
            {"prefix_hints": ["320","321","322","323","324","325","326","327","328","329"],
             "name": "Telenor PK"},
            {"prefix_hints": ["340","341","342","343","344","345","346","347","348","349"],
             "name": "Ufone"},
        ]
    },
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 EPC-OSINT/1.0"})
TIMEOUT = 8

def clear():
    os.system("cls" if sys.platform == "win32" else "clear")

def sep(char="─", w=72, color=GY):
    print(f"{color}{char * w}{R}")

def pause():
    print(f"\n  Press {W}ENTER{R} to return...", end="", flush=True)
    input()

def nav_prompt():
    print(f"\n  {GY}Press {W}1{GY} to skip  /  {W}0{GY} to go back  /  {W}ENTER{GY} for menu{R}  ",
          end="", flush=True)
    line = input().strip()
    if line == "1":  return "skip"
    if line == "0":  return "back"
    return "menu"

def fmt_ts(val):
    if not val:  return "N/A"
    try:
        return datetime.fromtimestamp(int(val), tz=timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    except Exception:
        return str(val)

def fmt_dt(s):
    if not s:  return "N/A"
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt[:19]).strftime("%d.%m.%Y %H:%M UTC")
        except Exception:
            pass
    return s

def spinner(stop_ev, label=""):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    i = 0
    while not stop_ev.is_set():
        sys.stdout.write(f"\r  {YL}{frames[i % len(frames)]}{R}  {label}   ")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write("\r" + " " * 70 + "\r")
    sys.stdout.flush()

def print_row(label, value, label_color=GY, value_color=W, width=None):
    pad = f"{label:<{width}}" if width else label
    print(f"  {label_color}{pad}{R} {value_color}{value}{R}")

BANNER_LINES = [
    r"  ███████╗████████╗██╗  ██╗██╗ ██████╗███████╗     ███████╗██████╗ ██╗   ██╗",
    r"  ██╔════╝╚══██╔══╝██║  ██║██║██╔════╝██╔════╝     ██╔════╝██╔══██╗╚██╗ ██╔╝",
    r"  █████╗     ██║   ███████║██║██║     ███████╗     ███████╗██████╔╝ ╚████╔╝ ",
    r"  ██╔══╝     ██║   ██╔══██║██║██║     ╚════██║     ╚════██║██╔═══╝   ╚██╔╝  ",
    r"  ███████╗   ██║   ██║  ██║██║╚██████╗███████║     ███████║██║        ██║   ",
    r"  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝     ╚══════╝╚═╝        ╚═╝   ",
]

def print_banner():
    print(f"\n{MG}{BLD}")
    for ln in BANNER_LINES: print(ln)
    print(R)

def login_screen():
    while True:
        clear()
        print_banner()
        sep()
        print(f"  {GY}=== Ethics Anti Extortion - Multipurpose Tool ==={R}")
        sep()
        print()
        token = getpass_star(f"  {W}Access Token:{R}      ")
        if token == ACCESS_TOKEN:
            return
        print(f"\n  {RD}[!] Invalid token.{R}")
        time.sleep(1.2)

def main_menu():
    clear()
    print_banner()
    sep()
    print(f"  {GY}Discord : {CY}ethicsware{R}")
    print(f"  {GY}GitHub  : {CY}github.com/Edwardiance{R}")
    sep()
    print(f"  {GY}[{W}1{GY}] {W}Spy Command        {GY}(OSINT Username Lookup)")
    print(f"  {GY}[{W}2{GY}] {W}PWN Check          {GY}(Gmail Breach Lookup)")
    print(f"  {GY}[{W}3{GY}] {W}Phone Number Lookup{GY}")
    print(f"  {GY}[{W}4{GY}] {W}IP Lookup          {GY}")
    print(f"  {GY}[{W}5{GY}] {W}Domain Lookup      {GY}")
    print(f"  {GY}[{W}6{GY}] {W}Email Lookup       {GY}(Account & Breach Finder)")
    print(f"  {GY}[{W}0{GY}] {W}Exit               {GY}")
    sep()
    print(f"\n  {W}Select >{R} ", end="", flush=True)
    return input().strip()

def check_platform(name, cfg, username):
    u       = username
    profile = cfg.get("profile","").replace("{u}", u)
    kind    = cfg.get("type","http")
    hdrs    = cfg.get("headers", {})

    if kind == "manual":
        return {"found": None, "url": profile, "data": {}, "kind": "manual"}

    api_url = cfg["url"].replace("{u}", u)
    try:
        r = SESSION.get(api_url, timeout=TIMEOUT, headers=hdrs, allow_redirects=True)

        if kind == "api":
            if r.status_code != 200:
                return {"found": False, "url": profile, "data": {}, "kind": "api"}
            try:
                d = r.json()
            except Exception:
                return {"found": True, "url": profile, "data": {}, "kind": "api"}
            if d is None:
                return {"found": False, "url": profile, "data": {}, "kind": "api"}
            if isinstance(d, dict) and d.get("error"):
                return {"found": False, "url": profile, "data": {}, "kind": "api"}
            if name == "Duolingo":
                users = d.get("users", [])
                if not users:
                    return {"found": False, "url": profile, "data": {}, "kind": "api"}
                d = users[0]
            if name == "TryHackMe":
                ok = d.get("status") == "success" or d.get("exists") is True
                return {"found": ok, "url": profile, "data": d, "kind": "api"}
            return {"found": True, "url": profile, "data": d, "kind": "api"}

        if kind == "api_list":
            if r.status_code == 200:
                lst = r.json()
                if isinstance(lst, list) and lst:
                    return {"found": True, "url": profile, "data": lst[0], "kind": "api"}
            return {"found": False, "url": profile, "data": {}, "kind": "api"}

        if r.status_code == 200:
            body = r.text.lower()
            if any(h in body for h in NOT_FOUND_HINTS):
                return {"found": False, "url": profile, "data": {}, "kind": "http"}
            return {"found": True, "url": profile, "data": {}, "kind": "http"}
        return {"found": False, "url": profile, "data": {}, "kind": "http"}

    except requests.exceptions.Timeout:
        return {"found": None, "url": profile, "data": {}, "kind": "timeout"}
    except Exception:
        return {"found": None, "url": profile, "data": {}, "kind": "error"}

def extract_info(name, data):
    if not data:
        return []
    if name == "Chess.com":
        pairs = [("Status",      data.get("status","N/A")),
                 ("Joined",      fmt_ts(data.get("joined"))),
                 ("Last Online", fmt_ts(data.get("last_online"))),
                 ("Streamer",    "Yes" if data.get("is_streamer") else "No"),
                 ("Verified",    "Yes" if data.get("verified") else "No")]
        if data.get("title"): pairs.insert(0, ("Title", data["title"]))
        return pairs
    if name == "Lichess":
        pairs = [("Username", data.get("username","N/A")),
                 ("Online",   "Yes" if data.get("online") else "No")]
        for cat in ("bullet","blitz","rapid","classical"):
            v = data.get("perfs",{}).get(cat,{}).get("rating")
            if v: pairs.append((f"{cat.capitalize()} rating", v))
        if data.get("bio"): pairs.append(("Bio", data["bio"][:80]))
        return pairs
    if name == "Reddit":
        return [("Name",        data.get("name","N/A")),
                ("Total Karma", str(data.get("total_karma",
                   data.get("link_karma",0)+data.get("comment_karma",0)))),
                ("Link Karma",  str(data.get("link_karma","N/A"))),
                ("Gold",        "Yes" if data.get("is_gold") else "No"),
                ("Created",     fmt_ts(data.get("created_utc")))]
    if name == "GitHub":
        return [("Name",         data.get("name","N/A")),
                ("Bio",          (data.get("bio") or "N/A")[:80]),
                ("Followers",    str(data.get("followers","N/A"))),
                ("Following",    str(data.get("following","N/A"))),
                ("Public Repos", str(data.get("public_repos","N/A"))),
                ("Location",     data.get("location") or "N/A"),
                ("Blog",         data.get("blog") or "N/A"),
                ("Company",      data.get("company") or "N/A"),
                ("Created",      fmt_dt(data.get("created_at","")))]
    if name == "Dev.to":
        return [("Name",    data.get("name","N/A")),
                ("Summary", (data.get("summary") or "N/A")[:80]),
                ("Joined",  fmt_dt(data.get("joined_at","")))]
    if name == "GitLab":
        return [("Name",    data.get("name","N/A")),
                ("State",   data.get("state","N/A")),
                ("Created", fmt_dt(data.get("created_at","")))]
    if name == "HackerNews":
        pairs = [("Karma",   str(data.get("karma","N/A"))),
                 ("Created", fmt_ts(data.get("created")))]
        if data.get("about"): pairs.append(("About", data["about"][:80]))
        return pairs
    if name == "Bitbucket":
        return [("Display Name", data.get("display_name","N/A")),
                ("Account Type", data.get("account_type","N/A")),
                ("Created",      fmt_dt(data.get("created_on","")))]
    if name == "Duolingo":
        return [("Name",   data.get("name","N/A")),
                ("Streak", str(data.get("streak","N/A"))),
                ("XP",     str(data.get("totalXp","N/A")))]
    if name == "Keybase":
        them = data.get("them", [{}])
        if isinstance(them, list) and them: them = them[0]
        return [("Username", them.get("basics",{}).get("username","N/A"))]
    return []

def show_network_map(username, results):
    clear(); sep()
    print(f"  {MG}{BLD}SOCIAL NETWORK MAP  /  {YL}{username}{R}"); sep(); print()

    found_auto = [n for n, r in results.items() if r["found"] is True]

    if not found_auto:
        print(f"  {RD}[!]  Not enough data to build a network map.{R}")
        print(f"  {GY}     No accounts were confirmed via API on any platform.{R}")
        print(); sep(); pause()
        return

    node_data = {}
    for n in found_auto:
        d = results[n].get("data", {})
        info = extract_info(n, d)
        node_data[n] = {k: str(v) for k, v in info}

    all_names     = {}
    all_locations = {}
    all_bios      = {}

    name_keys     = {"name", "Name", "Display Name", "Username"}
    location_keys = {"location", "Location"}
    bio_keys      = {"bio", "Bio", "About", "Summary"}

    for plat, info in node_data.items():
        for k, v in info.items():
            if v in ("N/A", "", "None"): continue
            if k in name_keys:
                all_names.setdefault(v, []).append(plat)
            if k in location_keys:
                all_locations.setdefault(v, []).append(plat)
            if k in bio_keys:
                all_bios.setdefault(v[:60], []).append(plat)

    print(f"  {W}[ PLATFORM NODES ]{R}"); print()
    for plat in found_auto:
        info = node_data.get(plat, {})
        url  = results[plat].get("url", "")
        print(f"  {GR}◉  {BLD}{plat}{R}")
        if url:
            print(f"  {GY}   ↳ {CY}{url}{R}")
        for k, v in info.items():
            if v not in ("N/A", "", "None"):
                print(f"  {GY}   {k:<16}{W}{v}{R}")
        print()

    has_links = False

    if any(len(v) > 1 for v in all_names.values()):
        sep(char="·")
        print(f"  {YL}{BLD}[ SHARED NAME / USERNAME ]{R}"); print()
        for val, plats in all_names.items():
            if len(plats) > 1:
                joined = f"  {GR}↔{R}  ".join(f"{GR}{p}{R}" for p in plats)
                print(f"  {W}\"{val}\"{R}  →  {joined}")
        print()
        has_links = True

    if any(len(v) > 1 for v in all_locations.values()):
        sep(char="·")
        print(f"  {YL}{BLD}[ SHARED LOCATION ]{R}"); print()
        for val, plats in all_locations.items():
            if len(plats) > 1:
                joined = f"  {GR}↔{R}  ".join(f"{GR}{p}{R}" for p in plats)
                print(f"  {W}\"{val}\"{R}  →  {joined}")
        print()
        has_links = True

    if any(len(v) > 1 for v in all_bios.values()):
        sep(char="·")
        print(f"  {YL}{BLD}[ SHARED BIO / DESCRIPTION ]{R}"); print()
        for val, plats in all_bios.items():
            if len(plats) > 1:
                joined = f"  {GR}↔{R}  ".join(f"{GR}{p}{R}" for p in plats)
                print(f"  {W}\"{val}...\"{R}  →  {joined}")
        print()
        has_links = True

    if not has_links:
        sep(char="·")
        print(f"  {GY}  No directly matching shared data found across platforms.")
        print(f"  {GY}  This may indicate different profile details are used per platform.{R}")
        print()

    manual_found = [n for n, r in results.items() if r["kind"] == "manual"]
    if manual_found:
        sep(char="·")
        print(f"  {YL}{BLD}[ PLATFORMS REQUIRING MANUAL VERIFICATION ]{R}")
        print(f"  {GY}  The platforms below cannot be checked via API.")
        print(f"  {GY}  Visit the profile URLs manually:{R}"); print()
        for n in sorted(manual_found):
            url = results[n].get("url","")
            print(f"  {YL}◎  {W}{n:<18}{R}  {CY}{url}{R}")
        print()

    sep()
    print(f"  {GY}Note: The network map is based solely on publicly available API data.{R}")
    sep(); pause()

def run_spy_for_username(username):
    results    = {}
    names      = list(PLATFORMS.keys())
    lock       = threading.Lock()
    scan_lines = []

    clear(); sep()
    print(f"  {MG}{BLD}SCANNING  /  {YL}{username}{R}"); sep(); print()

    def check_one(n):
        res = check_platform(n, PLATFORMS[n], username)
        with lock:
            results[n] = res
            f, url, knd = res["found"], res["url"], res["kind"]
            if knd == "manual":
                tag = f"{YL}[?]{R}"; lbl = f"{YL}{n:<18}{R} {GY}manual verification{R}"
            elif f is True:
                tag = f"{GR}[+]{R}"; lbl = f"{GR}{n:<18}{R} {CY}{url}{R}"
            elif f is False:
                tag = f"{RD}[-]{R}"; lbl = f"{GY}{n:<18}{R} Not Found"
            else:
                tag = f"{YL}[~]{R}"; lbl = f"{GY}{n:<18}{R} Timeout / Error"
            line = f"  {tag} {lbl}"
            scan_lines.append(line)
            print(line); sys.stdout.flush()

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(check_one, n): n for n in names}
        for fut in as_completed(futures):
            pass

    print(); sep()
    return results, scan_lines

def spy_command():
    clear(); sep()
    print(f"  {MG}{BLD}SPY COMMAND  —  USERNAME OSINT{R}"); sep(); print()

    print(f"  {GY}Select scan mode:{R}")
    print(f"  {GY}[{W}1{GY}] {W}Single Scan      {GY}(single username)")
    print(f"  {GY}[{W}2{GY}] {W}Bulk Scan        {GY}(comma-separated list of usernames)")
    print(f"  {GY}[{W}3{GY}] {W}Compare          {GY}(compare two usernames side by side)")
    print(f"  {GY}[{W}0{GY}] {W}Back              {GY}")
    print()
    print(f"  {W}Select >{R} ", end="", flush=True)
    mode = input().strip()

    if mode == "0": return
    elif mode == "2": spy_bulk()
    elif mode == "3": spy_compare()
    else: spy_single()

def spy_single():
    clear(); sep()
    print(f"  {MG}{BLD}SPY COMMAND  —  SINGLE SCAN{R}"); sep(); print()
    print(f"  {W}Enter the username:{R} ", end="", flush=True)
    username = input().strip()
    if not username: return

    results, scan_lines = run_spy_for_username(username)
    nav = nav_prompt()
    if nav in ("menu", "back"): return

    _spy_result_pages(username, results, scan_lines)

def _spy_result_pages(username, results, scan_lines):
    found_auto   = [n for n, r in results.items() if r["found"] is True]
    found_manual = [n for n, r in results.items() if r["kind"] == "manual"]
    not_found    = [n for n, r in results.items() if r["found"] is False]
    errors       = [n for n, r in results.items()
                    if r["found"] is None and r["kind"] != "manual"]
    total        = len(PLATFORMS)
    conf_str     = ("HIGH"   if len(found_auto) >= 4 else
                    "MEDIUM" if len(found_auto) >= 2 else "LOW")
    conf_col     = (GR if conf_str == "HIGH" else YL if conf_str == "MEDIUM" else RD)

    while True:
        clear(); sep()
        print(f"  {MG}{BLD}OPEN SOURCE INFORMATION{R}"); sep(); print()
        print_row("Searched Username:", username, value_color=YL)
        print_row("Platforms Found:", str(len(found_auto)), value_color=GR)
        print_row("Manual Check:", str(len(found_manual)), value_color=YL)
        print_row("Not Found:", str(len(not_found)), value_color=RD)
        print_row("Errors / Timeouts:", str(len(errors)), value_color=GY)
        print_row("Confidence:", conf_str, value_color=conf_col)
        print_row("Sites Checked:", str(total), value_color=W)
        print(); sep()
        nav = nav_prompt()
        if nav == "menu": return
        if nav == "back":
            clear(); sep()
            print(f"  {MG}{BLD}SCAN RESULTS  /  {YL}{username}{R}"); sep(); print()
            for ln in scan_lines: print(ln)
            print(); sep()
            nav2 = nav_prompt()
            if nav2 in ("menu","back"): return
        break

    while True:
        clear(); sep()
        print(f"  {MG}{BLD}FALSE-POSITIVE INFORMATION{R}"); sep(); print()
        print(f"  {GR}{R}  API verified / safe")
        print(f"  {RD}{R}  Not found")
        print(f"  {YL}{R}  Manual control needed  (JS / Cloudflare protection)")
        print()
        if found_auto:
            print(f"  {W}Automated Checks{R}")
            for n in sorted(found_auto): print(f"  {GR} {n}{R}")
            print()
        if found_manual:
            print(f"  {W}Manual Check Links{R}")
            for n in sorted(found_manual): print(f"  {YL} {n}{R}")
            print()
        if not_found:
            print(f"  {W}Not Found{R}")
            for n in sorted(not_found): print(f"  {RD} {n}{R}")
            print()
        sep()
        nav = nav_prompt()
        if nav == "menu": return
        if nav == "back": continue
        break

    while True:
        clear(); sep()
        print(f"  {MG}{BLD}MANUAL CHECK LINKS{R}"); sep()
        print(f"  {GY}Platforms listed below require manual verification.{R}"); print()
        for i, n in enumerate(sorted(found_manual)):
            url = results[n]["url"]
            print(f"  {YL}{R}  {W}{n:<16}{R}  {CY}{url}{R}")
            if (i+1) % 4 == 0: print()
        print(); sep()
        nav = nav_prompt()
        if nav == "menu": return
        if nav == "back": break
        break

    clear(); sep()
    print(f"  {MG}{BLD}RESULTS{R}"); sep(); print()
    bullet_facts = []
    for n in found_auto:
        res  = results[n]
        info = extract_info(n, res.get("data", {}))
        print(f"  {GR}  {BLD}{n}{R}")
        print(f"  {GY}     {CY}{res['url']}{R}")
        for label, val in info:
            s = str(val)
            print(f"  {GY}    {label:<16}{W}{s}{R}")
            bullet_facts.append(f"{n} -- {label}: {s}")
        print()
    sep(); print()
    print_row("Username:", username, value_color=YL)
    print_row("Found on:", f"{len(found_auto)} platform(s)", value_color=GR)
    print()
    if bullet_facts:
        print(f"  {MG}{BLD}About Person:{R}")
        for f in bullet_facts[:12]:
            print(f"  {GR}-{R} {GY}{f}{R}")
    print(); sep()

    print(f"\n  {GY}Press {W}ENTER{GY} to view the social network map,")
    print(f"  or press {W}0{GY} to return to the main menu.{R}  ", end="", flush=True)
    c = input().strip()
    if c == "0": return
    show_network_map(username, results)

def spy_bulk():
    clear(); sep()
    print(f"  {MG}{BLD}SPY COMMAND  —  BULK SCAN{R}"); sep(); print()
    print(f"  {GY}Enter usernames separated by commas:{R}")
    print(f"  {GY}Example: {W}john_doe, jane123, hacker99{R}"); print()
    print(f"  {W}Usernames >{R} ", end="", flush=True)
    raw = input().strip()
    if not raw: return

    usernames = [u.strip() for u in raw.split(",") if u.strip()]
    if not usernames:
        print(f"  {RD}[!] No valid usernames found.{R}")
        time.sleep(1.5)
        return

    if len(usernames) > 10:
        print(f"  {YL}[!] Maximum 10 usernames allowed. Using first 10.{R}")
        usernames = usernames[:10]
        time.sleep(1.2)

    all_results = {}

    for idx, username in enumerate(usernames, 1):
        print()
        sep()
        print(f"  {MG}{BLD}[{idx}/{len(usernames)}]  SCANNING:  {YL}{username}{R}")
        sep(); print()
        results, _ = run_spy_for_username(username)
        all_results[username] = results
        time.sleep(0.3)

    clear(); sep()
    print(f"  {MG}{BLD}BULK SCAN RESULTS{R}"); sep(); print()

    for username, results in all_results.items():
        found_auto   = [n for n, r in results.items() if r["found"] is True]
        found_manual = [n for n, r in results.items() if r["kind"] == "manual"]
        conf_str     = ("HIGH"   if len(found_auto) >= 4 else
                        "MEDIUM" if len(found_auto) >= 2 else "LOW")
        conf_col     = (GR if conf_str == "HIGH" else YL if conf_str == "MEDIUM" else RD)

        print(f"  {YL}{BLD}{username}{R}")
        print(f"  {GY}  API Verified    : {GR}{len(found_auto)}{R}  "
              f"{GY}Manual          : {YL}{len(found_manual)}{R}  "
              f"{GY}Confidence      : {conf_col}{conf_str}{R}")

        if found_auto:
            plat_str = ", ".join(found_auto[:8])
            if len(found_auto) > 8:
                plat_str += f" +{len(found_auto)-8} more"
            print(f"  {GY}  Platforms       : {GR}{plat_str}{R}")
        else:
            print(f"  {GY}  Platforms       : {RD}Not found on any{R}")
        print()

    sep()
    print(f"  {GY}Use Single Scan mode for a detailed report.{R}")
    sep(); pause()

def spy_compare():
    clear(); sep()
    print(f"  {MG}{BLD}SPY COMMAND  —  COMPARE MODE{R}"); sep(); print()
    print(f"  {GY}Scans two usernames side by side and highlights shared platforms.{R}"); print()

    print(f"  {W}1st Username >{R} ", end="", flush=True)
    u1 = input().strip()
    if not u1: return

    print(f"  {W}2nd Username >{R} ", end="", flush=True)
    u2 = input().strip()
    if not u2: return

    print()
    sep()
    print(f"  {MG}{BLD}SCANNING: {YL}{u1}{R}"); sep(); print()
    r1, _ = run_spy_for_username(u1)

    print()
    sep()
    print(f"  {MG}{BLD}SCANNING: {YL}{u2}{R}"); sep(); print()
    r2, _ = run_spy_for_username(u2)

    clear(); sep()
    print(f"  {MG}{BLD}COMPARISON RESULT{R}"); sep(); print()

    found1 = {n for n, r in r1.items() if r["found"] is True}
    found2 = {n for n, r in r2.items() if r["found"] is True}
    common = sorted(found1 & found2)
    only1  = sorted(found1 - found2)
    only2  = sorted(found2 - found1)

    col_w = 22
    print(f"  {GY}{'Platform':<28}  {YL}{u1:<{col_w}}{R}  {CY}{u2:<{col_w}}{R}")
    sep(char="─", w=72)

    all_platforms = sorted(found1 | found2)
    for plat in all_platforms:
        in1 = plat in found1
        in2 = plat in found2
        mark1 = f"{GR}✔  FOUND{R}" if in1 else f"{RD}✘  ——{R}"
        mark2 = f"{GR}✔  FOUND{R}" if in2 else f"{RD}✘  ——{R}"
        row_col = YL if (in1 and in2) else W
        print(f"  {row_col}{plat:<28}{R}  {mark1:<28}  {mark2}")

    print()
    sep()
    print(f"  {W}[ SUMMARY ]{R}"); print()
    print_row(f"{u1} Total:", f"{len(found1)} platform(s)", value_color=YL)
    print_row(f"{u2} Total:", f"{len(found2)} platform(s)", value_color=CY)

    if common:
        print()
        print(f"  {YL}{BLD}Shared Platforms ({len(common)} found):{R}")
        for c in common:
            print(f"  {YL}◈  {W}{c}{R}")
        print()
        if len(common) >= 3:
            print(f"  {RD}[!]  High overlap — these two accounts may belong to the same person.{R}")
        elif len(common) >= 1:
            print(f"  {YL}[~]  Medium overlap — same username may be in use.{R}")
    else:
        print()
        print(f"  {GR}[OK]  No shared platforms found. Accounts likely belong to different people.{R}")

    if only1:
        print()
        print(f"  {W}Only {YL}{u1}{W} found on:{R}")
        print(f"  {GY}  " + ", ".join(only1) + f"{R}")
    if only2:
        print()
        print(f"  {W}Only {CY}{u2}{W} found on:{R}")
        print(f"  {GY}  " + ", ".join(only2) + f"{R}")

    print(); sep(); pause()

def pwn_check():
    clear(); sep()
    print(f"  {MG}{BLD}PWN CHECK  —  GMAIL BREACH LOOKUP{R}"); sep(); print()
    print(f"  {W}Enter the Gmail you want to search:{R} ", end="", flush=True)
    email = input().strip()
    if not email: return

    clear(); sep()
    print(f"  {MG}{BLD}PWN CHECK  /  {YL}{email}{R}"); sep(); print()

    breaches       = []
    breach_details = []

    stop_ev = threading.Event()
    t = threading.Thread(target=spinner,
                         args=(stop_ev, "Querying breach databases..."), daemon=True)
    t.start()

    try:
        r = SESSION.get(
            f"https://api.xposedornot.com/v1/breach-analytics?email={email}",
            timeout=12)
        if r.status_code == 200:
            d = r.json()
            for b in d.get("ExposedBreaches", {}).get("breaches_details", []):
                name   = b.get("breach", b.get("name","Unknown"))
                fields = [x.strip() for x in b.get("xposed_data","").split(";") if x.strip()]
                breaches.append(name)
                breach_details.append({"site": name, "fields": fields})
    except Exception:
        pass

    if not breaches:
        try:
            r2 = SESSION.get(
                f"https://leakcheck.io/api/public?check={email}", timeout=10)
            if r2.status_code == 200:
                d2 = r2.json()
                if d2.get("success"):
                    for s in d2.get("sources", []):
                        name = s.get("name","Unknown")
                        flds = s.get("fields", [])
                        breaches.append(name)
                        breach_details.append({"site": name, "fields": flds})
        except Exception:
            pass

    stop_ev.set(); t.join()

    print()
    if breaches:
        for b in breaches:
            print(f"  {RD}[!]{R} Breach at: {W}{b}{R}")
    else:
        print(f"  {GR}[OK]{R} No public breaches found for this address.")
        print(f"  {GY}    Free APIs have limited coverage -- result may not be exhaustive.{R}")

    risk = ("HIGH" if len(breaches) >= 5 else "MEDIUM" if len(breaches) >= 2 else "LOW")
    rc   = (RD if risk == "HIGH" else YL if risk == "MEDIUM" else GR)

    print(); sep()
    print(f"  {W}[OPEN SOURCE INFORMATION]{R}")
    print_row("Gmail:", email)
    print_row("Risk:", risk, value_color=rc)
    print()

    if breach_details:
        for bd in breach_details:
            site = bd["site"]
            for fld in bd["fields"]:
                fl = fld.lower()
                if "password" in fl:
                    print(f"  {RD}-{R} Breached {W}password{R} at {W}{site}{RD}!{R}")
                elif "email" in fl or "username" in fl:
                    print(f"  {YL}-{R} Breached {W}{fld}{R} at {W}{site}{R}")
                elif "ip" in fl:
                    print(f"  {YL}-{R} Breached {W}IP address{R} at {W}{site}{R}")
                else:
                    print(f"  {GY}-{R} Breached {W}{fld}{R} at {W}{site}{R}")

    print(); sep(); pause()

def phone_lookup():
    clear(); sep()
    print(f"  {MG}{BLD}PHONE NUMBER LOOKUP{R}"); sep(); print()
    print(f"  {GY}Enter number in international format  {W}e.g. +90 555 123 4567{R}")
    print(f"  {W}Phone Number:{R} ", end="", flush=True)
    raw = input().strip()
    if not raw: return

    digits_only = "".join(c for c in raw if c.isdigit() or c == "+")
    if not digits_only.startswith("+"):
        digits_only = "+" + digits_only

    clear(); sep()
    print(f"  {MG}{BLD}PHONE LOOKUP  /  {YL}{digits_only}{R}"); sep(); print()

    stop_ev = threading.Event()
    t = threading.Thread(target=spinner,
                         args=(stop_ev, "Querying phone databases..."), daemon=True)
    t.start()

    result = {
        "valid":        None,
        "number":       digits_only,
        "local_format": "N/A",
        "intl_format":  digits_only,
        "country":      "N/A",
        "country_code": "N/A",
        "location":     "N/A",
        "carrier":      "N/A",
        "line_type":    "N/A",
        "timezone":     "N/A",
        "region_code":  None,
        "national_num": None,
    }

    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone as pn_tz

        parsed = phonenumbers.parse(digits_only, None)
        result["valid"]        = phonenumbers.is_valid_number(parsed)
        result["local_format"] = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        result["intl_format"]  = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        result["country_code"] = f"+{parsed.country_code}"
        result["national_num"] = str(parsed.national_number)

        geo = geocoder.description_for_number(parsed, "en")
        if geo: result["location"] = geo

        carr = carrier.name_for_number(parsed, "en")
        if carr: result["carrier"] = carr

        tzs = pn_tz.time_zones_for_number(parsed)
        if tzs: result["timezone"] = ", ".join(tzs)

        region = phonenumbers.region_code_for_number(parsed)
        result["region_code"] = region

        if region:
            region_map = {
                "TR":"Turkey","US":"United States","GB":"United Kingdom",
                "DE":"Germany","FR":"France","IT":"Italy","ES":"Spain",
                "RU":"Russia","UA":"Ukraine","PL":"Poland","NL":"Netherlands",
                "BE":"Belgium","CH":"Switzerland","AT":"Austria","SE":"Sweden",
                "NO":"Norway","DK":"Denmark","FI":"Finland","PT":"Portugal",
                "GR":"Greece","CZ":"Czech Republic","HU":"Hungary","RO":"Romania",
                "BG":"Bulgaria","HR":"Croatia","SK":"Slovakia","SI":"Slovenia",
                "EE":"Estonia","LV":"Latvia","LT":"Lithuania","AL":"Albania",
                "RS":"Serbia","BA":"Bosnia and Herzegovina","MK":"North Macedonia",
                "CN":"China","JP":"Japan","KR":"South Korea","IN":"India",
                "BR":"Brazil","MX":"Mexico","AR":"Argentina","AU":"Australia",
                "CA":"Canada","ZA":"South Africa","EG":"Egypt","NG":"Nigeria",
                "SA":"Saudi Arabia","AE":"UAE","IL":"Israel","IR":"Iran",
                "PK":"Pakistan","BD":"Bangladesh","ID":"Indonesia","TH":"Thailand",
                "VN":"Vietnam","PH":"Philippines","MY":"Malaysia","SG":"Singapore",
            }
            result["country"] = region_map.get(region, region)

    except ImportError:
        pass
    except Exception:
        pass

    carrier_from_table = None
    carrier_table_note = None

    region_code = result.get("region_code")
    national    = result.get("national_num", "")

    if region_code and region_code in CARRIER_TABLE and national:
        tbl = CARRIER_TABLE[region_code]
        for entry in tbl["carriers"]:
            for prefix in entry["prefix_hints"]:
                if national.startswith(prefix):
                    carrier_from_table = entry["name"]
                    break
            if carrier_from_table:
                break

        if not carrier_from_table:
            carrier_table_note = f"Country: {tbl['name']} — no prefix match, table check complete"

    if carrier_from_table:
        if result["carrier"] == "N/A":
            result["carrier"] = carrier_from_table
        else:
            result["carrier_table"] = carrier_from_table

    if result["valid"] is None:
        try:
            r = SESSION.get(
                f"https://api.apilayer.com/number_verification/validate?number={digits_only}",
                timeout=10)
            if r.status_code == 200:
                d = r.json()
                result["valid"]        = d.get("valid", False)
                result["country"]      = d.get("country_name", "N/A")
                result["country_code"] = d.get("country_code", "N/A")
                result["location"]     = d.get("location", "N/A")
                result["carrier"]      = d.get("carrier", "N/A")
                result["line_type"]    = d.get("line_type", "N/A")
                result["local_format"] = d.get("local_format", "N/A")
                result["intl_format"]  = d.get("international_format", digits_only)
        except Exception:
            pass

    try:
        r3 = SESSION.get(
            f"https://phonevalidation.abstractapi.com/v1/?api_key=free&phone={digits_only}",
            timeout=8)
        if r3.status_code == 200:
            d3 = r3.json()
            if d3.get("carrier") and result["carrier"] == "N/A":
                result["carrier"] = d3["carrier"]
            if d3.get("type") and result["line_type"] == "N/A":
                result["line_type"] = d3["type"].capitalize()
            if d3.get("country",{}).get("name") and result["country"] == "N/A":
                result["country"] = d3["country"]["name"]
    except Exception:
        pass

    stop_ev.set(); t.join()

    print()
    valid_str = (f"{GR}Yes{R}" if result["valid"] else
                 f"{RD}No{R}"  if result["valid"] is False else
                 f"{YL}Unknown{R}")

    sep()
    print(f"  {W}[PHONE NUMBER INFORMATION]{R}"); print()
    print_row("Number (Intl):", result["intl_format"],  value_color=YL)
    print_row("Number (Local):", result["local_format"],  value_color=W)
    print_row("Country Code:", result["country_code"],  value_color=W)
    print_row("Country:", result["country"],       value_color=W)
    print_row("Location / Region:", result["location"],      value_color=W)
    print_row("Carrier / Operator:", result["carrier"],       value_color=CY)

    if result.get("carrier_table"):
        print_row("Carrier (Table):", result["carrier_table"], value_color=CY)

    print_row("Line Type:", result["line_type"],     value_color=W)
    print_row("Timezone:", result["timezone"],      value_color=W)
    print(f"  {GY}{'Valid Number':<18}{R}{valid_str}")
    print()

    filled = sum(1 for k in ("country","carrier","location","line_type","timezone")
                 if result[k] not in ("N/A",""))
    conf   = ("HIGH" if filled >= 4 else "MEDIUM" if filled >= 2 else "LOW")
    cc     = (GR if conf == "HIGH" else YL if conf == "MEDIUM" else RD)
    print_row("Data Confidence:", conf, value_color=cc)

    if region_code and region_code in CARRIER_TABLE:
        tbl = CARRIER_TABLE[region_code]
        print()
        sep(char="·")
        print(f"  {W}[COUNTRY CARRIER TABLE — {tbl['name'].upper()}]{R}"); print()
        for entry in tbl["carriers"]:
            prefixes_str = ", ".join(entry["prefix_hints"][:5])
            if len(entry["prefix_hints"]) > 5:
                prefixes_str += f" +{len(entry['prefix_hints'])-5} more"
            match = ""
            if national:
                for p in entry["prefix_hints"]:
                    if national.startswith(p):
                        match = f"  {GR}<-- this number{R}"
                        break
            print(f"  {GY}{entry['name']:<28}{R}  {W}{prefixes_str}{R}{match}")
        if carrier_table_note:
            print(f"\n  {GY}Note: {carrier_table_note}{R}")
        print()

    if result["valid"] is False:
        print(f"\n  {RD}[!] This number appears to be invalid or unassigned.{R}")
    elif result["valid"] is None:
        print(f"\n  {YL}[~] Could not fully verify. Install 'phonenumbers' library for")
        print(f"      offline validation:  {W}pip install phonenumbers{R}")

    print()
    sep()
    print(f"  {GY}Note: Carrier info is from public numbering databases.{R}")
    print(f"  {GY}Owner identity is not available through open sources.{R}")
    sep(); pause()

def ip_lookup():
    clear(); sep()
    print(f"  {MG}{BLD}IP LOOKUP{R}"); sep(); print()
    print(f"  {GY}Enter an IPv4 or IPv6 address  {W}e.g. 8.8.8.8{R}")
    print(f"  {W}IP Address:{R} ", end="", flush=True)
    ip = input().strip()
    if not ip: return

    clear(); sep()
    print(f"  {MG}{BLD}IP LOOKUP  /  {YL}{ip}{R}"); sep(); print()

    stop_ev = threading.Event()
    t = threading.Thread(target=spinner,
                         args=(stop_ev, "Querying IP intelligence sources..."), daemon=True)
    t.start()

    data = {
        "ip":           ip,
        "valid":        None,
        "country":      "N/A",
        "country_code": "N/A",
        "region":       "N/A",
        "city":         "N/A",
        "zip":          "N/A",
        "lat":          "N/A",
        "lon":          "N/A",
        "timezone":     "N/A",
        "isp":          "N/A",
        "org":          "N/A",
        "asn":          "N/A",
        "reverse_dns":  "N/A",
        "proxy":        "N/A",
        "hosting":      "N/A",
        "mobile":       "N/A",
        "abuse_email":  "N/A",
    }

    try:
        r = SESSION.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
            f"region,regionName,city,zip,lat,lon,timezone,isp,org,as,reverse,proxy,hosting,mobile",
            timeout=10)
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == "success":
                data["valid"]        = True
                data["country"]      = d.get("country",      "N/A")
                data["country_code"] = d.get("countryCode",  "N/A")
                data["region"]       = d.get("regionName",   "N/A")
                data["city"]         = d.get("city",         "N/A")
                data["zip"]          = d.get("zip",          "N/A")
                data["lat"]          = str(d.get("lat",      "N/A"))
                data["lon"]          = str(d.get("lon",      "N/A"))
                data["timezone"]     = d.get("timezone",     "N/A")
                data["isp"]          = d.get("isp",          "N/A")
                data["org"]          = d.get("org",          "N/A")
                data["asn"]          = d.get("as",           "N/A")
                data["reverse_dns"]  = d.get("reverse",      "N/A")
                data["proxy"]        = "Yes" if d.get("proxy")   else "No"
                data["hosting"]      = "Yes" if d.get("hosting") else "No"
                data["mobile"]       = "Yes" if d.get("mobile")  else "No"
            else:
                data["valid"] = False
    except Exception:
        pass

    if data["valid"] is None:
        try:
            r2 = SESSION.get(f"https://ipwho.is/{ip}", timeout=10)
            if r2.status_code == 200:
                d2 = r2.json()
                if d2.get("success"):
                    data["valid"]        = True
                    data["country"]      = d2.get("country",      "N/A")
                    data["country_code"] = d2.get("country_code", "N/A")
                    data["region"]       = d2.get("region",       "N/A")
                    data["city"]         = d2.get("city",         "N/A")
                    data["lat"]          = str(d2.get("latitude",  "N/A"))
                    data["lon"]          = str(d2.get("longitude", "N/A"))
                    data["timezone"]     = d2.get("timezone", {}).get("id", "N/A")
                    data["isp"]          = d2.get("connection", {}).get("isp", "N/A")
                    data["asn"]          = str(d2.get("connection", {}).get("asn", "N/A"))
                    data["org"]          = d2.get("connection", {}).get("org", "N/A")
        except Exception:
            pass

    if data["reverse_dns"] == "N/A":
        try:
            rdns = socket.gethostbyaddr(ip)
            if rdns and rdns[0]:
                data["reverse_dns"] = rdns[0]
        except Exception:
            pass

    stop_ev.set(); t.join()

    print()
    if data["valid"] is False:
        print(f"  {RD}[!] Invalid or private IP address. Cannot resolve.{R}")
        print(); sep(); pause()
        return

    sep()
    print(f"  {W}[GEOLOCATION]{R}"); print()
    print_row("IP Address:", data["ip"],           value_color=YL)
    print_row("Country:", f"{data['country']} ({data['country_code']})", value_color=W)
    print_row("Region:", data["region"],       value_color=W)
    print_row("City:", data["city"],         value_color=W)
    print_row("ZIP Code:", data["zip"],          value_color=W)
    print_row("Coordinates:", f"{data['lat']}, {data['lon']}", value_color=CY)
    print_row("Timezone:", data["timezone"],     value_color=W)
    print()

    sep()
    print(f"  {W}[NETWORK INFORMATION]{R}"); print()
    print_row("ISP:", data["isp"],          value_color=W)
    print_row("Organization:", data["org"],          value_color=W)
    print_row("ASN:", data["asn"],          value_color=W)
    print_row("Reverse DNS:", data["reverse_dns"],  value_color=CY)
    print()

    sep()
    print(f"  {W}[FLAGS]{R}"); print()

    def flag_line(label, val, yes_bad=True):
        if val == "Yes":
            col = RD if yes_bad else GR
        elif val == "No":
            col = GR if yes_bad else RD
        else:
            col = GY
        print_row(label, val, value_color=col)

    flag_line("Proxy / VPN       :", data["proxy"],   yes_bad=True)
    flag_line("Hosting / DC      :", data["hosting"], yes_bad=True)
    flag_line("Mobile Network    :", data["mobile"],  yes_bad=False)
    print()

    if data["lat"] != "N/A" and data["lon"] != "N/A":
        maps_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
        print_row("Google Maps:", maps_url, value_color=CY)

    sep(char="·")
    print(f"  {W}[SHODAN SEARCH LINK]{R}"); print()
    shodan_url = f"https://www.shodan.io/host/{ip}"
    print(f"  {GY}Open ports, services, and banner info for this IP")
    print(f"  can be explored on Shodan:{R}")
    print()
    print(f"  {CY}{shodan_url}{R}")
    print()
    print(f"  {GY}Note: A free Shodan account is sufficient to search.{R}")
    print()

    sep()
    print(f"  {GY}Sources: ip-api.com  /  ipwho.is  /  socket rDNS  /  Shodan (link){R}")
    sep(); pause()

def domain_lookup():
    clear(); sep()
    print(f"  {MG}{BLD}DOMAIN LOOKUP{R}"); sep(); print()
    print(f"  {GY}Enter a domain name  {W}e.g. google.com  or  https://google.com{R}")
    print(f"  {W}Domain:{R} ", end="", flush=True)
    raw = input().strip()
    if not raw: return

    domain = raw.lower()
    for prefix in ("https://","http://","www."):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0].strip()

    clear(); sep()
    print(f"  {MG}{BLD}DOMAIN LOOKUP  /  {YL}{domain}{R}"); sep(); print()

    stop_ev = threading.Event()
    t = threading.Thread(target=spinner,
                         args=(stop_ev, "Querying domain intelligence sources..."), daemon=True)
    t.start()

    data = {
        "domain":        domain,
        "registrar":     "N/A",
        "created":       "N/A",
        "updated":       "N/A",
        "expires":       "N/A",
        "status":        "N/A",
        "name_servers":  [],
        "dnssec":        "N/A",
        "registrant":    "N/A",
        "country":       "N/A",
        "emails":        [],
        "ip_addresses":  [],
        "mx_records":    [],
        "txt_records":   [],
        "resolved_ip":   "N/A",
        "ip_country":    "N/A",
        "ip_isp":        "N/A",
        "ssl_issuer":    "N/A",
        "ssl_expiry":    "N/A",
        "subdomains":    [],
    }

    try:
        ip_list = socket.getaddrinfo(domain, None)
        ips = list(dict.fromkeys(r[4][0] for r in ip_list))
        data["ip_addresses"] = ips
        if ips:
            data["resolved_ip"] = ips[0]
    except Exception:
        pass

    if data["resolved_ip"] != "N/A":
        try:
            ri = SESSION.get(
                f"http://ip-api.com/json/{data['resolved_ip']}?fields=country,isp,org",
                timeout=8)
            if ri.status_code == 200:
                di = ri.json()
                if di.get("status") == "success":
                    data["ip_country"] = di.get("country", "N/A")
                    data["ip_isp"]     = di.get("isp", di.get("org","N/A"))
        except Exception:
            pass

    try:
        rdap_r = SESSION.get(f"https://rdap.org/domain/{domain}", timeout=12)
        if rdap_r.status_code == 200:
            rd = rdap_r.json()
            for ev in rd.get("events", []):
                act  = ev.get("eventAction","")
                date = ev.get("eventDate","")[:10]
                if "registration" in act:   data["created"] = date
                elif "expiration" in act:   data["expires"] = date
                elif "last changed" in act: data["updated"] = date
            ns_list = [ns.get("ldhName","").lower()
                       for ns in rd.get("nameservers",[]) if ns.get("ldhName")]
            if ns_list: data["name_servers"] = ns_list
            statuses = rd.get("status", [])
            if statuses: data["status"] = ", ".join(statuses[:3])
            for entity in rd.get("entities", []):
                roles = entity.get("roles", [])
                vcard = entity.get("vcardArray", [])
                if "registrar" in roles:
                    for vc in (vcard[1] if len(vcard) > 1 else []):
                        if vc[0] == "fn":
                            data["registrar"] = vc[3]
                if "registrant" in roles:
                    for vc in (vcard[1] if len(vcard) > 1 else []):
                        if vc[0] == "org":
                            data["registrant"] = vc[3]
                        elif vc[0] == "email":
                            data["emails"].append(vc[3])
                        elif vc[0] == "adr":
                            addr = vc[3]
                            if isinstance(addr, list) and len(addr) > 6:
                                data["country"] = addr[6]
            data["dnssec"] = "Signed" if rd.get("secureDNS",{}).get("delegationSigned") else "Unsigned"
    except Exception:
        pass

    try:
        import dns.resolver
        mx_answers = dns.resolver.resolve(domain, "MX")
        data["mx_records"] = sorted(
            [str(r.exchange).rstrip(".") for r in mx_answers])[:5]
    except Exception:
        try:
            doh = SESSION.get(
                f"https://dns.google/resolve?name={domain}&type=MX",
                timeout=8)
            if doh.status_code == 200:
                answers = doh.json().get("Answer", [])
                mx_raw  = [a.get("data","") for a in answers if a.get("type") == 15]
                parsed  = []
                for m in mx_raw:
                    parts = m.split()
                    if len(parts) >= 2:
                        parsed.append(parts[1].rstrip("."))
                data["mx_records"] = sorted(parsed)[:5]
        except Exception:
            pass

    try:
        doh_txt = SESSION.get(
            f"https://dns.google/resolve?name={domain}&type=TXT",
            timeout=8)
        if doh_txt.status_code == 200:
            answers = doh_txt.json().get("Answer", [])
            for a in answers:
                val = a.get("data","").strip('"')
                if val.startswith(("v=spf","v=DMARC","google-site","MS=")):
                    data["txt_records"].append(val[:80])
    except Exception:
        pass

    try:
        import ssl
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(
                socket.create_connection((domain, 443), timeout=6),
                server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            issuer = dict(x[0] for x in cert.get("issuer",[]))
            data["ssl_issuer"] = issuer.get("organizationName", "N/A")
            nb = cert.get("notAfter","")
            if nb:
                try:
                    exp = datetime.strptime(nb, "%b %d %H:%M:%S %Y %Z")
                    data["ssl_expiry"] = exp.strftime("%d.%m.%Y")
                    days_left = (exp - datetime.utcnow()).days
                    data["ssl_days_left"] = days_left
                except Exception:
                    data["ssl_expiry"] = nb
    except Exception:
        data["ssl_days_left"] = None

    try:
        crt_r = SESSION.get(
            f"https://crt.sh/?q=%.{domain}&output=json",
            timeout=15)
        if crt_r.status_code == 200:
            crt_data = crt_r.json()
            seen = set()
            for entry in crt_data:
                for name in entry.get("name_value","").splitlines():
                    name = name.strip().lower().lstrip("*.")
                    if name and name != domain and name.endswith(f".{domain}"):
                        seen.add(name)
            data["subdomains"] = sorted(seen)[:40]
    except Exception:
        pass

    stop_ev.set(); t.join()

    print()
    sep()
    print(f"  {W}[REGISTRATION]{R}"); print()
    print_row("Domain:", data["domain"],     value_color=YL)
    print_row("Registrar:", data["registrar"],  value_color=W)
    print_row("Registrant:", data["registrant"], value_color=W)
    print_row("Country:", data["country"],    value_color=W)
    print_row("Created:", data["created"],    value_color=W)
    print_row("Updated:", data["updated"],    value_color=W)
    print_row("Expires:", data["expires"],    value_color=W)
    print_row("DNSSEC:", data["dnssec"],
              value_color=(GR if data["dnssec"]=="Signed" else YL))
    print_row("Status:", data["status"],     value_color=GY)
    print()

    sep()
    print(f"  {W}[DNS & HOSTING]{R}"); print()
    if data["ip_addresses"]:
        for ip_a in data["ip_addresses"][:4]:
            print_row("Resolved IP:", ip_a, value_color=CY)
    print_row("Hosted Country:", data["ip_country"], value_color=W)
    print_row("ISP / Host:", data["ip_isp"],     value_color=W)
    if data["name_servers"]:
        for ns in data["name_servers"][:4]:
            print_row("Nameserver:", ns, value_color=W)
    print()

    if data["mx_records"]:
        sep()
        print(f"  {W}[MAIL SERVERS (MX)]{R}"); print()
        for mx in data["mx_records"]:
            print(f"  {GY}→{R}  {W}{mx}{R}")
        print()

    if data["txt_records"]:
        sep()
        print(f"  {W}[TXT RECORDS (SPF / DMARC)]{R}"); print()
        for tx in data["txt_records"][:4]:
            print(f"  {GY}> {R}  {GY}{tx}{R}")
        print()

    sep()
    print(f"  {W}[SSL CERTIFICATE]{R}"); print()
    print_row("Issuer:", data["ssl_issuer"], value_color=W)
    if data["ssl_expiry"] != "N/A":
        days = data.get("ssl_days_left")
        if days is not None:
            exp_col = GR if days > 30 else YL if days > 7 else RD
            print_row("Expires:", f"{data['ssl_expiry']}  ({days} days left)",
                      value_color=exp_col)
        else:
            print_row("Expires:", data["ssl_expiry"], value_color=W)
    else:
        print_row("SSL:", "Not available / no HTTPS", value_color=RD)
    print()

    if data["emails"]:
        sep()
        print(f"  {W}[CONTACT EMAILS]{R}"); print()
        for em in data["emails"][:5]:
            print(f"  {GY}@ {R}  {CY}{em}{R}")
        print()

    sep()
    print(f"  {W}[SUBDOMAIN SCAN  —  crt.sh]{R}"); print()
    if data["subdomains"]:
        print(f"  {GY}Found {GR}{len(data['subdomains'])}{GY} subdomains via SSL certificate logs:{R}"); print()
        cols = 3
        subs = data["subdomains"]
        for i in range(0, len(subs), cols):
            row = subs[i:i+cols]
            line = "  "
            for s in row:
                line += f"{GR}◦{R}  {W}{s:<36}{R}"
            print(line)
        if len(data["subdomains"]) == 40:
            print(f"\n  {YL}[!] 40-subdomain limit reached. Full list at:{R}")
            print(f"  {CY}https://crt.sh/?q=%.{domain}{R}")
    else:
        print(f"  {GY}No subdomains found.{R}")
        print(f"  {GY}(Domain may be new, or it may be using a wildcard certificate.){R}")
        print()
        print(f"  {GY}Manual check: {CY}https://crt.sh/?q=%.{domain}{R}")
    print()

    sep()
    print(f"  {GY}Sources: RDAP  /  ip-api.com  /  Google DNS-over-HTTPS  /  SSL socket  /  crt.sh{R}")
    sep(); pause()

def email_lookup():
    import hashlib

    clear(); sep()
    print(f"  {MG}{BLD}EMAIL LOOKUP  —  ACCOUNT & BREACH FINDER{R}"); sep(); print()
    print(f"  {GY}Checks which platforms have a registered account for this email.{R}")
    print(f"  {GY}Uses public APIs -- does not attempt login or access any account.{R}")
    print()
    print(f"  {W}Enter the email address to investigate:{R} ", end="", flush=True)
    email = input().strip()
    if not email: return

    email_lower    = email.lower().strip()
    email_hash_md5 = hashlib.md5(email_lower.encode()).hexdigest()

    results    = {}
    lock       = threading.Lock()
    scan_lines = []

    clear(); sep()
    print(f"  {MG}{BLD}SCANNING  /  {YL}{email}{R}"); sep(); print()

    def check_gravatar():
        try:
            r = SESSION.get(
                f"https://en.gravatar.com/{email_hash_md5}.json",
                timeout=TIMEOUT)
            if r.status_code == 200:
                d = r.json()
                entry = d.get("entry", [{}])[0] if d.get("entry") else {}
                username = entry.get("preferredUsername", entry.get("id", ""))
                display  = entry.get("displayName", "")
                profile  = f"https://en.gravatar.com/{email_hash_md5}"
                return {"found": True, "url": profile,
                        "data": {"username": username, "display": display}, "kind": "api"}
            return {"found": False, "url": "", "data": {}, "kind": "api"}
        except Exception:
            return {"found": None, "url": "", "data": {}, "kind": "error"}

    def check_github():
        try:
            r = SESSION.get(
                f"https://api.github.com/search/users?q={email_lower}+in:email",
                timeout=TIMEOUT,
                headers={"Accept": "application/vnd.github+json"})
            if r.status_code == 200:
                d = r.json()
                items = d.get("items", [])
                if items:
                    u = items[0]
                    return {"found": True,
                            "url": u.get("html_url", f"https://github.com/{u.get('login','')}"),
                            "data": {"login": u.get("login",""), "id": str(u.get("id",""))},
                            "kind": "api"}
            return {"found": False, "url": "", "data": {}, "kind": "api"}
        except Exception:
            return {"found": None, "url": "", "data": {}, "kind": "error"}

    def check_keybase():
        try:
            r = SESSION.get(
                f"https://keybase.io/_/api/1.0/user/lookup.json?email={email_lower}",
                timeout=TIMEOUT)
            if r.status_code == 200:
                d = r.json()
                them = d.get("them")
                if them:
                    if isinstance(them, list): them = them[0]
                    uname = them.get("basics", {}).get("username", "")
                    return {"found": True,
                            "url": f"https://keybase.io/{uname}",
                            "data": {"username": uname}, "kind": "api"}
            return {"found": False, "url": "", "data": {}, "kind": "api"}
        except Exception:
            return {"found": None, "url": "", "data": {}, "kind": "error"}

    def check_xon():
        try:
            r = SESSION.get(
                f"https://api.xposedornot.com/v1/breach-analytics?email={email_lower}",
                timeout=12)
            if r.status_code == 200:
                d = r.json()
                breaches = d.get("ExposedBreaches", {}).get("breaches_details", [])
                if breaches:
                    names = [b.get("breach", b.get("name","?")) for b in breaches]
                    return {"found": True, "url": "",
                            "data": {"breaches": names, "count": len(names)}, "kind": "breach"}
            return {"found": False, "url": "", "data": {}, "kind": "breach"}
        except Exception:
            return {"found": None, "url": "", "data": {}, "kind": "error"}

    checkers = {
        "Gravatar":              check_gravatar,
        "GitHub":                check_github,
        "Keybase":               check_keybase,
        "XposedOrNot (Breach)":  check_xon,
    }

    manual_platforms = {
        "Twitter / X":  "https://twitter.com/",
        "Instagram":    "https://www.instagram.com/",
        "Snapchat":     "https://www.snapchat.com/",
        "Google":       "https://accounts.google.com/",
        "Microsoft":    "https://login.microsoftonline.com/",
        "Adobe":        "https://account.adobe.com/",
        "Spotify":      "https://accounts.spotify.com/",
        "LinkedIn":     "https://www.linkedin.com/",
        "Dropbox":      "https://www.dropbox.com/login",
        "PayPal":       "https://www.paypal.com/",
    }

    def run_checker(name, fn):
        res = fn()
        with lock:
            results[name] = res
            f, knd = res["found"], res["kind"]
            if knd == "breach":
                if f is True:
                    cnt = res["data"].get("count", "?")
                    tag = f"{RD}[!]{R}"
                    lbl = f"{RD}{name:<30}{R} {cnt} breach(es) found"
                else:
                    tag = f"{GR}[OK]{R}"
                    lbl = f"{GY}{name:<30}{R} No breaches found"
            elif f is True:
                tag = f"{GR}[+]{R}"
                lbl = f"{GR}{name:<30}{R} {CY}{res['url']}{R}"
            elif f is False:
                tag = f"{RD}[-]{R}"
                lbl = f"{GY}{name:<30}{R} Not Found"
            else:
                tag = f"{YL}[~]{R}"
                lbl = f"{GY}{name:<30}{R} Timeout / Error"
            line = f"  {tag} {lbl}"
            scan_lines.append(line)
            print(line); sys.stdout.flush()

    threads = [threading.Thread(target=run_checker, args=(n, fn), daemon=True)
               for n, fn in checkers.items()]
    for th in threads: th.start()
    for th in threads: th.join()

    print()
    print(f"  {YL}[?]{R} {YL}{'Manual Verification Required':<30}{R} {GY}(password-reset / login check){R}")
    for name in manual_platforms:
        line = f"  {YL}[?]{R} {YL}{name:<30}{R} {GY}manual verification{R}"
        scan_lines.append(line)
        print(line)

    print(); sep()

    found_auto    = [n for n, r in results.items() if r["found"] is True]
    found_breach  = [n for n, r in results.items() if r.get("kind") == "breach" and r["found"] is True]
    not_found     = [n for n, r in results.items() if r["found"] is False]

    conf_str = ("HIGH"   if len(found_auto) >= 3 else
                "MEDIUM" if len(found_auto) >= 1 else "LOW")
    conf_col = (GR if conf_str == "HIGH" else YL if conf_str == "MEDIUM" else RD)

    print()
    sep()
    print(f"  {W}[OPEN SOURCE INFORMATION]{R}"); print()
    print_row("Email:", email, value_color=YL)
    print_row("Platforms Found:", str(len(found_auto)), value_color=GR)
    print_row("Breach Exposure:", str(len(found_breach)) + " source(s)",
              value_color=(RD if found_breach else GR))
    print_row("Manual Check:", str(len(manual_platforms)), value_color=YL)
    print_row("Confidence:", conf_str, value_color=conf_col)
    print()

    if found_auto:
        sep()
        print(f"  {W}[FOUND ACCOUNTS]{R}"); print()
        for n in found_auto:
            res = results[n]
            knd = res.get("kind","")
            if knd == "breach":
                bnames = res["data"].get("breaches", [])
                print(f"  {RD}[!]  {BLD}{n}{R}")
                for b in bnames[:6]:
                    print(f"  {GY}       - {RD}{b}{R}")
            else:
                print(f"  {GR}  {BLD}{n}{R}")
                if res.get("url"):
                    print(f"  {GY}     {CY}{res['url']}{R}")
                d = res.get("data", {})
                if d.get("login"):    print(f"  {GY}    Username   {W}{d['login']}{R}")
                if d.get("username"): print(f"  {GY}    Username   {W}{d['username']}{R}")
                if d.get("display"):  print(f"  {GY}    Display    {W}{d['display']}{R}")
            print()

    sep()
    print(f"  {W}[MANUAL CHECK LINKS]{R}")
    print(f"  {GY}Use password-reset on these platforms to verify email registration.{R}"); print()
    for name, url in manual_platforms.items():
        print(f"  {YL}{R}  {W}{name:<16}{R}  {CY}{url}{R}")

    print(); sep()
    print(f"  {GY}Sources: Gravatar / GitHub API / Keybase / XposedOrNot{R}")
    print(f"  {GY}Note: Account existence does not equal ownership. Results are indicative only.{R}")
    sep(); pause()

def main():
    if sys.platform == "win32":
        try: os.system("chcp 65001 > nul")
        except Exception: pass

    login_screen()

    while True:
        choice = main_menu()
        if   choice == "1": spy_command()
        elif choice == "2": pwn_check()
        elif choice == "3": phone_lookup()
        elif choice == "4": ip_lookup()
        elif choice == "5": domain_lookup()
        elif choice == "6": email_lookup()
        elif choice == "0":
            clear()
            print(f"\n  {GY}Session terminated.{R}\n")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {GY}Interrupted.{R}\n")
        sys.exit(0)