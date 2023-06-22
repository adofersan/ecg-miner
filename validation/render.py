# Standard library imports
import io
from math import ceil
import re
from typing import Iterable, Tuple

# Third-party imports
import cv2 as cv
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
from PIL import ImageFont, ImageDraw, Image


def render(
    ecg: Iterable[Iterable[float]],
    path: str,
    layout: Tuple[int, int] = (3, 4),
    rhythm: Iterable[str] = ["II"],
    cabrera: bool = False,
    sample_rate: int = 500,
    ref_pulse_at_right: bool = True,
    show_lead_names: bool = True,
    show_lead_sep: bool = True,
    metadata: dict = None,
):
    # Dimension constants
    PERIOD = 1 / sample_rate
    ROW_HEIGHT = 6
    LINE_WIDTH = 0.5
    SQUARES = 5

    # Formats
    STANDARD = [
        "I",
        "II",
        "III",
        "aVR",
        "aVL",
        "aVF",
        "V1",
        "V2",
        "V3",
        "V4",
        "V5",
        "V6",
    ]
    CABRERA = [
        "aVL",
        "I",
        "aVR",
        "II",
        "aVF",
        "III",
        "V1",
        "V2",
        "V3",
        "V4",
        "V5",
        "V6",
    ]

    # Color constants
    COL_MAJOR = "#FF0000"
    COL_MINOR = "#FFB3B3"
    COL_LINE = "#000000"
    max_rows = layout[0] + len(rhythm)
    max_cols = layout[1]
    lead_time = (ecg.shape[0] / sample_rate) / max_cols

    # Axis bounds
    x_min = 0 - 0.04 * 8 * (1 - ref_pulse_at_right)
    x_max = max_cols * lead_time + 0.04 * 8 * ref_pulse_at_right
    y_min = ROW_HEIGHT / 4 - (max_rows / 2) * ROW_HEIGHT
    y_max = ROW_HEIGHT / 2.5

    plt.ioff()
    fig, ax = plt.subplots(
        figsize=(max_cols * lead_time, max_rows * ROW_HEIGHT / SQUARES)
    )
    fig.subplots_adjust(
        left=0,
        right=1,
        bottom=0,
        top=1,
        wspace=0,
        hspace=0,
    )
    # Ax lims
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    # Ax ticks
    ax.set_xticks(np.arange(x_min, x_max, 0.2))
    ax.set_yticks(np.arange(y_min, y_max, 0.5))
    # Ax grid
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(AutoMinorLocator(SQUARES))

    ax.grid(which="major", linewidth=LINE_WIDTH, ls="-", color=COL_MAJOR)
    ax.grid(which="minor", linewidth=LINE_WIDTH, ls="-", color=COL_MINOR)
    # Draw 12-lead ECG

    leads = CABRERA if cabrera else STANDARD
    for i, lead in enumerate(leads + rhythm):
        is_rhythm = i >= 12
        r = i % layout[0] if not is_rhythm else layout[0] + rhythm.index(lead)

        c_num = 1 if is_rhythm else layout[1]
        c = 0 if is_rhythm else i // layout[0]
        y_offset = -(ROW_HEIGHT / 2) * ceil(r % max_rows)
        x_offset = lead_time * c
        # Lead sep
        if show_lead_sep:
            __plot_lead_sep(
                ax,
                x_offset=x_offset
                + lead_time * (max_cols + 1 - c_num) * ref_pulse_at_right,
                y_offset=y_offset,
                linewidth=LINE_WIDTH * 2,
                color=COL_LINE,
            )
        # Lead names
        if show_lead_names:
            lead
            ax.text(
                x_offset + 0.1,
                y_offset + 0.5,
                ("-" if (lead == "aVR" and cabrera) else "") + lead,
                fontsize=9,
                family="serif",
            )
        # Signal
        total_data = ecg[lead]
        data_len = len(total_data) // c_num
        y = total_data.iloc[data_len * c : data_len * (c + 1)]
        y = -y if (lead == "aVR" and cabrera) else y
        x = np.arange(0, len(y) * PERIOD, PERIOD) + x_offset
        y = y + y_offset
        ax.plot(x, y, linewidth=LINE_WIDTH, color=COL_LINE)
        # Ref pulse
        __plot_ref_pulse(
            ax,
            x_offset=lead_time * max_cols if ref_pulse_at_right else x_min,
            y_offset=y_offset,
            linewidth=LINE_WIDTH * 2,
            color=COL_LINE,
        )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    buf.close()
    img = cv.imdecode(img_arr, 1)
    plt.close(fig)

    if metadata is not None:
        img = __add_metadata(img, metadata)
    cv.imwrite(path, img)


def __plot_lead_sep(ax, x_offset, y_offset, linewidth, color):
    x = [x_offset, x_offset]
    y = [y_offset - 0.6, y_offset - 0.2]
    ax.plot(x, y, linewidth=linewidth, color=color)
    y = [y_offset + 0.2, y_offset + 0.6]
    ax.plot(x, y, linewidth=linewidth, color=color)


def __plot_ref_pulse(ax, x_offset, y_offset, linewidth, color):
    x = [
        x_offset,
        x_offset + 0.04,
        x_offset + 0.04,
        x_offset + 0.04 * 6,
        x_offset + 0.04 * 6,
        x_offset + 0.04 * 7,
    ]
    y = [
        y_offset,
        y_offset,
        y_offset + 1,
        y_offset + 1,
        y_offset,
        y_offset,
    ]
    ax.plot(x, y, linewidth=linewidth, color=color)


def __add_metadata(img, metadata):
    FONT = r"data\timesbd.ttf"
    EOL = "<EOL>"
    MAX_LENGTH = 150
    u = img.shape[1] // 20
    # Make border
    img = cv.copyMakeBorder(
        img,
        u * 5,
        u,
        u,
        u * 2,
        cv.BORDER_CONSTANT,
        value=[255, 255, 255],
    )
    height, widht, _ = img.shape
    img = Image.fromarray(img)
    draw = ImageDraw.Draw(img)
    # Draw title
    draw.text(
        (u, u),
        "PTB-XL REPORT",
        fill="black",
        font=ImageFont.truetype(FONT, 60),
    )
    # Draw subtitle
    draw.text(
        (u * 7, u * 1.15),
        "ECG ID: "
        + metadata["ecg_id"]
        + 7 * " "
        + "PATIENT ID: "
        + metadata["patient_id"]
        + 7 * " "
        + "DATE: "
        + metadata["recording_date"],
        fill="black",
        font=ImageFont.truetype(FONT, 45),
    )
    # Draw attributes
    loc = 2.5 * u
    attrs = ["age", "sex", "height", "weight", "nurse", "site"]
    for line in attrs:
        draw.text(
            (u, loc),
            line.capitalize() + ": " + metadata[line],
            fill="black",
            font=ImageFont.truetype(FONT, 30),
        )

        loc += 0.35 * u
    loc = 2.5 * u
    # Draw report
    report = metadata["report"]
    report = re.sub(r"(\n|\s|\t){3,}", EOL, report)
    report = re.sub(
        r"([^0-9|<EOL>])\.([^0-9|<EOL>])", r"\1" + EOL + r"\2", report
    )
    report = report.split(EOL)

    for line in report:
        if len(line) > MAX_LENGTH:
            spaces = [i for i, c in enumerate(line) if c == " "]
            mid_space = min(spaces, key=lambda c: abs(c - len(line) // 2))
            s1 = line[:mid_space]
            s2 = line[mid_space + 1 :]
            draw.text(
                (u * 4, loc),
                "· " + s1.strip().capitalize().rstrip("."),
                fill="black",
                font=ImageFont.truetype(FONT, 30),
            )
            loc += 0.35 * u
            draw.text(
                (u * 4, loc),
                "  " + s2.strip().rstrip("."),
                fill="black",
                font=ImageFont.truetype(FONT, 30),
            )
        else:
            draw.text(
                (u * 4, loc),
                "· " + line.strip().capitalize().rstrip("."),
                fill="black",
                font=ImageFont.truetype(FONT, 30),
            )
        loc += 0.35 * u

    # Draw device data
    draw.text(
        (u, height - 0.8 * u),
        "Device: " + metadata["device"],
        fill="black",
        font=ImageFont.truetype(FONT, 30),
    )
    draw.text(
        (widht - 6.6 * u, height - 0.8 * u),
        "25mm/s" + 8 * " " + " 10mm/mV " + 8 * " " + "500Hz",
        fill="black",
        font=ImageFont.truetype(FONT, 30),
    )
    img = np.asarray(img)
    return img
