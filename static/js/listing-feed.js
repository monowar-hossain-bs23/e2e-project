/**
 * Basha Pass — Listing Feed Client Interaction (Story 026)
 * Handles offcanvas filter drawer, real-time HTMX filtering, budget slider, and sort sync.
 */
document.addEventListener('DOMContentLoaded', () => {
  const drawer = document.getElementById('filter-drawer');
  const backdrop = document.getElementById('filter-backdrop');
  const filterForm = document.getElementById('filter-form');

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

  // Delegated click handling ensures open/close works across HTMX DOM swaps
  document.addEventListener('click', (e) => {
    if (e.target.closest('#open-filters-btn')) {
      openDrawer();
    } else if (
      e.target.closest('#close-filters-btn') ||
      e.target.closest('#apply-filters-btn') ||
      e.target === backdrop
    ) {
      closeDrawer();
    }
  });

  // Escape key closes drawer
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('is-open')) {
      closeDrawer();
    }
  });

  // Clear all filters resets inputs and triggers real-time HTMX feed update
  document.addEventListener('click', (e) => {
    if (e.target.closest('#clear-filters-btn') && filterForm) {
      // Uncheck area and occupation checkboxes
      filterForm.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
        cb.checked = false;
        const chip = cb.closest('.bp-chip');
        if (chip) chip.classList.remove('bp-chip--selected');
      });

      // Reset radio defaults
      filterForm.querySelectorAll('input[type="radio"]').forEach((radio) => {
        if (radio.value === '' || radio.value === 'any' || radio.value === 'flexible') {
          radio.checked = true;
          const chip = radio.closest('.bp-chip');
          if (chip) chip.classList.add('bp-chip--selected');
        } else {
          radio.checked = false;
          const chip = radio.closest('.bp-chip');
          if (chip) chip.classList.remove('bp-chip--selected');
        }
      });

      // Reset budget inputs
      const minBudget = filterForm.querySelector('input[name="budget_min"]');
      const maxBudget = filterForm.querySelector('input[name="budget_max"]');
      const budgetSlider = document.getElementById('budget-max-slider');
      const budgetDisplay = document.getElementById('budget-max-display');

      if (minBudget) minBudget.value = '500';
      if (maxBudget) maxBudget.value = '50000';
      if (budgetSlider) budgetSlider.value = '50000';
      if (budgetDisplay) budgetDisplay.textContent = '৳50,000';

      // Trigger HTMX update or fallback submission
      if (window.htmx) {
        window.htmx.trigger(filterForm, 'change');
      } else {
        filterForm.submit();
      }
    }
  });

  // Budget slider and input two-way synchronization
  const budgetSlider = document.getElementById('budget-max-slider');
  const budgetOutput = document.getElementById('budget-max-display');
  const budgetInput = document.getElementById('budget-max-input');

  if (budgetSlider && budgetOutput) {
    budgetSlider.addEventListener('input', () => {
      const val = parseInt(budgetSlider.value, 10).toLocaleString();
      budgetOutput.textContent = `৳${val}`;
      if (budgetInput) {
        budgetInput.value = budgetSlider.value;
        budgetInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  }

  if (budgetInput && budgetSlider && budgetOutput) {
    budgetInput.addEventListener('input', () => {
      const num = parseInt(budgetInput.value, 10);
      if (!isNaN(num)) {
        budgetSlider.value = num;
        budgetOutput.textContent = `৳${num.toLocaleString()}`;
      }
    });
  }

  // Chip selection visual class synchronization
  document.addEventListener('change', (e) => {
    if (e.target.matches('#filter-form input[type="checkbox"], #filter-form input[type="radio"]')) {
      const form = document.getElementById('filter-form');
      if (form) {
        form.querySelectorAll('.bp-chip').forEach((chip) => {
          const input = chip.querySelector('input');
          if (input && input.checked) {
            chip.classList.add('bp-chip--selected');
          } else if (input) {
            chip.classList.remove('bp-chip--selected');
          }
        });
      }
    }

    // Keep hidden sort input inside filter-form synchronized with the sort dropdown
    if (e.target.matches('#sort-select')) {
      const hiddenSort = document.getElementById('filter-sort-input');
      if (hiddenSort) {
        hiddenSort.value = e.target.value;
      }
    }
  });
});
