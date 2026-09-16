"""
Dev-to-delivery packager for the Purdy Electric site.
Run after every edit to index.html/styles.css/assets/*: inlines styles.css into a <style>
tag and embeds every local image as a base64 data: URI, so the shipped index.html works
standalone (double-clicked, emailed, dragged into a browser) with no external files.
"""
import base64
import mimetypes
import re
from pathlib import Path

SITE = Path(__file__).parent
SRC_HTML = SITE / "dev.html"
CSS = SITE / "styles.css"

html = SRC_HTML.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")


def minify_css(text):
    """Conservative minifier: strip comments, collapse whitespace, trim space around
    punctuation. styles.css stays fully commented/formatted as the dev source — only the
    embedded copy in index.html is minified, saving ~6KiB (flagged by Lighthouse)."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}:;,])\s*", r"\1", text)
    text = re.sub(r";}", "}", text)
    return text.strip()


# Inline stylesheet (minified — dev source stays readable in styles.css)
html = html.replace(
    '<link rel="stylesheet" href="styles.css">',
    f"<style>{minify_css(css)}</style>",
)

# Embed every local asset (assets/...) as a base64 data URI
def embed(match):
    prefix, path, suffix = match.group(1), match.group(2), match.group(3)
    file_path = SITE / path
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    data = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f'{prefix}data:{mime};base64,{data}{suffix}'

html = re.sub(r'(src=")(assets/[^"]+)(")', embed, html)

out = SITE / "index.html"
out.write_text(html, encoding="utf-8")
print("Packaged", out, len(html), "bytes")
