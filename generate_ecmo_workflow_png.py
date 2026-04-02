import math
import struct
import zlib
from pathlib import Path


WIDTH = 2000
HEIGHT = 2600


PALETTE = {
    "bg": (248, 250, 252),
    "title": (15, 23, 42),
    "subtitle": (71, 85, 105),
    "line": (148, 163, 184),
    "arrow": (71, 85, 105),
    "input": (224, 242, 254),
    "curation": (220, 252, 231),
    "features": (254, 249, 195),
    "ai": (254, 226, 226),
    "prioritize": (237, 233, 254),
    "validation": (255, 237, 213),
    "update": (224, 231, 255),
    "loop": (204, 251, 241),
    "text": (30, 41, 59),
    "accent": (37, 99, 235),
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
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def blank_canvas():
    return [[PALETTE["bg"][0], PALETTE["bg"][1], PALETTE["bg"][2], 255] for _ in range(WIDTH * HEIGHT)]


def set_px(pixels, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[y * WIDTH + x] = [color[0], color[1], color[2], 255]


def fill_rect(pixels, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + w)
    y1 = min(HEIGHT, y + h)
    for yy in range(y0, y1):
        row = yy * WIDTH
        for xx in range(x0, x1):
            pixels[row + xx] = [color[0], color[1], color[2], 255]


def draw_rect_outline(pixels, x, y, w, h, color, t=4):
    fill_rect(pixels, x, y, w, t, color)
    fill_rect(pixels, x, y + h - t, w, t, color)
    fill_rect(pixels, x, y, t, h, color)
    fill_rect(pixels, x + w - t, y, t, h, color)


def draw_line(pixels, x0, y0, x1, y1, color, thickness=4):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    for i in range(steps + 1):
        x = round(x0 + dx * i / steps)
        y = round(y0 + dy * i / steps)
        r = thickness // 2
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r, x + r + 1):
                set_px(pixels, xx, yy, color)


def draw_arrow_down(pixels, cx, y0, y1, color):
    draw_line(pixels, cx, y0, cx, y1 - 22, color, thickness=6)
    draw_line(pixels, cx, y1 - 22, cx - 14, y1 - 40, color, thickness=6)
    draw_line(pixels, cx, y1 - 22, cx + 14, y1 - 40, color, thickness=6)


def draw_arrow_right(pixels, x0, y, x1, color):
    draw_line(pixels, x0, y, x1 - 22, y, color, thickness=6)
    draw_line(pixels, x1 - 22, y, x1 - 42, y - 14, color, thickness=6)
    draw_line(pixels, x1 - 22, y, x1 - 42, y + 14, color, thickness=6)


def draw_arrow_polyline(pixels, points, color):
    for start, end in zip(points, points[1:]):
        draw_line(pixels, start[0], start[1], end[0], end[1], color, thickness=6)
    end = points[-1]
    prev = points[-2]
    if end[1] != prev[1]:
        direction = 1 if end[1] > prev[1] else -1
        draw_line(pixels, end[0], end[1], end[0] - 14, end[1] - 18 * direction, color, thickness=6)
        draw_line(pixels, end[0], end[1], end[0] + 14, end[1] - 18 * direction, color, thickness=6)
    else:
        direction = 1 if end[0] > prev[0] else -1
        draw_line(pixels, end[0], end[1], end[0] - 18 * direction, end[1] - 14, color, thickness=6)
        draw_line(pixels, end[0], end[1], end[0] - 18 * direction, end[1] + 14, color, thickness=6)


def text_width(text, scale):
    return len(text) * (5 * scale + scale) - scale


def wrap_text(text, max_width, scale):
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
        cursor += 5 * scale + scale


def draw_paragraph(pixels, text, x, y, w, scale, color, center=False, line_gap=8):
    lines = wrap_text(text.upper(), w, scale)
    line_height = 7 * scale + line_gap
    for idx, line in enumerate(lines):
        draw_text(
            pixels,
            line,
            x + w // 2 if center else x,
            y + idx * line_height,
            scale,
            color,
            align="center" if center else "left",
        )
    return len(lines) * line_height


def box(pixels, x, y, w, h, fill, title, items):
    fill_rect(pixels, x, y, w, h, fill)
    draw_rect_outline(pixels, x, y, w, h, PALETTE["line"], t=4)
    draw_text(pixels, title.upper(), x + w // 2, y + 24, 4, PALETTE["title"], align="center")
    draw_line(pixels, x + 26, y + 72, x + w - 26, y + 72, PALETTE["line"], thickness=3)
    cursor_y = y + 102
    for item in items:
        draw_text(pixels, "-", x + 28, cursor_y + 2, 3, PALETTE["accent"])
        used = draw_paragraph(pixels, item, x + 58, cursor_y, w - 84, 3, PALETTE["text"])
        cursor_y += used + 16


def add_title(pixels):
    draw_text(
        pixels,
        "AI-DRIVEN ECMO LIGAND DISCOVERY WORKFLOW",
        WIDTH // 2,
        48,
        5,
        PALETTE["title"],
        align="center",
    )
    draw_paragraph(
        pixels,
        "FROM LIGAND INPUT TO ACTIVE LEARNING FOR HIGH-AFFINITY AND ECMO-SUITABLE IMMUNOMODULATORY CANDIDATES",
        250,
        108,
        WIDTH - 500,
        3,
        PALETTE["subtitle"],
        center=True,
        line_gap=10,
    )


def save_png(path, pixels):
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)
        row = pixels[y * WIDTH : (y + 1) * WIDTH]
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
    pixels = blank_canvas()
    add_title(pixels)

    left = 180
    box_w = 1640
    box_h = 240
    gap = 70
    top = 190

    sections = [
        (
            "1. INPUT DATA",
            PALETTE["input"],
            [
                "KNOWN LIGANDS, CUSTOM DESIGNS, AND STRUCTURALLY RELATED STARTING CANDIDATES",
                "TARGET RECEPTOR DATA SUCH AS SIGLEC-9, SIRPA, PDB STRUCTURES, AND BINDING RESIDUES",
                "ECMO SURFACE CONSTRAINTS INCLUDING PEG BRUSHES, LINKERS, AND GRAFTING RULES",
            ],
        ),
        (
            "2. DATA CURATION",
            PALETTE["curation"],
            [
                "STANDARDIZE SEQUENCES, SMILES, RECEPTOR RECORDS, AND ASSAY METADATA",
                "BUILD LINKED TABLES FOR LIGANDS, RECEPTORS, LIGAND-RECEPTOR PAIRS, SURFACE CONSTRUCTS, AND EXPERIMENTS",
                "ADD QUALITY FLAGS, REMOVE DUPLICATES, AND DEFINE INITIAL LABELS",
            ],
        ),
        (
            "3. FEATURE ENGINEERING",
            PALETTE["features"],
            [
                "LIGAND FEATURES: MOTIFS, CHARGE, MW, HYDROPHOBICITY, AND MODIFIABLE SITES",
                "PAIR FEATURES: DOCKING SCORE, CONTACT RESIDUES, POSE CONFIDENCE, AND MD STABILITY",
                "SURFACE AND BIOLOGY FEATURES: GRAFTING COMPATIBILITY, ROS, NETS, TNF-A, IL-10, AND HEMOCOMPATIBILITY",
            ],
        ),
        (
            "4. AI SCORING ENGINE",
            PALETTE["ai"],
            [
                "MODEL A ESTIMATES BINDING AFFINITY OR RANK LIKELIHOOD",
                "MODEL B ESTIMATES ECMO SUITABILITY AFTER IMMOBILIZATION",
                "COMPOSITE SCORE = AFFINITY + SPECIFICITY + SURFACE COMPATIBILITY + IMMUNE EFFECT + SAFETY",
            ],
        ),
        (
            "5. CANDIDATE PRIORITIZATION",
            PALETTE["prioritize"],
            [
                "TOP-TIER CANDIDATES ADVANCE TO SYNTHESIS OR PURCHASE",
                "MID-TIER CANDIDATES RETURN FOR SEQUENCE, LINKER, OR SCAFFOLD OPTIMIZATION",
                "LOW-TIER CANDIDATES ARE STORED AS NEGATIVE EXAMPLES FOR MODEL LEARNING",
            ],
        ),
        (
            "6. EXPERIMENTAL VALIDATION",
            PALETTE["validation"],
            [
                "BIOPHYSICAL TESTS SUCH AS SPR, BLI, DOCKING CONFIRMATION, OR OPTIONAL MD",
                "SURFACE TESTS INCLUDING XPS, CONTACT ANGLE, LIGAND DENSITY, AND STABILITY AFTER GRAFTING",
                "BIOLOGICAL TESTS FOR ROS, NETS, CYTOKINES, M1/M2 SHIFT, HEMOLYSIS, AND PLATELET ADHESION",
            ],
        ),
        (
            "7. EVALUATION AND LABEL UPDATE",
            PALETTE["update"],
            [
                "GENERATE FINAL COMPOSITE SCORES AND DECISION LABELS: ADVANCE, SECONDARY, HOLD, OR REJECT",
                "IDENTIFY FAILURE MODES SUCH AS WEAK AFFINITY, BAD ORIENTATION, OR POOR HEMOCOMPATIBILITY",
                "USE EXPERT REVIEW TO CONFIRM WHICH CANDIDATES SHOULD MOVE TO THE NEXT ROUND",
            ],
        ),
    ]

    centers = []
    y = top
    for title, fill, items in sections:
        box(pixels, left, y, box_w, box_h, fill, title, items)
        centers.append((left + box_w // 2, y, y + box_h))
        y += box_h + gap

    loop_y = y + 20
    loop_h = 180
    box(
        pixels,
        350,
        loop_y,
        1300,
        loop_h,
        PALETTE["loop"],
        "8. ACTIVE LEARNING LOOP",
        [
            "NEW EXPERIMENTAL RESULTS UPDATE THE DATASET, REFINE THE WEIGHTS, AND GUIDE THE NEXT GENERATION OF CUSTOM LIGAND DESIGNS",
        ],
    )

    for idx in range(len(centers) - 1):
        cx = centers[idx][0]
        draw_arrow_down(pixels, cx, centers[idx][2] + 10, centers[idx + 1][1] - 10, PALETTE["arrow"])

    draw_arrow_down(pixels, centers[-1][0], centers[-1][2] + 10, loop_y - 12, PALETTE["arrow"])
    draw_arrow_polyline(
        pixels,
        [
            (350, loop_y + loop_h // 2),
            (150, loop_y + loop_h // 2),
            (150, top + box_h // 2),
            (left - 18, top + box_h // 2),
        ],
        PALETTE["accent"],
    )
    footer = "PROPOSED ARCHITECTURE FOR UNIVERSITY RESEARCH DISCUSSION"
    draw_text(pixels, footer, WIDTH // 2, HEIGHT - 46, 3, PALETTE["subtitle"], align="center")

    save_png("ecmo-ai-workflow.png", pixels)


if __name__ == "__main__":
    main()
