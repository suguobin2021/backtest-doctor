"""Standalone offline HTML reporting. Never embeds input rows or paths."""
from html import escape
import json


def render_html(report):
    """Render aggregate-only results using escaped values and zero external assets."""
    title = escape(report['status'])
    parts = []
    sections = report.get('metrics', {}).get('sections', {})
    for name, item in sections.items():
        parts.append('<div class="section"><strong>'+escape(name.upper())+'</strong><span class="state">'
                     +escape(item['status'])+'</span><small>Rows: '+str(item['rows_examined'])
                     +' · Errors: '+str(item['errors'])+' · Warnings: '+str(item['warnings'])+'</small></div>')
    rows = ''.join(
        '<tr><td>'+escape(str(f.get('source','-')))+'</td><td>'+escape(f['code'])+
        '</td><td>'+escape(f['severity'])+'</td><td>'+
        escape(str(f['row']) if f['row'] is not None else '-')+'</td></tr>'
        for f in report['findings']
    )
    metrics = escape(json.dumps(report['metrics'], ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
    return ('''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Backtest Doctor — Audit</title>
<style>:root{color-scheme:light}body{font:15px/1.6 system-ui, sans-serif;margin:0;background:#f4f7fb;color:#17253a}
main{max-width:900px;margin:40px auto;padding:0 22px}h1{font-size:30px;margin:0}h2{font-size:18px;margin-top:28px}
.kicker{color:#60738c;text-transform:uppercase;letter-spacing:.14em;font-size:11px;font-weight:700}
.top{background:#142c48;color:#fff;padding:27px;border-radius:16px}.top p{color:#c7d9e8}
.status{display:inline-block;background:#fff;color:#142c48;border-radius:8px;padding:5px 14px;font-weight:800}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px;margin-top:16px}
.panel,.section{background:#fff;border:1px solid #dce5f1;border-radius:12px;padding:16px}
.panel strong{display:block;font-size:24px}.panel span{font-size:12px;color:#60738c}
.section{display:flex;gap:12px;align-items:center;margin-bottom:8px}.section small{color:#60738c;margin-left:auto}
.state{background:#eaf0f7;border-radius:6px;padding:2px 8px;font-size:12px}
table{border-collapse:collapse;background:white;width:100%;font-size:13px;overflow-wrap:anywhere}
th,td{border-bottom:1px solid #dde7f1;padding:9px;text-align:left}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#fff;border:1px solid #dce5f1;padding:16px;border-radius:10px}
small,.foot{color:#60738c}details{margin-bottom:32px}
</style></head><body><main><div class="top"><div class="kicker">Offline diagnostic report · no telemetry</div>
<h1>Backtest Doctor</h1><p>Evidence checks are not proof of strategy profitability.</p>
<span class="status">'''+title+'''</span></div><div class="grid">
<div class="panel"><strong>'''+str(report['errors'])+'''</strong><span>Errors</span></div>
<div class="panel"><strong>'''+str(report['warnings'])+'''</strong><span>Warnings</span></div>
<div class="panel"><strong>'''+str(report['rows_examined'])+'''</strong><span>Rows examined</span></div></div>
<h2>Sections</h2>'''+(''.join(parts) or '<p>No combined sections in this mode.</p>')+'''
<h2>Evidence findings</h2><table><thead><tr><th>Mode</th><th>Code</th><th>Severity</th><th>Row</th></tr></thead><tbody>'''
+rows+'''</tbody></table><h2>Aggregate metrics</h2><details><summary>Show summary data</summary><pre>'''+metrics+'''</pre></details>
<p class="foot">Input rows, filenames, identifiers, account data and strategy signals are excluded from the report.
Metrics use simplifying assumptions. No external scripts, fonts, images or network requests.</p></main></body></html>''')
