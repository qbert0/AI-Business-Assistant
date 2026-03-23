-- Kích hoạt extension để tự động tạo UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- ĐỊNH NGHĨA CÁC KIỂU ENUM
-- ==========================================
CREATE TYPE user_role_enum AS ENUM ('admin', 'employee');
CREATE TYPE file_status_enum AS ENUM ('processing', 'completed', 'failed');
CREATE TYPE upload_action_enum AS ENUM ('upload_started', 'chunking', 'embedding_success', 'error');
CREATE TYPE sender_type_enum AS ENUM ('user', 'ai');
CREATE TYPE notification_type_enum AS ENUM ('system', 'organization');

-- ==========================================
-- TẠO BẢNG DỮ LIỆU
-- ==========================================

-- 1. Bảng organization
CREATE TABLE organization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bảng organization_user (Trung gian)
CREATE TABLE organization_user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    role user_role_enum DEFAULT 'employee', -- Đã áp dụng ENUM
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_org UNIQUE (user_id, organization_id)
);

-- 4. Bảng file
CREATE TABLE file (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    file_name VARCHAR NOT NULL,
    file_url VARCHAR NOT NULL,
    status file_status_enum DEFAULT 'processing', -- Đã áp dụng ENUM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Bảng upload_history
CREATE TABLE upload_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES file(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action upload_action_enum NOT NULL, -- Đã áp dụng ENUM
    log_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Bảng chat_session
CREATE TABLE chat_session (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Bảng chat_message
CREATE TABLE chat_message (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_session(id) ON DELETE CASCADE,
    sender_type sender_type_enum NOT NULL, -- Đã áp dụng ENUM
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Bảng notification
CREATE TABLE notification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organization(id) ON DELETE CASCADE,
    notification_type notification_type_enum DEFAULT 'system', -- Đã áp dụng ENUM
    title VARCHAR NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);