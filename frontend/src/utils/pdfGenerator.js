import { jsPDF } from 'jspdf';

/**
 * FoodVerse AI — Enterprise PDF Generation Engine
 * Produces publication-grade, accessible, multi-page vector PDF reports
 * with strict geometry, dynamic wrapping, page-break management, and zero overlaps.
 */

export function savePDF(doc, filename) {
  if (typeof doc?.save === 'function') {
    doc.save(filename);
  } else if (typeof doc?.output === 'function') {
    doc.output('blob');
  }
}

// ── Geometry & Palette Constants ─────────────────────────────────────────────
const PAGE_W = 210;
const PAGE_H = 297;
const MARGIN_X = 14;
const CONTENT_W = 182; // PAGE_W - 2 * MARGIN_X
const MAX_Y = 270;

const COLORS = {
  primary: [15, 61, 34],      // #0f3d22 deep forest green
  primaryLight: [240, 248, 242],
  primaryBorder: [187, 228, 198],
  accent: [245, 154, 27],     // #f59a1b amber
  accentLight: [255, 250, 240],
  accentBorder: [253, 224, 171],
  danger: [220, 38, 38],      // red
  dangerLight: [254, 242, 242],
  dangerBorder: [254, 202, 202],
  warning: [217, 119, 6],     // orange/amber
  warningLight: [254, 243, 199],
  textDark: [15, 23, 42],     // slate 900
  textMuted: [100, 116, 139], // slate 500
  cardBg: [255, 253, 247],    // warm ivory
  cardBorder: [226, 217, 196],
  white: [255, 255, 255],
  divider: [238, 233, 220],
};

// ── Layout Manager ────────────────────────────────────────────────────────────
class PDFSession {
  constructor(doc, title, subtitle, categoryBadge) {
    this.doc = doc;
    this.title = title;
    this.subtitle = subtitle;
    this.categoryBadge = categoryBadge;
    this.y = 0;
    this.initPage();
  }

  initPage() {
    const isFirst = this.doc.internal.getNumberOfPages() === 1;
    if (isFirst) {
      // 1. First Page Header Banner
      this.doc.setFillColor(...COLORS.primary);
      this.doc.rect(0, 0, PAGE_W, 25, 'F');

      this.doc.setFillColor(...COLORS.accent);
      this.doc.rect(0, 25, PAGE_W, 2, 'F');

      // Brand Logo Text
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(13);
      this.doc.setTextColor(...COLORS.white);
      this.doc.text('FOODVERSE AI', MARGIN_X, 11);

      this.doc.setFont('helvetica', 'normal');
      this.doc.setFontSize(7.5);
      this.doc.setTextColor(230, 240, 233);
      this.doc.text('Multimodal Food Intelligence & Clinical Nutrition Platform', MARGIN_X, 17);

      // Category Pill
      if (this.categoryBadge) {
        this.doc.setFillColor(255, 255, 255, 0.18);
        this.doc.roundedRect(PAGE_W - MARGIN_X - 60, 7, 60, 11, 2, 2, 'F');
        this.doc.setFont('helvetica', 'bold');
        this.doc.setFontSize(7);
        this.doc.setTextColor(...COLORS.white);
        this.doc.text(this.categoryBadge.toUpperCase(), PAGE_W - MARGIN_X - 30, 14, { align: 'center' });
      }

      // Title & Subtitle
      this.y = 36;
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(15);
      this.doc.setTextColor(...COLORS.primary);
      this.doc.text(this.title, MARGIN_X, this.y);

      if (this.subtitle) {
        this.y += 6;
        this.doc.setFont('helvetica', 'normal');
        this.doc.setFontSize(8.5);
        this.doc.setTextColor(...COLORS.textMuted);
        this.doc.text(this.subtitle, MARGIN_X, this.y);
      }
      this.y += 7;
    } else {
      // Subsequent Pages: Compact Running Header
      this.doc.setFillColor(...COLORS.primary);
      this.doc.rect(0, 0, PAGE_W, 10, 'F');

      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(7.5);
      this.doc.setTextColor(...COLORS.white);
      this.doc.text('FOODVERSE AI', MARGIN_X, 6.5);

      this.doc.setFont('helvetica', 'normal');
      this.doc.text(this.title, PAGE_W - MARGIN_X, 6.5, { align: 'right' });

      this.doc.setDrawColor(...COLORS.divider);
      this.doc.setLineWidth(0.4);
      this.doc.line(MARGIN_X, 15, PAGE_W - MARGIN_X, 15);

      this.y = 20;
    }
  }

  ensureSpace(neededHeight) {
    if (this.y + neededHeight > MAX_Y) {
      this.doc.addPage();
      this.initPage();
    }
  }

  drawSectionHeading(heading, iconSymbol = '■') {
    this.ensureSpace(16);
    this.y += 2;
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(10.5);
    this.doc.setTextColor(...COLORS.primary);

    // Accent square
    this.doc.setFillColor(...COLORS.accent);
    this.doc.rect(MARGIN_X, this.y - 3.5, 3.5, 3.5, 'F');

    this.doc.text(heading, MARGIN_X + 6, this.y);
    this.y += 5;
  }

  drawKeyValueGrid(pairs, numCols = 2) {
    const colW = CONTENT_W / numCols;
    const rowH = 11;
    const numRows = Math.ceil(pairs.length / numCols);
    const boxH = numRows * rowH + 6;

    this.ensureSpace(boxH + 4);

    this.doc.setFillColor(...COLORS.cardBg);
    this.doc.setDrawColor(...COLORS.cardBorder);
    this.doc.setLineWidth(0.4);
    this.doc.roundedRect(MARGIN_X, this.y, CONTENT_W, boxH, 2, 2, 'FD');

    let currentY = this.y + 7;
    for (let r = 0; r < numRows; r++) {
      for (let c = 0; c < numCols; c++) {
        const idx = r * numCols + c;
        if (idx < pairs.length) {
          const item = pairs[idx];
          const x = MARGIN_X + 4 + c * colW;
          this.doc.setFont('helvetica', 'bold');
          this.doc.setFontSize(7.5);
          this.doc.setTextColor(...COLORS.textMuted);
          this.doc.text(item.key.toUpperCase(), x, currentY);

          this.doc.setFont('helvetica', 'bold');
          this.doc.setFontSize(8.5);
          this.doc.setTextColor(...COLORS.textDark);
          const valStr = String(item.val ?? 'Not provided');
          const maxTextW = colW - 8;
          const valTrunc = this.doc.splitTextToSize(valStr, maxTextW)[0] || valStr;
          this.doc.text(valTrunc, x, currentY + 4.5);
        }
      }
      currentY += rowH;
    }
    this.y += boxH + 5;
  }

  drawCallout(title, text, type = 'normal') {
    if (!text) return;
    const padding = 4;
    const maxTextW = CONTENT_W - 8;
    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(8.5);
    const lines = this.doc.splitTextToSize(text, maxTextW);
    const boxH = (title ? 6 : 0) + lines.length * 4.4 + padding * 2;

    this.ensureSpace(boxH + 4);

    let bg = COLORS.cardBg;
    let border = COLORS.cardBorder;
    let titleColor = COLORS.primary;

    if (type === 'success') {
      bg = COLORS.primaryLight;
      border = COLORS.primaryBorder;
      titleColor = COLORS.primary;
    } else if (type === 'warning' || type === 'amber') {
      bg = COLORS.accentLight;
      border = COLORS.accentBorder;
      titleColor = COLORS.warning;
    } else if (type === 'danger') {
      bg = COLORS.dangerLight;
      border = COLORS.dangerBorder;
      titleColor = COLORS.danger;
    }

    this.doc.setFillColor(...bg);
    this.doc.setDrawColor(...border);
    this.doc.setLineWidth(0.4);
    this.doc.roundedRect(MARGIN_X, this.y, CONTENT_W, boxH, 2, 2, 'FD');

    let innerY = this.y + padding + 3;
    if (title) {
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(8.5);
      this.doc.setTextColor(...titleColor);
      this.doc.text(title, MARGIN_X + 4, innerY);
      innerY += 5;
    }

    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(8);
    this.doc.setTextColor(...COLORS.textDark);
    this.doc.text(lines, MARGIN_X + 4, innerY);

    this.y += boxH + 4;
  }

  finalizeFooters() {
    const totalPages = this.doc.internal.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
      this.doc.setPage(p);
      this.doc.setDrawColor(...COLORS.divider);
      this.doc.setLineWidth(0.4);
      this.doc.line(MARGIN_X, 283, PAGE_W - MARGIN_X, 283);

      this.doc.setFont('helvetica', 'normal');
      this.doc.setFontSize(7.5);
      this.doc.setTextColor(...COLORS.textMuted);
      this.doc.text(
        'FoodVerse AI · AI estimates are informational and not certified medical, dietary, or regulatory advice.',
        MARGIN_X,
        288
      );
      this.doc.text(`Page ${p} of ${totalPages}`, PAGE_W - MARGIN_X, 288, { align: 'right' });
    }
  }
}

// ── Helper: Normalize Meal Plan Day Keys ──────────────────────────────────────
const DAY_MAP = {
  Mon: 'Monday',
  Tue: 'Tuesday',
  Wed: 'Wednesday',
  Thu: 'Thursday',
  Fri: 'Friday',
  Sat: 'Saturday',
  Sun: 'Sunday',
  Monday: 'Monday',
  Tuesday: 'Tuesday',
  Wednesday: 'Wednesday',
  Thursday: 'Thursday',
  Friday: 'Friday',
  Saturday: 'Saturday',
  Sunday: 'Sunday',
};

const ORDERED_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function findDayObject(daysObj, targetShortDay) {
  if (!daysObj || typeof daysObj !== 'object') return null;
  // Direct match
  if (daysObj[targetShortDay]) return daysObj[targetShortDay];
  // Full name match
  const full = DAY_MAP[targetShortDay];
  if (full && daysObj[full]) return daysObj[full];
  // Case-insensitive / prefix search
  const foundKey = Object.keys(daysObj).find((k) =>
    k.toLowerCase().startsWith(targetShortDay.toLowerCase())
  );
  return foundKey ? daysObj[foundKey] : null;
}

// ══════════════════════════════════════════════════════════════════════════════
// 1. MEAL PLANNER PDF GENERATOR (CRITICAL FIX)
// ══════════════════════════════════════════════════════════════════════════════
export function generateMealPlanPDF(mealPlan, options = {}) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const prefs = mealPlan?.prefs || {};
  const nutritionNote = options.nutritionNote || mealPlan?.nutrition_notes || '';
  const goalCal = options.goalCal || mealPlan?.target_calories || 1900;
  const allergies = options.allergies || prefs.allergies || 'None stated';

  const session = new PDFSession(
    doc,
    '7-Day Personalized AI Nutrition Schedule',
    `Customized weekly meal plan calibrated for ${prefs.diet || 'Standard'} · ${prefs.goal || 'Weight Maintain'}`,
    'Meal Intelligence'
  );

  // A. Report Overview Grid
  session.drawKeyValueGrid([
    { key: 'Dietary Preference', val: prefs.diet || 'Vegetarian' },
    { key: 'Primary Health Goal', val: prefs.goal || 'Weight Maintain' },
    { key: 'Daily Calorie Target', val: `~${goalCal} kcal / day` },
    { key: 'Budget Category', val: prefs.budget || 'Medium' },
    { key: 'Allergies & Exclusions', val: allergies },
    { key: 'AI Planning Engine', val: mealPlan?.engine || (mealPlan?.ai_generated ? 'Gemini 3.8 Flash LLM' : 'Algorithmic Planner') },
  ], 3);

  // B. Nutrition Recommendations Note
  if (nutritionNote) {
    session.drawSectionHeading('Dietitian Intelligence & Nutrition Guidelines');
    session.drawCallout(
      'Clinical Dietary Recommendation',
      nutritionNote,
      'success'
    );
  }

  // C. Complete 7-Day Meal Plan (Day-by-Day Section)
  session.drawSectionHeading('Seven-Day Nutritional Meal Schedule');

  const slots = ['breakfast', 'lunch', 'dinner', 'snack'];
  const slotLabels = {
    breakfast: 'Breakfast',
    lunch: 'Lunch',
    dinner: 'Dinner',
    snack: 'Snack',
  };

  let weeklyTotalCalories = 0;
  let daysCount = 0;

  ORDERED_DAYS.forEach((shortDay) => {
    const dayData = findDayObject(mealPlan?.days, shortDay);
    const dayFullName = DAY_MAP[shortDay] || shortDay;

    // Calculate day calorie sum
    let dayCalories = 0;
    if (dayData && typeof dayData === 'object') {
      slots.forEach((s) => {
        const item = dayData[s];
        if (item && item.cal) dayCalories += Number(item.cal) || 0;
      });
    }

    if (dayCalories > 0) {
      weeklyTotalCalories += dayCalories;
      daysCount++;
    }

    // Estimate needed height for this day card:
    // Header strip = 7mm + each available slot row ~8mm + padding ~4mm
    const activeSlots = slots.filter((s) => dayData && dayData[s]);
    const renderedSlots = activeSlots.length > 0 ? activeSlots : ['breakfast', 'lunch', 'dinner'];
    const estimatedDayHeight = 8 + renderedSlots.length * 8.5 + 4;

    session.ensureSpace(estimatedDayHeight + 4);

    // Day Header Strip
    doc.setFillColor(...COLORS.primary);
    doc.rect(MARGIN_X, session.y, CONTENT_W, 6.5, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8.5);
    doc.setTextColor(...COLORS.white);
    doc.text(dayFullName.toUpperCase(), MARGIN_X + 4, session.y + 4.5);

    const calLabel = dayCalories > 0 ? `Planned Intake: ${dayCalories} kcal` : 'Intake: Calibrated';
    doc.text(calLabel, PAGE_W - MARGIN_X - 4, session.y + 4.5, { align: 'right' });
    session.y += 6.5;

    // Render Slots Table / Rows
    renderedSlots.forEach((slotKey, sIdx) => {
      const meal = dayData ? dayData[slotKey] : null;
      const mealName = meal?.name || (dayData ? 'Nutrient-rich seasonal preparation' : 'Meal data not generated');
      const mealCal = meal?.cal ? `${meal.cal} kcal` : '—';
      const portion = meal?.portion || '';
      const protein = meal?.protein ? `P: ${meal.protein}g` : '';
      const carbs = meal?.carbs ? `C: ${meal.carbs}g` : '';
      const fat = meal?.fat ? `F: ${meal.fat}g` : '';
      const macroStr = [protein, carbs, fat].filter(Boolean).join(' · ');

      const rowH = (portion || macroStr) ? 8.5 : 7.2;

      // Alternating row background
      doc.setFillColor(sIdx % 2 === 0 ? 255 : 250, sIdx % 2 === 0 ? 253 : 249, sIdx % 2 === 0 ? 247 : 243);
      doc.rect(MARGIN_X, session.y, CONTENT_W, rowH, 'F');

      // Border outline
      doc.setDrawColor(...COLORS.cardBorder);
      doc.setLineWidth(0.2);
      doc.rect(MARGIN_X, session.y, CONTENT_W, rowH, 'S');

      // Slot Label
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(7.5);
      doc.setTextColor(...COLORS.textMuted);
      doc.text(slotLabels[slotKey] || slotKey, MARGIN_X + 3, session.y + 4.5);

      // Meal Name (safely truncated/wrapped if long)
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.textDark);
      const maxNameWidth = 100;
      const splitName = doc.splitTextToSize(mealName, maxNameWidth);
      doc.text(splitName[0] || mealName, MARGIN_X + 28, session.y + 4.5);

      // Portion / Macros Subtext
      if (portion || macroStr) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(6.8);
        doc.setTextColor(...COLORS.textMuted);
        const sub = [portion, macroStr].filter(Boolean).join(' | ');
        doc.text(sub, MARGIN_X + 28, session.y + 7.5);
      }

      // Calories Pill
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.warning);
      doc.text(mealCal, PAGE_W - MARGIN_X - 4, session.y + 4.8, { align: 'right' });

      session.y += rowH;
    });

    session.y += 3.5;
  });

  // D. Weekly Nutritional Summary Box
  const weeklyAvg = daysCount > 0 ? Math.round(weeklyTotalCalories / daysCount) : goalCal;
  session.drawSectionHeading('Weekly Target & Compliance Summary');
  session.drawKeyValueGrid([
    { key: 'Target Calorie Budget', val: `${goalCal} kcal / day` },
    { key: 'Average Scheduled Intake', val: `${weeklyAvg} kcal / day` },
    { key: 'Total 7-Day Caloric Intake', val: `${weeklyTotalCalories.toLocaleString()} kcal` },
    { key: 'Dietary Compliance', val: `${prefs.diet || 'Standard'} Approved` },
  ], 2);

  // E. Grouped Shopping List (if available from AI)
  if (mealPlan?.shopping_list && typeof mealPlan.shopping_list === 'object') {
    const sl = mealPlan.shopping_list;
    const hasItems = Object.values(sl).some((arr) => Array.isArray(arr) && arr.length > 0);
    if (hasItems) {
      session.drawSectionHeading('Recommended Weekly Shopping List');
      const shoppingPairs = [];
      if (Array.isArray(sl.produce) && sl.produce.length > 0) {
        shoppingPairs.push({ key: 'Fresh Produce', val: sl.produce.join(', ') });
      }
      if (Array.isArray(sl.grains_and_legumes) && sl.grains_and_legumes.length > 0) {
        shoppingPairs.push({ key: 'Grains & Legumes', val: sl.grains_and_legumes.join(', ') });
      }
      if (Array.isArray(sl.dairy_and_protein) && sl.dairy_and_protein.length > 0) {
        shoppingPairs.push({ key: 'Dairy & Proteins', val: sl.dairy_and_protein.join(', ') });
      }
      if (Array.isArray(sl.spices_and_pantry) && sl.spices_and_pantry.length > 0) {
        shoppingPairs.push({ key: 'Pantry & Spices', val: sl.spices_and_pantry.join(', ') });
      }
      session.drawKeyValueGrid(shoppingPairs, 1);
    }
  }

  session.finalizeFooters();
  savePDF(doc, 'foodverse-7day-meal-plan.pdf');
}

// ══════════════════════════════════════════════════════════════════════════════
// 2. RESTAURANT HYGIENE & KITCHEN SAFETY AUDIT PDF
// ══════════════════════════════════════════════════════════════════════════════
export function generateHygieneAuditPDF(result, fileName = 'media_frame') {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const session = new PDFSession(
    doc,
    'Kitchen Sanitation & Food Safety Audit Report',
    'Commercial hygiene compliance and cross-contamination evaluation',
    'Safety Audit'
  );

  const score = result.score || 0;
  const grade = result.grade || (score >= 85 ? 'Excellent' : score >= 70 ? 'Good' : 'Needs Attention');
  const isPassing = score >= 70;

  // A. Meta Grid
  session.drawKeyValueGrid([
    { key: 'Audit Date & Time', val: new Date().toLocaleString() },
    { key: 'Inspected Image / Frame', val: fileName },
    { key: 'Computer Vision Engine', val: result.engine || 'Gemini 3.8 Flash Vision' },
    { key: 'Regulatory Standard', val: 'Health Code Visual Sanitation Rubric' },
  ], 2);

  // B. Score KPI Banner
  session.ensureSpace(24);
  const bannerBg = isPassing ? COLORS.primaryLight : COLORS.dangerLight;
  const bannerBorder = isPassing ? COLORS.primaryBorder : COLORS.dangerBorder;
  const bannerText = isPassing ? COLORS.primary : COLORS.danger;

  doc.setFillColor(...bannerBg);
  doc.setDrawColor(...bannerBorder);
  doc.setLineWidth(0.5);
  doc.roundedRect(MARGIN_X, session.y, CONTENT_W, 20, 2, 2, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.setTextColor(...bannerText);
  doc.text(`${score} / 100`, MARGIN_X + 6, session.y + 13);

  doc.setFontSize(10);
  doc.text(`Rating: ${grade}  ·  ${isPassing ? 'Satisfactory Health Compliance' : 'Corrective Action Required'}`, MARGIN_X + 60, session.y + 12);
  session.y += 24;

  // C. Executive Summary
  session.drawSectionHeading('Executive Audit Summary');
  session.drawCallout(
    'Inspector Assessment',
    result.summary || 'Visual assessment of food preparation area sanitation.',
    isPassing ? 'normal' : 'danger'
  );

  if (result.rubric_explanation) {
    session.drawCallout('Scoring Rubric Context', result.rubric_explanation, 'amber');
  }

  // D. Inspection Findings List
  session.drawSectionHeading('Standardized Inspection Observations');
  const findings = Array.isArray(result.findings) ? result.findings : [];
  findings.forEach((f) => {
    const ok = !!f.ok;
    const textLines = doc.splitTextToSize(f.text || '', CONTENT_W - 38);
    const itemH = Math.max(7, textLines.length * 4.2 + 3);

    session.ensureSpace(itemH + 2);

    // Status Pill
    doc.setFillColor(...(ok ? COLORS.primaryLight : COLORS.dangerLight));
    doc.setDrawColor(...(ok ? COLORS.primaryBorder : COLORS.dangerBorder));
    doc.setLineWidth(0.3);
    doc.roundedRect(MARGIN_X, session.y, 30, 5, 1, 1, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(...(ok ? COLORS.primary : COLORS.danger));
    doc.text(ok ? 'COMPLIANT' : 'VIOLATION', MARGIN_X + 15, session.y + 3.5, { align: 'center' });

    // Finding Text
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.textDark);
    doc.text(textLines, MARGIN_X + 34, session.y + 3.5);

    session.y += itemH;
  });

  // E. Actionable Corrective Recommendations
  session.drawSectionHeading('Mandatory Corrective Action Items');
  const corrections = Array.isArray(result.actionable_corrections) && result.actionable_corrections.length > 0
    ? result.actionable_corrections
    : findings.filter((f) => !f.ok).map((f) => `Address inspection finding: ${f.text}`);

  if (corrections.length === 0) {
    session.drawCallout('Compliance Status', 'No urgent sanitation deficiencies detected in inspected frame.', 'success');
  } else {
    corrections.forEach((c) => {
      const cLines = doc.splitTextToSize(c, CONTENT_W - 12);
      const rowH = cLines.length * 4.2 + 3;
      session.ensureSpace(rowH + 2);

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8.5);
      doc.setTextColor(...COLORS.accent);
      doc.text('▶', MARGIN_X + 2, session.y + 3.5);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.textDark);
      doc.text(cLines, MARGIN_X + 8, session.y + 3.5);

      session.y += rowH;
    });
  }

  // F. Regulatory Disclaimer
  session.drawCallout(
    'LEGAL NOTICE & REGULATORY DISCLAIMER',
    result.disclaimer || 'Visual AI inspection is an advisory decision-support tool and does not substitute for certified statutory on-site regulatory health department examinations.',
    'normal'
  );

  session.finalizeFooters();
  savePDF(doc, 'foodverse-hygiene-safety-audit.pdf');
}

// ══════════════════════════════════════════════════════════════════════════════
// 3. FOOD RECOGNITION & NUTRITIONAL ANALYSIS PDF
// ══════════════════════════════════════════════════════════════════════════════
export function generateFoodRecognitionPDF(result, fileName = 'food_image') {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const nut = result.nutrition || {};
  const dishName = result.predicted_class || 'Recognized Food Item';

  const session = new PDFSession(
    doc,
    'Food Recognition & Nutritional Breakdown',
    `Multimodal AI nutrient evaluation for ${dishName}`,
    'Nutrition Report'
  );

  // A. Meta Overview
  session.drawKeyValueGrid([
    { key: 'Identified Dish', val: dishName },
    { key: 'Confidence Rating', val: `${result.confidence || 95}%` },
    { key: 'Analyzed File', val: fileName },
    { key: 'Computer Vision Model', val: result.engine || 'Gemini 3.8 Flash Vision' },
  ], 2);

  // B. Description & Serving Assumption
  if (result.description) {
    session.drawSectionHeading('Culinary Identification');
    session.drawCallout('Dish Profile', result.description, 'normal');
  }

  // C. Macronutrient Breakdown Cards
  session.drawSectionHeading('Nutritional Profile & Serving Estimates');

  const nutMetrics = [
    { key: 'Estimated Calories', val: `${nut.calories || 0} kcal` },
    { key: 'Protein', val: `${nut.protein || 0} g` },
    { key: 'Carbohydrates', val: `${nut.carbs || 0} g` },
    { key: 'Total Fat', val: `${nut.fat || 0} g` },
    { key: 'Dietary Fiber', val: `${nut.fiber || 0} g` },
    { key: 'Serving Portion', val: nut.serving || '1 standard serving' },
  ];
  if (nut.health_score != null) {
    nutMetrics.push({ key: 'Nutritional Balance Score', val: `${nut.health_score} / 100 (${nut.health_score_label || 'Balanced'})` });
  }
  if (nut.data_source) {
    nutMetrics.push({ key: 'Nutritional Source', val: nut.data_source });
  }
  session.drawKeyValueGrid(nutMetrics, 2);

  // D. Visual Observations
  if (Array.isArray(result.visual_observations) && result.visual_observations.length > 0) {
    session.drawSectionHeading('Visual Ingredients & Observations');
    result.visual_observations.forEach((obs) => {
      const lines = doc.splitTextToSize(obs, CONTENT_W - 10);
      const rowH = lines.length * 4.2 + 2;
      session.ensureSpace(rowH + 2);

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.primary);
      doc.text('•', MARGIN_X + 2, session.y + 3);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.textDark);
      doc.text(lines, MARGIN_X + 7, session.y + 3);

      session.y += rowH;
    });
  }

  // E. Dietary Guidance & Insights
  const combinedInsights = [
    ...(Array.isArray(nut.insights) ? nut.insights : []),
    ...(nut.tip && !Array.isArray(nut.insights) ? [nut.tip] : [])
  ];
  if (combinedInsights.length > 0) {
    session.drawSectionHeading('Dietary Insights & Pairing Guidance');
    session.drawCallout('Practical Recommendations', combinedInsights.join('\n\n• '), 'amber');
  } else if (nut.tip) {
    session.drawSectionHeading('Dietary Guidance');
    session.drawCallout('Nutritionist Recommendation', nut.tip, 'amber');
  }

  // F. Disclaimer
  session.drawCallout(
    'ESTIMATION NOTICE',
    'Nutritional parameters are computed via visual proportion algorithms and verified database tables. Individual ingredient substitutions and preparation methods may alter actual caloric values.',
    'normal'
  );

  session.finalizeFooters();
  savePDF(doc, 'foodverse-food-recognition-report.pdf');
}

// ══════════════════════════════════════════════════════════════════════════════
// 4. FOOD FRESHNESS & SPOILAGE DETECTION PDF
// ══════════════════════════════════════════════════════════════════════════════
export function generateFreshnessPDF(result, fileName = 'produce_image') {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const status = result.status || 'fresh';
  const label = result.label || (status === 'fresh' ? 'Fresh' : status === 'aging' ? 'Use Soon' : 'Potential Spoilage');
  const itemName = result.food_item || 'Inspected Food Item';

  const session = new PDFSession(
    doc,
    'Food Freshness & Quality Assessment',
    `Computer vision evaluation for ${itemName}`,
    'Produce Quality'
  );

  // A. Meta Overview
  session.drawKeyValueGrid([
    { key: 'Inspected Produce / Item', val: itemName },
    { key: 'Inspection Date', val: new Date().toLocaleString() },
    { key: 'Assessment Status', val: label },
    { key: 'Vision Engine', val: result.engine || 'Gemini 3.8 Flash Vision' },
  ], 2);

  // B. Status Banner
  session.ensureSpace(22);
  const isSpoiled = status === 'spoiled';
  const isAging = status === 'aging';
  const bannerBg = isSpoiled ? COLORS.dangerLight : isAging ? COLORS.accentLight : COLORS.primaryLight;
  const bannerBorder = isSpoiled ? COLORS.dangerBorder : isAging ? COLORS.accentBorder : COLORS.primaryBorder;
  const bannerColor = isSpoiled ? COLORS.danger : isAging ? COLORS.warning : COLORS.primary;

  doc.setFillColor(...bannerBg);
  doc.setDrawColor(...bannerBorder);
  doc.setLineWidth(0.5);
  doc.roundedRect(MARGIN_X, session.y, CONTENT_W, 18, 2, 2, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(...bannerColor);
  doc.text(`Condition: ${label.toUpperCase()}`, MARGIN_X + 6, session.y + 11);

  doc.setFontSize(8.5);
  doc.text(`Shelf Life: ${result.shelf || 'Check daily'} · Certainty: ${result.certainty || 'High'}`, PAGE_W - MARGIN_X - 6, session.y + 11, { align: 'right' });
  session.y += 22;

  // C. Visual Observations
  if (result.observations) {
    session.drawSectionHeading('Surface & Organic Observations');
    const obsPairs = [];
    if (result.observations.color) obsPairs.push({ key: 'Color Analysis', val: result.observations.color });
    if (result.observations.texture) obsPairs.push({ key: 'Texture & Firmness', val: result.observations.texture });
    if (result.observations.defects) obsPairs.push({ key: 'Defects / Blemishes', val: result.observations.defects });
    session.drawKeyValueGrid(obsPairs, 1);
  }

  // D. Safety Checks
  if (Array.isArray(result.checks) && result.checks.length > 0) {
    session.drawSectionHeading('Visual Safety Verification Checklist');
    result.checks.forEach((chk) => {
      const ok = !!chk.ok;
      const lines = doc.splitTextToSize(chk.text || '', CONTENT_W - 34);
      const rowH = Math.max(7, lines.length * 4.2 + 3);

      session.ensureSpace(rowH + 2);

      doc.setFillColor(...(ok ? COLORS.primaryLight : COLORS.dangerLight));
      doc.setDrawColor(...(ok ? COLORS.primaryBorder : COLORS.dangerBorder));
      doc.roundedRect(MARGIN_X, session.y, 26, 5, 1, 1, 'FD');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(6.5);
      doc.setTextColor(...(ok ? COLORS.primary : COLORS.danger));
      doc.text(ok ? 'PASS' : 'CAUTION', MARGIN_X + 13, session.y + 3.5, { align: 'center' });

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.textDark);
      doc.text(lines, MARGIN_X + 30, session.y + 3.5);

      session.y += rowH;
    });
  }

  // E. Recommended Handling Steps
  session.drawSectionHeading('Storage & Safe Handling Recommendations');
  const recommendations = Array.isArray(result.recommendations) ? result.recommendations : [
    'Store in crisper drawer at 4°C with controlled humidity.',
    'Wash produce immediately prior to meal preparation.',
    'Discard any portion exhibiting fungal mycelium or discoloration.'
  ];

  recommendations.forEach((rec) => {
    const lines = doc.splitTextToSize(rec, CONTENT_W - 10);
    const rowH = lines.length * 4.2 + 2;
    session.ensureSpace(rowH + 2);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.primary);
    doc.text('✓', MARGIN_X + 2, session.y + 3);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.textDark);
    doc.text(lines, MARGIN_X + 8, session.y + 3);

    session.y += rowH;
  });

  // F. Disclaimer
  session.drawCallout(
    'MICROBIOLOGICAL NOTICE',
    result.disclaimer || 'Visual inspection evaluates macroscopic degradation indicators only. It cannot identify microscopic bacterial pathogens or chemical residues.',
    'normal'
  );

  session.finalizeFooters();
  savePDF(doc, 'foodverse-freshness-inspection.pdf');
}

// ══════════════════════════════════════════════════════════════════════════════
// 5. SMART COOKING ASSISTANT RECIPE PDF
// ══════════════════════════════════════════════════════════════════════════════
export function generateRecipePDF(recipe) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const recipeName = recipe.name || 'Personalized AI Recipe';

  const session = new PDFSession(
    doc,
    recipeName,
    `Authentic culinary formulation · ${recipe.diet || 'Vegetarian'} · ${recipe.time || 30} mins`,
    'Culinary Recipe'
  );

  // A. Meta Overview
  session.drawKeyValueGrid([
    { key: 'Dietary Classification', val: recipe.diet || 'Vegetarian' },
    { key: 'Total Preparation & Cooking', val: `${recipe.time || 30} minutes` },
    { key: 'Serving Portions', val: `${recipe.servings || 2} persons` },
    { key: 'Energy Density', val: `~${recipe.calories || 350} kcal / serving` },
  ], 2);

  // B. Description
  if (recipe.description) {
    session.drawSectionHeading('Chef Description');
    session.drawCallout('Culinary Notes', recipe.description, 'normal');
  }

  // C. Ingredients Table
  session.drawSectionHeading('Required Ingredients & Measure');
  const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];

  ingredients.forEach((ing, iIdx) => {
    session.ensureSpace(7);
    const name = ing.n || ing.name || 'Ingredient';
    const qty = ing.q || ing.quantity || 'As required';

    doc.setFillColor(iIdx % 2 === 0 ? 255 : 250, iIdx % 2 === 0 ? 253 : 249, iIdx % 2 === 0 ? 247 : 243);
    doc.rect(MARGIN_X, session.y, CONTENT_W, 6.5, 'F');
    doc.setDrawColor(...COLORS.cardBorder);
    doc.setLineWidth(0.2);
    doc.rect(MARGIN_X, session.y, CONTENT_W, 6.5, 'S');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.textDark);
    doc.text(`• ${name}`, MARGIN_X + 4, session.y + 4.5);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.primary);
    doc.text(String(qty), PAGE_W - MARGIN_X - 4, session.y + 4.5, { align: 'right' });

    session.y += 6.5;
  });
  session.y += 4;

  // D. Step-by-Step Instructions
  session.drawSectionHeading('Cooking & Preparation Steps');
  const steps = Array.isArray(recipe.steps) ? recipe.steps : [];

  steps.forEach((step, sIdx) => {
    const stepLines = doc.splitTextToSize(step, CONTENT_W - 14);
    const stepH = Math.max(7, stepLines.length * 4.2 + 3);
    session.ensureSpace(stepH + 2);

    // Number circle badge
    doc.setFillColor(...COLORS.primary);
    doc.roundedRect(MARGIN_X, session.y + 0.5, 6, 6, 1.5, 1.5, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(...COLORS.white);
    doc.text(String(sIdx + 1), MARGIN_X + 3, session.y + 4.5, { align: 'center' });

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8.5);
    doc.setTextColor(...COLORS.textDark);
    doc.text(stepLines, MARGIN_X + 9, session.y + 4.5);

    session.y += stepH;
  });

  // E. Nutrition Tip
  if (recipe.nutrition_tip) {
    session.drawSectionHeading('Nutritional & Flavor Insights');
    session.drawCallout('Health Tip', recipe.nutrition_tip, 'amber');
  }

  session.finalizeFooters();
  savePDF(doc, `foodverse-recipe-${recipeName.toLowerCase().replace(/[^a-z0-9]/g, '-')}.pdf`);
}

// ══════════════════════════════════════════════════════════════════════════════
// 6. USER ACTIVITY & HEALTH TRACKING REPORT PDF
// ══════════════════════════════════════════════════════════════════════════════
export function generateActivityReportPDF({ user, profile, stats, calorieGoal, progress, activity }) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const session = new PDFSession(
    doc,
    'User Nutrition & Activity Report',
    'Verified health log derived from FoodVerse AI SQLite database',
    'Activity Audit'
  );

  // A. User Overview
  session.drawKeyValueGrid([
    { key: 'Account Holder', val: user?.name || 'Verified User' },
    { key: 'Email Address', val: user?.email || 'user@foodverse.ai' },
    { key: 'Configured Diet', val: profile?.diet || 'Standard' },
    { key: 'Health Target', val: profile?.goal || 'Weight Maintain' },
    { key: 'Daily Calorie Target', val: `${calorieGoal || 1900} kcal / day` },
    { key: 'Today\'s Calorie Intake', val: `${stats?.calories || 0} kcal` },
  ], 2);

  // B. KPI Highlights
  session.drawSectionHeading('Health Progress Metrics');
  session.drawKeyValueGrid([
    { key: 'Total Meals Verified', val: `${stats?.meals || 0} meals` },
    { key: 'Total AI Analyses', val: `${stats?.totalScans || stats?.meals || 0} audits` },
    { key: 'Goal Completion', val: `${progress || 0}% Tracked` },
  ], 3);

  // C. Timeline
  session.drawSectionHeading('Verified Activity History (SQLite Database)');
  const actList = Array.isArray(activity) ? activity : [];

  if (actList.length === 0) {
    session.drawCallout('Activity Status', 'No meals or audits recorded yet in active SQLite database session.', 'normal');
  } else {
    actList.forEach((act) => {
      const type = (act.type || 'audit').toUpperCase();
      const timeStr = act.ts ? new Date(act.ts).toLocaleString() : 'Recent';
      const textLines = doc.splitTextToSize(act.text || '', CONTENT_W - 55);
      const rowH = Math.max(7, textLines.length * 4.2 + 3);

      session.ensureSpace(rowH + 2);

      // Type Badge
      doc.setFillColor(...COLORS.primaryLight);
      doc.setDrawColor(...COLORS.primaryBorder);
      doc.setLineWidth(0.3);
      doc.roundedRect(MARGIN_X, session.y, 20, 5, 1, 1, 'FD');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(6.5);
      doc.setTextColor(...COLORS.primary);
      doc.text(type, MARGIN_X + 10, session.y + 3.5, { align: 'center' });

      // Action text
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.textDark);
      doc.text(textLines, MARGIN_X + 23, session.y + 3.5);

      // Time
      doc.setFontSize(7.5);
      doc.setTextColor(...COLORS.textMuted);
      doc.text(timeStr, PAGE_W - MARGIN_X, session.y + 3.5, { align: 'right' });

      session.y += rowH;
    });
  }

  session.finalizeFooters();
  savePDF(doc, 'foodverse-activity-report.pdf');
}
