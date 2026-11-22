# RikiGaku-AHIRU（力学アヒル）

[![Open MDAO/V&V in Colab (A100 GPU)](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sc8z35a-collab/RikiGaku-AHIRU/blob/main/colab/RikiGaku_AHIRU_MDAO_VV_A100.ipynb)
[![Open V12 12-Domain Suite in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sc8z35a-collab/RikiGaku-AHIRU/blob/main/colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb)

力学の法則・物理法則に基づいて本物のジェットエンジンで空を飛ぶ、**全長 18 cm × 幅 10 cm × 高さ 20 cm** のアヒル型飛行置物の超高精細 3D CAD 解剖図＆リアルタイム物理稼働シミュレーター、および **Google Colab Pro（L4 / A100 GPU）対応・航空宇宙グレード完全連成 MDAO / V&V マルチフィジックス検証環境** です。

## 外形寸法・基本諸元（設計目標）

| 項目 | 数値 |
|---|---|
| 外形サイズ | 全長 **180 mm (18 cm)** × 幅 **100 mm (10 cm)** × 高さ **200 mm (20 cm)** |
| 発明エンジン | **AHIRU-μTJ42V**（垂直軸・折り返し環状燃焼室マイクロターボジェット） |
| 乾燥質量 / 離陸質量 | **480 g** / **592 g**（Jet-A1 航空ケロシン燃料 140 mL = 112 g 搭載時） |
| 機体重量 $W = mg$ | **5.81 N** |
| 最大実効推力 $T_{\text{net}}$ | **11.43 N**（約 1.16 kgf） |
| 推力重量比 (TWR) | **1.97**（スロットル約 51% でホバリング、全開で急上昇・高速前進） |
| 連続ホバリング時間 | **約 5.2 分** |

## 3D CAD ビューアー起動方法

[index.html](index.html) をモダンブラウザ（WebGL 対応）で開くと、純白背景・UI内文字ゼロのインタラクティブ 3D CAD 解剖ビューアーが起動します。

## 最先端航空宇宙グレード完全連成 MDAO / V&V（Phase 0〜9・実ソルバー総動員）

上の左バッジから [`colab/RikiGaku_AHIRU_MDAO_VV_A100.ipynb`](colab/RikiGaku_AHIRU_MDAO_VV_A100.ipynb) を開き、**`ランタイム` → `すべてのセルを実行`（`Ctrl+F9`）** を実行すると、簡易計算・モック一切なしで全実ソルバーを JSON + HDF5 チェックポイント経由で完全連成させ、FAIL項目がある場合は **OpenMDAO SLSQP で成立解を自動逆算・実ソルバー再検証** まで完了します。

| Phase | 連成検証領域 | 実行される実ソルバー |
|---:|---|---|
| **0** | 環境構築・Google Drive・GPU/CPU診断 | `apt` + `micromamba` (`SU2_CFD`) + `pip` 全導入＆スモークテスト |
| **1** | 3D幾何整合・動的衝突・CTE熱膨張 | `python-fcl` (BVH静的干渉体積・±14°スウェプト距離場) / `trimesh` / `CadQuery` |
| **2** | 詳細燃焼化学動力学 & 非設計点サイクル | **`Cantera`** (`nDodecane_Reitz` Jet-A1サロゲート: $c_p(T), T_{\text{ad}}, S_L, \tau_{\text{ign}}$, LBO) + **`OpenMDAO`** |
| **3** | 圧縮性RANS CFD・地面効果(IGE/HGI)・GCI | **`Gmsh`** (境界層メッシュ) + **`mpirun SU2_CFD`** (RANS $k$-$\omega$ SST: 吸気DC60 / IGE・HGI / 空力 + Roache GCI) |
| **4** | 共役熱伝達・輻射・停止後300秒ソークバック | **`CalculiX (ccx)`** 3D `*HEAT TRANSFER` + `*RADIATE` (Stefan-Boltzmann) + 接触熱抵抗 |
| **5** | 100%/125%熱応力連成FEA & ローター力学 | **`CalculiX (ccx)`** 3D C3D8 遠心＋熱応力FEA + **`ROSS 3.0`** (Campbell・危険速度・ISO 1940・ジャイロ軸受) |
| **6** | パワエレ過渡回路・ブラウンアウト・フェイルセーフ | **`PySpice` / `Ngspice`** (温度連成ESR・始動突入・サージ・10ms以内ハード遮断) |
| **7** | 6-DOF非線形飛行制御・スロッシング・GPU大量MC | **`CasADi`** NMPC + `control` LQR + **`MuJoCo`** 接触着地 + **`JAX`** GPU並列 6-DOF モンテカルロ |
| **8** | 不確実性定量化(UQ) & グローバル感度解析 | **`OpenTURNS`** 多項式カオス展開(PCE) 破壊確率 $P_f$ + **`SALib`** Sobol ($S_1, S_T$) |
| **9** | 統合Plotlyダッシュボード & 自動最適設計 | **`Plotly`** 対話型HTMLレポート + **`OpenMDAO` SLSQP** 自動再設計 & `CalculiX`/`Ngspice`/`OpenTURNS` 再検証 |

### 12領域クイック・スクリーニング検証（AHIRU-V12）

全12領域（C11 MISRAファームウェア静的解析・SPIN/Z3形式検証・SCRAM FTA・SLM/5軸CNC DFM含む）の高速一括検証は [`colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb`](colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb) を使用してください。

### ローカルCLI実行

```bash
# Phase 1-9 完全連成 MDAO / V&V
python3 -m mdao_vv.run_pipeline --work-dir ./mdao_out

# V12 12領域クイック検証
python3 -m verification.run_all --html index.html --out ./verification_out
```