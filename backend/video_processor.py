"""
FoodVerse AI — Video Frame Extraction Service
Smart Bridge Milestone 4, Activity 4.1

Provides reusable, safe OpenCV-based video ingestion and frame extraction for
restaurant/kitchen hygiene analysis.

Responsibilities:
  1. Validate file size and supported content types.
  2. Decode video from raw bytes via a temporary in-memory path (cv2.VideoCapture
     from a numpy byte array) — no permanent disk writes.
  3. Extract representative frames at a configurable interval.
  4. Enforce a maximum frame count to limit API cost.
  5. Resize frames preserving aspect ratio.
  6. Release VideoCapture resources safely even on error.
  7. Return frames as PIL Images with associated timestamps.

Limitations:
  - OpenCV VideoCapture from memory bytes requires writing to a temp file on
    Windows because cv2.imdecode only handles single images, not video streams.
    The temp file is deleted immediately after capture is released.
  - Duration and frame-count accuracy depend on the codec and container metadata
    reported by OpenCV; values may be approximate for VBR/damaged files.
  - No permanent storage of uploaded videos or extracted frames.
"""

from __future__ import annotations

import os
import tempfile
from typing import List, Tuple

import cv2
import numpy as np
from fastapi import HTTPException
from PIL import Image

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_VIDEO_BYTES     = 50 * 1024 * 1024   # 50 MB hard limit
MAX_VIDEO_SECONDS   = 300                 # 5 minutes
DEFAULT_INTERVAL_S  = 3.0                 # sample one frame every 3 s
MAX_FRAMES          = 10                  # hard cap on extracted frames
RESIZE_MAX_DIM      = 1024                # max dimension for extracted frames

SUPPORTED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
    "video/avi",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_frames(
    raw_bytes: bytes,
    content_type: str,
    interval_s: float = DEFAULT_INTERVAL_S,
    max_frames: int = MAX_FRAMES,
    resize_max_dim: int = RESIZE_MAX_DIM,
) -> Tuple[List[Tuple[float, Image.Image]], dict]:
    """
    Extract representative frames from a video byte stream.

    Parameters
    ----------
    raw_bytes : bytes
        Raw video file content.
    content_type : str
        MIME type reported by the client (used for validation only).
    interval_s : float
        Approximate seconds between sampled frames.
    max_frames : int
        Maximum number of frames to return. Caps extraction after this count.
    resize_max_dim : int
        Maximum pixel dimension (width or height) for returned frames.

    Returns
    -------
    frames : list of (timestamp_s, PIL.Image)
        Extracted frames with their source timestamps in seconds.
    telemetry : dict
        Metadata about the video: duration, fps, total_frames, sampled_count,
        interval_s_used, resize_max_dim.

    Raises
    ------
    HTTPException 400 : empty bytes, corrupt/unreadable video, zero duration.
    HTTPException 413 : file exceeds MAX_VIDEO_BYTES.
    HTTPException 415 : unsupported content type.
    HTTPException 422 : video duration exceeds MAX_VIDEO_SECONDS.
    """
    # -- Validation -----------------------------------------------------------
    if not raw_bytes:
        raise HTTPException(400, "Empty video upload.")

    if len(raw_bytes) > MAX_VIDEO_BYTES:
        raise HTTPException(
            413,
            f"Video exceeds {MAX_VIDEO_BYTES // (1024 * 1024)} MB limit "
            f"({len(raw_bytes) // (1024 * 1024)} MB received).",
        )

    if content_type not in SUPPORTED_VIDEO_TYPES:
        raise HTTPException(
            415,
            f"Unsupported video type '{content_type}'. "
            f"Supported: {sorted(SUPPORTED_VIDEO_TYPES)}",
        )

    # -- Write to temp file (required for VideoCapture on Windows) -----------
    suffix = _ext_for_mime(content_type)
    tmp_path: str | None = None
    cap: cv2.VideoCapture | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise HTTPException(400, "Video could not be decoded. File may be corrupt or unsupported.")

        fps          = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_s   = total_frames / fps if fps > 0 else 0.0

        # Guard against unreliable metadata — try reading one frame
        if total_frames <= 0 or duration_s <= 0:
            ok, _test = cap.read()
            if not ok:
                raise HTTPException(400, "Video appears to be empty or unreadable (zero frames).")
            # Reset and attempt estimation
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            duration_s = max(duration_s, interval_s)

        if duration_s > MAX_VIDEO_SECONDS:
            raise HTTPException(
                422,
                f"Video duration ({duration_s:.0f} s) exceeds {MAX_VIDEO_SECONDS} s limit.",
            )

        # -- Frame sampling ---------------------------------------------------
        interval_s = max(interval_s, 0.1)
        frames: List[Tuple[float, Image.Image]] = []
        target_timestamps = _build_timestamps(duration_s, interval_s, max_frames)

        for ts in target_timestamps:
            frame_idx = int(ts * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, bgr = cap.read()
            if not ok or bgr is None:
                continue

            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            pil = _resize_preserving_aspect(pil, resize_max_dim)
            frames.append((round(ts, 2), pil))

        if not frames:
            raise HTTPException(400, "No readable frames could be extracted from the video.")

        telemetry = {
            "duration_s":     round(duration_s, 2),
            "fps":            round(fps, 2),
            "total_frames":   total_frames,
            "sampled_count":  len(frames),
            "interval_s_used": interval_s,
            "resize_max_dim": resize_max_dim,
        }
        return frames, telemetry

    finally:
        if cap is not None:
            cap.release()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass  # Non-fatal — temp file cleanup failure


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_timestamps(
    duration_s: float,
    interval_s: float,
    max_frames: int,
) -> List[float]:
    """
    Build a list of target timestamps evenly spaced across the video duration,
    capped at max_frames. Always includes a sample near the start.
    """
    if duration_s <= 0:
        return [0.0]

    timestamps: List[float] = []
    t = 0.0
    while t < duration_s and len(timestamps) < max_frames:
        timestamps.append(min(t, duration_s - 0.05))
        t += interval_s

    # Ensure at least one timestamp
    if not timestamps:
        timestamps = [0.0]

    return timestamps


def _resize_preserving_aspect(img: Image.Image, max_dim: int) -> Image.Image:
    """Downscale image so neither dimension exceeds max_dim. Upscaling is skipped."""
    w, h = img.size
    if w <= max_dim and h <= max_dim:
        return img
    scale = max_dim / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


def _ext_for_mime(mime: str) -> str:
    """Return a file extension for the given MIME type."""
    return {
        "video/mp4":       ".mp4",
        "video/webm":      ".webm",
        "video/quicktime": ".mov",
        "video/x-msvideo": ".avi",
        "video/avi":       ".avi",
    }.get(mime, ".mp4")
