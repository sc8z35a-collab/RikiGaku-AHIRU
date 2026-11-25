#!/usr/bin/env python3
"""
Sync repository documentation, BOM, all 11 2026 ultra-lowest-cost procurement routes,
and the 'Is It Really OK?' Cost-vs-Safety Trade-Off audit into index.html's offline
embedded JSON payload (<script id="ahiru-data" type="application/json">).

Keeps index.html 100% self-contained (zero CDN / zero CORS issues via file:// or GitHub Pages)
with zero drift against README.md, PROCUREMENT_CHECKLIST_AND_COST_ROUTES.md,
FLIGHT_QUALIFICATION_MANUAL.md, BOM_AHIRU_Rev3.md, and procurement_checklist.csv.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = REPO_ROOT / "index.html"


def build_payload() -> dict:
    summary = json.loads((REPO_ROOT / "manufacturing" / "procurement_summary.json").read_text(encoding="utf-8"))

    items = []
    csv_path = REPO_ROOT / "manufacturing" / "procurement_checklist.csv"
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            items.append({
                "item": r["Item"].strip(),
                "wave": r["Wave"].strip(),
                "tier": r["Safety_Tier"].strip(),
                "part_no": r["Part_No"].strip(),
                "sub": r["Subsystem"].strip(),
                "desc": r["Description"].strip(),
                "qty": int(r["Qty"]),
                "mass_g": float(r["Mass_g"]),
                "p": {
                    "route_a": int(r["Route_A_Proto_USD"]),
                    "route_b1": int(r["Route_B1_MinCustom_USD"]),
                    "route_b2": int(r["Route_B2_ExtStart_USD"]),
                    "route_b3": int(r["Route_B3_BlueprintMinSelf_USD"]),
                    "route_b4": int(r["Route_B4_DIYHybridMin_USD"]),
                    "route_c": int(r["Route_C_COTSCore_USD"]),
                    "route_c_x45": int(r["Route_CX45_OptCOTS_USD"]),
                    "route_c_min": int(r["Route_CMin_SW60B_USD"]),
                    "route_d": int(r["Route_D_Batch10_USD"]),
                    "route_e_edf": int(r["Route_E_Step0EDF_USD"]),
                    "route_e_min": int(r["Route_EMin_UltraEDF_USD"]),
                },
                "lead_b1": r["LeadTime_B1"].strip(),
                "lead_c": r["LeadTime_C"].strip(),
                "v_b1": r["Recommended_Vendor_B1"].strip(),
                "v_b3": r["Recommended_Vendor_B3"].strip(),
                "v_c": r["Recommended_Vendor_C"].strip(),
                "files": r["Attached_Repo_Files"].strip(),
                "rfq": r["RFQ_Critical_Notes"].strip(),
                "accept": r["Incoming_Acceptance_Criteria"].strip(),
            })

    route_meta = [
        {
            "key": "route_e_min",
            "badge": "Step-0 極限最安",
            "tag": "電動EDF",
            "verdict": "◎ 強く推奨",
            "name": "Route E-Min — 電動64mm EDF 極限最安実証機",
            "short": "Dynam 64mm EDF ($76) + TBS Lucid H7 ($49) + FDM PETG-CF",
            "desc": "2026年実売精査で総額$495（約7.4万円）を実現！本番同一のSTM32H743＋デュアルICM-42688-P＋KST X08H Plusサーボ＋Sorbothane 50Dを無火気・最安で先に実証し、電装・サーボはそのまま本機へ流用可能。",
            "accent": "#0284c7",
        },
        {
            "key": "route_e_edf",
            "badge": "Step-0 自作基板",
            "tag": "電動EDF",
            "verdict": "○ 推奨",
            "name": "Route E — 電動64mm EDF + 本番4層PCBA",
            "short": "64mm 6S EDF + JLCPCB 2枚SMT + JLC3DP PA12-CF",
            "desc": "自作4層FADEC基板（60V FOC含む）とJLC3DP PA12-CF外殻まで本番と完全共通化して先行テストするStep-0実証機構成。",
            "accent": "#0369a1",
        },
        {
            "key": "route_c_x45",
            "badge": "市販ジェット推奨最適",
            "tag": "本物ジェット",
            "verdict": "◎ 市販最良バランス",
            "name": "Route C-X45 — 市販ジェット推奨 (Xicoy X45)",
            "short": "Xicoy X45 (Ø59.8mm/395g) + TBS Lucid H7 + JLC3DP PA12-CF",
            "desc": "再精査で判明した市販ジェット最良解！Swiwin SW60Bより+$229（約3.4万円）だけで重さ約半分（395g vs 783g）・小型Ø59.8mm・1.35×コンパクト機体・応答2.8sを実現。本体のみ$2,828（約42.4万円）。",
            "accent": "#059669",
        },
        {
            "key": "route_c_min",
            "badge": "市販絶対最安(大型注意)",
            "tag": "本物ジェット",
            "verdict": "△ 1.65×大型化注意",
            "name": "Route C-Min — 市販ジェット絶対最安 (Swiwin SW60B)",
            "short": "Swiwin SW60B (Ø84mm/783g/60N) + TBS Lucid H7",
            "desc": "市販ジェットの単純金額最安（$3,004 / 約45.1万円）。ただしSwiwin最小現行機はSW60B（Ø76–84mm・783g・スプール3.2s）のため機体が1.65×（全長30cm・約1.8kg）に肥大化。サイズ・制御性ならRoute C-X45を推奨。",
            "accent": "#0f766e",
        },
        {
            "key": "route_b4",
            "badge": "180mm自作DIY極限",
            "tag": "180mm完全自作",
            "verdict": "○ 溶接治具あれば可",
            "name": "Route B4 — 180mm純自作 DIY板金ハイブリッド極限",
            "short": "鍛造Al 2618圧縮機 + 0.4mm SUS310S板金燃焼器 + Lucid H7",
            "desc": "安全聖域8項目100%厳守のまま、圧縮機を鍛造Al 2618（ジャイロ連成41.8%→33.6%改善！）、燃焼器＆ノズルを0.4mm SUS310Sレーザー板金溶接にしてBOM $3,005（安全・釣合い込$3,875 / 約58.1万円）まで圧縮。要スポット溶接治具＆ベンチPF確認。",
            "accent": "#ea580c",
        },
        {
            "key": "route_b3",
            "badge": "180mm純自作 推奨最安",
            "tag": "180mm完全自作",
            "verdict": "◎ 純自作ベスト",
            "name": "Route B3 — 180mm純自作 設計図完全準拠最安",
            "short": "鍛造Al 2618圧縮機 + IN718 SLM一括相乗り + Lucid H7 + WDT",
            "desc": "溶接ゼロ・公式STEP/DXF図面100%準拠で180mm自作ターボジェットを作る2026年最良解！鍛造Al 2618圧縮機（-$145＆ジャイロ改善）＋TBS Lucid H7＋共有炉HIP＋G0.4動釣合いでBOM $3,514（総額$4,444 / 約66.7万円）。",
            "accent": "#d97706",
        },
        {
            "key": "route_d",
            "badge": "10機量産単価",
            "tag": "バッチ量産",
            "verdict": "◎ 共同製作最適",
            "name": "Route D — 10機バッチ量産（1機あたり）",
            "short": "Route B1を10機同時発注時の1機単価",
            "desc": "研究室・共同製作向け。DMLSビルドプレート高密度ネストとCNC段取り償却により、フル仕様機を1機あたり$3,806（約57.1万円）で製造。",
            "accent": "#4f46e5",
        },
        {
            "key": "route_c",
            "badge": "代理店保証COTS",
            "tag": "本物ジェット",
            "verdict": "○ 安心サポート",
            "name": "Route C — 市販タービン正規代理店ルート",
            "short": "代理店保証X45/K45G4+ + 5枚PCBA + Lee RCS",
            "desc": "正規代理店保証付き小型タービン＋JLCPCB 5枚全実装＋The Lee Company RCS弁の安心市販コア標準構成。",
            "accent": "#0d9488",
        },
        {
            "key": "route_b2",
            "badge": "国内釣合い自作",
            "tag": "180mm完全自作",
            "verdict": "○ 国内高品質",
            "name": "Route B2 — 自作・外部スタータ（国内釣合い）",
            "short": "Ti-6Al-4V + 国内G0.4動釣合い + 5枚PCBA + 外部始動",
            "desc": "国内高速動釣合い受託＋JLCPCB 5枚実装（予備4枚）＋外部手持ち電動スタータで -19.4g 軽量化した国内安心自作構成。",
            "accent": "#b45309",
        },
        {
            "key": "route_b1",
            "badge": "機上発電フル自作",
            "tag": "180mm完全自作",
            "verdict": "○ 完全Rev.3",
            "name": "Route B1 — 完全Rev.3自作（SmCo28発電付）",
            "short": "直結SmCo28スタータ発電機 + 5枚PCBA + 国内釣合い",
            "desc": "クラッチレス直結2極SmCo28スタータ発電機（+18W能動整流）＋機上60V FOCまで100%搭載する完全オリジナルRev.3標準構成。",
            "accent": "#64748b",
        },
        {
            "key": "route_a",
            "badge": "欧米ワンオフ基準",
            "tag": "フル航空宇宙",
            "verdict": "基準比較用",
            "name": "Route A — フルカスタム航空宇宙ワンオフ",
            "short": "PEEK-CF30オートクレーブ + 欧米/国内特注",
            "desc": "コスト最適化前の欧米/国内フルワンオフ基準見積（$16,337 / 約245.1万円）。全11ルート削減率比較のベースライン。",
            "accent": "#94a3b8",
        },
    ]

    for rm in route_meta:
        r = summary["routes"][rm["key"]]
        rm["bom_usd"] = r["bom_usd"]
        rm["svc_usd"] = r["svc_usd"]
        rm["total_usd"] = r["total_usd"]
        rm["lead_weeks"] = r["lead_weeks"]
        rm["savings_pct"] = r.get("savings_vs_a_pct", 0.0)

    cots_compare = [
        {"engine": "AHIRU-μTJ42V (自社設計・B3)", "price_usd": 4444, "diam_mm": 42.0, "mass_g": 122, "thrust_n": 13.1, "spool_s": 0.32, "duck_scale": "1.00× (180mm)", "verdict": "◎ 本命 18cm"},
        {"engine": "Xicoy X45 (Route C-X45)", "price_usd": 1750, "diam_mm": 59.8, "mass_g": 395, "thrust_n": 45.0, "spool_s": 2.80, "duck_scale": "1.35× (243mm)", "verdict": "◎ 市販最良"},
        {"engine": "KingTech K-45G4+", "price_usd": 1720, "diam_mm": 62.0, "mass_g": 450, "thrust_n": 45.0, "spool_s": 3.00, "duck_scale": "1.40× (252mm)", "verdict": "○ 優良代替"},
        {"engine": "Swiwin SW60B (Route C-Min)", "price_usd": 1500, "diam_mm": 84.0, "mass_g": 783, "thrust_n": 60.0, "spool_s": 3.20, "duck_scale": "1.65× (300mm)", "verdict": "△ 大型化注意"},
        {"engine": "JetCat P20-SX", "price_usd": 2350, "diam_mm": 50.0, "mass_g": 360, "thrust_n": 24.0, "spool_s": 3.50, "duck_scale": "1.20× (216mm)", "verdict": "△ 高価・遅応答"},
    ]

    rfq_templates = [
        {
            "id": "RFQ-1",
            "title": "金属3Dプリント (Inconel 718 単一プレート相乗り)",
            "vendor": "Unionfab / WeNext / FacFox",
            "files": "02_turbine_blisk_Inconel718.step, 05_combustor_liner_Inconel718.step, 00_AHIRU_Rev3_Core_Assembly.step, 07_tvc_gimbal_chevron_nozzle.step, DWG_03_Blisks_Flanges_IMU_GDT.dxf",
            "text": "Material: Inconel 718 (AMS 5662/5663). Total metal volume ~9.5 cm3. Please nest all 4 parts on a single build plate and share HIP furnace batch for Part 02 (Turbine Blisk, mandatory HIP 1180C/100MPa + solution/age); stress relief + complete ultrasonic powder removal inside 12 vaporizer tubes for Part 05. Wire-EDM/finish bore Ø4.000 H6 on Part 02 per DWG_03.",
        },
        {
            "id": "RFQ-2",
            "title": "5軸CNC & 精密研削 (鍛造Al 2618-T61 / Al 7075 / IN718)",
            "vendor": "JLCCNC / RapidDirect / PCBWay CNC",
            "files": "01_compressor_impeller_Ti6Al4V.step, 03_rotor_shaft_Inconel718.step, 04_diffuser_bearing_tunnel_Al7075.step, 06_containment_flange_Inconel718.step, DWG_01/02/03.dxf",
            "text": "Critical aerospace tolerances per attached DXFs: Part 01 Impeller in Forged Al 2618-T61 (Route B3/B4, DO NOT substitute Al 7075/6061!) or Ti-6Al-4V Gr.5 (Route B1/B2), bore Ø5.000 H6; Shaft (IN718) Ø5.000 h5 (+0/-0.005mm, Ra<=0.2um, TIR<=2um post-heat-treat grind); Diffuser (Al 7075-T651) bore Ø11.000 H6, coaxiality<=5um, mask bore during hard anodize; Containment ring wall >=2.05mm. CMM report mandatory.",
        },
        {
            "id": "RFQ-3",
            "title": "FADEC制御基板: TBS Lucid H7 ($49) + 外部WDT または 4層PCBA",
            "vendor": "TBS公式/代理店 (Route B3/B4/C-X45/E-Min) または JLCPCB (Route B1/B2)",
            "files": "electronics/generated/gerbers/* (9-file ZIP), AHIRU_FADEC_Rev3_BOM.csv, AHIRU_FADEC_Rev3_CPL.csv",
            "text": "[Route B3/B4/C-X45/E-Min]: Order TBS Lucid H7 FC (STM32H743 + Dual ICM-42688-P, $49) + external TPS3823-33 hardware watchdog fuel cutoff breakout ($36).\n[Route B1/B2 full onboard 60V FOC]: JLCPCB 4-layer FR-4 TG170, 1.6mm, 2oz Cu, ENIG. STRICT NO SUBSTITUTIONS for U1(STM32H743), U2/U3(ICM-42688-P), U6(DRV8353RS), Q1-Q6(BSC028N06LS3 60V), U9(TPS3823-33).",
        },
        {
            "id": "RFQ-4",
            "title": "樹脂3Dプリント (PA12-CF外殻 & PA12燃料タンク / Step-0 PETG-CF)",
            "vendor": "JLC3DP (MJF PA12-CF) / FDM造形 (Route E-Min)",
            "files": "00_AHIRU_Rev3_Core_Assembly.step, index.html抽出STL, 08_imu_sorbothane_mount_assembly.step",
            "text": "Fuel tank: MJF PA12 ($0.275/g) with 3 internal perforated anti-slosh baffles & UAT sump (powder-free interior, apply Jet-A1 resistant Novolac/Viton internal sealer). Outer duck shell: MJF PA12-CF (shell max verified 28.3C) or FDM PETG-CF for Step-0 EDF only.",
        },
        {
            "id": "RFQ-5",
            "title": "航空宇宙COTS精密部品 (GRW軸受・KSTサーボ・市販タービンX45)",
            "vendor": "GRW代理店 / O'Keefe / KST公式 / Xicoy",
            "files": "BOM_AHIRU_Rev3.csv (Parts 008, 009, 010, 014, 015, 017)",
            "text": "Exact P/Ns only (ZERO cheap substitutes!): GRW 685-2Z-CE Si3N4 ABEC-7 P4 (Qty 4 incl. spares), AS568-013 FKM Viton 60A (Qty 10), calibrated Ø0.25mm ruby orifice (Lee IEPA1211241H or O'Keefe + 5um filter, Qty 2), KST X08H Plus V6.0 ($39.99/ea, Qty 2-3), 5V 3ms micro-solenoid (Lee LHDA or SMC S070, Qty 2). For COTS jet route, request Xicoy X45 (Ø59.8mm, 395g) over oversized SW60B.",
        },
        {
            "id": "RFQ-6",
            "title": "外部 2面 G0.4 動釣合い (201,000 RPM ロータASSY)",
            "vendor": "高速動釣合い専門工場（国内/深圳マイクロターボ工房）",
            "files": "DWG_01_Rotor_Shaft_GDT.dxf, DWG_03_Blisks_Flanges_IMU_GDT.dxf, FLIGHT_QUALIFICATION_MANUAL.md",
            "text": "201,000 RPM マイクロタービン用ロータASSY（質量約34–36g）の2面動釣合い。ISO 1940 G0.4（残存不釣合い <= 0.22 mg·mm/面）。修正削りは図面指定のフロントカラー・リアボスのみ。分解再組付用の位相刻印および成績書発行を希望。",
        },
    ]

    safety_sanctuary = [
        {"part": "AHIRU-R3-008", "title": "GRW 685 Si3N4 ABEC-7 P4 軸受", "why": "dm·N = 1.71M 対応。AliExpress $15軸受（ABEC-1/金属保持器）は数秒で焼付き破損。"},
        {"part": "AHIRU-R3-009", "title": "AS568-013 FKM Viton 60A Oリング", "why": "スクイーズフィルム減衰の生命線。70A/90AやNBRは危険速度接触。"},
        {"part": "AHIRU-R3-010", "title": "較正済 Ø0.25mm ルビー潤滑オリフィス", "why": "0.12±0.01 mL/min 計量。流量不足は30秒以内に軸受焼付き。"},
        {"part": "AHIRU-R3-007", "title": "IN718 ≥2.05mm 封じ込めリング + A286ボルト", "why": "FAR 33.19 SF=46.5。SUS304ボルトは700°Cクリープ緩み厳禁。"},
        {"part": "AHIRU-R3-002", "title": "タービンブリスク HIP + 時効熱処理", "why": "DMLS内部空隙を完全閉鎖。未HIP品は48,000G遠心クリープ破壊の起点。"},
        {"part": "AHIRU-SVC-002", "title": "2面 ISO 1940 G0.4 動釣合い", "why": "≤0.22 mg·mm/面。DIY 1面バランスは遠心加振10倍・軸受寿命1/1000で絶対厳禁。"},
        {"part": "AHIRU-R3-020", "title": "独立WDT(TPS3823) + 二重IMU + (機上始動時60V FOC)", "why": "201k RPM暴走遮断＋二重系IMU投票。外部始動時はTBS Lucid H7 ($49) + 外部TPS3823で安全維持可。"},
        {"part": "AHIRU-R3-021", "title": "Sorbothane 50D IMU防振 + KST X08H Plus サーボ", "why": "3,350 Hz振動を-77.1 dB減衰＋ガタ≤0.25°。$12サーボ(ガタ2°)はLQR発振墜落。"},
    ]

    guide_md = """# RikiGaku-AHIRU Rev.3 — V3 検証実績 & 操作ガイド

## 1. 全マルチフィジックス検証スイート完全合格サマリー

| 検証スイート | 検証領域・ソルバー | 結果 | 主な確定数値 |
|---|---|---|---|
| **3D CAD / DMU / GD&T (D01)** | Node抽出 + trimesh/FCL + GPU 10万回MC | **7 / 7 PASS** | 外形 **`180.000 × 200.000 × 100.000 mm` (Δ=0.000 mm)**・干渉 **0/24**・非水密 **0**・最小Cpk **1.69**・TVC最小隙間 **+9.23 mm** |
| **AHIRU-V12 全12領域** | Cantera / ROSS / CalculiX / Ngspice / MuJoCo / Z3 | **52 / 52 PASS** | `T_net=13.14 N`・TWR `2.31`・ホバリング `5.2分`・騒音 `97.4 dB @7m`・`0 FAIL` |
| **Rev.3 6-Wall Qualification** | SU2 3D CFD / CalculiX 3D FEA / JAX 10万回MC | **7 / 7 PASS** | 10万回6-DOF生存率 **100.00% (墜落0)**・軸受寿命 `11,967 hr`・60V FOC耐圧 `SF=2.46` |
| **完全連成 MDAO / V&V** | OpenMDAO / OpenTURNS PCE / SALib | **Phase 1–9 PASS** | OpenTURNS 信頼度 **100.00%**・外殻最高温度 **`28.3 °C`** |
| **全22分野拡張検証 (verify_ahiru)** | D01–D22 全領域 (ROSS Campbell / GPU CFD / FW) | **22 / 22 PASS** | Viton 60A支持 危険速度 `+18.2%`分離・C11 FW `WCET=0.352 µs` |

## 2. 設計図（STEP / DXF）との 0.000 mm 寸法一致チェック

- **外形バウンディングボックス**: `X = [-90.000, +90.000]` (**180.000 mm**), `Y = [0.000, 200.000]` (**200.000 mm**), `Z = [-50.000, +50.000]` (**100.000 mm**) → 最大偏差 **`0.000 mm`**（目標 `≤ 0.01 mm`）
- **圧縮機インペラ (`01_compressor`)**: `Ø38.000 mm`・6+6スプリッタ・`Ø5.000 H6`ボア・G0.4カラー（鍛造 `Al 2618-T61` 選択時 `SF=2.21`・ジャイロ連成 `41.8% → 33.6%` 改善）
- **タービンブリスク (`02_turbine`)**: `Ø36.400 mm`・17素数ブレード・`Ø4.000 H6`ボア・G0.4ボス
- **静翼NGV (`06_NGV`)**: `Ø37.100 mm`シュラウド内径 (`r=18.550 mm`)・12静翼（17動翼と互いに素）
- **封じ込めリング (`06_containment`)**: `r = 18.550..20.600 mm`（肉厚 **`2.050 mm`**・FAR 33.19 SF=46.5）
- **チョークド・シェブロンTVCノズル (`07_nozzle`)**: スロート `r_t = 7.400 mm`・出口 `r_e = 8.600 mm`・12シェブロン・±14°ジンバル
- **燃料タンク**: `139.5 mL` 290°馬蹄型サドルタンク＋3枚アンチスロッシュバッフル＋UAT・Wet CoGオフセット **`1.47 mm`**

## 3. V3 Webアプリ 超多機能＆表示・処理・動的シミュレーション最適化

### 表示エンジン & GPU 負荷最適化 (V3)
- **Static GPU Super-Batch Megabuffer (`batchProg` + 52-byte インターリーブ VBO + Uint32 IBO)**: 剛体パーツ最大43部品を **1サーフェス Draw Call ＋ 1エッジ Draw Call** へ統合し、半断面剛体表示 **110 → 39 DC (-64.5%)**、ソリッド外殻表示 **120+ (V1) → 36 (V2) → 18 DC (-85% vs V1 / -50% vs V2)**・内部42/61パーツ自動遮蔽カリングを達成
- **4モード・マルチフィジックス PBR ウーバーシェーダー最適化**: 事前正規化ライト6軸＋CPU側事前リニア化＋`fastPow5()` 置換＋条件付きクリアコートによりALU負荷を削減しつつ、**`Studio PBR` / `FLIR IR サーモグラフィ (24–850°C)` / `建築ブループリント X線透視` / `201,000 RPM 遠心フォンミーゼス応力マップ`** の4解析モードをリアルタイム切替
- **ゼロGC ワールド空間フラスタムカリング & 完全0%アイドル休止**: 事前計算バウンディング球による視錐台カリング、ダーティチェックHUD、静止時・ドロワー展開時 `requestAnimationFrame` 完全停止、フレーム時間スパークライン波形付プロファイラを実装

### 多機能エンジニアリング CAD & 物理計算ツール
- **3D精密2点間ノギス計測**: モデル上の任意2点をクリックしてユークリッド距離 (`mm`) および `ΔX / ΔY / ΔZ` を3D計測表示（`全長180` / `全高200` / `全幅100` ワンクリック設計図照合プリセット付）
- **7段階ファクトリー組立シーケンス**: 主軸・軸受 → 圧縮機・SmCo28 → 燃焼器・17枚タービン・封じ込め → TVCノズル・KSTサーボ → 燃料系 → 電池・FADEC・防振IMU → 外殻・オレオTi脚 の全61パーツを質量積算付で工程再生
- **ISA推進サイクル & 飛行エンベロープ物理計算機 (`物理計算`)**: 外気温 (`-10..45°C`)・標高 (`0..3,000m`)・燃料・ペイロード・圧縮機材質 (`Al 2618` vs `Ti-6Al-4V`)・4推進機比較（`AHIRU-μTJ42V / Xicoy X45 / Swiwin SW60B / 64mm EDF`）を2種のライブグラフで算出し、ワンクリックで **6-DOF飛行シミュレーターへ即時注入**
- **高画質スタジオ PNG 撮影 & `Ctrl+K` コマンドパレット**: `preserveDrawingBuffer` ゼロ負荷のままワンクリックPNG保存、全パーツ・全解析モード・全飛行・全11予算・全説明書を瞬時検索

### 固定 240 Hz ローカル 6-DOF 飛行シミュレーター (V3)
- **固定タイムステップ 240 Hz 物理アキュムレータ & スローモーション (`0.25× / 0.5× / 1.0× / 2.0×`)**: 任意のモニタリフレッシュレートでも厳密決定論の240Hz RK2積分で稼働し、`0.25×` スローでオレオ脚着地やTVCジンバル応答を精密観察可能
- **1,200フレーム（直近20秒）ブラックボックス飛行リプレイ**: ゼロGCリングバッファにより飛行中の任意瞬間で一時停止・タイムライン巻き戻し＆3Dカメラ周回解析が可能
- **飛行中 リアルタイム圧縮機材質切替 (`Al2618·33.6%` ↔ `Ti64·41.8%`)**: ジャイロ角運動量と機体質量を飛行中に即時切替して歳差連成応答の差を体感可能
- **新自律ミッション (`らせん`・`着離陸`・`自動デモ`・`8の字`・`手動操縦`) + 4ch オシロスコープ + Web Audio タービン音響 + CSV出力**
"""

    docs = {
        "readme": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
        "procurement": (REPO_ROOT / "manufacturing" / "PROCUREMENT_CHECKLIST_AND_COST_ROUTES.md").read_text(encoding="utf-8"),
        "flight_manual": (REPO_ROOT / "manufacturing" / "generated" / "FLIGHT_QUALIFICATION_MANUAL.md").read_text(encoding="utf-8"),
        "bom": (REPO_ROOT / "manufacturing" / "generated" / "BOM_AHIRU_Rev3.md").read_text(encoding="utf-8"),
        "guide": guide_md.strip(),
    }

    return {
        "jpy_per_usd": summary["jpy_per_usd"],
        "dry_mass_g": 468.5,
        "wet_mass_g": 580.1,
        "envelope_mm": [180.0, 200.0, 100.0],
        "routes": route_meta,
        "items": items,
        "tradeoffs": summary.get("cost_safety_tradeoffs", []),
        "cots_compare": cots_compare,
        "rfq_templates": rfq_templates,
        "safety_sanctuary": safety_sanctuary,
        "docs": docs,
    }


def main() -> int:
    payload = build_payload()
    # Escape </script> safely for inline HTML JSON block
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = INDEX_HTML.read_text(encoding="utf-8")
    pattern = re.compile(r'(<script id="ahiru-data" type="application/json">)[\s\S]*?(</script>)')
    if not pattern.search(html):
        raise RuntimeError('Missing <script id="ahiru-data" type="application/json"></script> anchor in index.html')
    new_html = pattern.sub(lambda m: m.group(1) + raw_json + m.group(2), html, count=1)
    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(
        f"Synced embedded offline data into {INDEX_HTML.name}: {len(raw_json):,} bytes "
        f"({len(payload['items'])} BOM items, {len(payload['routes'])} routes, "
        f"{len(payload['tradeoffs'])} tradeoffs, {len(payload['docs'])} docs)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
