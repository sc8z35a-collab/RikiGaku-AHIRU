# RikiGaku-AHIRU（力学アヒル）

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sc8z35a-collab/RikiGaku-AHIRU/blob/main/RikiGaku_AHIRU_Colab_Pro_A100.ipynb)

力学の法則・物理法則に基づいて本物のジェットエンジンで空を飛ぶ、**全長 18 cm × 幅 10 cm × 高さ 20 cm** のアヒル型飛行置物の超高精細 3D CAD 解剖図＆リアルタイム物理稼働シミュレーター＋**全22分野・Google Colab Pro (A100 GPU) 一括物理検証スイート**です。

## 外形寸法・基本諸元

| 項目 | 数値 |
|---|---|
| 外形サイズ | 全長 **180 mm (18 cm)** × 幅 **100 mm (10 cm)** × 高さ **200 mm (20 cm)** |
| 発明エンジン | **AHIRU-μTJ42V**（垂直軸・折り返し環状燃焼室マイクロターボジェット） |
| 乾燥質量 / 離陸質量 | **480 g** / **592 g**（Jet-A1 航空ケロシン燃料 140 mL = 112 g 搭載時） |
| 機体重量 $W = mg$ | **5.81 N** |
| 最大実効推力 $T_{\text{net}}$ | **11.43 N〜15.0 N**（推力重量比 TWR **1.97+**、スロットル約 51% でホバリング） |
| 連続ホバリング時間 | **約 5.2 分** |

## 3D CAD ビューアーの起動方法

[index.html](index.html) をブラウザで開くと、純白背景・UI内文字ゼロのインタラクティブ 3D CAD 解剖ビューアーが起動します。

## Google Colab Pro (A100 GPU) 全22分野・ワンクリック一括検証

上の **Open In Colab** バッジから [RikiGaku_AHIRU_Colab_Pro_A100.ipynb](RikiGaku_AHIRU_Colab_Pro_A100.ipynb) を開き、ランタイムを **A100 GPU** に設定して **「すべてのセルを実行」** を押すと、以下の **主要12分野＋実機物理拡張10分野＝全22分野** を一括検証し、`reports/exports/` に商用・OSS ツール向けデック（STEP/OpenSCAD, SU2/OpenFOAM/Fluent, CalculiX, MuJoCo, ngspice, SCRAM, 5軸CNC G-code）を出力します。

- **D01**: 3D CAD・静的/動的衝突判定 (DMU)・250,000試行 GPU モンテカルロ 6σ 公差累積解析
- **D02**: 数値流体力学 (CFD)・圧縮性反応流 (Cantera + CUDA 圧縮性 Rusanov CFD)・推進サイクル
- **D03**: 共役熱伝達 (CHT)・熱輻射 (Au反射箔＋ZrO2エアロゲル)・熱暴走防止解析
- **D04**: 構造強度・熱応力連成・1.5m落下衝撃・ブレード飛散封じ込め FEA (CalculiX / 固体中心ブリスク 110% 過回転)
- **D05**: 超高速ローターダイナミクス・キャンベル線図 (ROSS / Timoshenko)・音響解析
- **D06**: マルチボディ動力学 (MuJoCo)・32,768粒子 GPU 3D SPH 燃料スロッシング解析
- **D07**: 電子回路 (ngspice / 600kHz同期整流降圧)・PCB DRC / IPC-2221 温度上昇
- **D08**: 電磁界 FEM (12S8P スターター発電機)・3D FDTD マクスウェル EMI/EMC 遮蔽解析
- **D09**: 飛行制御 (GNC)・10,000エピソード GPU 6自由度非線形モンテカルロ SIL 検証
- **D10**: 組込ソフトウェア ([firmware/ahiru_fadec.cpp](firmware/ahiru_fadec.cpp))・Cppcheck 静的解析・WCET・状態遷移形式検証
- **D11**: システム設計 (MBSE)・定量 FTA 故障木・FMEA 信頼性解析
- **D12**: 製造可能性 (DFM)・金属3D造形 (SLM)・20,000姿勢 GPU 5軸CNC工具干渉チェック
- **D13〜D22 (追加10検証)**: 着火/失火限界・ジャイロ歳差トルク＆RCSヨ―・地面効果(IGE)熱排気再吸込み・空力弾性フラッター・Si3N4セラミック軸受EHL油膜・燃料キャビテーション・3S LiHV過渡Sag・10m/s突風＆雨滴FOD・4kHz振動IMUエイリアシング・10,000時間加速寿命＆312秒ミッションデジタルツイン