"""Layered co-writing diff workflow.

The diff workflow keeps Claude Code/Codex conversations short:
conversation shows a summary, Markdown carries human-readable details, and
JSONL carries patch candidates for deterministic apply/reject operations.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class DiffGenerationResult:
    data: dict[str, Any]
    index_path: Path
    jsonl_path: Path
    patch_dir: Path


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def split_paragraphs(text: str) -> list[str]:
    if not text:
        return []
    paragraphs = re.split(r"\n{2,}", text.strip("\n"))
    return [para for para in paragraphs]


def join_paragraphs(paragraphs: Iterable[str]) -> str:
    return "\n\n".join(paragraphs).rstrip() + "\n"


def _summary(original: str, suggestion: str) -> str:
    if len(original) == len(suggestion):
        return "替换表达，长度基本不变"
    if len(original) > len(suggestion):
        return "压缩表达或删除重复"
    return "扩展表达或补足细节"


def _change_type(original: str, suggestion: str) -> str:
    ai_patterns = ["难以言说", "仿佛", "终于意识到", "这一刻", "内心"]
    if any(pattern in original for pattern in ai_patterns):
        return "AI味"
    if "“" in original or "\"" in original or "”" in original:
        return "对白"
    if abs(len(original) - len(suggestion)) > 80:
        return "节奏"
    return "语言润色"


def _risk(original: str, suggestion: str) -> str:
    risky_words = ["身份", "秘密", "真相", "伏笔", "父亲", "死亡", "背叛"]
    if any(word in suggestion and word not in original for word in risky_words):
        return "高"
    if abs(len(original) - len(suggestion)) > max(120, len(original) // 2):
        return "中"
    return "低"


def _candidate_id(index: int) -> str:
    return f"{index:02d}"


def candidate_paths(root: Path, chapter: int) -> tuple[Path, Path, Path]:
    prefix = chapter_prefix(chapter)
    index_path = root / "story/runtime" / f"{prefix}.diff_index.md"
    jsonl_path = root / "story/runtime" / f"{prefix}.patch_candidates.jsonl"
    patch_dir = root / "story/runtime/diffs" / prefix
    return index_path, jsonl_path, patch_dir


def generate_candidates(
    root: Path,
    chapter: int,
    original_path: Path,
    revised_path: Path,
) -> DiffGenerationResult:
    original_text = original_path.read_text(encoding="utf-8")
    revised_text = revised_path.read_text(encoding="utf-8")
    original_paras = split_paragraphs(original_text)
    revised_paras = split_paragraphs(revised_text)

    candidates: list[dict[str, Any]] = []
    count = max(len(original_paras), len(revised_paras))
    for idx in range(count):
        original = original_paras[idx] if idx < len(original_paras) else ""
        suggestion = revised_paras[idx] if idx < len(revised_paras) else ""
        if original == suggestion:
            continue
        candidate = {
            "schema": "narrative_workbench.patch_candidate.v1",
            "id": _candidate_id(len(candidates) + 1),
            "chapter": chapter,
            "paragraph_id": f"P{idx + 1:03d}",
            "paragraph_index": idx,
            "type": _change_type(original, suggestion),
            "risk": _risk(original, suggestion),
            "summary": _summary(original, suggestion),
            "reason": "由作者稿与候选润色稿的段落差异生成；语义采纳需作者确认。",
            "original": original,
            "suggestion": suggestion,
            "status": "pending",
            "source": {
                "original": str(original_path),
                "revised": str(revised_path),
            },
            "created_at": now_iso(),
        }
        candidates.append(candidate)

    index_path, jsonl_path, patch_dir = candidate_paths(root, chapter)
    patch_dir.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    write_candidates(jsonl_path, candidates)
    write_index(index_path, patch_dir, chapter, candidates)
    for candidate in candidates:
        write_patch_detail(patch_dir / f"patch-{candidate['id']}.md", candidate)

    data = {
        "schema": "narrative_workbench.diff_result.v1",
        "chapter": chapter,
        "candidate_count": len(candidates),
        "index_path": str(index_path),
        "jsonl_path": str(jsonl_path),
        "patch_dir": str(patch_dir),
        "summary": summarize_candidates(candidates),
    }
    return DiffGenerationResult(data=data, index_path=index_path, jsonl_path=jsonl_path, patch_dir=patch_dir)


def write_candidates(path: Path, candidates: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate, ensure_ascii=False) + "\n")


def read_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"patch candidates not found: {path}")
    candidates: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            candidates.append(json.loads(line))
    return candidates


def summarize_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for candidate in candidates:
        by_type[candidate["type"]] = by_type.get(candidate["type"], 0) + 1
        by_risk[candidate["risk"]] = by_risk.get(candidate["risk"], 0) + 1
    return {"by_type": by_type, "by_risk": by_risk}


def write_index(index_path: Path, patch_dir: Path, chapter: int, candidates: list[dict[str, Any]]) -> None:
    summary = summarize_candidates(candidates)
    lines = [
        f"# 第{chapter}章润色建议索引",
        "",
        f"> 共 {len(candidates)} 条修改建议。对话窗口只显示摘要；单条详情见 `{patch_dir.as_posix()}/`。",
        "",
        "## 类型统计",
        "",
    ]
    if summary["by_type"]:
        for label, count in sorted(summary["by_type"].items()):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- 无修改建议。")
    lines.extend(["", "## 风险统计", ""])
    if summary["by_risk"]:
        for label, count in sorted(summary["by_risk"].items()):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- 无风险项。")
    lines.extend(
        [
            "",
            "## 建议索引",
            "",
            "| ID | 段落 | 类型 | 摘要 | 风险 | 建议 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for candidate in candidates:
        recommendation = "人工确认" if candidate["risk"] in {"中", "高"} else "可接受"
        lines.append(
            f"| {candidate['id']} | {candidate['paragraph_id']} | {candidate['type']} | "
            f"{candidate['summary']} | {candidate['risk']} | {recommendation} |"
        )
    lines.extend(
        [
            "",
            "## 可直接输入的操作",
            "",
            f"- 显示修改 03：`nw diff show --chapter {chapter} --id 03`",
            f"- 应用选择：`nw diff apply --chapter {chapter} --accept 01,03 --reject 02`",
            "",
        ]
    )
    index_path.write_text("\n".join(lines), encoding="utf-8")


def write_patch_detail(path: Path, candidate: dict[str, Any]) -> None:
    lines = [
        f"# 修改建议 {candidate['id']}",
        "",
        f"位置：{candidate['paragraph_id']}",
        f"类型：{candidate['type']}",
        f"风险：{candidate['risk']}",
        "",
        "## 原文",
        "",
        candidate["original"] or "(空段落)",
        "",
        "## 建议文本",
        "",
        candidate["suggestion"] or "(删除该段)",
        "",
        "## 修改原因",
        "",
        candidate["reason"],
        "",
        "## 影响范围",
        "",
        "按段落替换；是否改变事实、伏笔或人物行为需作者确认。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_id_set(value: str | None) -> set[str]:
    if not value:
        return set()
    ids: set[str] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            start_i = int(start)
            end_i = int(end)
            for num in range(start_i, end_i + 1):
                ids.add(_candidate_id(num))
        else:
            ids.add(_candidate_id(int(part)))
    return ids


def show_candidate(root: Path, chapter: int, candidate_id: str) -> str:
    _, jsonl_path, _ = candidate_paths(root, chapter)
    candidate_id = _candidate_id(int(candidate_id))
    for candidate in read_candidates(jsonl_path):
        if candidate["id"] == candidate_id:
            return "\n".join(
                [
                    f"修改 {candidate['id']} / {candidate['paragraph_id']} / {candidate['type']} / 风险 {candidate['risk']}",
                    "",
                    "原文:",
                    candidate["original"] or "(空段落)",
                    "",
                    "建议:",
                    candidate["suggestion"] or "(删除该段)",
                    "",
                    f"原因: {candidate['reason']}",
                ]
            )
    raise ValueError(f"candidate id not found: {candidate_id}")


def apply_candidates(
    root: Path,
    chapter: int,
    accept: str | None,
    reject: str | None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    _, jsonl_path, _ = candidate_paths(root, chapter)
    candidates = read_candidates(jsonl_path)
    if not candidates:
        raise ValueError("no patch candidates available")

    accept_ids = parse_id_set(accept)
    reject_ids = parse_id_set(reject)
    overlap = accept_ids & reject_ids
    if overlap:
        raise ValueError(f"ids cannot be both accepted and rejected: {sorted(overlap)}")

    by_id = {candidate["id"]: candidate for candidate in candidates}
    unknown = (accept_ids | reject_ids) - set(by_id)
    if unknown:
        raise ValueError(f"unknown candidate ids: {sorted(unknown)}")

    original_path = Path(candidates[0]["source"]["original"])
    paragraphs = split_paragraphs(original_path.read_text(encoding="utf-8"))
    decisions: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate = dict(candidate)
        cid = candidate["id"]
        if cid in accept_ids:
            index = int(candidate["paragraph_index"])
            while len(paragraphs) <= index:
                paragraphs.append("")
            paragraphs[index] = candidate["suggestion"]
            candidate["status"] = "accepted"
        elif cid in reject_ids:
            candidate["status"] = "rejected"
        else:
            candidate["status"] = "pending"
        candidate["decided_at"] = now_iso() if candidate["status"] != "pending" else ""
        decisions.append(candidate)

    write_candidates(jsonl_path, decisions)
    if output_path is None:
        prefix = chapter_prefix(chapter)
        output_path = root / "chapters/drafts" / f"{prefix}.author.v2.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(join_paragraphs(paragraphs), encoding="utf-8")

    log_path = root / "story/runtime" / f"{chapter_prefix(chapter)}.decision_log.md"
    write_decision_log(log_path, chapter, decisions, output_path)
    return {
        "schema": "narrative_workbench.diff_apply_result.v1",
        "chapter": chapter,
        "accepted": sorted(accept_ids),
        "rejected": sorted(reject_ids),
        "pending": [item["id"] for item in decisions if item["status"] == "pending"],
        "output_path": str(output_path),
        "decision_log": str(log_path),
        "jsonl_path": str(jsonl_path),
    }


def write_decision_log(path: Path, chapter: int, decisions: list[dict[str, Any]], output_path: Path) -> None:
    accepted = [item for item in decisions if item["status"] == "accepted"]
    rejected = [item for item in decisions if item["status"] == "rejected"]
    pending = [item for item in decisions if item["status"] == "pending"]
    lines = [
        f"# 第{chapter}章润色决策日志",
        "",
        f"- 生成版本：`{output_path}`",
        f"- 接受：{len(accepted)}",
        f"- 拒绝：{len(rejected)}",
        f"- 保留待定：{len(pending)}",
        "",
        "## 决策明细",
        "",
        "| ID | 段落 | 类型 | 风险 | 状态 |",
        "|---|---|---|---|---|",
    ]
    for item in decisions:
        lines.append(
            f"| {item['id']} | {item['paragraph_id']} | {item['type']} | "
            f"{item['risk']} | {item['status']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
