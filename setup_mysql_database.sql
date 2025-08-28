
-- Script para criar banco de dados no XAMPP/MySQL
-- Execute este script no phpMyAdmin ou MySQL Workbench

-- 1. Criar banco de dados
CREATE DATABASE IF NOT EXISTS chat_empenhos 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 2. Usar o banco
USE chat_empenhos;

-- 3. Criar usuário específico (opcional)
-- CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'chat_password';
-- GRANT ALL PRIVILEGES ON chat_empenhos.* TO 'chat_user'@'localhost';
-- FLUSH PRIVILEGES;

-- 4. Tabelas serão criadas automaticamente pelo SQLAlchemy

-- Verificar se foi criado
SHOW DATABASES LIKE 'chat_empenhos';
