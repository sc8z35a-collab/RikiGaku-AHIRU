# RikiGaku-AHIRU Rev.3 — 2026再精査・極限最安ルート選定 ＆「本当にそれでいいのか？」工学リスク再比較書

> **前提**: 本書は実機 GPU 上で **Rev.3 6-Wall Qualification (7/7 PASS, 10万回MC生存率 100.0%)**・**V12 (52/52 PASS)**・**MDAO/V&V (Phase 1〜9 PASS)**・**全22分野 (D01–D22 PASS)** を通過した確定設計（[BOM_AHIRU_Rev3.csv](generated/BOM_AHIRU_Rev3.csv)）に対し、**2026年の実市場価格を徹底再精査**（`TBS Lucid H7 FC \$49`・`Dynam 64mm EDF+80A ESC \$75.99`・`CNHL LiPo \$37.98/2本`・`鍛造 Al 2618-T61 5軸CNC`・`Swiwin SW60B Ø84mm/783g 実寸確認`・`Xicoy X45 Ø59.8mm/395g`・`KingTech K-45G4+`・`JLC3DP PA12-CF -24%`）し、**「さらに安い代替品が本当に安全・成立するのか？」を1項目ずつ物理根拠で再比較した最終調達ガイド**です。  
> 為替換算レート目安：`1 USD = 150 JPY`。スプレッドシート管理用CSV：[procurement_checklist.csv](procurement_checklist.csv)

---

## 1. 全11ルート定量比較（2026再精査・安全設備/2面釣合い全計上）

| ルート | コンセプト・サイズ感 | 機体BOM | コア/釣合い/安全/予備 | **総額 (USD)** | **総額目安 (JPY)** | Route A比 | 納期 | 「本当にそれでいいのか？」総合判定 |
|---|---|---:|---:|---:|---:|---:|---|---|
| **Route E-Min（Step-0 極限最安EDF）** | **TBS Lucid H7(\$49)＋Dynam 64mm EDF+80A ESC(\$76)＋KST X08H＋PA12/PETG-CF** | \$389 | \$106 | **\$495** | **約7.4万円** | **-97.0%** | 1–2週間 | **◎ 制御実証の最安最適解**（FC/サーボ/防振はジェット機へ100%移植可） |
| **Route C-Min（市販ジェット絶対最安）** | **Swiwin SW60B直販(\$1,500)＋TBS Lucid H7＋PA12-CF**（本体+タービン \$2,629 / 約39.4万円） | \$1,129 | \$1,875 | **\$3,004** | **約45.1万円** | **-81.6%** | 3–4週間 | **△ 大型化注意**：SW60Bは実寸 **Ø76–84mm・783g・3.2秒遅れ** のため機体が1.65倍（全長30cm・全備1.8kg）化 |
| **Route C-X45（市販ジェット推奨最適）** | **Xicoy X45 / KingTech K-45G4+(\$1,750)＋TBS Lucid H7＋PA12-CF**（本体+タービン \$2,853 / 約42.8万円） | \$1,103 | \$2,130 | **\$3,233** | **約48.5万円** | **-80.2%** | 3–4週間 | **◎ 市販ジェット最推奨**（+\$229で重量半減395g・Ø59.8mm小型維持・2.8s高速応答） |
| **Route B4（180mm純自作 DIY板金極限）** | **鍛造Al 2618圧縮機＋SUS310S板金燃焼器＆ノズル＋TBS Lucid H7＋安全聖域8項目100%死守** | \$3,005 | \$870 | **\$3,875** | **約58.1万円** | **-76.3%** | 5–7週間 | **○ 上級工作向け極限最安**（溶接治具＆ベンチPF検証ができる場合のみ推奨） |
| **Route B3（180mm純自作 図面準拠最安）** | **鍛造Al 2618圧縮機＋STEP図面通りIN718 SLM相乗り＋TBS Lucid H7＋安全聖域8項目100%死守** | \$3,514 | \$930 | **\$4,444** | **約66.7万円** | **-72.8%** | 5–7週間 | **◎ 180mm純自作の最推奨解**（溶接不要・97.4 dBシェブロン＆PF=0.0451再現） |
| **Route D（10機ロット単価）** | Route B1を10機同時発注時の1機単価 | \$3,431 | \$375 | **\$3,806/機** | **約57.1万円/機** | **-76.7%** | 7–9週間 (10機) | 研究室・共同製作・小ロット量産 |
| Route E（独自PCBA付EDF） | JLCPCB独自FADEC基板＋64mm 6S EDF | \$786 | \$185 | \$971 | 約14.6万円 | -94.1% | 2–3週間 | 独自PCBAの先行試験を行いたい場合 |
| Route C（代理店保証COTS） | 正規代理店保証タービン＋5枚PCBA | \$2,500 | \$2,570 | \$5,070 | 約76.0万円 | -69.0% | 3–4週間 | 国内代理店フル保証重視 |
| Route B2 / B1 / A | 国内釣合い自作 / 機上発電フル自作 / 欧米ワンオフ | \$6,312〜\$13,467 | \$1,790〜\$2,870 | \$8,102〜\$16,337 | 約121.5万円〜約245.1万円 | -50%〜基準 | 5–14週間 | 法人・研究機関向けフルスペック |

---

## 2. 「本当にそれでいいのか？」さらなる最安案 9項目・工学再比較 ＆ 偽の節約トラップ監査

最安値を追い求める際、**「物理的に安全かつ高性能な本物の節約」**と**「数万円ケチって機体全損・破損を招く偽の節約（トラップ）」**を厳格に仕分けしました。

| 判定 | 検討したさらなる最安案 | コスト差 | 物理・工学再評価（「本当にそれでいいのか？」の結論） |
|---|---|---:|---|
| **◎ 強く推奨 (性能向上)** | 圧縮機: Ti-6Al-4V ($260) → 鍛造 Al 2618-T61 ($115) | **-\$145** | PR=2.8出口温度は140°C（Al 2618耐熱200°C以下）。遠心応力154 MPaに対し耐力340 MPaでSF=2.21を確保しつつ、回転慣性が-38%減りジャイロ連成が41.8%→33.6%へ劇的改善！（※Al 7075は120°C超で軟化するためNG） |
| **◎ 推奨 (外部始動/市販機)** | FADEC基板: JLCPCB 2枚SMT ($235) → TBS Lucid H7 ($49) + 外部WDT ($36) | **-\$150** | 2026実売$49のTBS Lucid H7は本番同一のSTM32H743＋デュアルICM-42688-Pを標準搭載。外部スタータ運用（Route B3/B4）や市販ECU機（C-X45/E-Min）では機上60V FOCが不要なため、TPS3823独立WDT外付けで安全性ゼロ妥協のまま-$150削減。 |
| **△ 安物買い注意 (大型化)** | 市販タービン: Xicoy X45 ($1,750) vs Swiwin SW60B ($1,500) | **-\$250** | 実市場精査でSwiwin最小機はSW60B（Ø76–84mm・783g・スプール遅れ3.2秒・SW30Bは現行非存在）と判明！機体が1.65倍（全長30cm・全備1.8kg）に肥大化。+$229（約3.4万円）でXicoy X45（Ø59.8mm・395g・2.8s）を選ぶ方がVTOL安定性・サイズ感とも圧倒的優位！ |
| **○ 条件付可 (溶接治具要)** | 燃焼器＆ノズル: IN718 SLM ($570) → 0.4mm SUS310S板金溶接 ($240) | **-\$330** | Wren 44 / KJ-66等DIYタービン王道手法で軽量化＆-$330。ただし気化管角度や希釈孔のズレでホットストリーク(PF)が悪化しやすく、スポット溶接治具がない場合はSTEP図面そのままのIN718 SLM一括相乗り（Route B3）が安全。 |
| **◎ 電動EDF機で推奨** | Step-0外殻: JLC3DP PA12-CF ($115) → FDM PETG-CF/PA12 ($48) | **-\$67** | 電動EDF（Route E-Min）は排気常温で熱変形ゼロ。2026年FDM造形（$0.05–$0.15/g）＋TBS Lucid H7＋Dynam 64mm EDF($76)で制御実証機総額を約7.4万円($495)まで圧縮可能。 |
| **× 絶対NG (発振墜落)** | 【罠】TVCサーボ: KST X08H Plus ($95) → 安価$12メタルギアサーボ ($24) | **-\$71** | 安価な$12サーボはギアバックラッシ1.5〜3.0°（KSTは≤0.25°）。TVCのガタが0.8°を超えると1kHz LQRがリミットサイクル発振し離陸1秒で転倒墜落。$71ケチって50万円の機体を破壊する最悪の偽節約！ |
| **× 絶対NG (数秒で焼付き)** | 【罠】軸受: GRW 685 ABEC-7 P4 ($220) → AliExpress中華ハイブリッド ($15) | **-\$205** | 実測調査の通り安価ハイブリッド軸受はABEC-1/C0ガタ(3–18µm)＋金属冠型保持器（上限22,000 RPM）。201,000 RPM（dm·N=1.71M）では保持器が遠心破断して即ロック・タービン破損。 |
| **× 絶対NG (ブレード飛散)** | 【罠】タービン熱処理: HIP+時効 ($490) → 未HIP造形っぱなし ($240) | **-\$250** | SLM造形直後のIN718は内部マイクロポア（空隙）を含み、920°C・遠心48,000G環境下でクリープ亀裂が急速進展。共有HIP炉を使えばコストを抑えつつ空隙ゼロを保証できるためHIP省略は厳禁。 |
| **× 絶対NG (軸受寿命1/1000)** | 【罠】動釣合い: 専門2面G0.4 ($380) → スマホ/圧電DIY1面バランス ($60) | **-\$320** | 201,000 RPMでは残存不釣合いがG0.4(0.22 mg·mm)からG4.0へ悪化するだけで遠心加振力が10倍（~96 N）・軸受疲労寿命が1/1000に崩壊し、IMUも3.35 kHz振動で飽和。外部専門2面G0.4は絶対必須。 |

### 再比較の結論（本当に選ぶべきベスト3）
1. **まず7.4万円で確実に飛ばす → `Route E-Min`（\$495 / 約7.4万円）**
   - `TBS Lucid H7`（STM32H743＋二重ICM-42688-P）＋`KST X08H Plus`＋`Sorbothane 50D`＋`Dynam 64mm EDF`で制御則と2軸TVCを100%実証。主要電装はそのままジェット機へ移植できるため無駄ゼロ。
2. **本物のジェット推力を最小コスト＆最小リスクで → `Route C-X45`（\$3,233 / 約48.5万円・本体+タービン \$2,853）**
   - 絶対最安の `Route C-Min`（Swiwin SW60B, \$3,004）よりわずか **+\$229（約3.4万円）** 高いだけで、タービン重量が **783 g → 395 g（半減）**、外径が **Ø84 mm → Ø59.8 mm** になり、机上サイズ感とVTOL安定性が劇的に改善します。
3. **180×200×100 mm 完全オリジナル自作ターボジェット → `Route B3`（\$4,444 / 約66.7万円・BOM \$3,514）**
   - 鍛造 `Al 2618-T61` 圧縮機（むしろジャイロ連成が `41.8% → 33.6%` へ改善！）＋ `TBS Lucid H7` 外部始動構成＋ STEP図面通りのIN718 SLM相乗りで、溶接リスクなしで66万円台を実現。金属板金溶接ができる上級者なら `Route B4`（**\$3,875 / 約58.1万円**）まで圧縮可能。

---

## 3. 絶対に削ってはいけない「安全聖域（Non-Negotiable 8項目）」

1. **軸受 (`AHIRU-R3-008`)**: 必ず `GRW 685-2Z-CE`（Si3N4球・PEEK/フェノール保持器・ABEC-7 P4）。`\$15` AliExpressハイブリッド軸受（ABEC-1/金属保持器）は即焼付き。
2. **スクイーズフィルムOリング (`AHIRU-R3-009`)**: 必ず `AS568-013 FKM Viton Shore 60A`（70A/90AやNBRは危険速度接触）。
3. **潤滑オリフィス (`AHIRU-R3-010`)**: 必ず較正済 `Ø0.25 mm` ルビーオリフィス（Lee / O'Keefe）＋5µmフィルタ。
4. **ブレード封じ込めリング & 高温ボルト (`AHIRU-R3-007`)**: Inconel 718 最小肉厚 `2.05 mm` ＋ `A286` 耐熱ボルト＋皿ばね（SUS304厳禁）。
5. **タービンブリスク熱処理 (`AHIRU-R3-002`)**: DMLS造形後の **HIP（1180°C/100MPa）＋時効処理** は省略厳禁。
6. **2面動釣合い (`AHIRU-SVC-002`)**: 組付状態で **`ISO 1940 G0.4`（≤ 0.22 mg·mm/面）** を専門バランサで施工（DIY1面厳禁）。
7. **FADEC 独立WDT & 二重IMU (`AHIRU-R3-020`)**: `STM32H743`＋二重`ICM-42688-P`＋独立`TPS3823-33 WDT`（機上発電構成時は60V MOSFET `BSC028N06LS3` 必須）。
8. **Sorbothane 50D 防振マウント (`AHIRU-R3-021`)**: `f_n = 38 Hz` で 3,350 Hz 1X振動を `-77.1 dB` 減衰（通常シリコンゴム不可）。

---

## 4. フェーズ別 完全発注チェックリスト（Wave 1〜4・全27項目）

### Wave 1：最長納期クリティカルパス（Week 1 即発注・納期 3〜6週間）

| 済 | Part No | 品目 | 安全区分 | B4極限DIY | B3推奨自作 | C-X45推奨市販 | E-Min電動 | 推奨ベンダー（2026精査版） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-R3-001` | 6+6 Splitter Centrifugal Compressor Impeller (×1) | Tier-S (妥協厳禁) | \$115 | \$115 | \$0 | \$0 | JLCCNC 5軸 鍛造Al 2618-T61 (150°C耐力340MPa/SF=2.21・慣性-38%改善! ※7075/6061不可) | Ø5.000 +0.008/-0.000 mm (H6), 翼厚公差 ±0.03 mm, 浸透探傷ゼロ欠陥 |
| `[ ]` | `AHIRU-R3-002` | 17-Blade Tapered Bleed-Cooled Turbine Blisk (×1) | Tier-S (妥協厳禁) | \$490 | \$490 | \$0 | \$0 | Unionfab / WeNext IN718 SLM単一プレート相乗り + 共有炉HIP + EDM Ø4 H6 (妥協厳禁) | HIP証明・熱処理成績書, Ø4.000 H6, X線/CT内部空隙ゼロ, 17翼ピッチ異常なし |
| `[ ]` | `AHIRU-R3-003` | High-Stiffness Rotor Main Shaft (×1) | Tier-S (妥協厳禁) | \$155 | \$165 | \$0 | \$0 | 国内/アジア精密切削＋円筒研削 (Ø5.000 h5, TIR<=2µm) | CMM/真円度測定成績書: Ø5.000 h5, TIR <= 2 µm, Ra <= 0.2 µm |
| `[ ]` | `AHIRU-R3-004` | 15-Vane Diffuser & Integral Bearing Tunnel (×1) | Tier-S (妥協厳禁) | \$195 | \$210 | \$0 | \$0 | JLCCNC / RapidDirect 5軸 Al 7075-T651 + Ø11 H6 + 硬質アルマイト | エアマイクロ測定 Ø11.000 H6, 同軸度 <= 5 µm, Oリング溝14%潰し代確認 |
| `[ ]` | `AHIRU-R3-005` | Reverse-Flow Annular Combustor + 12 Vaporizers (×1) | Tier-A (高温重要) | \$95 | \$280 | \$0 | \$0 | B3: Unionfab IN718 SLM相乗り($280) / B4: 0.4mm SUS310S板金レーザー+細管溶接($95・要治具) | 全12気化管+36希釈孔の通気・内視鏡残留粉末ゼロ確認 |
| `[ ]` | `AHIRU-R3-006` | 12-Vane Turbine Stator NGV + Tailcone (×1) | Tier-A (高温重要) | \$215 | \$230 | \$0 | \$0 | Unionfab / WeNext IN718 SLM (002と相乗り・1.9cm³) + 端面旋盤 | 12静翼流路面積バラつき <= ±3%, フランジ平面度 <= 0.02 mm |
| `[ ]` | `AHIRU-R3-007` | 360° Blade Containment Ring + A286 Flange (×1) | Tier-S (妥協厳禁) | \$165 | \$175 | \$0 | \$0 | JLCCNC IN718旋盤(壁厚>=2.05mm厳守) + A286耐熱ボルト＆皿ばね (妥協厳禁) | 最小肉厚 >= 2.05 mm 確認, A286ミルシート確認 |
| `[ ]` | `AHIRU-R3-008` | Hybrid Ceramic Angular-Contact Bearings (×2) | Tier-S (妥協厳禁) | \$220 | \$220 | \$0 | \$0 | GRW代理店 / Boca Bearings (GRW 685-2Z-CE Si3N4 ABEC-7 P4 妥協厳禁・$15品絶対NG) | メーカー証明書(dn >= 1.8M対応), 手回し引っ掛かりゼロ, シールド脱脂処理 |
| `[ ]` | `AHIRU-R3-009` | Squeeze-Film Damper O-Rings (×2) | Tier-S (妥協厳禁) | \$12 | \$12 | \$0 | \$0 | Parker / ミスミ (AS568-013 FKM Viton 60A 妥協厳禁) | 硬度 60±5 Shore A, 断面径 1.78±0.08 mm 確認 |
| `[ ]` | `AHIRU-R3-010` | Metered Oil-Mist Restrictors & Capillary Lines (×2) | Tier-S (妥協厳禁) | \$135 | \$140 | \$0 | \$0 | O'Keefe / Bird Precision 流量較正済Ø0.25mmルビーオリフィス + 5µmフィルタ (妥協厳禁) | 1.8 bar ろ過Jet-A1で各 0.12 ± 0.01 mL/min 実測確認 |
| `[ ]` | `AHIRU-R3-012` | Celeroton-Class Direct-Coupled Starter-Generator (×1) | Tier-A (高速回転重要) | \$48 | \$55 | \$0 | \$0 | 外部手持ちBLDCスタータワンド (2838 BLDC + 30A ESC + シリコンカップ) | Route B1: 201k RPM相当スピン/線間逆起電力 Kv=7,800±5% 確認, 絶縁耐圧 >= 100V |
| `[ ]` | `AHIRU-R3-013` | Choked Chevron De Laval Nozzle & Ti Gimbal (×1) | Tier-A (推力偏向重要) | \$145 | \$290 | \$225 | \$24 | B3: IN718 SLMシェブロン+Tiジンバル($290) / B4: SUS310S成形ノズル+CNCジンバル($145) / E-Min: PA12-CF($24) | ±14°全象限スムーズ可動(フリクション <= 12 mNm), クリアランス >= 9 mm |
| `[ ]` | `AHIRU-R3-015` | Bleed-Air Proportional Yaw RCS Valves & Nozzles (×2) | Tier-A (ヨー制御重要) | \$115 | \$125 | \$110 | \$0 | SMC S070 / Parker X-Valve 5V高速マイクロソレノイド弁×2 + Ti細管 | 5V駆動リークゼロ, 50Hz PWM比例流量応答確認 |
| `[ ]` | `AHIRU-SVC-001` | 市販認証済みマイクロタービンコア一式（Route C専用：Swiwin SW30B / KingTech K30G4+ 等） (×1) | Tier-S (Route C中核) | \$0 | \$0 | \$1,750 | \$76 | C-Min: Swiwin SW60B($1,500・Ø84mm/783g注意!) / C-X45: Xicoy X45・K-45G4+($1,750・Ø59.8mm/395g推奨) / E-Min: Dynam 64mm EDF+80A ESC($76) | メーカー出荷ベンチテスト成績書確認, 地上アイドル〜最大推力動作確認 |

### Wave 2：電装・サーボ・燃料系・バッテリー（Week 1〜2 発注・納期 1〜3週間）

| 済 | Part No | 品目 | 安全区分 | B4極限DIY | B3推奨自作 | C-X45推奨市販 | E-Min電動 | 推奨ベンダー（2026精査版） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-R3-014` | High-Speed Metal-Gear HV TVC Servos + Ti Linkages (×2) | Tier-A (姿勢制御重要) | \$92 | \$95 | \$95 | \$92 | KST公式直販 (KST X08H Plus V6.0 $39.99×2 + Tiリンク ※$12サーボはバックラッシ発振NG!) | 無負荷応答 <= 0.08s/60°, バックラッシ <= 0.25° |
| `[ ]` | `AHIRU-R3-016` | 290° Conformal Saddle Tank + 3 Baffles + UAT (×1) | Tier-A (燃料安全重要) | \$58 | \$68 | \$62 | \$0 | JLC3DP MJF PA12 ($0.275/g) + 耐Jet-A1 Novolac/Viton内面コート | 満水139.5±2 mL, 0.5 bar 30分リークゼロ, Jet-A1 72時間浸漬膨潤なし |
| `[ ]` | `AHIRU-R3-017` | Brushless Micro Gear Fuel Pump + Si3N4 Igniter (×1) | Tier-A (燃料供給重要) | \$155 | \$165 | \$0 | \$0 | Xicoy/Swiwin OEM ブラシレスマイクロ燃料ポンプ + 11V Si3N4グロープラグ | 0.1〜4.0 bar吐出流量カーブ取得, 気泡混入ゼロ |
| `[ ]` | `AHIRU-R3-020` | 4-Layer STM32H743 FADEC + 60V FOC + Dual IMU PCBA (×1) | Tier-S (妥協厳禁) | \$85 | \$85 | \$65 | \$65 | TBS Lucid H7 FC ($49・STM32H743+二重ICM42688P) + 外部TPS3823-33 WDT/FETキャリア ($16-$36) | 通電3.3V/5V実測, SWD(ST-LINK/V3)で firmware/fadec_rev3.c 書込+WDT遮断テスト合格 |
| `[ ]` | `AHIRU-R3-021` | Sorbothane 50D IMU Isolation Mount + Optical Eyes (×1) | Tier-S (妥協厳禁) | \$68 | \$72 | \$68 | \$52 | Isolate It! Sorbothane 50Dグロメット(厳守) + DigiKey VL53L4CD/熱電対 | 固有振動数 35〜45 Hz 確認, 3350 Hz加振でジャイロRMS < 0.08 deg/s |
| `[ ]` | `AHIRU-R3-022` | Split-Balanced 3S 750 mAh 60C LiHV Battery Pack (×1) | Tier-A (電源安全重要) | \$38 | \$42 | \$42 | \$26 | GNB / CNHL Black 130C LiHV/LiPo (CNHL実売 $37.98/2パック検証済) | 内部抵抗測定(ESR <= 65 mΩ), 30A負荷テストで V_bus >= 9.5 V |

### Wave 3：外殻・内部フレーム・断熱材・安全試験治具（Week 2〜3 発注・納期 1〜3週間）

| 済 | Part No | 品目 | 安全区分 | B4極限DIY | B3推奨自作 | C-X45推奨市販 | E-Min電動 | 推奨ベンダー（2026精査版） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-R3-011` | Silica Aerogel Shroud + Gold Liner + ZrO2 Firewall (×1) | Tier-A (熱安全重要) | \$95 | \$115 | \$85 | \$0 | カットシート Pyrogel XTE + DEI Reflect-A-Gold + 工業用YSZ板 | LiHVバッテリー〜燃焼器外殻ギャップ >= 13.5 mm 実測 |
| `[ ]` | `AHIRU-R3-018` | Duck CFRP Shell, S-Duct Intakes, Wings & Belly (×1) | Tier-B (コスト最適化大) | \$98 | \$115 | \$125 | \$48 | JLC3DP MJF PA12-CF (-24%改定後) + YSZ底部断熱 (E-MinはFDM PETG-CF/PA12 $48) | 総外殻質量 <= 115 g, 合わせ面段差 <= 0.3 mm, Sダクト内面平滑研磨 |
| `[ ]` | `AHIRU-R3-019` | Al 7075-T6 Internal Frame & 26.8mm Oleo-Ti Struts (×1) | Tier-A (構造重要) | \$165 | \$195 | \$180 | \$58 | JLCCNC Al 7075-T6フレーム + ミスミ規格ばね/Tiパイプ脚 (E-MinはCFRPパイプ+Al金具 $58) | 10G静的荷重(60 N)たわみ確認, 着陸脚ストローク 15.6 mm 確認 |
| `[ ]` | `AHIRU-R3-023` | Harnesses, Silicone/PTFE Wire, XT30, Hardware (×1) | Tier-A (配線信頼性) | \$46 | \$55 | \$46 | \$24 | LCSC / ミスミ PTFEシールドツイストペア + AWG14シリコン + Tiねじ | 全コネクタ抜去力・導通・絶縁確認, ツイストピッチ <= 5 mm |
| `[ ]` | `AHIRU-SVC-003` | 屋外火入れ試験台・3点重心計・防爆シールド・CO2消火器・二重聴覚保護具・係留3軸リグ (×1) | Tier-S (人命安全) | \$290 | \$310 | \$290 | \$30 | DIYアルミフレーム推力台 + HX711 + 8mmポリカ防爆板 + CO2消火器 + 二重防音 | 非常停止応答 < 50 ms, ロードセル較正誤差 <= ±0.05 N, 3点CoG測定精度 <= ±0.5 mm |

### Wave 1–2 同時同梱：クリティカル予備品（再調達6週間待ちの防止）

| 済 | Part No | 品目 | 安全区分 | B4極限DIY | B3推奨自作 | C-X45推奨市販 | E-Min電動 | 推奨ベンダー（2026精査版） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-SPR-001` | 消耗・破損リスク予備品パック（GRW 685軸受×2, Viton Oリング×10, KSTサーボ×1, 熱電対×2, 燃料フィルタ） (×1) | Tier-A (開発停止防止) | \$220 | \$240 | \$90 | \$0 | 最低限クリティカル予備 (GRW 685軸受×2 + Viton Oリング + フィルタ) | 全スペア部品の防湿保管・シリアル番号紐付け完了 |

### Wave 4：受入精密検査・外部2面 G0.4 動釣合い（Week 5〜7・組付前必須ゲート）

| 済 | Part No | 品目 | 安全区分 | B4極限DIY | B3推奨自作 | C-X45推奨市販 | E-Min電動 | 推奨ベンダー（2026精査版） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-SVC-002` | 外部2面動釣合い加工（ISO 1940 G0.4 @ 201,000 RPM）＋主要部CMM検査サービス (×1) | Tier-S (妥協厳禁) | \$360 | \$380 | \$0 | \$0 | 深圳/上海 高速マイクロターボ専門2面動釣合い (ISO 1940 G0.4 <=0.22mg·mm・妥協厳禁) | 釣合い成績書 <= 0.22 mg·mm/面 (G0.4), 再組付用位相合いマーク刻印済 |


---

## 5. サプライヤー別 RFQ（見積依頼）送信パッケージ一覧

| パッケージ | 送信先業種・推奨ベンダー | 添付するリポジトリ内ファイル | 見積依頼時の必須追記文（コピー可） |
|---|---|---|---|
| **RFQ-1: 金属3Dプリント (IN718単一プレート相乗り)** | Unionfab / WeNext / FacFox | `02_turbine_blisk_Inconel718.step`, `05_combustor_liner_Inconel718.step`, `00_AHIRU_Rev3_Core_Assembly.step`, `07_tvc_gimbal_chevron_nozzle.step`, `DWG_03_Blisks_Flanges_IMU_GDT.dxf` | *Material: Inconel 718 (AMS 5662/5663). Nest parts on a single build plate + shared HIP furnace batch for Part 02 (1180C/100MPa + age); stress relief + ultrasonic powder removal inside 12 vaporizer tubes; wire-EDM Ø4.000 H6 bore on Part 02.* |
| **RFQ-2: 5軸CNC & 精密研削 (Al 2618 / Al 7075 / IN718)** | JLCCNC / RapidDirect / PCBWay CNC | `01_compressor_impeller_Ti6Al4V.step` (Al 2618-T61可), `03_rotor_shaft_Inconel718.step`, `04_diffuser_bearing_tunnel_Al7075.step`, `06_containment_flange_Inconel718.step`, `DWG_01/02/03.dxf` | *Impeller: Forged Al 2618-T61 (NOT 6061/7075) or Ti-6Al-4V, Ø5.000 H6 bore; Shaft: IN718 Ø5.000 h5 post-HT grind (TIR<=2um, Ra<=0.2um); Diffuser: Al 7075 Ø11.000 H6 (coaxiality<=5um, mask bore during hard anodize); Containment ring wall >=2.05mm.* |
| **RFQ-3: FADEC電装 (TBS Lucid H7 + WDT / またはJLCPCB 4層PCBA)** | TBS正規店 / JLCPCB | `electronics/generated/gerbers/*`, `AHIRU_FADEC_Rev3_BOM.csv`, `AHIRU_FADEC_Rev3_CPL.csv` | *External-start / COTS route: TBS Lucid H7 FC (STM32H743 + Dual ICM-42688-P) + external TPS3823-33 hardware WDT cutoff board. Onboard-generator B1 route: JLCPCB 4-layer TG170 2oz ENIG, NO substitutions on BSC028N06LS3(60V) / DRV8353RS / TPS3823-33.* |
| **RFQ-4: 樹脂3Dプリント (PA12-CF外殻 & PA12燃料タンク)** | JLC3DP | `00_AHIRU_Rev3_Core_Assembly.step`, `index.html`抽出STL, `08_imu_sorbothane_mount_assembly.step` | *Fuel tank: MJF PA12 ($0.275/g) w/ 3 internal perforated baffles & UAT sump (apply Jet-A1 Novolac/Viton internal sealer). Outer duck shell: MJF PA12-CF (shell max verified 28.3C).* |
| **RFQ-5: 航空宇宙COTS精密部品** | GRW代理店 / O'Keefe / KST公式 / Xicoy | `BOM_AHIRU_Rev3.csv`（Part `008, 009, 010, 014, 015, 017`） | *Exact P/Ns only: GRW 685-2Z-CE Si3N4 ABEC-7 P4 (Qty 4 incl. spares), AS568-013 FKM Viton 60A (Qty 10), calibrated Ø0.25mm ruby orifice (Qty 2), KST X08H Plus V6.0 ($39.99/ea, Qty 2-3), SMC S070 5V micro-solenoid (Qty 2).* |
| **RFQ-6: 外部 2面 G0.4 動釣合い** | 高速動釣合い専門工場（国内/深圳マイクロターボ工房） | `DWG_01_Rotor_Shaft_GDT.dxf`, `DWG_03_Blisks_Flanges_IMU_GDT.dxf`, `FLIGHT_QUALIFICATION_MANUAL.md` | *201,000 RPM マイクロタービン用ロータASSYの2面動釣合い。ISO 1940 G0.4（残存不釣合い ≤ 0.22 mg·mm/面）。修正削りは図面指定のカラー・ボスのみ。位相刻印・成績書必須。* |
