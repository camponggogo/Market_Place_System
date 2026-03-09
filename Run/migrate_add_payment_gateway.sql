-- Add payment_gateway to promptpay_back_transactions (for Stripe/Omise/SCB report).
-- Run once on existing DB if you get: Unknown column 'promptpay_back_transactions.payment_gateway'
-- Example: mysql -u root -p market_place_system < Run/migrate_add_payment_gateway.sql

ALTER TABLE `promptpay_back_transactions`
  ADD COLUMN `payment_gateway` varchar(30) DEFAULT NULL AFTER `status`,
  ADD KEY `ix_promptpay_back_transactions_payment_gateway` (`payment_gateway`);
