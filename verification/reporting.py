"""
Executive Aerospace Verification Reporting, Self-Contained HTML Dashboard
(with embedded 12-domain plots), Quantitative Redesign Action Plan, and
Commercial CAE Export Bundle (.zip) Packager.
"""
from __future__ import annotations

import base64
import html
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .cad_loader import CADAssembly
from .schema import DomainReport, Verdict


def _img_to_data_uri(img_path: str) -> str:
    p = Path(img_path)
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _badge_html(v: Verdict) -> str:
    colors = {
        Verdict.PASS: ("#DCFCE7", "#166534", "#22C55E"),
        Verdict.MARGINAL: ("#FEF3C7", "#92400E", "#F59E0B"),
        Verdict.FAIL: ("#FEE2E2", "#991B1B", "#EF4444"),
        Verdict.INFO: ("#E0F2FE", "#075985", "#0EA5E9"),
    }
    bg, fg, bd = colors[v]
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
        f'background:{bg};color:{fg};border:1px solid {bd};font-weight:700;font-size:12px;">'
        f'{v.value}</span>'
    )


def generate_reports(
    cad: CADAssembly,
    reports: List[DomainReport],
    env_info: Dict[str, Any],
    out_dir: Path,
) -> Dict[str, Path]:
    """Generate JSON, Markdown, self-contained HTML Dashboard, and downloadable ZIP bundle."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    all_checks = [c for r in reports for c in r.checks]
    n_total = len(all_checks)
    n_pass = sum(1 for c in all_checks if c.verdict == Verdict.PASS)
    n_marg = sum(1 for c in all_checks if c.verdict == Verdict.MARGINAL)
    n_fail = sum(1 for c in all_checks if c.verdict == Verdict.FAIL)
    n_dom_pass = sum(1 for r in reports if r.overall_verdict == Verdict.PASS)
    overall = Verdict.PASS if (n_fail == 0 and n_marg == 0) else (Verdict.MARGINAL if n_fail == 0 else Verdict.FAIL)

    # 1. Master JSON Report
    master_json = {
        "generated_at": ts,
        "system": "RikiGaku-AHIRU (AHIRU-μTJ42V)",
        "overall_verdict": overall.value,
        "summary": {
            "domains_total": len(reports),
            "domains_fully_passed": n_dom_pass,
            "checks_total": n_total,
            "checks_pass": n_pass,
            "checks_marginal": n_marg,
            "checks_fail": n_fail,
            "pass_rate_pct": round(n_pass / max(n_total, 1) * 100.0, 1),
        },
        "compute_environment": env_info,
        "cad_mass_properties": {
            "part_count": len(cad.parts),
            "envelope_mm": [round(float(x), 3) for x in cad.global_envelope_mm],
            "dry_mass_g": round(cad.dry_mass_g, 2),
            "fuel_mass_g": round(cad.fuel_mass_g, 2),
            "wet_mass_g": round(cad.wet_mass_g, 2),
            "fuel_volume_ml": round(cad.fuel_volume_ml, 2),
            "wet_cog_mm": [round(float(x), 2) for x in cad.wet_cog_mm],
            "dry_cog_mm": [round(float(x), 2) for x in cad.dry_cog_mm],
        },
        "domains": [r.to_dict() for r in reports],
    }
    json_path = out_dir / "ahiru_v12_report.json"
    json_path.write_text(json.dumps(master_json, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Markdown Summary Report
    md_lines = [
        "# RikiGaku-AHIRU (AHIRU-μTJ42V) — 12-Domain Full-Spectrum Aerospace Verification Report",
        "",
        f"- **Generated**: {ts}",
        f"- **Compute Backend**: `{env_info.get('gpu_name') or 'CPU FP64'}` (CUDA={env_info.get('cuda_available')}, CPUs={env_info.get('cpu_count')})",
        f"- **Overall Qualification Verdict**: **{overall.value}** (`{n_pass}` PASS / `{n_marg}` MARGINAL / `{n_fail}` FAIL out of `{n_total}` engineering checks across 12 domains)",
        "",
        "## 12-Domain Master Scorecard",
        "",
        "| # | Domain | Verdict | PASS | MARGINAL | FAIL | Time (s) |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in reports:
        md_lines.append(
            f"| {r.domain_id:02d} | {r.title_ja} ({r.title_en}) | **{r.overall_verdict.value}** | {r.pass_count} | {r.marginal_count} | {r.fail_count} | {r.elapsed_sec:.2f} |"
        )

    md_lines.extend(["", "## Critical Failures & Quantitative Redesign Actions Required for 100% Physical Qualification", ""])
    fail_checks = [c for c in all_checks if c.verdict == Verdict.FAIL]
    if not fail_checks:
        md_lines.append("All 12 verification domains passed with ZERO critical failures!")
    else:
        for c in fail_checks:
            md_lines.append(f"### [{c.check_id}] {c.name} — **FAIL**")
            md_lines.append(f"- **Measured**: `{c.measured}`")
            md_lines.append(f"- **Target**: `{c.target}`")
            md_lines.append(f"- **Root Cause**: {c.details}")
            if c.remediation:
                md_lines.append(f"- **Quantitative Fix**: {c.remediation}")
            md_lines.append("")

    md_path = out_dir / "ahiru_v12_summary.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # 3. Self-Contained Interactive Executive HTML Dashboard (displays inline in Google Colab!)
    domain_cards_html = []
    for r in reports:
        rows_html = []
        for c in r.checks:
            rem_block = f'<div style="margin-top:4px;color:#0F766E;font-size:12px;"><b>Fix:</b> {html.escape(c.remediation)}</div>' if c.remediation and c.verdict != Verdict.PASS else ""
            rows_html.append(
                f"<tr>"
                f"<td style='font-family:monospace;font-weight:700;'>{html.escape(c.check_id)}</td>"
                f"<td><b>{html.escape(c.name)}</b><div style='color:#475569;font-size:12px;margin-top:2px;'>{html.escape(c.details)}</div>{rem_block}</td>"
                f"<td style='font-family:monospace;font-size:12px;'>{html.escape(str(c.measured))}</td>"
                f"<td style='font-size:12px;color:#334155;'>{html.escape(c.target)}</td>"
                f"<td style='font-size:11px;color:#64748B;'>{html.escape(c.solver)}</td>"
                f"<td style='text-align:center;'>{_badge_html(c.verdict)}</td>"
                f"</tr>"
            )
        plots_html = ""
        for pl in r.plots:
            uri = _img_to_data_uri(pl)
            if uri:
                plots_html += f'<div style="margin:14px 0;"><img src="{uri}" style="width:100%;border-radius:10px;border:1px solid #E2E8F0;"/></div>'

        tools_html = ""
        for t in r.tools:
            tools_html += (
                f"<div style='font-size:12px;color:#334155;margin-top:4px;'>"
                f"<b>{html.escape(t.category)}</b> — "
                f"<span style='color:#1D4ED8;'>Executed:</span> {html.escape(', '.join(t.oss_gpu_executed))} | "
                f"<span style='color:#64748B;'>Commercial Bridge:</span> {html.escape(', '.join(t.commercial_tools))}"
                f"</div>"
            )

        domain_cards_html.append(f"""
        <section style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;padding:20px;margin-bottom:22px;box-shadow:0 2px 10px rgba(15,23,42,0.04);">
          <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #F1F5F9;padding-bottom:10px;margin-bottom:12px;">
            <div>
              <div style="font-size:12px;font-weight:700;color:#64748B;letter-spacing:0.06em;">DOMAIN {r.domain_id:02d} • {html.escape(r.code)} • {r.elapsed_sec:.2f}s</div>
              <h2 style="margin:2px 0 0 0;font-size:19px;color:#0F172A;">{html.escape(r.title_ja)}</h2>
              <div style="font-size:13px;color:#475569;">{html.escape(r.title_en)}</div>
            </div>
            <div style="text-align:right;">
              {_badge_html(r.overall_verdict)}
              <div style="font-size:12px;color:#64748B;margin-top:4px;">{r.pass_count} PASS / {r.marginal_count} MARG / {r.fail_count} FAIL</div>
            </div>
          </div>
          {tools_html}
          <div style="overflow-x:auto;margin-top:12px;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead>
                <tr style="background:#F8FAFC;text-align:left;border-bottom:2px solid #E2E8F0;">
                  <th style="padding:8px;">ID</th>
                  <th style="padding:8px;">Verification Check & Engineering Findings</th>
                  <th style="padding:8px;">Measured</th>
                  <th style="padding:8px;">Requirement</th>
                  <th style="padding:8px;">Solver / Engine</th>
                  <th style="padding:8px;text-align:center;">Verdict</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows_html)}
              </tbody>
            </table>
          </div>
          {plots_html}
        </section>
        """)

    # Action Plan List
    remediation_items = []
    for c in all_checks:
        if c.verdict in (Verdict.FAIL, Verdict.MARGINAL) and c.remediation:
            remediation_items.append(
                f"<li style='margin-bottom:8px;'>{_badge_html(c.verdict)} <b>[{html.escape(c.check_id)}] {html.escape(c.name)}</b>: "
                f"{html.escape(c.remediation)}</li>"
            )

    html_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<title>RikiGaku-AHIRU V12 Aerospace Verification Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Hiragino Kaku Gothic ProN", sans-serif; background:#F1F5F9; color:#0F172A; margin:0; padding:24px; }}
  table td {{ padding:9px 8px; border-bottom:1px solid #F1F5F9; vertical-align:top; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin:18px 0 24px 0; }}
  .kpi {{ background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:14px 16px; }}
  .kpi-lbl {{ font-size:11px; text-transform:uppercase; color:#64748B; font-weight:700; letter-spacing:0.05em; }}
  .kpi-val {{ font-size:24px; font-weight:800; margin-top:4px; color:#0F172A; }}
</style>
</head>
<body>
  <div style="max-width:1380px;margin:0 auto;">
    <header style="background:linear-gradient(135deg,#0F172A,#1E3A8A);color:#FFFFFF;border-radius:16px;padding:24px 28px;margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
        <div>
          <div style="font-size:12px;letter-spacing:0.1em;color:#93C5FD;font-weight:700;">AEROSPACE FULL-SPECTRUM QUALIFICATION SUITE • AHIRU-V12</div>
          <h1 style="margin:6px 0 4px 0;font-size:26px;">RikiGaku-AHIRU (AHIRU-μTJ42V) 全12領域・一括物理検証レポート</h1>
          <div style="font-size:13px;color:#CBD5E1;">Generated: {ts} | Hardware: {html.escape(str(env_info.get('gpu_name') or 'CPU FP64'))} (CUDA={env_info.get('cuda_available')}) | Extracted 54 CAD Parts from index.html</div>
        </div>
        <div style="background:rgba(255,255,255,0.12);padding:12px 18px;border-radius:12px;text-align:center;">
          <div style="font-size:11px;color:#CBD5E1;margin-bottom:4px;">OVERALL FLIGHT-READINESS</div>
          {_badge_html(overall)}
        </div>
      </div>
    </header>

    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-lbl">Checks Passed</div><div class="kpi-val" style="color:#16A34A;">{n_pass} / {n_total}</div></div>
      <div class="kpi"><div class="kpi-lbl">Marginal Warnings</div><div class="kpi-val" style="color:#D97706;">{n_marg}</div></div>
      <div class="kpi"><div class="kpi-lbl">Critical Failures</div><div class="kpi-val" style="color:#DC2626;">{n_fail}</div></div>
      <div class="kpi"><div class="kpi-lbl">CAD Dry / Wet Mass</div><div class="kpi-val">{cad.dry_mass_g:.0f}g / {cad.wet_mass_g:.0f}g</div></div>
      <div class="kpi"><div class="kpi-lbl">Actual CAD Fuel Vol</div><div class="kpi-val">{cad.fuel_volume_ml:.1f} mL</div></div>
      <div class="kpi"><div class="kpi-lbl">Domains 100% Clean</div><div class="kpi-val">{n_dom_pass} / {len(reports)}</div></div>
    </div>

    <section style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:14px;padding:18px 22px;margin-bottom:24px;">
      <h2 style="margin:0 0 10px 0;font-size:17px;color:#92400E;">Prioritized Engineering Redesign Roadmap (Required for 100% Real-World Fabrication Pass)</h2>
      <ul style="margin:0;padding-left:20px;font-size:13px;line-height:1.55;">
        {''.join(remediation_items) if remediation_items else '<li>All verification criteria satisfied — zero redesign items required!</li>'}
      </ul>
    </section>

    {''.join(domain_cards_html)}
  </div>
</body>
</html>
"""
    html_path = out_dir / "ahiru_v12_dashboard.html"
    html_path.write_text(html_doc, encoding="utf-8")

    # 4. Package Complete Downloadable Bundle (.zip) including Commercial CAE Export Decks
    zip_path = out_dir / "ahiru_v12_verification_bundle.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fpath in out_dir.rglob("*"):
            if fpath.is_file() and fpath.name != zip_path.name:
                # Skip temporary compiled binaries
                if fpath.name in ("fadec_test_bin", "pan"):
                    continue
                zf.write(fpath, arcname=str(fpath.relative_to(out_dir)))

    return {
        "json": json_path,
        "markdown": md_path,
        "html": html_path,
        "zip": zip_path,
    }
