/**
 * 数据库模块 - 实现
 * 
 * 调用关系:
 *   init_db -> log_message (utils.c)
 *   query_user -> exec_query -> log_message (utils.c)
 *   execute_action -> exec_update -> log_message (utils.c)
 */

#include "database.h"
#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 全局数据库连接
static DatabaseConnection* g_db_conn = NULL;

// 模拟用户数据
static UserInfo mock_users[] = {
    {1, "admin", "a1b2c3d4e5f67890", "admin@example.com", "admin", 1},
    {2, "user1", "1234567890abcdef", "user1@example.com", "user", 1},
    {3, "editor", "fedcba0987654321", "editor@example.com", "editor", 1},
    {0, NULL, NULL, NULL, NULL, 0}  // 终止标记
};

// 数据库初始化
int init_db(const char* host, int port, const char* database) {
    log_message("INFO", "Initializing database connection");
    log_formatted("DEBUG", "Connecting to %s:%d/%s", host, port, database);
    
    if (g_db_conn != NULL) {
        log_message("WARNING", "Database already initialized");
        return 0;
    }
    
    g_db_conn = (DatabaseConnection*)safe_malloc(sizeof(DatabaseConnection));
    g_db_conn->host = str_copy(host);
    g_db_conn->port = port;
    g_db_conn->database = str_copy(database);
    g_db_conn->connection = NULL;  // 模拟连接
    g_db_conn->is_connected = 1;
    
    log_message("INFO", "Database connection established");
    return 0;
}

void close_db(void) {
    log_message("INFO", "Closing database connection");
    
    if (g_db_conn != NULL) {
        safe_free(g_db_conn->host);
        safe_free(g_db_conn->database);
        safe_free(g_db_conn);
        g_db_conn = NULL;
    }
}

int is_db_connected(void) {
    return g_db_conn != NULL && g_db_conn->is_connected;
}

// 执行查询
QueryResult* exec_query(const char* sql) {
    log_message("DEBUG", "Executing query");
    log_formatted("DEBUG", "SQL: %s", sql);
    
    if (!is_db_connected()) {
        log_message("ERROR", "Database not connected");
        return NULL;
    }
    
    // 模拟查询执行
    QueryResult* result = (QueryResult*)safe_malloc(sizeof(QueryResult));
    result->row_count = 0;
    result->column_count = 0;
    result->data = NULL;
    
    log_message("DEBUG", "Query executed successfully");
    return result;
}

int exec_update(const char* sql) {
    log_message("DEBUG", "Executing update");
    log_formatted("DEBUG", "SQL: %s", sql);
    
    if (!is_db_connected()) {
        log_message("ERROR", "Database not connected");
        return -1;
    }
    
    // 模拟更新执行
    log_message("DEBUG", "Update executed successfully");
    return 1;  // 影响的行数
}

void free_query_result(QueryResult* result) {
    if (result != NULL) {
        if (result->data != NULL) {
            for (int i = 0; i < result->row_count; i++) {
                for (int j = 0; j < result->column_count; j++) {
                    safe_free(result->data[i][j]);
                }
                safe_free(result->data[i]);
            }
            safe_free(result->data);
        }
        safe_free(result);
    }
}

// 用户查询
UserInfo* query_user(const char* username) {
    log_formatted("DEBUG", "Querying user: %s", username);
    
    // 构建查询
    char sql[256];
    snprintf(sql, sizeof(sql), "SELECT * FROM users WHERE username = '%s'", username);
    
    // 执行查询
    QueryResult* result = exec_query(sql);
    if (result == NULL) {
        return NULL;
    }
    free_query_result(result);
    
    // 从模拟数据查找
    for (int i = 0; mock_users[i].username != NULL; i++) {
        if (str_equals(mock_users[i].username, username)) {
            UserInfo* user = (UserInfo*)safe_malloc(sizeof(UserInfo));
            user->id = mock_users[i].id;
            user->username = str_copy(mock_users[i].username);
            user->password_hash = str_copy(mock_users[i].password_hash);
            user->email = str_copy(mock_users[i].email);
            user->role = str_copy(mock_users[i].role);
            user->is_active = mock_users[i].is_active;
            
            log_message("DEBUG", "User found");
            return user;
        }
    }
    
    log_message("DEBUG", "User not found");
    return NULL;
}

UserInfo* query_user_by_id(int user_id) {
    log_formatted("DEBUG", "Querying user by ID: %d", user_id);
    
    char sql[256];
    snprintf(sql, sizeof(sql), "SELECT * FROM users WHERE id = %d", user_id);
    
    QueryResult* result = exec_query(sql);
    if (result == NULL) {
        return NULL;
    }
    free_query_result(result);
    
    // 从模拟数据查找
    for (int i = 0; mock_users[i].username != NULL; i++) {
        if (mock_users[i].id == user_id) {
            UserInfo* user = (UserInfo*)safe_malloc(sizeof(UserInfo));
            user->id = mock_users[i].id;
            user->username = str_copy(mock_users[i].username);
            user->password_hash = str_copy(mock_users[i].password_hash);
            user->email = str_copy(mock_users[i].email);
            user->role = str_copy(mock_users[i].role);
            user->is_active = mock_users[i].is_active;
            return user;
        }
    }
    
    return NULL;
}

void free_user_info(UserInfo* user) {
    if (user != NULL) {
        safe_free(user->username);
        safe_free(user->password_hash);
        safe_free(user->email);
        safe_free(user->role);
        safe_free(user);
    }
}

// 用户操作
int create_user(const char* username, const char* password, const char* email) {
    log_formatted("INFO", "Creating user: %s", username);
    
    // 计算密码哈希
    char* password_hash = hash_str(password);
    
    char sql[512];
    snprintf(sql, sizeof(sql), 
             "INSERT INTO users (username, password_hash, email, role, is_active) "
             "VALUES ('%s', '%s', '%s', 'user', 1)",
             username, password_hash, email);
    
    safe_free(password_hash);
    
    return exec_update(sql);
}

int update_user(int user_id, const char* field, const char* value) {
    log_formatted("INFO", "Updating user %d: %s = %s", user_id, field, value);
    
    char sql[256];
    snprintf(sql, sizeof(sql), 
             "UPDATE users SET %s = '%s' WHERE id = %d",
             field, value, user_id);
    
    return exec_update(sql);
}

int delete_user(int user_id) {
    log_formatted("INFO", "Deleting user: %d", user_id);
    
    char sql[128];
    snprintf(sql, sizeof(sql), "DELETE FROM users WHERE id = %d", user_id);
    
    return exec_update(sql);
}

// 执行用户操作
int execute_action(UserInfo* user, const char* action) {
    log_formatted("INFO", "Executing action '%s' for user '%s'", action, user->username);
    
    if (str_equals(action, "read")) {
        log_message("DEBUG", "Performing read operation");
        exec_query("SELECT * FROM data");
        return 0;
    }
    
    if (str_equals(action, "write")) {
        log_message("DEBUG", "Performing write operation");
        exec_update("INSERT INTO data (value) VALUES ('test')");
        return 0;
    }
    
    if (str_equals(action, "delete")) {
        log_message("DEBUG", "Performing delete operation");
        exec_update("DELETE FROM data WHERE id = 1");
        return 0;
    }
    
    log_formatted("WARNING", "Unknown action: %s", action);
    return -1;
}

// 事务管理
int begin_transaction(void) {
    log_message("DEBUG", "Beginning transaction");
    return exec_update("BEGIN TRANSACTION");
}

int commit_transaction(void) {
    log_message("DEBUG", "Committing transaction");
    return exec_update("COMMIT");
}

int rollback_transaction(void) {
    log_message("DEBUG", "Rolling back transaction");
    return exec_update("ROLLBACK");
}

// 预处理语句 (简化实现)
void* prepare_statement(const char* sql) {
    log_formatted("DEBUG", "Preparing statement: %s", sql);
    return str_copy(sql);
}

int bind_parameter(void* stmt, int index, const char* value) {
    log_formatted("DEBUG", "Binding parameter %d: %s", index, value);
    return 0;
}

QueryResult* execute_prepared(void* stmt) {
    log_message("DEBUG", "Executing prepared statement");
    return exec_query((const char*)stmt);
}

