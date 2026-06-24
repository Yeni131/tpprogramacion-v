/* ============================================================
   MYA MY ACCOUNT  —  static/js/my-account.js
   Carga, edita datos personales y permite cambiar contraseña.
   ============================================================ */
(function () {
  'use strict';

  const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';

  const els = {
    avatar:   document.getElementById('accountAvatar'),
    name:     document.getElementById('accountName'),
    email:    document.getElementById('accountEmail'),
    firstName: document.getElementById('profFirstName'),
    lastName:  document.getElementById('profLastName'),
    profEmail: document.getElementById('profEmail'),
    phone:     document.getElementById('profPhone'),
    address:   document.getElementById('profAddress'),
    profileForm: document.getElementById('profileForm'),
    profileMsg:  document.getElementById('profileMsg'),
    btnSaveProfile: document.getElementById('btnSaveProfile'),
    passwordForm: document.getElementById('passwordForm'),
    passwordMsg:  document.getElementById('passwordMsg'),
    btnSavePassword: document.getElementById('btnSavePassword'),
    pwCurrent: document.getElementById('pwCurrent'),
    pwNew:     document.getElementById('pwNew'),
    pwNew2:    document.getElementById('pwNew2'),
  };

  function showMessage(el, text, isError) {
    el.textContent = text;
    el.classList.remove('success', 'error');
    el.classList.add(isError ? 'error' : 'success', 'show');
    setTimeout(() => el.classList.remove('show'), 4000);
  }

  function renderAvatar(user) {
    if (user.avatar_url) {
      els.avatar.innerHTML = `<img src="${user.avatar_url}" alt="Avatar" />`;
    } else {
      const initials = (
        (user.first_name?.[0] ?? '') + (user.last_name?.[0] ?? '')
      ).toUpperCase() || '?';
      els.avatar.textContent = initials;
    }
  }

  async function loadProfile() {
    try {
      const res = await fetch('/api/users/me/', { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const user = await res.json();

      const fullName = `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim();
      els.name.textContent  = fullName || user.email;
      els.email.textContent = user.email;
      renderAvatar(user);

      els.firstName.value = user.first_name ?? '';
      els.lastName.value  = user.last_name ?? '';
      els.profEmail.value = user.email ?? '';
      els.phone.value     = user.phone ?? '';
      els.address.value   = user.address ?? '';

    } catch (e) {
      console.error('loadProfile:', e);
      showMessage(els.profileMsg, 'No pudimos cargar tus datos.', true);
    }
  }

  els.profileForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    els.btnSaveProfile.disabled = true;
    els.btnSaveProfile.textContent = 'Guardando...';

    try {
      const res = await fetch('/api/users/me/', {
        method: 'PATCH',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF(),
        },
        body: JSON.stringify({
          first_name: els.firstName.value.trim(),
          last_name:  els.lastName.value.trim(),
          phone:      els.phone.value.trim(),
          address:    els.address.value.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        const firstError = data.errors
          ? Object.values(data.errors).flat()[0]
          : 'Error al guardar los cambios.';
        showMessage(els.profileMsg, firstError, true);
        return;
      }

      els.name.textContent = `${data.user.first_name} ${data.user.last_name}`.trim() || data.user.email;
      renderAvatar(data.user);
      showMessage(els.profileMsg, 'Datos actualizados correctamente.', false);

    } catch (e) {
      showMessage(els.profileMsg, 'Error de conexión. Intentá de nuevo.', true);
    } finally {
      els.btnSaveProfile.disabled = false;
      els.btnSaveProfile.textContent = 'Guardar cambios';
    }
  });

  els.passwordForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    if (els.pwNew.value !== els.pwNew2.value) {
      showMessage(els.passwordMsg, 'Las contraseñas no coinciden.', true);
      return;
    }

    els.btnSavePassword.disabled = true;
    els.btnSavePassword.textContent = 'Actualizando...';

    try {
      const res = await fetch('/api/users/change-password/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF(),
        },
        body: JSON.stringify({
          current_password: els.pwCurrent.value,
          new_password:      els.pwNew.value,
          new_password2:      els.pwNew2.value,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        const firstError = data.errors
          ? Object.values(data.errors).flat()[0]
          : 'Error al actualizar la contraseña.';
        showMessage(els.passwordMsg, firstError, true);
        return;
      }

      showMessage(els.passwordMsg, 'Contraseña actualizada correctamente.', false);
      els.passwordForm.reset();

    } catch (e) {
      showMessage(els.passwordMsg, 'Error de conexión. Intentá de nuevo.', true);
    } finally {
      els.btnSavePassword.disabled = false;
      els.btnSavePassword.textContent = 'Actualizar contraseña';
    }
  });

  document.addEventListener('DOMContentLoaded', loadProfile);
})();