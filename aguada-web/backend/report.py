# backend/report.py
"""Geração de relatório HTML + PDF com WeasyPrint."""
from __future__ import annotations
import aiosqlite
from .db import get_all_states, get_readings_for_date
from .calc import calc_consumption_events


def _build_html(date: str, reservoirs: list[dict]) -> str:
    rows_html = ""
    alerts_html = ""

    for r in reservoirs:
        alias = r.get("alias", "")
        name = r.get("name", "")
        pct = r.get("pct") or 0
        level = r.get("level_cm") or 0
        volume = r.get("volume_l") or 0
        volume_max = r.get("volume_max_l") or 1
        events = r.get("events", [])
        consumed = sum(abs(e["delta_l"]) for e in events if e["type"] == "consumption")
        supplied = sum(e["delta_l"] for e in events if e["type"] == "supply")
        color = "#16a34a" if pct >= 80 else "#2563eb" if pct >= 50 else "#d97706" if pct >= 20 else "#dc2626"

        rows_html += f"""
        <tr>
          <td><strong>{alias}</strong></td>
          <td>{name}</td>
          <td style="color:{color};font-weight:bold">{pct:.1f}%</td>
          <td>{level:.0f} cm</td>
          <td>{volume:,.0f} L / {volume_max:,.0f} L</td>
          <td style="color:#dc2626">-{consumed:,.0f} L</td>
          <td style="color:#16a34a">+{supplied:,.0f} L</td>
        </tr>"""

        if pct < 20:
            alerts_html += f'<li style="color:#dc2626">⚠️ {alias} ({name}) abaixo de 20%: {pct:.1f}%</li>'

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; margin: 30px; color: #1e293b; }}
    h1 {{ color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 8px; }}
    h2 {{ color: #374151; margin-top: 24px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th {{ background: #1e40af; color: white; padding: 8px 12px; text-align: left; font-size: 12px; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    .alerts {{ background: #fef2f2; border: 1px solid #fca5a5; border-radius: 6px; padding: 12px; margin-top: 16px; }}
    .footer {{ margin-top: 40px; font-size: 11px; color: #94a3b8; text-align: center; }}
  </style>
</head>
<body>
  <h1>💧 CMASM — Aguada — Relatório Diário</h1>
  <p><strong>Data:</strong> {date} &nbsp;|&nbsp; <strong>Sistema:</strong> Aguada Web v1.0</p>

  <h2>Resumo dos Reservatórios</h2>
  <table>
    <thead>
      <tr>
        <th>Alias</th><th>Reservatório</th><th>Nível %</th>
        <th>Nível cm</th><th>Volume</th><th>Consumo 24h</th><th>Abastec. 24h</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>

  {"<div class='alerts'><h3>⚠️ Alertas</h3><ul>" + alerts_html + "</ul></div>" if alerts_html else ""}

  <div class="footer">Gerado automaticamente por Aguada Web — CMASM Ilha do Engenho</div>
</body>
</html>"""


async def generate_daily_report_pdf(
    conn: aiosqlite.Connection, date: str, out_path: str
) -> None:
    from weasyprint import HTML
    states = await get_all_states(conn)
    enriched = []
    for s in states:
        readings = await get_readings_for_date(conn, alias=s["alias"], date_str=date)
        events = calc_consumption_events(readings, date=date) if readings else []
        enriched.append({**s, "events": events})

    html = _build_html(date, enriched)
    HTML(string=html).write_pdf(out_path)
