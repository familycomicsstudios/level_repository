# Security audit findings

## 1) Brute-force risk on login endpoint
- **Severity:** High
- **Location:** `/tmp/workspace/familycomicsstudios/level_repository/levels/views.py`
- **Issue:** Login accepted unlimited repeated attempts.
- **Fix implemented:** Added cache-backed throttling for login attempts (per IP and per username) with HTTP `429` responses when limits are exceeded.

## 2) CSRF-prone state-changing GET endpoint (comment deletion)
- **Severity:** Medium
- **Location:** `/tmp/workspace/familycomicsstudios/level_repository/levels/views.py`, `/tmp/workspace/familycomicsstudios/level_repository/levels/templates/levels/level_detail.html`
- **Issue:** Comments could be deleted using a GET request.
- **Fix implemented:** Restricted comment deletion to POST-only and replaced delete links with CSRF-protected forms.

## 3) Logout CSRF via GET
- **Severity:** Low
- **Location:** `/tmp/workspace/familycomicsstudios/level_repository/levels/views.py`, `/tmp/workspace/familycomicsstudios/level_repository/levels/templates/base.html`
- **Issue:** Logout could be triggered by GET, allowing forced logout.
- **Fix implemented:** Restricted logout to POST-only and switched UI logout action to a CSRF-protected form.

## 4) API rate-limit bypass risk through untrusted forwarded headers
- **Severity:** Medium
- **Location:** `/tmp/workspace/familycomicsstudios/level_repository/levels/views.py`, `/tmp/workspace/familycomicsstudios/level_repository/level_repository/settings.py`
- **Issue:** `X-Forwarded-For` was trusted unconditionally for rate-limit identity.
- **Fix implemented:** Forwarded header trust is now opt-in (`TRUST_X_FORWARDED_FOR`), defaulting to `False`.
