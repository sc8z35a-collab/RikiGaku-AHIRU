# RikiGaku-AHIRU（力学アヒル）

[![Open MDAO/V&V in Colab (A100 GPU)](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sc8z35a-collab/RikiGaku-AHIRU/blob/main/colab/RikiGaku_AHIRU_MDAO_VV_A100.ipynb)
[![Open V12 12-Domain Suite in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sc8z35a-collab/RikiGaku-AHIRU/blob/main/colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb)

力学の法則・物理法則に基づいて本物のジェットエンジンで空を飛ぶ、**全長 18 cm × 幅 10 cm × 高さ 20 cm** のアヒル型飛行置物の超高精細 3D CAD 解剖図＆リアルタイム物理稼働シミュレーター、および **Google Colab Pro（L4 / A100 GPU）対応・航空宇宙グレード完全連成 MDAO / V&V マルチフィジックス検証環境** です。

## 外形寸法・基本諸元（Rev.2 実機飛行対応・実測値）

| 項目 | 数値（Rev.2 58パーツ 100%水密ソリッドCAD実測） |
|---|---|
| 外形サイズ | 全長 **180.00 mm** × 幅 **99.98 mm** × 高さ **200.00 mm**（誤差 0.024 mm） |
| パーツ構成 / 水密性 | **58パーツ**（非水密 0・法線反転 0・燃焼室開口 0°・静的/±14°動的FCL干渉 0） |
| 発明エンジン | **AHIRU-μTJ42V Rev.2**（垂直軸・折り返し環状燃焼室・ブリード冷却インコネル718ブリスク・201,000 RPM定格・GRW 685 Si3N4軸受 + 60A Viton Oリング・インコネル718主軸・360°ブレード飛散封じ込めリング） |
| 乾燥質量 / 離陸質量 | **460.6 g** / **572.2 g**（290°馬蹄型サドルタンク Jet-A1 燃料 **139.5 mL = 111.6 g**＋3枚アンチスロッシュバッフル搭載） |
| バッテリー・電装 | 分割重心バランス **3S 705 mAh 60C LiHV**（胸部2セル＋尾部カウンターウェイト1セル・ZrO₂断熱防火壁）＋ Wye-Start/Delta-Gen スプラグクラッチ付スターター発電機 |
| 最大実効推力 $T_{\text{net}}$ | **13.14〜14.39 N**（V12 1D+2D CFD / Cantera+OpenMDAO 実測） |
| 推力重量比 (TWR) | **2.34〜2.56**（ホバリングトリム角 Wet **2.85°** / Dry **4.52°**、±14° TVC 余裕 ±9.48°） |
| 連続ホバリング時間 | **5.06〜6.44 分**（実タンク容量 139.5 mL 実測） |
| 音響・衝撃・信頼性 | 12枚シェブロンノズル **97.4 dB @ 7 m** / 26.8 mm オレオTi脚（MuJoCo 17.3 G・ノズル底面余裕 16.9 mm・転倒なし） / **OpenTURNS 50,000回 PCE信頼性 100.000%** |

## 3D CAD ビューアー起動方法

[index.html](index.html) をモダンブラウザ（WebGL 対応）で開くと、純白背景・UI内文字ゼロのインタラクティブ 3D CAD 解剖ビューアー（精密サーボIK・2軸TVCジンバル・チョークドシェブロン排気プルーム対応）が起動します。

## 検証結果サマリー（実ソルバー総動員・モック一切なし）

- **12領域 AHIRU-V12 検証（`python3 -m verification.run_all`）**: **52 / 52 PASS（0 FAIL / 0 MARGINAL）**
- **Phase 1〜9 完全連成 MDAO / V&V（`python3 -m mdao_vv.run_pipeline`）**: **`Baseline Verdict: PASS`（29 / 29 項目すべて PASS・Phase 8 OpenTURNS 信頼性 100.000%）**

## 最先端航空宇宙グレード完全連成 MDAO / V&V（Phase 0〜9・実ソルバー総動員）

上の左バッジから [`colab/RikiGaku_AHIRU_MDAO_VV_A100.ipynb`](colab/RikiGaku_AHIRU_MDAO_VV_A100.ipynb) を開き、**`ランタイム` → `すべてのセルを実行`（`Ctrl+F9`）** を実行すると、簡易計算・モック一切なしで全実ソルバーを JSON + HDF5 チェックポイント経由で完全連成させ、FAIL項目がある場合は **OpenMDAO SLSQP で成立解を自動逆算・実ソルバー再検証** まで完了します。

| Phase | 連成検証領域 | 実行される実ソルバー | Rev.2 実測判定 |
|---:|---|---|---|
| **0** | 環境構築・Google Drive・GPU/CPU診断 | `apt` + `micromamba` (`SU2_CFD`) + `pip` 全導入＆スモークテスト | **READY** |
| **1** | 3D幾何整合・動的衝突・CTE熱膨張 | `python-fcl` / `trimesh` / Node.js抽出 | **PASS**（干渉 0/24、TVC最小隙間 +9.04 mm、タービン熱間隙間 0.260 mm） |
| **2** | 詳細燃焼化学動力学 & 非設計点サイクル | **`Cantera`** (`nDodecane_Reitz`) + **`OpenMDAO`** | **PASS**（$T_{\text{net}}=14.39\text{ N}$、TWR 2.56、TIT 1165 K、持続 5.06 分） |
| **3** | 圧縮性/非圧縮性 RANS CFD・IGE/HGI・GCI | **`Gmsh`** (BLメッシュ) + **`mpirun SU2_CFD`** (RANS/INC\_RANS SST) | **PASS**（$\eta_d=0.9970$、DC60 0.190、$\Delta T_{\text{HGI}}=10.5\text{ K}$、空力 GCI 0.73%） |
| **4** | 共役熱伝達・輻射・停止後300秒ソークバック | **`CalculiX (ccx)`** 3D DC3D8 `*HEAT TRANSFER` + `*RADIATE` | **PASS**（電池 22.9 °C、燃料壁 48.9 °C、Alフレーム 34.5 °C、ライナー 723.8 °C） |
| **5** | 100%/125%熱応力連成FEA & ローター力学 | **`CalculiX (ccx)`** 3D C3D8 + **`ROSS 3.0`** | **PASS**（圧縮機 SF 2.35、タービン SF 1.72、危険速度分離 38.1%/64.4%、DN 1.71M） |
| **6** | パワエレ過渡回路・ブラウンアウト・フェイルセーフ | **`PySpice` / `Ngspice`** | **PASS**（$V_{\text{bus,min}}=9.48\text{ V}$、3.3V `[3.190, 3.357] V`、遮断 0.005 ms） |
| **7** | 6-DOF非線形飛行制御・スロッシング・GPU並列MC | **`CasADi`** NMPC + `control` LQR + **`MuJoCo`** + **`JAX`** MC | **PASS**（NMPC 0.41°、着地 17.6 G/転倒なし、MC 生存率 99.71%、3σ 21.5°） |
| **8** | 不確実性定量化(UQ) & グローバル感度解析 | **`OpenTURNS`** PCE ($P_f$) + **`SALib`** Sobol ($S_1, S_T$) | **PASS**（PCE $Q^2=0.99530$、システム信頼性 **100.000%** / $P_f=0$） |
| **9** | 統合Plotlyダッシュボード & 自動最適設計 | **`Plotly`** + **`OpenMDAO` SLSQP** | **Baseline Verdict: PASS** |

### 12領域クイック・スクリーニング検証（AHIRU-V12：52 / 52 PASS）

全12領域（C11 MISRAファームウェア静的解析・SPIN/Z3形式検証・SCRAM FTA・SLM/5軸CNC DFM含む）の高速一括検証は [`colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb`](colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb) を使用してください。

### ローカルCLI実行

```bash
# Phase 1-9 完全連成 MDAO / V&V
python3 -m mdao_vv.run_pipeline --work-dir ./mdao_out --no-resume

# V12 12領域クイック検証
python3 -m verification.run_all --html index.html --out ./verification_out
```