/* ============================================================
   MYA REVIEWS  —  static/js/reviews.js
   Carga, renderiza y permite publicar reseñas de un producto.

   DEPENDENCIAS:
   - window.PRODUCT_ID  (definido en detail.html)
   - window.MYA_USER     (definido en base.html, con isAuthenticated)
   ============================================================ */
(function () {
  'use strict';

  const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';

  const els = {
    avg:          document.getElementById('reviewsAvg'),
    avgStars:     document.getElementById('reviewsAvgStars'),
    count:        document.getElementById('reviewsCount'),
    list:         document.getElementById('reviewsList'),
    formCard:     document.getElementById('reviewFormCard'),
    loginPrompt:  document.getElementById('reviewLoginPrompt'),
    starInput:    document.getElementById('starInput'),
    comment:      document.getElementById('reviewComment'),
    btnSubmit:    document.getElementById('btnSubmitReview'),
    formMsg:      document.getElementById('reviewFormMsg'),
  };

  let selectedRating = 0;

  function buildStarsHtml(rating, max = 5) {
    let html = '';
    for (let i = 1; i <= max; i++) {
      html += i <= Math.round(rating)
        ? '<i class="bi bi-star-fill"></i>'
        : '<i class="bi bi-star"></i>';
    }
    return html;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatDate(isoString) {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function renderSummary(avg, count) {
    els.avg.textContent      = avg > 0 ? avg.toFixed(1) : '—';
    els.avgStars.innerHTML   = buildStarsHtml(avg);
    els.count.textContent    = `${count} reseña${count === 1 ? '' : 's'}`;
  }

  function renderReviews(reviews) {
    if (!reviews.length) {
      els.list.innerHTML = `<div class="reviews-empty">Todavía no hay reseñas para este producto. ¡Sé el primero en dejar la tuya!</div>`;
      return;
    }

    els.list.innerHTML = reviews.map(r => `
      <div class="review-item">
        <div class="review-item-header">
          <span class="review-author">${escapeHtml(r.user_name)}</span>
          <span class="review-stars">${buildStarsHtml(r.rating)}</span>
        </div>
        <div class="review-date">${formatDate(r.created)}</div>
        <p class="review-comment">${escapeHtml(r.comment)}</p>
      </div>
    `).join('');
  }

  async function loadReviews() {
    try {
      const res = await fetch(`/api/reviews/${window.PRODUCT_ID}/`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      renderSummary(data.average_rating, data.total_reviews);
      renderReviews(data.reviews);

    } catch (e) {
      console.error('loadReviews:', e);
      els.list.innerHTML = `<div class="reviews-empty">No pudimos cargar las reseñas.</div>`;
    }
  }

  function setupStarInput() {
    const stars = els.starInput.querySelectorAll('i');
    stars.forEach(star => {
      star.addEventListener('mouseenter', () => highlightStars(parseInt(star.dataset.value)));
      star.addEventListener('mouseleave', () => highlightStars(selectedRating));
      star.addEventListener('click', () => {
        selectedRating = parseInt(star.dataset.value);
        highlightStars(selectedRating);
      });
    });
  }

  function highlightStars(rating) {
    const stars = els.starInput.querySelectorAll('i');
    stars.forEach(star => {
      const isFilled = parseInt(star.dataset.value) <= rating;
      star.classList.toggle('filled', isFilled);
      star.className = isFilled ? 'bi bi-star-fill filled' : 'bi bi-star';
    });
  }

  function showFormMessage(text, isError) {
    els.formMsg.textContent = text;
    els.formMsg.classList.remove('success', 'error');
    els.formMsg.classList.add(isError ? 'error' : 'success', 'show');
    setTimeout(() => els.formMsg.classList.remove('show'), 4000);
  }

  async function submitReview() {
    if (selectedRating < 1) {
      showFormMessage('Seleccioná una calificación de 1 a 5 estrellas.', true);
      return;
    }
    const comment = els.comment.value.trim();
    if (!comment) {
      showFormMessage('Escribí un comentario antes de publicar.', true);
      return;
    }

    els.btnSubmit.disabled = true;
    els.btnSubmit.textContent = 'Publicando...';

    try {
      const res = await fetch(`/api/reviews/${window.PRODUCT_ID}/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF(),
        },
        body: JSON.stringify({ rating: selectedRating, comment }),
      });

      const data = await res.json();

      if (!res.ok) {
        const firstError = Array.isArray(data)
          ? data[0]
          : Object.values(data).flat()[0] || 'Error al publicar la reseña.';
        showFormMessage(firstError, true);
        return;
      }

      showFormMessage('¡Gracias por tu reseña!', false);
      els.comment.value = '';
      selectedRating = 0;
      highlightStars(0);
      els.formCard.style.display = 'none'; // ya dejó su reseña, no puede dejar otra
      await loadReviews();

    } catch (e) {
      console.error('submitReview:', e);
      showFormMessage('Error de conexión. Intentá de nuevo.', true);
    } finally {
      els.btnSubmit.disabled = false;
      els.btnSubmit.textContent = 'Publicar reseña';
    }
  }

  function init() {
    const isAuthenticated = window.MYA_USER?.isAuthenticated ?? false;

    if (isAuthenticated) {
      els.formCard.style.display = 'block';
      setupStarInput();
      els.btnSubmit.addEventListener('click', submitReview);
    } else {
      els.loginPrompt.style.display = 'flex';
    }

    loadReviews();
  }

  document.addEventListener('DOMContentLoaded', init);
})();