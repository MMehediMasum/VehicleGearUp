import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
 
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown
 
WXR_PATH = "wordpress-export.xml"
BLOG_DIR = Path("src/content/blog")
PAGE_DIR = Path("src/content/pages")
AUTHORS_DIR = Path("src/content/authors")
ERROR_LOG = Path("conversion-errors.json")
 
NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
 
 
def slugify(text):
    text = str(text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"
 

def bing_query_slug(text):
    text = str(text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)  # strips %, ?, commas, periods, etc.
    text = re.sub(r"\s+", "-", text)
    return text
 
 
def bing_thumb_url(query, w, h):
    return f"https://tse1.mm.bing.net/th?q={query}&w={w}&h={h}&c=7"
 
 
def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()
 
 
def first_two_sentences(text):
    text = text.strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:2]).strip()
 
 
def is_review_post(soup):
    """Post has at least one Amazon link wrapping a product image."""
    for a in soup.find_all("a", href=True):
        if "amazon.com" in a["href"] and a.find("img"):
            return True
    return False
 
 
def extract_amazon_blocks(soup):
    """
    Replace every Amazon-linked <a> (title link or image link) with a placeholder
    token so its exact original HTML (target, rel, tag param, alt) survives
    markdown conversion untouched, then restore it afterward.
    """
    tokens = {}
    counter = 0
    for a in soup.find_all("a", href=True):
        if "amazon.com" in a["href"]:
            token = f"%%AMZBLOCK{counter}%%"
            tokens[token] = str(a)
            a.replace_with(token)
            counter += 1
    return soup, tokens
 
 
def strip_all_images(soup):
    """Remove every <img> for non-review posts; drop now-empty wrapping <a>/<figure>."""
    for img in soup.find_all("img"):
        parent = img.parent
        img.decompose()
        if parent and parent.name in ("a", "figure") and not parent.get_text(strip=True) and not parent.find(True):
            parent.decompose()
    return soup
 
 
def insert_bing_images(markdown_body, min_images=2, max_images=5):
    """
    Insert a Bing thumbnail image right after selected H2 headings (skipping the
    first H2), using the first two sentences of that section's first paragraph
    as the search query. Number of images scales with word count.
    """
    lines = markdown_body.split("\n")
    h2_indices = [i for i, line in enumerate(lines) if line.startswith("## ")]
 
    if len(h2_indices) <= 1:
        return markdown_body
 
    word_count = len(re.sub(r"[#*_`\[\]()]", "", markdown_body).split())
    target_count = max(min_images, min(max_images, round(word_count / 300)))
 
    candidates = h2_indices[1:]
    step = max(1, len(candidates) // target_count)
    chosen = candidates[::step][:target_count]
 
    offset = 0
    for h2_line_idx in chosen:
        idx = h2_line_idx + offset
        j = idx + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j >= len(lines) or lines[j].startswith("#"):
            continue
 
        snippet = first_two_sentences(lines[j])
        if not snippet:
            continue
        query = bing_query_slug(snippet)
        img_markdown = f"![]({bing_thumb_url(query, 424, 324)})"
 
        lines.insert(idx + 1, "")
        lines.insert(idx + 2, img_markdown)
        offset += 2
 
    return "\n".join(lines)
 
 
def main():
    if not Path(WXR_PATH).exists():
        print(f"ERROR: {WXR_PATH} not found.")
        return
 
    tree = ET.parse(WXR_PATH)
    root = tree.getroot()
    channel = root.find("channel")
    items = channel.findall("item")
 
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    AUTHORS_DIR.mkdir(parents=True, exist_ok=True)

    items_to_convert = [
    item for item in items
    if (item.find("wp:post_type", NS) is not None and item.find("wp:post_type", NS).text in ["post", "page"])
    and (item.find("wp:status", NS) is not None and item.find("wp:status", NS).text == "publish")
]
    print(f"Found {len(items_to_convert)} published posts and pages.")
 
 
    authors_seen = {}
    converted = 0
    review_count = 0
    info_count = 0
    errors = []
 
    for i, item in enumerate(items_to_convert, 1):
        slug = "unknown"
        try:
            post_type = item.find("wp:post_type", NS).text
            title_el = item.find("title")
            title = html.unescape((title_el.text or "Untitled").strip()) if title_el is not None else "Untitled"
 
            slug_el = item.find("wp:post_name", NS)
            slug = (slug_el.text or "").strip() if slug_el is not None else ""
            slug = slug or slugify(title)
 
            date_el = item.find("wp:post_date", NS)
            pub_date = date_el.text.split(" ")[0] if date_el is not None and date_el.text else "2024-01-01"
 
            author_el = item.find("dc:creator", NS)
            author_login = (author_el.text or "unknown").strip() if author_el is not None else "unknown"
            author_slug = slugify(author_login)
            authors_seen[author_slug] = author_login
 
            categories = []
            for cat in item.findall("category"):
                if cat.get("domain") == "category" and cat.text:
                    categories.append(html.unescape(cat.text.strip()))
 
            content_el = item.find("content:encoded", NS)
            content_html = content_el.text or "" if content_el is not None else ""
 
            excerpt_el = item.find("excerpt:encoded", NS)
            excerpt_html = excerpt_el.text or "" if excerpt_el is not None else ""
            description = strip_html(excerpt_html or content_html)[:160]
 
            soup = BeautifulSoup(content_html, "html.parser")
            review_post = is_review_post(soup)
 
            if review_post:
                soup, amazon_tokens = extract_amazon_blocks(soup)
                markdown_body = html_to_markdown(str(soup), heading_style="ATX")
                for token, raw_html in amazon_tokens.items():
                    markdown_body = markdown_body.replace(token, raw_html)
                review_count += 1
            else:
                soup = strip_all_images(soup)
                markdown_body = html_to_markdown(str(soup), heading_style="ATX")
                markdown_body = insert_bing_images(markdown_body)
                info_count += 1
 
            hero_image = bing_thumb_url(slugify(slug), 424, 424)
 
            frontmatter_lines = [
                "---",
                f"title: {json.dumps(title, ensure_ascii=False)}",
                f"description: {json.dumps(description, ensure_ascii=False)}",
                f"pubDate: {pub_date}",
                f"author: {json.dumps(author_slug, ensure_ascii=False)}",
                f"categories: {json.dumps(categories, ensure_ascii=False)}",
                f"heroImage: {json.dumps(hero_image, ensure_ascii=False)}",
                "---",
            ]
 
            file_content = "\n".join(frontmatter_lines) + "\n\n" + markdown_body.strip() + "\n"
            target_dir = BLOG_DIR if post_type == "post" else PAGE_DIR
            (target_dir / f"{slug}.md").write_text(file_content, encoding="utf-8")
            converted += 1
 
            if i % 250 == 0:
                print(f"Progress: {i}/{len(items_to_convert)}")
 
        except Exception as e:
            errors.append({"slug": slug, "error": str(e)})
 
    for aslug, name in authors_seen.items():
        author_file = AUTHORS_DIR / f"{aslug}.json"
        if not author_file.exists():
            author_file.write_text(
                json.dumps({"name": name, "bio": "", "avatar": ""}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
 
    print("---")
    print(f"Converted: {converted}")
    print(f"Review posts (Amazon images kept as-is): {review_count}")
    print(f"Info posts (Bing images inserted): {info_count}")
    print(f"Errors: {len(errors)}")
    if errors:
        ERROR_LOG.write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Details: {ERROR_LOG}")
 
 
if __name__ == "__main__":
    main()
