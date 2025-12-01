/*
 * 工具函数实现
 */

#include "utils.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

/* 内部函数声明 */
static void internal_log(const char *prefix, const char *msg);
static int validate_data(const char *data, size_t length);

/**
 * 处理数据
 */
int process_data(const char *data, size_t length) {
    if (data == NULL || length == 0) {
        return -1;
    }

    // 验证数据
    if (!validate_data(data, length)) {
        log_message("ERROR", "Data validation failed");
        return -2;
    }

    // 处理数据（简单示例）
    char temp_buffer[1024];
    if (length < sizeof(temp_buffer)) {
        memcpy(temp_buffer, data, length);
        temp_buffer[length] = '\0';
        
        // 这里可能有处理逻辑
        internal_log("PROCESS", temp_buffer);
    }

    return 0;
}

/**
 * 记录日志消息
 */
void log_message(const char *level, const char *message) {
    if (level == NULL || message == NULL) {
        return;
    }

    time_t now = time(NULL);
    char time_str[64];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", localtime(&now));

    fprintf(stderr, "[%s] %s: %s\n", time_str, level, message);
}

/**
 * 内部日志函数
 */
static void internal_log(const char *prefix, const char *msg) {
    if (prefix != NULL && msg != NULL) {
        printf("%s: %s\n", prefix, msg);
    }
}

/**
 * 验证数据
 */
static int validate_data(const char *data, size_t length) {
    if (data == NULL || length == 0) {
        return 0;
    }

    // 简单验证：检查是否包含NULL字节
    for (size_t i = 0; i < length; i++) {
        if (data[i] == '\0') {
            return 0;
        }
    }

    return 1;
}

/**
 * 不安全的字符串复制
 */
char* unsafe_strcpy(char *dest, const char *src) {
    // VULNERABLE: 没有边界检查
    return strcpy(dest, src);
}

/**
 * 安全的字符串复制
 */
int safe_strcpy(char *dest, const char *src, size_t size) {
    if (dest == NULL || src == NULL || size == 0) {
        return -1;
    }

    size_t src_len = strlen(src);
    if (src_len >= size) {
        // 源字符串太长
        return -2;
    }

    strncpy(dest, src, size - 1);
    dest[size - 1] = '\0';

    return 0;
}

/**
 * 解析配置文件
 */
int parse_config(const char *filename) {
    if (filename == NULL) {
        return -1;
    }

    FILE *fp = fopen(filename, "r");
    if (fp == NULL) {
        log_message("ERROR", "Failed to open config file");
        return -2;
    }

    char line[512];
    int line_num = 0;

    while (fgets(line, sizeof(line), fp) != NULL) {
        line_num++;
        
        // 移除换行符
        line[strcspn(line, "\n")] = '\0';

        // 跳过注释和空行
        if (line[0] == '#' || line[0] == '\0') {
            continue;
        }

        // 解析配置行（简单示例：key=value）
        char *equals = strchr(line, '=');
        if (equals != NULL) {
            *equals = '\0';
            char *key = line;
            char *value = equals + 1;

            // 处理配置项
            internal_log("CONFIG", key);
            internal_log("VALUE", value);
        }
    }

    fclose(fp);
    return 0;
}

