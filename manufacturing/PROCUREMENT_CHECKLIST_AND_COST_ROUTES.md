# RikiGaku-AHIRU Rev.3 — 実機製作 発注チェックリスト & 2026極限最安コスト最適化ルート選定書

> **前提**: 本書は実機 Colab GPU 上で **Rev.3 6-Wall Qualification (7/7 PASS, 10万回MC生存率 100.0%)**・**V12 (52/52 PASS)**・**MDAO/V&V (Phase 1〜9 PASS)**・**全22分野 (D01–D22 PASS)** を通過した確定設計（[BOM_AHIRU_Rev3.csv](generated/BOM_AHIRU_Rev3.csv)）と、2025–2026年の実市場価格調査（JLC3DP PA12-CF -24%値下げ・MJF PA12 \$0.275/g・KST公式 \$39.99・JLCPCB 2枚SMT実装・Swiwin SW60B/SW30B直販・中国単一プレートSLM+共有HIP炉）に基づく実務発注仕様書です。  
> 為替換算レート目安：`1 USD = 150 JPY`。Excel/Google スプレッドシート管理用CSV：[procurement_checklist.csv](procurement_checklist.csv)

---

## 1. コスト最小化 全8ルート定量比較（2026極限最安＋安全設備・2面釣合い全計上）

「機体部品だけ安く見えて、後から動釣合い・防爆治具・予備品で予算超過する」ことを防ぐため、**全ルートに外部検査/釣合い・安全試験設備・予備品まで全額含めた総実費**と**純粋な機体部品代のみ**を両方明記しています。

| ルート | コンセプト | 機体BOM (23品目) | コア/釣合い/安全/予備 | **総額 (USD)** | **総額目安 (JPY)** | Route A比 | 最短納期 | 推奨用途 |
|---|---|---:|---:|---:|---:|---:|---|---|
| **Route E（Step-0 EDF訓練機）** | **64mm 6S電動EDF (`20 N`級)＋本番FADEC/TVC**（火気ゼロの制御先行実証機） | \$786 | \$185 | **\$971** | **約14.6万円** | **-94.1%** | 2–3週間 | **墜落リスク最小の制御/TVC先行検証（基板/サーボは本番流用）** |
| **Route C-Min（市販ジェット極限最安）** | **Swiwin SW60B/SW30B直販(\$1,550)＋JLC3DP＋JLCPCB 2枚SMT**（本体のみ \$2,939 / 約44.1万円） | \$1,389 | \$1,955 | **\$3,344** | **約50.2万円** | **-79.5%** | 3–4週間 | **本物のジェット推力で最安・最短3〜4週間の初飛行** |
| **Route B3（純自作180mm極限最安）** | **2026実市場最安・完全オリジナル180mm自作ジェット**（安全聖域8項目100%維持・外部スタータ） | \$3,809 | \$930 | **\$4,739** | **約71.1万円** | **-71.0%** | 5–7週間 | **180×200×100mm 純粋自作ターボジェットの現実的最安解** |
| **Route D（10機ロット単価）** | Route B1最適化を10機バッチ発注（1機あたり単価） | \$3,431 | \$375 | **\$3,806/機** | **約57.1万円/機** | **-76.7%** | 7–9週間 (10機) | 研究室・共同製作・小ロット量産 |
| **Route C（市販タービン標準）** | 市販認証済みマイクロタービン（代理店保証品）換装 1.25× 機体 | \$2,500 | \$2,570 | **\$5,070** | **約76.0万円** | **-69.0%** | 3–4週間 | 国内/正規代理店サポート重視の市販タービン機 |
| **Route B2（自作・国内釣合い）** | Route B1＋外部電動スタータ始動（国内2面G0.4釣合い・JLCPCB 5枚SMT） | \$6,312 | \$1,790 | **\$8,102** | **約121.5万円** | **-50.4%** | 5–7週間 | 国内動釣合い＋予備基板4枚の安心自作構成 |
| **Route B1（自作・機上発電付）** | 戦略的アジア高精度CNC＋DMLS一括ネスト＋SmCo28機上スタータ発電機付 | \$6,772 | \$1,790 | **\$8,562** | **約128.4万円** | **-47.6%** | 6–8週間 | 機上自立始動＆発電まで完全再現する自作フル構成 |
| **Route A（欧米/国内ワンオフ）** | フルカスタム航空宇宙仕様（PEEK-CF30・欧米ワンオフCNC/DMLS） | \$13,467 | \$2,870 | **\$16,337** | **約245.1万円** | 基準 | 10–14週間 | 機関・法人向けフルスペック実証 |

### 結論：2026年時点で現実的に到達できる「絶対最安」ライン

1. **本物のジェット推進で絶対最安 → `Route C-Min`（総額 \$3,344 / 約50.2万円・機体+タービン本体のみ \$2,939 / 約44.1万円）**
   - 2026年市場で最安クラスの市販ブラシレスマイクロタービン（Swiwin SW60B/SW30B直販 `\$1,450–\$1,650`）＋ JLC3DP（2026年7月 `-24%` 値下げ後 PA12-CF）＋ JLCPCB 2枚SMT実装 ＋ KST公式直販（`\$39.99/個`）を組み合わせ、安全装備一式を含めて **約50.2万円** で本物のジェットアヒルが飛びます。
2. **180×200×100 mm の純粋自作ターボジェットで絶対最安 → `Route B3`（総額 \$4,739 / 約71.1万円・機体部品BOMのみ \$3,809 / 約57.1万円）**
   - **安全聖域8項目（GRW 685 Si3N4 ABEC-7軸受・Viton 60A Oリング・較正済ルビーオリフィス・2.05mm IN718封じ込め＆A286ボルト・タービンHIP処理・2面ISO 1940 G0.4釣合い・60V FOC＋独立WDT＋二重IMU・Sorbothane 50D）は1ミリも妥協せず**、全4点の微小IN718 SLM部品（合計わずか `9.5 cm³`）の単一プレート相乗り＋共有HIP炉＋JLC3DP/JLCCNC直接手配で、従来の Route B2（`\$8,102`）からさらに **`-\$3,363`（約50.4万円）** 圧縮しました。
3. **さらに賢い「失敗ゼロ・ステップアップ戦略」**
   - **Step 0**: まず `Route E`（電動64mm EDF訓練機・**\$971 / 約14.6万円**）で本番と同一の `STM32H743` FADEC基板・`KST X08H Plus` サーボ・`Sorbothane 50D`・2軸TVC制御を火気ゼロで完全デバッグ。
   - **Step 1**: FADEC・サーボ・安全治具をそのまま流用し、`Route C-Min` または `Route B3` へ換装（重複購入ゼロで初飛行成功率を最大化！）。

---

## 2. Route A → Route B3（2026極限最安）コスト削減ドライバー TOP 10

| 順位 | Part No | 品目 | Route A (ワンオフ) | Route B3 (2026極限最安) | 削減額 | 2026最安調達ソース・安全担保根拠 |
|---:|---|---|---:|---:|---:|---|
| 1 | `AHIRU-R3-012` | Celeroton-Class Direct-Coupled Starter-Generator | \$1,450 | \$55 | **-\$1,395** | 外部手持ちBLDCスタータワンド (2838 BLDC + 30A ESC + シリコンカップ) |
| 2 | `AHIRU-R3-018` | Duck CFRP Shell, S-Duct Intakes, Wings & Belly | \$1,350 | \$115 | **-\$1,235** | JLC3DP MJF PA12-CF (2026年7月 -24%値下げ後単価, 108.5g) + YSZ底部断熱 |
| 3 | `AHIRU-R3-002` | 17-Blade Tapered Bleed-Cooled Turbine Blisk | \$1,650 | \$490 | **-\$1,160** | Unionfab / WeNext IN718 SLM単一プレート相乗り + 共有炉HIP + EDM Ø4 H6 |
| 4 | `AHIRU-R3-005` | Reverse-Flow Annular Combustor + 12 Vaporizers | \$1,100 | \$280 | **-\$820** | Unionfab / WeNext IN718 SLM (002と単一プレート相乗り・4.4cm³) |
| 5 | `AHIRU-R3-001` | 6+6 Splitter Centrifugal Compressor Impeller | \$950 | \$260 | **-\$690** | JLCCNC / Shenzhen 5-Axis Ti-6Al-4V + CMM + Ø5 H6 |
| 6 | `AHIRU-R3-013` | Choked Chevron De Laval Nozzle & Ti Gimbal | \$920 | \$290 | **-\$630** | Unionfab IN718 SLM相乗りノズル + 4軸CNC Tiジンバル (EDF機はPA12-CF造形) |
| 7 | `AHIRU-R3-006` | 12-Vane Turbine Stator NGV + Tailcone | \$850 | \$230 | **-\$620** | Unionfab / WeNext IN718 SLM (002と相乗り・1.9cm³) + 端面旋盤 |
| 8 | `AHIRU-R3-004` | 15-Vane Diffuser & Integral Bearing Tunnel | \$820 | \$210 | **-\$610** | JLCCNC / RapidDirect 5-Axis Al 7075-T651 + Ø11 H6 + 硬質アルマイト |
| 9 | `AHIRU-R3-019` | Al 7075-T6 Internal Frame & 26.8mm Oleo-Ti Struts | \$760 | \$195 | **-\$565** | JLCCNC Al 7075-T6フレーム + ミスミ規格ばね/Tiパイプ脚 |
| 10 | `AHIRU-R3-007` | 360° Blade Containment Ring + A286 Flange | \$540 | \$175 | **-\$365** | JLCCNC IN718旋盤(壁厚>=2.05mm厳守) + A286耐熱ボルト＆皿ばね |

> **なぜここまで下がるのか（2026実市場ファクト）**：
> - **JLC3DP 2025年末〜2026年7月大幅値下げ**：`MJF PA12` が `\$0.275/g`、`PA12-CF` がさらに `-24%` 改定。実ソルバー連成熱解析で外殻最高温度 `28.3 °C` と実証済みのため、PEEK-CF30（`\$1,350`）→ JLC3DP PA12-CF（`\$115`）で **`-\$1,235`（-91.5%）** 削減。
> - **微小IN718 SLM 4部品（合計体積わずか `9.5 cm³`）の単一プレート相乗り＋共有HIP炉**：002タービン(`0.74 cm³`)・005燃焼器(`4.43 cm³`)・006 NGV(`1.86 cm³`)・013ノズル(`2.4 cm³`)を1枚に相乗り造形＋共有HIP炉チャージで **`\$4,520` → `\$1,290`（-\$3,230）**。
> - **JLCPCB 5枚基板＋2枚のみSMT実装**：5枚全実装（`\$425`）から「5枚基板製造＋2枚のみSMT実装（メイン1＋予備1）」にするだけで、Tier-S部品を1点も削らず **`\$235`（-\$190）**。
> - **KST公式直販**：`KST X08H Plus V6.0` は公式定価 **`\$39.99/個`**（2個＋Tiリンクで `\$95`）。

---

## 3. 絶対に削ってはいけない「安全聖域（Non-Negotiable 8項目）」

以下の 8 項目はどれほど最安化しても変更厳禁です（安価な代替品は **201,000 RPM 破損・焼付き・墜落・火災** に直結）：

1. **軸受 (`AHIRU-R3-008`)**: 必ず `GRW 685-2Z-CE`（Si3N4セラミック球・PEEK/フェノール保持器・ABEC-7 P4以上）。釣りリール用\$5軸受は `dm·N = 1.71M` で即破損。
2. **スクイーズフィルムOリング (`AHIRU-R3-009`)**: 必ず `AS568-013 FKM Viton Shore 60A`（70A/90AやNBRは剛性変化・膨潤で危険速度に接触）。
3. **潤滑オリフィス (`AHIRU-R3-010`)**: 必ず較正済み `Ø0.25 mm` ルビーオリフィス（Lee `IEPA1211241H` または O'Keefe/Bird Precision 較正ルビーオリフィス）＋ 5µm フィルタ。流量不足は30秒以内に軸受焼付き。
4. **ブレード封じ込めリング & 高温ボルト (`AHIRU-R3-007`)**: Inconel 718 最小肉厚 `2.05 mm` ＋ `A286` 耐熱ボルト＋皿ばね（SUS304ボルトは700°Cクリープで緩むため厳禁）。
5. **タービンブリスク熱処理 (`AHIRU-R3-002`)**: DMLS造形後の **HIP（熱間等方圧加圧）＋時効処理** は省略不可（内部空隙が遠心クリープ破壊の起点になる）。
6. **2面動釣合い (`AHIRU-SVC-002`)**: 必ず組付状態で **`ISO 1940 G0.4`（≤ 0.22 mg·mm/面）** を専門バランサで施工（簡易1面バランス厳禁）。
7. **FADEC 60V MOSFET & 独立WDT (`AHIRU-R3-020`)**: 201k RPM 逆起電力 `25.8 V` に対し `60V定格 BSC028N06LS3`（30V/40V品不可）、暴走時燃料遮断用 `TPS3823-33` 独立WDT、二重 `ICM-42688-P` 実装を維持。
8. **Sorbothane 50D 防振マウント (`AHIRU-R3-021`)**: 一般的なシリコン防振ゴムは 3,350 Hz 帯の減衰が不足し IMU が飽和するため、必ず `Sorbothane 50 Duro` を使用。

---

## 4. 発注前ゲート（Wave 0：発注ボタンを押す前の必須確認）

- [ ] **法規・飛行場所の確認（日本国内）**
  - [ ] 国土交通省 **DIPS 2.0** 機体登録・リモートID準備（MTOW `579 g ≥ 100 g` のため必須）
  - [ ] **消防法** 確認：Jet-A1/灯油（第4類第2石油類）を UN 規格金属携行缶＋防油堤で保管（指定数量未満）、CO₂ 消火器常備
  - [ ] 騒音 `97.4 dB @ 7 m` に対応した屋外テストベンチ場所（RCジェット飛行場または防音設備）を確保
- [ ] **採用ルートの最終決定**
  - [ ] `Route E`（Step-0 EDF訓練・約14.6万円） / `Route C-Min`（市販ジェット極限最安・約50.2万円） / `Route B3`（180mm純自作極限最安・約71.1万円） / `Route B1`（機上発電フル自作・約128.4万円）
- [ ] **製造ファイル完全性確認**
  - [ ] STEP 9点（`manufacturing/generated/step/*.step`）
  - [ ] 2D GD&T DXF 3点（`manufacturing/generated/drawings/*.dxf`）
  - [ ] Gerber 9点＋BOM/CPL（`electronics/generated/gerbers/*`, `AHIRU_FADEC_Rev3_BOM.csv`, `AHIRU_FADEC_Rev3_CPL.csv`）
  - [ ] 本番C11ファームウェア（`firmware/fadec_rev3.c`, `firmware/fadec_rev3.h`）

---

## 5. フェーズ別 完全発注チェックリスト（Wave 1〜4・全27項目）

### Wave 1：最長納期クリティカルパス（Week 1 即発注・納期 3〜6週間）

| 済 | Part No | 品目 | 安全区分 | B3極限自作 | C-Min市販 | B1標準自作 | 推奨ベンダー（2026最安B3基準） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-R3-001` | 6+6 Splitter Centrifugal Compressor Impeller (×1) | Tier-S (妥協厳禁) | \$260 | \$0 | \$380 | JLCCNC / Shenzhen 5-Axis Ti-6Al-4V + CMM + Ø5 H6 | Ø5.000 +0.008/-0.000 mm (H6), 翼厚公差 ±0.03 mm, 浸透探傷ゼロ欠陥 |
| `[ ]` | `AHIRU-R3-002` | 17-Blade Tapered Bleed-Cooled Turbine Blisk (×1) | Tier-S (妥協厳禁) | \$490 | \$0 | \$780 | Unionfab / WeNext IN718 SLM単一プレート相乗り + 共有炉HIP + EDM Ø4 H6 | HIP証明・熱処理成績書, Ø4.000 H6, X線/CT内部空隙ゼロ, 17翼ピッチ異常なし |
| `[ ]` | `AHIRU-R3-003` | High-Stiffness Rotor Main Shaft (×1) | Tier-S (妥協厳禁) | \$165 | \$0 | \$220 | 国内/アジア精密切削＋円筒研削 (Ø5.000 h5, TIR<=2µm) | CMM/真円度測定成績書: Ø5.000 h5, TIR <= 2 µm, Ra <= 0.2 µm |
| `[ ]` | `AHIRU-R3-004` | 15-Vane Diffuser & Integral Bearing Tunnel (×1) | Tier-S (妥協厳禁) | \$210 | \$0 | \$320 | JLCCNC / RapidDirect 5-Axis Al 7075-T651 + Ø11 H6 + 硬質アルマイト | エアマイクロ測定 Ø11.000 H6, 同軸度 <= 5 µm, Oリング溝14%潰し代確認 |
| `[ ]` | `AHIRU-R3-005` | Reverse-Flow Annular Combustor + 12 Vaporizers (×1) | Tier-A (高温重要) | \$280 | \$0 | \$550 | Unionfab / WeNext IN718 SLM (002と単一プレート相乗り・4.4cm³) | 全12気化管+36希釈孔の通気・内視鏡残留粉末ゼロ確認 |
| `[ ]` | `AHIRU-R3-006` | 12-Vane Turbine Stator NGV + Tailcone (×1) | Tier-A (高温重要) | \$230 | \$0 | \$440 | Unionfab / WeNext IN718 SLM (002と相乗り・1.9cm³) + 端面旋盤 | 12静翼流路面積バラつき <= ±3%, フランジ平面度 <= 0.02 mm |
| `[ ]` | `AHIRU-R3-007` | 360° Blade Containment Ring + A286 Flange (×1) | Tier-S (妥協厳禁) | \$175 | \$0 | \$240 | JLCCNC IN718旋盤(壁厚>=2.05mm厳守) + A286耐熱ボルト＆皿ばね | 最小肉厚 >= 2.05 mm 確認, A286ミルシート確認 |
| `[ ]` | `AHIRU-R3-008` | Hybrid Ceramic Angular-Contact Bearings (×2) | Tier-S (妥協厳禁) | \$220 | \$0 | \$240 | GRW代理店 / Boca Bearings (GRW 685-2Z-CE Si3N4 ABEC-7 P4 妥協厳禁) | メーカー証明書(dn >= 1.8M対応), 手回し引っ掛かりゼロ, シールド脱脂処理 |
| `[ ]` | `AHIRU-R3-009` | Squeeze-Film Damper O-Rings (×2) | Tier-S (妥協厳禁) | \$12 | \$0 | \$12 | Parker / ミスミ (AS568-013 FKM Viton 60A 妥協厳禁) | 硬度 60±5 Shore A, 断面径 1.78±0.08 mm 確認 |
| `[ ]` | `AHIRU-R3-010` | Metered Oil-Mist Restrictors & Capillary Lines (×2) | Tier-S (妥協厳禁) | \$140 | \$0 | \$190 | O'Keefe / Bird Precision 流量較正済Ø0.25mmルビーオリフィス + 5µmフィルタ | 1.8 bar ろ過Jet-A1で各 0.12 ± 0.01 mL/min 実測確認 |
| `[ ]` | `AHIRU-R3-012` | Celeroton-Class Direct-Coupled Starter-Generator (×1) | Tier-A (高速回転重要) | \$55 | \$0 | \$580 | 外部手持ちBLDCスタータワンド (2838 BLDC + 30A ESC + シリコンカップ) | Route B1: 201k RPM相当スピン/線間逆起電力 Kv=7,800±5% 確認, 絶縁耐圧 >= 100V |
| `[ ]` | `AHIRU-R3-013` | Choked Chevron De Laval Nozzle & Ti Gimbal (×1) | Tier-A (推力偏向重要) | \$290 | \$240 | \$480 | Unionfab IN718 SLM相乗りノズル + 4軸CNC Tiジンバル (EDF機はPA12-CF造形) | ±14°全象限スムーズ可動(フリクション <= 12 mNm), クリアランス >= 9 mm |
| `[ ]` | `AHIRU-R3-015` | Bleed-Air Proportional Yaw RCS Valves & Nozzles (×2) | Tier-A (ヨー制御重要) | \$125 | \$125 | \$280 | SMC S070 / Parker X-Valve 5V高速マイクロソレノイド弁×2 + Ti細管 | 5V駆動リークゼロ, 50Hz PWM比例流量応答確認 |
| `[ ]` | `AHIRU-SVC-001` | 市販認証済みマイクロタービンコア一式（Route C専用：Swiwin SW30B / KingTech K30G4+ 等） (×1) | Tier-S (Route C中核) | \$0 | \$1,550 | \$0 | C-Min: Swiwin SW60B/SW30B直販 ($1,450-$1,650) / Route E: 64mm 6S EDF+80A ESC ($145) | メーカー出荷ベンチテスト成績書確認, 地上アイドル〜最大推力動作確認 |

### Wave 2：電装PCBA・サーボ・燃料系・バッテリー（Week 1〜2 発注・納期 1〜3週間）

| 済 | Part No | 品目 | 安全区分 | B3極限自作 | C-Min市販 | B1標準自作 | 推奨ベンダー（2026最安B3基準） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-R3-014` | High-Speed Metal-Gear HV TVC Servos + Ti Linkages (×2) | Tier-A (姿勢制御重要) | \$95 | \$95 | \$130 | KST公式直販 (KST X08H Plus V6.0 $39.99×2 + Tiプッシュロッド) | 無負荷応答 <= 0.08s/60°, バックラッシ <= 0.25° |
| `[ ]` | `AHIRU-R3-016` | 290° Conformal Saddle Tank + 3 Baffles + UAT (×1) | Tier-A (燃料安全重要) | \$68 | \$75 | \$145 | JLC3DP MJF PA12 ($0.275/g, 31.6g) + 耐Jet-A1 Novolac/Viton内面コート | 満水139.5±2 mL, 0.5 bar 30分リークゼロ, Jet-A1 72時間浸漬膨潤なし |
| `[ ]` | `AHIRU-R3-017` | Brushless Micro Gear Fuel Pump + Si3N4 Igniter (×1) | Tier-A (燃料供給重要) | \$165 | \$0 | \$260 | Xicoy/Swiwin OEM ブラシレスマイクロ燃料ポンプ + 11V Si3N4グロープラグ | 0.1〜4.0 bar吐出流量カーブ取得, 気泡混入ゼロ |
| `[ ]` | `AHIRU-R3-020` | 4-Layer STM32H743 FADEC + 60V FOC + Dual IMU PCBA (×1) | Tier-S (妥協厳禁) | \$235 | \$235 | \$425 | JLCPCB 4層 TG170 2oz ENIG (5枚基板+2枚SMT実装・Tier-S部品厳守) | 通電3.3V/5V実測, SWD(ST-LINK/V3)で firmware/fadec_rev3.c 書込+WDT遮断テスト合格 |
| `[ ]` | `AHIRU-R3-021` | Sorbothane 50D IMU Isolation Mount + Optical Eyes (×1) | Tier-S (妥協厳禁) | \$72 | \$72 | \$95 | Isolate It! Sorbothane 50Dグロメット(厳守) + DigiKey VL53L4CD/熱電対 | 固有振動数 35〜45 Hz 確認, 3350 Hz加振でジャイロRMS < 0.08 deg/s |
| `[ ]` | `AHIRU-R3-022` | Split-Balanced 3S 750 mAh 60C LiHV Battery Pack (×1) | Tier-A (電源安全重要) | \$42 | \$42 | \$85 | GNB / Tattu 1S 850mAh 60C LiHV ×3 分割組電池 (EDF機は6S 1300mAh) | 内部抵抗測定(ESR <= 65 mΩ), 30A負荷テストで V_bus >= 9.5 V |

### Wave 3：外殻・内部フレーム・断熱材・安全試験治具（Week 2〜3 発注・納期 1〜3週間）

| 済 | Part No | 品目 | 安全区分 | B3極限自作 | C-Min市販 | B1標準自作 | 推奨ベンダー（2026最安B3基準） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-R3-011` | Silica Aerogel Shroud + Gold Liner + ZrO2 Firewall (×1) | Tier-A (熱安全重要) | \$115 | \$95 | \$210 | カットシート Pyrogel XTE + DEI Reflect-A-Gold + 工業用YSZ板 | LiHVバッテリー〜燃焼器外殻ギャップ >= 13.5 mm 実測 |
| `[ ]` | `AHIRU-R3-018` | Duck CFRP Shell, S-Duct Intakes, Wings & Belly (×1) | Tier-B (コスト最適化大) | \$115 | \$135 | \$260 | JLC3DP MJF PA12-CF (2026年7月 -24%値下げ後単価, 108.5g) + YSZ底部断熱 | 総外殻質量 <= 115 g, 合わせ面段差 <= 0.3 mm, Sダクト内面平滑研磨 |
| `[ ]` | `AHIRU-R3-019` | Al 7075-T6 Internal Frame & 26.8mm Oleo-Ti Struts (×1) | Tier-A (構造重要) | \$195 | \$220 | \$340 | JLCCNC Al 7075-T6フレーム + ミスミ規格ばね/Tiパイプ脚 | 10G静的荷重(60 N)たわみ確認, 着陸脚ストローク 15.6 mm 確認 |
| `[ ]` | `AHIRU-R3-023` | Harnesses, Silicone/PTFE Wire, XT30, Hardware (×1) | Tier-A (配線信頼性) | \$55 | \$55 | \$110 | LCSC / ミスミ PTFEシールドツイストペア + AWG14シリコン + Tiねじ | 全コネクタ抜去力・導通・絶縁確認, ツイストピッチ <= 5 mm |
| `[ ]` | `AHIRU-SVC-003` | 屋外火入れ試験台・3点重心計・防爆シールド・CO2消火器・二重聴覚保護具・係留3軸リグ (×1) | Tier-S (人命安全) | \$310 | \$310 | \$480 | DIYアルミフレーム推力台 + HX711 + 8mmポリカ防爆板 + CO2消火器 + 二重防音 | 非常停止応答 < 50 ms, ロードセル較正誤差 <= ±0.05 N, 3点CoG測定精度 <= ±0.5 mm |

### Wave 1–2 同時同梱：クリティカル予備品（再調達6週間待ちの防止）

| 済 | Part No | 品目 | 安全区分 | B3極限自作 | C-Min市販 | B1標準自作 | 推奨ベンダー（2026最安B3基準） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-SPR-001` | 消耗・破損リスク予備品パック（GRW 685軸受×2, Viton Oリング×10, KSTサーボ×1, 熱電対×2, 燃料フィルタ） (×1) | Tier-A (開発停止防止) | \$240 | \$95 | \$360 | 最低限クリティカル予備 (GRW 685軸受×2 + Viton Oリング + フィルタ) | 全スペア部品の防湿保管・シリアル番号紐付け完了 |

### Wave 4：受入精密検査・外部2面 G0.4 動釣合い（Week 5〜7・組付前必須ゲート）

| 済 | Part No | 品目 | 安全区分 | B3極限自作 | C-Min市販 | B1標準自作 | 推奨ベンダー（2026最安B3基準） | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---:|---|---|
| `[ ]` | `AHIRU-SVC-002` | 外部2面動釣合い加工（ISO 1940 G0.4 @ 201,000 RPM）＋主要部CMM検査サービス (×1) | Tier-S (妥協厳禁) | \$380 | \$0 | \$950 | 深圳/上海 高速マイクロターボ専門2面動釣合い (ISO 1940 G0.4 <=0.22mg·mm) | 釣合い成績書 <= 0.22 mg·mm/面 (G0.4), 再組付用位相合いマーク刻印済 |


---

## 6. サプライヤー別 RFQ（見積依頼）送信パッケージ一覧

業者ごとに以下の ZIP パッケージを作ってそのまま見積依頼（RFQ）を送れます：

| パッケージ | 送信先業種・推奨ベンダー | 添付するリポジトリ内ファイル | 見積依頼時の必須追記文（コピー可） |
|---|---|---|---|
| **RFQ-1: 金属3Dプリント (Inconel 718 単一プレート相乗り)** | Unionfab / WeNext / FacFox | `02_turbine_blisk_Inconel718.step`, `05_combustor_liner_Inconel718.step`, `00_AHIRU_Rev3_Core_Assembly.step`, `07_tvc_gimbal_chevron_nozzle.step`, `DWG_03_Blisks_Flanges_IMU_GDT.dxf` | *Material: Inconel 718 (AMS 5662/5663). Total volume ~9.5 cm³. Please nest all 4 parts on a single build plate and share HIP furnace batch for Part 02 (Turbine Blisk, mandatory HIP + solution/age); stress relief + complete powder removal inside 12 vaporizer tubes for Part 05. Wire-EDM/grind Ø4.000 H6 bore on Part 02 per DWG_03.* |
| **RFQ-2: 5軸CNC & 精密研削 (Ti / Al / IN718)** | JLCCNC / RapidDirect / PCBWay CNC | `01_compressor_impeller_Ti6Al4V.step`, `03_rotor_shaft_Inconel718.step`, `04_diffuser_bearing_tunnel_Al7075.step`, `06_containment_flange_Inconel718.step`, `DWG_01/02/03.dxf` | *Critical aerospace tolerances per attached DXFs: Shaft Ø5.000 h5 (+0/-0.005mm, Ra<=0.2um, TIR<=2um post-heat-treat cylindrical grind); Diffuser bore Ø11.000 H6 (+0.011/-0mm, coaxiality<=5um, mask bore during hard anodize); Impeller bore Ø5.000 H6; Containment wall >=2.05mm. CMM report mandatory.* |
| **RFQ-3: 4層PCBA + 2枚SMT実装** | JLCPCB | `electronics/generated/gerbers/*` (9ファイルZIP), `AHIRU_FADEC_Rev3_BOM.csv`, `AHIRU_FADEC_Rev3_CPL.csv` | *4-layer FR-4 High-Tg (TG170), 1.6mm, 2oz copper (outer & inner), ENIG finish, 5 bare PCBs + SMT assembly on 2 boards (Route B3/C-Min) or 5 boards (Route B1). NO substitutions for U1(STM32H743), U2/U3(ICM-42688-P), U6(DRV8353RS), Q1-Q6(BSC028N06LS3 60V), U9(TPS3823-33).* |
| **RFQ-4: 樹脂3Dプリント (外殻 & 燃料タンク)** | JLC3DP | `00_AHIRU_Rev3_Core_Assembly.step`, `index.html`抽出STL, `08_imu_sorbothane_mount_assembly.step` | *Fuel tank: MJF PA12 ($0.275/g) with 3 internal perforated baffles & UAT sump (powder-free interior, apply fuel-resistant Novolac/Viton internal sealer). Outer duck shell: MJF PA12-CF (Route B3/C-Min/E, shell max verified 28.3°C).* |
| **RFQ-5: 航空宇宙COTS精密部品** | GRW代理店 / O'Keefe / KST公式 / Xicoy | `BOM_AHIRU_Rev3.csv`（Part `008, 009, 010, 014, 015, 017`） | *Exact P/Ns only: GRW 685-2Z-CE Si3N4 ABEC-7 P4 (Qty 4 incl. spares), AS568-013 FKM Viton 60A (Qty 10), calibrated Ø0.25mm ruby orifice (Lee IEPA1211241H or O'Keefe + 5µm filter, Qty 2), KST X08H Plus V6.0 ($39.99/ea, Qty 2-3), 5V 3ms micro-solenoid (Lee LHDA or SMC S070, Qty 2).* |
| **RFQ-6: 外部 2面 G0.4 動釣合い** | 高速動釣合い専門工場（国内/深圳マイクロターボ工房） | `DWG_01_Rotor_Shaft_GDT.dxf`, `DWG_03_Blisks_Flanges_IMU_GDT.dxf`, `FLIGHT_QUALIFICATION_MANUAL.md` | *201,000 RPM マイクロタービン用ロータASSY（質量約36g）の2面動釣合い。ISO 1940 G0.4（残存不釣合い ≤ 0.22 mg·mm/面）。修正削りは図面指定のフロントカラー・リアボスのみ。分解再組付用の位相刻印および成績書発行を希望。* |

---

## 7. 推奨ステップアップ実行タイムライン（最短2週間〜8週間）

```text
[Step-0 電動EDF訓練機 Route E: 2–3週間 / 約14.6万円]
Week 1 : JLC3DP PA12-CF外殻 + JLCPCB FADEC(2枚SMT) + KST X08H Plus + 64mm 6S EDF 発注
Week 2 : C11 FW (fadec_rev3.c) 書込 → 係留3軸SysID → 屋外フリーホバリング・TVC制御完全実証！

[市販ジェット極限最安 Route C-Min: 3–4週間 / 約50.2万円]
Week 1 : Swiwin SW60B/SW30B直販 + Unionfab TVCノズル + JLC3DP外殻/タンク + JLCPCB/KST 発注
Week 2 : 安全治具・ロードセル推力台製作 + C11 FW ベンチ試験
Week 3 : 全品受入・組付・3点CoG調整 (±2.5mm)・地上火入れ (Gate B1-B4)
Week 4 : 係留3軸SysID (Gate F1-F2) → 地面効果確認 (F3) → 本物のジェットで初フリーホバリング (F4)！

[純粋自作180mm極限最安 Route B3: 5–7週間 / 約71.1万円]
Week 1   : Wave 1 一括発注 (IN718 SLM単一プレート+共有HIP + JLCCNC 5軸 + GRW軸受 + ルビーオリフィス)
Week 2-3 : Wave 2-3 受入 (JLCPCB 2枚SMT + JLC3DP外殻/タンク + DIY防爆試験台完成)
Week 4-5 : 回転系受入 → CMM/エアマイクロ公差検査 (h5/H6/TIR<=2µm) → 2面G0.4動釣合い
Week 6-7 : 屋外防爆セル火入れ (B1→B4) → 係留SysID (F1→F3) → 180mm完全自作機 初ホバリング (F4)！
```
