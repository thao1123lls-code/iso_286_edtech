# TODO - Fix HTTP 404 errors (Không tải được lịch sử / danh sách)

## Root cause
Frontend `index.html` has 6 `fetch()` calls that use **single quotes** around
`${API_BASE}` instead of **backticks** (template literals). This means
`${API_BASE}` is never interpolated; the browser requests a literal
`/${API_BASE}/api/...` path → server returns **HTTP 404**.

## Affected lines (index.html)
- [x] Line 299  — `GET /api/iso/tables`
- [x] Line 338  — `POST /api/history` (save history)
- [x] Line 1901 — `GET /api/history` (load history) → "Không tải được lịch sử!"
- [x] Line 2997 — `GET /api/students` (student list) → "Không tải được danh sách!"
- [x] Line 3041 — `POST /api/teachers/upload-students`
- [x] Line 3266 — `POST /api/login`

## Steps
1. Replace single-quoted `'${API_BASE}/api/...'` with backtick template literals
   `` `${API_BASE}/api/...` `` in all 6 fetch calls. ✅ **DONE**
   (Verified: all 11 fetch() calls now use backticks, 0 single-quoted occurrences remain.)
2. Reload frontend and verify history + student list load without 404.

## Verification (2026)
Ran `_verify_all.py` → **ALL CHECKS PASSED**:
- `index.html`: 11/11 fetch() calls use backtick template literals with `${API_BASE}`;
  0 single-quoted `'${API_BASE}'` remain → no more HTTPS 404 for history/students.
- DNTU exam header integration complete:
  - `pdf_service.py` imports & calls `build_exam_header(ma_de, batch)`.
  - `docx_service.py` imports & calls `build_docx_header(doc, ma_de=..., ma_lo_dot=batch)`.
  - Both `pdf_exam_header.py` and `docx_exam_header.py` modules exist.

