"""Builds the submission package: decks (PDF, PPTX, PNG) and narrated MP4s.

Needs: a running app (uvicorn supplylens.app:app --port 8765), Google Chrome, Windows (SAPI voices),
and `pip install python-pptx pillow imageio-ffmpeg`.
Run from the repo root: python submission/build.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image
from pptx import Presentation
from pptx.util import Emu

sys.path.insert(0, str(Path(__file__).parent))
from content import DEMO, IDEA, PROTO  # noqa: E402

OUT = Path(__file__).parent
ASSETS = OUT / "assets"
BASE = os.environ.get("SUPPLYLENS_URL", "http://localhost:8765/")
CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
TMP = Path(tempfile.mkdtemp(prefix="supplylens-build-"))

# (asset name, app route, window height, crop box at 1440 px width)
SHOTS = [
    ("raw", "#raw", 1500, (100, 140, 1340, 1040)),
    ("hotel_top", "#search?v=hotels&q=marina%20hotel%20with%20breakfast%2C%20free%20cancellation", 3600, (100, 740, 1340, 1480)),
    ("hotel_detail", "#search?v=hotels&q=marina%20hotel%20with%20breakfast%2C%20free%20cancellation", 3600, (660, 760, 1340, 1490)),
    ("hotel_rooms", "#search?v=hotels&q=marina%20hotel%20with%20breakfast%2C%20free%20cancellation", 3600, (660, 1480, 1340, 2100)),
    ("hotel_offers", "#search?v=hotels&q=marina%20hotel%20with%20breakfast%2C%20free%20cancellation", 3600, (660, 2090, 1340, 2800)),
    ("exp_top", "#search?v=experiences&q=evening%20activity%20with%20hotel%20pickup%20and%20flexible%20cancellation&open=A-X11", 2100, (100, 740, 1340, 1600)),
    ("exp_detail", "#search?v=experiences&q=evening%20activity%20with%20hotel%20pickup%20and%20flexible%20cancellation&open=A-X11", 2100, (660, 760, 1340, 1790)),
    ("cruise", "#search?v=experiences&q=dinner%20cruise", 1700, (100, 740, 1340, 1600)),
    ("review", "#review", 1150, (100, 340, 1340, 950)),
    ("evidence", "#evidence", 2200, (100, 400, 1340, 1300)),
]

CSS = """
:root{--canvas:#f0eee6;--card:#faf9f5;--feature:#f5e3c7;--panel:#e3dacc;--ink:#141413;--soft:#5e5d59;--line:#cccbc8;--clay:#d97757;
--serif:'Source Serif 4',Georgia,serif;--sans:Inter,'Segoe UI',Arial,sans-serif;--mono:'JetBrains Mono',Consolas,monospace}
@page{size:1920px 1080px;margin:0}
*{box-sizing:border-box}html,body{margin:0;background:var(--canvas);color:var(--ink)}
.slide{width:1920px;height:1080px;padding:84px 120px 72px;position:relative;overflow:hidden;page-break-after:always;font:400 28px/1.4 var(--serif);display:flex;flex-direction:column;gap:28px}
.slide .top{position:absolute;top:36px;left:120px;right:120px;display:flex;justify-content:space-between;font:700 15px/1 var(--sans);letter-spacing:.16em;text-transform:uppercase}
.kicker{font:700 18px/1.3 var(--sans);letter-spacing:.14em;text-transform:uppercase;margin:0}
h1{font:700 60px/1.08 var(--sans);margin:0;letter-spacing:-.002em}
h1.display{font:400 150px/1 var(--serif)}
h3{font:600 28px/1.2 var(--sans);margin:0 0 8px}
.lead{font:400 40px/1.3 var(--serif);max-width:1400px;margin:0}
.mono{font:400 24px/1.4 var(--mono);margin:0}
.cover{background:var(--feature);border-radius:24px;flex:1;padding:96px 110px;display:flex;flex-direction:column;justify-content:center;gap:36px}
.card{background:var(--card);border-radius:24px;padding:28px 32px}
.k{font:700 15px/1.3 var(--sans);letter-spacing:.14em;text-transform:uppercase;margin:0 0 10px}
.card p{margin:0}.card ul,.card ol{margin:0;padding-left:26px}.card li{margin:4px 0}
.cols3{display:grid;grid-template-columns:1fr 1.6fr 1fr;gap:12px;flex:1;font-size:23px}
.cols3.tight{grid-template-columns:1fr 1fr 1fr;flex:0}
.cols2{display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1;font-size:24px}
.layers{display:flex;align-items:stretch;gap:10px;font-size:20px}
.layers.small{margin-top:12px}
.layer{flex:1;background:var(--panel);border-radius:16px;padding:18px 20px}
.layer h3{font-size:22px}.layer .k{font-size:12px}
.arrow{font:700 34px/1 var(--sans);align-self:center}
.flow{display:flex;gap:10px}.step{flex:1;background:var(--feature);border-radius:0 0 12px 12px;padding:18px 18px;font-size:19px;display:flex;flex-direction:column;gap:6px}
.step b{font:700 20px/1.2 var(--sans)}
table{width:100%;border-collapse:collapse;font:400 21px/1.35 var(--sans)}td,th{border-bottom:1px solid var(--line);padding:9px 10px 9px 0;text-align:left;vertical-align:top}
th{font-weight:600}table.num td:not(:first-child),table.num th:not(:first-child){text-align:center}
.note{font:400 17px/1.4 var(--sans);color:var(--soft);margin-top:14px!important}
.split{display:grid;grid-template-columns:.85fr 1.15fr;gap:48px;flex:1;align-items:start}
.split h1{margin-bottom:28px}
ul.big{padding-left:28px;margin:0;font-size:29px}ul.big li{margin:10px 0}
.screen{background:var(--card);border-radius:20px;border:1px solid var(--line);padding:14px;display:flex;justify-content:center;align-items:flex-start;overflow:hidden}
.split .screen{max-height:800px}.split .screen img{max-width:100%;max-height:770px;object-fit:contain}
.full{flex:1;display:flex;flex-direction:column;gap:14px;min-height:0}.full .screen{flex:none;height:850px}.full .screen img{height:100%;width:auto;max-width:100%;object-fit:contain}
.cap{font:600 22px/1.3 var(--sans);margin:0}
.shot{margin:0;display:flex;flex-direction:column;gap:14px;min-height:0}.full .shot{flex:1}
.ask{font-size:30px;margin:0;background:var(--feature);border-radius:0 0 12px 12px;padding:18px 26px}
.foot{position:absolute;bottom:28px;left:120px;right:120px;font:400 14px/1 var(--sans);color:var(--soft);display:flex;justify-content:space-between}
"""
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">'


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def chrome(*args):
    run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
         "--virtual-time-budget=8000", "--allow-file-access-from-files", *args])


def capture_assets():
    ASSETS.mkdir(exist_ok=True)
    cache = {}
    for name, route, h, box in SHOTS:
        key = (route, h)
        if key not in cache:
            p = TMP / f"full{len(cache)}.png"
            chrome(f"--window-size=1440,{h}", f"--screenshot={p}", BASE + route)
            cache[key] = p
        Image.open(cache[key]).crop(box).save(ASSETS / f"{name}.png")


def slide_html(s, n, total, deck_name):
    if s["layout"] == "cover":
        body = f'<div class="cover">{s["html"]}</div>'
    elif s["layout"] == "full":
        body = f'<div class="full">{s["html"]}</div>'
    elif s["layout"] == "split":
        body = f'<p class="kicker">{s["kicker"]}</p><div class="split">{s["html"]}</div>'
    else:
        body = f'<p class="kicker">{s["kicker"]}</p>{s["html"]}'
    top = f'<div class="top"><span>AlphaFire · SupplyLens</span><span>{n} / {total}</span></div>'
    foot = f'<div class="foot"><span>{deck_name}</span><span>Synthetic data. All suppliers, prices and availability are fictional.</span></div>'
    return f'<section class="slide">{top}{body}{foot}</section>'


def render_deck(slides, stem, deck_name):
    total = len(slides)
    pages = [slide_html(s, i + 1, total, deck_name) for i, s in enumerate(slides)]
    head = f'<!DOCTYPE html><html><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head><body>'
    full = OUT / f"_{stem}.html"
    full.write_text(head + "".join(pages) + "</body></html>", encoding="utf-8")
    pngs = []
    for i, page in enumerate(pages):
        single = OUT / f"_{stem}_{i + 1}.html"
        single.write_text(head + page + "</body></html>", encoding="utf-8")
        png = TMP / f"{stem}_{i + 1:02d}.png"
        chrome("--window-size=1920,1080", f"--screenshot={png}", single.as_uri())
        single.unlink()
        pngs.append(png)
    chrome("--no-pdf-header-footer", f"--print-to-pdf={OUT / (stem + '.pdf')}", full.as_uri())
    full.unlink()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    for png, s in zip(pngs, slides):
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        sl.shapes.add_picture(str(png), 0, 0, prs.slide_width, prs.slide_height)
        sl.notes_slide.notes_text_frame.text = s["say"]
    prs.save(OUT / f"{stem}.pptx")
    return pngs


def tts(text, wav, voice="Microsoft Zira Desktop", rate=0):
    ps = ("Add-Type -AssemblyName System.Speech;$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
          f"$s.SelectVoice('{voice}');$s.Rate={rate};$s.SetOutputToWaveFile('{wav}');"
          f"$s.Speak([IO.File]::ReadAllText('{wav}.txt'));$s.Dispose()")
    Path(f"{wav}.txt").write_text(text, encoding="utf-8")
    run(["powershell", "-NoProfile", "-Command", ps])


def make_video(pngs, slides, out):
    parts = []
    for i, (png, s) in enumerate(zip(pngs, slides)):
        wav = TMP / f"{out.stem}_{i}.wav"
        tts(s["say"], str(wav))
        seg = TMP / f"{out.stem}_{i}.mp4"
        # still frame for the narration plus 0.6 s of padding at the end
        run([FFMPEG, "-y", "-loop", "1", "-i", str(png), "-i", str(wav), "-af", "apad=pad_dur=0.6",
             "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30", "-vf", "scale=1920:1080",
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", str(seg)])
        parts.append(seg)
    lst = TMP / f"{out.stem}.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)])


if __name__ == "__main__":
    capture_assets()
    idea = render_deck(IDEA, "AlphaFire_MultiSupplier_Idea_v1", "Idea submission · VoyageHack 4.0")
    proto = render_deck(PROTO, "AlphaFire_MultiSupplier_Prototype_v1", "Prototype submission · VoyageHack 4.0")
    demo = render_deck(DEMO, "_demo_frames", "Prototype walkthrough")
    for f in OUT.glob("_demo_frames.*"):
        f.unlink()  # frames only feed the video
    make_video(idea, IDEA, OUT / "AlphaFire_MultiSupplier_IdeaPitch_v1.mp4")
    make_video(demo, DEMO, OUT / "AlphaFire_MultiSupplier_Demo_v1.mp4")
    print("built in", OUT)
