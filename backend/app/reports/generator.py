"""
CryptoScope Comprehensive Report Generator
Generates PDF, HTML, and JSON audit reports for firmware binary analyses.
Includes Executive Summary, Architecture Details, Primitive Classifications,
Protocol Patterns, Defensive Security Findings, and Scientific Caveats.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from jinja2 import Template

HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CryptoScope Security Audit Report - {{ filename }}</title>
    <style>
        :root {
            --bg: #0F1115;
            --surface: #161A21;
            --surface-2: #1D222B;
            --border: #2A303B;
            --text: #E7E9EE;
            --text-muted: #8C95A4;
            --accent: #F2A93B;
            --danger: #E5645F;
            --success: #4CC38A;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 40px;
            line-height: 1.6;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { border-bottom: 2px solid var(--border); padding-bottom: 20px; margin-bottom: 30px; }
        .title { font-size: 28px; font-weight: 700; color: var(--text); margin: 0 0 10px 0; }
        .subtitle { font-size: 14px; color: var(--text-muted); font-family: monospace; }
        .card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .card-title { font-size: 18px; font-weight: 600; margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
        .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
        .metric-box { background: var(--surface-2); padding: 16px; border-radius: 4px; border: 1px solid var(--border); }
        .metric-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }
        .metric-value { font-size: 20px; font-weight: 700; color: var(--accent); font-family: monospace; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); }
        th { background-color: var(--surface-2); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 11px; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .badge-danger { background: rgba(229, 100, 95, 0.2); color: var(--danger); border: 1px solid var(--danger); }
        .badge-warning { background: rgba(242, 169, 59, 0.2); color: var(--accent); border: 1px solid var(--accent); }
        .badge-success { background: rgba(76, 195, 138, 0.2); color: var(--success); border: 1px solid var(--success); }
        .caveat-banner {
            background: rgba(242, 169, 59, 0.1);
            border-left: 4px solid var(--accent);
            padding: 16px;
            margin-bottom: 30px;
            font-size: 13px;
            color: #E8B34A;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1 class="title">CryptoScope Defensive Security Audit</h1>
        <div class="subtitle">Binary Target: {{ filename }} | SHA-256: {{ sha256 }}</div>
    </div>

    <div class="caveat-banner">
        <strong>SCIENTIFIC CAVEAT & SCOPE:</strong> This defensive report documents machine-learning and structural 
        identification of cryptographic algorithms recovered from stripped multi-architecture machine code. 
        Static analysis reflects compiled algorithmic capability; runtime confirmation requires dynamic instrumentation.
    </div>

    <div class="card">
        <h2 class="card-title">Binary Architecture & Execution Context</h2>
        <div class="grid-4">
            <div class="metric-box"><div class="metric-label">Format</div><div class="metric-value">{{ format }}</div></div>
            <div class="metric-box"><div class="metric-label">Architecture</div><div class="metric-value">{{ isa }}</div></div>
            <div class="metric-box"><div class="metric-label">Endianness / Bits</div><div class="metric-value">{{ endianness }} ({{ bits }}-bit)</div></div>
            <div class="metric-box"><div class="metric-label">Entry Point</div><div class="metric-value">{{ entrypoint }}</div></div>
        </div>
    </div>

    <div class="card">
        <h2 class="card-title">Defensive Security Observations</h2>
        {% if advisories %}
            {% for adv in advisories %}
            <div style="margin-bottom: 20px; border-left: 3px solid var(--danger); padding-left: 14px;">
                <div style="font-weight: 700; font-size: 15px; margin-bottom: 4px;">
                    <span class="badge badge-danger">{{ adv.severity }}</span> {{ adv.title }}
                </div>
                <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 6px;">{{ adv.risk_summary }}</div>
                <div style="font-size: 13px; color: var(--success);"><strong>Remediation:</strong> {{ adv.remediation_guidance }}</div>
            </div>
            {% endfor %}
        {% else %}
            <div>No critical defensive security advisories identified.</div>
        {% endif %}
    </div>

    <div class="card">
        <h2 class="card-title">Inferred Protocol Patterns</h2>
        {% for pat in patterns %}
        <div style="margin-bottom: 16px;">
            <div style="font-weight: 600; font-size: 14px; color: var(--accent);">
                {{ pat.pattern_name }} (Confidence: {{ (pat.confidence * 100) | round(1) }}%)
            </div>
            <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">{{ pat.description }}</div>
        </div>
        {% endfor %}
    </div>

    <div class="card">
        <h2 class="card-title">Classified Functions (First 25 Entries)</h2>
        <table>
            <thead>
                <tr>
                    <th>Address</th>
                    <th>Size (Bytes)</th>
                    <th>Family</th>
                    <th>Primitive</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody>
                {% for fn in functions[:25] %}
                <tr>
                    <td style="font-family: monospace;">{{ fn.hex_address }}</td>
                    <td>{{ fn.size }}</td>
                    <td>{{ fn.family }}</td>
                    <td><strong>{{ fn.primitive }}</strong></td>
                    <td style="font-family: monospace;">{{ (fn.confidence * 100) | round(1) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
"""

def generate_html_report(analysis_data: Dict[str, Any]) -> str:
    template = Template(HTML_REPORT_TEMPLATE)
    return template.render(
        filename=analysis_data.get("filename", "firmware.bin"),
        sha256=analysis_data.get("sha256", "N/A"),
        format=analysis_data.get("format", "ELF"),
        isa=analysis_data.get("isa", "x86-64"),
        endianness=analysis_data.get("endianness", "little"),
        bits=analysis_data.get("bits", 64),
        entrypoint=analysis_data.get("entrypoint", "0x0"),
        advisories=analysis_data.get("advisories", []),
        patterns=analysis_data.get("patterns", []),
        functions=analysis_data.get("functions", [])
    )

def generate_pdf_report(analysis_data: Dict[str, Any], output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    heading2 = styles["Heading2"]

    story = []

    # Title
    story.append(Paragraph("<b>CryptoScope Security Audit Report</b>", heading))
    story.append(Paragraph(f"Target: {analysis_data.get('filename')} | SHA-256: {analysis_data.get('sha256')[:16]}...", normal))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2A303B")))
    story.append(Spacer(1, 12))

    # Architecture Overview Table
    arch_data = [
        ["Format", analysis_data.get("format", "ELF"), "Architecture", analysis_data.get("isa", "x86-64")],
        ["Endianness", analysis_data.get("endianness", "little"), "Bit Width", f"{analysis_data.get('bits', 64)}-bit"],
        ["Entry Point", analysis_data.get("entrypoint", "0x0"), "Functions", str(len(analysis_data.get("functions", [])))]
    ]
    t = Table(arch_data, colWidths=[100, 150, 100, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F6F7F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D7DBE3")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # Advisories
    story.append(Paragraph("<b>Defensive Security Observations</b>", heading2))
    advisories = analysis_data.get("advisories", [])
    if advisories:
        for adv in advisories:
            adv_text = f"<b>[{adv.get('severity')}] {adv.get('title')}</b><br/>{adv.get('risk_summary')}<br/><b>Remediation:</b> {adv.get('remediation_guidance')}"
            story.append(Paragraph(adv_text, normal))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("No critical security advisories identified.", normal))
    story.append(Spacer(1, 16))

    # Protocol Patterns
    story.append(Paragraph("<b>Inferred Protocol Patterns</b>", heading2))
    for pat in analysis_data.get("patterns", []):
        pat_text = f"<b>{pat.get('pattern_name')} (Conf: {int(pat.get('confidence', 0)*100)}%)</b><br/>{pat.get('description')}"
        story.append(Paragraph(pat_text, normal))
        story.append(Spacer(1, 6))

    doc.build(story)
