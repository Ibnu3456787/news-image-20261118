#!/usr/bin/env python3
"""Compose the news-image-20261118 front page (1024x1024) — layout variants.

Fresh code for this entry. All text is rendered in PIL with real fonts; the 11
vignettes are text-free illustrations made for this entry; the world map is
drawn from Natural Earth 110m land polygons (public data).

Usage: python3 compose.py [variant ...]   # variants: e, b ; default: both
Outputs go to layouts/ next to this file: one PNG per variant, a 300px
preview of each, and a crop-preview sheet showing exactly how each vignette
is cropped in the tile and lead slots.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, "candidates")
OUT = os.path.join(HERE, "layouts")
W, H = 1024, 1024

PAPER = (250, 247, 240)
CARD = (255, 255, 255)
INK = (17, 17, 17)
GREY = (90, 90, 90)
RULE = (215, 210, 198)
RED = (179, 38, 30)
NAVY = (27, 42, 74)
SEA = (220, 233, 242)
LAND = (232, 224, 208)
LAND_LINE = (190, 180, 158)

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

MARG, GUT = 12, 8  # page margin, gutter between cells


def load_font(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def crop_to_aspect(im, tw, th, roi=None, anchor=(0.5, 0.5)):
    """Crop im to the target aspect, optionally inside a region of interest.

    roi is (x0, y0, x1, y1) as fractions of the image; anchor (ax, ay) in
    [0, 1] picks where the crop sits inside the roi (0.5 = centred).
    """
    iw, ih = im.size
    if roi is not None:
        x0, y0, x1, y1 = roi
        im = im.crop((int(iw * x0), int(ih * y0), int(iw * x1), int(ih * y1)))
        iw, ih = im.size
    target = tw / th
    src = iw / ih
    if src > target:
        nw = int(ih * target)
        x = int((iw - nw) * anchor[0])
        im = im.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw / target)
        y = int((ih - nh) * anchor[1])
        im = im.crop((0, y, iw, y + nh))
    return im.resize((tw, th), Image.LANCZOS)


# ------------------------------------------------------------------ data
# roi: region of interest as fractions; anchor: crop position inside it.
# 03 keeps one US flag + the Philippine flag (image has two US flags).
STORIES = [
    dict(num=1, file="01-lead-a.png", region="MIDDLE EAST",
         headline="IRAN STRIKES KUWAIT & BAHRAIN",
         sub="Iranian drones hit US air defences at Ali Al Salem; Bahrain "
             "intercepts a third wave. Kuwait calls it a \u201cdangerous "
             "escalation\u201d.",
         lat=29.35, lon=47.52),
    dict(num=2, file="02-xiputin-a.png", region="ASIA",
         headline="XI & PUTIN MEET IN SHENZHEN",
         sub="Fifth meeting this year; trilateral next.",
         sub_b="Fifth meeting this year.",
         lat=22.55, lon=114.06),
    dict(num=3, file="03-trumpmarcos-a-fixed.png", region="ASIA",
         headline="TRUMP & MARCOS REAFFIRM ALLIANCE",
         sub="Arms sales top $5bn; nuclear deal teased.",
         sub_b="US arms sales top $5bn.",
         lat=14.60, lon=120.98, roi=(0.0, 0.28, 1.0, 0.56)),
    dict(num=4, file="04-peltola-a.png", region="NORTH AMERICA",
         headline="PELTOLA WINS ALASKA SENATE SEAT",
         sub="Democrats take 56-44 Senate majority.",
         lat=61.22, lon=-149.90),
    dict(num=5, file="05-xavier-a.png", region="OCEANIA",
         headline="CYCLONE XAVIER, CAT 5",
         sub="220 km/h winds batter the Cook Islands.",
         sub_b="220 km/h winds hit Cook Islands.",
         lat=-10.1, lon=-163.6),
    dict(num=6, file="06-ebola-a.png", region="AFRICA",
         headline="WHO KEEPS EBOLA EMERGENCY",
         sub="11,000+ cases, 5,400+ deaths.",
         lat=1.56, lon=30.25),
    dict(num=7, file="07-gpt-a.png", region="TECH",
         headline="OPENAI LAUNCHES GPT-6.2",
         sub="Astra frontier, Sol everyday.",
         sub_b="Astra frontier, Sol everyday.",
         lat=37.77, lon=-122.42),
    dict(num=8, file="08-peace-a.png", region="MIDDLE EAST",
         headline="BOARD OF PEACE FAULTS BOTH SIDES",
         sub="UN report: both sides failing ceasefire pledges.",
         sub_b="Both sides failing ceasefire pledges.",
         lat=31.50, lon=34.47, roi=(0.0, 0.02, 1.0, 0.30)),
    dict(num=9, file="09-an12-a-fixed.png", region="EUROPE",
         headline="CASE OPENED OVER AN-12 CRASH",
         sub="Probe into Tuesday's Siberia crash; 19 dead.",
         sub_b="Probe into Tuesday's crash; 19 dead.",
         lat=55.36, lon=86.09),
    dict(num=10, file="10-canada-b.png", region="NORTH AMERICA",
         headline="CANADA-CHINA TIES DEEPEN",
         sub="Market access widened; exports up over a third.",
         sub_b="Exports to China up over a third.",
         lat=45.42, lon=-75.70),
    dict(num=11, file="11-java-a.png", region="TECH",
         headline="JAVA4SHELL FLAW UNDER ATTACK",
         sub="Critical flaw patched; scans probing for it.",
         sub_b="Critical flaw patched; scans probing.",
         lat=30.27, lon=-97.74),
]

INDEX = [
    (12, "Voyager 1 reaches one light-day from Earth."),
    (13, "Xi greets Trump on the Shenzhen tarmac \u2014 a hug on arrival."),
    (14, "Carney-Trump talks \u2018nice\u2019 but no deal; 50% tariffs stay."),
    (15, "Sheinbaum: Mexico-US trade talks \u2018very far along\u2019."),
    (16, "Lee meets Xi in Shenzhen; Korea-China FTA talks conclude."),
    (17, "Nvidia slips 2.9% despite record $115.84bn quarter."),
    (18, "COP31 launches the second Global Stocktake; 21 issues open."),
    (19, "Fiji declares national disaster over El Nino drought."),
    (20, "World Court to rule Thursday on Myanmar genocide case."),
    (21, "UK and EU drop \u2018trusted partnership\u2019 from summit draft."),
    (22, "EU approves Indonesia trade deal; 90% of duties cut."),
    (23, "EU proposes \u20ac45bn Ukraine loan; \u20ac25bn military."),
    (24, "Cape Town condemned over 44 baboons in tiny enclosure."),
    (25, "DOJ moves to block Jack Smith\u2019s deposition in BBC suit."),
    (26, "Myanmar\u2019s Min Aung Hlaing to review ASEAN relationship."),
    (27, "Putin to keep fighting in Ukraine into 2027, intel says."),
    (28, "NATO releases first Alliance-wide 5G/6G/SATCOM strategy."),
    (29, "Rubio dismisses report of an Iranian \u2018dirty bomb\u2019 plot."),
    (30, "Senate panel advances Trump\u2019s FCC pick 15-0; Dems boycott."),
    (31, "Alcaraz beats Medvedev 6-2, 6-4 to top ATP Finals group."),
    (32, "Google rolls out Genie 4 world-builder to Ultra users."),
    (33, "Cornyn blocks Trump\u2019s judicial nominee in lame-duck setback."),
    (34, "Senators press DNI over NSA outage; ROOT CAUSE Act filed."),
    (35, "Brazil Senate passes $10bn fiscal package to calm markets."),
]

SOURCES = ("Sources: AP, Reuters, AFP, BBC, Al Jazeera, UN News, NASA, WHO, "
           "NATO, Nextgov, OpenAI, Google, PNA. The day\u2019s news, "
           "Wednesday 18 November 2026. Original drawings.")

JUDGE_LINE = ("Every story below happened, or was first reported, on this day.")

VIGNETTES = {s["file"]: Image.open(os.path.join(CAND, s["file"])).convert("RGB")
             for s in STORIES}

with open(os.path.join(HERE, "ne_110m_land.geojson")) as fh:
    GEO = json.load(fh)

LAT_TOP, LAT_BOT = 74.0, -56.0

# Pin nudges as fractions of map width / height, to separate close pins.
# Gaza/Kuwait and Shenzhen/Manila would otherwise overlap.
PIN_NUDGE = {
    1: (0.012, -0.045),   # Kuwait: up-right
    2: (-0.014, -0.05),   # Shenzhen: up-left
    3: (0.014, 0.05),     # Manila: down-right
    8: (-0.014, 0.055),   # Gaza: down-left
}


# ------------------------------------------------------------------ page
class Page:
    def __init__(self):
        self.img = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self.warnings = []

    # -- header ------------------------------------------------------
    def header(self, rule_y):
        d = self.d
        f_mast = load_font(SERIF_B, 58)
        title = "THE WORLD TODAY"
        tw = d.textlength(title, font=f_mast)
        d.text(((W - tw) / 2, 2), title, fill=INK, font=f_mast)
        f_date = load_font(SANS_B, 17)
        dateline = "WEDNESDAY 18 NOVEMBER 2026"
        dw = d.textlength(dateline, font=f_date)
        d.text(((W - dw) / 2, 62), dateline, fill=INK, font=f_date)
        f_cnt = load_font(SANS_B, 15)
        count = "35 STORIES  \u00b7  6 CONTINENTS  \u00b7  ONE DAY"
        cw = d.textlength(count, font=f_cnt)
        d.text(((W - cw) / 2, 84), count, fill=RED, font=f_cnt)
        f_j = load_font(SERIF_I, 13)
        jw = d.textlength(JUDGE_LINE, font=f_j)
        d.text(((W - jw) / 2, 104), JUDGE_LINE, fill=GREY, font=f_j)
        d.line((MARG, rule_y, W - MARG, rule_y), fill=INK, width=2)

    # -- shared bits -------------------------------------------------
    def badge(self, x, y, r, num, size=14):
        d = self.d
        cx, cy = x + r, y + r
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED)
        f = load_font(SANS_B, size)
        t = str(num)
        d.text((cx - d.textlength(t, font=f) / 2, cy - size / 2 - 1),
               t, fill=CARD, font=f)

    def tile(self, box, story, img_h, hl_size=15, sub_size=11,
             badge_r=12, max_hl=2, max_sub=1, sub_key="sub"):
        """One illustrated story tile. Text shrinks to fit; nothing leaves
        the box. Records a warning if a shrink floor is hit. sub_key picks
        which sub-line field to use ('sub' or the shorter 'sub_b')."""
        d = self.d
        x0, y0, x1, y1 = (int(v) for v in box)
        d.rectangle((x0, y0, x1, y1), fill=CARD, outline=RULE, width=1)
        w = x1 - x0
        pic = crop_to_aspect(VIGNETTES[story["file"]], w - 2, img_h,
                             roi=story.get("roi"), anchor=story.get("anchor", (0.5, 0.5)))
        self.img.paste(pic, (x0 + 1, y0 + 1))
        self.badge(x0 + 6, y0 + 6, badge_r, story["num"],
                   size=14 if badge_r >= 12 else 12)
        ty = y0 + 1 + img_h + 5
        d.text((x0 + 6, ty), story["region"], fill=NAVY,
               font=load_font(SANS_B, 10))
        ty += 13
        size = hl_size
        while size > 10:
            f_h = load_font(SANS_B, size)
            if len(wrap_text(d, story["headline"], f_h, w - 12)) <= max_hl:
                break
            size -= 1
        if size <= 10:
            self.warnings.append(f"tile {story['num']}: headline hit shrink floor")
        f_h = load_font(SANS_B, size)
        for line in wrap_text(d, story["headline"], f_h, w - 12)[:max_hl]:
            if ty + size > y1 - 2:
                self.warnings.append(f"tile {story['num']}: headline clipped")
                break
            d.text((x0 + 6, ty), line, fill=INK, font=f_h)
            ty += size + 2
        sub = story.get(sub_key, story["sub"])
        size = sub_size
        while size > 9:
            f_s = load_font(SANS, size)
            if len(wrap_text(d, sub, f_s, w - 12)) <= max_sub:
                break
            size -= 1
        if size <= 9:
            self.warnings.append(f"tile {story['num']}: sub hit shrink floor")
        f_s = load_font(SANS, size)
        for line in wrap_text(d, sub, f_s, w - 12)[:max_sub]:
            if ty + size > y1 - 2:
                self.warnings.append(f"tile {story['num']}: sub clipped")
                break
            d.text((x0 + 6, ty), line, fill=GREY, font=f_s)
            ty += size + 2

    def lead_row(self, box):
        """Full-width lead: big image left, headline + dek right."""
        d = self.d
        x0, y0, x1, y1 = (int(v) for v in box)
        d.rectangle((x0, y0, x1, y1), fill=CARD, outline=RULE, width=1)
        iw = 560
        pic = crop_to_aspect(VIGNETTES[STORIES[0]["file"]], iw, y1 - y0 - 2)
        self.img.paste(pic, (x0 + 1, y0 + 1))
        self.badge(x0 + 6, y0 + 6, 14, 1, size=16)
        tx = x0 + iw + 16
        tw = x1 - tx - 10
        ty = y0 + 12
        d.text((tx, ty), "MIDDLE EAST", fill=NAVY, font=load_font(SANS_B, 12))
        ty += 20
        f_h = load_font(SANS_B, 30)
        for line in wrap_text(d, STORIES[0]["headline"], f_h, tw):
            d.text((tx, ty), line, fill=INK, font=f_h)
            ty += 34
        ty += 4
        f_s = load_font(SANS, 15)
        for line in wrap_text(d, STORIES[0]["sub"], f_s, tw):
            if ty + 15 > y1 - 4:
                self.warnings.append("lead: dek clipped")
                break
            d.text((tx, ty), line, fill=GREY, font=f_s)
            ty += 19

    def lead_band(self, img_box, text_box):
        """Full-width lead image band with a headline band below it."""
        d = self.d
        x0, y0, x1, y1 = (int(v) for v in img_box)
        d.rectangle((x0, y0, x1, y1), fill=CARD, outline=RULE, width=1)
        pic = crop_to_aspect(VIGNETTES[STORIES[0]["file"]], x1 - x0 - 2, y1 - y0 - 2)
        self.img.paste(pic, (x0 + 1, y0 + 1))
        self.badge(x0 + 6, y0 + 6, 14, 1, size=16)
        x0, y0, x1, y1 = (int(v) for v in text_box)
        d.rectangle((x0, y0, x1, y1), fill=CARD, outline=RULE, width=1)
        tx, ty = x0 + 10, y0 + 6
        d.text((tx, ty), "MIDDLE EAST", fill=NAVY, font=load_font(SANS_B, 11))
        ty += 16
        f_h = load_font(SANS_B, 26)
        for line in wrap_text(d, STORIES[0]["headline"], f_h, x1 - tx - 10):
            d.text((tx, ty), line, fill=INK, font=f_h)
            ty += 30
        f_s = load_font(SANS, 13)
        for line in wrap_text(d, STORIES[0]["sub"], f_s, x1 - tx - 10):
            if ty + 13 > y1 - 4:
                self.warnings.append("lead band: sub clipped")
                break
            d.text((tx, ty), line, fill=GREY, font=f_s)
            ty += 17

    # -- map ---------------------------------------------------------
    def world_map(self, box, pin_r=9):
        d = self.d
        x0, y0, x1, y1 = (int(v) for v in box)
        f_t = load_font(SANS_B, 15)
        d.text((x0, y0), "WHERE IT HAPPENED", fill=NAVY, font=f_t)
        d.text((x0 + d.textlength("WHERE IT HAPPENED", font=f_t) + 10, y0 + 2),
               "the 11 pictured stories, numbered", fill=GREY,
               font=load_font(SANS, 12))
        top = y0 + 22
        mw, mh = x1 - x0, y1 - top
        d.rectangle((x0, top, x1, y1), fill=SEA, outline=RULE, width=1)

        def proj(lon, lat):
            px = x0 + (lon + 180.0) / 360.0 * mw
            py = top + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * mh
            return (px, py)

        for feat in GEO["features"]:
            geom = feat["geometry"]
            rings = []
            if geom["type"] == "Polygon":
                rings = geom["coordinates"]
            elif geom["type"] == "MultiPolygon":
                for part in geom["coordinates"]:
                    rings.extend(part)
            for ring in rings:
                pts, prev = [], None
                for lon, lat in ring:
                    if lat > LAT_TOP or lat < LAT_BOT:
                        continue
                    if prev is not None and abs(lon - prev) > 180:
                        if len(pts) > 2:
                            d.polygon(pts, fill=LAND, outline=LAND_LINE)
                        pts = []
                    pts.append(proj(lon, lat))
                    prev = lon
                if len(pts) > 2:
                    d.polygon(pts, fill=LAND, outline=LAND_LINE)

        f_pin = load_font(SANS_B, 11 if pin_r <= 9 else 13)
        for s in STORIES:
            cx, cy = proj(s["lon"], s["lat"])
            fx, fy = PIN_NUDGE.get(s["num"], (0.0, 0.0))
            px, py = cx + fx * mw, cy + fy * mh
            if (fx, fy) != (0.0, 0.0):
                d.line((cx, cy, px, py), fill=RED, width=1)
            d.ellipse((px - pin_r - 1, py - pin_r - 1, px + pin_r + 1, py + pin_r + 1),
                      fill=CARD)
            d.ellipse((px - pin_r, py - pin_r, px + pin_r, py + pin_r), fill=RED)
            t = str(s["num"])
            tw = d.textlength(t, font=f_pin)
            d.text((px - tw / 2, py - f_pin.size / 2 - 1), t, fill=CARD, font=f_pin)

    # -- index + sources ----------------------------------------------
    def index(self, box, cols, font_size, row_h):
        d = self.d
        x0, y0, x1, y1 = (int(v) for v in box)
        f_t = load_font(SANS_B, 15)
        d.text((x0, y0), "ALSO ON THIS DAY", fill=NAVY, font=f_t)
        d.text((x0 + d.textlength("ALSO ON THIS DAY", font=f_t) + 10, y0 + 2),
               "stories 12-35", fill=GREY, font=load_font(SANS, 12))
        top = y0 + 22
        f_n = load_font(SANS_B, font_size)
        f_i = load_font(SANS, font_size)
        cw = (x1 - x0 - (cols - 1) * 16) / cols
        per_col = (len(INDEX) + cols - 1) // cols
        for i, (num, text) in enumerate(INDEX):
            c, r = divmod(i, per_col)
            cx = x0 + c * (cw + 16)
            cy = top + r * row_h
            if cy + font_size > y1:
                self.warnings.append(f"index {num}: row past box bottom")
            d.text((cx, cy), f"{num}.", fill=RED, font=f_n)
            nw = d.textlength(f"{num}. ", font=f_n)
            if d.textlength(text, font=f_i) > cw - nw:
                self.warnings.append(f"index {num}: line too wide "
                                     f"({d.textlength(text, font=f_i):.0f}px > "
                                     f"{cw - nw:.0f}px)")
            d.text((cx + nw, cy), text, fill=INK, font=f_i)

    def sources(self, y):
        d = self.d
        d.line((MARG, y - 6, W - MARG, y - 6), fill=RULE, width=1)
        f_s = load_font(SANS, 11)
        for j, line in enumerate(wrap_text(d, SOURCES, f_s, W - 2 * MARG)):
            d.text((MARG, y + j * 14), line, fill=GREY, font=f_s)


# ---------------------------------------------------------------- layouts
def col_x(c, cw):
    return MARG + c * (cw + GUT)


def layout_e():
    """Baseline (20261117 layout E adapted): full-width lead row (image left,
    text right); 2 rows x 4 tiles; row 3 = 2 tiles + map cell (2 cols);
    2-col index; sources."""
    p = Page()
    p.header(122)
    cw = (W - 2 * MARG - 3 * GUT) / 4  # 244
    p.lead_row((MARG, 130, W - MARG, 298))
    for c in range(4):
        p.tile((col_x(c, cw), 306, col_x(c, cw) + cw, 442), STORIES[1 + c],
               img_h=68, hl_size=15, sub_size=11)
    for c in range(4):
        p.tile((col_x(c, cw), 450, col_x(c, cw) + cw, 586), STORIES[5 + c],
               img_h=68, hl_size=15, sub_size=11)
    for c in range(2):
        p.tile((col_x(c, cw), 594, col_x(c, cw) + cw, 754), STORIES[9 + c],
               img_h=80, hl_size=15, sub_size=11)
    p.world_map((col_x(2, cw), 594, W - MARG, 754), pin_r=9)
    p.index((MARG, 762, W - MARG, 972), cols=2, font_size=12, row_h=16)
    p.sources(978)
    return p


def layout_b():
    """Lead-band variant: full-width lead image band + headline band; 2 rows
    x 5 tiles (short subs); full-width map strip; 2-col index; sources."""
    p = Page()
    p.header(122)
    p.lead_band((MARG, 130, W - MARG, 300), (MARG, 300, W - MARG, 370))
    cw = (W - 2 * MARG - 4 * GUT) / 5  # 195.2
    for c in range(5):
        p.tile((col_x(c, cw), 378, col_x(c, cw) + cw, 514), STORIES[1 + c],
               img_h=64, hl_size=14, sub_size=11, sub_key="sub_b")
    for c in range(5):
        p.tile((col_x(c, cw), 522, col_x(c, cw) + cw, 658), STORIES[6 + c],
               img_h=64, hl_size=14, sub_size=11, sub_key="sub_b")
    p.world_map((MARG, 666, W - MARG, 778), pin_r=9)
    p.index((MARG, 786, W - MARG, 966), cols=2, font_size=11, row_h=13)
    p.sources(972)
    return p


def layout_d():
    """Lead-band + 4-col hybrid: full-width lead image band + headline band;
    2 rows x 4 tiles; row 3 = 2 tiles + map cell (2 cols); 2-col index;
    sources. Tests whether the big lead image can coexist with roomy tiles."""
    p = Page()
    p.header(122)
    p.lead_band((MARG, 130, W - MARG, 290), (MARG, 290, W - MARG, 360))
    cw = (W - 2 * MARG - 3 * GUT) / 4  # 244
    for c in range(4):
        p.tile((col_x(c, cw), 368, col_x(c, cw) + cw, 500), STORIES[1 + c],
               img_h=64, hl_size=15, sub_size=11)
    for c in range(4):
        p.tile((col_x(c, cw), 508, col_x(c, cw) + cw, 640), STORIES[5 + c],
               img_h=64, hl_size=15, sub_size=11)
    for c in range(2):
        p.tile((col_x(c, cw), 648, col_x(c, cw) + cw, 776), STORIES[9 + c],
               img_h=62, hl_size=15, sub_size=11)
    p.world_map((col_x(2, cw), 648, W - MARG, 776), pin_r=9)
    p.index((MARG, 784, W - MARG, 968), cols=2, font_size=11, row_h=13.5)
    p.sources(974)
    return p


VARIANTS = {"e": ("layout-e", layout_e), "b": ("layout-b", layout_b),
            "d": ("layout-d", layout_d)}


def crop_preview():
    """Sheet of the 11 vignettes cropped exactly as used: tile aspect
    (242x68) in rows of 4, plus the lead-row (560x166) and lead-band
    (1000x200 and 1000x160) crops — to verify crops (esp. the 03 flags
    and the 08 dove) before judging."""
    sheet = Image.new("RGB", (1024, 1000), PAPER)
    d = ImageDraw.Draw(sheet)
    f = load_font(SANS_B, 16)
    d.text((12, 8), "Tile crops (242x68) as used in layout E", fill=INK, font=f)
    y = 36
    for r in range(3):
        x = 12
        for s in STORIES[r * 4:(r + 1) * 4]:
            pic = crop_to_aspect(VIGNETTES[s["file"]], 242, 68,
                                 roi=s.get("roi"),
                                 anchor=s.get("anchor", (0.5, 0.5)))
            sheet.paste(pic, (x, y))
            d.text((x, y + 74), f"#{s['num']} {s['file']}", fill=GREY,
                   font=load_font(SANS, 11))
            x += 242 + 8
        y += 114
    # lead crops
    d.text((12, y + 2), "Lead crops: row (560x166), band 200, band 160",
           fill=INK, font=f)
    y += 30
    lead = crop_to_aspect(VIGNETTES[STORIES[0]["file"]], 560, 166)
    sheet.paste(lead, (12, y))
    y += 176
    band = crop_to_aspect(VIGNETTES[STORIES[0]["file"]], 1000, 200)
    sheet.paste(band, (12, y))
    y += 210
    band160 = crop_to_aspect(VIGNETTES[STORIES[0]["file"]], 1000, 160)
    sheet.paste(band160, (12, y))
    return sheet


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    wanted = argv[1:] or list(VARIANTS)
    for key in wanted:
        name, fn = VARIANTS[key]
        page = fn()
        path = os.path.join(OUT, f"{name}.png")
        page.img.save(path, optimize=True)
        page.img.resize((300, 300), Image.LANCZOS).save(
            os.path.join(OUT, f"{name}-300.png"))
        size = os.path.getsize(path)
        print(f"{name}: {size:,} bytes "
              f"({'OK <=1MiB' if size <= 1048576 else 'OVER 1MiB!'})")
        for w in page.warnings:
            print(f"  WARNING: {w}")
        if not page.warnings:
            print("  no warnings")
    sheet = crop_preview()
    sheet.save(os.path.join(OUT, "crop-preview.png"))
    print("crop-preview.png saved")


if __name__ == "__main__":
    main(sys.argv)
