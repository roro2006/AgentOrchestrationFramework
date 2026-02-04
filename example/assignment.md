# TEACHER: Assignment Specification

## Task
Create a Python function that checks if a string is a valid palindrome, ignoring case and non-alphanumeric characters.

---

## Assignment Specification

### Requirements
Implement `is_palindrome(s: str) -> bool` that:
1. Returns `True` if the input is a palindrome
2. Returns `False` otherwise
3. Ignores case (e.g., "RaceCar" is a palindrome)
4. Ignores non-alphanumeric characters (e.g., "A man, a plan, a canal: Panama" is a palindrome)
5. Empty string returns `True`

### Constraints
- Language: Python 3.8+
- No external dependencies
- Single file implementation
- Time complexity: O(n)
- Space complexity: O(n) maximum

---

## Definition of Done (DoD)

- [ ] Function signature matches spec
- [ ] All 8 provided test cases pass
- [ ] Edge cases handled (empty, single char, all non-alpha)
- [ ] Performance verified with benchmark
- [ ] Code passes linter with no warnings
- [ ] Docstring documents behavior

---

## Required Evidence

| Rubric | Evidence Type |
|--------|---------------|
| R1 | Feature checklist with code references |
| R2 | Test output showing all cases pass |
| R3 | Error handling for None/non-string inputs |
| R4 | Complexity analysis + timing benchmark |
| R5 | Linter output (pylint or flake8) |
| R6 | Docstring in function |
| R7 | Single command to run tests |
| R8 | No hardcoded paths or secrets |

---

## Test Cases (STUDENT must pass ALL)

```python
# Basic cases
assert is_palindrome("racecar") == True
assert is_palindrome("hello") == False

# Case insensitivity
assert is_palindrome("RaceCar") == True

# Ignore non-alphanumeric
assert is_palindrome("A man, a plan, a canal: Panama") == True
assert is_palindrome("race a car") == False

# Edge cases
assert is_palindrome("") == True
assert is_palindrome("a") == True
assert is_palindrome(".,!") == True  # All non-alpha = empty = palindrome
```

---

## Rubric Weights (Confirmed)

| ID | Criterion | Weight | Blocking |
|----|-----------|--------|----------|
| R1 | Requirements Coverage | 20 | Yes |
| R2 | Correctness | 25 | Yes |
| R3 | Reliability | 15 | Yes |
| R4 | Performance | 10 | Yes |
| R5 | Code Quality | 10 | No |
| R6 | Documentation | 10 | No |
| R7 | Reproducibility | 5 | No |
| R8 | Safety/Compliance | 5 | No |

---

**TEACHER NOTE:** STUDENT should now create V1 submission in `submission/V1/`
