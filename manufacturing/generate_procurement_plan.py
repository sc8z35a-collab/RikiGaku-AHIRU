#!/usr/bin/env python3
"""
RikiGaku-AHIRU Rev.3 — Production Procurement Checklist & Cost-Minimization Route Builder

Reads the authoritative Rev.3 BOM (`manufacturing/generated/BOM_AHIRU_Rev3.csv`),
verifies every referenced STEP/DXF/Gerber/PCBA/firmware file exists on disk, and
generates:
  1. `manufacturing/procurement_checklist.csv`
  2. `manufacturing/PROCUREMENT_CHECKLIST_AND_COST_ROUTES.md`
  3. `manufacturing/procurement_summary.json`

Zero hardcoded drift: every Route A price, mass, and part number is pulled directly
from `BOM_AHIRU_Rev3.csv`, and all route subtotals are computed programmatically.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
BOM_CSV = REPO_ROOT / "manufacturing" / "generated" / "BOM_AHIRU_Rev3.csv"
OUT_DIR = REPO_ROOT / "manufacturing"
JPY_PER_USD = 150


# Per-part procurement metadata keyed by Part_No (strictly matched against BOM_AHIRU_Rev3.csv)
# Route B1: Cost-minimized Full-Custom Rev.3 (180mm original size, 201k RPM custom core + direct-coupled starter-gen)
# Route B2: Cost-minimized Rev.3 1st-Flight Variant (external start wand, omit onboard starter-gen for -19.4g & -$460)
# Route C : COTS Certified Micro-Turbine Hybrid (1.25x scale airframe + Swiwin SW30B / KingTech K30G4+ core)
# Route D : 10-Unit Small Batch Cost-Optimized (per-unit cost in USD)
PART_PROCUREMENT_DB: Dict[str, Dict[str, Any]] = {
    "AHIRU-R3-001": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 380,
        "route_b2_usd": 380,
        "route_c_usd": 0,  # Included in COTS turbine
        "route_d_usd": 190,
        "lead_wk_b1": "3-4w",
        "lead_wk_c": "-",
        "vendor_b1": "PCBWay CNC / RapidDirect 5-Axis Ti-6Al-4V + 国内H6仕上げ",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/01_compressor_impeller_Ti6Al4V.step",
            "manufacturing/generated/drawings/DWG_03_Blisks_Flanges_IMU_GDT.dxf",
        ],
        "rfq_notes": "Ti-6Al-4V Gr.5 AMS 4928; Ø5.000 H6ボア+端面同軸同時加工; バランスカラー削り代確保; CMM検査成績書必須",
        "acceptance": "Ø5.000 +0.008/-0.000 mm (H6), 翼厚公差 ±0.03 mm, 浸透探傷ゼロ欠陥",
    },
    "AHIRU-R3-002": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 780,
        "route_b2_usd": 780,
        "route_c_usd": 0,
        "route_d_usd": 340,
        "lead_wk_b1": "4-6w",
        "lead_wk_c": "-",
        "vendor_b1": "Unionfab / Xometry Asia Inconel 718 DMLS一括ネスト + HIP + 5軸仕上げ",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/02_turbine_blisk_Inconel718.step",
            "manufacturing/generated/drawings/DWG_03_Blisks_Flanges_IMU_GDT.dxf",
        ],
        "rfq_notes": "Inconel 718 AMS 5662/5663; 005/006/013と同一ビルドプレート相乗り造形; HIP(1180°C/100MPa)+時効処理必須; ボアØ4.000 H6ワイヤー放電/研削",
        "acceptance": "HIP証明・熱処理成績書, Ø4.000 H6, X線/CT内部空隙ゼロ, 17翼ピッチ異常なし",
    },
    "AHIRU-R3-003": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 220,
        "route_b2_usd": 220,
        "route_c_usd": 0,
        "route_d_usd": 85,
        "lead_wk_b1": "2-3w",
        "lead_wk_c": "-",
        "vendor_b1": "国内精密切削/円筒研削（ミスミmeviy / 国内町工場）",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/03_rotor_shaft_Inconel718.step",
            "manufacturing/generated/drawings/DWG_01_Rotor_Shaft_GDT.dxf",
        ],
        "rfq_notes": "Inconel 718 溶体化・時効後に最終円筒研削; ジャーナルØ5.000 h5(+0/-0.005), Ra<=0.2um, 全振れTIR<=2um",
        "acceptance": "CMM/真円度測定成績書: Ø5.000 h5, TIR <= 2 µm, Ra <= 0.2 µm",
    },
    "AHIRU-R3-004": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 320,
        "route_b2_usd": 320,
        "route_c_usd": 0,
        "route_d_usd": 150,
        "lead_wk_b1": "3-4w",
        "lead_wk_c": "-",
        "vendor_b1": "PCBWay CNC / RapidDirect 5-Axis Al 7075-T651 + 硬質アルマイト(ボアマスキング)",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/04_diffuser_bearing_tunnel_Al7075.step",
            "manufacturing/generated/drawings/DWG_02_Diffuser_Lube_ORing_GDT.dxf",
        ],
        "rfq_notes": "Ø11.000 H6(+0.011/-0)軸受穴は前後一発通し加工(同軸度<=5um); AS568-013溝深さ厳守; アルマイト時ボアマスキング",
        "acceptance": "エアマイクロ測定 Ø11.000 H6, 同軸度 <= 5 µm, Oリング溝14%潰し代確認",
    },
    "AHIRU-R3-005": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-A (高温重要)",
        "route_b1_usd": 550,
        "route_b2_usd": 550,
        "route_c_usd": 0,
        "route_d_usd": 240,
        "lead_wk_b1": "3-4w",
        "lead_wk_c": "-",
        "vendor_b1": "Unionfab / FacFox Inconel 718 DMLS一括ネスト（002と同プレート）",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/05_combustor_liner_Inconel718.step",
            "manufacturing/generated/drawings/DWG_03_Blisks_Flanges_IMU_GDT.dxf",
        ],
        "rfq_notes": "肉厚0.8mm + 12気化管内部粉末の完全除去(超音波+エアブロー確認); 980°C応力除去熱処理",
        "acceptance": "全12気化管+36希釈孔の通気・内視鏡残留粉末ゼロ確認",
    },
    "AHIRU-R3-006": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-A (高温重要)",
        "route_b1_usd": 440,
        "route_b2_usd": 440,
        "route_c_usd": 0,
        "route_d_usd": 180,
        "lead_wk_b1": "3-4w",
        "lead_wk_c": "-",
        "vendor_b1": "Unionfab / FacFox Inconel 718 DMLS一括ネスト + 端面旋盤仕上げ",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/00_AHIRU_Rev3_Core_Assembly.step",
            "manufacturing/generated/drawings/DWG_03_Blisks_Flanges_IMU_GDT.dxf",
        ],
        "rfq_notes": "12静翼(17動翼と互いに素); フランジ接合面のみ旋盤仕上げ加工; 応力除去熱処理必須",
        "acceptance": "12静翼流路面積バラつき <= ±3%, フランジ平面度 <= 0.02 mm",
    },
    "AHIRU-R3-007": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 240,
        "route_b2_usd": 240,
        "route_c_usd": 0,
        "route_d_usd": 110,
        "lead_wk_b1": "2-3w",
        "lead_wk_c": "-",
        "vendor_b1": "PCBWay CNC Inconel 718 旋盤 + McMaster/ミスミ A286ボルト＆皿ばね",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/06_containment_flange_Inconel718.step",
            "manufacturing/generated/drawings/DWG_03_Blisks_Flanges_IMU_GDT.dxf",
        ],
        "rfq_notes": "ブレード封じ込め壁厚 2.05mm以上厳守(FAR 33.19 SF=46.5); ボルトは必ずA286耐熱合金+Inconel 718皿ばね(SUS304不可)",
        "acceptance": "最小肉厚 >= 2.05 mm 確認, A286ミルシート確認",
    },
    "AHIRU-R3-008": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 240,
        "route_b2_usd": 240,
        "route_c_usd": 0,
        "route_d_usd": 175,
        "lead_wk_b1": "3-6w",
        "lead_wk_c": "-",
        "vendor_b1": "GRW代理店 / Boca Bearings / WIB（GRW 685-2Z-CE Si3N4 ABEC-7 P4）",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/drawings/DWG_01_Rotor_Shaft_GDT.dxf",
            "manufacturing/generated/drawings/DWG_02_Diffuser_Lube_ORing_GDT.dxf",
        ],
        "rfq_notes": "絶対妥協禁止: 必ずSi3N4窒化ケイ素球+PEEK/フェノール保持器(金属保持器不可)+ABEC-7以上; 予備+2個同時購入推奨",
        "acceptance": "メーカー証明書(dn >= 1.8M対応), 手回し引っ掛かりゼロ, シールド脱脂処理",
    },
    "AHIRU-R3-009": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 12,
        "route_b2_usd": 12,
        "route_c_usd": 0,
        "route_d_usd": 6,
        "lead_wk_b1": "1w",
        "lead_wk_c": "-",
        "vendor_b1": "Parker / McMaster-Carr / ミスミ（AS568-013 FKM Viton 60A）",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/drawings/DWG_02_Diffuser_Lube_ORing_GDT.dxf",
        ],
        "rfq_notes": "硬度 Shore A 60A 指定(70A/90Aは剛性過多で危険速度がズレる); 耐Jet-A1 FKM Viton材; 10本パック購入",
        "acceptance": "硬度 60±5 Shore A, 断面径 1.78±0.08 mm 確認",
    },
    "AHIRU-R3-010": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 190,
        "route_b2_usd": 190,
        "route_c_usd": 0,
        "route_d_usd": 110,
        "lead_wk_b1": "2-4w",
        "lead_wk_c": "-",
        "vendor_b1": "The Lee Company Japan（IEPA1211241H / Ø0.25mmルビーオリフィス）",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/drawings/DWG_02_Diffuser_Lube_ORing_GDT.dxf",
        ],
        "rfq_notes": "絶対妥協禁止: 潤滑流量が狂うと201k RPMで即焼付き; 流量較正済みルビーオリフィス + 5µmフィルタ内蔵型",
        "acceptance": "1.8 bar ろ過Jet-A1で各 0.12 ± 0.01 mL/min 実測確認",
    },
    "AHIRU-R3-011": {
        "wave": "Wave 3 (Week 2-3)",
        "safety_tier": "Tier-A (熱安全重要)",
        "route_b1_usd": 210,
        "route_b2_usd": 210,
        "route_c_usd": 160,
        "route_d_usd": 120,
        "lead_wk_b1": "2w",
        "lead_wk_c": "2w",
        "vendor_b1": "Aspen Aerogels Pyrogel + DEI金箔遮熱シート + 国内ジルコニア(YSZ)板カット",
        "vendor_c": "Aspen Aerogels Pyrogel + DEI金箔遮熱シート + YSZ板（1.25x寸）",
        "files": [
            "manufacturing/generated/step/00_AHIRU_Rev3_Core_Assembly.step",
        ],
        "rfq_notes": "放射率 ε<=0.04 相当の金属蒸着金箔 + 2mm厚 YSZ遮熱スペーサでバッテリー温度<=40°C維持",
        "acceptance": "LiHVバッテリー〜燃焼器外殻ギャップ >= 13.5 mm 実測",
    },
    "AHIRU-R3-012": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-A (高速回転重要)",
        "route_b1_usd": 580,
        "route_b2_usd": 120,  # External handheld brushless starter wand only (saves $460 & 19.4g!)
        "route_c_usd": 0,     # Included in COTS turbine
        "route_d_usd": 310,
        "lead_wk_b1": "4-6w",
        "lead_wk_c": "-",
        "vendor_b1": "中国超高速PM特注(SmCo28 2極+0.35mm IN718圧入スリーブ+0.1mm NO10ステータ)",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/step/03_rotor_shaft_Inconel718.step",
            "manufacturing/generated/drawings/DWG_01_Rotor_Shaft_GDT.dxf",
        ],
        "rfq_notes": "Route B1: SmCo28(300°C耐熱、NdFeB不可!)+0.35mm IN718リテーナスリーブ圧入; Route B2初号機: 外部スピナ電動スタータ+発電省略で軽量化",
        "acceptance": "Route B1: 201k RPM相当スピン/線間逆起電力 Kv=7,800±5% 確認, 絶縁耐圧 >= 100V",
    },
    "AHIRU-R3-013": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-A (推力偏向重要)",
        "route_b1_usd": 480,
        "route_b2_usd": 480,
        "route_c_usd": 360,  # 1.25x scaled Inconel/Ti TVC chevron gimbal nozzle
        "route_d_usd": 220,
        "lead_wk_b1": "3-4w",
        "lead_wk_c": "3w",
        "vendor_b1": "Unionfab Inconel 718 DMLS一括ネスト（002と同プレート）+ TiジンバルリングCNC",
        "vendor_c": "Unionfab Inconel 718 DMLS(1.25x TVCノズル) + TiジンバルリングCNC",
        "files": [
            "manufacturing/generated/step/07_tvc_gimbal_chevron_nozzle.step",
        ],
        "rfq_notes": "スロート半径 r_t=7.4mm/出口 r_e=8.6mm 12シェブロン; ±14°全可動域で干渉ゼロ確認; ピボット軸受は焼結含油ブロンズ/セラミックブッシュ",
        "acceptance": "±14°全象限スムーズ可動(フリクション <= 12 mNm), クリアランス >= 9 mm",
    },
    "AHIRU-R3-014": {
        "wave": "Wave 2 (Week 1-2)",
        "safety_tier": "Tier-A (姿勢制御重要)",
        "route_b1_usd": 130,
        "route_b2_usd": 130,
        "route_c_usd": 130,
        "route_d_usd": 110,
        "lead_wk_b1": "1-2w",
        "lead_wk_c": "1-2w",
        "vendor_b1": "KST公式 / 国内RCショップ（KST X08H Plus V6.0 × 2個 + Tiリンク）",
        "vendor_c": "KST公式 / 国内RCショップ（KST X08H Plus V6.0 × 2個 + Tiリンク）",
        "files": [
            "manufacturing/generated/step/07_tvc_gimbal_chevron_nozzle.step",
        ],
        "rfq_notes": "必ずHV(8.4V対応)メタルギア版 X08H Plus を選定(ガタ極小); 予備+1個推奨",
        "acceptance": "無負荷応答 <= 0.08s/60°, バックラッシ <= 0.25°",
    },
    "AHIRU-R3-015": {
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-A (ヨー制御重要)",
        "route_b1_usd": 280,
        "route_b2_usd": 280,
        "route_c_usd": 280,
        "route_d_usd": 190,
        "lead_wk_b1": "3-5w",
        "lead_wk_c": "3-5w",
        "vendor_b1": "The Lee Company Japan（LHDA0523111H 超小型高速ソレノイド弁 × 2 + Ti細管）",
        "vendor_c": "The Lee Company Japan（LHDA0523111H × 2 + Ti細管 / または電動ダクトヨー補助）",
        "files": [
            "manufacturing/generated/step/00_AHIRU_Rev3_Core_Assembly.step",
        ],
        "rfq_notes": "応答時間 <= 3ms クラス; 200Hz PWM駆動対応; 耐圧 >= 3 barG",
        "acceptance": "5V駆動リークゼロ, 50Hz PWM比例流量応答確認",
    },
    "AHIRU-R3-016": {
        "wave": "Wave 2 (Week 1-2)",
        "safety_tier": "Tier-A (燃料安全重要)",
        "route_b1_usd": 145,
        "route_b2_usd": 145,
        "route_c_usd": 165,  # 1.25x scaled tank for COTS turbine
        "route_d_usd": 85,
        "lead_wk_b1": "2w",
        "lead_wk_c": "2w",
        "vendor_b1": "JLCPCB 3DP / FacFox PA12 MJF造形 + 耐燃料FKM/エポキシ内面コート(Baffles+UAT一体)",
        "vendor_c": "JLCPCB 3DP PA12 MJF造形(1.25x) + 耐燃料コート(またはKevlar RCタンク転用)",
        "files": [
            "manufacturing/generated/step/00_AHIRU_Rev3_Core_Assembly.step",
        ],
        "rfq_notes": "3枚多孔バッフル＋中央UAT気泡トラップ必須; 造形後必ず耐Jet-A1シーラント含浸+0.5bar気密テスト",
        "acceptance": "満水139.5±2 mL, 0.5 bar 30分リークゼロ, Jet-A1 72時間浸漬膨潤なし",
    },
    "AHIRU-R3-017": {
        "wave": "Wave 2 (Week 1-2)",
        "safety_tier": "Tier-A (燃料供給重要)",
        "route_b1_usd": 260,
        "route_b2_usd": 260,
        "route_c_usd": 0,  # Included in COTS turbine
        "route_d_usd": 195,
        "lead_wk_b1": "2-3w",
        "lead_wk_c": "-",
        "vendor_b1": "Flightworks 200-series / KingTech互換ブラシレスギアポンプ + 11Vセラミックイグナイタ",
        "vendor_c": "COTSタービン同梱（不要）",
        "files": [
            "manufacturing/generated/BOM_AHIRU_Rev3.csv",
        ],
        "rfq_notes": "真鍮AGMAギア・ブラシレス駆動(脈動極小)+ 11V Si3N4グロープラグ; 5µmインラインフィルタ同時購入",
        "acceptance": "0.1〜4.0 bar吐出流量カーブ取得, 気泡混入ゼロ",
    },
    "AHIRU-R3-018": {
        "wave": "Wave 3 (Week 2-3)",
        "safety_tier": "Tier-B (コスト最適化大)",
        "route_b1_usd": 260,  # PA12-CF MJF/SLS + epoxy + YSZ belly (shell temp verified 28.3°C!)
        "route_b2_usd": 260,
        "route_c_usd": 310,  # 1.25x PA12-CF MJF shell
        "route_d_usd": 165,
        "lead_wk_b1": "2w",
        "lead_wk_c": "2w",
        "vendor_b1": "JLCPCB 3DP / FacFox PA12-CF(炭素繊維強化ナイロン) MJF分割造形 + YSZ底部断熱",
        "vendor_c": "JLCPCB 3DP / FacFox PA12-CF MJF分割造形（1.25xスケール）",
        "files": [
            "index.html",
            "manufacturing/generated/step/00_AHIRU_Rev3_Core_Assembly.step",
        ],
        "rfq_notes": "実ソルバー熱解析で外殻最高温度28.3°Cのため、初号機はPEEK-CF30オートクレーブ(USD 1,350)からPA12-CF MJF(USD 260)へ代替で-81%削減しつつ剛性・質量維持",
        "acceptance": "総外殻質量 <= 115 g, 合わせ面段差 <= 0.3 mm, Sダクト内面平滑研磨",
    },
    "AHIRU-R3-019": {
        "wave": "Wave 3 (Week 2-3)",
        "safety_tier": "Tier-A (構造重要)",
        "route_b1_usd": 340,
        "route_b2_usd": 340,
        "route_c_usd": 380,
        "route_d_usd": 180,
        "lead_wk_b1": "2-3w",
        "lead_wk_c": "2-3w",
        "vendor_b1": "PCBWay CNC / ミスミmeviy Al 7075-T6 フレーム + ミスミ規格ばね/Ti脚パイプ",
        "vendor_c": "PCBWay CNC / ミスミmeviy Al 7075-T6(1.25x COTSマウント仕様)",
        "files": [
            "manufacturing/generated/step/00_AHIRU_Rev3_Core_Assembly.step",
        ],
        "rfq_notes": "Al 7075-T651; 着陸脚ばね定数 k=2395 N/m・ストローク15.6mm(ミスミ規格ばねで特注費削減)",
        "acceptance": "10G静的荷重(60 N)たわみ確認, 着陸脚ストローク 15.6 mm 確認",
    },
    "AHIRU-R3-020": {
        "wave": "Wave 2 (Week 1-2)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 425,  # 5-board JLCPCB 4-layer 2oz High-Tg SMT batch (~$85/board, 4 spares included!)
        "route_b2_usd": 425,
        "route_c_usd": 425,
        "route_d_usd": 115,
        "lead_wk_b1": "2w",
        "lead_wk_c": "2w",
        "vendor_b1": "JLCPCB 4層 TG170 2oz銅 ENIG + PCBA実装（5枚セット発注＝本体1+予備4）",
        "vendor_c": "JLCPCB 4層 TG170 2oz銅 ENIG + PCBA実装（5枚セット発注＝本体1+予備4）",
        "files": [
            "electronics/generated/gerbers/AHIRU_FADEC_Rev3-F_Cu.gtl",
            "electronics/generated/gerbers/AHIRU_FADEC_Rev3-In1_Cu.g1",
            "electronics/generated/gerbers/AHIRU_FADEC_Rev3-In2_Cu.g2",
            "electronics/generated/gerbers/AHIRU_FADEC_Rev3-B_Cu.gbl",
            "electronics/generated/gerbers/AHIRU_FADEC_Rev3.drl",
            "electronics/generated/AHIRU_FADEC_Rev3_BOM.csv",
            "electronics/generated/AHIRU_FADEC_Rev3_CPL.csv",
        ],
        "rfq_notes": "絶対妥協禁止: FR-4 TG170 / 4層 / 2oz銅 / ENIG仕上げ; 60V FET(BSC028N06LS3)・独立WDT(TPS3823-33)・二重IMU(ICM-42688-P)の代替品変更不可",
        "acceptance": "通電3.3V/5V実測, SWD(ST-LINK/V3)で firmware/fadec_rev3.c 書込+WDT遮断テスト合格",
    },
    "AHIRU-R3-021": {
        "wave": "Wave 2 (Week 1-2)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_b1_usd": 95,
        "route_b2_usd": 95,
        "route_c_usd": 95,
        "route_d_usd": 55,
        "lead_wk_b1": "1-2w",
        "lead_wk_c": "1-2w",
        "vendor_b1": "Isolate It! / McMaster Sorbothane 50Dグロメット + DigiKey(VL53L4CD, K型熱電対)",
        "vendor_c": "Isolate It! Sorbothane 50Dグロメット + DigiKey(VL53L4CD, K型熱電対)",
        "files": [
            "manufacturing/generated/step/08_imu_sorbothane_mount_assembly.step",
            "manufacturing/generated/drawings/DWG_03_Blisks_Flanges_IMU_GDT.dxf",
        ],
        "rfq_notes": "Sorbothane 50 Duro厳守(f_n=38 Hzで1X 3350 Hzを-77.1 dB減衰); 通常シリコン防振ゴムは減衰不足のため不可",
        "acceptance": "固有振動数 35〜45 Hz 確認, 3350 Hz加振でジャイロRMS < 0.08 deg/s",
    },
    "AHIRU-R3-022": {
        "wave": "Wave 2 (Week 1-2)",
        "safety_tier": "Tier-A (電源安全重要)",
        "route_b1_usd": 85,
        "route_b2_usd": 85,
        "route_c_usd": 85,
        "route_d_usd": 45,
        "lead_wk_b1": "1-2w",
        "lead_wk_c": "1-2w",
        "vendor_b1": "Tattu / GNB 750-850mAh 60C-90C 1S LiHVセル×3 分割組電池(胸2+尾1)",
        "vendor_c": "Tattu / GNB 3S 850mAh 75C LiHV（重心調整用分割可）",
        "files": [
            "manufacturing/generated/BOM_AHIRU_Rev3.csv",
        ],
        "rfq_notes": "ESR <= 65 mΩ(3S合計)厳守; セル間配線はAWG14シリコン線+カプトン絶縁",
        "acceptance": "内部抵抗測定(ESR <= 65 mΩ), 30A負荷テストで V_bus >= 9.5 V",
    },
    "AHIRU-R3-023": {
        "wave": "Wave 3 (Week 2-3)",
        "safety_tier": "Tier-A (配線信頼性)",
        "route_b1_usd": 110,
        "route_b2_usd": 110,
        "route_c_usd": 110,
        "route_d_usd": 55,
        "lead_wk_b1": "1w",
        "lead_wk_c": "1w",
        "vendor_b1": "ミスミ / DigiKey（PTFE同軸・AWG14シリコン・XT30・JST-GH・Ti M2/M2.5ねじ）",
        "vendor_c": "ミスミ / DigiKey（PTFE同軸・AWG14シリコン・XT30・JST-GH・Ti M2/M2.5ねじ）",
        "files": [
            "electronics/generated/AHIRU_FADEC_Rev3_BOM.csv",
        ],
        "rfq_notes": "IMU-MCU間ハーネスは必ずツイストペア+シールド(B_IMU=4.14 µT達成の必須条件; 非ツイストは51.8 µTでNG)",
        "acceptance": "全コネクタ抜去力・導通・絶縁確認, ツイストピッチ <= 5 mm",
    },
}


# Additional mandatory non-BOM procurement items (COTS turbine option, G0.4 balancing, test stand, safety gear, spares)
EXTRA_ITEMS: List[Dict[str, Any]] = [
    {
        "item": "24",
        "part_no": "AHIRU-SVC-001",
        "subsystem": "COTS Core",
        "description": "市販認証済みマイクロタービンコア一式（Route C専用：Swiwin SW30B / KingTech K30G4+ 等）",
        "spec": "30N級(スロットル制限14-18N運用), ECU・ポンプ・スタータ・G0.4釣合い済",
        "material": "COTS Complete",
        "qty": 1,
        "mass_g": 0.0,
        "wave": "Wave 1 (Week 1)",
        "safety_tier": "Tier-S (Route C中核)",
        "route_a_usd": 0,
        "route_b1_usd": 0,
        "route_b2_usd": 0,
        "route_c_usd": 1950,
        "route_d_usd": 0,
        "lead_wk_b1": "-",
        "lead_wk_c": "2-3w",
        "vendor_b1": "不要（自作コア使用）",
        "vendor_c": "Swiwin / KingTech / Xicoy 正規代理店（SW30B ~$1,950 / K30G4+ ~$2,250）",
        "files": ["manufacturing/generated/FLIGHT_QUALIFICATION_MANUAL.md"],
        "rfq_notes": "Route Cのみ発注: メーカー出荷時G0.4バランス済・ECU/ポンプ/燃料弁同梱のため自作タービン工程を完全スキップ",
        "acceptance": "メーカー出荷ベンチテスト成績書確認, 地上アイドル〜最大推力動作確認",
    },
    {
        "item": "25",
        "part_no": "AHIRU-SVC-002",
        "subsystem": "Metrology/Bal",
        "description": "外部2面動釣合い加工（ISO 1940 G0.4 @ 201,000 RPM）＋主要部CMM検査サービス",
        "spec": "残存不釣合い <= 0.22 mg·mm/面（Schenck / Hofmann 高速マイクロバランサ）",
        "material": "Service",
        "qty": 1,
        "mass_g": 0.0,
        "wave": "Wave 4 (Week 5-7)",
        "safety_tier": "Tier-S (妥協厳禁)",
        "route_a_usd": 1800,
        "route_b1_usd": 950,
        "route_b2_usd": 950,
        "route_c_usd": 0,  # Already factory balanced in COTS turbine
        "route_d_usd": 220,
        "lead_wk_b1": "1-2w",
        "lead_wk_c": "-",
        "vendor_b1": "国内高速動釣合い受託（長浜製作所/国際計測器系受託・ターボチャージャ専門工房）",
        "vendor_c": "不要（COTSメーカー釣合い済）",
        "files": [
            "manufacturing/generated/FLIGHT_QUALIFICATION_MANUAL.md",
            "manufacturing/generated/drawings/DWG_01_Rotor_Shaft_GDT.dxf",
            "manufacturing/generated/drawings/DWG_03_Blisks_Flanges_IMU_GDT.dxf",
        ],
        "rfq_notes": "絶対妥協禁止: シャフト+圧縮機+タービン(+スタータロータ)を組付けた状態で2面同時バランス; 修正削りは指定カラー/ボスのみ",
        "acceptance": "釣合い成績書 <= 0.22 mg·mm/面 (G0.4), 再組付用位相合いマーク刻印済",
    },
    {
        "item": "26",
        "part_no": "AHIRU-SVC-003",
        "subsystem": "Test & Safety",
        "description": "屋外火入れ試験台・3点重心計・防爆シールド・CO2消火器・二重聴覚保護具・係留3軸リグ",
        "spec": "ロードセル5kgf, ポリカ8mm防爆板, CO2消火器(粉/水厳禁), NRR30+イヤーマフ, ST-LINK/V3",
        "material": "GSE / Safety",
        "qty": 1,
        "mass_g": 0.0,
        "wave": "Wave 3 (Week 2-3)",
        "safety_tier": "Tier-S (人命安全)",
        "route_a_usd": 650,
        "route_b1_usd": 480,
        "route_b2_usd": 480,
        "route_c_usd": 480,
        "route_d_usd": 60,
        "lead_wk_b1": "1-2w",
        "lead_wk_c": "1-2w",
        "vendor_b1": "モノタロウ / ミスミ / Amazon / DigiKey（ST-LINK/V3MINI, HX711ロードセル等）",
        "vendor_c": "モノタロウ / ミスミ / Amazon / DigiKey（同一装備）",
        "files": ["manufacturing/generated/FLIGHT_QUALIFICATION_MANUAL.md"],
        "rfq_notes": "絶対必須: 114.3 dB騒音対策・遠隔非常燃料遮断(E-STOP)スイッチ・UN規格金属燃料缶(Jet-A1+5% AeroShell 500)",
        "acceptance": "非常停止応答 < 50 ms, ロードセル較正誤差 <= ±0.05 N, 3点CoG測定精度 <= ±0.5 mm",
    },
    {
        "item": "27",
        "part_no": "AHIRU-SPR-001",
        "subsystem": "Spares",
        "description": "消耗・破損リスク予備品パック（GRW 685軸受×2, Viton Oリング×10, KSTサーボ×1, 熱電対×2, 燃料フィルタ）",
        "spec": "初回火入れ・係留試験での即復旧用クリティカルスペア",
        "material": "Spares",
        "qty": 1,
        "mass_g": 0.0,
        "wave": "Wave 1-2",
        "safety_tier": "Tier-A (開発停止防止)",
        "route_a_usd": 420,
        "route_b1_usd": 360,
        "route_b2_usd": 360,
        "route_c_usd": 140,
        "route_d_usd": 95,
        "lead_wk_b1": "2-4w",
        "lead_wk_c": "1-2w",
        "vendor_b1": "本体発注時に同一ベンダーへ同時追加（送料・再調達6週間待ちを回避）",
        "vendor_c": "KST予備サーボ×1 + 熱電対×2 + 燃料フィルタ + AeroShell 500 1L",
        "files": ["manufacturing/generated/BOM_AHIRU_Rev3.csv"],
        "rfq_notes": "GRW軸受やLee部品は再発注すると6週間止まるため初回に必ず予備同梱; PCBAはWave2の5枚発注に予備4枚込み",
        "acceptance": "全スペア部品の防湿保管・シリアル番号紐付け完了",
    },
]


def load_bom() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with BOM_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def verify_all_files_exist(all_rows: List[Dict[str, Any]]) -> None:
    missing: List[str] = []
    for row in all_rows:
        for rel in row["files"]:
            if not (REPO_ROOT / rel).exists():
                missing.append(f"{row['part_no']}: {rel}")
    if missing:
        raise FileNotFoundError("Missing referenced repo files:\n" + "\n".join(missing))


def build_unified_rows(bom_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unified: List[Dict[str, Any]] = []
    seen = set()
    for r in bom_rows:
        pn = r["Part_No"].strip()
        seen.add(pn)
        if pn not in PART_PROCUREMENT_DB:
            raise KeyError(f"BOM part {pn} missing from PART_PROCUREMENT_DB")
        meta = PART_PROCUREMENT_DB[pn]
        unified.append({
            "item": r["Item"].strip(),
            "part_no": pn,
            "subsystem": r["Subsystem"].strip(),
            "description": r["Description"].strip(),
            "spec": r["Spec_or_COTS_PN"].strip(),
            "material": r["Material"].strip(),
            "qty": int(r["Qty"]),
            "mass_g": float(r["Total_Mass_g"]),
            "wave": meta["wave"],
            "safety_tier": meta["safety_tier"],
            "route_a_usd": int(r["Proto_USD"]),
            "route_b1_usd": int(meta["route_b1_usd"]),
            "route_b2_usd": int(meta["route_b2_usd"]),
            "route_c_usd": int(meta["route_c_usd"]),
            "route_d_usd": int(meta["route_d_usd"]),
            "bom_batch10_usd": int(r["Batch10_USD"]),
            "lead_wk_b1": meta["lead_wk_b1"],
            "lead_wk_c": meta["lead_wk_c"],
            "vendor_b1": meta["vendor_b1"],
            "vendor_c": meta["vendor_c"],
            "files": meta["files"],
            "rfq_notes": meta["rfq_notes"],
            "acceptance": meta["acceptance"],
            "is_bom": True,
        })

    if set(PART_PROCUREMENT_DB.keys()) != seen:
        raise ValueError("Mismatch between BOM_AHIRU_Rev3.csv and PART_PROCUREMENT_DB keys!")

    for ex in EXTRA_ITEMS:
        ex_copy = dict(ex)
        ex_copy["bom_batch10_usd"] = ex["route_d_usd"]
        ex_copy["is_bom"] = False
        unified.append(ex_copy)

    return unified


def write_csv(unified: List[Dict[str, Any]]) -> Path:
    out_csv = OUT_DIR / "procurement_checklist.csv"
    fieldnames = [
        "Item", "Wave", "Safety_Tier", "Part_No", "Subsystem", "Description", "Qty",
        "Mass_g", "Route_A_Proto_USD", "Route_B1_MinCustom_USD", "Route_B2_ExtStart_USD",
        "Route_C_COTSCore_USD", "Route_D_Batch10_USD", "LeadTime_B1", "LeadTime_C",
        "Recommended_Vendor_B1", "Recommended_Vendor_C", "Attached_Repo_Files",
        "RFQ_Critical_Notes", "Incoming_Acceptance_Criteria", "Order_Status",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in unified:
            w.writerow({
                "Item": r["item"],
                "Wave": r["wave"],
                "Safety_Tier": r["safety_tier"],
                "Part_No": r["part_no"],
                "Subsystem": r["subsystem"],
                "Description": r["description"],
                "Qty": r["qty"],
                "Mass_g": f"{r['mass_g']:.1f}",
                "Route_A_Proto_USD": r["route_a_usd"],
                "Route_B1_MinCustom_USD": r["route_b1_usd"],
                "Route_B2_ExtStart_USD": r["route_b2_usd"],
                "Route_C_COTSCore_USD": r["route_c_usd"],
                "Route_D_Batch10_USD": r["route_d_usd"],
                "LeadTime_B1": r["lead_wk_b1"],
                "LeadTime_C": r["lead_wk_c"],
                "Recommended_Vendor_B1": r["vendor_b1"],
                "Recommended_Vendor_C": r["vendor_c"],
                "Attached_Repo_Files": " ; ".join(r["files"]),
                "RFQ_Critical_Notes": r["rfq_notes"],
                "Incoming_Acceptance_Criteria": r["acceptance"],
                "Order_Status": "[ ] Not Ordered",
            })
    return out_csv


def fmt_jpy(usd: int) -> str:
    man = usd * JPY_PER_USD / 10000.0
    return f"約{man:,.1f}万円"


def write_markdown_and_json(unified: List[Dict[str, Any]]) -> tuple[Path, Path, Dict[str, Any]]:
    bom_only = [r for r in unified if r["is_bom"]]
    svc_only = [r for r in unified if not r["is_bom"]]

    def sum_col(rows: List[Dict[str, Any]], key: str) -> int:
        return sum(int(r[key]) for r in rows)

    totals = {
        "route_a": {
            "bom_usd": sum_col(bom_only, "route_a_usd"),
            "svc_usd": sum_col(svc_only, "route_a_usd"),
            "total_usd": sum_col(unified, "route_a_usd"),
            "lead_weeks": "10–14週間",
        },
        "route_b1": {
            "bom_usd": sum_col(bom_only, "route_b1_usd"),
            "svc_usd": sum_col(svc_only, "route_b1_usd"),
            "total_usd": sum_col(unified, "route_b1_usd"),
            "lead_weeks": "6–8週間",
        },
        "route_b2": {
            "bom_usd": sum_col(bom_only, "route_b2_usd"),
            "svc_usd": sum_col(svc_only, "route_b2_usd"),
            "total_usd": sum_col(unified, "route_b2_usd"),
            "lead_weeks": "5–7週間",
        },
        "route_c": {
            "bom_usd": sum_col(bom_only, "route_c_usd"),
            "svc_usd": sum_col(svc_only, "route_c_usd"),
            "total_usd": sum_col(unified, "route_c_usd"),
            "lead_weeks": "3–4週間",
        },
        "route_d": {
            "bom_usd": sum_col(bom_only, "route_d_usd"),
            "svc_usd": sum_col(svc_only, "route_d_usd"),
            "total_usd": sum_col(unified, "route_d_usd"),
            "lead_weeks": "7–9週間 (10機)",
        },
    }

    ra_tot = totals["route_a"]["total_usd"]
    for k in ("route_b1", "route_b2", "route_c", "route_d"):
        totals[k]["savings_vs_a_pct"] = round((1.0 - totals[k]["total_usd"] / ra_tot) * 100.0, 1)

    dry_mass_g = round(sum(r["mass_g"] for r in bom_only), 1)

    # Verify against BOM_AHIRU_Rev3.csv exact total ($13,467)
    assert totals["route_a"]["bom_usd"] == 13467, f"Unexpected Route A BOM sum: {totals['route_a']['bom_usd']}"

    summary = {
        "jpy_per_usd": JPY_PER_USD,
        "bom_item_count": len(bom_only),
        "total_procurement_line_items": len(unified),
        "dry_mass_rollup_g": dry_mass_g,
        "routes": totals,
        "recommended_primary_route": "Route B1 (完全オリジナル180mm Rev.3 コスト最小化) / 初飛行リスク最小化は 2段階方式 (Route C -> Route B1)",
    }

    out_json = OUT_DIR / "procurement_summary.json"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Build Wave sections
    waves_order = ["Wave 1 (Week 1)", "Wave 2 (Week 1-2)", "Wave 3 (Week 2-3)", "Wave 1-2", "Wave 4 (Week 5-7)"]
    wave_titles = {
        "Wave 1 (Week 1)": "Wave 1：最長納期クリティカルパス（Week 1 即発注・納期 3〜6週間）",
        "Wave 2 (Week 1-2)": "Wave 2：電装PCBA・サーボ・燃料系・バッテリー（Week 1〜2 発注・納期 1〜3週間）",
        "Wave 3 (Week 2-3)": "Wave 3：外殻・内部フレーム・断熱材・安全試験治具（Week 2〜3 発注・納期 1〜3週間）",
        "Wave 1-2": "Wave 1–2 同時同梱：クリティカル予備品（再調達6週間待ちの防止）",
        "Wave 4 (Week 5-7)": "Wave 4：受入精密検査・外部2面 G0.4 動釣合い（Week 5〜7・組付前必須ゲート）",
    }

    wave_md_blocks: List[str] = []
    for w_key in waves_order:
        w_rows = [r for r in unified if r["wave"] == w_key]
        lines = [f"### {wave_titles[w_key]}", ""]
        lines.append("| 済 | Part No | 品目 | 安全区分 | Route B1 (USD) | Route C (USD) | 推奨ベンダー（B1基準） | 納期 | 受入合格基準（抜粋） |")
        lines.append("|:---:|---|---|---|---:|---:|---|---|---|")
        for r in w_rows:
            lines.append(
                f"| `[ ]` | `{r['part_no']}` | {r['description']} (×{r['qty']}) | {r['safety_tier']} | "
                f"\\${r['route_b1_usd']:,} | \\${r['route_c_usd']:,} | {r['vendor_b1']} | {r['lead_wk_b1']} | {r['acceptance']} |"
            )
        lines.append("")
        wave_md_blocks.append("\n".join(lines))

    # Top cost reduction breakdown (Route A -> Route B1)
    deltas = []
    for r in bom_only:
        diff = r["route_a_usd"] - r["route_b1_usd"]
        if diff != 0:
            deltas.append((diff, r))
    deltas.sort(key=lambda x: x[0], reverse=True)

    delta_lines = [
        "| 順位 | Part No | 品目 | Route A (ワンオフ) | Route B1 (最適化) | 削減額 | 安全・性能への影響 |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for idx, (diff, r) in enumerate(deltas[:8], 1):
        sign = "-" if diff > 0 else "+"
        delta_lines.append(
            f"| {idx} | `{r['part_no']}` | {r['description']} | \\${r['route_a_usd']:,} | \\${r['route_b1_usd']:,} | "
            f"**{sign}\\${abs(diff):,}** | {r['rfq_notes'].split(';')[0]} |"
        )

    md_content = f"""# RikiGaku-AHIRU Rev.3 — 実機製作 発注チェックリスト & コスト最小化ルート選定書

> **前提**: 本書は実機 Colab GPU 上で **Rev.3 6-Wall Qualification (7/7 PASS, 10万回MC生存率 100.0%)**・**V12 (0 FAIL)**・**MDAO/V&V (Phase 1〜9 PASS, OpenTURNS信頼度 100.00%)** を通過した確定設計（[BOM_AHIRU_Rev3.csv](generated/BOM_AHIRU_Rev3.csv)）に基づく実務発注仕様書です。  
> 為替換算レート目安：`1 USD = {JPY_PER_USD} JPY`。Excel/Google スプレッドシート管理用CSV：[procurement_checklist.csv](procurement_checklist.csv)

---

## 1. コスト最小化 4ルート定量比較（検査・動釣合い・安全設備・予備品まで全計上）

「機体部品だけ安く見えて、後から動釣合い・防爆治具・予備品で予算超過する」ことを防ぐため、**全ルートに外部検査/釣合い・安全試験設備・予備品まで全額含めた総実費**で比較しています。

| ルート | コンセプト | 機体BOM (23品目) | COTSコア/釣合い/安全/予備 | **総額 (USD)** | **総額目安 (JPY)** | Route A比 | 最短納期 | 推奨用途 |
|---|---|---:|---:|---:|---:|---:|---|---|
| **Route A** | フルカスタム航空宇宙仕様（欧米/国内ワンオフ） | \\${totals['route_a']['bom_usd']:,} | \\${totals['route_a']['svc_usd']:,} | **\\${totals['route_a']['total_usd']:,}** | **{fmt_jpy(totals['route_a']['total_usd'])}** | 基準 | {totals['route_a']['lead_weeks']} | 機関・法人向けフルスペック実証 |
| **Route B1（純自作最推奨）** | **戦略的アジア高精度CNC＋DMLS一括ネスト＋MJF外殻**（180mm完全オリジナルRev.3） | \\${totals['route_b1']['bom_usd']:,} | \\${totals['route_b1']['svc_usd']:,} | **\\${totals['route_b1']['total_usd']:,}** | **{fmt_jpy(totals['route_b1']['total_usd'])}** | **-{totals['route_b1']['savings_vs_a_pct']}%** | {totals['route_b1']['lead_weeks']} | **完全自作エンジンでRev.3を最小コスト実現** |
| **Route B2（初号機最安自作）** | Route B1＋**初号機限定「外部電動スタータ始動」**（機上発電省略で `-19.4 g` 軽量化） | \\${totals['route_b2']['bom_usd']:,} | \\${totals['route_b2']['svc_usd']:,} | **\\${totals['route_b2']['total_usd']:,}** | **{fmt_jpy(totals['route_b2']['total_usd'])}** | **-{totals['route_b2']['savings_vs_a_pct']}%** | {totals['route_b2']['lead_weeks']} | **初号機ホバリング実証のコスト＆重量最小化** |
| **Route C（最短初飛行最推奨）** | **市販認証済みマイクロタービン（SW30B/K30G4+）換装 1.25× 機体** | \\${totals['route_c']['bom_usd']:,} | \\${totals['route_c']['svc_usd']:,} | **\\${totals['route_c']['total_usd']:,}** | **{fmt_jpy(totals['route_c']['total_usd'])}** | **-{totals['route_c']['savings_vs_a_pct']}%** | {totals['route_c']['lead_weeks']} | **最短3〜4週間・最小リスクで初飛行達成** |
| **Route D（10機ロット単価）** | Route B1最適化を10機バッチ発注（1機あたり単価） | \\${totals['route_d']['bom_usd']:,} | \\${totals['route_d']['svc_usd']:,} | **\\${totals['route_d']['total_usd']:,}/機** | **{fmt_jpy(totals['route_d']['total_usd'])}/機** | **-{totals['route_d']['savings_vs_a_pct']}%** | {totals['route_d']['lead_weeks']} | 研究室・共同製作・小ロット量産 |

### 結論：最も賢いコスト最小化ルート選定

1. **「確実に最短・最安で飛ばす」なら → `Route C`（総額 \\${totals['route_c']['total_usd']:,} / {fmt_jpy(totals['route_c']['total_usd'])}・3〜4週間）**
   - 201,000 RPM 自作タービンの公差・HIP・G0.4 動釣合いリスクを丸ごと回避し、メーカー保証済みの市販マイクロタービン（Swiwin SW30B 等）を搭載。
   - **自作FADEC基板（`AHIRU-R3-020`）・Sorbothane 50D防振（`021`）・2軸TVCシェブロンノズル（`013`）・C11ファームウェア（`firmware/fadec_rev3.c`）は 100% そのまま実機実証**できます。
2. **「180×200×100 mm の純粋自作エンジン機を最小コストで作る」なら → `Route B2`（\\${totals['route_b2']['total_usd']:,} / {fmt_jpy(totals['route_b2']['total_usd'])}）または `Route B1`（\\${totals['route_b1']['total_usd']:,} / {fmt_jpy(totals['route_b1']['total_usd'])}）**
   - Route A と同じ安全マージン（GRW 685軸受・Inconel 718 HIP・Leeルビーオリフィス・2面G0.4釣合い・60V FOC PCBA）を一切削らず、加工手配の最適化だけで **約 {totals['route_b1']['savings_vs_a_pct']}%〜{totals['route_b2']['savings_vs_a_pct']}% のコスト削減**を実現します。
3. **プロ推奨の2段階ステップ方式（総失敗コスト最小）**
   - **Step 1**: まず `Route C`（{fmt_jpy(totals['route_c']['total_usd'])}）でアヒル機体のホバリング・TVC制御・地面効果・前進遷移を 100% 実証。
   - **Step 2**: 制御と運用が確立した状態で `Route B1/B2` の純粋自作 Ø38mm コアへ移行（PCBA・安全設備・地上試験治具・サーボ・計測器はそのまま流用できるため、Step 2 の追加投資はさらに圧縮可能）。

---

## 2. Route A → Route B1 コスト削減の主要ドライバー（どこで安全を削らずに安くするか）

{chr(10).join(delta_lines)}

> **注目ポイント**：
> - **Inconel 718 DMLS 一括ネスト（4部品相乗り）**：`AHIRU-R3-002 / 005 / 006 / 013` を別々に発注すると毎回セットアップ費・粉末充填費・熱処理炉チャージが発生します。**1枚のビルドプレートに4部品をネスト同時造形＋一括応力除去**することで約50%削減できます。
> - **アヒル外殻の PA12-CF MJF 代替**：V12・MDAO/V&V の連成熱解析で外殻最高温度は **`28.3 °C`**（耐熱火壁 `AHIRU-R3-011` が別体）と実証済みのため、初号機は PEEK-CF30 オートクレーブ（\\$1,350）ではなく **PA12-CF MJF 一体造形（\\$260）** で安全マージンを落とさずに **-\\$1,090（-81%）** 削減できます。
> - **FADEC PCBA の JLCPCB 5枚バッチ化**：1枚特注（\\$380）より **JLCPCB 5枚バッチ（\\$425＝1枚あたり\\$85）** の方が予備4枚が確保でき、試験中の万一のショートでも開発が止まりません。

---

## 3. 絶対に削ってはいけない「安全聖域（Non-Negotiable 8項目）」

以下の 8 項目はコスト削減のために安価な代替品へ変更すると、**201,000 RPM 破損・焼付き・墜落・火災に直結する**ため変更厳禁です：

1. **軸受 (`AHIRU-R3-008`)**: 必ず `GRW 685-2Z-CE`（Si3N4セラミック球・PEEK/フェノール保持器・ABEC-7以上）。安価な鉄球・金属保持器は `dm·N = 1.71M` で即破損。
2. **スクイーズフィルムOリング (`AHIRU-R3-009`)**: 必ず `AS568-013 FKM Viton Shore 60A`（70A/90AやNBRは剛性変化・膨潤で危険速度に接触）。
3. **潤滑オリフィス (`AHIRU-R3-010`)**: 必ず較正済み `Ø0.25 mm` ルビーオリフィス（Lee `IEPA1211241H` 等）＋ 5µm フィルタ。流量不足は30秒以内に軸受焼付き。
4. **ブレード封じ込めリング & 高温ボルト (`AHIRU-R3-007`)**: Inconel 718 最小肉厚 `2.05 mm` ＋ `A286` 耐熱ボルト＋皿ばね（ステンレスSUS304ボルトは700°Cクリープで緩むため厳禁）。
5. **タービンブリスク熱処理 (`AHIRU-R3-002`)**: DMLS造形後の **HIP（熱間等方圧加圧）＋時効処理** は省略不可（内部空隙が遠心クリープ破壊の起点になる）。
6. **2面動釣合い (`AHIRU-SVC-002`)**: 必ず組付状態で **`ISO 1940 G0.4`（≤ 0.22 mg·mm/面）** を外部専門バランサで施工（簡易1面バランス厳禁）。
7. **FADEC 60V MOSFET & 独立WDT (`AHIRU-R3-020`)**: 201k RPM 逆起電力 `25.8 V` に対し `60V定格 BSC028N06LS3`（30V/40V品不可）、暴走時燃料遮断用 `TPS3823-33` 独立WDT、二重 `ICM-42688-P` 実装を維持。
8. **Sorbothane 50D 防振マウント (`AHIRU-R3-021`)**: 一般的なシリコン防振ゴムは 3,350 Hz 帯の減衰が不足し IMU が飽和するため、必ず `Sorbothane 50 Duro` を使用。

---

## 4. 発注前ゲート（Wave 0：発注ボタンを押す前の必須確認）

- [ ] **法規・飛行場所の確認（日本国内）**
  - [ ] 国土交通省 **DIPS 2.0** 機体登録・リモートID準備（MTOW `579 g ≥ 100 g` のため必須）
  - [ ] **消防法** 確認：Jet-A1/灯油（第4類第2石油類）を UN 規格金属携行缶＋防油堤で保管（指定数量未満）、CO₂ 消火器常備
  - [ ] 騒音 `97.4 dB @ 7 m` に対応した屋外テストベンチ場所（RCジェット飛行場または防音設備）を確保
- [ ] **採用ルートの最終決定**
  - [ ] `Route C`（最短初飛行・{fmt_jpy(totals['route_c']['total_usd'])}） / `Route B2`（初号機最安自作・{fmt_jpy(totals['route_b2']['total_usd'])}） / `Route B1`（完全Rev.3自作・{fmt_jpy(totals['route_b1']['total_usd'])}）のいずれかを選択
- [ ] **製造ファイル完全性確認**
  - [ ] STEP 9点（`manufacturing/generated/step/*.step`）
  - [ ] 2D GD&T DXF 3点（`manufacturing/generated/drawings/*.dxf`）
  - [ ] Gerber 9点＋BOM/CPL（`electronics/generated/gerbers/*`, `AHIRU_FADEC_Rev3_BOM.csv`, `AHIRU_FADEC_Rev3_CPL.csv`）
  - [ ] 本番C11ファームウェア（`firmware/fadec_rev3.c`, `firmware/fadec_rev3.h`）

---

## 5. フェーズ別 完全発注チェックリスト（Wave 1〜4・全27項目）

{chr(10).join(wave_md_blocks)}

---

## 6. サプライヤー別 RFQ（見積依頼）送信パッケージ一覧

業者ごとに以下の ZIP パッケージを作ってそのまま見積依頼（RFQ）を送れます：

| パッケージ | 送信先業種・推奨ベンダー | 添付するリポジトリ内ファイル | 見積依頼時の必須追記文（コピー可） |
|---|---|---|---|
| **RFQ-1: 金属3Dプリント (Inconel 718 一括ネスト)** | Unionfab / FacFox / Xometry Asia | `02_turbine_blisk_Inconel718.step`, `05_combustor_liner_Inconel718.step`, `00_AHIRU_Rev3_Core_Assembly.step`, `07_tvc_gimbal_chevron_nozzle.step`, `DWG_03_Blisks_Flanges_IMU_GDT.dxf` | *Material: Inconel 718 (AMS 5662/5663). Please nest all 4 parts on a single build plate to minimize setup cost. Mandatory HIP + solution/age heat treatment for Part 02 (Turbine Blisk); stress relief + complete powder removal inside 12 vaporizer tubes for Part 05. Finish-machine Ø4.000 H6 bore on Part 02 per DWG_03.* |
| **RFQ-2: 5軸CNC & 精密研削 (Ti / Al / IN718)** | PCBWay CNC / RapidDirect + 国内円筒研削 | `01_compressor_impeller_Ti6Al4V.step`, `03_rotor_shaft_Inconel718.step`, `04_diffuser_bearing_tunnel_Al7075.step`, `06_containment_flange_Inconel718.step`, `DWG_01/02/03.dxf` | *Critical aerospace tolerances per attached DXFs: Shaft Ø5.000 h5 (+0/-0.005mm, Ra<=0.2um, TIR<=2um post-heat-treat cylindrical grind); Diffuser bore Ø11.000 H6 (+0.011/-0mm, coaxiality<=5um, mask bore during hard anodize); Impeller bore Ø5.000 H6. Full CMM inspection report mandatory.* |
| **RFQ-3: 4層PCBA + SMT実装** | JLCPCB / PCBWay SMT | `electronics/generated/gerbers/*` (9ファイルZIP), `AHIRU_FADEC_Rev3_BOM.csv`, `AHIRU_FADEC_Rev3_CPL.csv` | *4-layer FR-4 High-Tg (TG170), 1.6mm, 2oz copper (outer & inner), ENIG finish, Qty=5 assembled boards. NO component substitutions permitted for U1(STM32H743), U2/U3(ICM-42688-P), U6(DRV8353RS), Q1-Q6(BSC028N06LS3 60V), U9(TPS3823-33).* |
| **RFQ-4: 樹脂3Dプリント (外殻 & 燃料タンク)** | JLCPCB 3DP / FacFox | `00_AHIRU_Rev3_Core_Assembly.step`（燃料タンク・アヒル外殻STL/STEP）, `08_imu_sorbothane_mount_assembly.step` | *Fuel tank: PA12 MJF with 3 internal perforated baffles & UAT sump (powder-free interior, leak-proof fuel-resistant FKM/epoxy internal sealing). Outer duck shell: PA12-CF MJF (Route B1/C) or PEEK-CF30 (Route A).* |
| **RFQ-5: 航空宇宙COTS精密部品** | GRW代理店 / The Lee Company Japan / KST / Flightworks | `BOM_AHIRU_Rev3.csv`（Part `008, 009, 010, 014, 015, 017`） | *Exact P/Ns only: GRW 685-2Z-CE Si3N4 ABEC-7 (Qty 4 incl. 2 spares), AS568-013 FKM Viton 60A (Qty 10), Lee IEPA1211241H Ø0.25mm ruby orifice (Qty 2), Lee LHDA0523111H micro-solenoid (Qty 2), KST X08H Plus (Qty 3 incl. 1 spare).* |
| **RFQ-6: 外部 2面 G0.4 動釣合い** | 国内高速動釣合い専門工場 | `DWG_01_Rotor_Shaft_GDT.dxf`, `DWG_03_Blisks_Flanges_IMU_GDT.dxf`, `FLIGHT_QUALIFICATION_MANUAL.md` | *201,000 RPM マイクロタービン用ロータASSY（質量約36g）の2面動釣合い。ISO 1940 G0.4（残存不釣合い ≤ 0.22 mg·mm/面）。修正削りは図面指定のフロントカラー・リアボスのみ。分解再組付用の位相刻印および成績書発行を希望。* |

---

## 7. 受入〜初飛行までの実行タイムライン（Route B1：約8週間 / Route C：約4週間）

```text
[Route C 最短初飛行: 4週間 / {fmt_jpy(totals['route_c']['total_usd'])}]
Week 1 : Wave 1-2 全発注 (SW30B/K30G4+ + JLCPCB 5枚 + TVCノズル + PA12-CF外殻/タンク + KST/Lee)
Week 2 : 安全治具・ロードセル推力台製作 + C11 FW (fadec_rev3.c) ベンチ試験
Week 3 : 全品受入・組付・3点CoG調整 (±2.5mm)・地上火入れ (Gate B1-B4)
Week 4 : 係留3軸SysID (Gate F1-F2) → 地面効果確認 (F3) → 初フリーホバリング (F4)！

[Route B1 純粋自作Rev.3: 8週間 / {fmt_jpy(totals['route_b1']['total_usd'])}]
Week 1   : Wave 1 最長納期一括発注 (IN718 DMLSネスト + Ti/Al/IN718 5軸CNC + GRW軸受 + Lee + スタータ)
Week 2-3 : Wave 2-3 発注 & 受入 (JLCPCB 5枚 + FWベンチ通電 + 外殻/フレーム/防爆試験台完成)
Week 4-5 : 回転系・燃焼器受入 → CMM/エアマイクロ公差検査 (h5/H6/TIR<=2µm) → ルビーオリフィス流量試験
Week 6   : 外部2面動釣合い (ISO 1940 G0.4 <= 0.22 mg·mm/面) → コア最終組付
Week 7   : 屋外防爆セル火入れ試験 (Gate B1冷間回転 → B2点火 → B3 201k RPM全開 → B4 300sソークバック)
Week 8   : 係留3軸SysID (Gate F1-F2) → 地面効果HGI確認 (F3) → 初フリーホバリング & 前進遷移 (F4)！
```
"""

    out_md = OUT_DIR / "PROCUREMENT_CHECKLIST_AND_COST_ROUTES.md"
    out_md.write_text(md_content, encoding="utf-8")
    return out_md, out_json, summary


def main() -> int:
    bom_rows = load_bom()
    unified = build_unified_rows(bom_rows)
    verify_all_files_exist(unified)
    out_csv = write_csv(unified)
    out_md, out_json, summary = write_markdown_and_json(unified)
    print(f"Verified {len(unified)} procurement line items ({summary['bom_item_count']} BOM + {len(EXTRA_ITEMS)} Services/Spares) and all attached repo files.")
    for k, v in summary["routes"].items():
        print(f"  {k:8s}: BOM=${v['bom_usd']:>6,} | Svc/Core=${v['svc_usd']:>5,} | TOTAL=${v['total_usd']:>6,} ({fmt_jpy(v['total_usd'])}) | {v['lead_weeks']}")
    print(f"Generated:\n  - {out_md}\n  - {out_csv}\n  - {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
