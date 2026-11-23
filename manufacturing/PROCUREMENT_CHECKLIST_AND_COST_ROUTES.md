# RikiGaku-AHIRU Rev.3 — 実機製作 発注チェックリスト & コスト最小化ルート選定書

> **前提**: 本書は実機 Colab GPU 上で **Rev.3 6-Wall Qualification (7/7 PASS, 10万回MC生存率 100.0%)**・**V12 (0 FAIL)**・**MDAO/V&V (Phase 1〜9 PASS, OpenTURNS信頼度 100.00%)** を通過した確定設計（[BOM_AHIRU_Rev3.csv](generated/BOM_AHIRU_Rev3.csv)）に基づく実務発注仕様書です。  
> 為替換算レート目安：`1 USD = 150 JPY`。Excel/Google スプレッドシート管理用CSV：[procurement_checklist.csv](procurement_checklist.csv)

---

## 1. コスト最小化 4ルート定量比較（検査・動釣合い・安全設備・予備品まで全計上）

「機体部品だけ安く見えて、後から動釣合い・防爆治具・予備品で予算超過する」ことを防ぐため、**全ルートに外部検査/釣合い・安全試験設備・予備品まで全額含めた総実費**で比較しています。

| ルート | コンセプト | 機体BOM (23品目) | COTSコア/釣合い/安全/予備 | **総額 (USD)** | **総額目安 (JPY)** | Route A比 | 最短納期 | 推奨用途 |
|---|---|---:|---:|---:|---:|---:|---|---|
| **Route A** | フルカスタム航空宇宙仕様（欧米/国内ワンオフ） | \$13,467 | \$2,870 | **\$16,337** | **約245.1万円** | 基準 | 10–14週間 | 機関・法人向けフルスペック実証 |
| **Route B1（純自作最推奨）** | **戦略的アジア高精度CNC＋DMLS一括ネスト＋MJF外殻**（180mm完全オリジナルRev.3） | \$6,772 | \$1,790 | **\$8,562** | **約128.4万円** | **-47.6%** | 6–8週間 | **完全自作エンジンでRev.3を最小コスト実現** |
| **Route B2（初号機最安自作）** | Route B1＋**初号機限定「外部電動スタータ始動」**（機上発電省略で `-19.4 g` 軽量化） | \$6,312 | \$1,790 | **\$8,102** | **約121.5万円** | **-50.4%** | 5–7週間 | **初号機ホバリング実証のコスト＆重量最小化** |
| **Route C（最短初飛行最推奨）** | **市販認証済みマイクロタービン（SW30B/K30G4+）換装 1.25× 機体** | \$2,500 | \$2,570 | **\$5,070** | **約76.0万円** | **-69.0%** | 3–4週間 | **最短3〜4週間・最小リスクで初飛行達成** |
| **Route D（10機ロット単価）** | Route B1最適化を10機バッチ発注（1機あたり単価） | \$3,431 | \$375 | **\$3,806/機** | **約57.1万円/機** | **-76.7%** | 7–9週間 (10機) | 研究室・共同製作・小ロット量産 |

### 結論：最も賢いコスト最小化ルート選定

1. **「確実に最短・最安で飛ばす」なら → `Route C`（総額 \$5,070 / 約76.0万円・3〜4週間）**
   - 201,000 RPM 自作タービンの公差・HIP・G0.4 動釣合いリスクを丸ごと回避し、メーカー保証済みの市販マイクロタービン（Swiwin SW30B 等）を搭載。
   - **自作FADEC基板（`AHIRU-R3-020`）・Sorbothane 50D防振（`021`）・2軸TVCシェブロンノズル（`013`）・C11ファームウェア（`firmware/fadec_rev3.c`）は 100% そのまま実機実証**できます。
2. **「180×200×100 mm の純粋自作エンジン機を最小コストで作る」なら → `Route B2`（\$8,102 / 約121.5万円）または `Route B1`（\$8,562 / 約128.4万円）**
   - Route A と同じ安全マージン（GRW 685軸受・Inconel 718 HIP・Leeルビーオリフィス・2面G0.4釣合い・60V FOC PCBA）を一切削らず、加工手配の最適化だけで **約 47.6%〜50.4% のコスト削減**を実現します。
3. **プロ推奨の2段階ステップ方式（総失敗コスト最小）**
   - **Step 1**: まず `Route C`（約76.0万円）でアヒル機体のホバリング・TVC制御・地面効果・前進遷移を 100% 実証。
   - **Step 2**: 制御と運用が確立した状態で `Route B1/B2` の純粋自作 Ø38mm コアへ移行（PCBA・安全設備・地上試験治具・サーボ・計測器はそのまま流用できるため、Step 2 の追加投資はさらに圧縮可能）。

---

## 2. Route A → Route B1 コスト削減の主要ドライバー（どこで安全を削らずに安くするか）

| 順位 | Part No | 品目 | Route A (ワンオフ) | Route B1 (最適化) | 削減額 | 安全・性能への影響 |
|---:|---|---|---:|---:|---:|---|
| 1 | `AHIRU-R3-018` | Duck CFRP Shell, S-Duct Intakes, Wings & Belly | \$1,350 | \$260 | **-\$1,090** | 実ソルバー熱解析で外殻最高温度28.3°Cのため、初号機はPEEK-CF30オートクレーブ(USD 1,350)からPA12-CF MJF(USD 260)へ代替で-81%削減しつつ剛性・質量維持 |
| 2 | `AHIRU-R3-002` | 17-Blade Tapered Bleed-Cooled Turbine Blisk | \$1,650 | \$780 | **-\$870** | Inconel 718 AMS 5662/5663 |
| 3 | `AHIRU-R3-012` | Celeroton-Class Direct-Coupled Starter-Generator | \$1,450 | \$580 | **-\$870** | Route B1: SmCo28(300°C耐熱、NdFeB不可!)+0.35mm IN718リテーナスリーブ圧入 |
| 4 | `AHIRU-R3-001` | 6+6 Splitter Centrifugal Compressor Impeller | \$950 | \$380 | **-\$570** | Ti-6Al-4V Gr.5 AMS 4928 |
| 5 | `AHIRU-R3-005` | Reverse-Flow Annular Combustor + 12 Vaporizers | \$1,100 | \$550 | **-\$550** | 肉厚0.8mm + 12気化管内部粉末の完全除去(超音波+エアブロー確認) |
| 6 | `AHIRU-R3-004` | 15-Vane Diffuser & Integral Bearing Tunnel | \$820 | \$320 | **-\$500** | Ø11.000 H6(+0.011/-0)軸受穴は前後一発通し加工(同軸度<=5um) |
| 7 | `AHIRU-R3-013` | Choked Chevron De Laval Nozzle & Ti Gimbal | \$920 | \$480 | **-\$440** | スロート半径 r_t=7.4mm/出口 r_e=8.6mm 12シェブロン |
| 8 | `AHIRU-R3-019` | Al 7075-T6 Internal Frame & 26.8mm Oleo-Ti Struts | \$760 | \$340 | **-\$420** | Al 7075-T651 |

> **注目ポイント**：
> - **Inconel 718 DMLS 一括ネスト（4部品相乗り）**：`AHIRU-R3-002 / 005 / 006 / 013` を別々に発注すると毎回セットアップ費・粉末充填費・熱処理炉チャージが発生します。**1枚のビルドプレートに4部品をネスト同時造形＋一括応力除去**することで約50%削減できます。
> - **アヒル外殻の PA12-CF MJF 代替**：V12・MDAO/V&V の連成熱解析で外殻最高温度は **`28.3 °C`**（耐熱火壁 `AHIRU-R3-011` が別体）と実証済みのため、初号機は PEEK-CF30 オートクレーブ（\$1,350）ではなく **PA12-CF MJF 一体造形（\$260）** で安全マージンを落とさずに **-\$1,090（-81%）** 削減できます。
> - **FADEC PCBA の JLCPCB 5枚バッチ化**：1枚特注（\$380）より **JLCPCB 5枚バッチ（\$425＝1枚あたり\$85）** の方が予備4枚が確保でき、試験中の万一のショートでも開発が止まりません。

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
  - [ ] `Route C`（最短初飛行・約76.0万円） / `Route B2`（初号機最安自作・約121.5万円） / `Route B1`（完全Rev.3自作・約128.4万円）のいずれかを選択
- [ ] **製造ファイル完全性確認**
  - [ ] STEP 9点（`manufacturing/generated/step/*.step`）
  - [ ] 2D GD&T DXF 3点（`manufacturing/generated/drawings/*.dxf`）
  - [ ] Gerber 9点＋BOM/CPL（`electronics/generated/gerbers/*`, `AHIRU_FADEC_Rev3_BOM.csv`, `AHIRU_FADEC_Rev3_CPL.csv`）
  - [ ] 本番C11ファームウェア（`firmware/fadec_rev3.c`, `firmware/fadec_rev3.h`）

---

## 5. フェーズ別 完全発注チェックリスト（Wave 1〜4・全27項目）

### Wave 1：最長納期クリティカルパス（Week 1 即発注・納期 3〜6週間）

| 済 | Part No | 品目 | 安全区分 | Route B1 (USD) | Route C (USD) | 推奨ベンダー（B1基準） | 納期 | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---|---|---|
| `[ ]` | `AHIRU-R3-001` | 6+6 Splitter Centrifugal Compressor Impeller (×1) | Tier-S (妥協厳禁) | \$380 | \$0 | PCBWay CNC / RapidDirect 5-Axis Ti-6Al-4V + 国内H6仕上げ | 3-4w | Ø5.000 +0.008/-0.000 mm (H6), 翼厚公差 ±0.03 mm, 浸透探傷ゼロ欠陥 |
| `[ ]` | `AHIRU-R3-002` | 17-Blade Tapered Bleed-Cooled Turbine Blisk (×1) | Tier-S (妥協厳禁) | \$780 | \$0 | Unionfab / Xometry Asia Inconel 718 DMLS一括ネスト + HIP + 5軸仕上げ | 4-6w | HIP証明・熱処理成績書, Ø4.000 H6, X線/CT内部空隙ゼロ, 17翼ピッチ異常なし |
| `[ ]` | `AHIRU-R3-003` | High-Stiffness Rotor Main Shaft (×1) | Tier-S (妥協厳禁) | \$220 | \$0 | 国内精密切削/円筒研削（ミスミmeviy / 国内町工場） | 2-3w | CMM/真円度測定成績書: Ø5.000 h5, TIR <= 2 µm, Ra <= 0.2 µm |
| `[ ]` | `AHIRU-R3-004` | 15-Vane Diffuser & Integral Bearing Tunnel (×1) | Tier-S (妥協厳禁) | \$320 | \$0 | PCBWay CNC / RapidDirect 5-Axis Al 7075-T651 + 硬質アルマイト(ボアマスキング) | 3-4w | エアマイクロ測定 Ø11.000 H6, 同軸度 <= 5 µm, Oリング溝14%潰し代確認 |
| `[ ]` | `AHIRU-R3-005` | Reverse-Flow Annular Combustor + 12 Vaporizers (×1) | Tier-A (高温重要) | \$550 | \$0 | Unionfab / FacFox Inconel 718 DMLS一括ネスト（002と同プレート） | 3-4w | 全12気化管+36希釈孔の通気・内視鏡残留粉末ゼロ確認 |
| `[ ]` | `AHIRU-R3-006` | 12-Vane Turbine Stator NGV + Tailcone (×1) | Tier-A (高温重要) | \$440 | \$0 | Unionfab / FacFox Inconel 718 DMLS一括ネスト + 端面旋盤仕上げ | 3-4w | 12静翼流路面積バラつき <= ±3%, フランジ平面度 <= 0.02 mm |
| `[ ]` | `AHIRU-R3-007` | 360° Blade Containment Ring + A286 Flange (×1) | Tier-S (妥協厳禁) | \$240 | \$0 | PCBWay CNC Inconel 718 旋盤 + McMaster/ミスミ A286ボルト＆皿ばね | 2-3w | 最小肉厚 >= 2.05 mm 確認, A286ミルシート確認 |
| `[ ]` | `AHIRU-R3-008` | Hybrid Ceramic Angular-Contact Bearings (×2) | Tier-S (妥協厳禁) | \$240 | \$0 | GRW代理店 / Boca Bearings / WIB（GRW 685-2Z-CE Si3N4 ABEC-7 P4） | 3-6w | メーカー証明書(dn >= 1.8M対応), 手回し引っ掛かりゼロ, シールド脱脂処理 |
| `[ ]` | `AHIRU-R3-009` | Squeeze-Film Damper O-Rings (×2) | Tier-S (妥協厳禁) | \$12 | \$0 | Parker / McMaster-Carr / ミスミ（AS568-013 FKM Viton 60A） | 1w | 硬度 60±5 Shore A, 断面径 1.78±0.08 mm 確認 |
| `[ ]` | `AHIRU-R3-010` | Metered Oil-Mist Restrictors & Capillary Lines (×2) | Tier-S (妥協厳禁) | \$190 | \$0 | The Lee Company Japan（IEPA1211241H / Ø0.25mmルビーオリフィス） | 2-4w | 1.8 bar ろ過Jet-A1で各 0.12 ± 0.01 mL/min 実測確認 |
| `[ ]` | `AHIRU-R3-012` | Celeroton-Class Direct-Coupled Starter-Generator (×1) | Tier-A (高速回転重要) | \$580 | \$0 | 中国超高速PM特注(SmCo28 2極+0.35mm IN718圧入スリーブ+0.1mm NO10ステータ) | 4-6w | Route B1: 201k RPM相当スピン/線間逆起電力 Kv=7,800±5% 確認, 絶縁耐圧 >= 100V |
| `[ ]` | `AHIRU-R3-013` | Choked Chevron De Laval Nozzle & Ti Gimbal (×1) | Tier-A (推力偏向重要) | \$480 | \$360 | Unionfab Inconel 718 DMLS一括ネスト（002と同プレート）+ TiジンバルリングCNC | 3-4w | ±14°全象限スムーズ可動(フリクション <= 12 mNm), クリアランス >= 9 mm |
| `[ ]` | `AHIRU-R3-015` | Bleed-Air Proportional Yaw RCS Valves & Nozzles (×2) | Tier-A (ヨー制御重要) | \$280 | \$280 | The Lee Company Japan（LHDA0523111H 超小型高速ソレノイド弁 × 2 + Ti細管） | 3-5w | 5V駆動リークゼロ, 50Hz PWM比例流量応答確認 |
| `[ ]` | `AHIRU-SVC-001` | 市販認証済みマイクロタービンコア一式（Route C専用：Swiwin SW30B / KingTech K30G4+ 等） (×1) | Tier-S (Route C中核) | \$0 | \$1,950 | 不要（自作コア使用） | - | メーカー出荷ベンチテスト成績書確認, 地上アイドル〜最大推力動作確認 |

### Wave 2：電装PCBA・サーボ・燃料系・バッテリー（Week 1〜2 発注・納期 1〜3週間）

| 済 | Part No | 品目 | 安全区分 | Route B1 (USD) | Route C (USD) | 推奨ベンダー（B1基準） | 納期 | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---|---|---|
| `[ ]` | `AHIRU-R3-014` | High-Speed Metal-Gear HV TVC Servos + Ti Linkages (×2) | Tier-A (姿勢制御重要) | \$130 | \$130 | KST公式 / 国内RCショップ（KST X08H Plus V6.0 × 2個 + Tiリンク） | 1-2w | 無負荷応答 <= 0.08s/60°, バックラッシ <= 0.25° |
| `[ ]` | `AHIRU-R3-016` | 290° Conformal Saddle Tank + 3 Baffles + UAT (×1) | Tier-A (燃料安全重要) | \$145 | \$165 | JLCPCB 3DP / FacFox PA12 MJF造形 + 耐燃料FKM/エポキシ内面コート(Baffles+UAT一体) | 2w | 満水139.5±2 mL, 0.5 bar 30分リークゼロ, Jet-A1 72時間浸漬膨潤なし |
| `[ ]` | `AHIRU-R3-017` | Brushless Micro Gear Fuel Pump + Si3N4 Igniter (×1) | Tier-A (燃料供給重要) | \$260 | \$0 | Flightworks 200-series / KingTech互換ブラシレスギアポンプ + 11Vセラミックイグナイタ | 2-3w | 0.1〜4.0 bar吐出流量カーブ取得, 気泡混入ゼロ |
| `[ ]` | `AHIRU-R3-020` | 4-Layer STM32H743 FADEC + 60V FOC + Dual IMU PCBA (×1) | Tier-S (妥協厳禁) | \$425 | \$425 | JLCPCB 4層 TG170 2oz銅 ENIG + PCBA実装（5枚セット発注＝本体1+予備4） | 2w | 通電3.3V/5V実測, SWD(ST-LINK/V3)で firmware/fadec_rev3.c 書込+WDT遮断テスト合格 |
| `[ ]` | `AHIRU-R3-021` | Sorbothane 50D IMU Isolation Mount + Optical Eyes (×1) | Tier-S (妥協厳禁) | \$95 | \$95 | Isolate It! / McMaster Sorbothane 50Dグロメット + DigiKey(VL53L4CD, K型熱電対) | 1-2w | 固有振動数 35〜45 Hz 確認, 3350 Hz加振でジャイロRMS < 0.08 deg/s |
| `[ ]` | `AHIRU-R3-022` | Split-Balanced 3S 750 mAh 60C LiHV Battery Pack (×1) | Tier-A (電源安全重要) | \$85 | \$85 | Tattu / GNB 750-850mAh 60C-90C 1S LiHVセル×3 分割組電池(胸2+尾1) | 1-2w | 内部抵抗測定(ESR <= 65 mΩ), 30A負荷テストで V_bus >= 9.5 V |

### Wave 3：外殻・内部フレーム・断熱材・安全試験治具（Week 2〜3 発注・納期 1〜3週間）

| 済 | Part No | 品目 | 安全区分 | Route B1 (USD) | Route C (USD) | 推奨ベンダー（B1基準） | 納期 | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---|---|---|
| `[ ]` | `AHIRU-R3-011` | Silica Aerogel Shroud + Gold Liner + ZrO2 Firewall (×1) | Tier-A (熱安全重要) | \$210 | \$160 | Aspen Aerogels Pyrogel + DEI金箔遮熱シート + 国内ジルコニア(YSZ)板カット | 2w | LiHVバッテリー〜燃焼器外殻ギャップ >= 13.5 mm 実測 |
| `[ ]` | `AHIRU-R3-018` | Duck CFRP Shell, S-Duct Intakes, Wings & Belly (×1) | Tier-B (コスト最適化大) | \$260 | \$310 | JLCPCB 3DP / FacFox PA12-CF(炭素繊維強化ナイロン) MJF分割造形 + YSZ底部断熱 | 2w | 総外殻質量 <= 115 g, 合わせ面段差 <= 0.3 mm, Sダクト内面平滑研磨 |
| `[ ]` | `AHIRU-R3-019` | Al 7075-T6 Internal Frame & 26.8mm Oleo-Ti Struts (×1) | Tier-A (構造重要) | \$340 | \$380 | PCBWay CNC / ミスミmeviy Al 7075-T6 フレーム + ミスミ規格ばね/Ti脚パイプ | 2-3w | 10G静的荷重(60 N)たわみ確認, 着陸脚ストローク 15.6 mm 確認 |
| `[ ]` | `AHIRU-R3-023` | Harnesses, Silicone/PTFE Wire, XT30, Hardware (×1) | Tier-A (配線信頼性) | \$110 | \$110 | ミスミ / DigiKey（PTFE同軸・AWG14シリコン・XT30・JST-GH・Ti M2/M2.5ねじ） | 1w | 全コネクタ抜去力・導通・絶縁確認, ツイストピッチ <= 5 mm |
| `[ ]` | `AHIRU-SVC-003` | 屋外火入れ試験台・3点重心計・防爆シールド・CO2消火器・二重聴覚保護具・係留3軸リグ (×1) | Tier-S (人命安全) | \$480 | \$480 | モノタロウ / ミスミ / Amazon / DigiKey（ST-LINK/V3MINI, HX711ロードセル等） | 1-2w | 非常停止応答 < 50 ms, ロードセル較正誤差 <= ±0.05 N, 3点CoG測定精度 <= ±0.5 mm |

### Wave 1–2 同時同梱：クリティカル予備品（再調達6週間待ちの防止）

| 済 | Part No | 品目 | 安全区分 | Route B1 (USD) | Route C (USD) | 推奨ベンダー（B1基準） | 納期 | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---|---|---|
| `[ ]` | `AHIRU-SPR-001` | 消耗・破損リスク予備品パック（GRW 685軸受×2, Viton Oリング×10, KSTサーボ×1, 熱電対×2, 燃料フィルタ） (×1) | Tier-A (開発停止防止) | \$360 | \$140 | 本体発注時に同一ベンダーへ同時追加（送料・再調達6週間待ちを回避） | 2-4w | 全スペア部品の防湿保管・シリアル番号紐付け完了 |

### Wave 4：受入精密検査・外部2面 G0.4 動釣合い（Week 5〜7・組付前必須ゲート）

| 済 | Part No | 品目 | 安全区分 | Route B1 (USD) | Route C (USD) | 推奨ベンダー（B1基準） | 納期 | 受入合格基準（抜粋） |
|:---:|---|---|---|---:|---:|---|---|---|
| `[ ]` | `AHIRU-SVC-002` | 外部2面動釣合い加工（ISO 1940 G0.4 @ 201,000 RPM）＋主要部CMM検査サービス (×1) | Tier-S (妥協厳禁) | \$950 | \$0 | 国内高速動釣合い受託（長浜製作所/国際計測器系受託・ターボチャージャ専門工房） | 1-2w | 釣合い成績書 <= 0.22 mg·mm/面 (G0.4), 再組付用位相合いマーク刻印済 |


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
[Route C 最短初飛行: 4週間 / 約76.0万円]
Week 1 : Wave 1-2 全発注 (SW30B/K30G4+ + JLCPCB 5枚 + TVCノズル + PA12-CF外殻/タンク + KST/Lee)
Week 2 : 安全治具・ロードセル推力台製作 + C11 FW (fadec_rev3.c) ベンチ試験
Week 3 : 全品受入・組付・3点CoG調整 (±2.5mm)・地上火入れ (Gate B1-B4)
Week 4 : 係留3軸SysID (Gate F1-F2) → 地面効果確認 (F3) → 初フリーホバリング (F4)！

[Route B1 純粋自作Rev.3: 8週間 / 約128.4万円]
Week 1   : Wave 1 最長納期一括発注 (IN718 DMLSネスト + Ti/Al/IN718 5軸CNC + GRW軸受 + Lee + スタータ)
Week 2-3 : Wave 2-3 発注 & 受入 (JLCPCB 5枚 + FWベンチ通電 + 外殻/フレーム/防爆試験台完成)
Week 4-5 : 回転系・燃焼器受入 → CMM/エアマイクロ公差検査 (h5/H6/TIR<=2µm) → ルビーオリフィス流量試験
Week 6   : 外部2面動釣合い (ISO 1940 G0.4 <= 0.22 mg·mm/面) → コア最終組付
Week 7   : 屋外防爆セル火入れ試験 (Gate B1冷間回転 → B2点火 → B3 201k RPM全開 → B4 300sソークバック)
Week 8   : 係留3軸SysID (Gate F1-F2) → 地面効果HGI確認 (F3) → 初フリーホバリング & 前進遷移 (F4)！
```
