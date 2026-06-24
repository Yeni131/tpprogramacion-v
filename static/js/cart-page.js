/* ============================================================
   MYA CART PAGE  —  static/js/cart-page.js
   Lógica de la página completa del carrito con formulario
   de checkout simplificado y modal de autenticación.
   Extraído de templates/cart/cart.html

   DEPENDENCIAS:
   - Cart  (de cart.js)
   - window.USER_IS_AUTHENTICATED → inyectado en base.html
   ============================================================ */
(function () {
  'use strict';

  const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';

  /* ── Carga y renderiza el carrito ──────────────────────────── */
  async function loadCart() {
    await Cart.fetchCart();

    const { items, total } = Cart.getState();

    const container   = document.getElementById('cart-page-items');
    const totalBlock  = document.getElementById('cart-page-total');
    const totalEl     = document.getElementById('cart-page-total-amount');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const formSection = document.getElementById('checkoutFormSection');

    container.innerHTML = '';

    if (!items.length) {
      container.innerHTML = `
        <div class="text-center py-5" style="color:var(--clr-muted);">
          <i class="bi bi-bag"
             style="font-size:2.5rem;opacity:.35;display:block;margin-bottom:1rem;"></i>
          <p>Tu carrito está vacío</p>
        </div>`;
      totalBlock.style.display  = 'none';
      checkoutBtn.style.display = 'none';
      formSection.style.display = 'none';
      return;
    }

    // Renderizar cada producto
    items.forEach(item => {
      const product     = item.product  ?? {};
      const variant     = item.variant  ?? null;
      const name        = product.name  ?? 'Producto';
      const variantName = variant?.name ?? '';
      const subtotal    = parseFloat(item.subtotal ?? 0);
      const unitPrice   = parseFloat(product.price ?? 0);
      const qty         = item.quantity ?? 1;

      const imgHtml = product.image
        ? `<img src="${product.image}"
                alt="${name}"
                style="width:100%;height:100%;object-fit:cover;"
                onerror="this.style.display='none'">`
        : '';

      const row = document.createElement('div');
      row.className  = 'd-flex align-items-center gap-3 py-3';
      row.dataset.id = item.id;
      row.style.borderBottom = '1px solid var(--clr-border)';

      row.innerHTML = `
        <div style="width:64px;height:64px;background:var(--clr-beige);
                    border-radius:var(--radius);flex-shrink:0;overflow:hidden;
                    display:flex;align-items:center;justify-content:center;">
          ${imgHtml}
        </div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:500;white-space:nowrap;
                      overflow:hidden;text-overflow:ellipsis;">${name}</div>
          ${variantName
            ? `<div style="font-size:.78rem;color:var(--clr-muted);">${variantName}</div>`
            : ''}
          <div style="font-size:.8rem;color:var(--clr-muted);">
            ${Cart.formatPrice(unitPrice)} ×
            <span class="page-qty-display">${qty}</span>
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0;">
          <div style="font-family:var(--font-display);font-size:1.05rem;
                      font-weight:500;margin-bottom:.4rem;">
            ${Cart.formatPrice(subtotal)}
          </div>
          <div class="d-flex align-items-center gap-1 justify-content-end">
            <button class="qty-btn page-dec" aria-label="Disminuir">−</button>
            <span class="qty-val"
                  style="min-width:24px;text-align:center;font-size:.88rem;">${qty}</span>
            <button class="qty-btn page-inc" aria-label="Aumentar">+</button>
          </div>
        </div>`;

      row.querySelector('.page-dec').addEventListener('click', () => {
        const cur = parseInt(row.querySelector('.qty-val').textContent, 10);
        updateItem(item.id, Math.max(0, cur - 1));
      });
      row.querySelector('.page-inc').addEventListener('click', () => {
        const cur = parseInt(row.querySelector('.qty-val').textContent, 10);
        updateItem(item.id, cur + 1);
      });

      container.appendChild(row);
    });

    // Total
    totalEl.textContent      = Cart.formatPrice(total);
    totalBlock.style.display = 'flex';

    // Mostrar botón solo si el formulario no está abierto
    if (formSection.style.display === 'none') {
      checkoutBtn.style.display = 'block';
    }
  }

  /* ── Actualizar cantidad ───────────────────────────────────── */
  async function updateItem(itemId, quantity) {
    try {
      const res = await fetch(`/api/cart/update/${itemId}/`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF() },
        body:    JSON.stringify({ quantity }),
      });
      if (!res.ok) throw new Error(await res.text());
      await loadCart();
    } catch (e) {
      console.error('updateItem:', e);
      Cart.showToast('Error al actualizar el carrito', true);
    }
  }

  /* ── Checkout ────────────────────────────────────────────── */
  function checkout() {
    if (!window.USER_IS_AUTHENTICATED) {
      showAuthModal();
      return;
    }
    document.getElementById('checkoutFormSection').style.display = 'block';
    document.getElementById('checkoutBtn').style.display         = 'none';
    document.getElementById('checkoutFormSection')
            .scrollIntoView({ behavior: 'smooth' });
  }

  function cancelCheckout() {
    document.getElementById('checkoutFormSection').style.display = 'none';
    document.getElementById('checkoutBtn').style.display         = 'block';
  }

  function togglePaymentFields() {
    const method = document.getElementById('co-payment-method').value;
    document.getElementById('fields-bank-transfer').style.display =
      method === 'bank_transfer' ? '' : 'none';
    document.getElementById('fields-cash').style.display =
      method === 'cash' ? '' : 'none';
  }

  function handleCheckoutSubmit() {
    const method = document.getElementById('co-payment-method').value;

    const formData = {
      shipping: {
        first_name: document.getElementById('co-first-name').value.trim(),
        last_name:  document.getElementById('co-last-name').value.trim(),
        email:      document.getElementById('co-email').value.trim(),
        phone:      document.getElementById('co-phone').value.trim(),
        address:    document.getElementById('co-address').value.trim(),
        city:       document.getElementById('co-city').value.trim(),
      },
      payment: { method },
    };

    if (method === 'bank_transfer') {
      formData.payment.bank             = document.getElementById('co-bank').value.trim();
      formData.payment.reference_number = document.getElementById('co-reference').value.trim();
      formData.payment.transfer_date    = document.getElementById('co-transfer-date').value;
    } else {
      formData.payment.amount_received  = document.getElementById('co-amount-received').value;
      formData.payment.observations     = document.getElementById('co-observations').value.trim();
    }

    submitCheckout(formData);
  }

  async function submitCheckout(formData) {
    const btn = document.querySelector('#checkoutFormSection .btn-checkout');
    btn.disabled    = true;
    btn.textContent = 'Procesando…';

    try {
      const res = await fetch('/api/orders/checkout/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF() },
        body:    JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) {
        const msg = data.errors
          ? Object.values(data.errors).flat().join(' — ')
          : (data.detail || 'Error al procesar el pedido');
        throw new Error(msg);
      }

      showOrderConfirmation(data.order_id);
      Cart.showToast(`✔ Orden #${data.order_id} creada`);
      await Cart.fetchCart(); // sincroniza badge del navbar

    } catch (err) {
      console.error('submitCheckout:', err);
      Cart.showToast('❌ ' + err.message, true);
      btn.disabled    = false;
      btn.textContent = 'Confirmar pedido';
    }
  }

  function showOrderConfirmation(orderId) {
    document.getElementById('cart-page-items').innerHTML = `
      <div class="text-center py-5">
        <i class="bi bi-check-circle"
           style="font-size:3rem;color:var(--clr-text);
                  display:block;margin-bottom:1rem;"></i>
        <h4 style="font-family:var(--font-display);">¡Pedido recibido!</h4>
        <p style="color:var(--clr-muted);font-size:.9rem;">Orden #${orderId}</p>
      </div>`;
    document.getElementById('cart-page-total').style.display     = 'none';
    document.getElementById('checkoutBtn').style.display         = 'none';
    document.getElementById('checkoutFormSection').style.display = 'none';
  }

  /* ── Auth modal ──────────────────────────────────────────── */
  function showAuthModal() {
    document.getElementById('authModal').style.display = 'block';
  }

  async function login() {
    try {
      const res = await fetch('/api/users/token/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: document.getElementById('auth-username').value,
          password: document.getElementById('auth-password').value,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('access',  data.access);
        localStorage.setItem('refresh', data.refresh);
        window.location.reload();
      } else {
        Cart.showToast('Error: ' + (data.detail || 'credenciales incorrectas'), true);
      }
    } catch {
      Cart.showToast('Error de red al iniciar sesión', true);
    }
  }

  async function register() {
    try {
      const res = await fetch('/api/users/register/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: document.getElementById('auth-username').value,
          password: document.getElementById('auth-password').value,
        }),
      });
      if (res.ok) {
        Cart.showToast('Usuario creado ✔ Ahora iniciá sesión');
      } else {
        const data = await res.json();
        Cart.showToast('Error: ' + JSON.stringify(data), true);
      }
    } catch {
      Cart.showToast('Error de red al registrarse', true);
    }
  }

  document.addEventListener('DOMContentLoaded', loadCart);

  // Exponer globalmente para los onclick del HTML
  window.checkout            = checkout;
  window.cancelCheckout      = cancelCheckout;
  window.togglePaymentFields = togglePaymentFields;
  window.handleCheckoutSubmit = handleCheckoutSubmit;
  window.showAuthModal       = showAuthModal;
  window.login               = login;
  window.register            = register;

})();