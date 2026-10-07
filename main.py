#!/usr/bin/env python3
import re
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://cigaedu22.github.io/g{g}/class-{c}/"
G_START, G_END = 5, 100
CLASS_START, CLASS_END = 1, 1000
WORKERS = 20
TIMEOUT = 10
SAVE_EVERY = 25

OUTPUT_FILE = Path("gefunden.txt")
PARTIAL_FILE = Path("gefunden_partial.txt")
USER_AGENT = "Mozilla/5.0 (compatible; PublicPageChecker/1.0)"

stop_requested = False

def handle_signal(signum, frame):
    global stop_requested
    if not stop_requested:
        print("\n[!] Abbruch angefordert. Aktueller Stand wird gespeichert...")
        stop_requested = True
    else:
        sys.exit(1)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def extract_title(html):
    m = re.search(r"<title\b[^>]*>(.*?)</title\s*>", html, re.I | re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()

def check_page(g, c):
    url = BASE_URL.format(g=g, c=c)
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urlopen(req, timeout=TIMEOUT) as response:
            if not 200 <= response.status < 300:
                return None
            data = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            html = data.decode(charset, errors="replace")
            return {"g": g, "class": c, "url": url, "title": extract_title(html)}
    except (HTTPError, URLError, TimeoutError, ConnectionError):
        return None
    except Exception:
        return None

def save_results(results):
    results = sorted(results, key=lambda x: (x["g"], x["class"]))
    content = "".join(
        f'g{x["g"]}/class-{x["class"]} | {x["title"] or "(kein Titel)"} | {x["url"]}\n'
        for x in results
    )
    for path in (PARTIAL_FILE, OUTPUT_FILE):
        tmp = path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)

def load_previous_results():
    results = []
    if not PARTIAL_FILE.exists():
        return results
    try:
        for line in PARTIAL_FILE.read_text(encoding="utf-8").splitlines():
            parts = line.split(" | ", 2)
            if len(parts) != 3:
                continue
            path, title, url = parts
            m = re.fullmatch(r"g(\d+)/class-(\d+)", path)
            if m:
                results.append({
                    "g": int(m.group(1)),
                    "class": int(m.group(2)),
                    "title": "" if title == "(kein Titel)" else title,
                    "url": url,
                })
    except OSError:
        pass
    return results

def main():
    global stop_requested
    total = (G_END-G_START+1) * (CLASS_END-CLASS_START+1)
    results = load_previous_results()
    existing = {(x["g"], x["class"]) for x in results}
    jobs = [
        (g, c)
        for g in range(G_START, G_END+1)
        for c in range(CLASS_START, CLASS_END+1)
        if (g, c) not in existing
    ]

    print(f"Prüfe bis zu {total:,} URLs mit {WORKERS} parallelen Verbindungen.")
    print(f"Schema: {BASE_URL}")
    print("Nur HTTP-Existenz + <title>; keine iframe/embed-Suche.")
    print("Ctrl+C speichert den bisherigen Stand und beendet den Scan.")

    completed = 0
    since_save = 0
    executor = ThreadPoolExecutor(max_workers=WORKERS)
    futures = {executor.submit(check_page, g, c): (g, c) for g, c in jobs}

    try:
        for future in as_completed(futures):
            if stop_requested:
                break
            g, c = futures[future]
            completed += 1
            result = future.result()
            if result:
                results.append(result)
                since_save += 1
                print(f'[FOUND] g{g}/class-{c} | {result["title"] or "(kein Titel)"} | {result["url"]}')
            if completed % 100 == 0:
                print(f"[...] {completed:,}/{len(jobs):,} geprüft | {len(results):,} Treffer")
            if since_save >= SAVE_EVERY:
                save_results(results)
                since_save = 0
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
        save_results(results)
        print(f"\nFertig/abgebrochen. Treffer: {len(results):,}")
        print(f"Liste: {OUTPUT_FILE}")
        print(f"Fortsetzung: {PARTIAL_FILE}")

if __name__ == "__main__":
    main()
