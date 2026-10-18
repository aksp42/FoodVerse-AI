"""
FoodVerse AI — Image Preprocessing and Visual Feature Extraction
Smart Bridge Milestone 3, Activity 3.1

Provides reusable, deterministic OpenCV-based image preprocessing and visual
feature extraction:
  1. Multi-format decoding (JPEG, PNG, WebP) with strict format and corruption validation.
  2. Safe handling of 1-channel grayscale and 4-channel transparent RGBA images
     (compositing alpha over neutral white to avoid black background artifacts).
  3. Aspect-ratio-preserving resizing with cv2.INTER_AREA downscaling for high-res inputs.
  4. Deterministic visual feature extraction:
     - Aspect ratio and orientation classification.
     - Laplacian-variance sharpness quantification and blur indicator.
     - Perceptual luminance calculation and exposure classification.
     - HSV color space analysis (mean hue, mean saturation, mean value, dominant tone).
     - Texture variation and RMS contrast via Sobel gradient magnitude.
  5. Structured freshness-related feature representation preparing Milestone 3, Activity 3.2.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from fastapi import HTTPException
from PIL import Image

# Maximum allowed file upload size (10 MB)
MAX_FILE_BYTES = 10 * 1024 * 1024

# Default maximum dimension for vision model ingestion
MAX_IMG_DIMENSION = 1600

# Supported image MIME types
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}

# Default Laplacian variance threshold for blur classification
DEFAULT_BLUR_THRESHOLD = 100.0


def decode_and_validate_image(raw_bytes: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Decodes, validates, and normalizes raw image bytes using OpenCV.

    Features:
      - Validates non-empty byte buffer.
      - Decodes unchanged channels via cv2.IMREAD_UNCHANGED.
      - Detects and rejects corrupt, truncated, or zero-dimension byte streams (HTTP 400).
      - Converts 1-channel grayscale to 3-channel RGB.
      - Converts 4-channel RGBA by compositing transparent pixels over a pure white
        background, preventing black bounding box artifacts in culinary imagery.
      - Converts standard 3-channel BGR to RGB.

    Returns:
      (rgb_image, normalization_telemetry)
    """
    if not raw_bytes or len(raw_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty image file uploaded. Please upload a valid food photo."
        )

    if len(raw_bytes) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Limit is {MAX_FILE_BYTES // (1024 * 1024)}MB."
        )

    np_buf = np.frombuffer(raw_bytes, dtype=np.uint8)
    # Decode unchanged to inspect original channel count (e.g., Grayscale or RGBA)
    decoded = cv2.imdecode(np_buf, cv2.IMREAD_UNCHANGED)

    if decoded is None or decoded.size == 0:
        raise HTTPException(
            status_code=400,
            detail="Corrupt, unreadable, or unsupported image file. Please upload a valid JPG, PNG, or WebP image."
        )

    shape = decoded.shape
    if len(shape) < 2 or shape[0] <= 0 or shape[1] <= 0:
        raise HTTPException(status_code=400, detail="Invalid image dimensions (0x0).")

    orig_h, orig_w = shape[0], shape[1]
    alpha_composited = False

    if len(shape) == 2:
        # 1-channel Grayscale image -> expand to 3-channel RGB
        channels_orig = 1
        rgb = cv2.cvtColor(decoded, cv2.COLOR_GRAY2RGB)
    elif shape[2] == 4:
        # 4-channel RGBA (or BGRA from OpenCV) -> composite over neutral white background
        channels_orig = 4
        alpha_composited = True
        b, g, r, a = cv2.split(decoded)
        alpha_factor = a.astype(np.float32) / 255.0
        white_bg = np.ones_like(b, dtype=np.float32) * 255.0

        r_comp = np.clip(r.astype(np.float32) * alpha_factor + white_bg * (1.0 - alpha_factor), 0, 255).astype(np.uint8)
        g_comp = np.clip(g.astype(np.float32) * alpha_factor + white_bg * (1.0 - alpha_factor), 0, 255).astype(np.uint8)
        b_comp = np.clip(b.astype(np.float32) * alpha_factor + white_bg * (1.0 - alpha_factor), 0, 255).astype(np.uint8)
        rgb = cv2.merge([r_comp, g_comp, b_comp])
    elif shape[2] == 3:
        # Standard 3-channel BGR -> RGB
        channels_orig = 3
        rgb = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
    else:
        # Fallback multi-channel
        channels_orig = int(shape[2])
        rgb = cv2.cvtColor(decoded[:, :, :3], cv2.COLOR_BGR2RGB)

    telemetry = {
        "original_width": int(orig_w),
        "original_height": int(orig_h),
        "channels_original": int(channels_orig),
        "alpha_composited": alpha_composited,
        "color_space": "RGB",
    }

    return rgb, telemetry


def resize_aspect_preserving(rgb_image: np.ndarray, max_dimension: int = MAX_IMG_DIMENSION) -> Tuple[np.ndarray, bool]:
    """
    Resizes image only if the largest dimension exceeds max_dimension,
    strictly preserving original aspect ratio using cv2.INTER_AREA.
    """
    orig_h, orig_w = rgb_image.shape[:2]
    max_dim = max(orig_h, orig_w)

    if max_dim > max_dimension:
        scale = float(max_dimension) / float(max_dim)
        new_w = max(1, int(round(orig_w * scale)))
        new_h = max(1, int(round(orig_h * scale)))
        resized = cv2.resize(rgb_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized, True

    return rgb_image, False


def apply_gentle_denoise(rgb_image: np.ndarray) -> np.ndarray:
    """
    Applies gentle noise reduction (Gaussian blur with 3x3 kernel, sigma=0.5)
    for visual feature measurement stability. Note: the clean un-blurred
    image is preserved for Gemini multimodal vision.
    """
    return cv2.GaussianBlur(rgb_image, (3, 3), sigmaX=0.5)


def extract_visual_features(
    rgb_image: np.ndarray,
    orig_dimensions: Tuple[int, int],
    blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
) -> Dict[str, Any]:
    """
    Extracts deterministic, verifiable visual features from an RGB image:
      1. Dimensions, aspect ratio, and orientation.
      2. Sharpness score (Laplacian variance) and blur flag.
      3. Perceptual luminance and exposure classification.
      4. HSV color space statistics (mean hue, mean saturation, dominant tone).
      5. Texture variation (Sobel gradient magnitude standard deviation) and RMS contrast.
      6. Freshness-related feature representation (supporting Activity 3.2).

    All numeric outputs are finite, non-negative where applicable, and sensibly rounded.
    """
    orig_w, orig_h = orig_dimensions
    proc_h, proc_w = rgb_image.shape[:2]

    # 1. Geometry & Aspect Ratio
    if orig_h > 0:
        aspect_ratio = round(float(orig_w) / float(orig_h), 2)
    else:
        aspect_ratio = 1.0

    if orig_w > orig_h:
        orientation = "landscape"
    elif orig_h > orig_w:
        orientation = "portrait"
    else:
        orientation = "square"

    # 2. Grayscale & Sharpness (Laplacian Variance)
    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    lap_var = float(lap.var())
    sharpness_score = round(lap_var if math.isfinite(lap_var) else 0.0, 2)
    is_blurry = bool(sharpness_score < blur_threshold)

    # 3. Luminance & Exposure (Rec. 601 coefficients: 0.299 R + 0.587 G + 0.114 B)
    r_channel = rgb_image[:, :, 0].astype(np.float64)
    g_channel = rgb_image[:, :, 1].astype(np.float64)
    b_channel = rgb_image[:, :, 2].astype(np.float64)

    luminance = 0.299 * r_channel + 0.587 * g_channel + 0.114 * b_channel
    lum_mean = float(np.mean(luminance))
    brightness_mean = round(lum_mean if math.isfinite(lum_mean) else 128.0, 2)

    if brightness_mean < 45.0:
        exposure_quality = "underexposed"
    elif brightness_mean > 215.0:
        exposure_quality = "overexposed"
    else:
        exposure_quality = "normal"

    # 4. Color Statistics (HSV space)
    hsv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
    h_channel = hsv[:, :, 0].astype(np.float64)  # OpenCV H is 0..179
    s_channel = hsv[:, :, 1].astype(np.float64)  # S is 0..255
    v_channel = hsv[:, :, 2].astype(np.float64)  # V is 0..255

    mean_h_deg = round(float(np.mean(h_channel)) * 2.0, 1)  # Scale to 0-360 degrees
    mean_sat_pct = round(float(np.mean(s_channel)) / 255.0 * 100.0, 1)  # Scale to 0-100%
    mean_val_pct = round(float(np.mean(v_channel)) / 255.0 * 100.0, 1)  # Scale to 0-100%

    # Descriptive dominant culinary color tone
    if mean_sat_pct < 15.0:
        dominant_tone = "neutral / low-saturation tone"
    elif mean_h_deg < 30.0 or mean_h_deg >= 330.0:
        dominant_tone = "warm reddish / amber tone"
    elif 30.0 <= mean_h_deg < 75.0:
        dominant_tone = "golden / yellowish tone"
    elif 75.0 <= mean_h_deg < 165.0:
        dominant_tone = "fresh green / herbal tone"
    elif 165.0 <= mean_h_deg < 260.0:
        dominant_tone = "cool cyan / bluish tone"
    else:
        dominant_tone = "purple / rich berry tone"

    # 5. Texture Variation & Contrast (Sobel Gradients & RMS Contrast)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(gx**2 + gy**2)

    grad_std = float(np.std(grad_mag))
    texture_variation = round(grad_std if math.isfinite(grad_std) else 0.0, 2)

    rms_contrast = round(float(np.std(gray)), 2)

    if texture_variation < 15.0:
        surface_uniformity = "high (smooth / uniform surface)"
    elif texture_variation < 45.0:
        surface_uniformity = "moderate (typical plated food texture)"
    else:
        surface_uniformity = "heterogeneous (rich multi-component or granular texture)"

    # 6. Structured Freshness-Related Feature Representation (Supports Activity 3.2)
    freshness_cues = {
        "color_profile": {
            "mean_saturation_pct": mean_sat_pct,
            "mean_hue_deg": mean_h_deg,
            "mean_value_pct": mean_val_pct,
            "dominant_tone": dominant_tone,
            "channel_means": {
                "red": round(float(np.mean(r_channel)), 1),
                "green": round(float(np.mean(g_channel)), 1),
                "blue": round(float(np.mean(b_channel)), 1),
            },
        },
        "texture_profile": {
            "texture_variation": texture_variation,
            "rms_contrast": rms_contrast,
            "surface_uniformity": surface_uniformity,
        },
        "quality_indicators": {
            "sharpness_score": sharpness_score,
            "is_blurry": is_blurry,
            "blur_threshold": blur_threshold,
            "brightness_mean": brightness_mean,
            "exposure_quality": exposure_quality,
        },
        "disclaimer": (
            "Visual feature statistics are objective image metrics prepared for Activity 3.2 "
            "freshness models. They do not constitute an independent clinical or microbiological spoilage diagnosis."
        ),
    }

    return {
        "aspect_ratio": aspect_ratio,
        "orientation": orientation,
        "sharpness_score": sharpness_score,
        "is_blurry": is_blurry,
        "brightness_mean": brightness_mean,
        "exposure_quality": exposure_quality,
        "mean_saturation": mean_sat_pct,
        "texture_variation": texture_variation,
        "rms_contrast": rms_contrast,
        "freshness_cues": freshness_cues,
    }


def preprocess_food_image(
    raw_bytes: bytes,
    max_dimension: int = MAX_IMG_DIMENSION,
    blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Master preprocessing and feature extraction pipeline for FoodVerse AI:
      1. Validates and decodes image bytes (JPEG, PNG, WebP).
      2. Normalizes grayscale to RGB, and composites RGBA transparency over white.
      3. Performs aspect-ratio-preserving resize for high-resolution images.
      4. Extracts comprehensive visual features (geometry, sharpness, color, texture).
      5. Prepares structured telemetry combining legacy fields with Activity 3.1 features.
      6. Emits a standard PIL Image ready for Gemini Multimodal Vision API ingestion.

    Returns:
      (pil_image_for_gemini, preprocessing_telemetry)
    """
    # 1 & 2: Decode & Normalize
    rgb, norm_meta = decode_and_validate_image(raw_bytes)
    orig_w = norm_meta["original_width"]
    orig_h = norm_meta["original_height"]

    # 3: Resizing
    rgb_proc, resized = resize_aspect_preserving(rgb, max_dimension=max_dimension)
    proc_h, proc_w = rgb_proc.shape[:2]

    # 4: Visual Feature Extraction
    features = extract_visual_features(
        rgb_proc,
        orig_dimensions=(orig_w, orig_h),
        blur_threshold=blur_threshold,
    )

    # 5: Telemetry payload preserving legacy contract + additive Activity 3.1 fields
    telemetry: Dict[str, Any] = {
        # -- Legacy Activity 2.1 contract fields (strictly preserved) --
        "original_dimensions": [orig_w, orig_h],
        "processed_dimensions": [proc_w, proc_h],
        "resized": resized,
        "color_space": "RGB",
        "channels": 3,
        "engine": f"OpenCV {cv2.__version__}",
        # -- Additive Activity 3.1 Feature Extraction fields --
        "aspect_ratio": features["aspect_ratio"],
        "orientation": features["orientation"],
        "sharpness_score": features["sharpness_score"],
        "is_blurry": features["is_blurry"],
        "brightness_mean": features["brightness_mean"],
        "exposure_quality": features["exposure_quality"],
        "mean_saturation": features["mean_saturation"],
        "texture_variation": features["texture_variation"],
        "rms_contrast": features["rms_contrast"],
        "normalization": {
            "channels_original": norm_meta["channels_original"],
            "alpha_composited": norm_meta["alpha_composited"],
            "pixel_value_range": [0, 255],
        },
        "freshness_cues": features["freshness_cues"],
    }

    # 6: Convert to PIL Image for downstream Gemini Multimodal Vision API
    pil_image = Image.fromarray(rgb_proc)

    return pil_image, telemetry
