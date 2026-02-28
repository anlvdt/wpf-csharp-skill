#!/usr/bin/env python3
"""Validate WPF C# skill structure — checks SKILL.md frontmatter, reference files, and code blocks."""

import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")

REQUIRED_FILES = [
    "mvvm-patterns.md",
    "xaml-best-practices.md",
    "async-patterns.md",
    "wmi-hardware.md",
    "hardware-testing.md",
    "testing-patterns.md",
    "di-architecture.md",
    "error-handling.md",
    "localization.md",
    "performance.md",
]

REQUIRED_KEYWORDS = ["WPF", "XAML", "WMI", "MVVM"]

failures = []

def check(condition, message):
    status = "✓" if condition else "✗"
    print(f"  [{status}] {message}")
    if not condition:
        failures.append(message)
    return condition


# ── 1. SKILL.md exists ──────────────────────────────────────────────────────
print("\n── SKILL.md Frontmatter ──")
if not os.path.exists(SKILL_MD):
    print(f"  [✗] SKILL.md not found at {SKILL_MD}")
    sys.exit(1)

with open(SKILL_MD, encoding="utf-8") as f:
    content = f.read()

# Parse YAML frontmatter between --- delimiters
fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
if not fm_match:
    check(False, "SKILL.md has valid YAML frontmatter (--- delimiters)")
    sys.exit(1)

frontmatter = fm_match.group(1)

# Check name field
name_match = re.search(r'^name:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
name_value = name_match.group(1).strip() if name_match else ""
check(name_value == "wpf-csharp", f'name = "wpf-csharp" (got: "{name_value}")')

# Check description non-empty
desc_match = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
desc_value = desc_match.group(1).strip() if desc_match else ""
check(bool(desc_value), "description is non-empty")

# Check trigger keywords in description
for kw in REQUIRED_KEYWORDS:
    check(kw in content, f'Trigger keyword "{kw}" present in SKILL.md')


# ── 2. Reference files exist ─────────────────────────────────────────────────
print("\n── Reference File Existence ──")
for filename in REQUIRED_FILES:
    filepath = os.path.join(SKILL_DIR, filename)
    check(os.path.exists(filepath), f"{filename} exists")


# ── 3. Each reference file has at least 1 code block ─────────────────────────
print("\n── Code Block Coverage ──")
CODE_BLOCK_RE = re.compile(r"```(csharp|xml|python|bash|powershell)", re.IGNORECASE)

for filename in REQUIRED_FILES:
    filepath = os.path.join(SKILL_DIR, filename)
    if not os.path.exists(filepath):
        check(False, f"{filename} has at least 1 code block (file missing)")
        continue
    with open(filepath, encoding="utf-8") as f:
        file_content = f.read()
    has_code = bool(CODE_BLOCK_RE.search(file_content))
    check(has_code, f"{filename} has at least 1 fenced code block with language tag")


# ── Summary ───────────────────────────────────────────────────────────────────
total = len(REQUIRED_FILES) * 2 + len(REQUIRED_KEYWORDS) + 3  # approx
print(f"\n── Result: {len(failures)} failure(s) ──")
if failures:
    print("\nFailed checks:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed ✓")
    sys.exit(0)
