# Project Prompt: 17Lands Card Synergy Analyzer

## Overview

Build a C program that analyzes Magic: The Gathering draft game data from 17Lands to compute card synergy scores and train a predictive model.

---

## 1. Data Inputs and Downloads

Use 17Lands Public Datasets (not API scraping) and decompress with gunzip.

### Download URLs
- **Powered Cube PremierDraft**: `https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.PremierDraft.csv.gz`
- **Powered Cube TradDraft**: `https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.TradDraft.csv.gz`
- **Card ID mapping**: `https://17lands-public.s3.amazonaws.com/analysis_data/cards/cards.csv`

### Shell Commands
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

## 2. Definitions (GIH and Four Buckets)

### Presence Definition
**GIH-style present** = "card was in the kept opening hand OR drawn later in the game"

This is consistent with 17Lands' definition that #GIH counts opening-hand plus drawn-later instances.

### Synergy Label Formula
For a card pair (A, B):

```
syn_Δ(A, B) = p11 - p10 - p01 + p00
```

Where:
- `p11 = P(win | A present, B present)`
- `p10 = P(win | A present, B not present)`
- `p01 = P(win | A not present, B present)`
- `p00 = P(win | A not present, B not present)`

---

## 3. Compute All Buckets Without "Missing Pair" Iteration

Track only:
- **Global counts**: N, W (total games, total wins)
- **Per-card present counts**: N_A, W_A
- **Pair both-present counts**: N_AB, W_AB

Derive remaining buckets:
- `N_10 = N_A - N_AB`, `W_10 = W_A - W_AB`
- `N_01 = N_B - N_AB`, `W_01 = W_B - W_AB`
- `N_00 = N - N_A - N_B + N_AB`, `W_00 = W - W_A - W_B + W_AB`

This is valid because the four buckets partition games under a fixed present/not-present definition.

---

## 4. Repository Structure

```
data/
  raw/           # gz files + cards mapping
  tmp/           # decompressed CSVs
  out/           # generated labels/models

src/
  csv.h/.c       # streaming CSV reader
  hash.h/.c      # open-addressing hash map (uint64 key → struct)
  cards.h/.c     # loads cards.csv and provides mtga_id ↔ name
  labels.h/.c    # builds synergy labels from game CSV
  train.h/.c     # trains model from labels
  infer.c        # CLI for querying two card names
  main_labels.c
  main_train.c

Makefile
```

---

## 5. Program: labels (build labels.csv)

### Inputs
- `data/tmp/powered_premier_games.csv`
- `data/tmp/powered_trad_games.csv`
- `data/raw/cards.csv`

### Outputs
- `data/out/labels_premier.csv`
- `data/out/labels_trad.csv`
- Optional: `data/out/labels_both.csv` with a format column

### Per Row Processing
1. Read `won` (0/1)
2. Parse "opening hand cards" list and "drawn cards" list
3. Union them to form GIH-present set
4. Update:
   - Global N, W
   - For each present card A: N_A, W_A
   - For each unordered pair in the present set: N_AB, W_AB

### Smoothing + Thresholds
- Use binary per-game presence (present at least once)
- Beta smoothing: `p̂ = (w + α) / (n + α + β)` (start α = β = 1)
- Emit pair labels only if `N_AB >= MIN_BOTH_PRESENT` (e.g., 500)

### Label Output Schema
```
card_a,card_b,n11,w11,p11,n10,w10,p10,n01,w01,p01,n00,w00,p00,syn_delta
```

---

## 6. Program: train (learn to predict synergy)

### Baseline Model
Per-card embedding `v_i ∈ R^d`, per-card bias `b_i`, global bias `c`

**Prediction**: `ŝ(A, B) = v_A^T · v_B + b_A + b_B + c`

### Training
- Read `labels*.csv`
- Optimize weighted L2-regularized squared error with SGD
- Weight `ω_AB` based on sample size (e.g., N_AB or capped)

### Outputs
- `data/out/model_premier.bin`
- `data/out/model_trad.bin`
- Optional: `data/out/model_both.bin`

---

## 7. Program: infer (CLI)

### Usage
```bash
./infer data/out/model_both.bin "Tinker" "Blightsteel Colossus"
```

### Steps
1. Name → ID via cards.csv
2. Compute `ŝ(A, B)`
3. Optionally also print observed `syn_Δ(A, B)` from labels if available

---

## 8. Validation Checklist

- [ ] **Bucket consistency**: Derived counts non-negative; totals match partition identities
- [ ] **Spot-check**: Known cube combos should skew positive (e.g., Tinker + artifact)
- [ ] **Cross-format stability**: Train on Premier, evaluate on Trad (and vice versa)

---

## 9. Compliance / Data Hygiene

- Use 17Lands public dumps; they prefer public dataset use over scraping
- Cache raw downloads locally
- Record dataset "last updated" metadata from the public datasets page

---

## User Stories

### US-1: Data Download & Decompression
- Download all three data files
- Decompress to tmp/
- Verify files exist and have content

### US-2: Card Database Loading
- Parse cards.csv
- Build name ↔ ID lookup
- Verify can look up "Black Lotus", "Tinker", etc.

### US-3: CSV Streaming Parser
- Parse game CSV row by row
- Extract: won, opening_hand, drawn columns
- Handle quoted fields with commas

### US-4: Label Generation - Card Tracking
- For each game, identify present cards (opening_hand ∪ drawn)
- Update per-card counts (N_A, W_A)
- Verify "Unique cards tracked" > 0

### US-5: Label Generation - Pair Tracking
- For each game, enumerate all pairs of present cards
- Update pair counts (N_AB, W_AB)
- Verify "Card pairs tracked" > 0

### US-6: Label Generation - Output
- Compute derived buckets (N_10, N_01, N_00, etc.)
- Apply beta smoothing
- Filter by MIN_BOTH_PRESENT threshold
- Write labels.csv with all columns

### US-7: Model Training
- Load labels.csv
- Initialize embeddings randomly
- Run SGD for N epochs
- Save binary model file

### US-8: Inference CLI
- Load model and cards database
- Accept two card names as arguments
- Output predicted synergy score

### US-9: End-to-End Validation
- Run full pipeline
- Verify known combos have positive synergy
- Cross-validate between Premier and Trad

---

## Acceptance Criteria

The project is **COMPLETE** when:
1. `make download-data` fetches all files
2. `make run-all` produces non-empty labels and models
3. `./infer model.bin cards.csv "Card1" "Card2"` outputs a score
4. Known synergistic pairs (Tinker+artifact, Channel+Fireball) show positive scores
5. Code compiles with no warnings under `-Wall -Wextra`
