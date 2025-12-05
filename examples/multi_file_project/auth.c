/**
 * 认证模块 - 实现
 * 
 * 调用关系:
 *   authenticate 
 *     -> check_password 
 *       -> hash_str (utils.c)
 *       -> query_user (database.c)
 *     -> log_message (utils.c)
 */

#include "auth.h"
#include "database.h"
#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_FAILED_ATTEMPTS 5

// 静态存储失败尝试次数
static int failed_attempts[100] = {0};

// 主认证函数
int authenticate(const char* username, const char* password) {
    log_message("INFO", "Starting authentication");
    log_formatted("DEBUG", "Authenticating user: %s", username);
    
    // 检查失败次数
    int attempts = get_failed_attempts(username);
    if (attempts >= MAX_FAILED_ATTEMPTS) {
        log_message("WARNING", "Account locked due to too many failed attempts");
        return 0;
    }
    
    // 检查密码
    if (check_password(username, password)) {
        log_message("INFO", "Authentication successful");
        reset_failed_attempts(username);
        return 1;
    } else {
        log_message("WARNING", "Authentication failed");
        increment_failed_attempts(username);
        return 0;
    }
}

// 密码检查
int check_password(const char* username, const char* password) {
    log_message("DEBUG", "Checking password");
    
    // 从数据库查询用户
    UserInfo* user = query_user(username);
    if (user == NULL) {
        log_message("WARNING", "User not found in database");
        return 0;
    }
    
    // 计算密码哈希并比较
    char* password_hash = hash_str(password);
    int result = verify_password_hash(password_hash, user->password_hash);
    
    safe_free(password_hash);
    free_user_info(user);
    
    return result;
}

// 验证密码哈希
int verify_password_hash(const char* password, const char* stored_hash) {
    log_message("DEBUG", "Verifying password hash");
    return str_equals(password, stored_hash);
}

// 权限检查
int check_permission(UserInfo* user, const char* action) {
    log_formatted("DEBUG", "Checking permission for action: %s", action);
    
    if (user == NULL || action == NULL) {
        return 0;
    }
    
    // 管理员拥有所有权限
    if (str_equals(user->role, "admin")) {
        return 1;
    }
    
    // 检查特定权限
    if (str_equals(action, "read")) {
        return 1;  // 所有用户都可以读
    }
    
    if (str_equals(action, "write")) {
        return str_equals(user->role, "editor") || str_equals(user->role, "admin");
    }
    
    if (str_equals(action, "delete")) {
        return str_equals(user->role, "admin");
    }
    
    return 0;
}

// 会话管理
char* create_session(const char* username) {
    log_formatted("DEBUG", "Creating session for user: %s", username);
    
    // 生成会话令牌
    char session_data[256];
    snprintf(session_data, sizeof(session_data), "%s:%ld", username, time(NULL));
    
    char* token = hash_str(session_data);
    
    // 存储会话 (简化实现)
    log_formatted("INFO", "Session created: %s", token);
    
    return token;
}

int validate_session(const char* session_token) {
    log_message("DEBUG", "Validating session");
    
    if (session_token == NULL || strlen(session_token) == 0) {
        return 0;
    }
    
    // 简化实现：假设所有非空令牌都有效
    return 1;
}

void destroy_session(const char* session_token) {
    log_message("DEBUG", "Destroying session");
    // 简化实现：清理会话数据
}

// 失败计数管理
int get_failed_attempts(const char* username) {
    unsigned long hash = hash_string(username);
    return failed_attempts[hash % 100];
}

void increment_failed_attempts(const char* username) {
    log_message("DEBUG", "Incrementing failed attempts");
    unsigned long hash = hash_string(username);
    failed_attempts[hash % 100]++;
}

void reset_failed_attempts(const char* username) {
    log_message("DEBUG", "Resetting failed attempts");
    unsigned long hash = hash_string(username);
    failed_attempts[hash % 100] = 0;
}

