/**
 * 数据库模块 - 头文件
 * 
 * 调用链: query_user -> exec_query -> log_message (utils)
 *         init_db -> log_message (utils)
 */

#ifndef DATABASE_H
#define DATABASE_H

// 用户信息结构
typedef struct {
    int id;
    char* username;
    char* password_hash;
    char* email;
    char* role;
    int is_active;
} UserInfo;

// 数据库连接信息
typedef struct {
    char* host;
    int port;
    char* database;
    void* connection;
    int is_connected;
} DatabaseConnection;

// 查询结果
typedef struct {
    int row_count;
    int column_count;
    char*** data;
} QueryResult;

// 数据库初始化和关闭
int init_db(const char* host, int port, const char* database);
void close_db(void);
int is_db_connected(void);

// 查询执行 - 核心函数
QueryResult* exec_query(const char* sql);
int exec_update(const char* sql);
void free_query_result(QueryResult* result);

// 用户查询 - 被 auth.c 调用
UserInfo* query_user(const char* username);
UserInfo* query_user_by_id(int user_id);
void free_user_info(UserInfo* user);

// 用户操作
int create_user(const char* username, const char* password, const char* email);
int update_user(int user_id, const char* field, const char* value);
int delete_user(int user_id);

// 执行用户操作 - 被 main.c 调用
int execute_action(UserInfo* user, const char* action);

// 事务管理
int begin_transaction(void);
int commit_transaction(void);
int rollback_transaction(void);

// 预处理语句
void* prepare_statement(const char* sql);
int bind_parameter(void* stmt, int index, const char* value);
QueryResult* execute_prepared(void* stmt);

#endif // DATABASE_H

