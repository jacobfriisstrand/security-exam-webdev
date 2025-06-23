-- Drop Tables in Correct Order
DROP TABLE IF EXISTS item_images;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users_roles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

-- Create Users Table
CREATE TABLE users (
    user_pk CHAR(36),
    user_name VARCHAR(20) NOT NULL,
    user_last_name VARCHAR(20) NOT NULL,
    user_email VARCHAR(100) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    user_image VARCHAR(50),
    user_created_at INTEGER UNSIGNED,
    user_deleted_at INTEGER UNSIGNED,
    user_blocked_at INTEGER UNSIGNED,
    user_updated_at INTEGER UNSIGNED,
    user_verified_at INTEGER UNSIGNED,
    user_verification_key CHAR(36),
    PRIMARY KEY(user_pk)
);

-- Create Items Table
CREATE TABLE items (
    item_pk CHAR(36),
    item_user_fk CHAR(36),
    item_title VARCHAR(50) NOT NULL,
    item_price DECIMAL(5,2) NOT NULL,
    item_description TEXT,
    item_created_at INTEGER UNSIGNED,
    item_updated_at INTEGER UNSIGNED,
    item_deleted_at INTEGER UNSIGNED,
    item_blocked_at INTEGER UNSIGNED,
    PRIMARY KEY(item_pk),
    FOREIGN KEY (item_user_fk) REFERENCES users(user_pk) ON DELETE CASCADE ON UPDATE RESTRICT
);

-- Create Images Table
CREATE TABLE item_images (
    item_image_pk CHAR(36),
    item_fk CHAR(36) NOT NULL,
    item_image VARCHAR(255) NOT NULL,
    item_image_created_at INTEGER UNSIGNED,
    item_image_updated_at INTEGER UNSIGNED,
    PRIMARY KEY (item_image_pk),
    FOREIGN KEY (item_fk) REFERENCES items(item_pk) ON DELETE CASCADE ON UPDATE RESTRICT
);

-- Create Roles Table
CREATE TABLE roles (
    role_pk CHAR(36),
    role_name VARCHAR(10) NOT NULL UNIQUE,
    PRIMARY KEY(role_pk)
);

-- Create Users_Roles Table
CREATE TABLE users_roles (
    user_role_user_fk CHAR(36),
    user_role_role_fk CHAR(36),
    PRIMARY KEY(user_role_user_fk, user_role_role_fk),
    FOREIGN KEY (user_role_user_fk) REFERENCES users(user_pk) ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY (user_role_role_fk) REFERENCES roles(role_pk) ON DELETE CASCADE ON UPDATE RESTRICT
);
