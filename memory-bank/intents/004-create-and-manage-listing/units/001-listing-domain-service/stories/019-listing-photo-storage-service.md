---
id: 019-listing-photo-storage-service
unit: 001-listing-domain-service
intent: 004-create-and-manage-listing
status: ready
priority: must
created: '2026-10-31T07:28:00Z'
assigned_bolt: 007-listing-domain-service
implemented: false
---

# Story: 019-listing-photo-storage-service

## User Story

**As a** system security engineer
**I want** `ListingPhotoStorageService` to validate, inspect, and persist uploaded listing photos in public media storage
**So that** only safe, valid image files between 1 and 7 photos per listing are saved at upload resolution without arbitrary file injection risks

## Acceptance Criteria

- [ ] **Given** a batch of uploaded files, **When** total count is less than 1 or exceeds 7, **Then** validation fails with a clear count error message.
- [ ] **Given** an uploaded file, **When** size exceeds 5 MB, **Then** validation fails with file size error.
- [ ] **Given** an uploaded file, **When** MIME type or magic bytes do not match JPEG, PNG, or WebP, **Then** validation fails with unsupported image format error.
- [ ] **Given** valid photos, **When** calling `save_photo()`, **Then** the file is stored under `listings/photos/<listing_id>/<uuid>.<ext>` using standard Django storage and returns the relative storage path.
- [ ] **Given** a photo deleted during listing edit or listing deletion, **When** cleaning up, **Then** `delete_photo()` removes the physical file from disk.

## Technical Notes

- Uses Pillow (`PIL.Image.verify()`) to validate image payload structure without re-encoding or downscaling (stored at original upload resolution per FR-10).
- Unlike NID verification photos (which are stored in private PII storage `media_private/`), listing photos are public accommodation marketing assets stored in standard public media storage.

## Dependencies

### Requires
- `017-listing-and-photo-models`

### Enables
- `018-listing-service-and-active-cap`
- `021-listing-create-form-and-view`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Executable renamed with `.jpg` extension | Magic byte and Pillow verification catches the invalid image and rejects it. |
| Zero photos submitted with listing | Rejected; at least 1 photo is mandatory per FR-10. |
| 8 photos submitted | Rejected; maximum 7 photos permitted. |
