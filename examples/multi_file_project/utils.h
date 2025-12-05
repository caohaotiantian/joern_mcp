/**
 * 工具函数模块 - 头文件
 * 
 * 提供基础工具函数，被所有其他模块调用
 */

#ifndef UTILS_H
#define UTILS_H

#include <stddef.h>

// 日志级别
typedef enum {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARNING,
    LOG_ERROR
} LogLevel;

// 日志函数 - 被所有模块调用
void log_message(const char* level, const char* message);
void log_formatted(const char* level, const char* format, ...);

// 字符串工具
char* str_copy(const char* src);
char* str_concat(const char* s1, const char* s2);
int str_equals(const char* s1, const char* s2);
char* str_trim(char* str);

// 内存工具
void* safe_malloc(size_t size);
void* safe_realloc(void* ptr, size_t size);
void safe_free(void* ptr);

// 哈希函数
unsigned long hash_string(const char* str);
char* hash_str(const char* input);  // 返回哈希字符串

// 配置读取
char* read_config(const char* key);
int parse_int_config(const char* key, int default_val);

#endif // UTILS_H

