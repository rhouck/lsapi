-- phpMyAdmin SQL Dump
-- version 3.5.2.2
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: Sep 20, 2013 at 10:05 PM
-- Server version: 5.5.27-log
-- PHP Version: 5.4.14

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `api_api`
--

-- --------------------------------------------------------

--
-- Table structure for table `analysis_additional_capacity`
--

CREATE TABLE IF NOT EXISTS `analysis_additional_capacity` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `quantity` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

--
-- Dumping data for table `analysis_additional_capacity`
--

INSERT INTO `analysis_additional_capacity` (`id`, `quantity`) VALUES
(1, 95);

-- --------------------------------------------------------

--
-- Table structure for table `analysis_cash_reserve`
--

CREATE TABLE IF NOT EXISTS `analysis_cash_reserve` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_date` datetime NOT NULL,
  `transaction_id` int(11) DEFAULT NULL,
  `cash_change` double NOT NULL,
  `cash_balance` double NOT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_cash_reserve_45d19ab3` (`transaction_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=17 ;

--
-- Dumping data for table `analysis_cash_reserve`
--

INSERT INTO `analysis_cash_reserve` (`id`, `action_date`, `transaction_id`, `cash_change`, `cash_balance`) VALUES
(1, '2013-09-18 00:22:05', NULL, 10000, 10000),
(2, '2013-09-18 00:42:45', 1, 25, 10025),
(3, '2013-09-18 00:46:49', 2, 25, 10050),
(4, '2013-09-18 01:06:22', 3, 25, 10075),
(5, '2013-09-18 01:20:43', 4, 25, 10100),
(6, '2013-09-18 01:22:04', 5, 25, 10125),
(7, '2013-09-18 01:57:59', 6, 25, 10150),
(8, '2013-09-18 02:01:22', 7, 25, 10175),
(9, '2013-09-18 02:58:07', 8, 25, 10200),
(10, '2013-09-18 03:11:58', 9, 25, 10225),
(11, '2013-09-19 00:22:15', 10, 25, 10250),
(12, '2013-09-19 00:42:43', 11, 25, 10275),
(13, '2013-09-19 01:22:39', 12, 25, 10300),
(14, '2013-09-19 01:27:13', 14, 25, 10325),
(15, '2013-09-19 17:18:09', 15, 25, 10350),
(16, '2013-09-19 18:16:39', 16, 25, 10375);

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_425ae3c4` (`group_id`),
  KEY `auth_group_permissions_1e014c8f` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_1bb8f392` (`content_type_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=49 ;

--
-- Dumping data for table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can add permission', 2, 'add_permission'),
(5, 'Can change permission', 2, 'change_permission'),
(6, 'Can delete permission', 2, 'delete_permission'),
(7, 'Can add group', 3, 'add_group'),
(8, 'Can change group', 3, 'change_group'),
(9, 'Can delete group', 3, 'delete_group'),
(10, 'Can add user', 4, 'add_user'),
(11, 'Can change user', 4, 'change_user'),
(12, 'Can delete user', 4, 'delete_user'),
(13, 'Can add content type', 5, 'add_contenttype'),
(14, 'Can change content type', 5, 'change_contenttype'),
(15, 'Can delete content type', 5, 'delete_contenttype'),
(16, 'Can add session', 6, 'add_session'),
(17, 'Can change session', 6, 'change_session'),
(18, 'Can delete session', 6, 'delete_session'),
(19, 'Can add site', 7, 'add_site'),
(20, 'Can change site', 7, 'change_site'),
(21, 'Can delete site', 7, 'delete_site'),
(22, 'Can add redirect', 8, 'add_redirect'),
(23, 'Can change redirect', 8, 'change_redirect'),
(24, 'Can delete redirect', 8, 'delete_redirect'),
(25, 'Can add Search History', 9, 'add_search_history'),
(26, 'Can change Search History', 9, 'change_search_history'),
(27, 'Can delete Search History', 9, 'delete_search_history'),
(28, 'Can add platform', 10, 'add_platform'),
(29, 'Can change platform', 10, 'change_platform'),
(30, 'Can delete platform', 10, 'delete_platform'),
(31, 'Can add customer', 11, 'add_customer'),
(32, 'Can change customer', 11, 'change_customer'),
(33, 'Can delete customer', 11, 'delete_customer'),
(34, 'Can add contract', 12, 'add_contract'),
(35, 'Can change contract', 12, 'change_contract'),
(36, 'Can delete contract', 12, 'delete_contract'),
(37, 'Can add open', 13, 'add_open'),
(38, 'Can change open', 13, 'change_open'),
(39, 'Can delete open', 13, 'delete_open'),
(40, 'Can add Cash Reserve', 14, 'add_cash_reserve'),
(41, 'Can change Cash Reserve', 14, 'change_cash_reserve'),
(42, 'Can delete Cash Reserve', 14, 'delete_cash_reserve'),
(43, 'Can add Additional Capacity', 15, 'add_additional_capacity'),
(44, 'Can change Additional Capacity', 15, 'change_additional_capacity'),
(45, 'Can delete Additional Capacity', 15, 'delete_additional_capacity'),
(46, 'Can add routes', 16, 'add_routes'),
(47, 'Can change routes', 16, 'change_routes'),
(48, 'Can delete routes', 16, 'delete_routes');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user`
--

CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

--
-- Dumping data for table `auth_user`
--

INSERT INTO `auth_user` (`id`, `username`, `first_name`, `last_name`, `email`, `password`, `is_staff`, `is_active`, `is_superuser`, `last_login`, `date_joined`) VALUES
(1, 'ryanchouck', '', '', 'ryan@levelskies.com', 'pbkdf2_sha256$10000$wEmYvjzo9Xrm$FtV/7GcIywq3m3muQ1Bsb7/ZJMhF8TSfk0yEAxDWgGA=', 1, 1, 1, '2013-09-19 17:43:13', '2013-09-18 00:17:57');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_groups`
--

CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_403f60f` (`user_id`),
  KEY `auth_user_groups_425ae3c4` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_user_permissions`
--

CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_403f60f` (`user_id`),
  KEY `auth_user_user_permissions_1e014c8f` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_403f60f` (`user_id`),
  KEY `django_admin_log_1bb8f392` (`content_type_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=6 ;

--
-- Dumping data for table `django_admin_log`
--

INSERT INTO `django_admin_log` (`id`, `action_time`, `user_id`, `content_type_id`, `object_id`, `object_repr`, `action_flag`, `change_message`) VALUES
(1, '2013-09-18 00:21:08', 1, 7, '2', 'http://127.0.0.1:8002', 1, ''),
(2, '2013-09-18 00:21:49', 1, 13, '1', 'True', 1, ''),
(3, '2013-09-18 00:21:57', 1, 15, '1', '99', 1, ''),
(4, '2013-09-18 00:22:15', 1, 14, '1', '10000.0', 1, ''),
(5, '2013-09-18 00:22:54', 1, 10, '1', 'Local', 1, '');

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=17 ;

--
-- Dumping data for table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `name`, `app_label`, `model`) VALUES
(1, 'log entry', 'admin', 'logentry'),
(2, 'permission', 'auth', 'permission'),
(3, 'group', 'auth', 'group'),
(4, 'user', 'auth', 'user'),
(5, 'content type', 'contenttypes', 'contenttype'),
(6, 'session', 'sessions', 'session'),
(7, 'site', 'sites', 'site'),
(8, 'redirect', 'redirects', 'redirect'),
(9, 'Search History', 'pricing', 'search_history'),
(10, 'platform', 'sales', 'platform'),
(11, 'customer', 'sales', 'customer'),
(12, 'contract', 'sales', 'contract'),
(13, 'open', 'sales', 'open'),
(14, 'Cash Reserve', 'analysis', 'cash_reserve'),
(15, 'Additional Capacity', 'analysis', 'additional_capacity'),
(16, 'routes', 'routes', 'routes');

-- --------------------------------------------------------

--
-- Table structure for table `django_redirect`
--

CREATE TABLE IF NOT EXISTS `django_redirect` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `site_id` int(11) NOT NULL,
  `old_path` varchar(200) NOT NULL,
  `new_path` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `site_id` (`site_id`,`old_path`),
  KEY `django_redirect_6223029` (`site_id`),
  KEY `django_redirect_516c23f0` (`old_path`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_3da3d3d8` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('1e956757200bdda844319f228177cd4a', 'ZGFmMDcyM2I3OGMyNDJjYjJlNjdjMWI4MWI5YWU4MGFlOGZlNDQ1MzqAAn1xAShVEl9hdXRoX3Vz\nZXJfYmFja2VuZHECVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZHED\nVQ1fYXV0aF91c2VyX2lkcQSKAQF1Lg==\n', '2013-10-02 00:51:26'),
('432c947e94bcb59c38dd8ad1013fd9df', 'ZGFmMDcyM2I3OGMyNDJjYjJlNjdjMWI4MWI5YWU4MGFlOGZlNDQ1MzqAAn1xAShVEl9hdXRoX3Vz\nZXJfYmFja2VuZHECVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZHED\nVQ1fYXV0aF91c2VyX2lkcQSKAQF1Lg==\n', '2013-10-02 00:37:05'),
('618f22f807179bb8df9ef7422f22e5d4', 'YzBjNGVkODlkMTVmOWE2Zjg5NjkyNzE3NWE2MGZhOTQzMTE4YzY4ZjqAAn1xAShVCnRlc3Rjb29r\naWVVBndvcmtlZFUSX2F1dGhfdXNlcl9iYWNrZW5kVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tl\nbmRzLk1vZGVsQmFja2VuZHECVQ1fYXV0aF91c2VyX2lkigEBdS4=\n', '2013-10-02 21:19:14'),
('67fa44e96fbccd777e39059908ca0c95', 'ZGFmMDcyM2I3OGMyNDJjYjJlNjdjMWI4MWI5YWU4MGFlOGZlNDQ1MzqAAn1xAShVEl9hdXRoX3Vz\nZXJfYmFja2VuZHECVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZHED\nVQ1fYXV0aF91c2VyX2lkcQSKAQF1Lg==\n', '2013-10-02 01:19:30'),
('6c6af1dbc23c821ca7fd5b80f4c12586', 'ZGFmMDcyM2I3OGMyNDJjYjJlNjdjMWI4MWI5YWU4MGFlOGZlNDQ1MzqAAn1xAShVEl9hdXRoX3Vz\nZXJfYmFja2VuZHECVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZHED\nVQ1fYXV0aF91c2VyX2lkcQSKAQF1Lg==\n', '2013-10-02 22:11:36'),
('8140329d5c17ed6a3c363a7ae9a0971a', 'ZWY4OGYzNjNmMmU0ZTIyM2ExZjE5MDg3N2UwZDY2MDc1ZDM2NTExNzqAAn1xAShVCnRlc3Rjb29r\naWVVBndvcmtlZFUSX2F1dGhfdXNlcl9iYWNrZW5kcQJVKWRqYW5nby5jb250cmliLmF1dGguYmFj\na2VuZHMuTW9kZWxCYWNrZW5kcQNVDV9hdXRoX3VzZXJfaWRxBIoBAXUu\n', '2013-10-02 00:20:19'),
('95ce08b0c5a560193c7ccb73b8a98b64', 'ZGFmMDcyM2I3OGMyNDJjYjJlNjdjMWI4MWI5YWU4MGFlOGZlNDQ1MzqAAn1xAShVEl9hdXRoX3Vz\nZXJfYmFja2VuZHECVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZHED\nVQ1fYXV0aF91c2VyX2lkcQSKAQF1Lg==\n', '2013-10-02 22:03:33'),
('acec7dcbf77e822cc653224cc88ea782', 'M2ZkNThlZmVlYWEzYmM3MTQ5MmEyNzhjNzZiY2Q3M2E0OGJlMjQ2MDqAAn1xAS4=\n', '2013-10-03 01:30:31'),
('eaab1f443f60c7a0ae36bf201ca36743', 'ZGFmMDcyM2I3OGMyNDJjYjJlNjdjMWI4MWI5YWU4MGFlOGZlNDQ1MzqAAn1xAShVEl9hdXRoX3Vz\nZXJfYmFja2VuZHECVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZHED\nVQ1fYXV0aF91c2VyX2lkcQSKAQF1Lg==\n', '2013-10-03 01:20:06'),
('f862ad265520391f2017691d95f6ded5', 'ZGFmMDcyM2I3OGMyNDJjYjJlNjdjMWI4MWI5YWU4MGFlOGZlNDQ1MzqAAn1xAShVEl9hdXRoX3Vz\nZXJfYmFja2VuZHECVSlkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZHED\nVQ1fYXV0aF91c2VyX2lkcQSKAQF1Lg==\n', '2013-10-03 17:43:13');

-- --------------------------------------------------------

--
-- Table structure for table `django_site`
--

CREATE TABLE IF NOT EXISTS `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=3 ;

--
-- Dumping data for table `django_site`
--

INSERT INTO `django_site` (`id`, `domain`, `name`) VALUES
(1, 'example.com', 'example.com'),
(2, 'http://127.0.0.1:8002', 'Level Skies API - Local');

-- --------------------------------------------------------

--
-- Table structure for table `pricing_search_history`
--

CREATE TABLE IF NOT EXISTS `pricing_search_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `search_date` datetime NOT NULL,
  `exp_date` date DEFAULT NULL,
  `open_status` tinyint(1) NOT NULL,
  `key` varchar(10) DEFAULT NULL,
  `origin_code` varchar(20) NOT NULL,
  `destination_code` varchar(20) NOT NULL,
  `holding_per` int(11) NOT NULL,
  `depart_date1` date NOT NULL,
  `depart_date2` date NOT NULL,
  `return_date1` date DEFAULT NULL,
  `return_date2` date DEFAULT NULL,
  `search_type` varchar(200) NOT NULL,
  `depart_times` int(11) NOT NULL,
  `return_times` int(11) NOT NULL,
  `nonstop` int(11) NOT NULL,
  `locked_fare` double DEFAULT NULL,
  `holding_price` double DEFAULT NULL,
  `error` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=51 ;

--
-- Dumping data for table `pricing_search_history`
--

INSERT INTO `pricing_search_history` (`id`, `search_date`, `exp_date`, `open_status`, `key`, `origin_code`, `destination_code`, `holding_per`, `depart_date1`, `depart_date2`, `return_date1`, `return_date2`, `search_type`, `depart_times`, `return_times`, `nonstop`, `locked_fare`, `holding_price`, `error`) VALUES
(1, '2013-09-18 00:26:51', '2013-10-08', 1, '1aMUdp', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(2, '2013-09-18 00:30:58', '2013-10-08', 1, 'bQYMuF', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(3, '2013-09-18 00:42:27', '2013-10-08', 1, 'Blgd5B', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(4, '2013-09-18 00:46:17', '2013-10-08', 1, 'TzRnyU', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(5, '2013-09-18 01:05:55', '2013-10-08', 1, '31wOkk', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-12', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(6, '2013-09-18 01:18:45', '2013-10-08', 1, '0aKH92', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(7, '2013-09-18 01:21:40', '2013-10-08', 1, 'N8rvBA', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-12', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(8, '2013-09-18 01:51:13', '2013-10-08', 1, 'YxBN3W', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(9, '2013-09-18 01:57:03', '2013-10-08', 1, '5mHHNs', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(10, '2013-09-18 02:01:10', '2013-10-08', 1, 'D7OdoN', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(11, '2013-09-18 02:01:37', '2013-10-08', 1, 'BH3j8L', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(12, '2013-09-18 02:48:36', '2013-10-08', 1, 'CTuWmJ', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(13, '2013-09-18 02:55:06', '2013-10-08', 1, '5Nc3b8', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(14, '2013-09-18 03:11:40', '2013-10-08', 1, '5WdpSY', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(15, '2013-09-18 19:31:36', '2013-10-09', 1, 'c6i9MC', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(16, '2013-09-18 21:53:44', '2013-10-09', 1, 'CDR8a0', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(17, '2013-09-18 21:58:58', '2013-10-09', 1, 'f57a6l', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(18, '2013-09-18 21:59:15', '2013-10-09', 1, 'JttaJa', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(19, '2013-09-19 00:20:22', '2013-10-09', 1, 'E2V0M0', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(20, '2013-09-19 00:42:28', '2013-10-09', 1, 'xSsWDi', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(21, '2013-09-19 01:17:39', '2013-10-09', 1, 'WVSWJG', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(22, '2013-09-19 01:22:28', '2013-10-09', 1, 'O8IdCq', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(23, '2013-09-19 01:27:01', '2013-10-09', 1, 'QP9Tcb', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(24, '2013-09-19 01:32:43', '2013-10-09', 1, 'Ih0Ntf', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(25, '2013-09-19 01:35:32', '2013-10-09', 1, 'sCdNRl', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(26, '2013-09-19 17:17:58', '2013-10-10', 1, 'NdFNg2', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(27, '2013-09-19 18:16:03', '2013-10-10', 1, 'EvKlBe', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(28, '2013-09-19 18:18:08', '2013-10-10', 1, 'kEMo4G', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(29, '2013-09-19 18:40:23', '2013-10-10', 1, 'd9fYKy', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(30, '2013-09-19 18:45:50', '2013-10-10', 1, 'bVfedu', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(31, '2013-09-19 18:48:10', '2013-10-10', 1, 'LcSQYS', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(32, '2013-09-19 18:48:26', '2013-10-10', 1, 'S3ka1i', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(33, '2013-09-19 18:49:31', '2013-10-10', 1, 'Y9SxCW', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(34, '2013-09-19 18:50:28', '2013-10-10', 1, 'fQjG0d', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(35, '2013-09-19 18:50:57', '2013-10-10', 1, 'S0FIBX', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(36, '2013-09-19 18:51:30', '2013-10-10', 1, 'InQM0F', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(37, '2013-09-19 18:52:06', '2013-10-10', 1, 'aNnFuT', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(38, '2013-09-19 18:53:49', '2013-10-10', 1, 'xicAnC', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(39, '2013-09-19 18:54:03', '2013-10-10', 1, 'WMsoYy', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(40, '2013-09-19 18:54:14', '2013-10-10', 1, 'oRpDYa', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(41, '2013-09-19 18:54:28', '2013-10-10', 1, 'fP6PIX', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(42, '2013-09-19 18:54:38', '2013-10-10', 1, 'wGvRRL', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(43, '2013-09-19 18:54:42', '2013-10-10', 1, 'uVuVKK', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(44, '2013-09-19 18:54:51', '2013-10-10', 1, 'JS6wJK', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(45, '2013-09-19 18:57:12', '2013-10-10', 1, 'UbfMqC', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(46, '2013-09-19 18:57:24', '2013-10-10', 1, 'wP84bU', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(47, '2013-09-19 18:58:01', '2013-10-10', 1, 'eCtXxM', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(48, '2013-09-19 19:06:21', '2013-10-10', 1, 'lhrG7g', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(49, '2013-09-19 19:18:22', '2013-10-10', 1, '4RStWz', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL),
(50, '2013-09-19 21:37:14', '2013-10-10', 1, 'oig4yO', 'SFO', 'MAD', 2, '2013-06-12', '2013-06-13', '2013-06-20', '2013-06-22', 'rt', 0, 0, 0, 500, 25, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `routes_routes`
--

CREATE TABLE IF NOT EXISTS `routes_routes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `org_code` longtext NOT NULL,
  `dest_code` longtext NOT NULL,
  `org_full` longtext,
  `dest_full` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `sales_contract`
--

CREATE TABLE IF NOT EXISTS `sales_contract` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `purch_date` datetime NOT NULL,
  `search_id` int(11) NOT NULL,
  `ex_fare` double DEFAULT NULL,
  `ex_date` datetime DEFAULT NULL,
  `gateway_id` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `search_id` (`search_id`),
  KEY `sales_contract_12366e04` (`customer_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=17 ;

--
-- Dumping data for table `sales_contract`
--

INSERT INTO `sales_contract` (`id`, `customer_id`, `purch_date`, `search_id`, `ex_fare`, `ex_date`, `gateway_id`) VALUES
(1, 2, '2013-09-18 00:42:43', 3, 500, '2013-09-18 00:46:10', NULL),
(2, 2, '2013-09-18 00:46:48', 4, 500, '2013-09-18 00:51:55', NULL),
(3, 2, '2013-09-18 01:06:20', 5, 500, '2013-09-18 01:37:19', '0'),
(4, 2, '2013-09-18 01:20:40', 6, 500, '2013-09-18 01:21:13', '0'),
(5, 2, '2013-09-18 01:22:03', 7, 500, '2013-09-18 02:58:15', '0'),
(6, 2, '2013-09-18 01:57:58', 9, 500, '2013-09-18 02:02:13', '0'),
(7, 2, '2013-09-18 02:01:22', 10, 500, '2013-09-19 01:26:52', '0'),
(8, 2, '2013-09-18 02:58:06', 13, 500, '2013-09-18 03:11:34', '0'),
(9, 2, '2013-09-18 03:11:58', 14, 500, '2013-09-19 01:01:36', '0'),
(10, 2, '2013-09-19 00:22:14', 19, 500, '2013-09-19 00:43:45', '0'),
(11, 2, '2013-09-19 00:42:43', 20, 500, '2013-09-19 01:26:46', '0'),
(12, 2, '2013-09-19 01:22:38', 22, 500, '2013-09-19 01:26:39', '0'),
(14, 2, '2013-09-19 01:27:13', 23, NULL, NULL, '0'),
(15, 2, '2013-09-19 17:18:08', 26, NULL, NULL, '0'),
(16, 2, '2013-09-19 18:16:37', 27, NULL, NULL, '0');

-- --------------------------------------------------------

--
-- Table structure for table `sales_customer`
--

CREATE TABLE IF NOT EXISTS `sales_customer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(10) NOT NULL,
  `email` varchar(75) NOT NULL,
  `platform_id` int(11) NOT NULL,
  `reg_date` date NOT NULL,
  `first_name` varchar(200) DEFAULT NULL,
  `last_name` varchar(200) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address1` varchar(50) DEFAULT NULL,
  `city` varchar(60) DEFAULT NULL,
  `state_province` varchar(30) DEFAULT NULL,
  `postal_code` varchar(50) DEFAULT NULL,
  `country` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sales_customer_2e5bc86d` (`platform_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=4 ;

--
-- Dumping data for table `sales_customer`
--

INSERT INTO `sales_customer` (`id`, `key`, `email`, `platform_id`, `reg_date`, `first_name`, `last_name`, `phone`, `address1`, `city`, `state_province`, `postal_code`, `country`) VALUES
(1, 'hbix6R', 'test1@test.com', 1, '2013-09-18', '', '', '', '', '', '', '', ''),
(2, 'urUyfk', 'ryanchouck@gmail.com', 1, '2013-09-18', 'Ryan', 'Houck', '1231231234', '2132 W. ALLUVIAL', 'FRESNO', 'California', '93711', 'United States'),
(3, 'iD4T76', 'brandon@levelskies.com', 1, '2013-09-18', '', '', '', '', '', '', '', '');

-- --------------------------------------------------------

--
-- Table structure for table `sales_open`
--

CREATE TABLE IF NOT EXISTS `sales_open` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `status` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

--
-- Dumping data for table `sales_open`
--

INSERT INTO `sales_open` (`id`, `status`) VALUES
(1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `sales_platform`
--

CREATE TABLE IF NOT EXISTS `sales_platform` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `org_name` varchar(200) NOT NULL,
  `web_site` varchar(200) NOT NULL,
  `contact_name` varchar(200) NOT NULL,
  `contact_email` varchar(75) NOT NULL,
  `reg_date` date NOT NULL,
  `key` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

--
-- Dumping data for table `sales_platform`
--

INSERT INTO `sales_platform` (`id`, `org_name`, `web_site`, `contact_name`, `contact_email`, `reg_date`, `key`) VALUES
(1, 'Local', 'levelskies.com', 'brandon', 'brandon@levelskies.com', '2013-09-17', '123456');

--
-- Constraints for dumped tables
--

--
-- Constraints for table `analysis_cash_reserve`
--
ALTER TABLE `analysis_cash_reserve`
  ADD CONSTRAINT `transaction_id_refs_id_55849dd2` FOREIGN KEY (`transaction_id`) REFERENCES `sales_contract` (`id`);

--
-- Constraints for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `permission_id_refs_id_5886d21f` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);

--
-- Constraints for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Constraints for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `user_id_refs_id_7ceef80f` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `group_id_refs_id_f116770` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Constraints for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `user_id_refs_id_dfbab7d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);

--
-- Constraints for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `django_redirect`
--
ALTER TABLE `django_redirect`
  ADD CONSTRAINT `site_id_refs_id_4aa27aa6` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`);

--
-- Constraints for table `sales_contract`
--
ALTER TABLE `sales_contract`
  ADD CONSTRAINT `search_id_refs_id_320f6a7e` FOREIGN KEY (`search_id`) REFERENCES `pricing_search_history` (`id`),
  ADD CONSTRAINT `customer_id_refs_id_170d8b33` FOREIGN KEY (`customer_id`) REFERENCES `sales_customer` (`id`);

--
-- Constraints for table `sales_customer`
--
ALTER TABLE `sales_customer`
  ADD CONSTRAINT `platform_id_refs_id_53838c6` FOREIGN KEY (`platform_id`) REFERENCES `sales_platform` (`id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
