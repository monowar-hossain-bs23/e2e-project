/**
 * Basha Pass — Listing Detail Page Gallery & Interactions (Story 028)
 * Handles photo thumbnail switching and copy-link actions.
 */
document.addEventListener('DOMContentLoaded', () => {
  const mainImg = document.getElementById('gallery-main-img');
  const thumbs = document.querySelectorAll('.bp-gallery__thumb');

  if (mainImg && thumbs.length > 0) {
    thumbs.forEach((thumb) => {
      thumb.addEventListener('click', () => {
        const fullUrl = thumb.getAttribute('data-full-url');
        if (fullUrl) {
          mainImg.setAttribute('src', fullUrl);
          thumbs.forEach((t) => t.classList.remove('is-active'));
          thumb.classList.add('is-active');
        }
      });
    });
  }

  // Share button copy link action
  const shareBtn = document.getElementById('share-listing-btn');
  if (shareBtn) {
    shareBtn.addEventListener('click', () => {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(window.location.href).then(() => {
          const originalText = shareBtn.innerHTML;
          shareBtn.innerHTML = '<i class="bi bi-check2 me-1"></i> Copied!';
          setTimeout(() => {
            shareBtn.innerHTML = originalText;
          }, 2000);
        });
      }
    });
  }

  // Copy phone action
  const copyPhoneBtn = document.getElementById('copy-phone-btn');
  if (copyPhoneBtn) {
    copyPhoneBtn.addEventListener('click', () => {
      const phone = copyPhoneBtn.getAttribute('data-phone');
      if (phone && navigator.clipboard) {
        navigator.clipboard.writeText(phone).then(() => {
          const originalText = copyPhoneBtn.innerHTML;
          copyPhoneBtn.innerHTML = '<i class="bi bi-check2 me-1"></i> Copied!';
          setTimeout(() => {
            copyPhoneBtn.innerHTML = originalText;
          }, 2000);
        });
      }
    });
  }
});
