(function () {
  const list = document.getElementById("publications-list");
  const sortSelect = document.getElementById("publications-sort");
  const directionSelect = document.getElementById("publications-sort-direction");
  const categorySelect = document.getElementById("publications-category-select");
  const tagSelect = document.getElementById("publications-tag-select");
  const authorSelect = document.getElementById("publications-author-select");
  const clearFiltersButton = document.getElementById("publications-clear-filters");
  const resultsSummary = document.getElementById("publications-results-summary");
  const emptyState = document.getElementById("publications-empty-state");

  if (!list || !sortSelect) return;

  const entries = Array.from(list.querySelectorAll(".publication-entry"));

  const parseDate = (value) => {
    if (!value) return 0;
    const t = Date.parse(value);
    return Number.isNaN(t) ? 0 : t;
  };

  const parseNum = (value) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  };

  const getSet = (entry, key) =>
    (entry.dataset[key] || "")
      .split(",")
      .map((part) => part.trim().toLowerCase())
      .filter(Boolean);

  const compareEntries = (a, b, mode, direction) => {
    let delta = 0;
    if (mode === "last_modified") {
      delta = parseDate(b.dataset.lastmod) - parseDate(a.dataset.lastmod);
    } else if (mode === "word_count") {
      delta = parseNum(b.dataset.wordcount) - parseNum(a.dataset.wordcount);
    } else {
      delta = parseDate(b.dataset.published) - parseDate(a.dataset.published);
      if (delta === 0) {
        delta = (a.dataset.title || "").localeCompare(b.dataset.title || "");
      }
    }
    return direction === "asc" ? delta * -1 : delta;
  };

  const updateResultsSummary = (visibleCount) => {
    if (!resultsSummary) return;

    const total = entries.length;
    const bits = [];
    const category = (categorySelect?.value || "").trim();
    const tag = (tagSelect?.value || "").trim();
    const author = (authorSelect?.value || "").trim();

    if (category) bits.push(`category: ${category}`);
    if (tag) bits.push(`tag: ${tag}`);
    if (author) bits.push(`author: ${author}`);

    if (!bits.length) {
      resultsSummary.textContent = `Showing all ${total} publications`;
      return;
    }

    resultsSummary.textContent = `Showing ${visibleCount} of ${total} publications for ${bits.join(" • ")}`;
  };

  const filterEntries = () => {
    const category = (categorySelect?.value || "").trim().toLowerCase();
    const tag = (tagSelect?.value || "").trim().toLowerCase();
    const author = (authorSelect?.value || "").trim().toLowerCase();

    let visibleCount = 0;
    entries.forEach((entry) => {
      const categoryMatch = !category || getSet(entry, "categories").includes(category);
      const tagMatch = !tag || getSet(entry, "tags").includes(tag);
      const authorMatch = !author || getSet(entry, "authors").includes(author);
      const visible = categoryMatch && tagMatch && authorMatch;
      entry.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    if (emptyState) emptyState.hidden = visibleCount !== 0;
    updateResultsSummary(visibleCount);
  };

  const sortEntries = () => {
    const mode = sortSelect.value;
    const direction = directionSelect?.value || "desc";
    entries.sort((a, b) => compareEntries(a, b, mode, direction));
    entries.forEach((entry) => list.appendChild(entry));
  };

  sortSelect.addEventListener("change", sortEntries);
  directionSelect?.addEventListener("change", sortEntries);
  categorySelect?.addEventListener("change", filterEntries);
  tagSelect?.addEventListener("change", filterEntries);
  authorSelect?.addEventListener("change", filterEntries);
  clearFiltersButton?.addEventListener("click", () => {
    if (categorySelect) categorySelect.value = "";
    if (tagSelect) tagSelect.value = "";
    if (authorSelect) authorSelect.value = "";
    filterEntries();
  });

  sortEntries();
  filterEntries();
})();
