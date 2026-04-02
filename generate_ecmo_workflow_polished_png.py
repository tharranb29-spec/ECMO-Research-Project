import struct
import zlib
from pathlib import Path


WIDTH = 2400
HEIGHT = 1550


COLORS = {
    "bg": (246, 248, 252),
    "navy": (18, 32, 59),
    "slate": (73, 85, 105),
    "line": (191, 199, 215),
    "blue": (218, 238, 255),
    "green": (221, 247, 231),
    "yellow": (255, 245, 204),
    "coral": (255, 227, 224),
    "violet": (234, 229, 255),
    "orange": (255, 235, 214),
    "teal": (217, 249, 241),
    "white": (255, 255, 255),
    "accent": (42, 104, 224),
    "text": (34, 45, 66),
}


FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00001", "00001", "00001", "00001", "10001", "10001", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ",": ["00000", "00000", "00000", "00000", "00100", "00100", "01000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00100", "00100"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def new_canvas():
    return [[*COLORS["bg"], 255] for _ in range(WIDTH * HEIGHT)]


def set_px(pixels, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[y * WIDTH + x] = [color[0], color[1], color[2], 255]


def fill_rect(pixels, x, y, w, h, color):
    for yy in range(max(0, y), min(HEIGHT, y + h)):
        base = yy * WIDTH
        for xx in range(max(0, x), min(WIDTH, x + w)):
            pixels[base + xx] = [color[0], color[1], color[2], 255]


def rect_outline(pixels, x, y, w, h, color, t=3):
    fill_rect(pixels, x, y, w, t, color)
    fill_rect(pixels, x, y + h - t, w, t, color)
    fill_rect(pixels, x, y, t, h, color)
    fill_rect(pixels, x + w - t, y, t, h, color)


def line(pixels, x0, y0, x1, y1, color, thickness=4):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    r = thickness // 2
    for i in range(steps + 1):
        x = round(x0 + dx * i / steps)
        y = round(y0 + dy * i / steps)
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r, x + r + 1):
                set_px(pixels, xx, yy, color)


def arrow_right(pixels, x0, y, x1, color):
    line(pixels, x0, y, x1 - 28, y, color, thickness=6)
    line(pixels, x1 - 28, y, x1 - 52, y - 18, color, thickness=6)
    line(pixels, x1 - 28, y, x1 - 52, y + 18, color, thickness=6)


def arrow_down(pixels, x, y0, y1, color):
    line(pixels, x, y0, x, y1 - 24, color, thickness=6)
    line(pixels, x, y1 - 24, x - 16, y1 - 46, color, thickness=6)
    line(pixels, x, y1 - 24, x + 16, y1 - 46, color, thickness=6)


def poly_arrow(pixels, points, color):
    for a, b in zip(points, points[1:]):
        line(pixels, a[0], a[1], b[0], b[1], color, thickness=5)
    end = points[-1]
    prev = points[-2]
    if end[0] != prev[0]:
        direction = 1 if end[0] > prev[0] else -1
        line(pixels, end[0], end[1], end[0] - 20 * direction, end[1] - 16, color, thickness=5)
        line(pixels, end[0], end[1], end[0] - 20 * direction, end[1] + 16, color, thickness=5)
    else:
        direction = 1 if end[1] > prev[1] else -1
        line(pixels, end[0], end[1], end[0] - 16, end[1] - 20 * direction, color, thickness=5)
        line(pixels, end[0], end[1], end[0] + 16, end[1] - 20 * direction, color, thickness=5)


def char_width(scale):
    return 5 * scale + scale


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * char_width(scale) - scale


def wrap(text, max_width, scale):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if text_width(candidate, scale) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_char(pixels, ch, x, y, scale, color):
    pattern = FONT.get(ch, FONT[" "])
    for row_idx, row in enumerate(pattern):
        for col_idx, bit in enumerate(row):
            if bit == "1":
                for yy in range(scale):
                    for xx in range(scale):
                        set_px(pixels, x + col_idx * scale + xx, y + row_idx * scale + yy, color)


def draw_text(pixels, text, x, y, scale, color, align="left"):
    width = text_width(text, scale)
    if align == "center":
        x -= width // 2
    elif align == "right":
        x -= width
    cursor = x
    for ch in text:
        draw_char(pixels, ch, cursor, y, scale, color)
        cursor += char_width(scale)


def draw_paragraph(pixels, text, x, y, w, scale, color, center=False, gap=8):
    lines = wrap(text.upper(), w, scale)
    line_h = 7 * scale + gap
    for idx, ln in enumerate(lines):
        draw_text(
            pixels,
            ln,
            x + w // 2 if center else x,
            y + idx * line_h,
            scale,
            color,
            align="center" if center else "left",
        )
    return len(lines) * line_h


def card(pixels, x, y, w, h, fill, title, subtitle):
    fill_rect(pixels, x, y, w, h, fill)
    rect_outline(pixels, x, y, w, h, COLORS["line"], t=4)
    fill_rect(pixels, x, y, w, 54, COLORS["white"])
    rect_outline(pixels, x, y, w, 54, COLORS["line"], t=2)
    draw_text(pixels, title.upper(), x + w // 2, y + 13, 4, COLORS["navy"], align="center")
    draw_paragraph(pixels, subtitle, x + 26, y + 80, w - 52, 3, COLORS["text"], center=False, gap=10)


def pill(pixels, x, y, w, h, fill, text):
    fill_rect(pixels, x, y, w, h, fill)
    rect_outline(pixels, x, y, w, h, COLORS["line"], t=3)
    draw_text(pixels, text.upper(), x + w // 2, y + (h - 28) // 2, 4, COLORS["navy"], align="center")


def save_png(path, pixels):
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)
        row = pixels[y * WIDTH:(y + 1) * WIDTH]
        for px in row:
            raw.extend(bytes(px))

    def chunk(tag, data):
        return (
            struct.pack("!I", len(data))
            + tag
            + data
            + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack("!IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=9)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def main():
    pixels = new_canvas()

    draw_text(
        pixels,
        "AI-DRIVEN LIGAND DISCOVERY MODEL FOR ECMO INTERFACES",
        WIDTH // 2,
        48,
        6,
        COLORS["navy"],
        align="center",
    )
    draw_paragraph(
        pixels,
        "A PROPOSED SCREENING AND ACTIVE-LEARNING PIPELINE FOR HIGH-AFFINITY, IMMUNOMODULATORY, SURFACE-FUNCTIONAL CANDIDATES",
        320,
        118,
        WIDTH - 640,
        3,
        COLORS["slate"],
        center=True,
        gap=10,
    )

    pill_specs = [
        ("1. INPUTS", COLORS["blue"]),
        ("2. CURATION", COLORS["green"]),
        ("3. FEATURES", COLORS["yellow"]),
        ("4. AI SCORING", COLORS["coral"]),
        ("5. PRIORITIZE", COLORS["violet"]),
        ("6. VALIDATE", COLORS["orange"]),
    ]

    start_x = 110
    y_pill = 260
    pill_w = 310
    pill_h = 86
    gap = 52

    cards = [
        (
            "INPUTS",
            "Known ligands, custom designs, receptor structures, ECMO surface rules, and early wet-lab readouts.",
        ),
        (
            "CURATION",
            "Standardize sequences, structures, assays, and metadata into linked ligand, receptor, pair, and experiment records.",
        ),
        (
            "FEATURES",
            "Build affinity, specificity, chemistry, grafting, and immune-response features for each ligand-receptor pair.",
        ),
        (
            "AI SCORING",
            "Rank candidates using a composite score: affinity + specificity + surface compatibility + immune effect + safety.",
        ),
        (
            "PRIORITIZE",
            "Advance top hits, optimize medium-tier candidates, and keep low performers as negative examples.",
        ),
        (
            "VALIDATE",
            "Test top candidates with docking review, SPR or BLI, surface characterization, cytokines, ROS, NETs, and hemocompatibility.",
        ),
    ]

    card_y = 410
    card_w = 310
    card_h = 440

    x_positions = []
    for idx, ((label, color), (title, subtitle)) in enumerate(zip(pill_specs, cards)):
        x = start_x + idx * (pill_w + gap)
        x_positions.append(x)
        pill(pixels, x, y_pill, pill_w, pill_h, color, label)
        card(pixels, x, card_y, card_w, card_h, color, title, subtitle)
        if idx < len(pill_specs) - 1:
            arrow_right(pixels, x + pill_w + 12, y_pill + pill_h // 2, x + pill_w + gap - 12, COLORS["slate"])

    score_x = 760
    score_y = 960
    score_w = 880
    score_h = 130
    fill_rect(pixels, score_x, score_y, score_w, score_h, COLORS["white"])
    rect_outline(pixels, score_x, score_y, score_w, score_h, COLORS["accent"], t=4)
    draw_text(pixels, "FINAL DECISION SCORE", score_x + score_w // 2, score_y + 16, 4, COLORS["accent"], align="center")
    draw_paragraph(
        pixels,
        "AFFINITY + SPECIFICITY + SURFACE COMPATIBILITY + IMMUNE REPROGRAMMING + HEMOCOMPATIBILITY",
        score_x + 50,
        score_y + 62,
        score_w - 100,
        3,
        COLORS["text"],
        center=True,
        gap=10,
    )

    eval_x = 340
    eval_y = 1180
    eval_w = 1720
    eval_h = 140
    fill_rect(pixels, eval_x, eval_y, eval_w, eval_h, COLORS["teal"])
    rect_outline(pixels, eval_x, eval_y, eval_w, eval_h, COLORS["line"], t=4)
    draw_text(pixels, "EVALUATION & LABEL UPDATE", eval_x + eval_w // 2, eval_y + 18, 4, COLORS["navy"], align="center")
    draw_paragraph(
        pixels,
        "ASSIGN ADVANCE, SECONDARY, HOLD, OR REJECT. RECORD WHY A CANDIDATE FAILED OR SUCCEEDED, THEN FEED THOSE LABELS BACK INTO THE NEXT TRAINING ROUND.",
        eval_x + 60,
        eval_y + 64,
        eval_w - 120,
        3,
        COLORS["text"],
        center=True,
        gap=10,
    )

    loop_x = 160
    loop_y = 1095
    loop_w = 150
    loop_h = 235
    fill_rect(pixels, loop_x, loop_y, loop_w, loop_h, COLORS["white"])
    rect_outline(pixels, loop_x, loop_y, loop_w, loop_h, COLORS["accent"], t=4)
    draw_paragraph(
        pixels,
        "ACTIVE LEARNING LOOP",
        loop_x + 20,
        loop_y + 26,
        loop_w - 40,
        3,
        COLORS["accent"],
        center=True,
        gap=8,
    )

    poly_arrow(
        pixels,
        [
            (loop_x + loop_w, loop_y + loop_h // 2),
            (eval_x - 20, loop_y + loop_h // 2),
            (eval_x - 20, eval_y + eval_h // 2),
            (eval_x, eval_y + eval_h // 2),
        ],
        COLORS["accent"],
    )
    poly_arrow(
        pixels,
        [
            (eval_x + 240, eval_y),
            (eval_x + 240, 930),
            (265, 930),
            (265, y_pill + pill_h + 20),
        ],
        COLORS["accent"],
    )

    arrow_down(pixels, WIDTH // 2, card_y + card_h + 18, score_y - 16, COLORS["slate"])
    arrow_down(pixels, WIDTH // 2, score_y + score_h + 14, eval_y - 16, COLORS["slate"])

    draw_text(
        pixels,
        "PROPOSED FOR GROUP DISCUSSION AND INITIAL PROJECT DESIGN",
        WIDTH // 2,
        HEIGHT - 42,
        3,
        COLORS["slate"],
        align="center",
    )

    save_png("ecmo-ai-workflow-polished.png", pixels)


if __name__ == "__main__":
    main()
