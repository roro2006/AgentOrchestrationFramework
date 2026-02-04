---
description: Show current RPI loop status
---

# Show Status

Display the current state of the RPI development loop.

## Gather Information

```bash
# Current story from PROJECT_STATUS.md
cat PROJECT_STATUS.md | head -20

# List research documents
ls -la research/ 2>/dev/null || echo "No research yet"

# List plans
ls -la plans/ 2>/dev/null || echo "No plans yet"

# List submissions
ls -la submission/ 2>/dev/null || echo "No submissions yet"

# List gradings
ls -la grading/ 2>/dev/null || echo "No gradings yet"

# Check state file
cat state/rpi_state.json 2>/dev/null || echo "No state file"
```

## Display Status

```markdown
## RPI Loop Status

### Current Story
- **ID:** US-X
- **Name:** [Story name]
- **Status:** [From PROJECT_STATUS.md]

### Phase Progress
| Phase | Artifact | Status |
|-------|----------|--------|
| Research | `research/US-X_research.md` | [EXISTS/MISSING] |
| Plan | `plans/US-X_plan.md` | [EXISTS/MISSING] |
| Implement | `submission/V{n}/` | [EXISTS/MISSING] |
| Grade | `grading/V{n}.md` | [EXISTS/MISSING] |

### Latest Grading
- **Version:** V{n}
- **Score:** XX/100
- **Blocking Issues:** [List or "None"]

### Iteration History
| Version | Score | Result |
|---------|-------|--------|
| V1 | XX | [PASS/FAIL] |
| V2 | XX | [PASS/FAIL] |

### Next Action
[Based on current state, recommend next command]
- If no research: `/research`
- If research but no plan: `/plan`
- If plan but no submission: `/implement`
- If submission but no grading: `/grade`
- If grading < 100: `/research` (retry with grading feedback)
- If grading = 100: Move to next story
```

## Quick Commands

Based on status, suggest:
```
Next step: /[command]
```
