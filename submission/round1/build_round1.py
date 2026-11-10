"""Round 1 (idea submission) builder: editable PPTX -> PDF, plus a narrated MP4 exported by PowerPoint.

Requires Windows with Microsoft PowerPoint, and: pip install python-pptx pywin32 edge-tts imageio-ffmpeg
Run: python submission/round1/build_round1.py
"""
import asyncio
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import win32com.client
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).resolve().parent
STEM = "AlphaFire_MultiSupplier_Idea_v2"
VOICE = "en-IN-NeerjaNeural"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

CANVAS, CARD, FEATURE, PANEL = "F0EEE6", "FAF9F5", "F5E3C7", "E3DACC"
INK, SOFT, LINE, CLAY = "141413", "5E5D59", "CCCBC8", "D97757"
SANS, SANS_B, SERIF = "Segoe UI", "Segoe UI Semibold", "Georgia"


def rgb(h):
    return RGBColor.from_string(h)


# ------------------------------------------------------------------ drawing helpers
def box(sl, x, y, w, h, fill, radius=0.08, name=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None):
    s = sl.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(0.75)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    s.text_frame.text = ""
    return s


def text(sl, x, y, w, h, paras, name=None, anchor=MSO_ANCHOR.TOP, shape=None):
    """paras: list of dicts {t, size, font, color, bold, bullet, after, align, italic}"""
    tb = shape or sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(0))
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        para.space_after = Pt(p.get("after", 6))
        para.line_spacing = p.get("spacing", 1.08)
        runs = p["t"] if isinstance(p["t"], list) else [(p["t"], {})]
        for chunk, over in runs:
            r = para.add_run()
            r.text = chunk
            f = r.font
            f.size = Pt(over.get("size", p.get("size", 14)))
            f.name = over.get("font", p.get("font", SERIF))
            f.bold = over.get("bold", p.get("bold", False))
            f.italic = over.get("italic", p.get("italic", False))
            f.color.rgb = rgb(over.get("color", p.get("color", INK)))
        if p.get("bullet"):
            pPr = para._p.get_or_add_pPr()
            pPr.set("marL", str(Inches(0.2)))
            pPr.set("indent", str(-Inches(0.2)))
            for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
                for el in pPr.findall(qn(tag)):
                    pPr.remove(el)
            bf = pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"})
            bc = pPr.makeelement(qn("a:buChar"), {"char": "•"})
            pPr.append(bf)
            pPr.append(bc)
    return tb


def kicker(t, size=10.5, color=INK):
    return {"t": t.upper(), "size": size, "font": SANS_B, "color": color, "after": 4}


def arrow(sl, x1, y1, x2, y2, name=None, color=INK, width=1.75):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    no_effects(c)
    if name:
        c.name = name
    return c


def no_effects(shape):
    """Drop the theme's default shadow from connectors."""
    spPr = shape._element.spPr
    if spPr.find(qn("a:effectLst")) is None:
        spPr.append(spPr.makeelement(qn("a:effectLst"), {}))


def frame(sl, n, total):
    bg = sl.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(CANVAS)
    text(sl, 0.6, 0.32, 6, 0.3, [{"t": "SUPPLYLENS  ·  TEAM ALPHAFIRE", "size": 9, "font": SANS_B, "color": SOFT}], name="chrome_l")
    text(sl, 10.2, 0.32, 2.53, 0.3, [{"t": f"{n} / {total}", "size": 9, "font": SANS_B, "color": SOFT, "align": PP_ALIGN.RIGHT}], name="chrome_r")
    text(sl, 0.6, 7.08, 12.13, 0.25, [{"t": "TBO VoyageHack 4.0  ·  Round 1: Idea Submission  ·  Multi Supplier Optimization", "size": 8.5, "font": SANS, "color": SOFT}], name="chrome_f")


# ------------------------------------------------------------------ slides
def cover(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    frame(sl, 1, 4)
    box(sl, 0.6, 0.85, 12.13, 6.0, FEATURE, 0.05, name="g0_bg")
    text(sl, 1.15, 1.45, 6.2, 4.8, [
        kicker("TBO VoyageHack 4.0  ·  Multi Supplier Optimization", 11),
        {"t": "SupplyLens", "size": 64, "font": SERIF, "after": 10, "spacing": 1.0},
    ], name="g1_title")
    text(sl, 1.15, 3.35, 5.7, 1.6, [
        {"t": "Every supplier. One clear listing.", "size": 26, "font": SANS_B, "after": 10},
        {"t": "Hotel and sightseeing inventory from many suppliers, matched into one trustworthy listing per product, without losing the differences travellers care about.", "size": 15.5, "color": INK, "spacing": 1.15},
    ], name="g2_tag")
    text(sl, 1.15, 5.75, 6, 0.8, [
        {"t": "Team AlphaFire", "size": 15, "font": SANS_B, "after": 2},
        {"t": "Problem statement: Multi Supplier Optimization (Hotels and Sightseeing)", "size": 11.5, "font": SANS, "color": SOFT},
    ], name="g4_team")
    # illustration: three supplier listings -> one listing
    names = [("Supplier A", "Marina Pearl Hotel"), ("Supplier B", "Marina Pearl Htl & Spa"), ("Supplier C", "The Marina Pearl")]
    for i, (s, n) in enumerate(names):
        y = 1.55 + i * 0.98
        b = box(sl, 7.55, y, 2.35, 0.78, CARD, 0.14, name=f"g3_sup{i}")
        text(sl, 0, 0, 0, 0, [{"t": s.upper(), "size": 8, "font": SANS_B, "color": SOFT, "after": 1},
                              {"t": n, "size": 12, "font": SERIF}], shape=b, anchor=MSO_ANCHOR.MIDDLE)
        b.text_frame.margin_left = Inches(0.16)
        arrow(sl, 9.95, y + 0.39, 10.35, 2.94, name=f"g3_arr{i}", color=SOFT, width=1.25)
    card = box(sl, 10.4, 1.95, 1.95, 2.0, INK, 0.1, name="g3_one")
    text(sl, 0, 0, 0, 0, [
        {"t": "ONE LISTING", "size": 8, "font": SANS_B, "color": PANEL, "after": 3},
        {"t": "Marina Pearl Hotel", "size": 13, "font": SERIF, "color": CARD, "after": 6},
        {"t": "3 suppliers", "size": 10, "font": SANS, "color": CARD, "after": 0},
        {"t": "4 room types kept", "size": 10, "font": SANS, "color": CARD, "after": 0},
        {"t": "Best bookable offer", "size": 10, "font": SANS, "color": CARD, "after": 0},
    ], shape=card, anchor=MSO_ANCHOR.MIDDLE)
    card.text_frame.margin_left = Inches(0.16)
    text(sl, 7.55, 4.55, 4.8, 0.3, [{"t": "Illustrative example", "size": 9, "font": SANS, "color": SOFT}], name="g3_note")
    return sl


def content1(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    frame(sl, 2, 4)
    text(sl, 0.6, 0.72, 12.1, 1.2, [
        kicker("Content 1 of 2  ·  Potential Impact  ·  Innovation", 10.5, SOFT),
        {"t": "One trustworthy listing per product, with every real difference kept.", "size": 28, "font": SANS_B, "spacing": 1.0},
    ], name="g1_title")

    # column 1: problem
    b = box(sl, 0.6, 1.95, 3.85, 4.95, CARD, 0.05, name="g2_problem")
    text(sl, 0.85, 2.2, 3.4, 4.6, [
        kicker("The problem today"),
        {"t": "Duplicates crowd the page", "size": 15, "font": SANS_B, "after": 3},
        {"t": "The same hotel arrives from several suppliers under different names.", "size": 13.5, "after": 18, "spacing": 1.15},
        {"t": "Naive merging hides real differences", "size": 15, "font": SANS_B, "after": 3},
        {"t": "Pickup vs self-transfer, twin vs king, refundable vs non-refundable.", "size": 13.5, "after": 18, "spacing": 1.15},
        {"t": "The cheapest price can be misleading", "size": 15, "font": SANS_B, "after": 3},
        {"t": "Taxes excluded, stale, or no refund at all, yet it ranks first.", "size": 13.5, "after": 18, "spacing": 1.15},
    ], name="g2_problem_t")

    # column 2: model
    box(sl, 4.6, 1.95, 4.4, 4.95, CARD, 0.05, name="g3_model")
    text(sl, 4.85, 2.2, 4.0, 0.4, [kicker("How SupplyLens sees inventory")], name="g3_k")
    rows = [
        ("ENTITY", "The same hotel or experience", "3 supplier listings  →  Marina Pearl Hotel"),
        ("VARIANTS", "Room types, transfers, meals, access", "King 32 m² = King 344 sq ft  ·  Twin kept apart"),
        ("OFFERS", "Price, availability, cancellation", "AED 1,720 with breakfast, free cancellation ✓\nAED 1,580 without taxes: not comparable"),
    ]
    for i, (k, d, ex) in enumerate(rows):
        y = 2.68 + i * 1.38
        r = box(sl, 4.85, y, 3.9, 1.12, PANEL, 0.1, name=f"g3_row{i}")
        text(sl, 0, 0, 0, 0, [
            {"t": [(k + "   ", {"font": SANS_B, "size": 9.5}), (d, {"font": SANS_B, "size": 11})], "after": 3},
            {"t": ex, "size": 11, "spacing": 1.05, "after": 0},
        ], shape=r, anchor=MSO_ANCHOR.MIDDLE)
        r.text_frame.margin_left = Inches(0.16)
        r.text_frame.margin_right = Inches(0.1)
        if i < 2:
            arrow(sl, 6.8, y + 1.13, 6.8, y + 1.37, name=f"g3_a{i}", color=SOFT, width=1.25)

    # column 3: impact + innovation
    box(sl, 9.15, 1.95, 3.58, 2.55, FEATURE, 0.07, name="g4_impact")
    text(sl, 9.4, 2.18, 3.15, 2.3, [
        kicker("Potential impact"),
        {"t": "Cleaner listing pages: one card per product", "size": 12.5, "bullet": True, "after": 4},
        {"t": "Best bookable price surfaced: stronger price competitiveness", "size": 12.5, "bullet": True, "after": 4},
        {"t": "Fewer post-booking surprises: higher booking conversion", "size": 12.5, "bullet": True, "after": 4},
    ], name="g4_impact_t")
    box(sl, 9.15, 4.6, 3.58, 2.3, CARD, 0.07, name="g5_innov")
    text(sl, 9.4, 4.83, 3.15, 2.05, [
        kicker("Innovation"),
        {"t": "Variant-safe matching, not name-only deduplication", "size": 12.5, "bullet": True, "after": 4},
        {"t": "Best eligible offer, not lowest headline price", "size": 12.5, "bullet": True, "after": 4},
        {"t": "A visible reason for every decision; unsure cases go to review", "size": 12.5, "bullet": True, "after": 4},
    ], name="g5_innov_t")
    return sl


def content2(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    frame(sl, 3, 4)
    text(sl, 0.6, 0.72, 12.1, 1.2, [
        kicker("Content 2 of 2  ·  Implementation & Technical Feasibility  ·  Adoption Risk / Feasibility", 10.5, SOFT),
        {"t": "A simple, explainable pipeline that TBO can pilot safely.", "size": 28, "font": SANS_B, "spacing": 1.0},
    ], name="g1_title")
    steps = [("1  Normalize", "Names, units, addresses, currency. Source of every field kept."),
             ("2  Match", "Same / different / needs review. Hard conflicts block merges."),
             ("3  Map variants", "Rooms by occupancy, bed, size and view. Tours by inclusions."),
             ("4  Compare offers", "Only complete, available prices with the required policy."),
             ("5  Rank & explain", "Relevance first, then value, flexibility, freshness, reliability.")]
    w, gap, x0 = 2.37, 0.07, 0.6
    for i, (h, d) in enumerate(steps):
        c = box(sl, x0 + i * (w + gap), 1.92, w, 1.45, FEATURE if i % 2 == 0 else PANEL, 0, name=f"g2_step{i}",
                shape=MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON)
        c.adjustments[0] = 0.18
        text(sl, x0 + i * (w + gap) + (0.42 if i else 0.2), 2.04, w - 0.75, 1.25, [
            {"t": h, "size": 13, "font": SANS_B, "after": 3},
            {"t": d, "size": 10.5, "spacing": 1.05, "after": 0},
        ], name=f"g2_stept{i}", anchor=MSO_ANCHOR.MIDDLE)

    box(sl, 0.6, 3.6, 5.6, 3.3, CARD, 0.06, name="g3_feas")
    text(sl, 0.85, 3.82, 5.15, 3.0, [
        kicker("Technical feasibility"),
        {"t": "Python + FastAPI service; no heavy infrastructure, millisecond searches", "size": 12.5, "bullet": True, "after": 3},
        {"t": "Rules plus similarity on fields suppliers already send; no model training or GPUs", "size": 12.5, "bullet": True, "after": 3},
        {"t": "Runs before the listing page as a sidecar to existing search", "size": 12.5, "bullet": True, "after": 10},
        kicker("How we will prove it (per vertical)"),
        {"t": "Match precision and a harmful-merge test suite, offer-correctness checks, and ranking quality (NDCG) against raw-feed and cheapest-price baselines.", "size": 12.5, "spacing": 1.12, "after": 0},
    ], name="g3_feas_t")

    box(sl, 6.35, 3.6, 6.38, 3.3, CARD, 0.06, name="g4_risk")
    text(sl, 6.6, 3.82, 5.9, 0.35, [kicker("Adoption risk  →  mitigation")], name="g4_k")
    risks = [("Wrong merges", "Conflicts block auto-merge; unsure pairs go to a reversible review queue"),
             ("Missing or conflicting data", "Shown as unknown with its source, never assumed"),
             ("Stale or partial prices", "Excluded from “best offer”, with the reason shown"),
             ("Integration effort", "Offline run on TBO sample feeds, then a controlled pilot")]
    for i, (r, m) in enumerate(risks):
        y = 4.25 + i * 0.64
        text(sl, 6.6, y, 1.95, 0.6, [{"t": r, "size": 12, "font": SANS_B, "spacing": 1.0}], name=f"g4_r{i}")
        text(sl, 8.6, y, 3.95, 0.6, [{"t": m, "size": 12, "spacing": 1.05}], name=f"g4_m{i}")
        if i:
            ln = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(6.6), Inches(y - 0.07), Inches(12.5), Inches(y - 0.07))
            ln.line.color.rgb = rgb(LINE)
            ln.line.width = Pt(0.75)
            no_effects(ln)
            ln.name = f"g4_l{i}"
    return sl


def thanks(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    frame(sl, 4, 4)
    box(sl, 0.6, 0.85, 12.13, 6.0, INK, 0.05, name="g0_bg")
    text(sl, 1.15, 2.0, 11, 2.5, [
        kicker("Team AlphaFire  ·  SupplyLens", 11, PANEL),
        {"t": "Thank you.", "size": 64, "font": SERIF, "color": CARD, "after": 14, "spacing": 1.0},
        {"t": "Every supplier. One clear listing.", "size": 22, "font": SANS_B, "color": CARD},
    ], name="g1_thanks")
    text(sl, 1.15, 5.3, 11, 1.0, [
        {"t": "Code & documentation:  github.com/gurlivsingh/supplylens", "size": 13, "font": SANS, "color": PANEL, "after": 4},
        {"t": "Live demo:  supplylens-alphafire.onrender.com", "size": 13, "font": SANS, "color": PANEL},
    ], name="g2_links")
    return sl


# ------------------------------------------------------------------ narration (one list entry per reveal group g1..gN)
SCRIPT = [
    ["Hi, we're Team AlphaFire. This is SupplyLens, our idea for TBO's Multi Supplier Optimization challenge.",
     "It turns hotel and sightseeing inventory from many suppliers into one clear, trustworthy listing per product.",
     "For example, three suppliers sell the same hotel under three different names. SupplyLens shows it once, keeps all its room types, and points to the best offer you can actually book.",
     "Here's why that matters."],
    ["Today, there are three problems.",
     "Duplicates crowd the listing page. Naive merging hides real differences, like hotel pickup versus self-transfer, or a twin room versus a king. And the cheapest headline price can exclude taxes, or have no refund at all.",
     "SupplyLens separates three things. The entity: the same hotel or experience. Its variants: room types, transfers, meals and access. And the offers: each supplier's price and policy. Duplicates collapse, and real differences stay visible.",
     "The impact is cleaner listings, the best bookable price surfaced, and fewer surprises after booking, which lifts conversion.",
     "The innovation is variant-safe matching, the best eligible offer instead of the lowest headline price, and a visible reason for every decision, with unsure cases sent to a reviewer."],
    ["So, how do we build it?",
     "In five steps. Normalize supplier data and keep its source. Match records as the same, different, or needs review. Map room and activity variants. Compare only complete, eligible offers. And rank results with clear reasons.",
     "It's light to run: Python and FastAPI, rules plus similarity on fields suppliers already send, no model training, and searches in milliseconds. We'll prove it for each vertical with match precision, harmful-merge tests, and ranking against cheapest-price baselines.",
     "Adoption risk is covered too. Wrong merges go to a reversible review queue, missing data stays visibly unknown, stale prices can never win, and integration starts offline on TBO sample feeds, before a controlled pilot."],
    ["SupplyLens. Every supplier, one clear listing.",
     "Thank you, from Team AlphaFire."],
]


def build_pptx(path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for f in (cover, content1, content2, thanks):
        f(prs)
    for sl, lines in zip(prs.slides, SCRIPT):
        sl.notes_slide.notes_text_frame.text = " ".join(lines)
    prs.save(path)


# ------------------------------------------------------------------ narration audio
async def _tts(t, path):
    await edge_tts.Communicate(t, VOICE, rate="+2%").save(str(path))


def duration(path):
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = out.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def narrate(tmp):
    """Returns per slide: (wav path, [start time of each reveal group], total seconds)."""
    slides = []
    for si, lines in enumerate(SCRIPT):
        parts, starts, t = [], [], 0.6  # short lead-in after the transition
        for gi, line in enumerate(lines):
            mp3 = tmp / f"s{si}_{gi}.mp3"
            asyncio.run(_tts(line, mp3))
            starts.append(t)
            parts.append(mp3)
            t += duration(mp3) + 0.25
        wav = tmp / f"slide{si}.wav"
        inputs = sum((["-i", str(p)] for p in parts), [])
        pads = "".join(f"[{i}:a]apad=pad_dur=0.25[p{i}];" for i in range(len(parts)))
        cat = "".join(f"[p{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[c];[c]adelay=600:all=1[o]"
        subprocess.run([FFMPEG, "-y", *inputs, "-filter_complex", pads + cat, "-map", "[o]", "-ar", "44100", "-ac", "1", str(wav)],
                       check=True, capture_output=True)
        slides.append((wav, starts, duration(wav)))
    return slides


# ------------------------------------------------------------------ PowerPoint export
def export(pptx, narration):
    app = win32com.client.Dispatch("PowerPoint.Application")
    pdf = OUT / f"{STEM}.pdf"
    mp4 = OUT / "AlphaFire_MultiSupplier_IdeaPitch_v2.mp4"
    pres = app.Presentations.Open(str(pptx), WithWindow=False)
    pres.SaveAs(str(pdf), 32)  # ppSaveAsPDF
    for i in range(1, pres.Slides.Count + 1):
        pres.Slides(i).Export(str(OUT / "preview" / f"slide{i}.png"), "PNG", 1920, 1080)
    pres.Close()

    video_pptx = Path(tempfile.gettempdir()) / f"{STEM}_video.pptx"
    shutil.copy(pptx, video_pptx)
    pres = app.Presentations.Open(str(video_pptx), WithWindow=False)
    for i, (wav, starts, total) in enumerate(narration, start=1):
        sl = pres.Slides(i)
        seq = sl.TimeLine.MainSequence
        # reveal groups: shapes named gN_* fade in when narration reaches line N (g0 = always visible)
        groups = {}
        for s in range(1, sl.Shapes.Count + 1):
            shp = sl.Shapes(s)
            if shp.Name[:1] == "g" and shp.Name[1:2].isdigit() and shp.Name[1] != "0":
                groups.setdefault(int(shp.Name[1]), []).append(shp)
        audio = sl.Shapes.AddMediaObject2(str(wav), False, True, 0, 0, 10, 10)
        audio.Left, audio.Top = pres.PageSetup.SlideWidth + 100, 0  # off-slide: no speaker icon in the video
        play = seq.AddEffect(audio, 83, 0, 2)  # msoAnimEffectMediaPlay, with previous
        play.Timing.TriggerDelayTime = 0
        for g in sorted(groups):
            delay = 0.0 if g == 1 else starts[g - 1]
            for j, shp in enumerate(groups[g]):
                e = seq.AddEffect(shp, 10, 0, 2)  # fade, with previous
                e.Timing.Duration = 0.5
                e.Timing.TriggerDelayTime = delay
        sl.SlideShowTransition.EntryEffect = 3849  # ppEffectFadeSmoothly
        sl.SlideShowTransition.Duration = 0.6
        sl.SlideShowTransition.AdvanceOnTime = True
        sl.SlideShowTransition.AdvanceTime = total + 0.9
    pres.CreateVideo(str(mp4), True, 5, 1080, 30, 90)
    while pres.CreateVideoStatus in (1, 2):  # queued / in progress
        time.sleep(2)
    status = pres.CreateVideoStatus
    pres.Close()
    app.Quit()
    video_pptx.unlink(missing_ok=True)
    if status != 3:
        raise RuntimeError(f"PowerPoint video export failed (status {status})")
    # PowerPoint's export is large; re-encode to an upload-friendly size with the same look
    small = mp4.with_suffix(".tmp.mp4")
    subprocess.run([FFMPEG, "-y", "-i", str(mp4), "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(small)], check=True, capture_output=True)
    small.replace(mp4)
    return pdf, mp4


if __name__ == "__main__":
    (OUT / "preview").mkdir(exist_ok=True)
    pptx = OUT / f"{STEM}.pptx"
    build_pptx(pptx)
    tmp = Path(tempfile.mkdtemp(prefix="round1-"))
    narration = narrate(tmp)
    pdf, mp4 = export(pptx, narration)
    print("built:", pptx.name, pdf.name, mp4.name, f"{sum(n[2] + 1.8 for n in narration):.0f}s")
