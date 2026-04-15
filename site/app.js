const state = {
  items: [],
  filter: "all",
  query: "",
};

async function boot() {
  const response = await fetch("./data.json");
  const payload = await response.json();
  state.items = payload.items || [];
  document.getElementById("itemCount").textContent = `${state.items.length} 条`;
  bindUI();
  render();
}

function bindUI() {
  const input = document.getElementById("searchInput");
  input.addEventListener("input", (event) => {
    state.query = event.target.value.trim().toLowerCase();
    render();
  });

  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".filter-chip").forEach((node) => node.classList.remove("is-active"));
      chip.classList.add("is-active");
      state.filter = chip.dataset.filter;
      render();
    });
  });
}

function render() {
  const cards = document.getElementById("cards");
  const filtered = state.items.filter((item) => {
    const matchesFilter = state.filter === "all" || item.content_type === state.filter;
    const haystack = [
      item.title,
      item.summary,
      item.hook,
      item.title_option,
      item.opening,
      item.body,
      item.closing,
      ...(item.tags || []),
    ].join(" ").toLowerCase();
    const matchesQuery = !state.query || haystack.includes(state.query);
    return matchesFilter && matchesQuery;
  });

  cards.innerHTML = filtered.length
    ? filtered.map(renderCard).join("")
    : `<article class="card"><div class="card-body"><h2 class="card-title">暂时没有匹配内容</h2><p class="card-copy">你可以换个关键词，或者先在本地多跑几次生成库存。</p></div></article>`;
}

function renderCard(item) {
  const coverSrc = item.cover_url || (item.gallery_urls && item.gallery_urls[0]) || "";
  const tags = (item.tags || []).slice(0, 5).map((tag) => `<span class="tag">#${escapeHtml(tag)}</span>`).join("");
  const coverDesign = item.cover_design && item.cover_design.template
    ? `<div><strong>封面风格：</strong>${escapeHtml(item.cover_design.template)} / ${escapeHtml(item.cover_design.palette || "")}</div>`
    : "";

  return `
    <article class="card">
      ${coverSrc ? `<img class="card-cover" src="${coverSrc}" alt="">` : `<div class="card-cover"></div>`}
      <div class="card-body">
        <span class="card-type">${escapeHtml(item.content_type || "内容库存")}</span>
        <h2 class="card-title">${escapeHtml(item.title_option || item.title || "未命名内容")}</h2>
        <p class="card-copy">${escapeHtml(item.opening || item.summary || "")}</p>
        <div class="tag-list">${tags}</div>
        <div class="meta-list">
          <div><strong>原始标题：</strong>${escapeHtml(item.title || "")}</div>
          <div><strong>生成时间：</strong>${escapeHtml(item.generated_at || "")}</div>
          ${item.price_text ? `<div><strong>价格：</strong>${escapeHtml(item.price_text)}</div>` : ""}
          ${coverDesign}
        </div>
        <div class="actions">
          ${item.detail_url ? `<a class="action-link" href="${item.detail_url}">看图片和正文</a>` : ""}
          ${item.source_url ? `<a class="action-link secondary" href="${item.source_url}" target="_blank" rel="noreferrer">看官网原链</a>` : ""}
        </div>
      </div>
    </article>
  `;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

boot().catch((error) => {
  document.getElementById("cards").innerHTML = `<article class="card"><div class="card-body"><h2 class="card-title">站点加载失败</h2><p class="card-copy">${escapeHtml(error.message)}</p></div></article>`;
});
