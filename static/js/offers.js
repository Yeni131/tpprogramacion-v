/* ============================================================
   MYA OFFERS  —  static/js/offers.js
   Carga y renderiza los cupones activos en /ofertas/.
   ============================================================ */
(function () {
  'use strict';

  const gridEl = document.getElementById('offersGrid');

  function formatDate(isoString) {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-AR', { day: '2-digit', month: 'long', year: 'numeric' });
  }

  function buildCouponCard(coupon) {
    return `
      <div class="coupon-card">
        <div class="coupon-card-discount">
          <span class="coupon-discount-value">${parseFloat(coupon.discount)}%</span>
          <span class="coupon-discount-label">Descuento</span>
        </div>
        <div class="coupon-card-body">
          <div class="coupon-code-row">
            <span class="coupon-code">${coupon.code}</span>
            <button class="btn-copy-coupon" data-code="${coupon.code}" aria-label="Copiar código">
              <i class="bi bi-clipboard"></i>
            </button>
          </div>
          <div class="coupon-expiry">
            <i class="bi bi-clock-history"></i>
            Válido hasta el ${formatDate(coupon.valid_to)}
          </div>
        </div>
      </div>`;
  }

  function renderEmpty() {
    gridEl.innerHTML = `
      <div class="offers-empty">
        <i class="bi bi-tag"></i>
        <p>No hay cupones activos en este momento. ¡Volvé a revisar pronto!</p>
      </div>`;
  }

  function setupCopyButtons() {
    gridEl.querySelectorAll('.btn-copy-coupon').forEach(btn => {
      btn.addEventListener('click', async () => {
        const code = btn.dataset.code;
        try {
          await navigator.clipboard.writeText(code);
          btn.classList.add('copied');
          btn.innerHTML = '<i class="bi bi-check2"></i>';
          setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = '<i class="bi bi-clipboard"></i>';
          }, 1800);
        } catch (e) {
          console.warn('No se pudo copiar el cupón:', e);
        }
      });
    });
  }

  async function loadOffers() {
    try {
      const res = await fetch('/api/coupons/active/', { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const coupons = await res.json();

      if (!coupons.length) {
        renderEmpty();
        return;
      }

      gridEl.innerHTML = coupons.map(buildCouponCard).join('');
      setupCopyButtons();

    } catch (e) {
      console.error('loadOffers:', e);
      gridEl.innerHTML = `<div class="offers-empty"><p>No pudimos cargar las ofertas. Intentá de nuevo más tarde.</p></div>`;
    }
  }

  document.addEventListener('DOMContentLoaded', loadOffers);
})();