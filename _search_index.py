# Helper: search for key markers in index.html
import io

path = r"d:/ISO 286 EdTech/iso_286_edtech/index.html"
patterns = ["MOCK_USERS", "StudentPortal", "TeacherPortal", "2110481",
            "Danh sách sinh viên", "Nhập danh sách", "giangvien",
            "studentList", "login", "Đăng nhập", "sinhvien"]

with io.open(path, encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, start=1):
    for p in patterns:
        if p.lower() in line.lower():
            print(f"{i}: {line.rstrip()}") if len(line.strip()) < 150 else print(f"{i}: {line.strip()[:150]}...")
            break
