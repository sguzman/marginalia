(function () {
  const grid = document.getElementById("publications-grid");
  const sortSelect = document.getElementById("publications-sort");
  const categorySelect = document.getElementById("publications-category-select");
  const tagSelect = document.getElementById("publications-tag-select");
  const authorSelect = document.getElementById("publications-author-select");
  const clearFiltersButton = document.getElementById("publications-clear-filters");
  const resultsSummary = document.getElementById("publications-results-summary");

  if (!grid || !sortSelect) return;

  const cards = Array.from(grid.querySelectorAll(".publication-card"));
  const chipButtons = Array.from(grid.querySelectorAll(".publication-chip"));

  const parseDate = (value) => {
    if (!value) return 0;
    const t = Date.parse(value);
    return Number.isNaN(t) ? 0 : t;
  };

  const parseNum = (value) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  };

  const getSet = (card, key) =>
    (card.dataset[key] || "")
      .split(",")
      .map((part) => part.trim().toLowerCase())
      .filter(Boolean);

  const compareCards = (a, b, mode) => {
    if (mode === "last_modified") {
      return parseDate(b.dataset.lastmod) - parseDate(a.dataset.lastmod);
    }
    if (mode === "word_count") {
      return parseNum(b.dataset.wordcount) - parseNum(a.dataset.wordcount);
    }
    const publishedDelta = parseDate(b.dataset.published) - parseDate(a.dataset.published);
    if (publishedDelta !== 0) return publishedDelta;
    return (a.dataset.title || "").localeCompare(b.dataset.title || "");
  };

  const updateChipStates = () => {
    const selectedCategory = (categorySelect?.value || "").trim().toLowerCase();
    const selectedTag = (tagSelect?.value || "").trim().toLowerCase();
    const selectedAuthor = (authorSelect?.value || "").trim().toLowerCase();

    chipButtons.forEach((button) => {
      const type = button.dataset.filterType || "";
      const value = (button.dataset.filterValue || "").toLowerCase();
      const active =
        (type === "category" && selectedCategory === value) ||
        (type === "tag" && selectedTag === value) ||
        (type === "author" && selectedAuthor === value);
      button.classList.toggle("is-active", active);
    });
  };

  const updateResultsSummary = (visibleCount) => {
    if (!resultsSummary) return;

    const total = cards.length;
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

  const filterCards = () => {
    const category = (categorySelect?.value || "").trim().toLowerCase();
    const tag = (tagSelect?.value || "").trim().toLowerCase();
    const author = (authorSelect?.value || "").trim().toLowerCase();

    let visibleCount = 0;
    cards.forEach((card) => {
      const categoryMatch = !category || getSet(card, "categories").includes(category);
      const tagMatch = !tag || getSet(card, "tags").includes(tag);
      const authorMatch = !author || getSet(card, "authors").includes(author);
      const visible = categoryMatch && tagMatch && authorMatch;
      card.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    updateChipStates();
    updateResultsSummary(visibleCount);
  };

  const sortCards = () => {
    const mode = sortSelect.value;
    cards.sort((a, b) => compareCards(a, b, mode));
    cards.forEach((card) => grid.appendChild(card));
  };

  const applyFilter = (type, value) => {
    if (!value) return;
    if (type === "category" && categorySelect) {
      categorySelect.value = categorySelect.value === value ? "" : value;
    }
    if (type === "tag" && tagSelect) {
      tagSelect.value = tagSelect.value === value ? "" : value;
    }
    if (type === "author" && authorSelect) {
      authorSelect.value = authorSelect.value === value ? "" : value;
    }
    filterCards();
  };

  sortSelect.addEventListener("change", sortCards);
  categorySelect?.addEventListener("change", filterCards);
  tagSelect?.addEventListener("change", filterCards);
  authorSelect?.addEventListener("change", filterCards);
  clearFiltersButton?.addEventListener("click", () => {
    if (categorySelect) categorySelect.value = "";
    if (tagSelect) tagSelect.value = "";
    if (authorSelect) authorSelect.value = "";
    filterCards();
  });

  chipButtons.forEach((button) => {
    button.addEventListener("click", () => {
      applyFilter(button.dataset.filterType || "", (button.dataset.filterValue || "").toLowerCase());
    });
  });

  sortCards();
  filterCards();
})();
