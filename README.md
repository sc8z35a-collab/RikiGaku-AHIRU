# RikiGaku-AHIRU（力学アヒル）

[![Open In Colab (A100 GPU)](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sc8z35a-collab/RikiGaku-AHIRU/blob/main/colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb)

力学の法則・物理法則に基づいて本物のジェットエンジンで空を飛ぶ、**全長 18 cm × 幅 10 cm × 高さ 20 cm** のアヒル型飛行置物の超高精細 3D CAD 解剖図＆リアルタイム物理稼働シミュレーター、および **Google Colab Pro（NVIDIA A100 GPU）対応・全12領域一括物理検証システム（AHIRU-V12）** です。

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

## 全12領域・一括物理検証システム（Google Colab Pro A100 GPU ワンクリック実行）

上の **「Open in Colab」バッジ** から [`colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb`](colab/RikiGaku_AHIRU_V12_Verification_A100.ipynb) を開き、ランタイムを **A100 GPU** にして **`ランタイム` → `すべてのセルを実行`（`Ctrl+F9`）** を押すだけで、`index.html` から54個の3D CADパーツ（53,127三角形）をビット完全抽出し、以下の全12領域を一括検証して **インタラクティブHTMLダッシュボード・12領域高解像度解析図・全商用CAE互換デッキ一式（ZIP）** を自動生成します。

| # | 検証領域 | Colab Pro (A100 GPU) ライブ実行エンジン | 商用ツール互換エクスポート |
|---:|---|---|---|
| 1 | 3D CAD・静的/動的DMU衝突・6σ公差累積 | Node.js抽出 / `trimesh` / `python-fcl` / Möller-Trumbore / `CadQuery` / `OpenSCAD` / A100 10万回モンテカルロGD&T | STEP AP214, 54 STL, OpenSCAD |
| 2 | CFD・ターボ機械・燃焼・空力 | `Cantera` (詳細化学反応・PSR) / A100 2D圧縮性Euler CFD / `XFOIL` / `OpenFOAM` | OpenFOAM, SU2 `.cfg` |
| 3 | 共役熱伝達(CHT)・熱輻射・熱暴走 | A100 2D/3D CHT FVM + 灰体輻射 + 停止後15分熱ソークバック + LiHV熱暴走 | CalculiX/Abaqus 熱 `.inp` |
| 4 | 構造強度(FEA)・熱応力・衝撃封じ込め・破壊力学 | `CalculiX (ccx)` 3D FEA + `Gmsh` + 遠心バースト + ブレード飛散封じ込め + Goodman/Paris LEFM | Abaqus/CalculiX `.inp` |
| 5 | 超高速ローター力学・軸受・空力騒音(CAA) | `ROSS` + 20-DOF FEジャイロCampbell線図 + Si3N4軸受DN/$L_{10h}$ + AGMA歯車 + Lighthill/FW-H CAA | Campbell/不釣り合い応答データ |
| 6 | マルチボディ(MBD)・燃料スロッシング | `MuJoCo` 6-DOF着地衝撃接触 + A100 3D WCSPH 4,096粒子スロッシング + ジャイロ歳差 | MJCF `.xml` |
| 7 | 電子回路(SPICE)・基板DRC・SI/PI | `ngspice` 過渡回路解析 + PDNインピーダンス/伝送線路SI + `KiCad` 八角形FADEC PCB DRC | SPICE `.cir`, KiCad `.kicad_pcb` |
| 8 | 電磁界(モーター/発電機)・3D FDTD EMI/EMC | 2D極座標静磁界 + 225kRPM逆起電力解析 + A100 3D Yee-FDTD Maxwell方程式 (CISPR-25) | FEMM `.lua` |
| 9 | 飛行制御(GNC)・6自由度非線形SIL | `python-control` + `CasADi` NMPC + CARE MIMO LQR + 6-DOF 突風/スロッシング/巡航遷移SIL | JSBSim `.xml` |
| 10 | 組み込みFW・静的解析・WCET・形式検証 | C11 FADEC FW生成 + `Cppcheck` + `Clang Static Analyzer` + ASan/UBSan WCET + `SPIN` + `Z3` | C11 `.c/.h`, Promela `.pml` |
| 11 | システム設計(MBSE)・FTA・FMEA (RAMS) | `SCRAM` Open-PSA故障木解析(最小カットセット) + 物理連動FMEA + SysML RTM/ICD監査 | Open-PSA `.xml`, SysML RTM `.json` |
| 12 | 製造性(DFM/DFA)・SLM金属3D造形・5軸CNC | 固有ひずみSLM残留歪み/オーバーハング + A100 5軸CNC干渉レイキャスト + 型抜き勾配/DFA | DFM/CAM `.json` |

### ローカルCLI実行

```bash
pip install -r verification/requirements-colab.txt
python3 -m verification.run_all --html index.html --out verification_out
```