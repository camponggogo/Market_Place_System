-- Add is_admin to users (for Store POS login / admin role).
-- Run once if you get 500 on POST /api/auth/login (e.g. Unknown column 'users.is_admin').
-- Example: mysql -u root -p market_place_system < Run/migrate_add_users_is_admin.sql

ALTER TABLE `users`
  ADD COLUMN `is_admin` tinyint(1) NOT NULL DEFAULT 0 AFTER `name`;
