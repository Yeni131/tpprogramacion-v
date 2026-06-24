/* ============================================================
   MYA NAVBAR ENGINE  —  static/js/navbar.js
   Maneja el menú de usuario (dropdown) y el logout.
   Extraído de base.html
   ============================================================ */
(function () {
  'use strict';

  /* ── Dropdown toggle ───────────────────────────────── */
  const wrap = document.getElementById('userMenuWrap');
  const btn  = document.getElementById('userMenuBtn');

  if (wrap && btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      const isOpen = wrap.classList.toggle('open');
      btn.setAttribute('aria-expanded', isOpen);
    });

    // Cerrar al hacer clic fuera
    document.addEventListener('click', function (e) {
      if (!wrap.contains(e.target)) {
        wrap.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });

    // Cerrar con Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        wrap.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
        btn.focus();
      }
    });
  }

  /* ── Logout ────────────────────────────────────────── */
  window.myaLogout = async function () {
    try {
      const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
      await fetch('/api/users/logout/', {
        method:      'POST',
        credentials: 'include',
        headers:     { 'X-CSRFToken': csrfToken },
      });
      // Redirigir al home independientemente de la respuesta
      window.location.href = '/';
    } catch (e) {
      window.location.href = '/';
    }
  };

})();