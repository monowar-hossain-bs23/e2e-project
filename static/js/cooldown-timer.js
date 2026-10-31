/**
 * Dynamic 24-hour Cooldown Timer for Basha Pass Rejection Screen (FR-5, Mockup 21)
 */
(function () {
  'use strict';

  function initCooldownTimer() {
    var timerEl = document.getElementById('cooldown-timer');
    if (!timerEl) return;

    var remainingSeconds = parseInt(timerEl.getAttribute('data-remaining-seconds'), 10);
    if (isNaN(remainingSeconds) || remainingSeconds <= 0) {
      unlockResubmission();
      return;
    }

    function formatTime(totalSeconds) {
      var hours = Math.floor(totalSeconds / 3600);
      var minutes = Math.floor((totalSeconds % 3600) / 60);
      var seconds = totalSeconds % 60;

      var pad = function (num) {
        return num < 10 ? '0' + num : num.toString();
      };

      return pad(hours) + ':' + pad(minutes) + ':' + pad(seconds);
    }

    function unlockResubmission() {
      timerEl.textContent = '00:00:00';
      var helperEl = document.getElementById('cooldown-helper');
      if (helperEl) {
        helperEl.textContent = 'You can now submit new documents. Please ensure all photos are clear and legible.';
        helperEl.classList.remove('text-muted');
        helperEl.classList.add('text-success', 'fw-semibold');
      }

      var resubmitBtn = document.getElementById('resubmit-btn');
      if (resubmitBtn) {
        resubmitBtn.removeAttribute('disabled');
        resubmitBtn.classList.remove('disabled');
        resubmitBtn.setAttribute('aria-disabled', 'false');
      }
    }

    // Initial render
    timerEl.textContent = formatTime(remainingSeconds);

    var intervalId = setInterval(function () {
      remainingSeconds -= 1;
      if (remainingSeconds <= 0) {
        clearInterval(intervalId);
        unlockResubmission();
      } else {
        timerEl.textContent = formatTime(remainingSeconds);
      }
    }, 1000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCooldownTimer);
  } else {
    initCooldownTimer();
  }
})();
