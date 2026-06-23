-- 悦选电商平台 — 数据库初始化（Day08 完整版）
CREATE DATABASE IF NOT EXISTS `yuexuan` DEFAULT CHARSET utf8mb4;

USE `yuexuan`;

-- ===== 用户/认证 =====
DROP TABLE IF EXISTS `t_user`;
CREATE TABLE `t_user` (
    `id`          BIGINT AUTO_INCREMENT,
    `username`    VARCHAR(50)  NOT NULL,
    `password`    VARCHAR(100) NOT NULL,  -- 明文密码（非生产）
    `phone`       VARCHAR(20)  DEFAULT NULL,
    `role`        VARCHAR(20)  DEFAULT 'user',    -- user / shop / admin
    `category`    VARCHAR(50)  DEFAULT NULL,      -- Day09 商家经营类目
    `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===== 商品 =====
DROP TABLE IF EXISTS `t_product`;
CREATE TABLE `t_product` (
    `pid`          BIGINT AUTO_INCREMENT,
    `name`         VARCHAR(200)  NOT NULL,
    `price`        DOUBLE        NOT NULL DEFAULT 0,
    `image`        VARCHAR(500)  DEFAULT NULL,
    `category`     VARCHAR(100)   DEFAULT NULL,
    `description`  VARCHAR(500)  DEFAULT NULL,
    `stock`        INT           NOT NULL DEFAULT 0,
    `rating`       DOUBLE        DEFAULT 0,
    `review_count` INT           DEFAULT 0,
    PRIMARY KEY (`pid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===== 订单 =====
DROP TABLE IF EXISTS `t_order`;
CREATE TABLE `t_order` (
    `id`               BIGINT AUTO_INCREMENT,
    `order_no`         VARCHAR(30)  DEFAULT NULL,
    `pid`              BIGINT       DEFAULT NULL,
    `product_name`     VARCHAR(200) DEFAULT NULL,
    `product_category` VARCHAR(50)  DEFAULT NULL,
    `product_price`    DOUBLE       DEFAULT NULL,
    `uid`              BIGINT       DEFAULT NULL,
    `username`         VARCHAR(50)  DEFAULT NULL,
    `number`           INT          DEFAULT 1,
    `total_amount`     DOUBLE       DEFAULT NULL,
    `status`           VARCHAR(20)  DEFAULT 'PENDING',  -- PENDING/PAID/SHIPPING/COMPLETED/CANCELLED
    `receiver_name`    VARCHAR(50)  DEFAULT NULL,
    `receiver_phone`   VARCHAR(20)  DEFAULT NULL,
    `address`          VARCHAR(500) DEFAULT NULL,
    `handled_by_port`  VARCHAR(10)  DEFAULT NULL,
    `create_time`      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    `pay_time`         DATETIME     DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===== 收货地址 =====
DROP TABLE IF EXISTS `t_user_address`;
CREATE TABLE `t_user_address` (
    `id`          BIGINT AUTO_INCREMENT,
    `user_id`     BIGINT       NOT NULL,
    `name`        VARCHAR(50)  NOT NULL,
    `phone`       VARCHAR(20)  NOT NULL,
    `province`    VARCHAR(50)  DEFAULT NULL,
    `city`        VARCHAR(50)  DEFAULT NULL,
    `district`    VARCHAR(50)  DEFAULT NULL,
    `detail`      VARCHAR(500) NOT NULL,
    `is_default`  INT          DEFAULT 0,
    `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===== 支付记录 =====
DROP TABLE IF EXISTS `t_pay_info`;
CREATE TABLE `t_pay_info` (
    `pay_id`      BIGINT AUTO_INCREMENT,
    `order_id`    BIGINT       NOT NULL,
    `order_no`    VARCHAR(30)  DEFAULT NULL,
    `user_id`     BIGINT       DEFAULT NULL,
    `amount`      DOUBLE       NOT NULL,
    `status`      VARCHAR(20)  DEFAULT 'UNPAID',  -- UNPAID / PAID
    `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP,
    `pay_time`    DATETIME     DEFAULT NULL,
    PRIMARY KEY (`pay_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===== 测试数据 =====
INSERT INTO `t_user` (`username`, `password`, `role`) VALUES
('admin',      '123456', 'admin'),
('shoe_shop',  '123456', 'shop'),
('cloth_shop', '123456', 'shop'),
('dafei',      '123456', 'user'),
('test',       '123456', 'user');

INSERT INTO `t_product` (`name`, `price`, `image`, `category`, `description`, `stock`, `rating`, `review_count`) VALUES
('小米14 Ultra',        6999, NULL, '数码',   '旗舰影像手机',         100, 4.8, 1200),
('华为 MatePad Pro',    4999, NULL, '数码',   '平板电脑',             80,  4.7, 800),
('Air Max 运动跑鞋',    899,  NULL, '运动鞋', '舒适缓震跑步鞋',       200, 4.5, 1500),
('纯棉圆领T恤',         129,  NULL, 'T恤',    '100%纯棉',             500, 4.3, 3000),
('坚果礼盒',            88,   NULL, '食品',   '每日坚果混合装',       300, 4.6, 600),
('Maz Maz 番茄薯片',    15.9, 'mazmaz-chips-1.png', '食品',   '伊朗人气零食 · ketchup chips', 200, 4.8, 320),
('Mini Lina 迷你饼干',  12.9, 'minilina-1.png', '食品',   '伊朗经典零食 · 一口一个',       250, 4.6, 280),
('Maz Maz 土豆条',      13.9, 'mazmaz-sticks-1.png', '食品',   '伊朗热销零食 · potato sticks',   180, 4.7, 210),
('北欧风台灯',          159,  NULL, '家居',   'LED护眼台灯',          150, 4.4, 400);
