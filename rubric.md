# Rubric v1.1 - 17Lands Card Synergy Project

## Changelog
- **v1.1**: Customized for C synergy project (GIH, curl+gunzip, Premier+Trad)
- **v1.0**: Baseline rubric established

---

## Scoring Model
- **Mastery grading**: Each criterion is PASS (full points) or FAIL (0 points)
- **Blocking rule**: Any FAIL on criteria 1-4 caps total score at ≤79
- **100/100 requires**: ALL criteria PASS with evidence

---

## Criteria

| ID | Criterion | Weight | Evidence Required | Pass Condition |
|----|-----------|--------|-------------------|----------------|
| R1 | **Requirements Coverage** | 20 | All 7 components implemented | csv.h/c, hash.h/c, cards.h/c, labels.h/c, train.h/c, infer.c, Makefile all present and functional |
| R2 | **Correctness** | 25 | Test output, bucket math verification | Labels compute correctly; syn_delta formula matches spec; bucket identities hold (N_A - N_AB >= 0, etc.) |
| R3 | **Reliability** | 15 | Error handling tests | Handles missing files, malformed CSV, empty data gracefully; no crashes or memory leaks |
| R4 | **Performance** | 10 | Benchmark on full dataset | Processes 100k+ games in reasonable time; streaming CSV (not loading all to memory) |
| R5 | **Code Quality** | 10 | Compiles with -Wall -Wextra, no warnings | Clean build; consistent style; no undefined behavior |
| R6 | **Documentation** | 10 | README with usage | Build instructions, data download commands, CLI usage examples |
| R7 | **Reproducibility** | 5 | Single make command | `make && ./main_labels && ./main_train && ./infer model.bin "Card1" "Card2"` works |
| R8 | **Safety/Compliance** | 5 | Uses public dataset URLs | No API scraping; uses 17lands public S3 URLs; no hardcoded secrets |

---

## Project-Specific Requirements (R1 Detail)

### Data Pipeline
- [ ] Download script/commands for .gz files
- [ ] gunzip decompression
- [ ] cards.csv loaded for name↔ID mapping

### Labels Program (labels.h/c, main_labels.c)
- [ ] Reads game CSV row by row (streaming)
- [ ] Computes N, W (global games/wins)
- [ ] Computes N_A, W_A per card (present counts)
- [ ] Computes N_AB, W_AB per pair (both present)
- [ ] Derives N_10, N_01, N_00 buckets correctly
- [ ] Applies beta smoothing (α=β=1)
- [ ] Filters pairs with MIN_BOTH_PRESENT >= 500
- [ ] Outputs CSV: card_a,card_b,n11,w11,p11,...,syn_delta

### Train Program (train.h/c, main_train.c)
- [ ] Per-card embedding v_i ∈ R^d
- [ ] Per-card bias b_i
- [ ] Global bias c
- [ ] Prediction: ŝ(A,B) = v_A·v_B + b_A + b_B + c
- [ ] SGD with L2 regularization
- [ ] Sample weighting by N_AB
- [ ] Outputs binary model file

### Infer Program (infer.c)
- [ ] CLI: `./infer model.bin "Card1" "Card2"`
- [ ] Name→ID lookup via cards.csv
- [ ] Computes ŝ(A,B)
- [ ] Optionally prints observed syn_delta

### Support Modules
- [ ] csv.h/c: streaming CSV parser
- [ ] hash.h/c: open-addressing hash map (uint64→struct)
- [ ] cards.h/c: loads cards.csv, provides lookups

---

## Blocking Criteria (score capped at 79 if ANY fail)
- R1: Requirements Coverage
- R2: Correctness
- R3: Reliability
- R4: Performance

## Total: 100 points
