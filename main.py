import os, re, difflib, shutil, sys, subprocess
from pathlib import Path
from itertools import combinations
from pprint import pprint


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


def group_similar_files(file_list, threshold=0.8):
    groups = []

    for file1, file2 in combinations(file_list, 2):
        text1 = read_file(file1)
        text2 = read_file(file2)

        ratio = difflib.SequenceMatcher(None, text1, text2).ratio()

        if ratio >= threshold:
            for group in groups:
                if file1 in group or file2 in group:
                    group.update([file1, file2])
                    break
            else:
                groups.append(set([file1, file2]))

    return groups


similar_groups = group_similar_files(files_by_ext["css"])

for i, group in enumerate(similar_groups, 1):
    print(f"Group {i}: {group}")

pprint(data)