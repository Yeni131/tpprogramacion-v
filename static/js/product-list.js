/* ============================================================
   MYA PRODUCT LIST  —  static/js/product-list.js
   Maneja la vista de grilla/lista, filtros, ordenamiento
   y paginación del catálogo de productos.
   Extraído de templates/products/list.html
   ============================================================ */
(function () {
  'use strict';
  /* ── VIEW TOGGLE ─────────────────────────────────── */
  const gridEl  = document.getElementById('productsGrid');
  const btnGrid = document.getElementById('viewGrid');
  const btnList = document.getElementById('viewList');
  if (btnGrid && btnList && gridEl) {
    btnGrid.addEventListener('click', () => {
      gridEl.classList.remove('list-view');
      btnGrid.classList.add('active');
      btnList.classList.remove('active');
      localStorage.setItem('mya_view', 'grid');
    });
    btnList.addEventListener('click', () => {
      gridEl.classList.add('list-view');
      btnList.classList.add('active');
      btnGrid.classList.remove('active');
      localStorage.setItem('mya_view', 'list');
    });
    // Restaurar vista guardada
    if (localStorage.getItem('mya_view') === 'list') btnList.click();
  }
  /* ── SORT SELECT ─────────────────────────────────── */
  const sortSelect = document.getElementById('sortSelect');
  if (sortSelect) {
    sortSelect.addEventListener('change', function () {
      const url = new URL(window.location.href);
      url.searchParams.set('sort', this.value);
      url.searchParams.delete('page');
      window.location.href = url.toString();
    });
  }
  /* ── FILTERS ─────────────────────────────────────── */
  const filtersForm = document.getElementById('filtersForm');
  if (filtersForm) {
    filtersForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const url = new URL(window.location.href);
      url.searchParams.delete('category');
      url.searchParams.delete('price_min');
      url.searchParams.delete('price_max');
      url.searchParams.delete('in_stock');
      url.searchParams.delete('page');
      const data = new FormData(this);
      for (const [key, val] of data.entries()) {
        url.searchParams.append(key, val);
      }
      window.location.href = url.toString();
    });
  }
  const resetFilters = document.getElementById('resetFilters');
  if (resetFilters) {
    resetFilters.addEventListener('click', () => {
      const url = new URL(window.location.href);
      ['category', 'price_min', 'price_max', 'in_stock', 'page'].forEach(k =>
        url.searchParams.delete(k)
      );
      window.location.href = url.toString();
    });
  }
  /* ── FILTROS DESPLEGABLES (acordeón) ──────────────── */
  const filtersToggleEl = document.getElementById('filtersToggle');
  const filtersBodyEl   = document.getElementById('filtersBody');
  if (filtersToggleEl && filtersBodyEl) {
    filtersToggleEl.addEventListener('click', () => {
      const isOpen = filtersBodyEl.classList.toggle('open');
      filtersToggleEl.classList.toggle('open', isOpen);
    });
  }
  /* ── PAGINATION ──────────────────────────────────── */
  function goToPage(n) {
    const url = new URL(window.location.href);
    url.searchParams.set('page', n);
    window.location.href = url.toString();
  }
  // Exponer globalmente para los onclick del HTML (paginación)
  window.goToPage = goToPage;
})();