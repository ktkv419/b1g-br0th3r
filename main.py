import os, re, shutil, sys
from pathlib import Path
from itertools import combinations
from difflib import SequenceMatcher
from dotenv import load_dotenv
from clone import clone_repo, get_all_repos, has_branch

load_dotenv()

ORG = os.getenv("ORG")
SUBSTR = os.getenv("SUBSTR")
BRANCH = os.getenv("BRANCH")
TOKEN = os.getenv("GITHUB_TOKEN")
DEST_DIR = f"clones/{ORG}-{SUBSTR}"

if not shutil.which("prettier"):
    print("Prettier is NOT installed")
    sys.exit(1)

ignored_folders = ["node_modules", ".*"]
file_exts = ["py"]
files_by_ext = {ext: [] for ext in file_exts}

data = []

if not (os.path.isdir(DEST_DIR)):
    os.makedirs(DEST_DIR)

# Scanning repos
with os.scandir(DEST_DIR) as entries:
    for entry in entries:
        with os.scandir(entry.path) as files:
            data.append({"folder": entry, "surname": entry.name.split("-")[-1]})

# Scanning files
for entry in data:
    files = os.scandir(entry["folder"].path)
    entry["files"] = {ext: [] for ext in file_exts}
    for root, dirs, files in os.walk(entry["folder"]):
        dirs[:] = [
            d for d in dirs if not re.search(r"node_modules|^\.", d, re.IGNORECASE)
        ]

        for file in files:
            ext = file.split(".")[-1]
            if ext in file_exts:
                file_name = os.path.join(root, file)
                if not re.search(r"normalize|reset|root", file_name):
                    entry["files"][ext].append(file_name)
                    files_by_ext[ext].append(file_name)

# Prettify to avoid format cheating
# for ext in ["html", "css", "js"]:
#     for path in files_by_ext[ext]:
#         subprocess.run(
#             ["prettier", "--write", path],
#             stdout=subprocess.DEVNULL,
#         )


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


# 1) Fetch & filter repo names
all_repos = get_all_repos(ORG, TOKEN)
targets = [r["name"] for r in all_repos if SUBSTR.lower() in r["name"].lower()]

# 2) Clone each wip branch
os.makedirs(DEST_DIR, exist_ok=True)
for name in targets:
    if has_branch(ORG, name, BRANCH, TOKEN):
        clone_repo(ORG, name, BRANCH, DEST_DIR)
    else:
        print(f"skip {name}: no {BRANCH}")


similar_groups = group_similar_files(files_by_ext["py"], threshold=0.5)

for ratio, pair in similar_groups:
    # ratio*100 → percentage, and .0f to round to nearest integer
    print(f"{ratio * 100:.0f}% {pair}")
