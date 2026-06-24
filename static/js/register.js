/* ============================================================
   MYA REGISTER  —  static/js/register.js
   Maneja el formulario de registro de usuario.
   Extraído de templates/users/register.html
   ============================================================ */
(function () {
  'use strict';

  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  async function doRegister() {
    const btn   = document.getElementById('btnRegister');
    const errEl = document.getElementById('regError');

    const first_name = document.getElementById('regFirstName').value.trim();
    const last_name  = document.getElementById('regLastName').value.trim();
    const email      = document.getElementById('regEmail').value.trim();
    const password   = document.getElementById('regPassword').value;
    const password2  = document.getElementById('regPassword2').value;

    errEl.style.display = 'none';

    // Validación client-side básica
    if (!first_name || !last_name || !email || !password || !password2) {
      errEl.textContent   = 'Completá todos los campos.';
      errEl.style.display = 'block';
      return;
    }
    if (password !== password2) {
      errEl.textContent   = 'Las contraseñas no coinciden.';
      errEl.style.display = 'block';
      return;
    }

    btn.disabled    = true;
    btn.textContent = 'Creando cuenta...';

    try {
      const res = await fetch('/api/users/register/', {
        method:      'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  getCookie('csrftoken'),
        },
        body: JSON.stringify({ first_name, last_name, email, password, password2 }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        // Mostrar primer error del serializer
        const errs = data.errors || {};
        const msg  = errs.email?.[0]
                  || errs.password?.[0]
                  || errs.password2?.[0]
                  || errs.non_field_errors?.[0]
                  || errs.detail
                  || 'Error al crear la cuenta.';
        errEl.textContent   = msg;
        errEl.style.display = 'block';
        return;
      }

      // Registro exitoso → directo al checkout
      window.location.href = '/checkout/';

    } catch (e) {
      errEl.textContent   = 'Error de conexión. Intentá de nuevo.';
      errEl.style.display = 'block';
    } finally {
      btn.disabled    = false;
      btn.textContent = 'Crear cuenta';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('regPassword2')?.addEventListener('keydown', e => {
      if (e.key === 'Enter') doRegister();
    });
  });

  // Exponer globalmente para el onclick del botón en el HTML
  window.doRegister = doRegister;

})();