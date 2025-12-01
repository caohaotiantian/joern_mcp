/*
 * 网络处理实现
 */

#include "network.h"
#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 全局网络状态 */
static int network_initialized = 0;
static int connection_fd = -1;

/* 内部函数 */
static int validate_host(const char *host);
static char* read_from_socket(int fd);

/**
 * 初始化网络
 */
int init_network(void) {
    if (network_initialized) {
        log_message("WARN", "Network already initialized");
        return 0;
    }

    // 初始化网络库（简化示例）
    log_message("INFO", "Initializing network...");

    network_initialized = 1;
    return 0;
}

/**
 * 清理网络资源
 */
void cleanup_network(void) {
    if (!network_initialized) {
        return;
    }

    log_message("INFO", "Cleaning up network resources...");

    if (connection_fd >= 0) {
        // 关闭连接（简化）
        connection_fd = -1;
    }

    network_initialized = 0;
}

/**
 * 从网络接收数据
 */
char* receive_network_data(void) {
    if (!network_initialized) {
        log_message("ERROR", "Network not initialized");
        return NULL;
    }

    if (connection_fd < 0) {
        log_message("ERROR", "Not connected");
        return NULL;
    }

    // 从socket读取数据（简化示例）
    char *data = read_from_socket(connection_fd);
    if (data == NULL) {
        log_message("ERROR", "Failed to read from socket");
        return NULL;
    }

    return data;
}

/**
 * 发送网络数据
 */
int send_network_data(const char *data, size_t length) {
    if (!network_initialized) {
        log_message("ERROR", "Network not initialized");
        return -1;
    }

    if (data == NULL || length == 0) {
        return -2;
    }

    if (connection_fd < 0) {
        log_message("ERROR", "Not connected");
        return -3;
    }

    // 发送数据（简化示例）
    log_message("INFO", "Sending network data...");

    return 0;
}

/**
 * 建立网络连接
 */
int connect_to_server(const char *host, int port) {
    if (!network_initialized) {
        log_message("ERROR", "Network not initialized");
        return -1;
    }

    if (host == NULL || port <= 0 || port > 65535) {
        log_message("ERROR", "Invalid host or port");
        return -2;
    }

    // 验证主机名
    if (!validate_host(host)) {
        log_message("ERROR", "Invalid host name");
        return -3;
    }

    // 建立连接（简化示例）
    char message[256];
    sprintf(message, "Connecting to %s:%d", host, port);  // VULNERABLE: sprintf
    log_message("INFO", message);

    // 模拟连接
    connection_fd = 42;  // 假的文件描述符

    return 0;
}

/**
 * 验证主机名
 */
static int validate_host(const char *host) {
    if (host == NULL) {
        return 0;
    }

    size_t len = strlen(host);
    if (len == 0 || len > 255) {
        return 0;
    }

    // 简单验证：检查是否包含有效字符
    for (size_t i = 0; i < len; i++) {
        char c = host[i];
        if (!((c >= 'a' && c <= 'z') ||
              (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') ||
              c == '.' || c == '-')) {
            return 0;
        }
    }

    return 1;
}

/**
 * 从socket读取数据
 */
static char* read_from_socket(int fd) {
    if (fd < 0) {
        return NULL;
    }

    // 分配缓冲区
    char *buffer = (char*)malloc(1024);
    if (buffer == NULL) {
        log_message("ERROR", "Memory allocation failed");
        return NULL;
    }

    // 模拟读取数据
    strcpy(buffer, "network_data_example");  // VULNERABLE: strcpy

    return buffer;
}

