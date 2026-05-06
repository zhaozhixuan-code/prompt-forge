/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80039
 Source Host           : localhost:3306
 Source Schema         : zzx_ai_code

 Target Server Type    : MySQL
 Target Server Version : 80039
 File Encoding         : 65001

 Date: 06/05/2026 21:27:17
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for app
-- ----------------------------
DROP TABLE IF EXISTS `app`;
CREATE TABLE `app`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `appName` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '应用名称',
  `cover` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '应用封面',
  `initPrompt` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '应用初始化的 prompt',
  `codeGenType` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '代码生成类型（枚举）',
  `deployKey` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '部署标识',
  `deployedTime` datetime NULL DEFAULT NULL COMMENT '部署时间',
  `priority` int NOT NULL DEFAULT 0 COMMENT '优先级',
  `userId` bigint NOT NULL COMMENT '创建用户id',
  `editTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '编辑时间',
  `createTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `isDelete` tinyint NOT NULL DEFAULT 0 COMMENT '是否删除',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_deployKey`(`deployKey` ASC) USING BTREE,
  INDEX `idx_appName`(`appName` ASC) USING BTREE,
  INDEX `idx_userId`(`userId` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 390402563977154561 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '应用' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for chat_group
-- ----------------------------
DROP TABLE IF EXISTS `chat_group`;
CREATE TABLE `chat_group`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `appId` bigint NOT NULL COMMENT '应用id',
  `roomName` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '房间名称',
  `creatorId` bigint NOT NULL COMMENT '创建者用户ID',
  `createTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `isDelete` tinyint NOT NULL DEFAULT 0 COMMENT '是否删除',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_app`(`appId` ASC) USING BTREE,
  INDEX `idx_creatorId`(`creatorId` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '对话房间' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for chat_group_member
-- ----------------------------
DROP TABLE IF EXISTS `chat_group_member`;
CREATE TABLE `chat_group_member`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `groupId` bigint NOT NULL COMMENT '群组ID',
  `userId` bigint NOT NULL COMMENT '用户ID',
  `role` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'member' COMMENT '成员角色：admin-管理员，member-普通成员',
  `joinTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
  `quitTime` datetime NULL DEFAULT NULL COMMENT '退出时间',
  `isQuit` tinyint NOT NULL DEFAULT 0 COMMENT '是否退出：0-未退出，1-已退出',
  `createTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `isDelete` tinyint NOT NULL DEFAULT 0 COMMENT '是否删除',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_groupId_userId`(`groupId` ASC, `userId` ASC) USING BTREE,
  INDEX `idx_groupId`(`groupId` ASC) USING BTREE,
  INDEX `idx_userId`(`userId` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '群组成员表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for chat_history
-- ----------------------------
DROP TABLE IF EXISTS `chat_history`;
CREATE TABLE `chat_history`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息',
  `messageType` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'user/ai',
  `appId` bigint NOT NULL COMMENT '应用id',
  `groupId` bigint NULL DEFAULT NULL COMMENT '群组ID（关联chat_group.id，null表示单人会话）',
  `migrateFlag` tinyint NOT NULL DEFAULT 0 COMMENT '迁移标记：0-原生消息，1-从单人同步到群聊的消息',
  `userId` bigint NOT NULL COMMENT '创建用户id',
  `createTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `isDelete` tinyint NOT NULL DEFAULT 0 COMMENT '是否删除',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_appId`(`appId` ASC) USING BTREE,
  INDEX `idx_createTime`(`createTime` ASC) USING BTREE,
  INDEX `idx_appId_createTime`(`appId` ASC, `createTime` ASC) USING BTREE,
  INDEX `idx_single_chat`(`appId` ASC, `userId` ASC, `createTime` ASC) USING BTREE,
  INDEX `idx_group_chat`(`groupId` ASC, `appId` ASC, `createTime` ASC) USING BTREE,
  INDEX `idx_migrateFlag`(`migrateFlag` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 390409154092765185 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '对话历史' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `userAccount` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号',
  `userPassword` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码',
  `userName` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `userAvatar` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户头像',
  `userProfile` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户简介',
  `userRole` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user' COMMENT '用户角色：user/admin',
  `editTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '编辑时间',
  `createTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `isDelete` tinyint NOT NULL DEFAULT 0 COMMENT '是否删除',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_userAccount`(`userAccount` ASC) USING BTREE,
  INDEX `idx_userName`(`userName` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1991139811048484869 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
