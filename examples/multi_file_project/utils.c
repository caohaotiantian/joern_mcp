/**
 * 工具函数模块 - 实现
 */

#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <time.h>

// 日志函数实现
void log_message(const char* level, const char* message) {
    time_t now = time(NULL);
    struct tm* tm_info = localtime(&now);
    char time_str[26];
    strftime(time_str, 26, "%Y-%m-%d %H:%M:%S", tm_info);
    
    printf("[%s] [%s] %s\n", time_str, level, message);
}

void log_formatted(const char* level, const char* format, ...) {
    char buffer[1024];
    va_list args;
    va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    
    log_message(level, buffer);
}

// 字符串工具实现
char* str_copy(const char* src) {
    if (src == NULL) return NULL;
    
    size_t len = strlen(src);
    char* dest = (char*)safe_malloc(len + 1);
    strcpy(dest, src);
    return dest;
}

char* str_concat(const char* s1, const char* s2) {
    if (s1 == NULL) return str_copy(s2);
    if (s2 == NULL) return str_copy(s1);
    
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char* result = (char*)safe_malloc(len1 + len2 + 1);
    
    strcpy(result, s1);
    strcat(result, s2);
    return result;
}

int str_equals(const char* s1, const char* s2) {
    if (s1 == NULL && s2 == NULL) return 1;
    if (s1 == NULL || s2 == NULL) return 0;
    return strcmp(s1, s2) == 0;
}

char* str_trim(char* str) {
    if (str == NULL) return NULL;
    
    // 去除前导空格
    while (*str == ' ' || *str == '\t') str++;
    
    // 去除尾部空格
    char* end = str + strlen(str) - 1;
    while (end > str && (*end == ' ' || *end == '\t')) end--;
    *(end + 1) = '\0';
    
    return str;
}

// 内存工具实现
void* safe_malloc(size_t size) {
    void* ptr = malloc(size);
    if (ptr == NULL) {
        log_message("ERROR", "Memory allocation failed");
        exit(1);
    }
    return ptr;
}

void* safe_realloc(void* ptr, size_t size) {
    void* new_ptr = realloc(ptr, size);
    if (new_ptr == NULL && size > 0) {
        log_message("ERROR", "Memory reallocation failed");
        exit(1);
    }
    return new_ptr;
}

void safe_free(void* ptr) {
    if (ptr != NULL) {
        free(ptr);
    }
}

// 哈希函数实现 (DJB2 算法)
unsigned long hash_string(const char* str) {
    unsigned long hash = 5381;
    int c;
    
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c;
    }
    
    return hash;
}

char* hash_str(const char* input) {
    unsigned long hash = hash_string(input);
    char* result = (char*)safe_malloc(17);
    snprintf(result, 17, "%016lx", hash);
    return result;
}

// 配置读取实现
static char config_buffer[256];

char* read_config(const char* key) {
    // 简化实现：从环境变量读取
    char* value = getenv(key);
    if (value != NULL) {
        strncpy(config_buffer, value, sizeof(config_buffer) - 1);
        return config_buffer;
    }
    return NULL;
}

int parse_int_config(const char* key, int default_val) {
    char* value = read_config(key);
    if (value == NULL) return default_val;
    return atoi(value);
}

