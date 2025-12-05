/**
 * 多文件测试项目 - 主入口
 * 
 * 调用关系图:
 * 
 *                    ┌──────────────┐
 *                    │     main     │
 *                    └──────┬───────┘
 *           ┌───────────────┼───────────────┐
 *           ▼               ▼               ▼
 *    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
 *    │ authenticate│ │ handle_req  │ │  init_app   │
 *    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
 *           │               │               │
 *           ▼               ▼               ▼
 *    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
 *    │ check_passwd│ │ query_user  │ │  init_db    │
 *    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
 *           │               │               │
 *           ▼               ▼               ▼
 *    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
 *    │  hash_str   │ │ exec_query  │ │ log_message │
 *    └─────────────┘ └──────┬──────┘ └─────────────┘
 *                           │
 *                           ▼
 *                    ┌─────────────┐
 *                    │ log_message │
 *                    └─────────────┘
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "auth.h"
#include "database.h"
#include "network.h"
#include "utils.h"

// 初始化应用
int init_app(const char* config_path) {
    log_message("INFO", "Initializing application...");
    
    if (init_db("localhost", 5432, "mydb") != 0) {
        log_message("ERROR", "Failed to initialize database");
        return -1;
    }
    
    if (init_network("0.0.0.0", 8080) != 0) {
        log_message("ERROR", "Failed to initialize network");
        return -1;
    }
    
    log_message("INFO", "Application initialized successfully");
    return 0;
}

// 处理用户请求
int handle_request(const char* username, const char* action) {
    log_message("DEBUG", "Handling request");
    
    // 查询用户信息
    UserInfo* user = query_user(username);
    if (user == NULL) {
        log_message("WARNING", "User not found");
        return -1;
    }
    
    // 检查权限
    if (!check_permission(user, action)) {
        log_message("WARNING", "Permission denied");
        free_user_info(user);
        return -2;
    }
    
    // 执行操作
    int result = execute_action(user, action);
    free_user_info(user);
    
    return result;
}

// 主入口
int main(int argc, char* argv[]) {
    printf("=== Multi-File Test Project ===\n");
    
    // 初始化
    if (init_app("config.json") != 0) {
        fprintf(stderr, "Failed to initialize application\n");
        return 1;
    }
    
    // 处理认证
    if (argc >= 3) {
        const char* username = argv[1];
        const char* password = argv[2];
        
        printf("Authenticating user: %s\n", username);
        
        if (authenticate(username, password)) {
            printf("Authentication successful!\n");
            
            // 处理请求
            if (argc >= 4) {
                handle_request(username, argv[3]);
            }
        } else {
            printf("Authentication failed!\n");
            return 1;
        }
    }
    
    // 清理
    close_network();
    close_db();
    
    return 0;
}

