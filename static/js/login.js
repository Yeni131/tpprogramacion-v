/* ============================================================
   MYA LOGIN  —  static/js/login.js
   Maneja el formulario de inicio de sesión.
   Extraído de templates/users/login.html
   ============================================================ */
(function () {
  'use strict';

  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  async function doLogin() {
    const btn   = document.getElementById('btnLogin');
    const errEl = document.getElementById('loginError');
    const email    = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    errEl.style.display = 'none';

    if (!email || !password) {
      errEl.textContent = 'Completá email y contraseña.';
      errEl.style.display = 'block';
      return;
    }

    btn.disabled    = true;
    btn.textContent = 'Ingresando...';

    try {
      const res = await fetch('/api/users/login/', {
        method:      'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  getCookie('csrftoken'),
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        const msg = data.errors?.detail || 'Credenciales incorrectas.';
        errEl.textContent   = msg;
        errEl.style.display = 'block';
        return;
      }

      // Redirigir al checkout (o al 'next' si viene de @login_required)
      const params = new URLSearchParams(window.location.search);
      window.location.href = params.get('next') || '/checkout/';

    } catch (e) {
      errEl.textContent   = 'Error de conexión. Intentá de nuevo.';
      errEl.style.display = 'block';
    } finally {
      btn.disabled    = false;
      btn.textContent = 'Iniciar sesión';
    }
  }

  // Permitir Enter en los campos
  document.addEventListener('DOMContentLoaded', () => {
    ['loginEmail', 'loginPassword'].forEach(id => {
      document.getElementById(id)?.addEventListener('keydown', e => {
        if (e.key === 'Enter') doLogin();
      });
    });
  });

  // Exponer globalmente para el onclick del botón en el HTML
  window.doLogin = doLogin;

})();