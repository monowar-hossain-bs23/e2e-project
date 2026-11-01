/**
 * Basha Pass — Listing Feed Client Interaction (Story 026)
 * Handles offcanvas filter drawer toggle, budget range updates, and sort selection.
 */
document.addEventListener('DOMContentLoaded', () => {
  const drawer = document.getElementById('filter-drawer');
  const backdrop = document.getElementById('filter-backdrop');
  const openBtn = document.getElementById('open-filters-btn');
  const closeBtn = document.getElementById('close-filters-btn');
  const clearBtn = document.getElementById('clear-filters-btn');
  const filterForm = document.getElementById('filter-form');
  const sortSelect = document.getElementById('sort-select');

  function openDrawer() {
    if (drawer && backdrop) {
      drawer.classList.add('is-open');
      backdrop.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeDrawer() {
    if (drawer && backdrop) {
      drawer.classList.remove('is-open');
      backdrop.classList.remove('is-open');
      document.body.style.overflow = '';
    }
  }

  if (openBtn) {
    openBtn.addEventListener('click', openDrawer);
  }
  if (closeBtn) {
    closeBtn.addEventListener('click', closeDrawer);
  }
  if (backdrop) {
    backdrop.addEventListener('click', closeDrawer);
  }

  // Escape key closes drawer
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('is-open')) {
      closeDrawer();
    }
  });

  // Clear all filters resets inputs and submits form
  if (clearBtn && filterForm) {
    clearBtn.addEventListener('click', () => {
      // Uncheck all checkboxes and radios
      const inputs = filterForm.querySelectorAll('input[type="checkbox"], input[type="radio"]');
      inputs.forEach((input) => {
        if (input.value === 'any' || input.value === 'flexible') {
          input.checked = true;
        } else {
          input.checked = false;
        }
      });

      // Reset budget inputs
      const minBudget = filterForm.querySelector('input[name="budget_min"]');
      const maxBudget = filterForm.querySelector('input[name="budget_max"]');
      if (minBudget) minBudget.value = '500';
      if (maxBudget) maxBudget.value = '50000';

      // Submit immediately
      window.location.href = window.location.pathname;
    });
  }

  // Sort select auto-submits with existing query params
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      const url = new URL(window.location.href);
      url.searchParams.set('sort', sortSelect.value);
      url.searchParams.set('page', '1');
      window.location.href = url.toString();
    });
  }

  // Budget slider synchronization if present
  const budgetSlider = document.getElementById('budget-max-slider');
  const budgetOutput = document.getElementById('budget-max-display');
  const budgetInput = document.getElementById('budget-max-input');
  if (budgetSlider && budgetOutput) {
    budgetSlider.addEventListener('input', () => {
      const val = parseInt(budgetSlider.value, 10).toLocaleString();
      budgetOutput.textContent = `৳${val}`;
      if (budgetInput) {
        budgetInput.value = budgetSlider.value;
      }
    });
  }
});
