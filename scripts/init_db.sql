/*
Navicat MySQL Data Transfer

Source Server         : localhost
Source Server Version : 120002
Source Host           : localhost:3306
Source Database       : maket_system

Target Server Type    : MYSQL
Target Server Version : 120002
File Encoding         : 65001

Date: 2026-02-01 14:57:08
*/
DROP DATABASE IF EXISTS maket_place_system;
CREATE DATABASE maket_place_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE maket_place_system;

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for audit_logs
-- ----------------------------
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `table_name` varchar(100) NOT NULL,
  `record_id` int(11) DEFAULT NULL,
  `old_values` text DEFAULT NULL,
  `new_values` text DEFAULT NULL,
  `ip_address` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_audit_logs_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of audit_logs
-- ----------------------------

-- ----------------------------
-- Table structure for counter_transactions
-- ----------------------------
DROP TABLE IF EXISTS `counter_transactions`;
CREATE TABLE `counter_transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `foodcourt_id` varchar(50) NOT NULL,
  `counter_id` int(11) NOT NULL,
  `counter_user_id` int(11) NOT NULL,
  `amount` float NOT NULL,
  `payment_method` enum('CASH','CREDIT_CARD_VISA','CREDIT_CARD_MASTERCARD','CREDIT_CARD_AMEX','CREDIT_CARD_JCB','CREDIT_CARD_UNIONPAY','TRUE_WALLET','PROMPTPAY','LINE_PAY','RABBIT_LINE_PAY','SHOPEE_PAY','GRAB_PAY','APPLE_PAY','GOOGLE_PAY','SAMSUNG_PAY','ALIPAY','WECHAT_PAY','PAYPAL','AMAZON_PAY','VENMO','ZELLE','CASH_APP','BANK_TRANSFER','WIRE_TRANSFER','CRYPTO_BTC','CRYPTO_ETH','CRYPTO_XRP','CRYPTO_BITKUB','CRYPTO_BINANCE','CRYPTO_SOLANA','CRYPTO_USDT','CRYPTO_USDC','CRYPTO_CUSTOM','POINTS_THE1','POINTS_BLUECARD','POINTS_CREDIT_CARD','POINTS_AIRLINE','POINTS_HOTEL','POINTS_CUSTOM','VOUCHER','GIFT_CARD','COUPON','BNPL_ATOME','BNPL_SPLIT','BNPL_GRAB_PAYLATER','BNPL_AFFIRM','BNPL_KLARNA','BNPL_AFTERPAY','CUSTOM') NOT NULL,
  `payment_details` text DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `foodcourt_id` (`foodcourt_id`),
  KEY `ix_counter_transactions_id` (`id`),
  CONSTRAINT `counter_transactions_ibfk_1` FOREIGN KEY (`foodcourt_id`) REFERENCES `foodcourt_ids` (`foodcourt_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of counter_transactions
-- ----------------------------

-- ----------------------------
-- Table structure for crypto_transactions
-- ----------------------------
DROP TABLE IF EXISTS `crypto_transactions`;
CREATE TABLE `crypto_transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `transaction_id` int(11) NOT NULL,
  `store_id` int(11) NOT NULL,
  `tx_hash` varchar(255) NOT NULL,
  `blockchain_address` varchar(255) NOT NULL,
  `amount_crypto` float NOT NULL,
  `crypto_type` varchar(50) NOT NULL,
  `status` enum('PENDING','CONFIRMED','FAILED') DEFAULT NULL,
  `explorer_url` text DEFAULT NULL,
  `last_checked` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transaction_id` (`transaction_id`),
  UNIQUE KEY `ix_crypto_transactions_tx_hash` (`tx_hash`),
  KEY `store_id` (`store_id`),
  KEY `ix_crypto_transactions_id` (`id`),
  CONSTRAINT `crypto_transactions_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`),
  CONSTRAINT `crypto_transactions_ibfk_2` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of crypto_transactions
-- ----------------------------

-- ----------------------------
-- Table structure for customers
-- ----------------------------
DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `phone` varchar(20) NOT NULL,
  `line_user_id` varchar(100) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `promptpay_number` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_customers_phone` (`phone`),
  UNIQUE KEY `ix_customers_line_user_id` (`line_user_id`),
  KEY `ix_customers_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of customers
-- ----------------------------
INSERT INTO `customers` VALUES ('1', '0812345678', null, 'ลูกค้าตัวอย่าง', '0812345678', '2026-02-01 14:48:57', null);

-- ----------------------------
-- Table structure for customer_balances
-- ----------------------------
DROP TABLE IF EXISTS `customer_balances`;
CREATE TABLE `customer_balances` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `balance` float NOT NULL,
  `last_reset_date` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `customer_id` (`customer_id`),
  KEY `ix_customer_balances_id` (`id`),
  CONSTRAINT `customer_balances_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of customer_balances
-- ----------------------------
INSERT INTO `customer_balances` VALUES ('1', '1', '100', null, '2026-02-01 14:48:57', null);

-- ----------------------------
-- Table structure for events
-- ----------------------------
DROP TABLE IF EXISTS `events`;
CREATE TABLE `events` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `profile_id` int(11) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `location` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `profile_id` (`profile_id`),
  KEY `ix_events_id` (`id`),
  CONSTRAINT `events_ibfk_1` FOREIGN KEY (`profile_id`) REFERENCES `profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of events
-- ----------------------------

-- ----------------------------
-- Table structure for foodcourt_ids
-- ----------------------------
DROP TABLE IF EXISTS `foodcourt_ids`;
CREATE TABLE `foodcourt_ids` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `foodcourt_id` varchar(50) NOT NULL,
  `customer_id` int(11) DEFAULT NULL,
  `initial_amount` float NOT NULL,
  `current_balance` float NOT NULL,
  `payment_method` enum('CASH','CREDIT_CARD_VISA','CREDIT_CARD_MASTERCARD','CREDIT_CARD_AMEX','CREDIT_CARD_JCB','CREDIT_CARD_UNIONPAY','TRUE_WALLET','PROMPTPAY','LINE_PAY','RABBIT_LINE_PAY','SHOPEE_PAY','GRAB_PAY','APPLE_PAY','GOOGLE_PAY','SAMSUNG_PAY','ALIPAY','WECHAT_PAY','PAYPAL','AMAZON_PAY','VENMO','ZELLE','CASH_APP','BANK_TRANSFER','WIRE_TRANSFER','CRYPTO_BTC','CRYPTO_ETH','CRYPTO_XRP','CRYPTO_BITKUB','CRYPTO_BINANCE','CRYPTO_SOLANA','CRYPTO_USDT','CRYPTO_USDC','CRYPTO_CUSTOM','POINTS_THE1','POINTS_BLUECARD','POINTS_CREDIT_CARD','POINTS_AIRLINE','POINTS_HOTEL','POINTS_CUSTOM','VOUCHER','GIFT_CARD','COUPON','BNPL_ATOME','BNPL_SPLIT','BNPL_GRAB_PAYLATER','BNPL_AFFIRM','BNPL_KLARNA','BNPL_AFTERPAY','CUSTOM') NOT NULL,
  `payment_details` text DEFAULT NULL,
  `counter_id` int(11) DEFAULT NULL,
  `counter_user_id` int(11) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_foodcourt_ids_foodcourt_id` (`foodcourt_id`),
  KEY `customer_id` (`customer_id`),
  KEY `ix_foodcourt_ids_id` (`id`),
  CONSTRAINT `foodcourt_ids_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of foodcourt_ids
-- ----------------------------

-- ----------------------------
-- Table structure for menus
-- ----------------------------
DROP TABLE IF EXISTS `menus`;
CREATE TABLE `menus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `store_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `unit_price` float NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_menus_store_id` (`store_id`),
  KEY `ix_menus_id` (`id`),
  CONSTRAINT `menus_ibfk_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of menus
-- ----------------------------

-- ----------------------------
-- Table structure for payment_gateways
-- ----------------------------
DROP TABLE IF EXISTS `payment_gateways`;
CREATE TABLE `payment_gateways` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `payment_method` varchar(50) NOT NULL,
  `gateway_type` varchar(50) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `config` text DEFAULT NULL,
  `exchange_rate` float NOT NULL,
  `points_per_baht` float DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_payment_gateways_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of payment_gateways
-- ----------------------------

-- ----------------------------
-- Table structure for profiles
-- ----------------------------
DROP TABLE IF EXISTS `profiles`;
CREATE TABLE `profiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `profile_type` varchar(50) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_profiles_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of profiles
-- ----------------------------

-- ----------------------------
-- Table structure for promptpay_back_transactions
-- ----------------------------
DROP TABLE IF EXISTS `promptpay_back_transactions`;
CREATE TABLE `promptpay_back_transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref1` varchar(20) NOT NULL,
  `ref2` varchar(50) DEFAULT NULL,
  `ref3` varchar(255) DEFAULT NULL,
  `amount` float NOT NULL,
  `paid_at` datetime NOT NULL,
  `slip_reference` varchar(100) DEFAULT NULL,
  `bank_account` varchar(50) DEFAULT NULL,
  `store_id` int(11) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `raw_payload` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_promptpay_back_transactions_store_id` (`store_id`),
  KEY `ix_promptpay_back_transactions_slip_reference` (`slip_reference`),
  KEY `ix_promptpay_back_transactions_id` (`id`),
  KEY `ix_promptpay_back_transactions_ref1` (`ref1`),
  CONSTRAINT `promptpay_back_transactions_ibfk_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of promptpay_back_transactions
-- ----------------------------

-- ----------------------------
-- Table structure for refund_notifications
-- ----------------------------
DROP TABLE IF EXISTS `refund_notifications`;
CREATE TABLE `refund_notifications` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `balance_amount` float NOT NULL,
  `notification_sent` tinyint(1) NOT NULL,
  `notification_sent_at` datetime DEFAULT NULL,
  `refund_requested` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `customer_id` (`customer_id`),
  KEY `ix_refund_notifications_id` (`id`),
  CONSTRAINT `refund_notifications_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of refund_notifications
-- ----------------------------

-- ----------------------------
-- Table structure for refund_requests
-- ----------------------------
DROP TABLE IF EXISTS `refund_requests`;
CREATE TABLE `refund_requests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `store_id` int(11) DEFAULT NULL,
  `amount` float NOT NULL,
  `refund_method` enum('CASH','PROMPTPAY') NOT NULL,
  `status` varchar(50) DEFAULT NULL,
  `promptpay_number` varchar(20) DEFAULT NULL,
  `processed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `customer_id` (`customer_id`),
  KEY `store_id` (`store_id`),
  KEY `ix_refund_requests_id` (`id`),
  CONSTRAINT `refund_requests_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`),
  CONSTRAINT `refund_requests_ibfk_2` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of refund_requests
-- ----------------------------

-- ----------------------------
-- Table structure for stores
-- ----------------------------
DROP TABLE IF EXISTS `stores`;
CREATE TABLE `stores` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `tax_id` varchar(20) DEFAULT NULL,
  `crypto_enabled` tinyint(1) NOT NULL,
  `contract_accepted` tinyint(1) NOT NULL,
  `contract_accepted_at` datetime DEFAULT NULL,
  `contract_version` varchar(20) DEFAULT NULL,
  `group_id` int(11) NOT NULL,
  `site_id` int(11) NOT NULL,
  `token` varchar(20) DEFAULT NULL,
  `biller_id` varchar(15) DEFAULT NULL,
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `location_name` varchar(255) DEFAULT NULL,
  `profile_id` int(11) DEFAULT NULL,
  `event_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_stores_token` (`token`),
  KEY `profile_id` (`profile_id`),
  KEY `event_id` (`event_id`),
  KEY `ix_stores_id` (`id`),
  CONSTRAINT `stores_ibfk_1` FOREIGN KEY (`profile_id`) REFERENCES `profiles` (`id`),
  CONSTRAINT `stores_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of stores
-- ----------------------------
INSERT INTO `stores` VALUES ('1', 'ร้านอาหารตัวอย่าง', '1234567890123', '0', '0', null, null, '0', '0', null, null, null, null, null, null, null, '2026-02-01 14:48:57', null);

-- ----------------------------
-- Table structure for store_quick_amounts
-- ----------------------------
DROP TABLE IF EXISTS `store_quick_amounts`;
CREATE TABLE `store_quick_amounts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `store_id` int(11) NOT NULL,
  `amount` float NOT NULL,
  `label` varchar(50) DEFAULT NULL,
  `display_order` int(11) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_store_quick_amounts_store_id` (`store_id`),
  KEY `ix_store_quick_amounts_id` (`id`),
  CONSTRAINT `store_quick_amounts_ibfk_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of store_quick_amounts
-- ----------------------------

-- ----------------------------
-- Table structure for store_settlements
-- ----------------------------
DROP TABLE IF EXISTS `store_settlements`;
CREATE TABLE `store_settlements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `store_id` int(11) NOT NULL,
  `settlement_date` datetime NOT NULL,
  `amount` float NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `transferred_at` datetime DEFAULT NULL,
  `notified_at` datetime DEFAULT NULL,
  `receipt_printed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_store_settlements_id` (`id`),
  KEY `ix_store_settlements_store_id` (`store_id`),
  CONSTRAINT `store_settlements_ibfk_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of store_settlements
-- ----------------------------

-- ----------------------------
-- Table structure for store_transactions
-- ----------------------------
DROP TABLE IF EXISTS `store_transactions`;
CREATE TABLE `store_transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `foodcourt_id` varchar(50) NOT NULL,
  `store_id` int(11) NOT NULL,
  `amount` float NOT NULL,
  `status` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `foodcourt_id` (`foodcourt_id`),
  KEY `store_id` (`store_id`),
  KEY `ix_store_transactions_id` (`id`),
  CONSTRAINT `store_transactions_ibfk_1` FOREIGN KEY (`foodcourt_id`) REFERENCES `foodcourt_ids` (`foodcourt_id`),
  CONSTRAINT `store_transactions_ibfk_2` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of store_transactions
-- ----------------------------

-- ----------------------------
-- Table structure for tax_invoices
-- ----------------------------
DROP TABLE IF EXISTS `tax_invoices`;
CREATE TABLE `tax_invoices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `transaction_id` int(11) NOT NULL,
  `invoice_number` varchar(50) NOT NULL,
  `tax_id` varchar(20) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `amount` float NOT NULL,
  `vat_amount` float NOT NULL,
  `total_amount` float NOT NULL,
  `payment_method` varchar(50) DEFAULT NULL,
  `issued_at` datetime DEFAULT current_timestamp(),
  `e_tax_sent` tinyint(1) NOT NULL,
  `e_tax_sent_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transaction_id` (`transaction_id`),
  UNIQUE KEY `ix_tax_invoices_invoice_number` (`invoice_number`),
  KEY `ix_tax_invoices_id` (`id`),
  CONSTRAINT `tax_invoices_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of tax_invoices
-- ----------------------------

-- ----------------------------
-- Table structure for transactions
-- ----------------------------
DROP TABLE IF EXISTS `transactions`;
CREATE TABLE `transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `store_id` int(11) NOT NULL,
  `amount` float NOT NULL,
  `payment_method` enum('CASH','CREDIT_CARD_VISA','CREDIT_CARD_MASTERCARD','CREDIT_CARD_AMEX','CREDIT_CARD_JCB','CREDIT_CARD_UNIONPAY','TRUE_WALLET','PROMPTPAY','LINE_PAY','RABBIT_LINE_PAY','SHOPEE_PAY','GRAB_PAY','APPLE_PAY','GOOGLE_PAY','SAMSUNG_PAY','ALIPAY','WECHAT_PAY','PAYPAL','AMAZON_PAY','VENMO','ZELLE','CASH_APP','BANK_TRANSFER','WIRE_TRANSFER','CRYPTO_BTC','CRYPTO_ETH','CRYPTO_XRP','CRYPTO_BITKUB','CRYPTO_BINANCE','CRYPTO_SOLANA','CRYPTO_USDT','CRYPTO_USDC','CRYPTO_CUSTOM','POINTS_THE1','POINTS_BLUECARD','POINTS_CREDIT_CARD','POINTS_AIRLINE','POINTS_HOTEL','POINTS_CUSTOM','VOUCHER','GIFT_CARD','COUPON','BNPL_ATOME','BNPL_SPLIT','BNPL_GRAB_PAYLATER','BNPL_AFFIRM','BNPL_KLARNA','BNPL_AFTERPAY','CUSTOM') NOT NULL,
  `status` enum('PENDING','CONFIRMED','FAILED','REFUNDED') DEFAULT NULL,
  `receipt_number` varchar(50) NOT NULL,
  `qr_code` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  `foodcourt_id` varchar(50) DEFAULT NULL,
  `ref1` varchar(20) DEFAULT NULL,
  `ref2` varchar(50) DEFAULT NULL,
  `ref3` varchar(255) DEFAULT NULL,
  `bank_account` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_transactions_receipt_number` (`receipt_number`),
  KEY `customer_id` (`customer_id`),
  KEY `store_id` (`store_id`),
  KEY `foodcourt_id` (`foodcourt_id`),
  KEY `ix_transactions_id` (`id`),
  KEY `ix_transactions_ref1` (`ref1`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`),
  CONSTRAINT `transactions_ibfk_2` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`),
  CONSTRAINT `transactions_ibfk_3` FOREIGN KEY (`foodcourt_id`) REFERENCES `foodcourt_ids` (`foodcourt_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of transactions
-- ----------------------------
