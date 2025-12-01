/*
 * 工具函数头文件
 */

#ifndef UTILS_H
#define UTILS_H

#include <stddef.h>

/* 日志级别 */
#define LOG_LEVEL_INFO  0
#define LOG_LEVEL_WARN  1
#define LOG_LEVEL_ERROR 2

/**
 * 处理数据
 * @param data 数据指针
 * @param length 数据长度
 * @return 0表示成功，非0表示错误
 */
int process_data(const char *data, size_t length);

/**
 * 记录日志消息
 * @param level 日志级别
 * @param message 日志消息
 */
void log_message(const char *level, const char *message);

/**
 * 字符串复制（不安全版本）
 * @param dest 目标缓冲区
 * @param src 源字符串
 * @return 目标指针
 */
char* unsafe_strcpy(char *dest, const char *src);

/**
 * 字符串复制（安全版本）
 * @param dest 目标缓冲区
 * @param src 源字符串
 * @param size 目标缓冲区大小
 * @return 0表示成功，非0表示错误
 */
int safe_strcpy(char *dest, const char *src, size_t size);

/**
 * 解析配置文件
 * @param filename 配置文件名
 * @return 0表示成功，非0表示错误
 */
int parse_config(const char *filename);

#endif /* UTILS_H */

