/**
 * ============================================================================
 *  API BASE URL — CẤU HÌNH TRUNG TÂM (Production-ready)
 * ============================================================================
 *  File cấu hình chung cho toàn bộ lệnh gọi API của Frontend.
 *  Mọi component đều dùng hằng số `window.API_BASE` (hoặc `API_BASE` global)
 *  thay vì viết cứng đường dẫn http://localhost:8000.
 *
 *  THỨ TỰ ƯU TIÊN (cao → thấp):
 *  1. `window.__API_URL__`  — Biến môi trường được inject lúc deploy/branch
 *                            (chuẩn Production). Vercel/Netlify thay chuỗi
 *                            `window.__API_URL__ = "..."` bằng giá trị thật
 *                            từ Environment Variables (xem bước Deploy).
 *  2. `window.location.origin`
 *                            — Mặc định khi frontend & backend cùng host
 *                            (VD: Render trả trang + API cùng domain).
 *                            Tránh tuyệt đối lỗi CORS.
 *  3. `http://localhost:8000` — Fallback khi mở `index.html` trực tiếp bằng
 *                            `file://` để test local (backend FastAPI chạy máy).
 * ============================================================================
 */
(function () {
  'use strict';

  // 1) Ưu tiên biến môi trường (được inject khi build/deploy Production).
  //    Vì dự án là HTML tĩnh (React qua CDN, không có Vite/Next.js build tool),
  //    ta dùng `window.__API_URL__` làm chuẩn thay vì import.meta.env/process.env.
  //    Nerf-source cũng đọc `window.API_URL` nếu ai inject theo kiểu VITE_API_URL.
  var configuredUrl =
    (typeof window !== 'undefined' && (window.__API_URL__ || window.API_URL)) || '';

  // 2) Mặc định: dùng đúng origin của trang hiện tại (cùng host, không lệch CORS).
  var originUrl = '';
  if (
    typeof window !== 'undefined' &&
    window.location &&
    window.location.origin &&
    window.location.protocol !== 'file:'
  ) {
    originUrl = window.location.origin;
  }

  // 3) Fallback cuối: backend FastAPI chạy local (test máy).
  var fallbackUrl = 'http://localhost:8000';

  // Bỏ dấu '/' thừa ở cuối nếu có (tránh lỗi `//api/...`).
  var clean = function (url) {
    return url ? url.replace(/\/+$/, '') : url;
  };

  var API_BASE = clean(configuredUrl) || clean(originUrl) || clean(fallbackUrl);

  // Gán ra global để mọi chỗ trong index.html dùng chung.
  window.API_BASE = API_BASE;
  // Đồng thời gán `window.API_BASE` bảo toàn cú pháp `${API_BASE}` trong JSX.
  if (typeof API_BASE === 'string') {
    // (window.API_BASE đã set ở trên; không cần re-declare)
  }

  // Tiện ích: gộp header Authorization (JWT) vào mọi request nếu có token.
  var getToken = function () {
    try {
      return (
        window.localStorage && window.localStorage.getItem('iso286_token')
      );
    } catch (e) {
      return null;
    }
  };

  window.getAuthHeaders = function (extra) {
    var token = getToken();
    var headers = extra || {};
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    return headers;
  };

  // Log hữu ích khi debug.
  if (console && console.info) {
    console.info('[API] API_BASE =', API_BASE);
  }
})();
