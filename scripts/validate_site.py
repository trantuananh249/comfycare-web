from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re


ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = sorted(
    path for path in ROOT.rglob("*.html")
    if "outputs" not in path.relative_to(ROOT).parts
)


class Inspector(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.refs = []
        self.links = []
        self.images_without_size = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            src = attrs.get("src", "")
            if "width" not in attrs or "height" not in attrs:
                self.images_without_size.append(src)
        for name in ("src", "href"):
            value = attrs.get(name)
            if value:
                (self.links if tag == "a" and name == "href" else self.refs).append(value)
        srcset = attrs.get("srcset", "")
        if srcset:
            self.refs.extend(item.strip().split()[0] for item in srcset.split(",") if item.strip())


def local_path(url: str):
    if not url or url.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None
    split = urlsplit(url)
    if split.scheme or split.netloc:
        return None
    clean = unquote(split.path)
    if not clean:
        return None
    return ROOT / clean.lstrip("/") if clean.startswith("/") else None


missing_assets = []
missing_links = []
unsized = []
for path in HTML_FILES:
    parser = Inspector(path)
    parser.feed(path.read_text(encoding="utf-8"))
    for ref in parser.refs:
        candidate = local_path(ref)
        if candidate is not None and candidate.suffix and not candidate.exists():
            missing_assets.append((str(path.relative_to(ROOT)), ref))
    for link in parser.links:
        candidate = local_path(link)
        if candidate is None:
            continue
        if candidate.suffix:
            exists = candidate.exists()
        else:
            exists = (candidate / "index.html").exists() or candidate.with_suffix(".html").exists()
        if not exists:
            missing_links.append((str(path.relative_to(ROOT)), link))
    for src in parser.images_without_size:
        if not src.startswith(("data:", "https://www.facebook.com/tr")):
            unsized.append((str(path.relative_to(ROOT)), src))

css_text = "\n".join((ROOT / name).read_text(encoding="utf-8") for name in ("styles.css", "styles.min.css"))
for url in re.findall(r"url\((?:['\"])?([^)'\"]+)", css_text):
    candidate = local_path(url)
    if candidate is not None and not candidate.exists():
        missing_assets.append(("styles.css", url))

layout_text = (ROOT / "layout.js").read_text(encoding="utf-8")
for url in sorted(set(re.findall(r'["\'](/assets/[^"\']+)["\']', layout_text))):
    candidate = local_path(url)
    if candidate is not None and not candidate.exists():
        missing_assets.append(("layout.js", url))

print({
    "html_files": len(HTML_FILES),
    "missing_assets": len(missing_assets),
    "missing_internal_links": len(missing_links),
    "unsized_images": len(unsized),
})
if missing_assets:
    print("MISSING ASSETS")
    for item in missing_assets:
        print(item)
if missing_links:
    print("MISSING INTERNAL LINKS")
    for item in missing_links:
        print(item)
if unsized:
    print("IMAGES WITHOUT INTRINSIC SIZE")
    for item in unsized:
        print(item)

raise SystemExit(1 if missing_assets or missing_links or unsized else 0)
