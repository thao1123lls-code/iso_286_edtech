"""Kiểm thử JWT Login + RBAC cho hệ thống ISO 286 EdTech.

Test các kịch bản:
1. POST /api/login với giangvien/123   -> thành công, có token + role lecturer
2. POST /api/login với sinhvien/123    -> thành công, có token + role student
3. POST /api/login sai mật khẩu        -> 401
4. GET  /api/iso/tables không token    -> 401 (đã bảo vệ)
5. GET  /api/iso/tables với token sinhvien -> 200 (student được tra cứu)
6. POST /api/export/docx với token student -> 403 (chặn student)
7. POST /api/export/docx với token lecturer -> 200 (lecturer xuất file)
"""
import os

# Dùng SQLite riêng cho test auth (không đụng DB chính)
_DB_PATH = "./iso286_auth_test.db"
if os.path.exists(_DB_PATH):
    os.remove(_DB_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

from fastapi.testclient import TestClient

from main import app

EXPORT_PAYLOAD = {
    "stats": {"total": 1, "batchCode": "AUTHTEST01"},
    "activeTasks": [
        {"id": "req_ES", "name": "1. Tra Sai lệch giới hạn trên của Lỗ (ES)", "points": 1.0},
        {"id": "req_ei", "name": "2. Tra Sai lệch giới hạn dưới của Trục (ei)", "points": 1.0},
    ],
    "questions": [
        {
            "student": {"mssv": "2021001", "name": "Nguyễn Văn A", "className": "21CK1", "classCode": "ME2026"},
            "diffLabel": "Trung bình",
            "examCode": "ME2026-2021001",
            "D": 40,
            "hole": {"sym": "H", "it": 7, "ES": 25, "EI": 0, "T": 25,
                     "Dmax": 40.025, "Dmin": 40.0},
            "shaft": {"sym": "g", "it": 6, "es": -9, "ei": -25, "T": 16,
                      "dmax": 39.991, "dmin": 39.975},
            "fit": {"type": "Lắp lỏng (Có độ hở)", "Smax": 50, "Smin": 9,
                    "Nmax": -9, "Nmin": -50, "TN": 41},
        }
    ],
}


def _login(client, username, password):
    r = client.post("/api/login", json={"username": username, "password": password})
    return r


def main():
    with TestClient(app) as client:  # kích hoạt lifespan
        # 1. Login giảng viên
        r = _login(client, "giangvien", "123")
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
        data = r.json()
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "lecturer"
        assert data["access_token"]
        lecturer_token = data["access_token"]
        print("[1] POST /api/login giangvien/123: OK -> role=lecturer")

        # 2. Login sinh viên
        r = _login(client, "sinhvien", "123")
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
        data = r.json()
        assert data["user"]["role"] == "student"
        student_token = data["access_token"]
        print("[2] POST /api/login sinhvien/123: OK -> role=student")

        # 3. Sai mật khẩu -> 401
        r = _login(client, "giangvien", "sai")
        assert r.status_code == 401, f"status={r.status_code}"
        print("[3] POST /api/login sai mật khẩu: OK -> 401")

        # 4. Truy cập bảng ISO không có token -> 401
        r = client.get("/api/iso/tables")
        assert r.status_code == 401, f"status={r.status_code}"
        print("[4] GET /api/iso/tables không token: OK -> 401")

        # 5. Student truy cập bảng ISO -> 200
        r = client.get(
            "/api/iso/tables",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
        assert len(r.json()["sizeRanges"]) == 13
        print("[5] GET /api/iso/tables (token sinhvien): OK -> 200")

        # 6. Student xuất docx -> 403
        r = client.post(
            "/api/export/docx",
            json=EXPORT_PAYLOAD,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert r.status_code == 403, f"status={r.status_code} body={r.text[:200]}"
        print("[6] POST /api/export/docx (token sinhvien): OK -> 403 (chặn)")

        # 7. Lecturer xuất docx -> 200
        r = client.post(
            "/api/export/docx",
            json=EXPORT_PAYLOAD,
            headers={"Authorization": f"Bearer {lecturer_token}"},
        )
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
        assert len(r.content) > 1000
        print(f"[7] POST /api/export/docx (token giangvien): OK -> 200 ({len(r.content)} bytes)")

        # 8. Lecturer xuất pdf -> 200
        r = client.post(
            "/api/export/pdf",
            json=EXPORT_PAYLOAD,
            headers={"Authorization": f"Bearer {lecturer_token}"},
        )
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
        assert r.content[:4] == b"%PDF"
        print(f"[8] POST /api/export/pdf (token giangvien): OK -> 200 ({len(r.content)} bytes)")

    print("\n=== AUTH + RBAC TEST PASSED ===")


if __name__ == "__main__":
    main()

