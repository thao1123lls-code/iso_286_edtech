-- =============================================================================
-- CƠ SỞ DỮ LIỆU QUAN HỆ BẢNG TRA ISO 286 (MySQL / PostgreSQL / SQLite)
-- =============================================================================
-- Script này mô tả đầy đủ DDL cho 4 bảng tra ISO 286-1:2010.
-- Mặc định ứng dụng dùng SQLAlchemy tự tạo bảng + seed (app/db/seed.py).
-- Khi triển khai MySQL/PostgreSQL thật, chỉ cần chạy script này trước
-- rồi đặt biến môi trường DATABASE_URL, ví dụ:
--   MySQL:      mysql+pymysql://user:pass@localhost:3306/iso286
--   PostgreSQL: postgresql+psycopg2://user:pass@localhost:5432/iso286
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. KHOẢNG KÍCH THƯỚC DANH NGHĨA
--    Cận dưới min_mm (loại trừ) - Cận trên max_mm (bao gồm)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS iso_size_ranges (
    id      INT          NOT NULL AUTO_INCREMENT,
    min_mm  DECIMAL(10,3) NOT NULL,
    max_mm  DECIMAL(10,3) NOT NULL,
    PRIMARY KEY (id)
);

-- -----------------------------------------------------------------------------
-- 2. DUNG SAI TIÊU CHUẨN IT (IT01 -> IT18)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS iso_it_grades (
    id       INT          NOT NULL AUTO_INCREMENT,
    grade    VARCHAR(4)   NOT NULL,           -- IT01, IT0, IT1 ... IT18
    range_id INT          NOT NULL,
    value_um DECIMAL(10,3) NOT NULL,          -- dung sai (μm)
    PRIMARY KEY (id),
    CONSTRAINT fk_it_range FOREIGN KEY (range_id) REFERENCES iso_size_ranges (id),
    CONSTRAINT uq_it_grade_range UNIQUE (grade, range_id)
);

-- -----------------------------------------------------------------------------
-- 3. SAI LỆCH CƠ BẢN CỦA TRỤC & LỖ
--    part_type: 'shaft' (es/ei) | 'hole' (ES/EI)
--    letter   : a..zc (trục) | A..ZC (lỗ)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS iso_deviations (
    id             INT          NOT NULL AUTO_INCREMENT,
    part_type      VARCHAR(8)   NOT NULL,
    letter         VARCHAR(2)   NOT NULL,
    deviation_kind VARCHAR(4)   NOT NULL,     -- es/ei (shaft), ES/EI (hole)
    range_id       INT          NOT NULL,
    value_um       DECIMAL(10,3) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_dev_range FOREIGN KEY (range_id) REFERENCES iso_size_ranges (id),
    CONSTRAINT uq_dev_plr UNIQUE (part_type, letter, range_id)
);

-- -----------------------------------------------------------------------------
-- 4. THƯ VIỆN KIỂU LẮP KHUYẾN CÁO CÔNG NGHIỆP
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS iso_fit_library (
    id          INT           NOT NULL AUTO_INCREMENT,
    symbol      VARCHAR(16)   NOT NULL,        -- VD: H7/g6
    category    VARCHAR(16)   NOT NULL,        -- clearance | transition | interference
    fit_type    VARCHAR(64)   NOT NULL,
    application VARCHAR(255)  NOT NULL,
    feature     VARCHAR(255)  NOT NULL,
    PRIMARY KEY (id)
);

-- =============================================================================
-- DỮ LIỆU MẪU (13 khoảng kích thước 0 - 500 mm)
-- =============================================================================
INSERT INTO iso_size_ranges (id, min_mm, max_mm) VALUES
    (1,  0,    3), (2, 3,   6),  (3, 6,  10), (4, 10, 18),
    (5,  18,   30), (6, 30, 50), (7, 50, 80), (8, 80, 120),
    (9,  120, 180), (10, 180, 250), (11, 250, 315), (12, 315, 400),
    (13, 400, 500);

-- Ghi chú: Toàn bộ dữ liệu IT01-IT18 (273 dòng) và sai lệch Trục/Lỗ
-- (26 ký hiệu x 13 khoảng) được sinh tự động bởi app/db/seed.py khi khởi động
-- (seed_all / seed_if_empty). Chạy:
--   python -m app.db.seed
-- để nạp dữ liệu vào CSDL đang cấu hình.

