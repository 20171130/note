#!/usr/bin/env python3
"""Render the Continuous Token Transformer in-token AR head diagram to SVG."""

import drawsvg as dw

# ----- Layout (px) -----
W, H = 900, 250
MAIN_Y = 190
BOX_H = 36
BOX_PAD_X = 14
BOX_GAP = 10
CHAR_W = 8

INNER_Y = 70
INNER_BOX_W = 96
INNER_BOX_H = 44
INNER_BOX_GAP = 14
INNER_CONTAINER_PAD = 12

STROKE = "#222"
FILL_TEXT = "#ffffff"
FILL_NUM = "#fff3cf"
CONTAINER_FILL = "#f4f4f4"
FONT = "Helvetica, Arial, sans-serif"
FONT_SIZE = 14
INNER_FONT_SIZE = 12


def label_width(text):
    return max(60, len(text) * CHAR_W + 2 * BOX_PAD_X)


main_tokens = [
    ("'one'", False),
    ("' inch'", False),
    ("' is'", False),
    ("'<scalar_token>'", True),
    ("' cm'", False),
    ("'.'", False),
]

widths = [label_width(t) for t, _ in main_tokens]
total_main_w = sum(widths) + (len(widths) - 1) * BOX_GAP
x_start = (W - total_main_w) / 2
xs, x = [], x_start
for w in widths:
    xs.append(x)
    x += w + BOX_GAP

st_idx = next(i for i, (_, n) in enumerate(main_tokens) if n)
ST_X_CENTER = xs[st_idx] + widths[st_idx] / 2
ST_TOP_Y = MAIN_Y - BOX_H / 2

inner_labels = [
    ("sign", "1 bit"),
    ("exponent", "11 bits"),
    ("mantissa", "52 bits"),
]
inner_total_w = len(inner_labels) * INNER_BOX_W + (len(inner_labels) - 1) * INNER_BOX_GAP
inner_x_start = ST_X_CENTER - inner_total_w / 2
inner_xs = [inner_x_start + i * (INNER_BOX_W + INNER_BOX_GAP) for i in range(len(inner_labels))]

CONTAINER_X = inner_x_start - INNER_CONTAINER_PAD
CONTAINER_Y = INNER_Y - INNER_BOX_H / 2 - INNER_CONTAINER_PAD - 16
CONTAINER_W = inner_total_w + 2 * INNER_CONTAINER_PAD
CONTAINER_H = INNER_BOX_H + 2 * INNER_CONTAINER_PAD + 16
CONTAINER_BOTTOM_Y = CONTAINER_Y + CONTAINER_H


d = dw.Drawing(W, H, origin=(0, 0))

# Arrowhead marker (solid)
arrow = dw.Marker(-1, -3, 8, 3, scale=2, orient="auto", id="arrow")
arrow.append(dw.Path(fill=STROKE).M(-1, -3).L(7, 0).L(-1, 3).Z())
d.append(arrow)

# Container
d.append(dw.Rectangle(
    CONTAINER_X, CONTAINER_Y, CONTAINER_W, CONTAINER_H,
    rx=8, ry=8, fill=CONTAINER_FILL, stroke=STROKE, stroke_width=1,
))
d.append(dw.Text(
    "inner AR head", INNER_FONT_SIZE - 1,
    x=CONTAINER_X + 8, y=CONTAINER_Y + 14,
    font_family=FONT, fill="#555",
))

# Inner-AR boxes
for (lab, sub), bx in zip(inner_labels, inner_xs):
    by = INNER_Y - INNER_BOX_H / 2
    d.append(dw.Rectangle(
        bx, by, INNER_BOX_W, INNER_BOX_H,
        rx=4, ry=4, fill=FILL_NUM, stroke=STROKE, stroke_width=1.2,
    ))
    cx = bx + INNER_BOX_W / 2
    d.append(dw.Text(lab, INNER_FONT_SIZE, x=cx, y=INNER_Y - 2,
                     font_family=FONT, text_anchor="middle"))
    d.append(dw.Text(sub, INNER_FONT_SIZE - 1, x=cx, y=INNER_Y + 14,
                     font_family=FONT, fill="#555", text_anchor="middle"))

# Inner-AR horizontal arrows
for i in range(len(inner_labels) - 1):
    s = inner_xs[i] + INNER_BOX_W
    t = inner_xs[i + 1]
    d.append(dw.Line(s, INNER_Y, t - 7, INNER_Y,
                     stroke=STROKE, stroke_width=1.4,
                     marker_end=arrow))

# Main-chain boxes
for (lab, is_num), bx, bw in zip(main_tokens, xs, widths):
    by = MAIN_Y - BOX_H / 2
    fill = FILL_NUM if is_num else FILL_TEXT
    d.append(dw.Rectangle(bx, by, bw, BOX_H,
                          rx=4, ry=4, fill=fill,
                          stroke=STROKE, stroke_width=1.2))
    d.append(dw.Text(lab, FONT_SIZE, x=bx + bw / 2, y=MAIN_Y + 5,
                     font_family=FONT, text_anchor="middle"))

# Main-chain horizontal arrows
for i in range(len(main_tokens) - 1):
    s = xs[i] + widths[i]
    t = xs[i + 1]
    d.append(dw.Line(s, MAIN_Y, t - 7, MAIN_Y,
                     stroke=STROKE, stroke_width=1.4,
                     marker_end=arrow))

# Perpendicular dashed branch from ST top to container bottom
d.append(dw.Line(
    ST_X_CENTER, ST_TOP_Y,
    ST_X_CENTER, CONTAINER_BOTTOM_Y + 1,
    stroke=STROKE, stroke_width=1.4,
    stroke_dasharray="4 4",
    marker_start=arrow,
))

out = "/Users/hangrui/Desktop/note/image/continuous_token_head.svg"
d.save_svg(out)
print(f"wrote {out}")
