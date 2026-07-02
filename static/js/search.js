/* ============================================================
   MYA SEARCH  —  static/js/search.js
   Búsqueda de productos via API REST con debounce.
   Endpoint: GET /api/products/?search=<query>&format=json
   ============================================================ */
(function () {
  'use strict';

  let debounceTimer = null;
  const DEBOUNCE_MS = 300;
  const MIN_CHARS   = 2;

  function $(id) { return document.getElementById(id); }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatPrice(num) {
    return Math.round(Number(num)).toLocaleString('es-PY');
  }

  /* ── Toggle del input ──────────────────────────────────── */
  function toggleSearch() {
    const box = $('searchBox');
    if (box.classList.contains('open')) {
      closeSearch();
    } else {
      box.classList.add('open');
      $('searchInput').focus();
    }
  }

  function closeSearch() {
    $('searchBox').classList.remove('open');
    $('searchResults').classList.remove('open');
    $('searchResults').innerHTML = '';
    $('searchInput').value = '';
    clearTimeout(debounceTimer);
  }

  /* ── Cerrar al hacer click fuera ───────────────────────── */
  document.addEventListener('click', function (e) {
    const wrap = $('searchWrap');
    if (wrap && !wrap.contains(e.target)) {
      closeSearch();
    }
  });

  /* ── Cerrar con Escape ─────────────────────────────────── */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeSearch();
  });

  /* ── Debounce + fetch ──────────────────────────────────── */
  function onSearchInput(query) {
    clearTimeout(debounceTimer);
    const res = $('searchResults');

    if (query.trim().length < MIN_CHARS) {
      res.classList.remove('open');
      res.innerHTML = '';
      return;
    }

    res.classList.add('open');
    res.innerHTML = '<div class="search-loading">Buscando…</div>';

    debounceTimer = setTimeout(() => fetchResults(query.trim()), DEBOUNCE_MS);
  }

  async function fetchResults(query) {
    const res = $('searchResults');
    try {
      const response = await fetch(
        '/api/products/?format=json&search=' + encodeURIComponent(query),
        {
          credentials: 'include',
          headers: { 'Accept': 'application/json' },
        }
      );

      if (!response.ok) throw new Error('HTTP ' + response.status);

      const data = await response.json();

      /* La API puede devolver { results: [...] } (paginado) o [...] (lista plana) */
      const items = Array.isArray(data) ? data : (data.results || []);

      renderResults(items, query);

    } catch (err) {
      res.innerHTML = '<div class="search-result-empty">Error al buscar. Intentá de nuevo.</div>';
      console.error('Search error:', err);
    }
  }

  /* ── Render ────────────────────────────────────────────── */
  function renderResults(items, query) {
    const res = $('searchResults');

    if (items.length === 0) {
      res.innerHTML = `<div class="search-result-empty">Sin resultados para "<strong>${escapeHtml(query)}</strong>"</div>`;
      return;
    }

    const visible = items.slice(0, 6);

    let html = visible.map(item => {
      const url   = `/api/products/${item.id}/`;
      const name  = escapeHtml(item.name || 'Producto');
      const price = item.price ? 'Gs. ' + formatPrice(item.price) : '';
      const img   = item.image
        ? `<img src="${escapeHtml(item.image)}" alt="${name}" class="search-result-img"
                onerror="this.style.display='none'">`
        : `<div class="search-result-img"
                style="background:var(--clr-surface,#f5f5f5);display:flex;
                       align-items:center;justify-content:center">
             <i class="bi bi-bag" style="color:var(--clr-muted,#aaa)"></i>
           </div>`;

      return `
        <a href="${url}" class="search-result-item">
          ${img}
          <div>
            <div class="search-result-name">${name}</div>
            <div class="search-result-price">${price}</div>
          </div>
        </a>`;
    }).join('');

    if (items.length > 6) {
      html += `
        <a href="/api/products/list/?search=${encodeURIComponent(query)}"
           class="search-result-item"
           style="justify-content:center;font-size:.78rem;color:var(--clr-muted)">
          Ver los ${items.length} resultados
        </a>`;
    }

    res.innerHTML = html;
  }

  /* ── Exports globales ──────────────────────────────────── */
  window.toggleSearch  = toggleSearch;
  window.closeSearch   = closeSearch;
  window.onSearchInput = onSearchInput;

})();