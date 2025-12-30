-- 1. DANH MỤC & THƯƠNG HIỆU
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    image_url TEXT
);

CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    logo_url TEXT
);

-- 2. NGƯỜI DÙNG & ĐỊA CHỈ
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    avatar TEXT,
    phone VARCHAR(20),
    tier VARCHAR(20) DEFAULT 'Bạc'
);

CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    receiver_name VARCHAR(255),
    receiver_phone VARCHAR(20),
    province VARCHAR(100), -- Tỉnh/Thành phố
    district VARCHAR(100), -- Quận/Huyện
    ward VARCHAR(100),     -- Phường/Xã
    street_details TEXT,   -- Số nhà, tên đường
    type VARCHAR(20),      -- Nhà riêng / Văn phòng
    is_default BOOLEAN DEFAULT FALSE
);

-- 3. SẢN PHẨM & BIẾN THỂ
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(15, 2) NOT NULL,
    original_price DECIMAL(15, 2),
    discount_percent INT DEFAULT 0,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    brand_id INT REFERENCES brands(id) ON DELETE SET NULL,
    rating_avg DECIMAL(2, 1) DEFAULT 0,
    reviews_count INT DEFAULT 0,
    sold_count INT DEFAULT 0,
    main_image TEXT,
    is_new BOOLEAN DEFAULT FALSE
);

CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL
);

CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    variant_type VARCHAR(20), -- 'size' hoặc 'color'
    variant_value VARCHAR(50)
);

-- 4. ĐƠN HÀNG & GIAO DỊCH
CREATE TABLE orders (
    id VARCHAR(50) PRIMARY KEY, -- ORD-2024-XXX
    user_id INT REFERENCES users(id),
    total_amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'Chờ xử lý', 'Đang vận chuyển', 'Hoàn thành', 'Đã hủy'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    price_at_purchase DECIMAL(15, 2) NOT NULL,
    selected_size VARCHAR(20),
    selected_color VARCHAR(50)
);

-- 5. TƯƠNG TÁC & THÔNG BÁO
CREATE TABLE favorites (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, product_id)
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    type VARCHAR(20), -- 'order', 'promo', 'system'
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);