import sys, shutil, os, pathlib


def check_prettier():
    """Check whether prettier is installed"""
    if not shutil.which("prettier"):
        print("Prettier is NOT installed")
        sys.exit(1)


def check_folders(folders):
    """Check whether an array of folders exists and create if not"""
    for folder in folders:
        if not (os.path.isdir(folder)):
            os.makedirs(folder)

# def read_file(path):
#     try:
#         return pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
#     except Exception:
#         return ""

def main():
    pass


if __name__ == "__main__":
    main()
