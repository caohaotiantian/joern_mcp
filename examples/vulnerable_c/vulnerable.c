/**
 * 示例：包含多种漏洞的C代码
 * 仅用于演示Joern MCP Server的漏洞检测功能
 * 请勿在实际项目中使用此代码！
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// ============================================
// 漏洞1: 命令注入 (CWE-78)
// ============================================
void command_injection(char *user_input) {
    char cmd[256];
    // 危险：直接将用户输入拼接到命令中
    sprintf(cmd, "ls %s", user_input);
    system(cmd);  // 攻击者可以注入: "; rm -rf /"
}

// ============================================
// 漏洞2: 缓冲区溢出 (CWE-120)
// ============================================
void buffer_overflow(char *input) {
    char buffer[32];
    // 危险：使用strcpy不检查长度
    strcpy(buffer, input);  // 如果input超过32字节，将溢出
    printf("Buffer: %s\n", buffer);
}

// ============================================
// 漏洞3: 格式化字符串漏洞 (CWE-134)
// ============================================
void format_string(char *user_input) {
    // 危险：用户输入直接作为格式化字符串
    printf(user_input);  // 攻击者可以输入 "%x%x%x" 泄露栈信息
}

// ============================================
// 漏洞4: 不安全的gets (CWE-120)
// ============================================
void unsafe_gets() {
    char buffer[64];
    printf("Enter your name: ");
    // 危险：gets不检查缓冲区大小
    gets(buffer);  // 已废弃的函数，永远不要使用
    printf("Hello, %s!\n", buffer);
}

// ============================================
// 漏洞5: SQL注入模拟 (CWE-89)
// ============================================
void sql_query(char *username) {
    char query[512];
    // 危险：直接拼接用户输入到SQL查询
    sprintf(query, "SELECT * FROM users WHERE name='%s'", username);
    // 假设这里执行SQL查询
    // exec_sql(query);  // 攻击者可以输入: ' OR '1'='1
    printf("Query: %s\n", query);
}

// ============================================
// 漏洞6: 路径遍历 (CWE-22)
// ============================================
void path_traversal(char *filename) {
    char path[256];
    // 危险：未验证文件名
    sprintf(path, "/var/data/%s", filename);
    // 攻击者可以输入: "../../../etc/passwd"
    FILE *f = fopen(path, "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            printf("%s", line);
        }
        fclose(f);
    }
}

// ============================================
// 漏洞7: 整数溢出导致的缓冲区问题
// ============================================
void integer_overflow(int size) {
    if (size < 100) {  // 检查看起来是安全的
        // 但如果size是负数呢？
        char *buffer = malloc(size);
        if (buffer) {
            memset(buffer, 0, size);  // 可能导致问题
            free(buffer);
        }
    }
}

// ============================================
// 安全的实现示例
// ============================================
void safe_copy(const char *input) {
    char buffer[32];
    // 安全：使用strncpy限制长度
    strncpy(buffer, input, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';
    printf("Safe buffer: %s\n", buffer);
}

void safe_command(const char *filename) {
    // 安全：验证输入只包含字母数字
    for (int i = 0; filename[i] != '\0'; i++) {
        char c = filename[i];
        if (!((c >= 'a' && c <= 'z') || 
              (c >= 'A' && c <= 'Z') || 
              (c >= '0' && c <= '9') ||
              c == '.' || c == '_')) {
            printf("Invalid filename\n");
            return;
        }
    }
    
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "cat %s", filename);
    system(cmd);
}

// ============================================
// 调用链示例
// ============================================
void process_data(char *data) {
    buffer_overflow(data);  // 调用有漏洞的函数
}

void handle_request(char *request) {
    process_data(request);  // 中间调用
}

void server_main() {
    char request[1024];
    printf("Enter request: ");
    fgets(request, sizeof(request), stdin);
    handle_request(request);  // 入口点
}

// ============================================
// 主函数
// ============================================
int main(int argc, char *argv[]) {
    printf("=== Vulnerable C Demo ===\n\n");
    
    if (argc < 2) {
        printf("Usage: %s <command>\n", argv[0]);
        printf("Commands:\n");
        printf("  cmd <input>     - Command injection demo\n");
        printf("  buffer <input>  - Buffer overflow demo\n");
        printf("  format <input>  - Format string demo\n");
        printf("  gets            - Unsafe gets demo\n");
        printf("  sql <username>  - SQL injection demo\n");
        printf("  path <filename> - Path traversal demo\n");
        printf("  server          - Server demo (call chain)\n");
        return 1;
    }
    
    if (strcmp(argv[1], "cmd") == 0 && argc > 2) {
        command_injection(argv[2]);
    } else if (strcmp(argv[1], "buffer") == 0 && argc > 2) {
        buffer_overflow(argv[2]);
    } else if (strcmp(argv[1], "format") == 0 && argc > 2) {
        format_string(argv[2]);
    } else if (strcmp(argv[1], "gets") == 0) {
        unsafe_gets();
    } else if (strcmp(argv[1], "sql") == 0 && argc > 2) {
        sql_query(argv[2]);
    } else if (strcmp(argv[1], "path") == 0 && argc > 2) {
        path_traversal(argv[2]);
    } else if (strcmp(argv[1], "server") == 0) {
        server_main();
    } else {
        printf("Unknown command\n");
    }
    
    return 0;
}

