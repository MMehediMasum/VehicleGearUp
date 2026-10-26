#!/usr/bin/env python3
r"""
Amazon Associates tracking-ID (tag=...) replacer for Astro / static sites.

Walks through every post/page file one by one, finds the old Amazon tag
and replaces it with the new one.

Usage (script placed in <site>/scripts/):
  Open a terminal in the site root (where package.json lives) and run.
  If no path is given, the script uses the folder above its own "scripts"
  folder as the site root, so it works from any current directory.

  # List every tag found in the site
  python scripts/change_amazon_tag.py --scan

  # Preview only (nothing is saved)
  python scripts/change_amazon_tag.py --old gearcookware-20 --new mofb05-20 --dry-run

  # Real run (keeps a .bak copy of every changed file)
  python scripts/change_amazon_tag.py --old gearcookware-20 --new mofb05-20 --backup

  # Other site(s) / several sites at once: pass the folder path(s)
  python scripts/change_amazon_tag.py D:\Sites\SiteA D:\Sites\SiteB --old OLD-20 --new NEW-20

  (On Windows use `py` if `python` is not recognised.)

Features:
  * Replaces only the `tag=<id>` parameter (?tag=, &tag=, &amp;tag= all work)
  * Leaves longer IDs alone (e.g. gearcookware-201 is NOT touched)
  * Preserves line endings (CRLF/LF) and encoding exactly (works on bytes)
  * Skips node_modules, .git, dist, .astro, etc.
"""
import argparse
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

DEFAULT_EXTS = [".md", ".mdx", ".astro", ".html", ".htm", ".json", ".ts", ".js", ".mjs", ".tsx", ".jsx", ".yaml", ".yml", ".txt"]
SKIP_DIRS = {"node_modules", ".git", "dist", ".astro", ".wrangler", ".vercel", ".netlify", ".next", "build"}
CODE_CHARS = rb"A-Za-z0-9_-"


def iter_files(roots, exts):
    for root in roots:
        root = Path(root)
        if root.is_file():
            yield root
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
                continue
            if p.suffix.lower() in exts and not p.name.endswith(".bak"):
                yield p


def main():
    # Avoid encoding errors when printing on Windows consoles
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Amazon affiliate tag replacer")
    ap.add_argument("paths", nargs="*", help="Site folder(s) or file(s); defaults to the folder above this script's folder")
    ap.add_argument("--old", help="Old tracking ID, e.g. gearcookware-20")
    ap.add_argument("--new", help="New tracking ID, e.g. mofb05-20")
    ap.add_argument("--ext", nargs="*", default=DEFAULT_EXTS, help="File extensions to scan")
    ap.add_argument("--dry-run", action="store_true", help="Report only; do not save any file")
    ap.add_argument("--backup", action="store_true", help="Save a file.ext.bak copy before changing a file")
    ap.add_argument("--scan", action="store_true", help="List all tag= IDs found (changes nothing)")
    ap.add_argument("-q", "--quiet", action="store_true", help="Print only the summary, not each file")
    args = ap.parse_args()
    if not args.paths:
        args.paths = [str(Path(__file__).resolve().parent.parent)]
        print(f"Site folder: {args.paths[0]}")

    exts = {e.lower() if e.startswith(".") else "." + e.lower() for e in args.ext}
    files = list(iter_files(args.paths, exts))

    any_tag = re.compile(rb"(?<![A-Za-z0-9])tag=([" + CODE_CHARS + rb"]+)")

    # ---------- scan mode ----------
    if args.scan or not (args.old and args.new):
        if not args.scan:
            ap.error("provide both --old and --new (or use --scan to just list the tags)")
        counts, per_file = Counter(), Counter()
        for f in files:
            data = f.read_bytes()
            found = any_tag.findall(data)
            for t in found:
                counts[t.decode()] += 1
            if found:
                per_file[f] += len(found)
        print(f"Files scanned: {len(files)} | files containing a tag: {len(per_file)}")
        for tag, n in counts.most_common():
            print(f"  tag={tag:<25} {n} time(s)")
        return 0

    old, new = args.old.strip(), args.new.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", old) or not re.fullmatch(r"[A-Za-z0-9_-]+", new):
        ap.error("IDs may contain only letters, digits, '-' and '_'")
    if old == new:
        ap.error("--old and --new are identical")

    pattern = re.compile(rb"((?<![A-Za-z0-9])tag=)" + re.escape(old.encode()) + rb"(?![" + CODE_CHARS + rb"])")
    repl = rb"\g<1>" + new.encode()

    total_files = changed_files = total_repl = 0
    others = Counter()
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(f"[{mode}] '{old}' -> '{new}' | files to check: {len(files)}\n")

    for f in files:
        total_files += 1
        data = f.read_bytes()
        for t in any_tag.findall(data):
            if t.decode() != old:
                others[t.decode()] += 1
        new_data, n = pattern.subn(repl, data)
        if n == 0:
            continue
        changed_files += 1
        total_repl += n
        if not args.quiet:
            print(f"  [OK] {f}  ({n} link(s))")
        if not args.dry_run:
            if args.backup:
                shutil.copy2(f, f.with_name(f.name + ".bak"))
            f.write_bytes(new_data)

    print("\n" + "=" * 50)
    upd = "to update" if args.dry_run else "updated"
    rep = "to replace" if args.dry_run else "replaced"
    print(f"{'Files checked':<16}: {total_files}")
    print(f"{'Files ' + upd:<16}: {changed_files}")
    print(f"{'Files unchanged':<16}: {total_files - changed_files}")
    print(f"{'Links ' + rep:<16}: {total_repl}")
    if args.dry_run:
        print("(dry run - nothing was saved)")
    print("=" * 50)
    if others:
        print("WARNING: other tags were found (left unchanged):")
        for t, n in others.most_common():
            print(f"    tag={t}  {n} time(s)")

    # Verify: any old tag left?
    if not args.dry_run:
        left = sum(len(pattern.findall(f.read_bytes())) for f in files)
        print(f"Verification: old tags remaining = {left}")
        return 0 if left == 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())