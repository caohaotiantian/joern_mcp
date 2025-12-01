/*
 * 复杂C项目示例 - 主程序
 * 用于测试多文件、复杂调用链、数据流分析
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils.h"
#include "network.h"

#define BUFFER_SIZE 1024

/* 全局变量 */
char global_buffer[BUFFER_SIZE];
int error_count = 0;

/* 函数声明 */
static void internal_handler(char *data);
static int validate_input(const char *input);

/**
 * 主函数 - 程序入口
 */
int main(int argc, char *argv[]) {
    char local_buffer[256];
    char *user_input = NULL;
    int result = 0;

    printf("Starting complex application...\n");

    // 初始化网络
    if (init_network() != 0) {
        fprintf(stderr, "Failed to initialize network\n");
        return 1;
    }

    // 处理命令行参数
    if (argc > 1) {
        user_input = argv[1];
        
        // 验证输入
        if (!validate_input(user_input)) {
            fprintf(stderr, "Invalid input: %s\n", user_input);
            cleanup_network();
            return 2;
        }

        // 复制到本地缓冲区（潜在的缓冲区溢出）
        strcpy(local_buffer, user_input);  // VULNERABLE: 缓冲区溢出
        
        // 处理输入
        result = process_data(local_buffer, strlen(local_buffer));
    } else {
        // 从网络接收数据
        char *network_data = receive_network_data();
        if (network_data != NULL) {
            internal_handler(network_data);
            free(network_data);
        }
    }

    // 记录日志
    log_message("INFO", "Processing completed");

    // 清理
    cleanup_network();

    return result;
}

/**
 * 验证输入数据
 */
static int validate_input(const char *input) {
    if (input == NULL) {
        return 0;
    }

    // 检查长度
    size_t len = strlen(input);
    if (len == 0 || len > 255) {
        return 0;
    }

    // 检查特殊字符（简单检查）
    for (size_t i = 0; i < len; i++) {
        if (input[i] == '\0') {
            break;
        }
        // 这里应该有更严格的检查
    }

    return 1;
}

/**
 * 内部处理函数
 */
static void internal_handler(char *data) {
    if (data == NULL) {
        error_count++;
        return;
    }

    // 处理数据（使用全局缓冲区）
    if (strlen(data) < BUFFER_SIZE) {
        strcpy(global_buffer, data);  // VULNERABLE: 使用全局缓冲区
        process_data(global_buffer, strlen(global_buffer));
    } else {
        fprintf(stderr, "Data too large: %zu bytes\n", strlen(data));
        error_count++;
    }
}

/**
 * 错误处理函数
 */
void handle_error(int error_code, const char *message) {
    error_count++;
    fprintf(stderr, "Error %d: %s\n", error_code, message);
    
    // 严重错误时退出
    if (error_code >= 100) {
        cleanup_network();
        exit(error_code);
    }
}

/**
 * 命令注入漏洞示例
 */
void execute_command(const char *user_cmd) {
    char command[512];
    
    // VULNERABLE: 命令注入
    sprintf(command, "sh -c %s", user_cmd);
    system(command);  // 危险：执行用户提供的命令
}

/**
 * SQL注入漏洞示例（模拟）
 */
void query_database(const char *username) {
    char query[256];
    
    // VULNERABLE: SQL注入（模拟）
    sprintf(query, "SELECT * FROM users WHERE name='%s'", username);
    printf("Executing query: %s\n", query);
}

