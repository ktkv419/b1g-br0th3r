#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import subprocess

ORG = "21ISR"
SUBSTR = "lab7"
BRANCH = "wip"
DEST_DIR = "./clones"
TOKEN = os.getenv("GITHUB_TOKEN")


def get_all_repos(org, token):
    """Paginate through /orgs/{org}/repos"""
    repos = []
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"token {token}"} if token else {}
    page = 1
    while True:
        resp = requests.get(
            url, headers=headers, params={"per_page": 100, "page": page}
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def has_branch(org, repo_name, branch, token):
    """Return True if repo has given branch."""
    url = f"https://api.github.com/repos/{org}/{repo_name}/branches/{branch}"
    headers = {"Authorization": f"token {token}"} if token else {}
    resp = requests.get(url, headers=headers)
    return resp.status_code == 200


def clone_repo(org, repo_name, branch, dest_dir):
    """Run git clone --branch <branch> <url> into dest_dir if not already cloned."""
    target_path = os.path.join(dest_dir, repo_name)
    if os.path.exists(target_path):
        print(f"✅ Skipping {repo_name}: already cloned at {target_path}")
        return

    repo_url = f"https://github.com/{org}/{repo_name}.git"
    cmd = ["git", "clone", "--branch", branch, "--single-branch", repo_url, target_path]
    print(f"🚀 Cloning {org}/{repo_name}@{branch} → {target_path}")
    subprocess.check_call(cmd)


def main():
    p = argparse.ArgumentParser(
        description="Clone all repos in an Org whose name contains a substring and have a specific branch"
    )
    p.add_argument("--org", required=True, help="GitHub organization name")
    p.add_argument(
        "--substring", default="lab7", help="Filter repos whose name includes this"
    )
    p.add_argument("--branch", default="wip", help="Branch name to look for and clone")
    p.add_argument("--dest", default=".", help="Destination directory for clones")
    args = p.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            "⚠️  Warning: no GITHUB_TOKEN env var set; you may hit API rate limits.",
            file=sys.stderr,
        )

    # 1) fetch repos
    repos = get_all_repos(args.org, token)
    # 2) filter by name
    target = [r["name"] for r in repos if args.substring.lower() in r["name"].lower()]

    if not target:
        print(f"No repos in org '{args.org}' matching substring '{args.substring}'.")
        sys.exit(0)

    os.makedirs(args.dest, exist_ok=True)

    # 3) for each, check branch & clone
    for name in target:
        if has_branch(args.org, name, args.branch, token):
            try:
                clone_repo(args.org, name, args.branch, args.dest)
            except subprocess.CalledProcessError:
                print(f"❌ Failed to clone {name}", file=sys.stderr)
        else:
            print(f"Skipping {name}: no '{args.branch}' branch")


if __name__ == "__main__":
    main()
