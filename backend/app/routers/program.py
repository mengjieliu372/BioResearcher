from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse
from pathlib import Path
import json
import os
import time
import hashlib
import csv
import mimetypes
import re
import zipfile
from pydantic import BaseModel
from app.models.our_utils import read_txt
from app.models.programming import code_generator, CodingNeedsFeedbackError, CodingFinalFailureError
from app.models.our_utils import read_json, MODEL_CODEX, MODEL_PRECISE, model_generate
from app.auth_core import EXAMPLE_PROJECT_ID, ensure_project_access, require_user

router = APIRouter()

EXCLUDED_DISPLAY_FILES = {
    "part5_dry_experiment_2_corr_heatmap.png",
    "part5_dry_experiment_3_km_plot.png",
    "ebayes_statistics.csv",
    "eligible_samples_final.csv",
    "go_enrichment_results.csv",
    "gtex_sarcoma_sample_metadata.csv",
    "part3_dry_experiment_5_degs.csv",
    "part5_dry_experiment_3_km_results.csv",
}


def _is_display_excluded(name: str) -> bool:
    return (name or "").strip().lower() in EXCLUDED_DISPLAY_FILES


class CodingFeedbackPayload(BaseModel):
    feedback: str


def _reject_example_regeneration(expid: int):
    if int(expid) == int(EXAMPLE_PROJECT_ID):
        raise HTTPException(
            status_code=409,
            detail={
                "demo_only": True,
                "message": "Example project is read-only demo. Existing outputs are presented directly.",
            },
        )


def _runtime_status_path(expid: int) -> Path:
    return Path(__file__).parent.parent / "data" / str(expid) / "runtime_status.json"


def _read_runtime_status(expid: int) -> dict:
    p = _runtime_status_path(expid)
    defaults = {
        "running": False,
        "progress": 0,
        "message": "Idle",
        "checkpoint": "init",
        "error": None,
        "updated_at": "",
    }
    if not p.exists():
        return defaults
    try:
        data = read_json(p)
        defaults.update(data)
    except Exception:
        pass
    return defaults


def _write_runtime_status(expid: int, **kwargs):
    p = _runtime_status_path(expid)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = _read_runtime_status(expid)
    data.update(kwargs)
    data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    p.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")

@router.get("/{id}/program")
async def get_program(id: int, value: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    try:
        return process_program(id, value)
    except FileNotFoundError:
        data_dir = Path(__file__).parent.parent / "data" / str(id)
        available = []
        if data_dir.exists():
            for p in data_dir.glob("coding*"):
                if p.is_dir():
                    digits = "".join(ch for ch in p.name if ch.isdigit())
                    if digits:
                        available.append(int(digits))
        return {
            "not_ready": True,
            "message": f"Directory coding{value + 1} not found for experiment id {id}.",
            "available_versions": sorted(set(available)),
            "files": {},
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Error decoding the JSON data in the coding file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


def process_program(id: int, value: int):
    data_dir = Path(__file__).parent.parent / "data" / str(id)
    code_dir = data_dir / f"coding{value + 1}"
    if not code_dir.exists():
        raise FileNotFoundError(f"Directory not found: {code_dir}")
    files_in_codingdir = os.listdir(code_dir)
    files_Rcode = dict()
    for file in files_in_codingdir:
        if file.endswith('.R') or file.endswith('.r') or file.endswith('.sh'):
            code_path = code_dir / file
            code_txt = read_txt(code_path)
            files_Rcode[file] = code_txt

    return files_Rcode


def _load_task_ids_from_dry(dry_path: Path) -> list[str]:
    if not dry_path.exists():
        return []
    try:
        dry = read_json(dry_path)
    except Exception:
        return []
    ids = []
    if isinstance(dry, dict):
        for _, tasks in dry.items():
            if isinstance(tasks, list):
                for t in tasks:
                    if isinstance(t, dict):
                        tid = t.get("task_id")
                        if isinstance(tid, str) and tid.strip():
                            ids.append(tid.strip())
    # de-dup keep order
    seen = set()
    out = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _collect_task_progress_from_log(log_payload: dict) -> tuple[set[str], set[str]]:
    completed = set()
    failed = set()
    if not isinstance(log_payload, dict):
        return completed, failed
    for k, v in log_payload.items():
        if not (isinstance(k, str) and k.startswith("Part") and isinstance(v, dict)):
            continue
        for task_id, rec in v.items():
            if not isinstance(task_id, str) or not isinstance(rec, dict):
                continue
            if rec.get("flag") is False:
                failed.add(task_id)
            elif "chat_history" in rec:
                completed.add(task_id)
    return completed, failed


def _generated_files_fingerprint(files: list[str]) -> str:
    txt = "\n".join(sorted(files or []))
    return hashlib.md5(txt.encode("utf-8")).hexdigest()


def _safe_output_file_path(code_dir: Path, name: str) -> Path:
    p = (code_dir / name).resolve()
    base = code_dir.resolve()
    if not str(p).startswith(str(base)):
        raise ValueError("invalid file path")
    return p


def _infer_render_type(name: str) -> str:
    n = (name or "").lower()
    if n.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
        return "image"
    if n.endswith(".json"):
        return "json"
    if n.endswith((".csv", ".tsv")):
        return "table"
    if n.endswith((".txt", ".md", ".log")):
        return "text"
    return "download"


def _build_file_preview(code_dir: Path, file_name: str) -> dict:
    p = _safe_output_file_path(code_dir, file_name)
    if not p.exists() or not p.is_file():
        return {"name": file_name, "exists": False, "render_type": "download"}
    render = _infer_render_type(file_name)
    item = {
        "name": file_name,
        "exists": True,
        "render_type": render,
        "size_bytes": p.stat().st_size,
    }
    try:
        if render == "json":
            data = read_json(p)
            if isinstance(data, list):
                item["json_preview"] = data[:10]
            elif isinstance(data, dict):
                keys = list(data.keys())[:20]
                item["json_preview"] = {k: data[k] for k in keys}
            else:
                item["json_preview"] = data
        elif render == "table":
            delim = "," if file_name.lower().endswith(".csv") else "\t"
            rows = []
            with p.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.reader(f, delimiter=delim)
                for i, row in enumerate(reader):
                    rows.append(row)
                    if i >= 20:
                        break
            item["table_preview"] = rows
        elif render == "text":
            txt = p.read_text(encoding="utf-8", errors="ignore")
            item["text_preview"] = txt[:5000]
        else:
            item["text_preview"] = ""
    except Exception as e:
        item["preview_error"] = str(e)
    return item


def _heuristic_recommended_files(files: list[str], limit: int = 24) -> list[str]:
    score_list = []
    for f in files:
        if _is_display_excluded(f):
            continue
        name = (f or "").lower()
        score = 0
        if name.endswith((".csv", ".tsv", ".txt", ".xlsx", ".json", ".rds", ".rda", ".md")):
            score += 5
        if any(k in name for k in ["summary", "result", "report", "statistics", "eligible", "sample", "design", "matrix", "deg", "enrichment", "kegg", "go_"]):
            score += 6
        if name.endswith((".png", ".pdf")):
            score += 2
        if any(k in name for k in ["tmp_", ".log", "__pycache__", ".pyc"]):
            score -= 4
        score_list.append((score, f))
    score_list.sort(key=lambda x: (-x[0], x[1]))
    out = [f for s, f in score_list if s > 0]
    if not out:
        out = [f for _, f in score_list]
    return out[:limit]


def _collect_code_files(code_dir: Path) -> list[str]:
    if not code_dir.exists():
        return []
    out = []
    for p in code_dir.iterdir():
        if not p.is_file():
            continue
        if p.name.endswith(".R") or p.name.endswith(".r") or p.name.endswith(".sh"):
            out.append(p.name)
    return sorted(out)


def _extract_r_packages_from_code(code_dir: Path, code_files: list[str]) -> list[str]:
    pkg = set()
    pattern = re.compile(r"(?:library|require)\s*\(\s*['\"]?([A-Za-z][A-Za-z0-9._]*)['\"]?\s*\)")
    for name in code_files:
        try:
            p = _safe_output_file_path(code_dir, name)
            txt = p.read_text(encoding="utf-8", errors="ignore")
            for m in pattern.finditer(txt):
                pkg.add(m.group(1))
        except Exception:
            continue
    return sorted(pkg)


def _build_display_zip_manifest(
    expid: int,
    display_names: list[str],
    code_names: list[str],
    r_packages: list[str],
) -> dict:
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return {
        "experiment_id": expid,
        "generated_at": now,
        "bundle_type": "display_results_plus_code",
        "display_files": display_names,
        "r_code_files": code_names,
        "detected_r_packages": r_packages,
        "notes": "This bundle contains files shown in Programming result view plus R code files.",
    }


def _file_fingerprint(code_dir: Path, names: list[str]) -> str:
    lines = []
    for n in sorted(set(names)):
        try:
            p = _safe_output_file_path(code_dir, n)
            st = p.stat()
            lines.append(f"{n}|{st.st_size}|{int(st.st_mtime)}")
        except Exception:
            lines.append(f"{n}|missing")
    return hashlib.md5("\n".join(lines).encode("utf-8")).hexdigest()


def _ensure_display_data_zip(
    expid: int,
    data_dir: Path,
    code_dir: Path,
    display_files: list[str],
    display_items: list[dict],
) -> dict:
    exports_dir = Path(__file__).parent.parent / "data" / "_exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    meta_path = data_dir / "program_data_zip_meta.json"
    manifest_disk_path = data_dir / "program_data_bundle_manifest.json"

    display_names = []
    for n in (display_files or []):
        if isinstance(n, str) and n.strip():
            display_names.append(n.strip())
    for item in (display_items or []):
        name = item.get("name") if isinstance(item, dict) else None
        if isinstance(name, str) and name.strip():
            display_names.append(name.strip())
    # keep order, de-dup
    seen = set()
    ordered_display = []
    for n in display_names:
        if n not in seen:
            seen.add(n)
            ordered_display.append(n)

    code_names = _collect_code_files(code_dir)
    r_packages = _extract_r_packages_from_code(code_dir, code_names)
    all_names = ordered_display + code_names
    fp = _file_fingerprint(code_dir, all_names)

    if meta_path.exists():
        try:
            old = read_json(meta_path)
            old_zip = old.get("zip_path")
            if old.get("fingerprint") == fp and isinstance(old_zip, str) and Path(old_zip).exists():
                return old
        except Exception:
            pass

    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    zip_path = exports_dir / f"experiment_{expid}_display_data_{ts}.zip"
    manifest = _build_display_zip_manifest(expid, ordered_display, code_names, r_packages)

    # Persist manifest in project folder as requested.
    manifest_disk_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ordered_display:
            try:
                p = _safe_output_file_path(code_dir, name)
                if p.exists() and p.is_file():
                    zf.write(str(p), arcname=f"display/{name}")
            except Exception:
                continue
        for name in code_names:
            try:
                p = _safe_output_file_path(code_dir, name)
                if p.exists() and p.is_file():
                    zf.write(str(p), arcname=f"code/{name}")
            except Exception:
                continue
        zf.writestr("manifest/program_data_bundle_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    out = {
        "experiment_id": expid,
        "fingerprint": fp,
        "zip_path": str(zip_path),
        "zip_name": zip_path.name,
        "display_count": len(ordered_display),
        "code_count": len(code_names),
        "r_packages_count": len(r_packages),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    meta_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _select_display_files_with_model(data_dir: Path, generated_files: list[str]) -> tuple[list[str], str]:
    """
    Pick a user-facing subset of generated files.
    Uses cached model result keyed by file-list fingerprint to avoid repeated token cost.
    """
    cache_path = data_dir / "program_display_files_cache.json"
    fp = _generated_files_fingerprint(generated_files)
    if cache_path.exists():
        try:
            cache = read_json(cache_path)
            if cache.get("fingerprint") == fp and isinstance(cache.get("display_files"), list):
                return cache["display_files"], "cache_hit"
        except Exception:
            pass

    # Fallback if model call fails.
    fallback = _heuristic_recommended_files(generated_files)

    prompt = (
        "You are selecting which generated analysis files should be shown to end users in a biomedical app.\n"
        "Given a list of filenames, return only the most meaningful result files for users to view/download.\n"
        "Prefer final reports/tables/figures; avoid temporary or noisy files.\n"
        "Return JSON only with this schema:\n"
        "{\"display_files\": [\"file1\", \"file2\"]}\n\n"
        "Filenames:\n" + "\n".join(f"- {x}" for x in generated_files)
    )
    try:
        raw, _, _ = model_generate(prompt, model=MODEL_PRECISE, temperature=0.1)
        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            l = raw.find("{")
            r = raw.rfind("}")
            if l != -1 and r != -1 and r > l:
                parsed = json.loads(raw[l:r + 1])
        chosen = parsed.get("display_files", []) if isinstance(parsed, dict) else []
        chosen = [x for x in chosen if isinstance(x, str) and x in generated_files]
        if not chosen:
            chosen = fallback
        result = chosen[:24]
        cache_path.write_text(
            json.dumps(
                {
                    "fingerprint": fp,
                    "display_files": result,
                    "generated_files_count": len(generated_files),
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return result, "model"
    except Exception:
        cache_path.write_text(
            json.dumps(
                {
                    "fingerprint": fp,
                    "display_files": fallback,
                    "generated_files_count": len(generated_files),
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "mode": "heuristic_fallback",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return fallback, "heuristic"


def _select_display_items_with_model(data_dir: Path, code_dir: Path, generated_files: list[str]) -> tuple[list[dict], str]:
    cache_path = data_dir / "program_display_items_cache.json"
    meta_lines = []
    for name in generated_files:
        try:
            p = _safe_output_file_path(code_dir, name)
            st = p.stat()
            meta_lines.append(f"{name}|size={st.st_size}|mtime={int(st.st_mtime)}|kind={_infer_render_type(name)}")
        except Exception:
            meta_lines.append(f"{name}|missing=1|kind={_infer_render_type(name)}")
    fp = hashlib.md5("\n".join(meta_lines).encode("utf-8")).hexdigest()

    if cache_path.exists():
        try:
            cache = read_json(cache_path)
            if cache.get("fingerprint") == fp and isinstance(cache.get("display_items"), list):
                return cache["display_items"], "cache_hit"
        except Exception:
            pass

    fallback_files = _heuristic_recommended_files(generated_files, limit=16)
    fallback_items = []
    for name in fallback_files:
        it = _build_file_preview(code_dir, name)
        it["show_reason"] = "heuristic fallback"
        fallback_items.append(it)

    prompt = (
        "You are deciding which generated output files should be shown to users and how.\n"
        "For each filename, decide show=true/false and one render_type from: table,text,json,image,download.\n"
        "Prefer files that represent final results, summaries, tables, figures.\n"
        "Avoid tmp/intermediate/noisy files unless necessary.\n"
        "Return strict JSON: {\"items\":[{\"name\":\"...\",\"show\":true,\"render_type\":\"table\",\"reason\":\"...\"}]}\n\n"
        "Files:\n" + "\n".join(f"- {x}" for x in meta_lines)
    )
    try:
        raw, _, _ = model_generate(prompt, model=MODEL_PRECISE, temperature=0.1)
        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            l = raw.find("{")
            r = raw.rfind("}")
            if l != -1 and r != -1 and r > l:
                parsed = json.loads(raw[l:r + 1])
        picks = parsed.get("items", []) if isinstance(parsed, dict) else []
        chosen = []
        for x in picks:
            if not isinstance(x, dict):
                continue
            name = x.get("name")
            if not isinstance(name, str) or name not in generated_files:
                continue
            if not bool(x.get("show", False)):
                continue
            it = _build_file_preview(code_dir, name)
            rt = str(x.get("render_type", "")).strip().lower()
            if rt in {"table", "text", "json", "image", "download"}:
                it["render_type"] = rt
            it["show_reason"] = str(x.get("reason", ""))[:240]
            chosen.append(it)
        if not chosen:
            chosen = fallback_items
            mode = "heuristic"
        else:
            mode = "model"
        out = chosen[:16]
        cache_path.write_text(
            json.dumps(
                {
                    "fingerprint": fp,
                    "display_items": out,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return out, mode
    except Exception:
        cache_path.write_text(
            json.dumps(
                {
                    "fingerprint": fp,
                    "display_items": fallback_items,
                    "mode": "heuristic",
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return fallback_items, "heuristic"


@router.post("/{id}/program/regenerate")
async def regenerate_program(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    _reject_example_regeneration(id)
    status_now = _read_runtime_status(id)
    if status_now.get("checkpoint") == "coding_failed_final":
        raise HTTPException(
            status_code=422,
            detail={
                "project_failed": True,
                "message": "项目已被标记为失败，请重新开始项目流程。",
            },
        )
    _write_runtime_status(
        id,
        running=True,
        progress=90,
        checkpoint="coding_regenerate_start",
        message="Regenerating coding output...",
        error=None,
    )
    try:
        result = regenerate_program_with_codex(id, user_feedback="", is_feedback_retry=False)
        data_dir = Path(__file__).parent.parent / "data" / str(id)
        code_dir = data_dir / "coding3"
        if code_dir.exists():
            generated_files = sorted([p.name for p in code_dir.iterdir() if p.is_file()])
            display_files = _heuristic_recommended_files(generated_files)
            display_items = []
            for name in _heuristic_recommended_files(generated_files, limit=16):
                it = _build_file_preview(code_dir, name)
                it["show_reason"] = "auto-zip after regenerate"
                display_items.append(it)
            _ensure_display_data_zip(id, data_dir, code_dir, display_files, display_items)
        _write_runtime_status(
            id,
            running=False,
            progress=98,
            checkpoint="coding_regenerate_done",
            message="Coding regeneration completed.",
            error=None,
            needs_user_feedback=False,
            failed_task_id=None,
        )
        return result
    except CodingNeedsFeedbackError as e:
        _write_runtime_status(
            id,
            running=False,
            progress=95,
            checkpoint="coding_wait_user_feedback",
            message="Coding paused: user feedback is required before retry.",
            error=str(e),
            needs_user_feedback=True,
            failed_task_id=e.task_id,
        )
        raise HTTPException(
            status_code=409,
            detail={
                "needs_user_feedback": True,
                "message": "代码执行在任务级升级链后仍失败。请补充你的思路后重试一次。",
                "failed_task_id": e.task_id,
                "diagnostic": str(e),
                "next_action": "POST /api/{id}/program/regenerate-with-feedback",
            },
        )
    except CodingFinalFailureError as e:
        _write_runtime_status(
            id,
            running=False,
            progress=100,
            checkpoint="coding_failed_final",
            message="Coding failed after user-feedback retry. Please restart the project.",
            error=str(e),
            needs_user_feedback=False,
            failed_task_id=e.task_id,
        )
        raise HTTPException(
            status_code=422,
            detail={
                "project_failed": True,
                "message": "项目在用户反馈后二次尝试仍失败，请重新开始项目流程。",
                "failed_task_id": e.task_id,
                "diagnostic": str(e),
            },
        )
    except FileNotFoundError as e:
        _write_runtime_status(
            id,
            running=False,
            checkpoint="coding_regenerate_error",
            message="Coding regeneration failed.",
            error=str(e),
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _write_runtime_status(
            id,
            running=False,
            checkpoint="coding_regenerate_error",
            message="Coding regeneration failed.",
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Regenerate failed: {str(e)}")


@router.post("/{id}/program/regenerate-with-feedback")
async def regenerate_program_with_feedback(id: int, payload: CodingFeedbackPayload, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    _reject_example_regeneration(id)
    status_now = _read_runtime_status(id)
    if status_now.get("checkpoint") == "coding_failed_final":
        raise HTTPException(
            status_code=422,
            detail={
                "project_failed": True,
                "message": "项目已被标记为失败，请重新开始项目流程。",
            },
        )
    feedback = (payload.feedback or "").strip()
    if not feedback:
        raise HTTPException(status_code=400, detail="feedback is required.")
    _write_runtime_status(
        id,
        running=True,
        progress=96,
        checkpoint="coding_feedback_retry_start",
        message="Retrying coding with user feedback...",
        error=None,
        needs_user_feedback=False,
    )
    try:
        result = regenerate_program_with_codex(id, user_feedback=feedback, is_feedback_retry=True)
        data_dir = Path(__file__).parent.parent / "data" / str(id)
        code_dir = data_dir / "coding3"
        if code_dir.exists():
            generated_files = sorted([p.name for p in code_dir.iterdir() if p.is_file()])
            display_files = _heuristic_recommended_files(generated_files)
            display_items = []
            for name in _heuristic_recommended_files(generated_files, limit=16):
                it = _build_file_preview(code_dir, name)
                it["show_reason"] = "auto-zip after feedback regenerate"
                display_items.append(it)
            _ensure_display_data_zip(id, data_dir, code_dir, display_files, display_items)
        _write_runtime_status(
            id,
            running=False,
            progress=98,
            checkpoint="coding_regenerate_done",
            message="Coding regeneration completed after user feedback.",
            error=None,
            needs_user_feedback=False,
            failed_task_id=None,
        )
        return result
    except CodingFinalFailureError as e:
        _write_runtime_status(
            id,
            running=False,
            progress=100,
            checkpoint="coding_failed_final",
            message="Coding failed after user-feedback retry. Please restart the project.",
            error=str(e),
            needs_user_feedback=False,
            failed_task_id=e.task_id,
        )
        raise HTTPException(
            status_code=422,
            detail={
                "project_failed": True,
                "message": "项目在用户反馈后二次尝试仍失败，请重新开始项目流程。",
                "failed_task_id": e.task_id,
                "diagnostic": str(e),
            },
        )
    except Exception as e:
        _write_runtime_status(
            id,
            running=False,
            checkpoint="coding_feedback_retry_error",
            message="Coding feedback retry failed.",
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Feedback retry failed: {str(e)}")


def regenerate_program_with_codex(id: int, user_feedback: str = "", is_feedback_retry: bool = False):
    data_dir = Path(__file__).parent.parent / "data" / str(id)
    if not data_dir.exists():
        raise FileNotFoundError(f"Experiment folder not found: {data_dir}")

    dry_path = data_dir / "dry_experiment3.json"
    if not dry_path.exists():
        raise FileNotFoundError(f"Dry experiment file not found: {dry_path}")

    dry_experiment = read_json(dry_path)
    code_result_log_path = data_dir / "coding3.log"
    code_save_dir = data_dir / "coding3"
    code_save_dir.mkdir(parents=True, exist_ok=True)

    def _on_coding_progress(stage: str, payload: dict):
        task_id = payload.get("task_id")
        if stage == "planning_start":
            _write_runtime_status(
                id,
                running=True,
                progress=90,
                checkpoint="coding_planning_start",
                message="Planning overall coding workflow with gpt-5.2-thinking...",
                error=None,
            )
        elif stage == "preflight_start":
            _write_runtime_status(
                id,
                running=True,
                progress=89,
                checkpoint="coding_preflight_start",
                message="Preflight checking task input files...",
                error=None,
            )
        elif stage == "preflight_done":
            _write_runtime_status(
                id,
                running=True,
                progress=90,
                checkpoint="coding_preflight_done",
                message="Task input preflight done. Building global plan...",
                error=None,
            )
        elif stage == "preflight_blocked":
            missing = payload.get("missing_tasks", [])
            msg = "Coding preflight blocked: missing input files."
            if missing:
                msg = f"Coding preflight blocked for tasks: {', '.join(missing)}"
            _write_runtime_status(
                id,
                running=False,
                progress=90,
                checkpoint="coding_preflight_blocked",
                message=msg,
                error=msg,
            )
        elif stage == "planning_done":
            _write_runtime_status(
                id,
                running=True,
                progress=91,
                checkpoint="coding_planning_done",
                message="Global coding plan is ready. Starting execution with gpt-5.2-codex...",
                error=None,
            )
        elif stage == "task_start":
            _write_runtime_status(
                id,
                running=True,
                progress=92,
                checkpoint="coding_task_start",
                message=f"Preparing task: {task_id}",
                error=None,
            )
        elif stage == "primary_execute_start":
            _write_runtime_status(
                id,
                running=True,
                progress=93,
                checkpoint="coding_primary_execute_start",
                message=f"Generating and executing code with gpt-5.2-codex: {task_id}",
                error=None,
            )
        elif stage == "diag_5_2_thinking_start":
            _write_runtime_status(
                id,
                running=True,
                progress=94,
                checkpoint="coding_retry_diag_5_2_thinking",
                message=f"Second-level diagnosis with gpt-5.2-thinking: {task_id}",
                error=None,
            )
        elif stage == "execute_5_3_codex_start":
            _write_runtime_status(
                id,
                running=True,
                progress=96,
                checkpoint="coding_retry_execute_5_3_codex",
                message=f"Escalated execution with gpt-5.3-codex: {task_id}",
                error=None,
            )
        elif stage == "task_success":
            _write_runtime_status(
                id,
                running=True,
                progress=97,
                checkpoint="coding_task_done",
                message=f"Task completed: {task_id}",
                error=None,
            )
        elif stage == "task_failed_final":
            _write_runtime_status(
                id,
                running=True,
                progress=97,
                checkpoint="coding_task_failed_final_chain",
                message=f"Escalation chain failed for task: {task_id}",
                error=None,
            )

    result = code_generator(
        dry_experiment,
        str(code_result_log_path),
        str(code_save_dir),
        model=MODEL_CODEX,
        user_feedback=user_feedback,
        is_feedback_retry=is_feedback_retry,
        progress_callback=_on_coding_progress,
    )
    return {
        "message": "Code regenerated with chain: 5.2-thinking planning -> 5.2-codex execution -> 5.2-thinking diagnosis -> 5.3-codex retry.",
        "input_tokens": result[1],
        "output_tokens": result[2],
        "code_dir": str(code_save_dir),
    }


@router.get("/{id}/program/meta")
async def get_program_meta(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    data_dir = Path(__file__).parent.parent / "data" / str(id)
    log_path = data_dir / "coding3.log"
    dry_path = data_dir / "dry_experiment3.json"
    code_dir = data_dir / "coding3"
    all_task_ids = _load_task_ids_from_dry(dry_path)
    generated_files = []
    if code_dir.exists():
        generated_files = sorted([p.name for p in code_dir.iterdir() if p.is_file()])
    if int(id) == int(EXAMPLE_PROJECT_ID):
        display_files = _heuristic_recommended_files(generated_files)
        display_mode = "example_static"
        display_items = []
        picked = _heuristic_recommended_files(generated_files, limit=16)
        image_files = [n for n in generated_files if _infer_render_type(n) == "image" and not _is_display_excluded(n)]
        for img in image_files:
            if img not in picked:
                picked.append(img)
        for name in picked[:24]:
            it = _build_file_preview(code_dir, name)
            it["show_reason"] = "example static view"
            display_items.append(it)
        display_items_mode = "example_static"
    else:
        display_files, display_mode = _select_display_files_with_model(data_dir, generated_files)
        display_items, display_items_mode = _select_display_items_with_model(data_dir, code_dir, generated_files)
    display_files = [x for x in (display_files or []) if not _is_display_excluded(x)]
    display_items = [
        x for x in (display_items or [])
        if isinstance(x, dict) and not _is_display_excluded(str(x.get("name", "")))
    ]
    zip_meta = {}
    if code_dir.exists():
        try:
            zip_meta = _ensure_display_data_zip(id, data_dir, code_dir, display_files, display_items)
        except Exception:
            zip_meta = {}
    if not log_path.exists():
        return {
            "global_plan": None,
            "message": "coding3.log not found",
            "task_progress": {
                "total_tasks": len(all_task_ids),
                "completed_tasks": 0,
                "failed_tasks": 0,
                "remaining_tasks": len(all_task_ids),
                "completed_task_ids": [],
                "failed_task_ids": [],
                "pending_task_ids": all_task_ids,
            },
            "generated_files": generated_files,
            "display_files": display_files,
            "display_files_mode": display_mode,
            "display_items": display_items,
            "display_items_mode": display_items_mode,
            "data_zip": zip_meta,
        }
    try:
        payload = read_json(log_path)
        gp = payload.get("global_plan", None) if isinstance(payload, dict) else None
        completed, failed = _collect_task_progress_from_log(payload if isinstance(payload, dict) else {})
        completed_ordered = [x for x in all_task_ids if x in completed]
        failed_ordered = [x for x in all_task_ids if x in failed]
        pending = [x for x in all_task_ids if x not in completed and x not in failed]
        total_tasks = len(all_task_ids)
        # Keep runtime_status consistent with coding completion even if other routes wrote stale checkpoints.
        if total_tasks > 0 and len(pending) == 0 and len(failed) == 0:
            _write_runtime_status(
                id,
                running=False,
                progress=98,
                checkpoint="coding_regenerate_done",
                message="Coding regeneration completed.",
                error=None,
                needs_user_feedback=False,
                failed_task_id=None,
            )
        return {
            "global_plan": gp,
            "task_progress": {
                "total_tasks": total_tasks,
                "completed_tasks": len(completed),
                "failed_tasks": len(failed),
                "remaining_tasks": len(pending),
                "completed_task_ids": completed_ordered,
                "failed_task_ids": failed_ordered,
                "pending_task_ids": pending,
            },
            "generated_files": generated_files,
            "display_files": display_files,
            "display_files_mode": display_mode,
            "display_items": display_items,
            "display_items_mode": display_items_mode,
            "data_zip": zip_meta,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read coding metadata: {str(e)}")


@router.get("/{id}/program/output-file")
async def get_program_output_file(id: int, name: str, authorization: str | None = Header(default=None)):
    # Browser <img src> / <a href> requests do not carry Authorization headers.
    # Keep strict auth for normal projects, but allow read-only direct access for Example demo assets.
    if int(id) != int(EXAMPLE_PROJECT_ID):
        user = require_user(authorization)
        ensure_project_access(user, id)
    data_dir = Path(__file__).parent.parent / "data" / str(id)
    code_dir = data_dir / "coding3"
    if not code_dir.exists():
        raise HTTPException(status_code=404, detail="coding3 folder not found")
    try:
        p = _safe_output_file_path(code_dir, name)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid file path")
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    mt, _ = mimetypes.guess_type(str(p))
    return FileResponse(path=str(p), filename=p.name, media_type=mt or "application/octet-stream")


@router.get("/{id}/program/download-data-zip")
async def download_data_zip(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    data_dir = Path(__file__).parent.parent / "data" / str(id)
    if not data_dir.exists() or not data_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Experiment folder not found: {data_dir}")
    code_dir = data_dir / "coding3"
    if not code_dir.exists():
        raise HTTPException(status_code=404, detail="coding3 folder not found")

    meta_path = data_dir / "program_data_zip_meta.json"
    zip_path = None
    zip_name = None
    if meta_path.exists():
        try:
            meta = read_json(meta_path)
            p = meta.get("zip_path")
            if isinstance(p, str) and Path(p).exists():
                zip_path = p
                zip_name = meta.get("zip_name")
        except Exception:
            pass

    if zip_path is None:
        generated_files = sorted([p.name for p in code_dir.iterdir() if p.is_file()])
        display_files = _heuristic_recommended_files(generated_files)
        display_items = []
        for name in _heuristic_recommended_files(generated_files, limit=16):
            it = _build_file_preview(code_dir, name)
            it["show_reason"] = "auto-zip fallback"
            display_items.append(it)
        meta = _ensure_display_data_zip(id, data_dir, code_dir, display_files, display_items)
        zip_path = meta.get("zip_path")
        zip_name = meta.get("zip_name")
        if not zip_path or not Path(zip_path).exists():
            raise HTTPException(status_code=500, detail="Failed to build data zip")

    filename = zip_name or Path(zip_path).name
    return FileResponse(
        path=zip_path,
        filename=filename,
        media_type="application/zip",
    )
