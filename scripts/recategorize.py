#!/usr/bin/env python3
"""Recategorize kept posts into new topic clusters (v5 keyword workbook).

Sets two separate frontmatter fields so the site stays niche-agnostic:
  - categories: [cluster_name]   -> the specific category (unchanged behaviour)
  - topic: pet                   -> the broad top-level grouping used for the
                                     Header dropdown / /topic/[topic].astro page

Uses real YAML parsing (not regex) so it handles every frontmatter format
(single-line list, multi-line list, empty list, missing field, etc.) and is
safe to rerun (idempotent).
"""
import json
from pathlib import Path
from urllib.parse import urlparse

import openpyxl
import yaml

XLSX_PATH = "pet_keyword_clusters_v5.xlsx"
BLOG_DIR = Path("src/content/blog")
LOG_PATH = Path("category_remap_log.json")

FRONTMATTER_DELIM = "---"


def slug_from_url(url):
    return urlparse(str(url)).path.strip("/").split("/")[-1]


def split_frontmatter(text):
    if not text.startswith(FRONTMATTER_DELIM):
        return None, None
    parts = text.split(FRONTMATTER_DELIM, 2)
    if len(parts) < 3:
        return None, None
    _, raw_fm, body = parts
    data = yaml.safe_load(raw_fm) or {}
    return data, body


def join_frontmatter(data, body):
    raw_fm = yaml.safe_dump(
        data, allow_unicode=True, sort_keys=False, default_flow_style=False
    )
    return f"{FRONTMATTER_DELIM}\n{raw_fm}{FRONTMATTER_DELIM}{body}"


def main():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    sheet = wb["All Keywords by Cluster"]

    updated = 0
    missing_file = []
    missing_field = []
    parse_error = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        # No. | Pet | Cluster Name | Topic Type | Keyword / Topic | Post URL
        _, pet, cluster_name, _topic_type, _keyword, post_url = row
        if not post_url:
            continue

        slug = slug_from_url(post_url)
        md_path = BLOG_DIR / f"{slug}.md"
        if not md_path.exists():
            missing_file.append({"slug": slug, "url": post_url})
            continue

        text = md_path.read_text(encoding="utf-8")
        try:
            data, body = split_frontmatter(text)
        except yaml.YAMLError as e:
            parse_error.append({"slug": slug, "error": str(e)})
            continue

        if data is None:
            missing_field.append({"slug": slug, "why": "no frontmatter block found"})
            continue

        if "categories" not in data:
            missing_field.append({"slug": slug, "why": "no categories key in frontmatter"})
            continue

        data["categories"] = [cluster_name]
        data["topic"] = pet

        md_path.write_text(join_frontmatter(data, body), encoding="utf-8")
        updated += 1

    print(f"Updated: {updated}")
    print(f"Missing local .md file: {len(missing_file)}")
    print(f"No categories field found: {len(missing_field)}")
    print(f"YAML parse errors: {len(parse_error)}")

    LOG_PATH.write_text(
        json.dumps(
            {
                "missing_file": missing_file,
                "missing_field": missing_field,
                "parse_error": parse_error,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Details saved to {LOG_PATH}")


if __name__ == "__main__":
    main()
