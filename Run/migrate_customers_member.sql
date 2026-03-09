-- Add Member (online) columns to customers: username, email, password_hash, total_points, updated_at.
-- Run once if you get "Unknown column 'customers.username'" when using /member or seed_members.py.
--
-- แนะนำ (ไม่ต้องมีโปรแกรม mysql):  python Run/run_migrations.py  (มี migration นี้รวมอยู่แล้ว)
-- หรือใช้ mysql โดยตรง:  CMD/Bash  mysql ... < Run/migrate_customers_member.sql  /  PowerShell  .\Run\run_migrate_customers_member.ps1
--
-- (ถ้า error Duplicate column / Duplicate key แปลว่ามีคอลัมน์แล้ว ไม่ต้องรันซ้ำ)

ALTER TABLE `customers`
  ADD COLUMN `username` varchar(64) DEFAULT NULL AFTER `promptpay_number`,
  ADD COLUMN `email` varchar(255) DEFAULT NULL AFTER `username`,
  ADD COLUMN `password_hash` varchar(255) DEFAULT NULL AFTER `email`,
  ADD COLUMN `total_points` float NOT NULL DEFAULT 0 AFTER `password_hash`,
  ADD COLUMN `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp() AFTER `created_at`;

ALTER TABLE `customers` ADD UNIQUE KEY `ix_customers_username` (`username`);
ALTER TABLE `customers` ADD UNIQUE KEY `ix_customers_email` (`email`);
