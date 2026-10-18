"""
FoodVerse AI — Hygiene Indicator Analysis and Compliance Scoring Service
Smart Bridge Milestone 4, Activity 4.1

Provides:
  1. Structured parsing of per-frame Gemini Vision hygiene observations.
  2. Deterministic, rule-based compliance score calculation.
  3. Alert generation tied to specific observations and timestamps.

═══════════════════════════════════════════════════════════════════════
SCORING FORMULA (documented)
═══════════════════════════════════════════════════════════════════════

Each hygiene indicator carries a weight (points at risk):

  Indicator                      | Weight | Rationale
  ───────────────────────────────|────────|──────────────────────────
  surface_cleanliness            |  25    | High cross-contamination risk
  food_handling_practices        |  20    | Direct food safety impact
  cross_contamination_risk       |  20    | Direct food safety impact
  gloves_ppe                     |  15    | PPE compliance
  hair_coverings                 |  10    | PPE compliance
  waste_management               |  10    | Environmental hygiene

  Total possible weight: 100

Score calculation:
  1. Only "assessable" indicators are counted (status ≠ "uncertain").
  2. For each assessable indicator:
     - status "observed" (positive finding)  → full weight retained.
     - status "not_observed" (negative finding) → 0 weight retained.
  3. coverage = assessable_weight / total_weight  (proportion of evidence)
  4. raw_score = sum(retained_weights) / assessable_weight × 100
     (if assessable_weight = 0: score = 0, coverage = 0)
  5. Final score is rounded to nearest integer, clamped to [0, 100].

Uncertain observations are excluded from score arithmetic but listed in
the result and flagged as requiring follow-up. "Not observed" means the
indicator was expected but not visible; it is scored as a deficit.
"Uncertain" means visibility was insufficient to make a determination.

═══════════════════════════════════════════════════════════════════════
LIMITATIONS (always disclosed)
═══════════════════════════════════════════════════════════════════════
- This is a visual screening tool, not a certified health inspection.
- Scores are based solely on visual evidence present in sampled frames.
- Indicators not visible in any frame are excluded from the score.
- Visual AI cannot detect microbial contamination, temperature compliance,
  or any factor not visible to the camera.
- This output does not constitute regulatory compliance or legal certification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Indicator registry — defines what we look for and its scoring weight
# ---------------------------------------------------------------------------

INDICATOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "surface_cleanliness": {
        "label":       "Surface & Countertop Cleanliness",
        "weight":      25,
        "description": "Visible cleanliness of food preparation surfaces and countertops.",
    },
    "food_handling_practices": {
        "label":       "Food Handling Practices",
        "weight":      20,
        "description": "Observable food-handling technique and hygiene behaviour.",
    },
    "cross_contamination_risk": {
        "label":       "Cross-Contamination Risk",
        "weight":      20,
        "description": "Visible indicators of potential cross-contamination (raw/cooked proximity, etc.).",
    },
    "gloves_ppe": {
        "label":       "Gloves / Personal Protective Equipment",
        "weight":      15,
        "description": "Presence of gloves or other required PPE during food handling.",
    },
    "hair_coverings": {
        "label":       "Hair Coverings",
        "weight":      10,
        "description": "Presence of appropriate hair restraints or coverings.",
    },
    "waste_management": {
        "label":       "Waste Management & Containment",
        "weight":      10,
        "description": "Visible waste handling, bin coverage, and disposal hygiene.",
    },
}

TOTAL_WEIGHT = sum(v["weight"] for v in INDICATOR_REGISTRY.values())  # 100

VALID_STATUSES = {"observed", "not_observed", "uncertain"}

_LIMITATIONS = (
    "This compliance screening score is derived from visual analysis of sampled "
    "video frames or still images only. It cannot detect microbial contamination, "
    "temperature compliance, or any hygiene factor not visible to the camera. "
    "This result is not a certified health inspection, regulatory assessment, "
    "or legal compliance determination. Always consult a qualified food safety "
    "inspector for official evaluation."
)

_DISCLAIMER = (
    "Visual inspection is an advisory screening tool and not a certified "
    "regulatory inspection. Results are indicative only."
)


# ---------------------------------------------------------------------------
# Structured observation parsing
# ---------------------------------------------------------------------------

def parse_frame_observations(
    gemini_data: Optional[dict],
    frame_timestamp: float,
) -> List[dict]:
    """
    Parse raw Gemini Vision response for a single frame into structured
    hygiene indicator observations.

    Each observation dict:
      {
        "indicator":       str,   # INDICATOR_REGISTRY key
        "label":           str,   # human-readable name
        "status":          str,   # "observed" | "not_observed" | "uncertain"
        "evidence":        str,   # Gemini's textual evidence
        "frame_timestamp": float, # seconds into the video
      }

    Unknown or invalid status values from Gemini are coerced to "uncertain".
    Missing fields are handled gracefully without raising exceptions.
    """
    observations: List[dict] = []

    if not gemini_data or not isinstance(gemini_data, dict):
        return observations

    raw_obs = gemini_data.get("observations") or []
    if not isinstance(raw_obs, list):
        return observations

    for item in raw_obs:
        if not isinstance(item, dict):
            continue

        raw_indicator = str(item.get("indicator", "")).strip().lower().replace(" ", "_")
        # Accept both exact key and fuzzy label match
        matched_key = _match_indicator_key(raw_indicator)
        if matched_key is None:
            continue  # Unknown indicator — skip

        raw_status = str(item.get("status", "")).strip().lower()
        status = raw_status if raw_status in VALID_STATUSES else "uncertain"

        evidence = str(item.get("evidence", "")).strip() or "No evidence text provided."

        observations.append({
            "indicator":       matched_key,
            "label":           INDICATOR_REGISTRY[matched_key]["label"],
            "status":          status,
            "evidence":        evidence,
            "frame_timestamp": round(frame_timestamp, 2),
        })

    return observations


def _match_indicator_key(raw: str) -> Optional[str]:
    """Return the canonical indicator key for a raw string, or None if unrecognised."""
    if raw in INDICATOR_REGISTRY:
        return raw
    # Partial match on label words
    for key, meta in INDICATOR_REGISTRY.items():
        label_words = meta["label"].lower().split()
        if any(w in raw for w in label_words) or raw in key:
            return key
    return None


# ---------------------------------------------------------------------------
# Compliance score calculation
# ---------------------------------------------------------------------------

def calculate_compliance_score(
    all_observations: List[dict],
) -> dict:
    """
    Calculate a deterministic compliance score from a list of structured
    observations (across all sampled frames).

    Strategy for multi-frame results:
      - For each indicator, take the WORST status observed across all frames.
        ("not_observed" beats "uncertain" beats "observed")
      - This is conservative: if any frame shows a deficit, it is flagged.

    Returns
    -------
    dict with:
      compliance_score      int     0–100
      assessable_indicators int     number of indicators with definitive evidence
      total_indicators      int     total registered indicators
      coverage              float   fraction of indicators assessable (0–1)
      score_breakdown       list    per-indicator detail
      alerts                list    violations with indicator + evidence
      uncertain_indicators  list    indicators lacking sufficient visual evidence
      limitations           str
      disclaimer            str
    """
    # --- Aggregate per indicator across frames (worst-case) -----------------
    aggregated: Dict[str, str] = {}   # indicator_key -> worst status
    evidence_map: Dict[str, str] = {}
    timestamp_map: Dict[str, float] = {}

    status_rank = {"not_observed": 0, "uncertain": 1, "observed": 2}

    for obs in all_observations:
        key  = obs.get("indicator")
        stat = obs.get("status")
        if not key or not stat:
            continue
        if key not in aggregated:
            aggregated[key]    = stat
            evidence_map[key]  = obs.get("evidence", "")
            timestamp_map[key] = obs.get("frame_timestamp", 0.0)
        else:
            if status_rank.get(stat, 1) < status_rank.get(aggregated[key], 1):
                aggregated[key]    = stat
                evidence_map[key]  = obs.get("evidence", "")
                timestamp_map[key] = obs.get("frame_timestamp", 0.0)

    # --- Score arithmetic ----------------------------------------------------
    total_indicators     = len(INDICATOR_REGISTRY)
    assessable_weight    = 0
    retained_weight      = 0
    score_breakdown: List[dict] = []
    alerts:           List[dict] = []
    uncertain_indicators: List[dict] = []

    for key, meta in INDICATOR_REGISTRY.items():
        weight = meta["weight"]
        status = aggregated.get(key)

        if status is None:
            # Not observed in any frame — treated as uncertain (insufficient evidence)
            uncertain_indicators.append({
                "indicator": key,
                "label":     meta["label"],
                "reason":    "Not present in any sampled frame.",
            })
            score_breakdown.append({
                "indicator": key,
                "label":     meta["label"],
                "weight":    weight,
                "status":    "not_in_frame",
                "points_at_risk": weight,
                "scored":    False,
                "note":      "Indicator not visible in sampled frames; excluded from score.",
            })
            continue

        if status == "uncertain":
            uncertain_indicators.append({
                "indicator": key,
                "label":     meta["label"],
                "reason":    evidence_map.get(key, "Insufficient visual evidence."),
            })
            score_breakdown.append({
                "indicator": key,
                "label":     meta["label"],
                "weight":    weight,
                "status":    "uncertain",
                "points_at_risk": weight,
                "scored":    False,
                "note":      "Uncertain — excluded from score arithmetic.",
            })
            continue

        # Definitive: observed or not_observed
        assessable_weight += weight
        points_retained    = weight if status == "observed" else 0
        retained_weight   += points_retained

        entry = {
            "indicator":     key,
            "label":         meta["label"],
            "weight":        weight,
            "status":        status,
            "points_earned": points_retained,
            "evidence":      evidence_map.get(key, ""),
            "timestamp_s":   timestamp_map.get(key, 0.0),
            "scored":        True,
        }
        score_breakdown.append(entry)

        if status == "not_observed":
            alerts.append({
                "type":        "hygiene_deficit",
                "indicator":   key,
                "label":       meta["label"],
                "evidence":    evidence_map.get(key, "Not observed in sampled frames."),
                "timestamp_s": timestamp_map.get(key, 0.0),
                "severity":    "high" if weight >= 20 else ("medium" if weight >= 10 else "low"),
                "action":      f"Ensure {meta['label'].lower()} is maintained in all food preparation areas.",
            })

    # --- Final score ---------------------------------------------------------
    if assessable_weight > 0:
        raw_score = (retained_weight / assessable_weight) * 100
    else:
        raw_score = 0.0

    compliance_score = max(0, min(100, round(raw_score)))
    coverage         = round(assessable_weight / TOTAL_WEIGHT, 3) if TOTAL_WEIGHT > 0 else 0.0
    assessable_count = sum(1 for b in score_breakdown if b.get("scored"))

    return {
        "compliance_score":       compliance_score,
        "assessable_indicators":  assessable_count,
        "total_indicators":       total_indicators,
        "coverage":               coverage,
        "score_breakdown":        score_breakdown,
        "alerts":                 alerts,
        "uncertain_indicators":   uncertain_indicators,
        "limitations":            _LIMITATIONS,
        "disclaimer":             _DISCLAIMER,
    }


def grade_from_score(score: int) -> str:
    """Map numeric score to descriptive grade label."""
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Needs Attention"
    return "Critical Issues"


def build_hygiene_result(
    score_result: dict,
    all_observations: List[dict],
    frames_telemetry: Optional[dict],
    gemini_model_used: str,
    media_type: str,               # "image" or "video"
) -> dict:
    """
    Compose the complete Activity 4.1 API response.

    Merges compliance score, raw observations, frame telemetry,
    and backward-compatible legacy fields (score, grade, findings, etc.).
    """
    score   = score_result["compliance_score"]
    grade   = grade_from_score(score)
    engine  = f"{gemini_model_used} Vision" if gemini_model_used else "Gemini Vision"

    # Backward-compatible findings list (for existing Hygiene.jsx checklist)
    findings: List[dict] = []
    for obs in all_observations:
        findings.append({
            "ok":            obs["status"] == "observed",
            "text":          f"[t={obs['frame_timestamp']}s] {obs['label']}: {obs['evidence']}",
            "indicator":     obs["indicator"],
            "status":        obs["status"],
            "timestamp_s":   obs["frame_timestamp"],
        })

    # Actionable corrections from alerts
    actionable_corrections = [
        a["action"] for a in score_result.get("alerts", [])
    ]
    if not actionable_corrections and score < 100:
        actionable_corrections = [
            "Conduct a detailed on-site inspection by a qualified food safety auditor.",
            "Review food handling SOPs with all food preparation staff.",
        ]

    rubric_explanation = (
        "Visual Screening Score — 85–100: Excellent; 70–84: Good (minor attention needed); "
        "50–69: Needs Attention; Below 50: Critical Issues. "
        f"Score computed from {score_result['assessable_indicators']} of "
        f"{score_result['total_indicators']} indicators "
        f"(coverage: {score_result['coverage'] * 100:.0f}%). "
        "Uncertain observations excluded from arithmetic."
    )

    return {
        # ---- Activity 4.1 canonical fields ----
        "compliance_score":       score,
        "assessable_indicators":  score_result["assessable_indicators"],
        "total_indicators":       score_result["total_indicators"],
        "coverage":               score_result["coverage"],
        "score_breakdown":        score_result["score_breakdown"],
        "alerts":                 score_result["alerts"],
        "uncertain_indicators":   score_result["uncertain_indicators"],
        "observations":           all_observations,
        "media_type":             media_type,
        "frames_telemetry":       frames_telemetry,
        "limitations":            score_result["limitations"],
        # ---- Backward-compatible fields (existing Hygiene.jsx) ----
        "score":                  score,           # alias
        "grade":                  grade,
        "rubric_explanation":     rubric_explanation,
        "summary":                _build_summary(score, grade, score_result, all_observations),
        "findings":               findings,
        "actionable_corrections": actionable_corrections,
        "disclaimer":             score_result["disclaimer"],
        "engine":                 engine,
    }


def _build_summary(
    score: int,
    grade: str,
    score_result: dict,
    observations: List[dict],
) -> str:
    n_ok      = sum(1 for o in observations if o["status"] == "observed")
    n_deficit = sum(1 for o in observations if o["status"] == "not_observed")
    n_uncert  = sum(1 for o in observations if o["status"] == "uncertain")
    cov_pct   = round(score_result["coverage"] * 100)

    parts = [f"Visual screening score: {score}/100 ({grade})."]
    parts.append(
        f"{n_ok} indicator(s) confirmed present, "
        f"{n_deficit} deficit(s) detected, "
        f"{n_uncert} uncertain."
    )
    parts.append(f"Evidence coverage: {cov_pct}% of monitored indicators.")
    if score_result["alerts"]:
        parts.append("Corrective action required — see alerts.")
    return " ".join(parts)
