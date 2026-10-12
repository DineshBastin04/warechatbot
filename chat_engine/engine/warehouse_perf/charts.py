"""
Static PNG charts for the executive email (email clients can't run scripts, and
many don't render SVG, so charts are images embedded inline by Content-ID).

Drawn with Pillow at 2x and downsampled, so edges are smooth. Colours follow a
validated palette (blue #2a78d6 / red #e34948 pass CVD and contrast checks on the
light surface); text always uses ink colours, never the series colour; grid and
axes are recessive; the legend is always present for two series. Every chart is
also described in words next to it in the email (alt text + a sentence), so
nothing depends on colour or the image loading.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFont

SCALE = 2
SURFACE = "#fcfcfb"
INK = "#1a1a19"
INK_2 = "#52514e"
INK_3 = "#76756f"
GRID = "#e7e6e2"
BLUE = "#2a78d6"          # today / better than normal
RED = "#e34948"           # worse than normal (needs attention)
NEUTRAL = "#b9b7b0"       # within normal variation
NORMAL_LINE = "#3b3a37"   # the "normal" reference line
BAND = "#fbe7e6"          # problem window shading

_FONT_CANDIDATES = {
    "regular": ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/Library/Fonts/Arial.ttf"],
    "bold": ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf"],
}
_font_cache = {}


def _font(size, weight="regular"):
    key = (size, weight)
    if key not in _font_cache:
        font = None
        for path in _FONT_CANDIDATES[weight]:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, size * SCALE)
                    break
                except OSError:
                    continue
        _font_cache[key] = font or ImageFont.load_default(size=size * SCALE)
    return _font_cache[key]


def _png(img, w, h):
    out = io.BytesIO()
    img.resize((w, h), Image.LANCZOS).save(out, format="PNG", optimize=True)
    return out.getvalue()


def _text_w(draw, text, font):
    return draw.textlength(text, font=font)


def _nice_scale(vmax, ticks=4):
    """(axis max, step) with round steps (1, 2, 5 x 10^k) and ~8% headroom above the tallest mark,
    so ticks read 0 / 5 / 10 / 15 / 20 rather than 3.8 / 11."""
    import math
    raw = max(float(vmax), 1e-9) * 1.08 / ticks
    exp = 10 ** math.floor(math.log10(raw))
    step = next(m * exp for m in (1, 2, 5, 10) if m * exp >= raw)
    return step * ticks, step


def _fmt(v):
    return f"{v:,.0f}" if abs(v) >= 10 or float(v).is_integer() else f"{v:,.1f}"


def _vtext(img, x, cy, text, font, fill):
    """Text rotated 90 degrees (reads bottom to top), centred vertically on cy, left edge at x."""
    probe = ImageDraw.Draw(img)
    w = int(probe.textlength(text, font=font)) + 4 * SCALE
    h = int(font.size * 1.4)
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((2 * SCALE, 0), text, font=font, fill=fill)
    rot = tmp.rotate(90, expand=True)
    img.paste(rot, (int(x), int(cy - rot.height / 2)), rot)


def hourly_chart(hourly, start_hour=None, width=620, height=330, y_title="Per hour", x_title="Hour of the day"):
    """Columns = today per hour, dark line = normal for that hour, shaded band = problem window.
    Axis titles say what is measured: across = hour of the day, up = y_title.
    hourly: [{"hour", "actual", "baseline"}]"""
    pts = [p for p in hourly if (p.get("actual") or 0) or (p.get("baseline") or 0)]
    if not pts:
        return None
    s = SCALE
    W, H = width * s, height * s
    img = Image.new("RGB", (W, H), SURFACE)
    d = ImageDraw.Draw(img)
    f_axis, f_leg, f_title = _font(11), _font(12), _font(11, "bold")
    left, right, top, bottom = 66 * s, 16 * s, 58 * s, 50 * s
    pw, ph = W - left - right, H - top - bottom
    vmax, step = _nice_scale(max(max(p.get("actual") or 0, p.get("baseline") or 0) for p in pts))
    y = lambda v: top + ph - (v / vmax) * ph
    n = len(pts)
    slot = pw / n
    bar_w = max(4 * s, min(slot * 0.62, 38 * s))

    if start_hour is not None:                          # problem band; its label sits ABOVE the plot,
        idx = next((i for i, p in enumerate(pts) if p["hour"] >= start_hour), None)   # clear of the line
        if idx is not None:
            x0 = left + idx * slot
            d.rectangle([x0, top, left + pw, top + ph], fill=BAND)
            d.line([x0, top - 6 * s, x0, top + ph], fill="#e3a3a2", width=s)
            d.text((x0 + 6 * s, top - 20 * s), f"Problem from {start_hour:02d}:00", fill=INK_2, font=f_title)

    k = 0
    while k * step <= vmax + 1e-9:                      # recessive grid + y labels
        v = k * step
        yy = y(v)
        d.line([left, yy, left + pw, yy], fill=GRID, width=s)
        t = _fmt(v)
        d.text((left - 8 * s - _text_w(d, t, f_axis), yy - 7 * s), t, fill=INK_3, font=f_axis)
        k += 1

    hour_label = (lambda h: f"{h:02d}:00") if slot >= 42 * s else (lambda h: f"{h:02d}")
    for i, p in enumerate(pts):                         # today = columns, 4px rounded tops
        cx = left + i * slot + slot / 2
        a = p.get("actual") or 0
        if a > 0:
            y0 = y(a)
            r = min(4 * s, (top + ph - y0) / 2)
            d.rounded_rectangle([cx - bar_w / 2, y0, cx + bar_w / 2, top + ph], radius=r, fill=BLUE,
                                corners=(True, True, False, False))
        if n <= 16 or i % 2 == 0:
            t = hour_label(p["hour"])
            d.text((cx - _text_w(d, t, f_axis) / 2, top + ph + 8 * s), t, fill=INK_3, font=f_axis)

    line = [(left + i * slot + slot / 2, y(p.get("baseline") or 0)) for i, p in enumerate(pts)]
    if len(line) > 1:                                   # normal = 2px dark line with markers + surface ring
        d.line(line, fill=NORMAL_LINE, width=2 * s, joint="curve")
    for (lx, ly) in line:
        d.ellipse([lx - 5 * s, ly - 5 * s, lx + 5 * s, ly + 5 * s], fill=SURFACE)
        d.ellipse([lx - 3.5 * s, ly - 3.5 * s, lx + 3.5 * s, ly + 3.5 * s], fill=NORMAL_LINE)
    d.line([left, top + ph, left + pw, top + ph], fill=INK_3, width=s)

    # axis titles: across (x) under the hour labels, up (y) rotated along the left edge
    xt = f"{x_title} →"
    d.text((left + pw / 2 - _text_w(d, xt, f_title) / 2, top + ph + 28 * s), xt, fill=INK_2, font=f_title)
    _vtext(img, 6 * s, top + ph / 2, f"{y_title} →", f_title, INK_2)

    lx = left                                           # legend (two series -> always present)
    d.rounded_rectangle([lx, 12 * s, lx + 12 * s, 24 * s], radius=2 * s, fill=BLUE)
    d.text((lx + 18 * s, 10 * s), "Today", fill=INK, font=f_leg)
    lx += 18 * s + _text_w(d, "Today", f_leg) + 22 * s
    d.line([lx, 18 * s, lx + 18 * s, 18 * s], fill=NORMAL_LINE, width=2 * s)
    d.ellipse([lx + 5.5 * s, 14.5 * s, lx + 12.5 * s, 21.5 * s], fill=NORMAL_LINE)
    d.text((lx + 24 * s, 10 * s), "Normal for this weekday and hour", fill=INK, font=f_leg)
    return _png(img, width, height)


def change_bars(rows, width=620, row_h=46, y_title=None):
    """Management bar chart: one row per warehouse / step / measure, worst first. Each row: the name, a bar of
    the % change against normal (only the sides that are used), and on the right the whole-number % in bold
    with "today X · normally Y" under it. Red = problem, grey = normal ups and downs, blue = better.
    rows: [{"name", "pct", "state": "worse"|"normal"|"better", "today", "normal"}]"""
    rows = [r for r in rows if r.get("pct") is not None]
    if not rows:
        return None
    s = SCALE
    f_name, f_val, f_sub, f_head, f_leg = _font(13, "bold"), _font(14, "bold"), _font(10.5), _font(11, "bold"), _font(11.5)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    states = [st for st in ("worse", "normal", "better") if any(r.get("state") == st for r in rows)]
    head, legend_h = 22, 30
    height = head + row_h * len(rows) + legend_h
    W, H = width * s, height * s
    img = Image.new("RGB", (W, H), SURFACE)
    d = ImageDraw.Draw(img)

    name_w = max(_text_w(probe, str(r["name"]), f_name) for r in rows) + 16 * s
    if y_title:
        name_w = max(name_w, _text_w(probe, y_title, f_head) + 16 * s)
    subs = [f"today {r.get('today')} · normally {r.get('normal')}" if r.get("today") is not None else "" for r in rows]
    val_w = max([_text_w(probe, t, f_sub) for t in subs] + [60 * s]) + 12 * s
    left, right = min(name_w, 200 * s), min(val_w, 200 * s)
    pw = W - left - right - 10 * s
    neg = max([-r["pct"] for r in rows if r["pct"] < 0] + [0])
    pos = max([r["pct"] for r in rows if r["pct"] > 0] + [0])
    span = (neg + pos) or 1.0
    zero = left + neg / span * pw
    x = lambda v: zero + v / span * pw
    colour = {"worse": RED, "better": BLUE, "normal": NEUTRAL}

    top = head * s
    if y_title:
        d.text((4 * s, 4 * s), y_title, fill=INK_2, font=f_head)
    t = "vs normal"
    d.text((W - 4 * s - _text_w(d, t, f_head), 4 * s), t, fill=INK_2, font=f_head)
    for i, r in enumerate(rows):
        cy = top + i * row_h * s + row_h * s / 2
        if i:
            d.line([4 * s, cy - row_h * s / 2, W - 4 * s, cy - row_h * s / 2], fill=GRID, width=s)
        d.text((4 * s, cy - 9 * s), str(r["name"]), fill=INK, font=f_name)
        x1 = x(r["pct"])
        a, b = sorted((zero, x1))
        if b - a >= 1:
            d.rounded_rectangle([a, cy - 9 * s, b, cy + 9 * s], radius=min(4 * s, (b - a) / 2),
                                fill=colour.get(r.get("state"), NEUTRAL))
        p = round(r["pct"])
        v = f"{'+' if p > 0 else '−' if p < 0 else ''}{abs(p)}%"
        d.text((W - 4 * s - _text_w(d, v, f_val), cy - 17 * s), v, fill=INK, font=f_val)
        if subs[i]:
            d.text((W - 4 * s - _text_w(d, subs[i], f_sub), cy + 3 * s), subs[i], fill=INK_3, font=f_sub)
    bottom = top + row_h * s * len(rows)
    d.line([zero, top - 2 * s, zero, bottom], fill=INK_3, width=s)

    words = {"worse": "Problem — worse than on normal days", "normal": "Normal ups and downs",
             "better": "Better than normal"}
    lx, ly = 4 * s, bottom + 10 * s                      # legend: only the colours that appear
    for st in states:
        d.rounded_rectangle([lx, ly + 2 * s, lx + 12 * s, ly + 14 * s], radius=2 * s, fill=colour[st])
        d.text((lx + 18 * s, ly), words[st], fill=INK_2, font=f_leg)
        lx += 18 * s + _text_w(d, words[st], f_leg) + 20 * s
    return _png(img, width, height)
