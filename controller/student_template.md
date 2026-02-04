# STUDENT Submission Template

---

## Header (Required)

```markdown
# Submission: {TITLE}
**Version:** V{n}
**Date:** {YYYY-MM-DD}
**Previous Version:** V{n-1} (or "N/A" for V1)
```

---

## Goal Statement (1-2 sentences)
What this submission accomplishes.

---

## Deliverables List

| File/Component | Description | Location |
|----------------|-------------|----------|
| {file.py} | {What it does} | submission/V{n}/{path} |

---

## Claims List
What this work accomplishes (map to rubric criteria):

- [ ] **R1**: {Claim about requirements coverage}
- [ ] **R2**: {Claim about correctness}
- [ ] **R3**: {Claim about reliability}
- [ ] **R4**: {Claim about performance}
- [ ] **R5**: {Claim about code quality}
- [ ] **R6**: {Claim about documentation}
- [ ] **R7**: {Claim about reproducibility}
- [ ] **R8**: {Claim about safety/compliance}

---

## Evidence Section

### Tests Run
```
{Command and output}
```

### Sample Inputs/Outputs
```
Input: {example}
Output: {example}
```

### Benchmarks/Complexity
- Time complexity: O({...})
- Space complexity: O({...})
- Benchmark: {results}

### Build/Lint Output
```
{Build output showing no errors/warnings}
```

---

## Known Limitations
1. {Limitation 1 - be honest}
2. {Limitation 2}

---

## How to Reproduce

```bash
# Step 1: {Setup}
# Step 2: {Run}
# Step 3: {Verify}
```

---

## Changes Since V{n-1} (Required for V2+)

### Diff Summary
| Rubric Item | Issue Fixed | Change Made |
|-------------|-------------|-------------|
| R{x} | {What was wrong} | {What changed} |

### New Evidence Added
- {Description of new test/benchmark/proof}

---

## Self-Grade (Optional but Encouraged)

| Criterion | Self-Assessment | Confidence |
|-----------|-----------------|------------|
| R1 | PASS/FAIL | High/Medium/Low |
| R2 | PASS/FAIL | High/Medium/Low |
| ... | ... | ... |

---

## Questions (Only if Absolutely Blocking)
1. {Question that cannot be resolved with reasonable defaults}
