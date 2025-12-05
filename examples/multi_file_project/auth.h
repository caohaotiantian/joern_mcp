/**
 * 认证模块 - 头文件
 * 
 * 调用链: authenticate -> check_password -> hash_str (utils)
 *                      -> query_user (database)
 */

#ifndef AUTH_H
#define AUTH_H

#include "database.h"

// 认证结果
typedef enum {
    AUTH_SUCCESS,
    AUTH_INVALID_USER,
    AUTH_INVALID_PASSWORD,
    AUTH_ACCOUNT_LOCKED,
    AUTH_ERROR
} AuthResult;

// 主认证函数 - 被 main 调用
int authenticate(const char* username, const char* password);

// 密码检查 - 被 authenticate 调用
int check_password(const char* username, const char* password);

// 验证密码哈希
int verify_password_hash(const char* password, const char* stored_hash);

// 权限检查 - 被 handle_request 调用
int check_permission(UserInfo* user, const char* action);

// 会话管理
char* create_session(const char* username);
int validate_session(const char* session_token);
void destroy_session(const char* session_token);

// 失败计数
int get_failed_attempts(const char* username);
void increment_failed_attempts(const char* username);
void reset_failed_attempts(const char* username);

#endif // AUTH_H

