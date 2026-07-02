(function () {
  "use strict";

  /* ─────────────────────────────────────────────────────
     ENDPOINTS
  ───────────────────────────────────────────────────── */
  const API = {
    CART:     "/api/cart/",
    CHECKOUT: "/api/orders/checkout/",
    ME:       "/api/users/me/",
    COUPON_APPLY: "/api/coupons/apply/",
  };

  /* ─────────────────────────────────────────────────────
     PASO ACTUAL
  ───────────────────────────────────────────────────── */
  let currentStep = 1;

  /* ─────────────────────────────────────────────────────
     ESTADO DEL CUPÓN — necesario para recalcular el total
     cuando se aplica un descuento sin recargar el carrito
  ───────────────────────────────────────────────────── */
  let cartSubtotal    = 0;
  let appliedDiscount = 0; // porcentaje, ej. 10 = 10%

  /* ─────────────────────────────────────────────────────
     CSRF — requerido para POST con sesión Django
  ───────────────────────────────────────────────────── */
  function getCookie(name) {
    const v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return v ? v.pop() : "";
  }

  /* ─────────────────────────────────────────────────────
     AUTOCOMPLETAR — llama /api/users/me/ y rellena campos
     Solo nombre, apellido y email. Teléfono queda vacío.
  ───────────────────────────────────────────────────── */
  async function prefillUserData() {
    try {
      const res = await fetch(API.ME, { credentials: "include" });
      if (!res.ok) return; // no autenticado o error → nada
      const user = await res.json();

      const nombre   = document.getElementById("shippingNombre");
      const apellido = document.getElementById("shippingApellido");
      const email    = document.getElementById("shippingEmail");

      if (nombre   && user.first_name) nombre.value   = user.first_name;
      if (apellido && user.last_name)  apellido.value  = user.last_name;
      if (email    && user.email)      email.value     = user.email;
      // Teléfono: NO autocompletar — el usuario lo ingresa manualmente

    } catch (e) {
      // Silencioso: si falla el prefill, el usuario llena a mano
      console.warn("prefillUserData:", e);
    }
  }

  /* ─────────────────────────────────────────────────────
     CART — carga y renderiza el resumen lateral
  ───────────────────────────────────────────────────── */
  async function loadCart() {
    try {
      const res = await fetch(API.CART, { credentials: "include" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data  = await res.json();

      // La API puede devolver { items: [...] } o directamente [...]
      const items = Array.isArray(data)
        ? data
        : (data.items || data.cart_items || []);

      renderCheckoutSummary(items);
    } catch (err) {
      console.error("Error cargando carrito:", err);
      const container = document.getElementById("checkoutItems");
      if (container) {
        container.innerHTML =
          "<p style='color:red;font-size:.85rem'>Error al cargar el carrito.</p>";
      }
    }
  }

  /* ─────────────────────────────────────────────────────
     RENDER SUMMARY
     Intenta múltiples claves para ser compatible con
     la estructura del CartSerializer de este proyecto.

     CartItem devuelve algo como:
     {
       id, quantity,
       product: { id, name, price, image },
       variant: { id, name, ... },
       unit_price, subtotal          ← posibles
     }
  ───────────────────────────────────────────────────── */
  function getField(item, ...keys) {
    for (const key of keys) {
      const val = key
        .split(".")
        .reduce((obj, k) => (obj && obj[k] !== undefined ? obj[k] : undefined), item);
      if (val !== undefined && val !== null && val !== "") return val;
    }
    return null;
  }

  function renderCheckoutSummary(items) {
    const container = document.getElementById("checkoutItems");
    if (!container) return;

    if (!items || items.length === 0) {
      container.innerHTML =
        "<p style='font-size:.85rem;color:var(--clr-muted)'>Carrito vacío</p>";
      setTotals(0);
      return;
    }

    let html     = "";
    let subtotal = 0;

    items.forEach(item => {
      /* ── Nombre del producto ──────────────────────────────────────────── */
      const name = getField(
        item,
        "product_name",   // CartSerializer puede exponer este campo flat
        "product.name",   // estructura anidada
        "name",           // si CartSerializer es flat
        "title",
        "product.title"
      ) || "Producto";

      /* ── Precio unitario ─────────────────────────────────────────────── */
      // Intentar en este orden de prioridad:
      // 1. unit_price (campo flat del CartSerializer)
      // 2. price
      // 3. product.price (estructura anidada)
      const price = Number(
        getField(
          item,
          "unit_price",
          "price",
          "product.price",
          "sale_price",
          "product.sale_price"
        ) || 0
      );

      /* ── Cantidad ────────────────────────────────────────────────────── */
      const qty = Number(getField(item, "quantity", "qty", "amount") || 1);

      /* ── Imagen ──────────────────────────────────────────────────────── */
      // BUG FIX: si image es null/undefined → mostrar placeholder SVG inline
      // en lugar de intentar cargar /media/placeholder.jpg (que da 404)
      const imageUrl = getField(
        item,
        "image_url",
        "image",
        "product.image_url",
        "product.image",
        "product.thumbnail",
        "thumbnail"
      );

      /* ── Variante ────────────────────────────────────────────────────── */
      const variant = getField(
        item,
        "variant_name",
        "variant.name",
        "variant",
        "size",
        "color"
      );

      const lineTotal = price * qty;
      subtotal += lineTotal;

      // Imagen: URL real o placeholder SVG inline (sin request HTTP)
      const imgTag = imageUrl
        ? `<img src="${imageUrl}"
                alt="${escapeHtml(name)}"
                class="summary-item-img"
                onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" />
           <div class="summary-item-img"
                style="display:none;background:var(--clr-beige);align-items:center;justify-content:center">
             <i class="bi bi-bag" style="color:var(--clr-muted)"></i>
           </div>`
        : `<div class="summary-item-img"
                style="background:var(--clr-beige);display:flex;align-items:center;justify-content:center">
             <i class="bi bi-bag" style="color:var(--clr-muted)"></i>
           </div>`;

      html += `
        <div class="summary-item">
          ${imgTag}
          <div class="summary-item-info">
            <div class="summary-item-name">${escapeHtml(name)}</div>
            <div class="summary-item-variant">
              ${variant ? escapeHtml(String(variant)) + " &times; " + qty : "&times; " + qty}
            </div>
          </div>
          <div class="summary-item-price">Gs. ${formatPrice(lineTotal)}</div>
        </div>
      `;
    });

    container.innerHTML = html;
    setTotals(subtotal);
  }

  function setTotals(subtotal) {
    cartSubtotal = subtotal; // guardamos para poder recalcular al aplicar/quitar cupón
    renderTotals();
  }

  /* ─────────────────────────────────────────────────────
     RENDER TOTALS — recalcula subtotal, descuento y total
     a partir de cartSubtotal + appliedDiscount (estado del módulo)
  ───────────────────────────────────────────────────── */
  function renderTotals() {
    const subtotalEl   = document.getElementById("summarySubtotal");
    const totalEl      = document.getElementById("summaryTotal");
    const discountLine = document.getElementById("discountLine");
    const discountEl   = document.getElementById("summaryDiscount");

    const discountAmount = cartSubtotal * (appliedDiscount / 100);
    const total           = cartSubtotal - discountAmount;

    if (subtotalEl) subtotalEl.textContent = "Gs. " + formatPrice(cartSubtotal);
    if (totalEl)    totalEl.textContent    = "Gs. " + formatPrice(total);

    if (appliedDiscount > 0) {
      if (discountLine) discountLine.style.display = "flex";
      if (discountEl)   discountEl.textContent = "- Gs. " + formatPrice(discountAmount);
    } else {
      if (discountLine) discountLine.style.display = "none";
    }
  }

  function formatPrice(num) {
    return Math.round(num).toLocaleString("es-PY");
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ─────────────────────────────────────────────────────
     NAVEGACIÓN DE PASOS
  ───────────────────────────────────────────────────── */
  function goToStep(step) {
    currentStep = step;

    document.querySelectorAll(".checkout-step-panel").forEach(panel => {
      panel.classList.toggle("step-visible", Number(panel.dataset.step) === step);
    });

    document.querySelectorAll(".step").forEach(el => {
      const n = Number(el.dataset.stepNum);
      el.classList.toggle("active", n === step);
      el.classList.toggle("done",   n < step);
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function continueToPayment() {
    const required = [
      "shippingNombre",
      "shippingApellido",
      "shippingEmail",
      "shippingTelefono",
      "shippingDireccion",
      "shippingCiudad",
    ];
    let valid = true;
    required.forEach(id => {
      const el = document.getElementById(id);
      if (el && !el.value.trim()) {
        el.style.borderColor = "red";
        valid = false;
      } else if (el) {
        el.style.borderColor = "";
      }
    });
    if (!valid) {
      alert("Por favor completá los campos obligatorios.");
      return;
    }
    goToStep(2);
  }

  function continueToConfirm() {
    const selected = document.querySelector('input[name="payment"]:checked');
    if (!selected) {
      alert("Por favor seleccioná un método de pago.");
      return;
    }
    buildConfirmSummary();
    goToStep(3);
  }

  function buildConfirmSummary() {
    const nombre    = document.getElementById("shippingNombre")?.value    || "";
    const apellido  = document.getElementById("shippingApellido")?.value  || "";
    const email     = document.getElementById("shippingEmail")?.value     || "";
    const telefono  = document.getElementById("shippingTelefono")?.value  || "";
    const direccion = document.getElementById("shippingDireccion")?.value || "";
    const ciudad    = document.getElementById("shippingCiudad")?.value    || "";
    const ref       = document.getElementById("shippingReferencia")?.value || "";
    const cp        = document.getElementById("shippingCP")?.value        || "";

    const payment = document.querySelector('input[name="payment"]:checked')?.value || "";
    const paymentLabels = {
      efectivo:      "Efectivo",
      transferencia: "Transferencia bancaria",
      credito:       "Tarjeta de Crédito",
      debito:        "Tarjeta de Débito",
    };

    const confirmShipping = document.getElementById("confirmShipping");
    if (confirmShipping) {
      confirmShipping.innerHTML = `
        <strong>${escapeHtml(nombre)} ${escapeHtml(apellido)}</strong><br>
        ${escapeHtml(email)}${telefono ? " · " + escapeHtml(telefono) : ""}<br>
        ${escapeHtml(direccion)}, ${escapeHtml(ciudad)}${cp ? " (" + escapeHtml(cp) + ")" : ""}
        ${ref ? "<br><em>" + escapeHtml(ref) + "</em>" : ""}
      `;
    }

    const confirmPayment = document.getElementById("confirmPayment");
    if (confirmPayment) {
      confirmPayment.textContent = paymentLabels[payment] || payment;
    }
  }

  /* ─────────────────────────────────────────────────────
     PLACE ORDER — envía al backend con campos correctos
  ───────────────────────────────────────────────────── */
  async function placeOrder() {
    const btn = document.getElementById("btnConfirmar");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Procesando...';
    }

    try {
      // ── BUG FIX: los campos deben coincidir con ShippingSerializer ───────
      // Serializer espera: first_name, last_name, phone, address, city
      // El HTML usa ids: shippingNombre, shippingApellido, shippingTelefono, shippingDireccion, shippingCiudad
      const payload = {
        shipping: {
          first_name: document.getElementById("shippingNombre")?.value?.trim()    || "",
          last_name:  document.getElementById("shippingApellido")?.value?.trim()  || "",
          email:      document.getElementById("shippingEmail")?.value?.trim()     || "",
          phone:      document.getElementById("shippingTelefono")?.value?.trim()  || "",
          address:    document.getElementById("shippingDireccion")?.value?.trim() || "",
          city:       document.getElementById("shippingCiudad")?.value?.trim()    || "",
          reference:  document.getElementById("shippingReferencia")?.value?.trim() || "",
          postal_code:document.getElementById("shippingCP")?.value?.trim()        || "",
        },
        payment: {
          // Valores enviados: 'efectivo' | 'transferencia' | 'credito' | 'debito'
          // El serializer ya los acepta directamente
          method: document.querySelector('input[name="payment"]:checked')?.value || "",
        },
        billing: (() => {
          const cb = document.getElementById("billingToggle");
          if (!cb?.checked) return { wants_invoice: false };
          return {
            wants_invoice: true,
            business_name:  document.getElementById("billingNombre")?.value?.trim()    || "",
            ruc:            document.getElementById("billingRUC")?.value?.trim()       || "",
            // FIX: este campo existía en el HTML pero nunca se enviaba al backend
            fiscal_address: document.getElementById("billingDireccion")?.value?.trim() || "",
          };
        })(),
      };

      const res = await fetch(API.CHECKOUT, {
        method:      "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken":  getCookie("csrftoken"),   // ← FIX: CSRF para sesión Django
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        // FIX: priorizar el mensaje de stock insuficiente si existe,
        // para que el usuario vea un mensaje claro en vez de JSON crudo
        const errMsg = data.errors?.stock
          || (data.errors
              ? Object.entries(data.errors)
                  .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
                  .join("\n")
              : (data.detail || "Error al procesar el pedido."));
        alert("Error:\n" + errMsg);
        return;
      }

      // Éxito → guardamos el order_id para poder ofrecer la descarga de factura
      window.location.href = "/api/orden-confirmada/" + (data.order_id || "");

    } catch (err) {
      console.error(err);
      alert("Error inesperado al procesar el pedido.");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-lock-fill"></i> Confirmar pedido';
      }
    }
  }

  /* ─────────────────────────────────────────────────────
     UI — SELECCIÓN DE PAGO
  ───────────────────────────────────────────────────── */
  function selectPayment(el, type) {
    document.querySelectorAll(".payment-option").forEach(o => o.classList.remove("selected"));
    el.classList.add("selected");
    const card = document.getElementById("cardFields");
    if (card) card.classList.toggle("open", type === "credito" || type === "debito");
  }

  /* ─────────────────────────────────────────────────────
     UI — TOGGLE FACTURA
  ───────────────────────────────────────────────────── */
  function toggleBilling() {
    const cb  = document.getElementById("billingToggle");
    const box = document.getElementById("billingFields");
    if (!cb || !box) return;
    box.classList.toggle("open", cb.checked);
  }

  /* ─────────────────────────────────────────────────────
     FORMATTERS
  ───────────────────────────────────────────────────── */
  function formatCardNumber(input) {
    let v = input.value.replace(/\D/g, "").slice(0, 16);
    input.value = v.replace(/(.{4})/g, "$1 ").trim();
  }

  function formatExpiry(input) {
    let v = input.value.replace(/\D/g, "").slice(0, 4);
    input.value = v.length >= 3 ? v.slice(0, 2) + " / " + v.slice(2) : v;
  }

  /* ─────────────────────────────────────────────────────
     CUPÓN — valida contra /api/coupons/apply/ y actualiza
     el resumen en tiempo real (sin recargar el carrito)
  ───────────────────────────────────────────────────── */
  async function applyCoupon() {
    const input = document.getElementById("couponInput");
    const code  = input?.value?.trim();
    if (!code) return;

    const btn = document.querySelector(".btn-coupon");
    if (btn) { btn.disabled = true; btn.textContent = "Validando..."; }

    try {
      const res = await fetch(API.COUPON_APPLY, {
        method:      "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken":  getCookie("csrftoken"),
        },
        body: JSON.stringify({ code }),
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.error || "Cupón inválido o expirado.");
        return;
      }

      appliedDiscount = parseFloat(data.discount);
      renderTotals();
      input.value = "";
      input.placeholder = `Cupón "${data.code}" aplicado ✓`;

    } catch (e) {
      console.error("applyCoupon:", e);
      alert("Error de conexión al validar el cupón.");
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Aplicar"; }
    }
  }

  /* ─────────────────────────────────────────────────────
     INIT
  ───────────────────────────────────────────────────── */
  document.addEventListener("DOMContentLoaded", () => {
    goToStep(1);
    loadCart();
    prefillUserData(); // ← autocompletado con datos del usuario logueado
  });

  /* ─────────────────────────────────────────────────────
     EXPORTS GLOBALES (llamados desde el HTML)
  ───────────────────────────────────────────────────── */
  window.loadCart              = loadCart;
  window.renderCheckoutSummary = renderCheckoutSummary;
  window.placeOrder            = placeOrder;
  window.selectPayment         = selectPayment;
  window.toggleBilling         = toggleBilling;
  window.formatCardNumber      = formatCardNumber;
  window.formatExpiry          = formatExpiry;
  window.applyCoupon           = applyCoupon;
  window.goToStep              = goToStep;
  window.continueToPayment     = continueToPayment;
  window.continueToConfirm     = continueToConfirm;

})();