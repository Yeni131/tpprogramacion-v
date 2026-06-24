/* ============================================================
   MYA PRODUCT DETAIL  —  static/js/product-detail.js
   Maneja la lógica del detalle de producto: selector de talle,
   variantes, cantidad, agregar al carrito y galería.
   Extraído de templates/products/detail.html

   DEPENDENCIAS:
   - window.PRODUCT_ID    (int)   → inyectado en detail.html
   - window.IS_CLOTHING   (bool)  → inyectado en detail.html
   - window.HAS_VARIANTS  (bool)  → inyectado en detail.html
   - Cart  (de cart.js)
   ============================================================ */
(function () {
  'use strict';

  let selectedSize    = null;
  let selectedVariant = null;

  /* ── SIZE SELECTOR ────────────────────────────────────────── */
  function selectSize(btn) {
    if (btn.classList.contains('unavailable')) return;
    document.querySelectorAll('.size-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    selectedSize = btn.dataset.size;
    document.getElementById('selectedSizeName').textContent = '— ' + selectedSize;
    clearErrors();
  }

  /* ── VARIANT SELECTOR ─────────────────────────────────────── */
  function selectVariant(chip) {
    document.querySelectorAll('.variant-chip').forEach(c => c.classList.remove('selected'));
    chip.classList.add('selected');
    selectedVariant = chip.dataset.variantId;
    document.getElementById('selectedVariantName').textContent = '— ' + chip.dataset.variantName;
    clearErrors();
  }

  /* ── QUANTITY ─────────────────────────────────────────────── */
  function changeQty(delta) {
    const input = document.getElementById('qtyInput');
    const max   = parseInt(input.max) || 99;
    const next  = Math.max(1, Math.min(max, parseInt(input.value) + delta));
    input.value = next;
  }

  /* ── VALIDATION ───────────────────────────────────────────── */
  function validate() {
    if (window.IS_CLOTHING) {
      if (!selectedSize) {
        showSizeError();
        return false;
      }
    } else if (window.HAS_VARIANTS) {
      if (!selectedVariant) {
        showVariantError();
        return false;
      }
    }
    return true;
  }

  function showSizeError() {
    const grid = document.getElementById('sizeGrid');
    const err  = document.getElementById('sizeError');
    grid.classList.add('error-highlight');
    err.classList.add('show');
    grid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => grid.classList.remove('error-highlight'), 800);
  }

  function showVariantError() {
    const chips = document.getElementById('variantChips');
    const err   = document.getElementById('variantError');
    if (!chips || !err) return;
    chips.classList.add('error-highlight');
    err.classList.add('show');
    chips.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => chips.classList.remove('error-highlight'), 800);
  }

  function clearErrors() {
    document.querySelectorAll('.variant-error').forEach(e => e.classList.remove('show'));
    document.querySelectorAll('.size-grid, .variant-chips').forEach(e => e.classList.remove('error-highlight'));
  }

  /* ── ADD TO CART ──────────────────────────────────────────── */
  async function handleAddToCart() {
    if (!validate()) return;

    const btn = document.getElementById('addToCartBtn');
    const qty = parseInt(document.getElementById('qtyInput').value);
    btn.classList.add('loading');
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Agregando...';

    const variantId = window.IS_CLOTHING ? null : (selectedVariant ?? null);
    const body = { product_id: window.PRODUCT_ID, quantity: qty };
    if (window.IS_CLOTHING && selectedSize) body.size = selectedSize;
    if (variantId) body.variant_id = variantId;

    try {
      const res = await fetch('/api/cart/add/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? ''
        },
        body: JSON.stringify(body)
      });
      if (!res.ok) throw new Error('Error al agregar');
      await Cart.fetchCart();
      // Abrir drawer manualmente
      document.getElementById('cartToggleBtn').click();
      Cart.showToast('¡Producto agregado!');
    } catch (e) {
      Cart.showToast('Error al agregar al carrito', true);
    } finally {
      btn.classList.remove('loading');
      btn.innerHTML = '<i class="bi bi-bag-plus"></i> Agregar al carrito';
    }
  }

  /* ── GALLERY ──────────────────────────────────────────────── */
  function switchImage(url, thumbEl) {
    const main = document.getElementById('mainImage');
    if (main) {
      main.style.opacity = '0';
      main.style.transition = 'opacity .2s';
      setTimeout(() => { main.src = url; main.style.opacity = '1'; }, 150);
    }
    document.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
    thumbEl.classList.add('active');
  }

  /* ── ACCORDION ────────────────────────────────────────────── */
  function toggleAcc(btn) {
    const body = btn.nextElementSibling;
    const isOpen = body.classList.contains('open');
    // Close all
    document.querySelectorAll('.acc-body').forEach(b => b.classList.remove('open'));
    document.querySelectorAll('.acc-toggle').forEach(b => b.classList.remove('open'));
    if (!isOpen) {
      body.classList.add('open');
      btn.classList.add('open');
    }
  }

  // Exponer globalmente para los onclick del HTML
  window.selectSize       = selectSize;
  window.selectVariant    = selectVariant;
  window.changeQty        = changeQty;
  window.handleAddToCart  = handleAddToCart;
  window.switchImage      = switchImage;
  window.toggleAcc        = toggleAcc;

})();