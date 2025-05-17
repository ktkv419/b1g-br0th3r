import os, re, shutil, sys, subprocess
from pathlib import Path
from itertools import combinations
from pprint import pprint
from difflib import SequenceMatcher


if not shutil.which("prettier"):
    print("Prettier is NOT installed")
    sys.exit(1)

basepath = "./test-data"
ignored_folders = ["node_modules", ".*"]
file_exts = ["css", "js", "html"]
files_by_ext = {ext: [] for ext in ["html", "js", "css"]}

data = []

# Scanning repos
with os.scandir(basepath) as entries:
    for entry in entries:
        with os.scandir(entry.path) as files:
            data.append({"folder": entry, "surname": entry.name.split("-")[-1]})

# Scanning files
for entry in data:
    files = os.scandir(entry["folder"].path)
    entry["files"] = {ext: [] for ext in ["html", "js", "css"]}
    for root, dirs, files in os.walk(entry["folder"]):
        dirs[:] = [
            d for d in dirs if not re.search(r"node_modules|^\.", d, re.IGNORECASE)
        ]

        for file in files:
            ext = file.split(".")[-1]
            if ext in file_exts:
                entry["files"][ext].append(os.path.join(root, file))
                files_by_ext[ext].append(os.path.join(root, file))

# Prettify to avoid format cheating
for ext in ["html", "css", "js"]:
    for path in files_by_ext[ext]:
        subprocess.run(
            ["prettier", "--write", path],
            stdout=subprocess.DEVNULL,
        )


def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def group_similar_files(file_list, threshold=0.5):
    """
    Compare each pair of files in file_list and return a list of
    (ratio, [file1, file2]) for those whose similarity >= threshold.

    `ratio` is a float in [0,1], so threshold=0.5 means 50%.
    """
    groups = []

    for f1, f2 in combinations(file_list, 2):
        # Read both files
        with open(f1, encoding="utf-8", errors="ignore") as a, open(
            f2, encoding="utf-8", errors="ignore"
        ) as b:
            txt1, txt2 = a.read(), b.read()

        # Compute similarity ratio
        ratio = SequenceMatcher(None, txt1, txt2).ratio()

        # Keep only those above threshold
        if ratio >= threshold:
            groups.append((ratio, [f1, f2]))

    # Sort descending by ratio
    groups.sort(key=lambda x: x[0], reverse=True)
    return groups


similar_groups = group_similar_files(files_by_ext["css"], threshold=0.5)

for ratio, pair in similar_groups:
    # ratio*100 → percentage, and .0f to round to nearest integer
    print(f"{ratio * 100:.0f}% {pair}")
