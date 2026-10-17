"""Model configuration and hot-swap endpoints."""

from __future__ import annotations

import asyncio
import fnmatch
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import db_service
from model_profiles import TTS_PROFILES, get_tts_profile
from utils import LLM, STT, normalize_tts_backend, resolve_local_model_source

logger = logging.getLogger(__name__)
router = APIRouter()

HF_DOWNLOAD_EXCLUDES = (
    "*.mp4",
    "*.mov",
    "*.webm",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
)


def _is_downloadable_model_file(filename: str) -> bool:
    return not any(fnmatch.fnmatch(filename, pattern) for pattern in HF_DOWNLOAD_EXCLUDES)


def _format_bytes(count: int) -> str:
    units = ("B", "KB", "MB", "GB")
    size = float(max(count, 0))
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def _hf_repo_cache_dir(repo_id: str) -> Path:
    try:
        from huggingface_hub.constants import HF_HUB_CACHE
    except Exception:
        HF_HUB_CACHE = os.path.expanduser("~/.cache/huggingface/hub")
    return Path(HF_HUB_CACHE) / f"models--{repo_id.replace('/', '--')}"


def _hf_blob_downloaded_bytes(repo_id: str, sibling: Any) -> int:
    blob_name = None
    lfs = getattr(sibling, "lfs", None)
    if lfs is not None:
        blob_name = getattr(lfs, "sha256", None)
    blob_name = blob_name or getattr(sibling, "blob_id", None)
    if not blob_name:
        return 0

    blobs = _hf_repo_cache_dir(repo_id) / "blobs"
    candidates = (blobs / blob_name, blobs / f"{blob_name}.incomplete")
    sizes = []
    for path in candidates:
        try:
            if path.exists():
                sizes.append(path.stat().st_size)
        except OSError:
            pass
    return max(sizes, default=0)


async def _download_hf_file_with_progress(repo_id: str, sibling: Any, *, downloaded_before: int, total_bytes: int):
    from huggingface_hub import hf_hub_download

    filename = sibling.rfilename
    expected_size = int(getattr(sibling, "size", 0) or 0)
    task = asyncio.create_task(
        asyncio.to_thread(
            lambda: hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_files_only=False,
            )
        )
    )

    last_seen = -1
    while not task.done():
        current = _hf_blob_downloaded_bytes(repo_id, sibling)
        if expected_size > 0:
            current = min(current, expected_size)
        if current != last_seen:
            last_seen = current
            overall = downloaded_before + current
            progress = overall / total_bytes if total_bytes > 0 else 0.0
            detail = (
                f"{_format_bytes(current)} / {_format_bytes(expected_size)}"
                if expected_size > 0
                else _format_bytes(current)
            )
            yield {
                "stage": "downloading",
                "progress": min(0.99, progress),
                "message": f"Downloading {filename} ({detail})",
            }
        await asyncio.sleep(0.5)

    await task


def _hf_file_is_cached(repo_id: str, filename: str) -> bool:
    try:
        from huggingface_hub import hf_hub_download

        hf_hub_download(repo_id=repo_id, filename=filename, local_files_only=True)
        return True
    except Exception:
        return False


@router.get("/models")
async def get_models(request: Request):
    pipeline = getattr(request.app.state, "pipeline", None)
    tts_backend = normalize_tts_backend(
        getattr(pipeline, "tts_backend", None)
        or db_service.db_service.get_setting("tts_backend")
        or "qwen3-tts"
    )
    tts_repo = None
    if pipeline and getattr(pipeline, "tts", None):
        tts_repo = getattr(pipeline.tts, "model_id", None)
    return {
        "llm": {
            "backend": "mlx",
            "repo": db_service.db_service.get_setting("llm_model") or LLM,
            "file": None,
            "context_window": 4096,
            "loaded": pipeline is not None and pipeline.llm is not None,
        },
        "tts": {
            "backend": tts_backend,
            "options": [
                {
                    "id": p.id,
                    "name": p.label,
                    "ramGb": p.ram_gb,
                    "diskGb": p.disk_gb,
                    "quality": p.quality,
                    "note": p.note,
                }
                for p in TTS_PROFILES
            ],
            "backbone_repo": tts_repo,
            "codec_repo": None,
            "loaded": pipeline is not None and pipeline.tts is not None,
        },
        "stt": {
            "backend": "whisper",
            "repo": STT,
            "loaded": pipeline is not None and pipeline.stt is not None,
        },
    }


class ModelsUpdate(BaseModel):
    model_repo: Optional[str] = None


@router.put("/models")
async def set_models(request: Request, body: ModelsUpdate):
    if body.model_repo:
        db_service.db_service.set_setting("llm_model", body.model_repo)
    return await get_models(request)


class ModelSwitchRequest(BaseModel):
    model_repo: str


@router.post("/models/switch")
async def switch_model(request: Request, body: ModelSwitchRequest):
    """Download a new LLM and hot-swap it. Returns newline-delimited JSON progress."""
    import mlx.core as mx

    pipeline = getattr(request.app.state, "pipeline", None)
    model_repo = body.model_repo.strip()
    if not model_repo:
        raise HTTPException(status_code=400, detail="model_repo is required")

    async def generate_progress():
        try:
            yield json.dumps({"stage": "downloading", "progress": 0.0, "message": f"Starting download of {model_repo}..."}) + "\n"

            from huggingface_hub import HfApi, snapshot_download
            from huggingface_hub.constants import HF_HUB_CACHE
            import threading

            download_complete = threading.Event()
            download_error = [None]
            download_path = [None]
            start_time = [asyncio.get_event_loop().time()]
            expected_total_bytes = [None]
            baseline_bytes = [0]
            last_bytes = [0]
            last_change_monotonic = [time.monotonic()]

            def _repo_cache_dir() -> str:
                return os.path.join(str(HF_HUB_CACHE), f"models--{model_repo.replace('/', '--')}")

            def _cache_bytes(base_dir: str) -> int:
                # blobs only: everything under snapshots/ is a symlink back into
                # blobs/, so walking both counts every finished file twice.
                total = 0
                d = os.path.join(base_dir, "blobs")
                if os.path.isdir(d):
                    for root, _, files in os.walk(d):
                        for fn in files:
                            try:
                                total += os.lstat(os.path.join(root, fn)).st_size
                            except Exception:
                                pass
                return total

            def _xet_cache_bytes() -> int:
                try:
                    hub_cache = str(HF_HUB_CACHE)
                    root = os.path.dirname(hub_cache)
                    candidates = [os.path.join(root, "xet"), os.path.join(root, "xet-cache")]
                    for env_key in ("HF_XET_CACHE", "XET_CACHE_DIR", "XET_HOME"):
                        v = os.environ.get(env_key)
                        if v and v.strip():
                            candidates.insert(0, v.strip())
                    total = 0
                    for d in candidates:
                        if not d or not os.path.isdir(d):
                            continue
                        for rd, _, files in os.walk(d):
                            for fn in files:
                                try:
                                    total += os.stat(os.path.join(rd, fn)).st_size
                                except Exception:
                                    pass
                    return total
                except Exception:
                    return 0

            def _downloaded_bytes() -> int:
                # The repo cache belongs to this download alone, so its bytes are the
                # progress outright -- that is what lets a resumed download pick up at
                # the percentage it stopped at instead of restarting the bar at 0.
                # Only the xet cache is shared across repos, so it gets a baseline.
                return _cache_bytes(_repo_cache_dir()) + max(0, _xet_cache_bytes() - baseline_bytes[0])

            def _compute_expected_total() -> int | None:
                try:
                    info = HfApi().model_info(model_repo, files_metadata=True)
                    total = sum(
                        getattr(s, "size", 0) or 0
                        for s in (getattr(info, "siblings", None) or [])
                        if isinstance(getattr(s, "size", None), int)
                    )
                    return total or None
                except Exception:
                    return None

            def download_model():
                try:
                    expected_total_bytes[0] = _compute_expected_total()
                    download_path[0] = snapshot_download(
                        repo_id=model_repo, local_files_only=False, max_workers=4,
                    )
                except Exception as e:
                    download_error[0] = str(e)
                finally:
                    download_complete.set()

            baseline_bytes[0] = _xet_cache_bytes()
            download_thread = threading.Thread(target=download_model)
            download_thread.start()

            stall_seconds = 300
            while not download_complete.is_set():
                await asyncio.sleep(1.0)
                elapsed = asyncio.get_event_loop().time() - start_time[0]
                current_bytes = _downloaded_bytes()
                if current_bytes != last_bytes[0]:
                    last_bytes[0] = current_bytes
                    last_change_monotonic[0] = time.monotonic()
                elif time.monotonic() - last_change_monotonic[0] > stall_seconds:
                    yield json.dumps({"stage": "error", "error": "Download stalled for 5 minutes. Retry."}) + "\n"
                    return

                if isinstance(expected_total_bytes[0], int) and expected_total_bytes[0] > 0:
                    progress = min(0.99, current_bytes / expected_total_bytes[0])
                else:
                    progress = min(0.95, 1.0 - (1.0 / (1.0 + elapsed / 10.0)))

                gb = current_bytes / (1024 ** 3)
                if elapsed > 30:
                    mins, secs = int(elapsed // 60), int(elapsed % 60)
                    time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
                    if isinstance(expected_total_bytes[0], int) and expected_total_bytes[0] > 0:
                        msg = f"Downloading {model_repo}... ({gb:.2f}/{expected_total_bytes[0]/(1024**3):.2f} GB, {time_str})"
                    else:
                        msg = f"Downloading {model_repo}... ({gb:.2f} GB, {time_str})"
                else:
                    msg = f"Downloading {model_repo}... ({gb:.2f} GB)"
                yield json.dumps({"stage": "downloading", "progress": progress, "message": msg}) + "\n"

            download_thread.join()
            if download_error[0]:
                yield json.dumps({"stage": "error", "error": f"Download failed: {download_error[0]}"}) + "\n"
                return

            yield json.dumps({"stage": "downloading", "progress": 1.0, "message": "Download complete!"}) + "\n"
            yield json.dumps({"stage": "loading", "progress": 0.0, "message": "Loading model weights..."}) + "\n"

            try:
                # The pipeline is built lazily on the first chat session, so a switch
                # made before that has nothing to hot-swap. Record the choice and let
                # the pipeline pick it up when it starts, rather than failing after a
                # multi-gigabyte download. app.state carries the value that
                # ensure_voice_pipeline() actually reads, so it has to move too.
                if not pipeline:
                    db_service.db_service.set_setting("llm_model", model_repo)
                    request.app.state.llm_model = model_repo
                    yield json.dumps({
                        "stage": "loading", "progress": 1.0,
                        "message": "Model downloaded. It loads when you start a session.",
                    }) + "\n"
                    yield json.dumps({
                        "stage": "complete", "progress": 1.0,
                        "message": f"Switched to {model_repo}",
                    }) + "\n"
                    return

                new_llm, new_tokenizer, new_backend = await pipeline.load_llm_backend(model_repo)
                yield json.dumps({"stage": "loading", "progress": 0.5, "message": "Model loaded, swapping..."}) + "\n"

                async with pipeline.llm_lock:
                    old_llm, old_tok = pipeline.llm, pipeline.tokenizer
                    pipeline.llm = new_llm
                    pipeline.tokenizer = new_tokenizer
                    pipeline.llm_model = model_repo
                    pipeline.llm_backend = new_backend
                    del old_llm, old_tok
                    mx.metal.clear_cache()

                db_service.db_service.set_setting("llm_model", model_repo)
                yield json.dumps({"stage": "loading", "progress": 1.0, "message": "Model weights loaded!"}) + "\n"
                yield json.dumps({"stage": "complete", "progress": 1.0, "message": f"Switched to {model_repo}"}) + "\n"
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                yield json.dumps({"stage": "error", "error": f"Failed to load model: {e}"}) + "\n"
        except Exception as e:
            logger.error(f"Model switch failed: {e}")
            yield json.dumps({"stage": "error", "error": str(e)}) + "\n"

    return StreamingResponse(
        generate_progress(), media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class TtsSwitchRequest(BaseModel):
    tts_backend: str


@router.post("/models/switch-tts")
async def switch_tts_model(request: Request, body: TtsSwitchRequest):
    """Download TTS weights and hot-swap the TTS backend."""
    pipeline = getattr(request.app.state, "pipeline", None)
    normalized_backend = normalize_tts_backend(body.tts_backend)
    target_repo = get_tts_profile(normalized_backend).repo

    async def generate_progress():
        try:
            yield json.dumps({"stage": "downloading", "progress": 0.0, "message": f"Checking {normalized_backend} cache..."}) + "\n"

            local_source = await asyncio.to_thread(lambda: resolve_local_model_source(target_repo))
            if os.path.isdir(local_source):
                yield json.dumps({
                    "stage": "downloading",
                    "progress": 1.0,
                    "message": f"Found cached {normalized_backend}. No download needed.",
                }) + "\n"
            else:
                from huggingface_hub import HfApi

                try:
                    info = await asyncio.to_thread(
                        lambda: HfApi().model_info(target_repo, files_metadata=True)
                    )
                    siblings = [
                        sibling
                        for sibling in info.siblings
                        if _is_downloadable_model_file(getattr(sibling, "rfilename", ""))
                    ]
                    total_bytes = sum(
                        int(getattr(sibling, "size", 0) or 0)
                        for sibling in siblings
                    )
                    downloaded_bytes = 0
                    file_count = len(siblings)

                    for index, sibling in enumerate(siblings, start=1):
                        filename = sibling.rfilename
                        size = int(getattr(sibling, "size", 0) or 0)
                        if await asyncio.to_thread(lambda filename=filename: _hf_file_is_cached(target_repo, filename)):
                            downloaded_bytes += size
                            progress = (
                                downloaded_bytes / total_bytes
                                if total_bytes > 0
                                else index / max(file_count, 1)
                            )
                            yield json.dumps({
                                "stage": "downloading",
                                "progress": min(1.0, progress),
                                "message": f"Using cached {filename} ({index}/{file_count})",
                            }) + "\n"
                            continue

                        baseline = (
                            downloaded_bytes / total_bytes
                            if total_bytes > 0
                            else (index - 1) / max(file_count, 1)
                        )
                        yield json.dumps({
                            "stage": "downloading",
                            "progress": min(0.99, baseline),
                            "message": f"Downloading missing file {filename} ({index}/{file_count})...",
                        }) + "\n"
                        async for update in _download_hf_file_with_progress(
                            target_repo,
                            sibling,
                            downloaded_before=downloaded_bytes,
                            total_bytes=total_bytes,
                        ):
                            yield json.dumps(update) + "\n"
                        downloaded_bytes += size
                        progress = (
                            downloaded_bytes / total_bytes
                            if total_bytes > 0
                            else index / max(file_count, 1)
                        )
                        detail = (
                            f"{_format_bytes(downloaded_bytes)} / {_format_bytes(total_bytes)}"
                            if total_bytes > 0
                            else f"{index}/{file_count} files"
                        )
                        yield json.dumps({
                            "stage": "downloading",
                            "progress": min(1.0, progress),
                            "message": f"Downloaded {filename} ({detail})",
                        }) + "\n"
                except Exception as e:
                    yield json.dumps({"stage": "error", "error": f"Download failed: {e}"}) + "\n"
                    return

                yield json.dumps({"stage": "downloading", "progress": 1.0, "message": "Download complete!"}) + "\n"
            yield json.dumps({"stage": "loading", "progress": 0.0, "message": "Loading TTS weights..."}) + "\n"

            # Same as the LLM switch: with no pipeline yet, persist and move on.
            if not pipeline:
                db_service.db_service.set_setting("tts_backend", normalized_backend)
                request.app.state.tts_backend = normalized_backend
                yield json.dumps({
                    "stage": "complete", "progress": 1.0,
                    "message": f"Switched to {normalized_backend}",
                }) + "\n"
                return
            try:
                await pipeline.set_tts_backend(normalized_backend)
                db_service.db_service.set_setting("tts_backend", normalized_backend)
                request.app.state.tts_backend = normalized_backend
            except Exception as e:
                logger.error(f"Failed to switch TTS backend: {e}")
                yield json.dumps({"stage": "error", "error": f"Failed to switch TTS backend: {e}"}) + "\n"
                return

            yield json.dumps({"stage": "loading", "progress": 1.0, "message": "TTS weights loaded!"}) + "\n"
            yield json.dumps({"stage": "complete", "progress": 1.0, "message": f"Switched to {normalized_backend}"}) + "\n"
        except Exception as e:
            logger.error(f"TTS switch failed: {e}")
            yield json.dumps({"stage": "error", "error": str(e)}) + "\n"

    return StreamingResponse(
        generate_progress(), media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
