import os, re, shutil, sys, subprocess
from itertools import combinations
from difflib import SequenceMatcher
from dotenv import load_dotenv
from clone import clone_repo, get_all_repos, has_branch
from datetime import datetime
from pprint import pprint
from collections import Counter

from utils.utils import check_folders, check_prettier

# List of files to be ignored
ignored_folders = ["node_modules", ".*"]
# Files to check
file_exts = ["py"]
threshold = 0.7

files_by_ext = {ext: [] for ext in file_exts}

data = []

load_dotenv()

ORG = os.getenv("ORG")
SUBSTR = os.getenv("SUBSTR")
BRANCH = os.getenv("BRANCH")
REPORT_DIR = os.getenv("REPORT_DIR")
TOKEN = os.getenv("GITHUB_TOKEN")
DEST_DIR = f"clones/{ORG}-{SUBSTR}"


########################
# Full file comparison #
########################
def group_similar_files(file_list, threshold=0.5):
    groups = {}  # key: representative file, value: list of (percent, file)

    for file in file_list:
        with open(file, encoding="utf-8", errors="ignore") as f:
            current_content = f.read()

        found_group = False

        for rep_file, group_entries in groups.items():
            with open(rep_file, encoding="utf-8", errors="ignore") as rf:
                rep_content = rf.read()

            ratio = SequenceMatcher(None, current_content, rep_content).ratio()

            if ratio >= threshold:
                percent = f"{ratio * 100:.0f}%"
                group_entries.append((percent, file))
                found_group = True
                break

        if not found_group:
            # Don't create a group unless a similar file is found later
            groups[file] = []

    # Filter: only return groups that have at least one similar file
    result = {rep: entries for rep, entries in groups.items() if len(entries) > 0}

    return result


####################
# Lines comparison #
####################

# def group_similar_files(file_list, threshold=0.5):
#     def multiset_line_similarity(lines1, lines2):
#         counter1 = Counter(lines1)
#         counter2 = Counter(lines2)
#         intersection = sum((counter1 & counter2).values())
#         union = sum((counter1 | counter2).values())
#         return intersection / union if union > 0 else 1.0

#     groups = {}

#     for file in file_list:
#         with open(file, encoding="utf-8", errors="ignore") as f:
#             lines1 = [line.strip() for line in f if line.strip()]

#         found_group = False

#         for rep_file, group_entries in groups.items():
#             with open(rep_file, encoding="utf-8", errors="ignore") as rf:
#                 lines2 = [line.strip() for line in rf if line.strip()]

#             ratio = multiset_line_similarity(lines1, lines2)

#             if ratio >= threshold:
#                 percent = f"{ratio * 100:.0f}%"
#                 group_entries.append((percent, file))
#                 found_group = True
#                 break

#         if not found_group:
#             groups[file] = []

#     return {rep: entries for rep, entries in groups.items() if entries}


def main():
    check_prettier()

    check_folders([REPORT_DIR, DEST_DIR])

    # # 1) Fetch & filter repo names
    all_repos = get_all_repos(ORG, TOKEN)
    targets = [r["name"] for r in all_repos if SUBSTR.lower() in r["name"].lower()]

    # # 2) Clone each wip branch
    # for name in targets:
    #     if has_branch(ORG, name, BRANCH, TOKEN):
    #         clone_repo(ORG, name, BRANCH, DEST_DIR)
    #     else:
    #         print(f"skip {name}: no {BRANCH}")

    # Search for folders
    with os.scandir(DEST_DIR) as entries:
        for entry in entries:
            if entry.is_dir():
                # Get last commit timestamp for the folder
                try:
                    result = subprocess.run(
                        [
                            "git",
                            "-C",
                            entry.path,
                            "log",
                            "-1",
                            "--format=%ct",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    timestamp = int(result.stdout.strip())
                    last_commit = datetime.fromtimestamp(timestamp)
                except subprocess.CalledProcessError:
                    last_commit = None

                data.append(
                    {
                        "folder": entry,
                        "surname": entry.name.split("-")[-1],
                        "last_commit": last_commit,
                    }
                )

    data.sort(key=lambda x: x["last_commit"])

    # Search for files
    for entry in data:
        files = os.scandir(entry["folder"].path)
        for root, dirs, files in os.walk(entry["folder"]):
            dirs[:] = [
                d for d in dirs if not re.search(r"node_modules|^\.", d, re.IGNORECASE)
            ]

            for file in files:
                ext = file.split(".")[-1]
                if ext in file_exts:
                    file_name = os.path.join(root, file)
                    if not re.search(r"normalize|reset|root", file_name):
                        files_by_ext[ext].append(file_name)

    # Prettify to avoid format cheating
    # for ext in file_exts:
    #     for path in files_by_ext[ext]:
    #         subprocess.run(
    #             ["prettier", "--write", path],
    #             stdout=subprocess.DEVNULL,
    #         )

    similar_groups = {}
    for ext in file_exts:
        similar_groups[ext] = group_similar_files(files_by_ext[ext], threshold)

    pprint(similar_groups)


if __name__ == "__main__":
    main()
