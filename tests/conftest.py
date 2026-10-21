# Copyright (c) 2026 Muhammad Hassan. MIT License.
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
for name in sorted(os.listdir(SKILLS)):
    path = os.path.join(SKILLS, name)
    if os.path.isdir(path):
        sys.path.insert(0, path)

sys.path.insert(0, os.path.join(ROOT, "tools"))
FIX = os.path.join(ROOT, "tests", "fixtures")


def fixture(name):
    return os.path.join(FIX, name)
