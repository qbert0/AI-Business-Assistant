-- Chuyển sang sử dụng database đã được tạo bởi Docker
USE my_database;

-- ==========================================
-- TẠO BẢNG DỮ LIỆU (MariaDB Syntax)
-- ==========================================

-- 1. Bảng organization
CREATE TABLE organization (
    id UUID PRIMARY KEY DEFAULT UUID(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT UUID(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bảng organization_user (Trung gian)
CREATE TABLE organization_user (
    id UUID PRIMARY KEY DEFAULT UUID(),
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    role ENUM('admin', 'employee') DEFAULT 'employee',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_org UNIQUE (user_id, organization_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE
);

-- 4. Bảng file
CREATE TABLE file (
    id UUID PRIMARY KEY DEFAULT UUID(),
    organization_id UUID NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    status ENUM('processing', 'completed', 'failed') DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE
);

-- 5. Bảng upload_history
CREATE TABLE upload_history (
    id UUID PRIMARY KEY DEFAULT UUID(),
    organization_id UUID NOT NULL,
    file_id UUID NOT NULL,
    user_id UUID,
    action ENUM('upload_started', 'chunking', 'embedding_success', 'error') NOT NULL,
    log_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES file(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 6. Bảng chat_session
CREATE TABLE chat_session (
    id UUID PRIMARY KEY DEFAULT UUID(),
    organization_id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 7. Bảng chat_message
CREATE TABLE chat_message (
    id UUID PRIMARY KEY DEFAULT UUID(),
    session_id UUID NOT NULL,
    sender_type ENUM('user', 'ai') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_session(id) ON DELETE CASCADE
);

-- 8. Bảng notification
CREATE TABLE notification (
    id UUID PRIMARY KEY DEFAULT UUID(),
    user_id UUID NOT NULL,
    organization_id UUID,
    notification_type ENUM('system', 'organization') DEFAULT 'system',
    title VARCHAR(255) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE
);