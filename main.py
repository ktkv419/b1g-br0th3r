import os, re, shutil, sys, subprocess
from itertools import combinations
from difflib import SequenceMatcher
from dotenv import load_dotenv
from clone import clone_repo, get_all_repos, has_branch
from datetime import datetime
from pprint import pprint

from utils.utils import check_folders, check_prettier

# List of files to be ignored
ignored_folders = ["node_modules", ".*"]
# Files to check
file_exts = ["css", "js", "html"]
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


def group_similar_files(file_list, threshold=0.5):
    """
    Compare each pair of files in file_list and return a list of
    (ratio, [file1, file2]) for those whose similarity >= threshold.

    `ratio` is a float in [0,1], so threshold=0.5 means 50%.
    """
    groups = {}

    for file in file_list:
        with open(file, encoding="utf-8", errors="ignore") as a:
            highest_group = None
            for group in dict.keys(groups):
                with open(group, encoding="utf-8", errors="ignore") as b:
                    txt1, txt2 = a.read(), b.read()

                ratio = SequenceMatcher(None, txt1, txt2).ratio()

                if ratio >= threshold:
                    groups[group].append((f"{ratio * 100:.0f}%", file))
                else:
                    groups[file] = []

        # # Read both files
        # with open(f1, encoding="utf-8", errors="ignore") as a, open(
        #     f2, encoding="utf-8", errors="ignore"
        # ) as b:
        #     txt1, txt2 = a.read(), b.read()

        # # Compute similarity ratio
        # ratio = SequenceMatcher(None, txt1, txt2).ratio()

        # # Keep only those above threshold
        # if ratio >= threshold:
        #     if dict.keys(groups).__contains__(f1):
        #         groups[f1].append((f"{ratio * 100:.0f}%", f2))
        #     else:
        #         groups[f1] = [(f"{ratio * 100:.0f}%", f2)]

    # Sort descending by ratio
    # groups.sort(key=lambda x: x[0], reverse=True)
    return {k: v for k, v in groups.items() if v}


def main():
    check_prettier()

    check_folders([REPORT_DIR, DEST_DIR])

    # # 1) Fetch & filter repo names
    # all_repos = get_all_repos(ORG, TOKEN)
    # targets = [r["name"] for r in all_repos if SUBSTR.lower() in r["name"].lower()]

    # # 2) Clone each wip branch
    # for name in targets:
    #     if has_branch(ORG, name, BRANCH, TOKEN):
    #         clone_repo(ORG, name, BRANCH, DEST_DIR)
    #     else:
    #         print(f"skip {name}: no {BRANCH}")

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
                    file_name = os.path.join(root, file)
                    if not re.search(r"normalize|reset|root", file_name):
                        entry["files"][ext].append(file_name)
                        files_by_ext[ext].append(file_name)

    # Prettify to avoid format cheating
    for ext in ["html", "css", "js"]:
        for path in files_by_ext[ext]:
            subprocess.run(
                ["prettier", "--write", path],
                stdout=subprocess.DEVNULL,
            )

    similar_groups = {}
    for ext in file_exts:
        similar_groups[ext] = group_similar_files(files_by_ext[ext], threshold)

    pprint(similar_groups)


if __name__ == "__main__":
    main()
