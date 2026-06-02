"""Simple dependency-free book export helpers."""

from __future__ import annotations

import html
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExportResult:
    data: dict[str, Any]
    output_path: Path


def _chapter_sort_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    digits = "".join(ch for ch in stem[:8] if ch.isdigit())
    return (int(digits) if digits else 999999, path.name)


def collect_chapters(root: Path) -> list[Path]:
    chapters_dir = root / "chapters"
    if not chapters_dir.is_dir():
        return []
    return sorted(
        [path for path in chapters_dir.glob("*.md") if path.name != "index.md"],
        key=_chapter_sort_key,
    )


def _combined_markdown(root: Path) -> str:
    parts = []
    for path in collect_chapters(root):
        parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts).strip() + "\n"


def export_book(root: Path, output_path: Path, fmt: str) -> ExportResult:
    fmt = fmt.lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = _combined_markdown(root)
    if fmt in {"md", "markdown"}:
        output_path.write_text(markdown, encoding="utf-8")
    elif fmt == "docx":
        _write_docx(output_path, markdown)
    elif fmt == "epub":
        _write_epub(output_path, markdown)
    else:
        raise ValueError("format must be markdown, docx, or epub")
    data = {
        "schema": "narrative_workbench.export_result.v1",
        "format": fmt,
        "chapter_count": len(collect_chapters(root)),
        "output_path": str(output_path),
    }
    return ExportResult(data=data, output_path=output_path)


def _paragraphs(markdown: str) -> list[str]:
    return [part.strip() for part in markdown.split("\n\n") if part.strip()]


def _write_docx(path: Path, markdown: str) -> None:
    body = []
    for para in _paragraphs(markdown):
        escaped = html.escape(para)
        body.append(f"<w:p><w:r><w:t>{escaped}</w:t></w:r></w:p>")
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)


def _write_epub(path: Path, markdown: str) -> None:
    body = "\n".join(f"<p>{html.escape(para)}</p>" for para in _paragraphs(markdown))
    chapter = f'<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>Book</title></head><body>{body}</body></html>'
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>'
        "</container>"
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package version="3.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Book</dc:title><dc:language>zh-CN</dc:language><dc:identifier id="bookid">narrative-workbench-export</dc:identifier></metadata>'
        '<manifest><item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="chapter"/></spine></package>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr("OEBPS/chapter.xhtml", chapter)


def export_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
