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
  const quadrantCoordinates = {
    A: [0.78, 0.78],
    B: [0.22, 0.22],
    C: [0.78, 0.22],
    D: [0.22, 0.78],
    N: [0.5, 0.5],
  };

  const deterministicJitter = (label, axis) => {
    const text = `${label || ""}:${axis}`;
    let hash = 0;
    for (const character of text) hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
    return ((Math.abs(hash) % 1000) / 1000 - 0.5) * 0.25;
  };

  const numberOr = (value, fallback) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.max(0.04, Math.min(0.96, parsed)) : fallback;
  };

  const render = () => {
    const points = Array.isArray(payload[level]) ? payload[level] : [];
    const filtered = points.filter((point) => {
      if (level !== "case") return true;
      return chartFilters.every((filter) => !filter.value || String(point[filter.dataset.chartFilter]) === filter.value);
    });
    pointsNode.replaceChildren();
    if (!filtered.length) {
      pointsNode.innerHTML = '<div class="chart-empty">当前筛选没有数据</div>';
      return;
    }
    filtered.forEach((point) => {
      const base = quadrantCoordinates[point.quadrant_code] || quadrantCoordinates.N;
      const x = level === "case" ? base[0] + deterministicJitter(point.label, "x") : numberOr(point.x, 0.5);
      const y = level === "case" ? base[1] + deterministicJitter(point.label, "y") : numberOr(point.y, 0.5);
      const anchor = document.createElement("a");
      anchor.className = `chart-point q-${String(point.quadrant_code || "n").toLowerCase()}`;
      anchor.href = point.href || "#";
      anchor.style.left = `${numberOr(x, 0.5) * 100}%`;
      anchor.style.bottom = `${numberOr(y, 0.5) * 100}%`;
      const tooltip = document.createElement("span");
      tooltip.className = "point-tooltip";
      tooltip.textContent = [
        point.label,
        `question_type: ${point.question_type ?? "NOT_RECORDED"}`,
        `recall_at_k: ${point.recall_at_k ?? "NOT_RECORDED"}`,
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
