// Click a column header to sort the table.
document.querySelectorAll("table.sortable").forEach((table) => {
  table.querySelectorAll("th").forEach((th, col) => {
    if (!th.dataset.type) return;
    th.addEventListener("click", () => {
      const asc = !th.classList.contains("asc");
      table.querySelectorAll("th").forEach((h) => h.classList.remove("asc", "desc"));
      th.classList.add(asc ? "asc" : "desc");
      const body = table.tBodies[0];
      const rows = Array.from(body.rows);
      const val = (r) => {
        const cell = r.cells[col];
        if (!cell) return "";
        const v = cell.dataset.v ?? cell.textContent.trim();
        return th.dataset.type === "num" ? parseFloat(v) || 0 : v;
      };
      rows.sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * (asc ? 1 : -1));
      rows.forEach((r) => body.appendChild(r));
    });
  });
});

// Search form: show only the date fields that apply.
const form = document.getElementById("searchForm");
if (form) {
  const mode = form.elements.date_mode;
  const trip = form.elements.trip;
  const hint = document.getElementById("creditHint");
  const update = () => {
    form.querySelectorAll("[data-show]").forEach((el) => {
      el.style.display = el.dataset.show.split(" ").includes(mode.value) ? "" : "none";
    });
    form.querySelectorAll("[data-trip]").forEach((el) => {
      el.style.display = trip.value === el.dataset.trip ? "" : "none";
    });
    let n = 1;
    if (mode.value === "flex") n = 2 * parseInt(form.elements.flex_days.value || "0") + 1;
    if (mode.value === "weekends") n = "4–5";
    hint.textContent = n === 1 ? "Uses 1 search credit (free if you searched this recently)."
      : `Checks ${n} date options = up to ${n} search credits (dates searched recently are free).`;
  };
  [mode, trip, form.elements.flex_days].forEach((el) => el.addEventListener("change", update));
  update();
}
