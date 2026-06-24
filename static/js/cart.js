/* ============================================================
   MYA CART ENGINE  —  static/js/cart.js
   Extraído de base.html
   ============================================================ */
const Cart = (() => {
  'use strict';

  const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';

  // ── State ──────────────────────────────────────────────────
  let state      = { items: [], total: 0, item_count: 0 };
  let timerID    = null;
  let drawerOpen = false;

  // ── DOM refs ───────────────────────────────────────────────
  const drawer   = document.getElementById('cartDrawer');
  const overlay  = document.getElementById('cartOverlay');
  const listEl   = document.getElementById('cartItemsList');
  const emptyEl  = document.getElementById('cartEmpty');
  const footerEl = document.getElementById('cartFooter');
  const totalEl  = document.getElementById('cartTotal');
  const badgeEl  = document.getElementById('cartBadge');
  const timerBar = document.getElementById('cartTimerBar');

  function applyResponse(data) {
    state = {
      items:      data.items      ?? [],
      total:      parseFloat(data.total      ?? 0),
      item_count: parseInt(data.item_count   ?? 0, 10),
    };
  }

  async function fetchCart() {
    try {
      const res = await fetch('/api/cart/', {
        headers: { 'X-CSRFToken': CSRF() },
      });
      if (!res.ok) throw new Error(`fetchCart HTTP ${res.status}`);
      applyResponse(await res.json());
      render();
    } catch (e) {
      console.error('fetchCart:', e);
    }
  }

  async function addItem(productId, variantId, qty = 1) {
    try {
      const body = { product_id: productId, quantity: qty };
      if (variantId) body.variant_id = variantId;

      const res = await fetch('/api/cart/add/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF() },
        body:    JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());

      applyResponse(await res.json());
      render();
      openDrawer();
      showToast('Producto agregado al carrito');
    } catch (e) {
      console.error('addItem:', e);
      showToast('Error al agregar producto', true);
    }
  }

  async function updateItem(itemId, qty) {
    try {
      const res = await fetch(`/api/cart/update/${itemId}/`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF() },
        body:    JSON.stringify({ quantity: qty }),
      });
      if (!res.ok) throw new Error(await res.text());
      applyResponse(await res.json());
      render();
    } catch (e) {
      console.error('updateItem:', e);
      showToast('Error al actualizar', true);
    }
  }

  function render() {
    const { items, total, item_count } = state;

    if (badgeEl) {
      badgeEl.textContent   = item_count;
      badgeEl.dataset.count = item_count;
    }

    if (!items.length) {
      if (emptyEl)  emptyEl.style.display  = 'flex';
      if (footerEl) footerEl.style.display = 'none';
      listEl.querySelectorAll('.cart-item').forEach(n => n.remove());
      return;
    }

    if (emptyEl)  emptyEl.style.display  = 'none';
    if (footerEl) footerEl.style.display = 'block';
    if (totalEl)  totalEl.textContent    = formatPrice(total);

    listEl.querySelectorAll('.cart-item').forEach(n => n.remove());
    items.forEach(item => listEl.appendChild(buildItemEl(item)));
  }

  function buildItemEl(item) {
    const el = document.createElement('div');
    el.className  = 'cart-item';
    el.dataset.id = item.id;

    const product     = item.product ?? {};
    const variant     = item.variant ?? null;
    const name        = product.name  ?? 'Producto';
    const variantName = variant?.name ?? '';
    const subtotal    = parseFloat(item.subtotal ?? 0);
    const qty         = item.quantity ?? 1;
    const imgSrc      = product.image ?? '';

    el.innerHTML = `
      <img
        src="${imgSrc}"
        alt="${escapeHtml(name)}"
        class="cart-item-img"
        onerror="this.onerror=null;this.style.display='none';this.nextElementSibling.style.display='flex';"
      />
      <div class="cart-item-img-placeholder" style="display:none;">
        <i class="bi bi-image"></i>
      </div>
      <div class="cart-item-info">
        <div class="cart-item-name">${escapeHtml(name)}</div>
        ${variantName ? `<div class="cart-item-variant">${escapeHtml(variantName)}</div>` : ''}
        <div class="cart-item-price">${formatPrice(subtotal)}</div>
        <div class="cart-item-qty">
          <button class="qty-btn" data-action="dec" aria-label="Disminuir">−</button>
          <span class="qty-value">${qty}</span>
          <button class="qty-btn" data-action="inc" aria-label="Aumentar">+</button>
        </div>
      </div>`;

    el.querySelectorAll('.qty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const currentQty = parseInt(el.querySelector('.qty-value').textContent, 10);
        const next = btn.dataset.action === 'inc'
          ? currentQty + 1
          : Math.max(0, currentQty - 1);
        updateItem(item.id, next);
      });
    });

    return el;
  }

  function openDrawer() {
    drawerOpen = true;
    drawer.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    startTimer();
  }

  function closeDrawer() {
    drawerOpen = false;
    drawer.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    clearTimeout(timerID);
    resetTimerBar();
  }

  function startTimer() {
    clearTimeout(timerID);
    resetTimerBar();
    requestAnimationFrame(() => {
      timerBar.style.transition = 'transform 5s linear';
      timerBar.style.transform  = 'scaleX(0)';
    });
    timerID = setTimeout(closeDrawer, 5000);
  }

  function resetTimerBar() {
    timerBar.style.transition = 'none';
    timerBar.style.transform  = 'scaleX(1)';
  }

  function showToast(msg, isError = false) {
    const t = document.getElementById('myaToast');
    if (!t) return;
    t.textContent      = msg;
    t.style.background = isError ? '#c0392b' : 'var(--clr-text)';
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2800);
  }

  function formatPrice(n) {
    return '$' + Number(n).toLocaleString('es-AR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function init() {
    const toggleBtn = document.getElementById('cartToggleBtn');
    const closeBtn  = document.getElementById('cartCloseBtn');
    if (toggleBtn) toggleBtn.addEventListener('click', () => drawerOpen ? closeDrawer() : openDrawer());
    if (closeBtn)  closeBtn.addEventListener('click', closeDrawer);
    if (overlay)   overlay.addEventListener('click', closeDrawer);
    if (drawer) {
      drawer.addEventListener('mouseenter', () => {
        clearTimeout(timerID);
        if (timerBar) { timerBar.style.transition = 'none'; }
      });
      drawer.addEventListener('mouseleave', () => {
        if (drawerOpen) startTimer();
      });
    }
    fetchCart();
  }

  return { init, addItem, fetchCart, updateItem, showToast, formatPrice, getState: () => ({ ...state }) };
})();

document.addEventListener('DOMContentLoaded', Cart.init);