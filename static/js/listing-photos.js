/**
 * Photo uploader, aspect ratio validator, and live preview sync for accommodation listings.
 * PRD §4.4, Mockup 05-listing-create.
 */
(function () {
  'use strict';

  function initListingAuthoring() {
    var fileInput = document.getElementById('listing-photo-input');
    var dropZone = document.getElementById('photo-drop-zone');
    var thumbsGrid = document.getElementById('photos-thumbs-grid');
    var countNotice = document.getElementById('photos-count-notice');
    var ratioAdvisory = document.getElementById('photos-ratio-advisory');
    var form = document.getElementById('listing-form');

    // Live preview elements
    var previewPrice = document.getElementById('preview-price');
    var previewUnit = document.getElementById('preview-unit');
    var previewKind = document.getElementById('preview-kind');
    var previewAreas = document.getElementById('preview-areas');
    var previewBody = document.getElementById('preview-body');
    var previewImage = document.getElementById('preview-image');

    // Form inputs
    var kindSelect = document.getElementById('id_kind');
    var kindRadios = document.querySelectorAll('input[name="kind"]');
    var rentInput = document.getElementById('id_rent_bdt');
    var unitSelect = document.getElementById('id_rent_unit');
    var bodyInput = document.getElementById('id_body');
    var areaInputs = document.querySelectorAll('input[name="area"]');

    var selectedFiles = [];
    var MAX_PHOTOS = 7;
    var MAX_SIZE = 5 * 1024 * 1024; // 5 MB

    function getSelectedKind() {
      if (kindRadios && kindRadios.length > 0) {
        for (var i = 0; i < kindRadios.length; i++) {
          if (kindRadios[i].checked) return kindRadios[i].value;
        }
      }
      return kindSelect ? kindSelect.value : 'seat';
    }

    // Parity sync between kind and rent_unit
    function syncKindAndUnit(kindVal) {
      if (!unitSelect) return;
      if (kindVal === 'seat') {
        unitSelect.value = 'per_seat';
      } else if (kindVal === 'room') {
        unitSelect.value = 'per_room';
      }
      updatePreview();
    }

    if (kindRadios.length > 0) {
      kindRadios.forEach(function (radio) {
        radio.addEventListener('change', function () {
          syncKindAndUnit(radio.value);
        });
      });
    }

    if (kindSelect) {
      kindSelect.addEventListener('change', function () {
        syncKindAndUnit(kindSelect.value);
      });
    }

    if (unitSelect) unitSelect.addEventListener('change', updatePreview);
    if (rentInput) rentInput.addEventListener('input', updatePreview);
    if (bodyInput) bodyInput.addEventListener('input', updatePreview);
    areaInputs.forEach(function (chk) {
      chk.addEventListener('change', updatePreview);
    });

    function updatePreview() {
      if (previewPrice && rentInput) {
        var rentVal = parseInt(rentInput.value, 10);
        previewPrice.textContent = isNaN(rentVal) ? '0' : rentVal.toLocaleString();
      }

      if (previewUnit && unitSelect) {
        var opt = unitSelect.options[unitSelect.selectedIndex];
        previewUnit.textContent = opt ? opt.text : '/month';
      }

      if (previewKind) {
        var currentKind = getSelectedKind();
        previewKind.textContent = currentKind === 'seat' ? 'Seat' : 'Room';
      }

      if (previewAreas) {
        var checkedAreas = [];
        areaInputs.forEach(function (chk) {
          if (chk.checked) checkedAreas.push(chk.value);
        });
        previewAreas.textContent = checkedAreas.length > 0 ? checkedAreas.join(', ') : 'Dhaka';
      }

      if (previewBody && bodyInput) {
        var text = bodyInput.value.trim();
        previewBody.textContent = text ? text : 'Comfortable accommodation in a secure neighborhood with verified housemates.';
      }
    }

    // Dropzone interactions
    if (dropZone && fileInput) {
      dropZone.addEventListener('click', function () {
        fileInput.click();
      });

      ['dragenter', 'dragover'].forEach(function (eventName) {
        dropZone.addEventListener(eventName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          dropZone.classList.add('border-primary', 'bg-light');
        });
      });

      ['dragleave', 'drop'].forEach(function (eventName) {
        dropZone.addEventListener(eventName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          dropZone.classList.remove('border-primary', 'bg-light');
        });
      });

      dropZone.addEventListener('drop', function (e) {
        if (e.dataTransfer && e.dataTransfer.files) {
          handleNewFiles(e.dataTransfer.files);
        }
      });

      fileInput.addEventListener('change', function () {
        if (fileInput.files) {
          handleNewFiles(fileInput.files);
        }
      });
    }

    function handleNewFiles(fileList) {
      var nonLandscapeCount = 0;
      var fileArray = Array.from(fileList);

      fileArray.forEach(function (file) {
        if (selectedFiles.length >= MAX_PHOTOS) return;

        // Size check
        if (file.size > MAX_SIZE) {
          alert('Photo "' + file.name + '" exceeds the 5MB size limit.');
          return;
        }

        // Duplicate check
        var exists = selectedFiles.some(function (f) {
          return f.name === file.name && f.size === file.size;
        });
        if (exists) return;

        selectedFiles.push(file);

        // Aspect ratio inspection
        var img = new Image();
        img.src = URL.createObjectURL(file);
        img.onload = function () {
          if (img.width < img.height) {
            nonLandscapeCount += 1;
            if (ratioAdvisory) {
              ratioAdvisory.classList.remove('d-none');
            }
          }
        };
      });

      syncFileInput();
      renderThumbs();
    }

    function syncFileInput() {
      if (!fileInput) return;
      var dataTransfer = new DataTransfer();
      selectedFiles.forEach(function (f) {
        dataTransfer.items.add(f);
      });
      fileInput.files = dataTransfer.files;

      if (countNotice) {
        countNotice.textContent = selectedFiles.length + ' / ' + MAX_PHOTOS + ' photos selected';
      }
    }

    function renderThumbs() {
      if (!thumbsGrid) return;
      thumbsGrid.innerHTML = '';

      if (selectedFiles.length === 0) {
        if (previewImage) {
          previewImage.style.backgroundImage = '';
        }
        return;
      }

      selectedFiles.forEach(function (file, idx) {
        var col = document.createElement('div');
        col.className = 'col-3 position-relative';

        var card = document.createElement('div');
        card.className = 'bp-thumb w-100 overflow-hidden';
        card.style.height = '100px';
        card.style.backgroundSize = 'cover';
        card.style.backgroundPosition = 'center';
        card.style.backgroundImage = 'url(' + URL.createObjectURL(file) + ')';

        // Primary badge on first photo
        if (idx === 0) {
          var badge = document.createElement('span');
          badge.className = 'badge bg-primary position-absolute top-0 start-0 m-1';
          badge.style.fontSize = '10px';
          badge.textContent = 'Primary';
          card.appendChild(badge);

          if (previewImage) {
            previewImage.style.backgroundImage = 'url(' + URL.createObjectURL(file) + ')';
            previewImage.style.backgroundSize = 'cover';
            previewImage.style.backgroundPosition = 'center';
          }
        }

        // Remove button
        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'bp-thumb__remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.title = 'Remove photo';
        removeBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          selectedFiles.splice(idx, 1);
          syncFileInput();
          renderThumbs();
        });

        card.appendChild(removeBtn);
        col.appendChild(card);
        thumbsGrid.appendChild(col);
      });
    }

    // Initialize state
    updatePreview();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initListingAuthoring);
  } else {
    initListingAuthoring();
  }
})();
