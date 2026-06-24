/* ============================================================
   MYA MY ORDERS  —  static/js/my-orders.js
   Trae y renderiza el historial de pedidos del usuario.
   ============================================================ */
(function () {
  'use strict';

  const listEl     = document.getElementById('ordersList');
  const subtitleEl = document.getElementById('ordersSubtitle');

  const STATUS_CLASS = {
    pending:   'status-pending',
    paid:      'status-paid',
    shipped:   'status-shipped',
    delivered: 'status-delivered',
    cancelled: 'status-cancelled',
  };

  function formatPrice(n) {
    return '$' + Number(n).toLocaleString('es-AR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  function formatDate(isoString) {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-AR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function buildItemRow(item) {
    const imgHtml = item.product_image
      ? `<img src="${item.product_image}" alt="${escapeHtml(item.product_name)}" class="order-item-img"
              onerror="this.outerHTML='<div class=&quot;order-item-img-placeholder&quot;><i class=&quot;bi bi-image&quot;></i></div>'" />`
      : `<div class="order-item-img-placeholder"><i class="bi bi-image"></i></div>`;

    return `
      <div class="order-item-row">
        ${imgHtml}
        <div class="order-item-info">
          <div class="order-item-name">${escapeHtml(item.product_name)}</div>
          ${item.variant_name ? `<div class="order-item-variant">${escapeHtml(item.variant_name)}</div>` : ''}
        </div>
        <div class="order-item-qty">${item.quantity} × ${formatPrice(item.price)}</div>
        <div class="order-item-subtotal">${formatPrice(item.subtotal)}</div>
      </div>`;
  }

  function buildOrderCard(order) {
    const statusClass = STATUS_CLASS[order.status] || 'status-pending';
    const itemsHtml = order.items.map(buildItemRow).join('');

    return `
      <article class="order-card">
        <div class="order-card-header">
          <div>
            <span class="order-id">Orden #${order.id}</span>
            <span class="order-date"> · ${formatDate(order.created)}</span>
          </div>
          <span class="order-status ${statusClass}">${escapeHtml(order.status_label)}</span>
        </div>
        <div class="order-items">${itemsHtml}</div>
        <div class="order-card-footer">
          <span class="order-total-label">${order.items_count} producto(s) · Total</span>
          <span class="order-total-amount">${formatPrice(order.total_price)}</span>
        </div>
      </article>`;
  }

  function renderEmpty() {
    listEl.innerHTML = `
      <div class="orders-empty">
        <i class="bi bi-bag"></i>
        <p>Todavía no realizaste ninguna compra.</p>
      </div>`;
  }

  function renderError() {
    listEl.innerHTML = `
      <div class="orders-empty">
        <i class="bi bi-exclamation-triangle"></i>
        <p>No pudimos cargar tu historial. Intentá de nuevo más tarde.</p>
      </div>`;
  }

  async function loadOrders() {
    try {
      const res = await fetch('/api/orders/', {
        credentials: 'include',
        headers: { 'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '' },
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const orders = await res.json();

      if (!orders.length) {
        subtitleEl.textContent = 'Todavía no realizaste ninguna compra.';
        renderEmpty();
        return;
      }

      subtitleEl.textContent = `${orders.length} pedido(s) realizado(s).`;
      listEl.innerHTML = orders.map(buildOrderCard).join('');

    } catch (e) {
      console.error('loadOrders:', e);
      subtitleEl.textContent = 'Ocurrió un error al cargar tus pedidos.';
      renderError();
    }
  }

  document.addEventListener('DOMContentLoaded', loadOrders);
})();