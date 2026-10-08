import io
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = sorted([*(ROOT / "src").rglob("*.py"), *(ROOT / "tests").rglob("*.py")])
WEB_DIR = ROOT / "src" / "cafesito" / "web"
LINE_COMMENT = re.compile(r"^\s*//")
BLOCK_COMMENT = re.compile(r"/\*")
HTML_COMMENT = re.compile(r"<!--")


@pytest.mark.parametrize("path", PYTHON_FILES, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_python_files_have_no_comments(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    comments = [token.string for token in tokens if token.type == tokenize.COMMENT]
    assert comments == []


@pytest.mark.parametrize(
    "path",
    sorted(WEB_DIR.rglob("*.js")),
    ids=lambda path: path.relative_to(ROOT).as_posix(),
)
def test_javascript_files_have_no_comments(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert not BLOCK_COMMENT.search(text)
    assert not any(LINE_COMMENT.match(line) for line in text.splitlines())


def test_css_and_html_have_no_comments() -> None:
    assert not BLOCK_COMMENT.search((WEB_DIR / "css" / "style.css").read_text(encoding="utf-8"))
    assert not HTML_COMMENT.search((WEB_DIR / "index.html").read_text(encoding="utf-8"))
