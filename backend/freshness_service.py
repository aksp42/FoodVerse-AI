"""
FoodVerse AI — Freshness Classification and Safety Recommendation Service
Smart Bridge Milestone 3, Activity 3.2

Classifies food freshness from:
  1. Image quality indicators from Activity 3.1 preprocessing telemetry.
  2. Gemini Vision multimodal assessment (primary engine).

Output status values: fresh | moderately_fresh | spoiled | inconclusive

Limitations (always disclosed):
  - Visual analysis cannot detect bacteria, toxins, or invisible microbial contamination.
  - Classification is informational only and does not constitute a food-safety guarantee.
  - Assessment accuracy depends on image quality and food visibility.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Evidence level mapping from Gemini certainty strings
# ---------------------------------------------------------------------------
_CERTAINTY_TO_EVIDENCE: Dict[str, str] = {
    "high":     "strong",
    "medium":   "moderate",
    "cautious": "limited",
}

# ---------------------------------------------------------------------------
# Human-readable labels for each canonical status
# ---------------------------------------------------------------------------
_STATUS_LABELS: Dict[str, str] = {
    "fresh":            "Fresh",
    "moderately_fresh": "Use Soon",
    "spoiled":          "Potential Spoilage",
    "inconclusive":     "Inconclusive",
}

# ---------------------------------------------------------------------------
# Safety recommendation templates per status
# ---------------------------------------------------------------------------
_SAFETY_RECOMMENDATIONS: Dict[str, List[str]] = {
    "fresh": [
        "Store in the crisper drawer at approximately 4 °C to maintain freshness.",
        "Keep away from ethylene-producing fruits (bananas, apples) to slow ripening.",
        "Wash only just before consumption to reduce moisture-related spoilage.",
        "Visual freshness is a general indicator only — inspect aroma and texture before eating.",
    ],
    "moderately_fresh": [
        "Cook or consume soon — visual signs suggest the item is past peak freshness.",
        "Trim and discard any softened, bruised, or discoloured portions before use.",
        "Chop and freeze for use in soups, stews, or smoothies to avoid waste.",
        "Do not rely solely on appearance — smell and texture are additional indicators.",
    ],
    "spoiled": [
        "Discard this item immediately — do not taste-test spoiled food.",
        "Sanitise the storage container and any surfaces that contacted the item.",
        "Do not consume food with visible mould, sliminess, or strong off-odours.",
        "Spoilage visible to a camera does not represent the full extent of microbial activity.",
    ],
    "inconclusive": [
        "Image quality or food type prevented a reliable visual freshness assessment.",
        "Apply the sniff test, check texture, and verify storage dates manually.",
        "If the item shows any off-odour, unusual texture, or visible mould, discard it.",
        "When in doubt about food safety, discard — do not risk consumption.",
    ],
}

# ---------------------------------------------------------------------------
# Standard limitation disclaimer (all responses)
# ---------------------------------------------------------------------------
_LIMITATIONS = (
    "Visual assessment identifies surface appearance only. It cannot detect bacteria, "
    "toxins, pathogens, or subsurface contamination. This result is informational and "
    "does not constitute a food-safety guarantee. Always apply sensory checks "
    "(smell, texture) and follow local food-safety guidelines."
)

_DISCLAIMER = (
    "Visual inspection cannot guarantee food safety or identify microbiological contaminants. "
    "When in doubt, discard."
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_status(raw_status: Optional[str]) -> str:
    """
    Map Gemini raw status strings to canonical Activity 3.2 status values.

    Gemini returns: "fresh" | "aging" | "spoiled"
    Canonical:      "fresh" | "moderately_fresh" | "spoiled" | "inconclusive"
    """
    if not raw_status or not isinstance(raw_status, str):
        return "inconclusive"
    s = raw_status.strip().lower()
    mapping = {
        "fresh":   "fresh",
        "aging":   "moderately_fresh",
        "spoiled": "spoiled",
    }
    return mapping.get(s, "inconclusive")


def _map_evidence_level(certainty: Optional[str]) -> str:
    """Map Gemini certainty string to Activity 3.2 evidence_level."""
    if not certainty or not isinstance(certainty, str):
        return "insufficient"
    return _CERTAINTY_TO_EVIDENCE.get(certainty.strip().lower(), "insufficient")


def _slim_preprocessing_features(freshness_cues: dict) -> dict:
    """Return a compact subset of preprocessing telemetry for the API response."""
    qi = freshness_cues.get("quality_indicators", {})
    cp = freshness_cues.get("color_profile", {})
    tp = freshness_cues.get("texture_profile", {})
    return {
        "sharpness_score":     qi.get("sharpness_score"),
        "is_blurry":           qi.get("is_blurry"),
        "exposure_quality":    qi.get("exposure_quality"),
        "brightness_mean":     qi.get("brightness_mean"),
        "dominant_tone":       cp.get("dominant_tone"),
        "mean_saturation_pct": cp.get("mean_saturation_pct"),
        "surface_uniformity":  tp.get("surface_uniformity"),
    }


def _build_observed_cues(gemini_data: dict, freshness_cues: dict) -> List[str]:
    """
    Merge Gemini visual observations with preprocessing-derived cues into a list of strings.
    """
    cues: List[str] = []

    # From Gemini observations dict
    observations = gemini_data.get("observations") or {}
    if isinstance(observations, dict):
        for key in ("color", "texture", "defects"):
            val = observations.get(key, "")
            if val and isinstance(val, str):
                cues.append(f"{key.capitalize()}: {val.strip()}")

    # From preprocessing telemetry
    cp = freshness_cues.get("color_profile", {})
    tp = freshness_cues.get("texture_profile", {})
    dominant = cp.get("dominant_tone", "")
    if dominant and isinstance(dominant, str) and dominant != "unknown":
        cues.append(f"Dominant colour tone: {dominant}")
    surface = tp.get("surface_uniformity", "")
    if surface and isinstance(surface, str):
        cues.append(f"Surface uniformity: {surface}")

    return cues if cues else ["No specific visual cues extracted."]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_freshness(
    freshness_cues: dict,
    gemini_data: Optional[dict],
    gemini_model_used: str = "",
) -> dict:
    """
    Classify food freshness from Activity 3.1 preprocessing telemetry and raw
    Gemini Vision response.

    Parameters
    ----------
    freshness_cues : dict
        Structured telemetry from ``image_processor.preprocess_food_image()``.
        Must contain at minimum ``quality_indicators`` with ``is_blurry`` and
        ``exposure_quality`` keys.
    gemini_data : dict | None
        Parsed JSON response from Gemini Vision, or ``None`` if the API call
        failed or was not attempted.
    gemini_model_used : str
        Name of the Gemini model that produced ``gemini_data`` (for provenance).

    Returns
    -------
    dict
        Structured Activity 3.2 classification result.

    Assessment methods
    ------------------
    - ``"gemini_vision_multimodal"``  — normal path; Gemini assessed image.
    - ``"inconclusive_image_quality"``— image too blurry or badly exposed.
    - ``"inconclusive_gemini_failure"``— Gemini API unavailable or returned error.
    """
    # ------------------------------------------------------------------ #
    # Step 1 — Image quality pre-check (before Gemini API quota is used)  #
    # ------------------------------------------------------------------ #
    quality = freshness_cues.get("quality_indicators", {})
    is_blurry       = bool(quality.get("is_blurry", False))
    exposure_quality = str(quality.get("exposure_quality", "normal"))

    if is_blurry or exposure_quality != "normal":
        reason = (
            "Image is too blurry for reliable freshness assessment."
            if is_blurry
            else f"Image exposure is '{exposure_quality}' — adequate lighting is required."
        )
        return _build_result(
            status="inconclusive",
            assessment_method="inconclusive_image_quality",
            evidence_level="insufficient",
            food_item="Unknown",
            shelf="Cannot determine",
            observed_cues=[reason],
            safety_recommendations=_SAFETY_RECOMMENDATIONS["inconclusive"],
            checks=[],
            observations={},
            engine="Activity 3.1 preprocessing checks (Gemini not called)",
            gemini_raw=None,
            freshness_cues=freshness_cues,
            extra_note=reason,
        )

    # ------------------------------------------------------------------ #
    # Step 2 — Gemini availability check                                  #
    # ------------------------------------------------------------------ #
    if gemini_data is None:
        return _build_result(
            status="inconclusive",
            assessment_method="inconclusive_gemini_failure",
            evidence_level="insufficient",
            food_item="Unknown",
            shelf="Cannot determine",
            observed_cues=["Gemini Vision API call failed or returned no data."],
            safety_recommendations=_SAFETY_RECOMMENDATIONS["inconclusive"],
            checks=[],
            observations={},
            engine=gemini_model_used or "Gemini (unavailable)",
            gemini_raw=None,
            freshness_cues=freshness_cues,
            extra_note="Gemini Vision API was unavailable or returned no data.",
        )

    # ------------------------------------------------------------------ #
    # Step 3 — Validate Gemini response structure                          #
    # ------------------------------------------------------------------ #
    required_fields = {"status", "label", "certainty", "food_item"}
    missing = required_fields - set(gemini_data.keys())
    if missing:
        return _build_result(
            status="inconclusive",
            assessment_method="inconclusive_gemini_failure",
            evidence_level="insufficient",
            food_item=gemini_data.get("food_item", "Unknown"),
            shelf=gemini_data.get("shelf", "Cannot determine"),
            observed_cues=[f"Gemini response was malformed — missing fields: {sorted(missing)}."],
            safety_recommendations=_SAFETY_RECOMMENDATIONS["inconclusive"],
            checks=gemini_data.get("checks", []),
            observations=gemini_data.get("observations", {}),
            engine=f"{gemini_model_used} Vision" if gemini_model_used else "Gemini Vision",
            gemini_raw=gemini_data,
            freshness_cues=freshness_cues,
            extra_note=f"Missing required Gemini fields: {sorted(missing)}",
        )

    # ------------------------------------------------------------------ #
    # Step 4 — Normalise status and map evidence level                    #
    # ------------------------------------------------------------------ #
    raw_status   = gemini_data.get("status", "")
    certainty    = gemini_data.get("certainty", "")
    status       = _normalize_status(raw_status)
    evidence_lvl = _map_evidence_level(certainty)

    # If Gemini says status but maps to inconclusive (unexpected value), reflect that
    if status == "inconclusive":
        assessment_method = "inconclusive_gemini_failure"
    else:
        assessment_method = "gemini_vision_multimodal"

    # ------------------------------------------------------------------ #
    # Step 5 — Build observed cues from Gemini + preprocessing data       #
    # ------------------------------------------------------------------ #
    observed_cues = _build_observed_cues(gemini_data, freshness_cues)

    # ------------------------------------------------------------------ #
    # Step 6 — Construct safety recommendations                           #
    # ------------------------------------------------------------------ #
    gemini_recs = gemini_data.get("recommendations") or []
    if isinstance(gemini_recs, list) and len(gemini_recs) >= 2:
        # Use Gemini recommendations but append our mandatory caveat
        safety_recs = list(gemini_recs) + [
            "Visual assessment cannot detect pathogens or toxins — apply smell and texture checks."
        ]
    else:
        safety_recs = _SAFETY_RECOMMENDATIONS.get(status, _SAFETY_RECOMMENDATIONS["inconclusive"])

    # ------------------------------------------------------------------ #
    # Step 7 — Compose and return full response                           #
    # ------------------------------------------------------------------ #
    engine_str = f"{gemini_model_used} Vision" if gemini_model_used else "Gemini Vision"

    return _build_result(
        status=status,
        assessment_method=assessment_method,
        evidence_level=evidence_lvl,
        food_item=gemini_data.get("food_item", "Unknown"),
        shelf=gemini_data.get("shelf", "Cannot determine"),
        observed_cues=observed_cues,
        safety_recommendations=safety_recs,
        checks=gemini_data.get("checks", []),
        observations=gemini_data.get("observations", {}),
        engine=engine_str,
        gemini_raw=gemini_data,
        freshness_cues=freshness_cues,
    )


def _build_result(
    *,
    status: str,
    assessment_method: str,
    evidence_level: str,
    food_item: str,
    shelf: str,
    observed_cues: List[str],
    safety_recommendations: List[str],
    checks: list,
    observations: dict,
    engine: str,
    gemini_raw: Optional[dict],
    freshness_cues: dict,
    extra_note: str = "",
) -> dict:
    """
    Compose the canonical Activity 3.2 response dict.
    All fields are always present to guarantee a stable API contract.
    """
    label = _STATUS_LABELS.get(status, status.replace("_", " ").title())

    # Legacy certainty field — preserved for backward compatibility with existing frontend
    certainty_legacy = ""
    if gemini_raw:
        certainty_legacy = gemini_raw.get("certainty", "")

    return {
        # ---- Activity 3.2 canonical fields ----
        "status":                 status,
        "label":                  label,
        "assessment_method":      assessment_method,
        "evidence_level":         evidence_level,
        "food_item":              food_item,
        "shelf":                  shelf,
        "observed_cues":          observed_cues,
        "safety_recommendations": safety_recommendations,
        "limitations":            _LIMITATIONS,
        "preprocessing_features": _slim_preprocessing_features(freshness_cues),
        # ---- Backward-compatible Gemini pass-through fields ----
        "checks":                 checks if isinstance(checks, list) else [],
        "observations":           observations if isinstance(observations, dict) else {},
        "recommendations":        safety_recommendations,   # alias for existing UI key
        "certainty":              certainty_legacy,          # legacy field for Freshness.jsx
        "disclaimer":             _DISCLAIMER,
        "engine":                 engine,
    }
