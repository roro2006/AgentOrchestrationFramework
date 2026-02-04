# 17Lands Card Synergy Project - Assignment Specification

## Overview

Build a complete C project that computes **card synergy labels** from 17Lands public game data and trains a model to predict synergy between any two Magic: The Gathering cards in the Powered Cube format.

---

## 1. Assignment Specification

### 1.1 Data Inputs and Download URLs

Use **17Lands Public Datasets** (not API scraping). Decompress with `gunzip`.

| Dataset | URL |
|---------|-----|
| Powered Cube PremierDraft game data | `https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.PremierDraft.csv.gz` |
| Powered Cube TradDraft game data | `https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.TradDraft.csv.gz` |
| Card ID mapping | `https://17lands-public.s3.amazonaws.com/analysis_data/cards/cards.csv` |

**Shell commands for data setup:**
```bash
mkdir -p data/raw data/tmp data/out

curl -L -o data/raw/powered_premier_games.csv.gz \
  "https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.PremierDraft.csv.gz"

curl -L -o data/raw/powered_trad_games.csv.gz \
  "https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.TradDraft.csv.gz"

curl -L -o data/raw/cards.csv \
  "https://17lands-public.s3.amazonaws.com/analysis_data/cards/cards.csv"

gunzip -c data/raw/powered_premier_games.csv.gz > data/tmp/powered_premier_games.csv
gunzip -c data/raw/powered_trad_games.csv.gz > data/tmp/powered_trad_games.csv
```

---

### 1.2 Definitions

#### GIH (Games In Hand) Presence Definition

**GIH-style present** = "card was in the kept opening hand OR drawn later in the game"

This is consistent with 17Lands' definition where #GIH counts opening-hand plus drawn-later instances.

#### Synergy Formula

For a card pair (A, B), the **synergy label** is:

```
syn_Δ(A, B) = p₁₁ - p₁₀ - p₀₁ + p₀₀
```

Where:
- `p₁₁ = P(win | A present, B present)`
- `p₁₀ = P(win | A present, B not present)`
- `p₀₁ = P(win | A not present, B present)`
- `p₀₀ = P(win | A not present, B not present)`

#### Four Buckets Computation

Track only these values during streaming:
- **Global counts:** `N, W` (total games, total wins)
- **Per-card present counts:** `N_A, W_A` for each card A
- **Pair both-present counts:** `N_AB, W_AB` for each unordered pair

**Derive remaining buckets algebraically:**
- `N₁₀ = N_A - N_AB`, `W₁₀ = W_A - W_AB`
- `N₀₁ = N_B - N_AB`, `W₀₁ = W_B - W_AB`
- `N₀₀ = N - N_A - N_B + N_AB`, `W₀₀ = W - W_A - W_B + W_AB`

This is valid because the four buckets partition all games under a fixed present/not-present definition.

#### Smoothing and Thresholds

- **Binary per-game presence:** A card is "present" if it appears at least once (keeps bucket algebra consistent)
- **Beta smoothing:** `p̂ = (w + α) / (n + α + β)` where `α = β = 1`
- **Minimum threshold:** Only emit pair labels if `N_AB ≥ MIN_BOTH_PRESENT` (e.g., 500)

---

### 1.3 Repository Structure

```
project/
├── data/
│   ├── raw/          # .gz files + cards.csv mapping
│   ├── tmp/          # decompressed CSVs
│   └── out/          # generated labels and models
├── src/
│   ├── csv.h/.c      # streaming CSV reader
│   ├── hash.h/.c     # open-addressing hash map (uint64 key → struct)
│   ├── cards.h/.c    # loads cards.csv, provides mtga_id ↔ name lookup
│   ├── labels.h/.c   # builds synergy labels from game CSV
│   ├── train.h/.c    # trains model from labels
│   ├── infer.c       # CLI for querying two card names
│   ├── main_labels.c # entry point for label generation
│   └── main_train.c  # entry point for training
└── Makefile
```

---

### 1.4 Program Specifications

#### Program 1: `labels` (build labels.csv)

**Inputs:**
- `data/tmp/powered_premier_games.csv`
- `data/tmp/powered_trad_games.csv`
- `data/raw/cards.csv`

**Outputs:**
- `data/out/labels_premier.csv`
- `data/out/labels_trad.csv`
- Optional: `data/out/labels_both.csv` (with a `format` column)

**Processing per row:**
1. Read `won` field (0 or 1)
2. Parse "opening hand cards" list and "drawn cards" list
3. Union them to form the GIH-present set
4. Update:
   - Global `N, W`
   - For each present card A: `N_A, W_A`
   - For each unordered pair (A,B) in the present set: `N_AB, W_AB`

**Label output schema:**
```
card_a,card_b,n11,w11,p11,n10,w10,p10,n01,w01,p01,n00,w00,p00,syn_delta
```

---

#### Program 2: `train` (learn to predict synergy)

**Model architecture (baseline factorization model):**
- Per-card embedding: `v_i ∈ ℝ^d`
- Per-card bias: `b_i`
- Global bias: `c`

**Prediction formula:**
```
ŝ(A, B) = v_A^T · v_B + b_A + b_B + c
```

**Training:**
1. Read `labels*.csv`
2. Optimize weighted L2-regularized squared error with SGD
3. Weight `ω_AB` based on sample size (e.g., `N_AB` or capped)

**Outputs:**
- `data/out/model_premier.bin`
- `data/out/model_trad.bin`
- Optional: `data/out/model_both.bin`

---

#### Program 3: `infer` (CLI)

**Usage:**
```bash
./infer data/out/model_both.bin "Tinker" "Blightsteel Colossus"
```

**Steps:**
1. Load card name → ID mapping via `cards.csv`
2. Load model from binary file
3. Compute `ŝ(A, B)` using the model
4. Optionally print observed `syn_Δ(A, B)` from labels if available

---

## 2. Definition of Done (DoD) - 100/100 Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | All source files compile with `gcc -std=c11 -Wall -Wextra` with **zero warnings** | `make clean && make 2>&1 \| grep -c warning` returns 0 |
| 2 | `labels` program produces valid CSV output for both Premier and Trad formats | Files exist and pass CSV validation |
| 3 | All bucket counts are non-negative | Assertion/check in code or post-processing validation |
| 4 | Partition identity holds: `N₁₁ + N₁₀ + N₀₁ + N₀₀ = N` for all pairs | Automated consistency check |
| 5 | `train` program produces binary model files | Files exist with non-zero size |
| 6 | `infer` program returns synergy prediction for valid card pairs | Manual test with known combos |
| 7 | Known synergy combos (e.g., Tinker + Blightsteel Colossus) show positive synergy | Spot-check passes |
| 8 | Cross-format validation: model trained on Premier evaluated on Trad (and vice versa) | Correlation or RMSE reported |
| 9 | Streaming CSV processing (no full file load into memory) | Code review confirms line-by-line processing |
| 10 | Hash map handles collisions correctly with open addressing | Unit test or stress test |

---

## 3. Constraints

### Language Requirements
- **Language:** C (C99 or C11 standard)
- **Compiler flags:** Must compile cleanly with `-Wall -Wextra`

### Library Restrictions
- **Allowed:** Standard C library (`libc`) only
- **Forbidden:** No external libraries (no cURL library, no JSON parsers, no SQLite, etc.)
- Data download uses shell `curl` command, not libcurl

### Performance Requirements
- **Streaming processing:** CSV files must be processed line-by-line
- **Memory efficiency:** Do not load entire CSV files into memory
- **Hash map:** Use open-addressing hash map with `uint64` keys

### Data Handling
- Use binary per-game presence (card present = appears at least once)
- Apply Beta smoothing with α = β = 1
- Only emit pairs with `N_AB ≥ 500` (MIN_BOTH_PRESENT threshold)

---

## 4. Required Evidence

### 4.1 Compilation Evidence
```bash
# Must produce zero warnings
make clean
make 2>&1 | tee build.log
grep -c "warning:" build.log  # Must output: 0
```

### 4.2 Test on Sample Data
```bash
# Generate labels
./labels data/tmp/powered_premier_games.csv data/raw/cards.csv data/out/labels_premier.csv

# Train model
./train data/out/labels_premier.csv data/out/model_premier.bin

# Test inference
./infer data/out/model_premier.bin "Tinker" "Blightsteel Colossus"
./infer data/out/model_premier.bin "Black Lotus" "Channel"
./infer data/out/model_premier.bin "Time Walk" "Snapcaster Mage"
```

### 4.3 Bucket Consistency Checks

Implement or run a validation script that verifies for every emitted pair:

```
# Non-negativity
n11 >= 0, n10 >= 0, n01 >= 0, n00 >= 0
w11 >= 0, w10 >= 0, w01 >= 0, w00 >= 0

# Partition identity
n11 + n10 + n01 + n00 == N  (global game count)

# Win rates bounded
0 <= p11 <= 1, 0 <= p10 <= 1, 0 <= p01 <= 1, 0 <= p00 <= 1

# Synergy bounded (theoretical range is [-1, 1] but practically smaller)
-1 <= syn_delta <= 1
```

### 4.4 Spot-Check Known Combos

These Powered Cube combos should show **positive synergy**:
- Tinker + Blightsteel Colossus
- Tinker + Mana Crypt
- Channel + Emrakul, the Aeons Torn
- Black Lotus + Any expensive spell
- Sneak Attack + Emrakul, the Aeons Torn

---

## 5. Rubric Mapping (R1-R8)

| Requirement | Description | Points | Criteria |
|-------------|-------------|--------|----------|
| **R1** | **Data Infrastructure** | 10 | Correct directory structure, CSV streaming reader, hash map implementation |
| **R2** | **Card Mapping** | 10 | `cards.c` correctly loads cards.csv, bidirectional mtga_id ↔ name lookup works |
| **R3** | **GIH Presence Logic** | 15 | Correctly parses opening hand + drawn cards, forms union, binary presence |
| **R4** | **Bucket Computation** | 20 | All four buckets computed correctly via algebraic derivation, partition identity holds |
| **R5** | **Label Generation** | 15 | `labels` program outputs valid CSV with correct schema, Beta smoothing applied, threshold enforced |
| **R6** | **Model Training** | 15 | `train` program implements SGD with L2 regularization, weighted by sample size, outputs binary model |
| **R7** | **Inference CLI** | 10 | `infer` program loads model, resolves card names, computes and displays prediction |
| **R8** | **Validation & Quality** | 5 | Zero compiler warnings, bucket consistency verified, spot-checks pass |

**Total: 100 points**

---

## 6. Detailed File Specifications

### 6.1 Input: Game Data CSV Columns (Expected)

The game data CSV contains (among others):
- `won`: 0 or 1 indicating game outcome
- `opening_hand`: List of card IDs in opening hand
- `drawn`: List of card IDs drawn during game

Note: Exact column names should be verified from actual CSV headers.

### 6.2 Input: cards.csv Schema

```
id,name,set,...
<mtga_id>,<card_name>,<set_code>,...
```

### 6.3 Output: labels_*.csv Schema

```csv
card_a,card_b,n11,w11,p11,n10,w10,p10,n01,w01,p01,n00,w00,p00,syn_delta
12345,67890,1500,825,0.5433,3200,1600,0.4938,2800,1344,0.4743,45000,22050,0.4878,0.0654
```

### 6.4 Output: model_*.bin Schema (Suggested)

Binary format containing:
```
Header:
  - magic number (4 bytes)
  - version (4 bytes)
  - embedding dimension d (4 bytes)
  - number of cards (4 bytes)

Per card (repeated):
  - card_id (8 bytes, uint64)
  - bias b_i (4 bytes, float)
  - embedding v_i (d * 4 bytes, float array)

Footer:
  - global bias c (4 bytes, float)
```

---

## 7. Compliance and Data Hygiene

1. **Use public dumps only** - 17Lands prefers public dataset use over API scraping
2. **Cache locally** - Store downloaded .gz files in `data/raw/`
3. **Record metadata** - Note dataset "last updated" timestamp from 17Lands public datasets page
4. **No redistribution** - Do not redistribute the downloaded data

---

## 8. Suggested Implementation Order

1. `csv.c` - Streaming CSV parser
2. `hash.c` - Open-addressing hash map
3. `cards.c` - Card ID/name mapping
4. `labels.c` + `main_labels.c` - Label generation
5. `train.c` + `main_train.c` - Model training
6. `infer.c` - Inference CLI
7. Validation and testing

---

## 9. References

- [Interaction Effects - Statistics How To](https://www.statisticshowto.com/interaction-effect-interacting-variable/)
- [Interaction Effects - Statistics by Jim](https://statisticsbyjim.com/regression/interaction-effects/)
- [Statistical Interaction - Statistics Solutions](https://www.statisticssolutions.com/statistical-interaction-more-than-the-sum-of-its-parts/)
- [17Lands Public Data](https://www.17lands.com/public_datasets)
