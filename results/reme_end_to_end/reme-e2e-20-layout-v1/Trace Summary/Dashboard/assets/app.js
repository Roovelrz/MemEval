(() => {
  "use strict";

  const menuButton = document.querySelector("[data-menu-toggle]");
  if (menuButton) {
    menuButton.addEventListener("click", () => document.body.classList.toggle("menu-open"));
  }

  document.querySelectorAll("[data-filter-table]").forEach((table) => {
    const scope = table.closest(".panel") || document;
    const rows = Array.from(table.querySelectorAll("tbody tr"));
    const selects = Array.from(scope.querySelectorAll("[data-filter-key]"));
    const search = scope.querySelector("[data-table-search]");
    const count = scope.querySelector("[data-visible-count]");
    const apply = () => {
      const query = (search?.value || "").trim().toLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const matchesSelects = selects.every((select) => {
          if (!select.value) return true;
          const attribute = `data-${select.dataset.filterKey.replaceAll("_", "-")}`;
          return row.getAttribute(attribute) === select.value;
        });
        const matchesSearch = !query || row.textContent.toLowerCase().includes(query);
        const show = matchesSelects && matchesSearch;
        row.hidden = !show;
        if (show) visible += 1;
      });
      if (count) count.textContent = String(visible);
    };
    selects.forEach((select) => select.addEventListener("change", apply));
    search?.addEventListener("input", apply);
  });

  document.querySelectorAll("[data-benchmark-switch]").forEach((select) => {
    select.addEventListener("change", () => {
      if (select.value) window.location.href = select.value;
    });
  });

  document.querySelectorAll("[data-back-button]").forEach((button) => {
    button.addEventListener("click", () => {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        window.location.href = button.dataset.backFallback || "../index.html";
      }
    });
  });

  const dataNode = document.querySelector("[data-chart-data]");
  const pointsNode = document.querySelector("[data-chart-points]");
  if (!dataNode || !pointsNode) return;

  let payload;
  try {
    payload = JSON.parse(dataNode.textContent);
  } catch (error) {
    pointsNode.innerHTML = '<div class="chart-empty">图表数据解析失败</div>';
    return;
  }

  let level = "case";
  const levelButtons = Array.from(document.querySelectorAll("[data-chart-level]"));
  const chartFilters = Array.from(document.querySelectorAll("[data-chart-filter]"));
  const quadrantRanges = {
    A: { x: [0.62, 0.93], y: [0.58, 0.90] },
    B: { x: [0.62, 0.93], y: [0.10, 0.42] },
    C: { x: [0.10, 0.42], y: [0.58, 0.90] },
    D: { x: [0.10, 0.42], y: [0.10, 0.42] },
  };

  const deterministicJitter = (label, axis) => {
    const text = `${label || ""}:${axis}`;
    let hash = 0;
    for (const character of text) hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
    return ((Math.abs(hash) % 1000) / 1000 - 0.5);
  };

  const scoreOrNull = (value) => {
    if (value === null || value === undefined || value === "" || value === "NOT_RECORDED") return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const normalizeScore = (value, values) => {
    const parsed = scoreOrNull(value);
    if (parsed === null || !values.length) return null;
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    return maximum - minimum < Number.EPSILON ? 0.5 : (parsed - minimum) / (maximum - minimum);
  };

  const spreadCasePoints = (points) => {
    const coordinates = new Map();
    Object.keys(quadrantRanges).forEach((code) => {
      const group = points
        .filter((point) => point.quadrant_code === code)
        .sort((left, right) => String(left.label).localeCompare(String(right.label)));
      if (!group.length) return;
      const range = quadrantRanges[code];
      const evidenceScores = group.map((point) => scoreOrNull(point.best_evidence_score)).filter((value) => value !== null);
      const nonEvidenceScores = group.map((point) => scoreOrNull(point.best_non_evidence_score)).filter((value) => value !== null);
      group.forEach((point) => {
        const normalizedEvidence = normalizeScore(point.best_evidence_score, evidenceScores);
        const normalizedNonEvidence = normalizeScore(point.best_non_evidence_score, nonEvidenceScores);
        // Each quadrant has a logical, hidden score plane. Small deterministic jitter
        // separates tied scores without obscuring the score-based ordering.
        const fallbackX = 0.35 + deterministicJitter(point.label, "missing-x") * 0.20;
        const fallbackY = 0.35 + deterministicJitter(point.label, "missing-y") * 0.20;
        const localX = (normalizedEvidence ?? fallbackX) + deterministicJitter(point.label, "x") * 0.04;
        const localY = (normalizedNonEvidence ?? fallbackY) + deterministicJitter(point.label, "y") * 0.04;
        const x = range.x[0] + Math.max(0.02, Math.min(0.98, localX)) * (range.x[1] - range.x[0]);
        const y = range.y[0] + Math.max(0.02, Math.min(0.98, localY)) * (range.y[1] - range.y[0]);
        coordinates.set(point, [x, y]);
      });
    });
    return coordinates;
  };

  const numberOr = (value, fallback) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.max(0.04, Math.min(0.96, parsed)) : fallback;
  };

  const percent = (value) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(1)}%` : "NOT_RECORDED";
  };

  const updateQuadrantCounts = (points) => {
    const counts = { A: 0, B: 0, C: 0, D: 0 };
    points.forEach((point) => {
      if (Object.hasOwn(counts, point.quadrant_code)) counts[point.quadrant_code] += 1;
    });
    document.querySelectorAll("[data-quadrant-count]").forEach((node) => {
      node.textContent = String(counts[node.dataset.quadrantCount] || 0);
    });
  };

  const render = () => {
    const points = Array.isArray(payload[level]) ? payload[level] : [];
    const filtered = points.filter((point) => {
      if (level !== "case") return true;
      return chartFilters.every((filter) => !filter.value || String(point[filter.dataset.chartFilter]) === filter.value);
    });
    const casePoints = Array.isArray(payload.case) ? payload.case : [];
    const visibleCases = level === "case" ? filtered : casePoints;
    updateQuadrantCounts(visibleCases);
    pointsNode.replaceChildren();
    if (!filtered.length) {
      pointsNode.innerHTML = '<div class="chart-empty">当前筛选没有数据</div>';
      return;
    }
    const caseCoordinates = level === "case" ? spreadCasePoints(filtered) : new Map();
    filtered.forEach((point) => {
      const coordinates = caseCoordinates.get(point) || [numberOr(point.x, 0.5), numberOr(point.y, 0.5)];
      const [x, y] = coordinates;
      const anchor = document.createElement("a");
      anchor.className = `chart-point q-${String(point.quadrant_code || "n").toLowerCase()}`;
      anchor.href = point.href || "#";
      anchor.setAttribute("aria-label", `查看 ${point.label}`);
      anchor.style.left = `${numberOr(x, 0.5) * 100}%`;
      anchor.style.bottom = `${numberOr(y, 0.5) * 100}%`;
      const tooltip = document.createElement("span");
      tooltip.className = "point-tooltip";
      tooltip.textContent = [
        point.label,
        `question_type: ${point.question_type ?? "NOT_RECORDED"}`,
        `Hit@${payload.top_k || 10}: ${percent(point.hit_at_k)}`,
        `Recall@${payload.top_k || 10}: ${percent(point.recall_at_k)}`,
        `best_evidence_score (x): ${point.best_evidence_score ?? "NOT_RECORDED"}`,
        `best_non_evidence_score (y): ${point.best_non_evidence_score ?? "NOT_RECORDED"}`,
        `answer_correct: ${point.answer_correct ?? "NOT_RECORDED"}`,
        `root_cause: ${point.root_cause ?? "NOT_RECORDED"}`,
      ].join("\n");
      anchor.appendChild(tooltip);
      pointsNode.appendChild(anchor);
    });
  };

  levelButtons.forEach((button) => {
    button.addEventListener("click", () => {
      level = button.dataset.chartLevel;
      levelButtons.forEach((item) => item.classList.toggle("active", item === button));
      chartFilters.forEach((filter) => { filter.disabled = level !== "case"; });
      render();
    });
  });
  chartFilters.forEach((filter) => filter.addEventListener("change", render));
  render();
})();
