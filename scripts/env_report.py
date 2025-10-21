#!/usr/bin/env python3
import sys, json, os
from importlib import metadata

packages = sorted([(d.metadata['Name'], d.version) for d in metadata.distributions()])
lines = [f"{name}=={ver}" for name, ver in packages]
report = "\n".join(lines)

print("Installed packages:")
print(report)

with open("env_report.txt", "w", encoding="utf-8") as f:
    f.write(report + "\n")

print("\nWrote env_report.txt")
