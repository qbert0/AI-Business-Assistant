import html
import json
import math
import re
from typing import Any


CHART_COLORS = ["#1769e0", "#0f9d58", "#f29900", "#d93025", "#7b61ff", "#0b7285"]
SVG_WIDTH = 720
SVG_HEIGHT = 380
CHART_FENCE_PATTERN = re.compile(r"```chart\s*\n(.*?)\n```", flags=re.DOTALL)


def _escape_html(value: str) -> str:
    return html.escape(value or "", quote=True)


def _clean_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and math.isfinite(value):
        return str(value)
    return ""


def _format_markdown_content(md_content: str) -> str:
    content = md_content or ""
    content = re.sub(r"\n(\[\d+\]\s+)", r"\n\n\1", content)
    content = re.sub(r"(https?://[^\s]+)\s+(\[\d+\]\s+)", r"\1\n\n\2", content)
    content = re.sub(r"(\.\s+)(\[\d+\]\s+)", r"\1\n\n\2", content)

    citation_run_pattern = re.compile(r"(?:\[\d+\]\s*){2,}")

    def _dedupe_citation_run(match: re.Match[str]) -> str:
        citation_run = match.group(0)
        seen: set[str] = set()
        ordered: list[str] = []
        for citation in re.findall(r"\[\d+\]", citation_run):
            if citation not in seen:
                seen.add(citation)
                ordered.append(citation)
        return "".join(ordered) + (" " if citation_run.endswith(" ") else "")

    return citation_run_pattern.sub(_dedupe_citation_run, content)


def _slugify(value: str, separator: str) -> str:
    normalized = re.sub(r"[^\w\s-]", "", value or "", flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", separator, normalized).strip(separator)


def _ellipse(value: str, limit: int = 18) -> str:
    if len(value or "") <= limit:
        return value
    return (value or "")[: max(0, limit - 1)].rstrip() + "…"


def _to_chart_color(value: Any, index: int) -> str:
    raw = _clean_text(value)
    if re.match(r"^#([0-9a-f]{3}|[0-9a-f]{6})$", raw, flags=re.IGNORECASE):
        return raw
    return CHART_COLORS[index % len(CHART_COLORS)]


def _format_full_value(value: float, fmt: str) -> str:
    if fmt == "percent":
        return f"{value:,.2f}%".replace(",", "_").replace(".", ",").replace("_", ".")
    if fmt == "currency_vnd":
        return f"{value:,.0f} VNĐ".replace(",", ".")
    if abs(value) < 100:
        return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{value:,.0f}".replace(",", ".")


def _format_short_value(value: float, fmt: str) -> str:
    if fmt == "percent":
        return f"{value:,.1f}%".replace(",", "_").replace(".", ",").replace("_", ".")

    abs_value = abs(value)
    scaled = value
    suffix = ""
    if abs_value >= 1_000_000_000:
        scaled = value / 1_000_000_000
        suffix = "B"
    elif abs_value >= 1_000_000:
        scaled = value / 1_000_000
        suffix = "M"
    elif abs_value >= 1_000:
        scaled = value / 1_000
        suffix = "K"

    if suffix:
        formatted = f"{scaled:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")
    else:
        formatted = f"{scaled:,.0f}".replace(",", ".")
    return formatted + suffix


def _build_tick_values(min_value: float, max_value: float, steps: int = 4) -> list[float]:
    value_range = (max_value - min_value) or 1
    return [max_value - ((value_range / steps) * index) for index in range(steps + 1)]


def _value_to_y(value: float, min_value: float, max_value: float, chart_top: float, chart_height: float) -> float:
    value_range = (max_value - min_value) or 1
    normalized = (value - min_value) / value_range
    return chart_top + ((1 - normalized) * chart_height)


def _polar_to_cartesian(center_x: float, center_y: float, radius: float, angle_degrees: float) -> tuple[float, float]:
    angle_radians = math.radians(angle_degrees - 90)
    return (
        center_x + (radius * math.cos(angle_radians)),
        center_y + (radius * math.sin(angle_radians)),
    )


def _describe_arc(center_x: float, center_y: float, radius: float, start_angle: float, end_angle: float) -> str:
    start_x, start_y = _polar_to_cartesian(center_x, center_y, radius, end_angle)
    end_x, end_y = _polar_to_cartesian(center_x, center_y, radius, start_angle)
    large_arc_flag = "0" if end_angle - start_angle <= 180 else "1"
    return (
        f"M {center_x} {center_y} "
        f"L {start_x} {start_y} "
        f"A {radius} {radius} 0 {large_arc_flag} 0 {end_x} {end_y} Z"
    )


def _normalize_chart_spec(raw_spec: dict[str, Any]) -> dict[str, Any] | None:
    chart_type = _clean_text(raw_spec.get("type")).lower()
    if chart_type not in {"bar", "line", "pie"}:
        return None

    raw_categories = raw_spec.get("categories")
    categories = [_clean_text(item) for item in raw_categories] if isinstance(raw_categories, list) else []
    categories = [item for item in categories if item][:8]

    raw_series = raw_spec.get("series")
    if not isinstance(raw_series, list) or not raw_series:
        return None

    series: list[dict[str, Any]] = []
    for index, item in enumerate(raw_series[: (1 if chart_type == "pie" else 2)]):
        if not isinstance(item, dict):
            continue
        raw_data = item.get("data")
        if not isinstance(raw_data, list):
            continue
        data = [float(value) for value in raw_data if isinstance(value, (int, float)) and math.isfinite(value)][:8]
        if not data:
            continue
        series.append(
            {
                "name": _clean_text(item.get("name")) or f"Series {index + 1}",
                "data": data,
                "color": _to_chart_color(item.get("color"), index),
            }
        )
    if not series:
        return None

    longest_series = max(len(item["data"]) for item in series)
    if not categories:
        categories = [f"Mục {index + 1}" for index in range(longest_series)]
    categories = categories[:longest_series]

    if chart_type != "pie" and len(categories) < 2:
        return None
    if chart_type == "pie" and len(categories) != len(series[0]["data"]):
        return None

    chart_format = _clean_text(raw_spec.get("format"))
    if chart_format not in {"number", "currency_vnd", "percent"}:
        chart_format = "number"

    return {
        "type": chart_type,
        "title": _clean_text(raw_spec.get("title")) or "Biểu đồ dữ liệu",
        "xLabel": _clean_text(raw_spec.get("xLabel")),
        "yLabel": _clean_text(raw_spec.get("yLabel")),
        "categories": categories,
        "series": [{**item, "data": item["data"][: len(categories)]} for item in series],
        "format": chart_format,
        "note": _clean_text(raw_spec.get("note")),
    }


def _render_legend(items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    inner = "".join(
        (
            "<div class=\"report-chart__legend-item\">"
            f"<span class=\"report-chart__legend-swatch\" style=\"background:{_escape_html(item['color'])}\"></span>"
            f"<span class=\"report-chart__legend-label\">{_escape_html(item['label'])}</span>"
            + (
                f"<span class=\"report-chart__legend-value\">{_escape_html(item['value'])}</span>"
                if item.get("value")
                else ""
            )
            + "</div>"
        )
        for item in items
    )
    return f"<div class=\"report-chart__legend\">{inner}</div>"


def _render_meta(spec: dict[str, Any]) -> str:
    meta_parts: list[str] = []
    if spec.get("xLabel"):
        meta_parts.append(f"<span><strong>Trục X:</strong> {_escape_html(spec['xLabel'])}</span>")
    if spec.get("yLabel"):
        meta_parts.append(f"<span><strong>Trục Y:</strong> {_escape_html(spec['yLabel'])}</span>")
    if not meta_parts and not spec.get("note"):
        return ""

    meta_html = f"<div class=\"report-chart__meta\">{''.join(meta_parts)}</div>" if meta_parts else ""
    note_html = f"<p class=\"report-chart__note\">{_escape_html(spec['note'])}</p>" if spec.get("note") else ""
    return f"<div class=\"report-chart__footer\">{meta_html}{note_html}</div>"


def _render_bar_chart(spec: dict[str, Any]) -> str:
    margin = {"top": 28, "right": 24, "bottom": 76, "left": 72}
    chart_width = SVG_WIDTH - margin["left"] - margin["right"]
    chart_height = SVG_HEIGHT - margin["top"] - margin["bottom"]
    chart_left = margin["left"]
    chart_top = margin["top"]
    chart_bottom = chart_top + chart_height
    values = [value for series in spec["series"] for value in series["data"]]
    min_value = min([0.0, *values])
    max_value = max([0.0, *values, 1.0])
    zero_line_y = _value_to_y(0, min_value, max_value, chart_top, chart_height)
    tick_values = _build_tick_values(min_value, max_value)
    group_width = chart_width / len(spec["categories"])
    series_gap = 6 if len(spec["series"]) > 1 else 0
    inner_width = max(22, group_width - 20)
    bar_width = max(12, min(42, (inner_width - (series_gap * (len(spec["series"]) - 1))) / len(spec["series"])))

    grid_html = "".join(
        (
            f"<line x1=\"{chart_left}\" y1=\"{y}\" x2=\"{chart_left + chart_width}\" y2=\"{y}\" class=\"report-chart__grid\" />"
            f"<text x=\"{chart_left - 12}\" y=\"{y + 4}\" class=\"report-chart__tick\" text-anchor=\"end\">{_escape_html(_format_short_value(tick, spec['format']))}</text>"
        )
        for tick in tick_values
        for y in [_value_to_y(tick, min_value, max_value, chart_top, chart_height)]
    )

    bar_groups: list[str] = []
    for category_index, label in enumerate(spec["categories"]):
        group_x = chart_left + (category_index * group_width)
        total_bars_width = (len(spec["series"]) * bar_width) + ((len(spec["series"]) - 1) * series_gap)
        start_x = group_x + ((group_width - total_bars_width) / 2)
        series_bars: list[str] = []
        for series_index, series in enumerate(spec["series"]):
            value = series["data"][category_index] if category_index < len(series["data"]) else 0
            x = start_x + (series_index * (bar_width + series_gap))
            y = _value_to_y(value, min_value, max_value, chart_top, chart_height) if value >= 0 else zero_line_y
            height = max(2, abs(_value_to_y(value, min_value, max_value, chart_top, chart_height) - zero_line_y))
            title = _escape_html(f"{series['name']} - {label}: {_format_full_value(value, spec['format'])}")
            series_bars.append(
                f"<rect x=\"{x}\" y=\"{y}\" width=\"{bar_width}\" height=\"{height}\" rx=\"6\" fill=\"{_escape_html(series['color'])}\"><title>{title}</title></rect>"
            )
        bar_groups.append(
            "".join(series_bars)
            + f"<text x=\"{group_x + (group_width / 2)}\" y=\"{chart_bottom + 22}\" class=\"report-chart__label\" text-anchor=\"middle\">{_escape_html(_ellipse(label))}</text>"
        )

    legend = _render_legend([{"color": item["color"], "label": item["name"]} for item in spec["series"]]) if len(spec["series"]) > 1 else ""
    return (
        "<figure class=\"report-chart\">"
        f"<div class=\"report-chart__header\"><h4 class=\"report-chart__title\">{_escape_html(spec['title'])}</h4></div>"
        "<div class=\"report-chart__body\">"
        f"<svg class=\"report-chart__svg\" viewBox=\"0 0 {SVG_WIDTH} {SVG_HEIGHT}\" role=\"img\" aria-label=\"{_escape_html(spec['title'])}\">"
        f"{grid_html}"
        f"<line x1=\"{chart_left}\" y1=\"{zero_line_y}\" x2=\"{chart_left + chart_width}\" y2=\"{zero_line_y}\" class=\"report-chart__axis\" />"
        f"<line x1=\"{chart_left}\" y1=\"{chart_top}\" x2=\"{chart_left}\" y2=\"{chart_bottom}\" class=\"report-chart__axis\" />"
        f"{''.join(bar_groups)}"
        "</svg></div>"
        f"{legend}{_render_meta(spec)}</figure>"
    )


def _render_line_chart(spec: dict[str, Any]) -> str:
    margin = {"top": 28, "right": 24, "bottom": 76, "left": 72}
    chart_width = SVG_WIDTH - margin["left"] - margin["right"]
    chart_height = SVG_HEIGHT - margin["top"] - margin["bottom"]
    chart_left = margin["left"]
    chart_top = margin["top"]
    chart_bottom = chart_top + chart_height
    values = [value for series in spec["series"] for value in series["data"]]
    min_value = min([0.0, *values])
    max_value = max([*values, 1.0])
    tick_values = _build_tick_values(min_value, max_value)
    step_x = chart_width / max(1, len(spec["categories"]) - 1)

    grid_html = "".join(
        (
            f"<line x1=\"{chart_left}\" y1=\"{y}\" x2=\"{chart_left + chart_width}\" y2=\"{y}\" class=\"report-chart__grid\" />"
            f"<text x=\"{chart_left - 12}\" y=\"{y + 4}\" class=\"report-chart__tick\" text-anchor=\"end\">{_escape_html(_format_short_value(tick, spec['format']))}</text>"
        )
        for tick in tick_values
        for y in [_value_to_y(tick, min_value, max_value, chart_top, chart_height)]
    )

    series_html: list[str] = []
    for series in spec["series"]:
        points: list[tuple[float, float, float, str]] = []
        for index, value in enumerate(series["data"]):
            x = chart_left + (index * step_x)
            y = _value_to_y(value, min_value, max_value, chart_top, chart_height)
            points.append((x, y, value, spec["categories"][index] if index < len(spec["categories"]) else ""))
        polyline = " ".join(f"{x},{y}" for x, y, _value, _label in points)
        circles = "".join(
            (
                f"<circle cx=\"{x}\" cy=\"{y}\" r=\"4.5\" fill=\"{_escape_html(series['color'])}\">"
                f"<title>{_escape_html(series['name'] + ' - ' + label + ': ' + _format_full_value(value, spec['format']))}</title>"
                "</circle>"
            )
            for x, y, value, label in points
        )
        series_html.append(
            f"<polyline points=\"{polyline}\" fill=\"none\" stroke=\"{_escape_html(series['color'])}\" stroke-width=\"3.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\" />"
            + circles
        )

    x_labels = "".join(
        f"<text x=\"{chart_left + (index * step_x)}\" y=\"{chart_bottom + 22}\" class=\"report-chart__label\" text-anchor=\"middle\">{_escape_html(_ellipse(label))}</text>"
        for index, label in enumerate(spec["categories"])
    )
    legend = _render_legend([{"color": item["color"], "label": item["name"]} for item in spec["series"]])
    return (
        "<figure class=\"report-chart\">"
        f"<div class=\"report-chart__header\"><h4 class=\"report-chart__title\">{_escape_html(spec['title'])}</h4></div>"
        "<div class=\"report-chart__body\">"
        f"<svg class=\"report-chart__svg\" viewBox=\"0 0 {SVG_WIDTH} {SVG_HEIGHT}\" role=\"img\" aria-label=\"{_escape_html(spec['title'])}\">"
        f"{grid_html}"
        f"<line x1=\"{chart_left}\" y1=\"{chart_bottom}\" x2=\"{chart_left + chart_width}\" y2=\"{chart_bottom}\" class=\"report-chart__axis\" />"
        f"<line x1=\"{chart_left}\" y1=\"{chart_top}\" x2=\"{chart_left}\" y2=\"{chart_bottom}\" class=\"report-chart__axis\" />"
        f"{''.join(series_html)}{x_labels}"
        "</svg></div>"
        f"{legend}{_render_meta(spec)}</figure>"
    )


def _render_pie_chart(spec: dict[str, Any]) -> str | None:
    values = spec["series"][0]["data"]
    categories = spec["categories"][: len(values)]
    total = sum(max(0, value) for value in values)
    if not total:
        return None

    center_x = 360
    center_y = 168
    radius = 112
    current_angle = 0.0
    slices: list[str] = []
    for index, value in enumerate(values):
        slice_value = max(0, value)
        slice_angle = (slice_value / total) * 360
        start_angle = current_angle
        end_angle = current_angle + slice_angle
        current_angle = end_angle
        color = CHART_COLORS[index % len(CHART_COLORS)]
        if slice_angle >= 359.99:
            shape = f"<circle cx=\"{center_x}\" cy=\"{center_y}\" r=\"{radius}\" fill=\"{_escape_html(color)}\"></circle>"
        else:
            shape = f"<path d=\"{_describe_arc(center_x, center_y, radius, start_angle, end_angle)}\" fill=\"{_escape_html(color)}\"></path>"
        title = _escape_html(f"{categories[index]}: {_format_full_value(value, spec['format'])}")
        slices.append(f"<g><title>{title}</title>{shape}</g>")

    legend = _render_legend(
        [
            {
                "color": CHART_COLORS[index % len(CHART_COLORS)],
                "label": categories[index],
                "value": _format_full_value(value, spec["format"]),
            }
            for index, value in enumerate(values)
        ]
    )
    return (
        "<figure class=\"report-chart\">"
        f"<div class=\"report-chart__header\"><h4 class=\"report-chart__title\">{_escape_html(spec['title'])}</h4></div>"
        "<div class=\"report-chart__body\">"
        f"<svg class=\"report-chart__svg\" viewBox=\"0 0 {SVG_WIDTH} {SVG_HEIGHT}\" role=\"img\" aria-label=\"{_escape_html(spec['title'])}\">"
        f"{''.join(slices)}"
        f"<circle cx=\"{center_x}\" cy=\"{center_y}\" r=\"{radius * 0.48}\" fill=\"#ffffff\"></circle>"
        f"<text x=\"{center_x}\" y=\"{center_y - 4}\" class=\"report-chart__center-label\" text-anchor=\"middle\">Tổng</text>"
        f"<text x=\"{center_x}\" y=\"{center_y + 20}\" class=\"report-chart__center-value\" text-anchor=\"middle\">{_escape_html(_format_short_value(total, spec['format']))}</text>"
        "</svg></div>"
        f"{legend}{_render_meta(spec)}</figure>"
    )


def render_chart_spec_to_html(raw_spec: str) -> str | None:
    try:
        parsed = json.loads(raw_spec)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    spec = _normalize_chart_spec(parsed)
    if not spec:
        return None
    if spec["type"] == "bar":
        return _render_bar_chart(spec)
    if spec["type"] == "line":
        return _render_line_chart(spec)
    return _render_pie_chart(spec)


def _replace_chart_blocks(md_content: str) -> str:
    def _replacer(match: re.Match[str]) -> str:
        chart_html = render_chart_spec_to_html((match.group(1) or "").strip())
        if not chart_html:
            return ""
        return "\n\n" + chart_html + "\n\n"

    return CHART_FENCE_PATTERN.sub(_replacer, md_content or "")


def build_pdf_html(md_content: str) -> str:
    try:
        import markdown
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Python package `markdown` is required for PDF export.") from exc

    md = markdown.Markdown(
        extensions=["extra", "tables", "fenced_code", "toc", "attr_list"],
        extension_configs={
            "toc": {
                "permalink": False,
                "slugify": _slugify,
                "toc_depth": "2-4",
            }
        },
    )
    prepared_markdown = _replace_chart_blocks(_format_markdown_content(md_content))
    body_html = md.convert(prepared_markdown)
    toc_html = md.toc if getattr(md, "toc_tokens", None) else ""

    toc_section = ""
    if toc_html:
        toc_section = (
            "<section class=\"toc-page\">"
            "<h1>Mục lục</h1>"
            f"<nav class=\"toc\" role=\"doc-toc\">{toc_html}</nav>"
            "</section>"
        )

    return (
        "<!DOCTYPE html>"
        "<html lang=\"vi\">"
        "<head><meta charset=\"utf-8\"><title>Báo cáo</title></head>"
        "<body>"
        f"{toc_section}"
        f"<main class=\"document-content\">{body_html}</main>"
        "</body></html>"
    )


def build_pdf_stylesheet() -> str:
    return """
    @page {
        margin: 2cm 1.8cm 2.2cm;
        size: A4;
        @bottom-center {
            content: "";
            display: block;
            width: 100%;
            border-top: 2px solid #1f4e8c;
            margin-bottom: 0.28cm;
        }
        @bottom-right {
            content: counter(page);
            font-family: "Noto Serif", "DejaVu Serif", "Times New Roman", serif;
            font-size: 10pt;
            font-weight: 700;
            color: #1f4e8c;
        }
    }
    html {
        color: #333;
    }
    body {
        font-family: "Noto Serif", "DejaVu Serif", "Times New Roman", serif;
        font-size: 11pt;
        line-height: 1.7;
        color: #333;
        text-align: justify;
        hyphens: auto;
    }
    .toc-page {
        page-break-after: always;
    }
    .toc {
        font-size: 11pt;
        line-height: 1.5;
    }
    .toc ul {
        list-style: none;
        margin: 0.4em 0;
        padding-left: 0;
    }
    .toc ul ul {
        padding-left: 1.2em;
    }
    .toc li {
        margin: 0.25em 0;
    }
    .toc a {
        color: #1f4e8c;
        text-decoration: none;
    }
    .toc a::after {
        content: leader(".") target-counter(attr(href), page);
        color: #999;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: "Noto Serif", "DejaVu Serif", "Times New Roman", serif;
        color: #1a1a1a;
        margin-top: 1.15em;
        margin-bottom: 0.45em;
        line-height: 1.25;
        break-after: avoid;
    }
    h1 {
        font-size: 21pt;
        color: #163b68;
        border-bottom: 2px solid #2d69b3;
        padding-bottom: 10px;
        bookmark-level: 1;
    }
    h2 {
        font-size: 16pt;
        margin-top: 1.4em;
        color: #1f4e8c;
        border-left: 5px solid #4f86c6;
        padding-left: 0.55em;
        background: linear-gradient(to right, rgba(79, 134, 198, 0.12), rgba(79, 134, 198, 0));
        padding-top: 0.18em;
        padding-bottom: 0.18em;
        bookmark-level: 2;
    }
    h3 {
        font-size: 13pt;
        color: #2f5f9c;
        border-bottom: 1px solid #b9cde6;
        padding-bottom: 0.15em;
        bookmark-level: 3;
    }
    p, li {
        orphans: 3;
        widows: 3;
    }
    a {
        color: #24558f;
        text-decoration: none;
    }
    code {
        font-family: "Noto Sans Mono", "DejaVu Sans Mono", monospace;
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 4px;
        font-size: 0.92em;
    }
    pre {
        background-color: #f4f4f4;
        padding: 1em;
        border-radius: 8px;
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-wrap: anywhere;
    }
    pre, table, blockquote, img, figure {
        break-inside: avoid;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
        font-size: 10.2pt;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
        vertical-align: top;
    }
    th {
        background-color: #edf4fb;
    }
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1em auto;
    }
    hr {
        border: 0;
        border-top: 1px solid #ddd;
        margin: 1.8em 0;
    }
    blockquote {
        border-left: 4px solid #ccc;
        margin: 1.5em 0;
        padding: 0.2em 0 0.2em 1em;
        color: #555;
        font-style: italic;
        background-color: #f5f9fd;
    }
    .report-chart {
        margin: 1.25em 0 1.5em;
        border: 1px solid #d9e4f4;
        border-radius: 14px;
        overflow: hidden;
        background: #ffffff;
    }
    .report-chart__header {
        padding: 12px 18px;
        border-bottom: 1px solid #e4edf8;
        background: #f8fbff;
    }
    .report-chart__title {
        margin: 0;
        font-size: 12pt;
        color: #153f73;
        border: 0;
        padding: 0;
    }
    .report-chart__body {
        padding: 14px 18px 8px;
    }
    .report-chart__svg {
        width: 100%;
        height: auto;
        display: block;
    }
    .report-chart__grid {
        stroke: #dce7f5;
        stroke-width: 1;
        stroke-dasharray: 4 6;
    }
    .report-chart__axis {
        stroke: #7388a2;
        stroke-width: 1.4;
    }
    .report-chart__tick,
    .report-chart__label,
    .report-chart__center-label,
    .report-chart__center-value {
        fill: #425466;
        font-size: 11px;
        font-family: "DejaVu Sans", "Arial", sans-serif;
    }
    .report-chart__center-value {
        font-size: 16px;
        font-weight: 700;
    }
    .report-chart__legend {
        display: flex;
        flex-wrap: wrap;
        gap: 10px 16px;
        padding: 0 18px 14px;
    }
    .report-chart__legend-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 10pt;
        color: #32465a;
    }
    .report-chart__legend-swatch {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        display: inline-block;
    }
    .report-chart__legend-value {
        color: #5f6f82;
        font-size: 9.5pt;
    }
    .report-chart__footer {
        padding: 0 18px 16px;
        color: #4f6277;
        font-size: 9.5pt;
    }
    .report-chart__meta {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 8px;
    }
    .report-chart__note {
        margin: 0;
    }
    """


def convert_markdown_to_pdf_bytes(md_content: str, *, base_path: str | None = None) -> bytes:
    try:
        from weasyprint import CSS, HTML
        from weasyprint.text.fonts import FontConfiguration
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Python package `weasyprint` is required for PDF export.") from exc

    html_content = build_pdf_html(md_content)
    font_config = FontConfiguration()
    css = CSS(string=build_pdf_stylesheet(), font_config=font_config)
    return HTML(string=html_content, base_url=base_path).write_pdf(
        stylesheets=[css],
        font_config=font_config,
    )
