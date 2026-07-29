"""Emit the analysis-page figures from the committed output tables.

Writes plotly write_html-format files into figures/ so the family page
builder (report_builder.py in basketball-analysis-tools) can embed them,
swap in the famplot engine, and theme them like every other study. No
figure number is typed by hand: everything reads from output/*.csv, the
same tables the reconcile gate holds equal to the R implementation.

Run: .venv/bin/python python/09_story_figures.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

FONT = {"color": "#52514e",
        "family": "system-ui, -apple-system, Segoe UI, sans-serif",
        "size": 13}
BASE_LAYOUT = {
    "paper_bgcolor": "#fcfcfb", "plot_bgcolor": "#fcfcfb", "font": FONT,
    "xaxis": {"gridcolor": "#e1e0d9", "linecolor": "#c3c2b7"},
    "yaxis": {"gridcolor": "#e1e0d9", "linecolor": "#c3c2b7"},
    "showlegend": False, "width": 900, "height": 500,
}

TEMPLATE = """<html>
<head><meta charset="utf-8" /></head>
<body>
    <div style="height:{h}px; width:900px;"> <script>window.PlotlyConfig = {{MathJaxConfig: 'local'}};</script>
        <script charset="utf-8" src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script> <div id="{fid}" class="plotly-graph-div" style="height:100%; width:100%;"></div> <script> window.PLOTLYENV=window.PLOTLYENV || {{}}; if (document.getElementById("{fid}")) {{ Plotly.newPlot( "{fid}", {data}, {layout}, {{"responsive": true}} ) }}; </script> </div>
</body>
</html>"""


def rows(name: str) -> list[dict]:
    with (OUT / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def write(name: str, data: list[dict], layout: dict) -> None:
    lay = json.loads(json.dumps(BASE_LAYOUT))
    for k, v in layout.items():
        if isinstance(v, dict) and isinstance(lay.get(k), dict):
            lay[k].update(v)
        else:
            lay[k] = v
    html = TEMPLATE.format(fid=f"fam-{name}", h=lay["height"],
                           data=json.dumps(data), layout=json.dumps(lay))
    (FIGS / f"{name}.html").write_text(html)
    print(f"wrote figures/{name}.html")


def fig1_slot_curve() -> None:
    curve = rows("pick_curve")
    write("fig1_slot_curve", [{
        "type": "scatter", "mode": "lines",
        "x": [int(r["pick"]) for r in curve],
        "y": [round(float(r["exp_ws"]), 1) for r in curve],
        "line": {"color": "#2a78d6", "width": 2},
        "hovertemplate": ("pick %{x}: %{y:.0f} expected career Win Shares"
                          "<extra></extra>"),
    }], {
        "title": {"text": "What a pick slot is worth: expected career Win"
                          " Shares, isotonic fit over picks 1-60",
                  "font": {"color": "#0b0b0b", "size": 17}},
        "xaxis": {"title": {"text": "draft pick"}},
        "yaxis": {"title": {"text": "expected career Win Shares"}},
        "margin": {"l": 70, "r": 40, "t": 70, "b": 55},
    })


def fig2_franchises() -> None:
    teams = sorted(rows("teams"), key=lambda r: -float(r["value_ws"]))
    write("fig2_franchises", [{
        "type": "bar", "orientation": "h",
        "y": [r["team"] for r in teams],
        "x": [round(float(r["value_ws"]), 1) for r in teams],
        "customdata": [[round(float(r["ci_lo"])), round(float(r["ci_hi"])),
                        r["picks"], round(float(r["kept_share"]) * 100)]
                       for r in teams],
        "marker": {"color": "#2a78d6", "line": {"color": "white",
                                                "width": 1}},
        "hovertemplate": ("%{y}: %{x:.0f} WS above slot over"
                          " %{customdata[2]} picks<br>95%% interval"
                          " %{customdata[0]} to %{customdata[1]} &middot;"
                          " kept %{customdata[3]}%% of drafted minutes"
                          "<extra></extra>"),
    }], {
        "title": {"text": "Career Win Shares above slot expectation by"
                          " drafting franchise, classes 1989-2015",
                  "font": {"color": "#0b0b0b", "size": 17}},
        "xaxis": {"title": {"text": "WS above slot expectation"}},
        "yaxis": {"autorange": "reversed",
                  "tickfont": {"size": 10}, "title": {"text": ""}},
        "margin": {"l": 190, "r": 40, "t": 70, "b": 55},
        "height": 640,
    })


def fig3_colleges() -> None:
    colleges = sorted(rows("colleges"),
                      key=lambda r: -float(r["value_ws"]))[:12]
    write("fig3_colleges", [{
        "type": "bar", "orientation": "h",
        "y": [r["college"] for r in colleges],
        "x": [round(float(r["value_ws"]), 1) for r in colleges],
        "customdata": [[r["draftees"], r["hits"],
                        round(float(r["hit_rate"]) * 100)]
                       for r in colleges],
        "marker": {"color": "#eb6834", "line": {"color": "white",
                                                "width": 1}},
        "hovertemplate": ("%{y}: %{x:.0f} WS above slot<br>%{customdata[0]}"
                          " draftees, %{customdata[1]} hits"
                          " (%{customdata[2]}%% became 10,000-minute"
                          " players)<extra></extra>"),
    }], {
        "title": {"text": "Colleges whose draftees most outplayed their"
                          " slots (8+ draftees, 1989-2015)",
                  "font": {"color": "#0b0b0b", "size": 17}},
        "xaxis": {"title": {"text": "WS above slot expectation"}},
        "yaxis": {"autorange": "reversed",
                  "tickfont": {"size": 11}, "title": {"text": ""}},
        "margin": {"l": 190, "r": 40, "t": 70, "b": 55},
        "height": 520,
    })


if __name__ == "__main__":
    fig1_slot_curve()
    fig2_franchises()
    fig3_colleges()
