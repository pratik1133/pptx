"""Generate the Jinja2 report template with embedded CSS."""
from pathlib import Path

HERE = Path(__file__).parent
css = (HERE / "base.css").read_text(encoding="utf-8")

template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ company.name }} — Equity Research | {{ theme.firm_name }}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Serif+4:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
''' + css + r'''
</style>
</head>
<body>
{% for slide in slides %}
{% if slide.layout == "cover_slide" %}
<!-- COVER PAGE -->
<div class="page">
  <div class="report-header">
    <div class="header-top">
      <div class="firm-brand">
        <div class="firm-logo">{{ theme.firm_name[0] }}</div>
        <div>
          <div class="firm-name">{{ theme.firm_name }}</div>
          <div class="firm-tagline">{{ theme.firm_tagline }}</div>
        </div>
      </div>
      <div class="report-type-badge">{{ meta.report_type }} — {{ meta.report_date.strftime("%b %Y") if meta.report_date.strftime is defined else meta.report_date }}</div>
    </div>
    <div class="header-company-line">
      <span class="company-name-hdr">{{ company.name }}</span>
      <span class="rating-badge">{{ meta.rating }}</span>
      <span class="sector-tag">{{ company.exchange }}: {{ company.ticker }} &nbsp;|&nbsp; {{ company.sector }}{% if company.industry %} / {{ company.industry }}{% endif %}</span>
    </div>
    <div class="header-stats-bar">
      <div class="hstat"><div class="hstat-label">CMP</div><div class="hstat-value">{{ cmp_str }}</div></div>
      <div class="hstat"><div class="hstat-label">Target Price</div><div class="hstat-value white">{{ tp_str }}</div></div>
      <div class="hstat"><div class="hstat-label">Upside</div><div class="hstat-value white">{{ upside_pct }}</div></div>
      {% if market_cap_str %}<div class="hstat"><div class="hstat-label">Market Cap</div><div class="hstat-value white">{{ market_cap_str }}</div></div>{% endif %}
      {% if model and model.saarthi %}<div class="hstat"><div class="hstat-label">SAARTHI Score</div><div class="hstat-value">{{ model.saarthi.total_score }}/{{ model.saarthi.max_score }}</div></div>{% endif %}
    </div>
    <div class="report-date">{{ meta.report_date }}</div>
  </div>

  {% if slide.subtitle %}<div class="tagline-band"><div class="tagline-text">"{{ slide.subtitle }}"</div></div>{% endif %}

  <div class="page-content pb48">
    {% for block in slide.blocks %}
      {% if block.type == "text" %}
      <div class="thesis-box"><p>{{ block.content }}</p></div>
      {% elif block.type == "metrics" %}
      <div class="metric-strip-{{ block.items|length }}">
        {% for item in block.items %}
        <div class="metric-card {% if loop.index % 4 == 2 %}accent-bg{% elif loop.index % 4 == 3 %}mid-bg{% elif loop.index % 4 == 0 %}teal-bg{% endif %}">
          <div class="metric-card-label">{{ item.label }}</div>
          <div class="metric-card-value">{{ item.value }}</div>
        </div>
        {% endfor %}
      </div>
      {% elif block.type == "bullets" %}
      <div class="two-col">
        {% for item in block.items %}
        <div class="highlight-box {% if loop.index % 3 == 1 %}accent-border{% elif loop.index % 3 == 2 %}navy-border{% else %}green-border{% endif %}">
          <p>{{ item }}</p>
        </div>
        {% endfor %}
      </div>
      {% endif %}
    {% endfor %}

    {% if fin_summary_rows %}
    <div class="fin-table-wrap mt8">
      <div class="fin-table-title">Financial Summary</div>
      <table>
        <thead><tr>
          <th>Metric</th>
          {% if fin_summary_rows[0]._periods is defined %}
            {% for p in fin_summary_rows[0]._periods %}<th>{{ p }}</th>{% endfor %}
          {% endif %}
        </tr></thead>
        <tbody>
          {% for row in fin_summary_rows %}
          <tr{% if "PAT" in row.label or "Net Profit" in row.label %} class="tbl-highlight"{% endif %}>
            <td>{{ row.label }}{% if row.unit %} ({{ row.unit }}){% endif %}</td>
            {% for p in row._periods %}<td>{{ row.get(p, "—") }}</td>{% endfor %}
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endif %}
  </div>

  <div class="page-footer">
    <div class="footer-left">{{ theme.footer_line }}</div>
    <div class="footer-center">{{ company.name }} — Equity Research</div>
    <div class="footer-right">Page {{ slide.page_number }} of {{ total_pages }}</div>
  </div>
</div>

{% else %}
<!-- INTERIOR PAGE: {{ slide.layout }} -->
<div class="page">
  <div class="mini-header">
    <div class="mini-firm">{{ theme.firm_name }}</div>
    <div class="mini-company">{{ company.name }} — {{ slide.title }}</div>
    <div class="mini-stats">
      <div class="mini-stat"><span class="mini-stat-label">CMP</span><span class="mini-stat-value">{{ cmp_str }}</span></div>
      <div class="mini-stat"><span class="mini-stat-label">TP</span><span class="mini-stat-value accent">{{ tp_str }}</span></div>
      <div class="mini-stat"><span class="mini-stat-label">Upside</span><span class="mini-stat-value green-v">{{ upside_pct }}</span></div>
      {% if market_cap_str %}<div class="mini-stat"><span class="mini-stat-label">Mkt Cap</span><span class="mini-stat-value">{{ market_cap_str }}</span></div>{% endif %}
      <div class="mini-stat"><span class="mini-stat-label">Rating</span><span class="mini-stat-value buy">{{ meta.rating }}</span></div>
    </div>
  </div>

  <div style="padding:10px 18px 48px;">
    <div class="section-header">
      <span class="section-number">{{ "%02d"|format(slide.page_number) }}</span>
      <span class="section-title">{{ slide.title }}</span>
    </div>

    {% if slide.subtitle %}
    <div class="thesis-box mb8"><p>{{ slide.subtitle }}</p></div>
    {% endif %}

    {% for block in slide.blocks %}

      {% if block.type == "text" %}
      <div class="analysis-block"><p>{{ block.content }}</p></div>

      {% elif block.type == "bullets" %}
      <div class="analysis-block">
        <ul>{% for item in block.items %}<li>{{ item }}</li>{% endfor %}</ul>
      </div>

      {% elif block.type == "metrics" %}
      <div class="metric-strip-{{ block.items|length }} mb10">
        {% for item in block.items %}
        <div class="metric-card {% if loop.index % 4 == 2 %}accent-bg{% elif loop.index % 4 == 3 %}mid-bg{% elif loop.index % 4 == 0 %}teal-bg{% endif %}">
          <div class="metric-card-label">{{ item.label }}</div>
          <div class="metric-card-value">{{ item.value }}</div>
        </div>
        {% endfor %}
      </div>

      {% elif block.type == "chart" %}
      <div style="border:1px solid #d5dce8;border-radius:4px;padding:8px;margin-bottom:10px;">
        <div class="figure-title">{{ block.title }}</div>
        {{ block.svg_html }}
        <div class="figure-source">Source: {{ theme.firm_name }} model</div>
      </div>

      {% elif block.type == "table" %}
      <div class="fin-table-wrap mb8">
        <div class="fin-table-title">{{ block.title }}</div>
        <table>
          <thead><tr>
            {% for col in block.columns %}<th>{{ col.label }}</th>{% endfor %}
          </tr></thead>
          <tbody>
            {% for row in block.rows %}
            <tr{% if loop.index is odd %} style="background:#f4f6f9;"{% endif %}>
              {% for col in block.columns %}
              {% set val = row.get(col.key, "—") if row.get is defined else row[col.key] if col.key in row else "—" %}
              <td{% if loop.first %} style="font-weight:500;color:#3a4d6b;"{% endif %}{% if val is string and val.startswith("+") %} class="green"{% elif val is string and val.startswith("-") %} class="red"{% endif %}>{{ val }}</td>
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>

      {% endif %}
    {% endfor %}

    {# --- Special layout enrichments from financial model --- #}

    {% if slide.layout == "saarthi_scorecard" and model and model.saarthi %}
    <div class="mb8" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
      {% for dim in model.saarthi.dimensions %}
      <div class="score-item">
        <div class="score-header">
          <span class="score-name">{{ dim.name }}</span>
          <span class="score-val">{{ dim.score }}/{{ dim.max_score }}</span>
        </div>
        <div class="score-bar-bg"><div class="score-bar-fill" style="width:{{ (dim.score / dim.max_score * 100)|int }}%;background:{% if dim.score / dim.max_score >= 0.8 %}#1a7a4a{% elif dim.score / dim.max_score >= 0.6 %}#FFA500{% else %}#b91c1c{% endif %};"></div></div>
        {% if dim.key_evidence %}<div class="score-desc">{{ dim.key_evidence }}</div>{% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {% if slide.layout == "management_profile" and model and model.management_team %}
    <div class="mb8">
      {% for m in model.management_team %}
      <div class="mgmt-row">
        <div class="mgmt-name">{{ m.name }}</div>
        <div class="mgmt-role">{{ m.role }}</div>
        <div class="mgmt-bio">{{ m.bio }}</div>
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {% if slide.layout in ["valuation_summary", "valuation_table"] and model and model.scenarios %}
    <div class="scenario-grid mb8">
      {% for sc in model.scenarios %}
      <div class="scenario-card {% if 'bear' in sc.name|lower %}bear{% elif 'bull' in sc.name|lower %}bull{% else %}base{% endif %}">
        <div class="scenario-label">{{ sc.name }}</div>
        <div class="scenario-tp">₹{{ sc.target_price|int if sc.target_price else "—" }}</div>
        {% if sc.probability_pct %}<div class="scenario-updown">{{ sc.probability_pct }}% probability</div>{% endif %}
        {% if sc.notes %}<div class="scenario-desc">{{ sc.notes }}</div>{% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {% if slide.layout == "segment_mix" and model and model.segments %}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;" class="mb8">
      {% for seg in model.segments %}
      <div class="segment-card">
        <div class="segment-card-header">
          <span class="segment-name">{{ seg.name }}</span>
          {% if seg.revenue_share_pct %}<span class="segment-share">{{ seg.revenue_share_pct }}% Rev</span>{% endif %}
        </div>
        {% if seg.aum_or_book_label %}<div class="segment-kpi"><span class="kpi-chip">{{ seg.aum_or_book_label }}: {{ seg.aum_or_book_value }}</span></div>{% endif %}
        {% if seg.description %}<div class="segment-desc">{{ seg.description }}</div>{% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {% if slide.layout == "risks_and_catalysts" %}
    <div class="mb8">
      {% for block in slide.blocks %}
        {% if block.type == "bullets" %}
          {% for item in block.items %}
          <div class="risk-item">
            <div class="risk-badge risk-med">RISK</div>
            <div><div class="risk-title">{{ item[:60] }}{% if item|length > 60 %}...{% endif %}</div><div class="risk-text">{{ item }}</div></div>
          </div>
          {% endfor %}
        {% endif %}
      {% endfor %}
    </div>
    {% endif %}

    {% if slide.layout == "disclaimer" or slide.layout == "analyst_certification" %}
    <div class="disclaimer">
      {% for block in slide.blocks %}{% if block.type == "text" %}{{ block.content|replace("\n\n", "</p><p>")|replace("\n", "<br>") }}{% endif %}{% endfor %}
    </div>
    {% endif %}

  </div>

  <div class="page-footer">
    <div class="footer-left">{{ theme.footer_line }}</div>
    <div class="footer-center">{{ company.name }} — Equity Research</div>
    <div class="footer-right">{{ meta.report_date }} | Page {{ slide.page_number }} of {{ total_pages }}</div>
  </div>
</div>
{% endif %}
{% endfor %}
</body>
</html>
'''

out = HERE / "report.html.j2"
out.write_text(template, encoding="utf-8")
print(f"Wrote report.html.j2 ({len(template)} chars)")
