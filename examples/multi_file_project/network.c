/**
 * 网络模块 - 实现
 * 
 * 调用关系:
 *   init_network -> log_message (utils.c)
 *   send_request -> log_message (utils.c)
 *   process_request -> authenticate (auth.c) -> query_user (database.c)
 */

#include "network.h"
#include "utils.h"
#include "auth.h"
#include "database.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 全局网络状态
static struct {
    char* bind_addr;
    int port;
    int server_fd;
    int is_running;
} g_network = {NULL, 0, -1, 0};

// 网络初始化
int init_network(const char* bind_addr, int port) {
    log_message("INFO", "Initializing network");
    log_formatted("DEBUG", "Binding to %s:%d", bind_addr, port);
    
    if (g_network.is_running) {
        log_message("WARNING", "Network already initialized");
        return 0;
    }
    
    g_network.bind_addr = str_copy(bind_addr);
    g_network.port = port;
    g_network.is_running = 1;
    
    log_message("INFO", "Network initialized successfully");
    return 0;
}

void close_network(void) {
    log_message("INFO", "Closing network");
    
    if (g_network.is_running) {
        stop_server();
        safe_free(g_network.bind_addr);
        g_network.is_running = 0;
    }
}

int is_network_ready(void) {
    return g_network.is_running;
}

// HTTP 客户端
HttpResponse* send_request(HttpRequest* request) {
    log_message("DEBUG", "Sending HTTP request");
    log_formatted("DEBUG", "URL: %s", request->url);
    
    if (!is_network_ready()) {
        log_message("ERROR", "Network not initialized");
        return NULL;
    }
    
    // 模拟 HTTP 请求
    HttpResponse* response = (HttpResponse*)safe_malloc(sizeof(HttpResponse));
    response->status_code = 200;
    response->headers = str_copy("Content-Type: application/json");
    response->body = str_copy("{\"status\": \"ok\"}");
    response->body_length = strlen(response->body);
    
    log_formatted("DEBUG", "Response status: %d", response->status_code);
    return response;
}

HttpResponse* http_get(const char* url) {
    log_formatted("DEBUG", "HTTP GET: %s", url);
    
    HttpRequest request = {
        .method = HTTP_GET,
        .url = (char*)url,
        .headers = NULL,
        .body = NULL,
        .body_length = 0
    };
    
    return send_request(&request);
}

HttpResponse* http_post(const char* url, const char* body) {
    log_formatted("DEBUG", "HTTP POST: %s", url);
    
    HttpRequest request = {
        .method = HTTP_POST,
        .url = (char*)url,
        .headers = NULL,
        .body = (char*)body,
        .body_length = body ? strlen(body) : 0
    };
    
    return send_request(&request);
}

void free_response(HttpResponse* response) {
    if (response != NULL) {
        safe_free(response->headers);
        safe_free(response->body);
        safe_free(response);
    }
}

// HTTP 服务器
int start_server(void) {
    log_message("INFO", "Starting HTTP server");
    
    if (!is_network_ready()) {
        log_message("ERROR", "Network not initialized");
        return -1;
    }
    
    // 模拟服务器启动
    g_network.server_fd = 100;  // 模拟文件描述符
    
    log_formatted("INFO", "Server listening on %s:%d", 
                  g_network.bind_addr, g_network.port);
    return 0;
}

int stop_server(void) {
    log_message("INFO", "Stopping HTTP server");
    
    if (g_network.server_fd >= 0) {
        g_network.server_fd = -1;
    }
    
    return 0;
}

void handle_connection(int client_fd) {
    log_formatted("DEBUG", "Handling connection: fd=%d", client_fd);
    
    // 模拟读取请求
    char raw_request[1024] = "GET /api/user HTTP/1.1\r\n";
    
    // 解析请求
    HttpRequest* request = parse_request(raw_request);
    if (request == NULL) {
        log_message("ERROR", "Failed to parse request");
        return;
    }
    
    // 处理请求
    HttpResponse* response = process_request(request);
    
    // 发送响应
    if (response != NULL) {
        char* response_str = serialize_response(response);
        log_formatted("DEBUG", "Sending response: %s", response_str);
        safe_free(response_str);
        free_response(response);
    }
    
    // 清理
    safe_free(request->url);
    safe_free(request);
}

// 请求处理
HttpResponse* process_request(HttpRequest* request) {
    log_message("DEBUG", "Processing request");
    
    HttpResponse* response = (HttpResponse*)safe_malloc(sizeof(HttpResponse));
    response->headers = str_copy("Content-Type: application/json");
    
    // 检查 URL 路由
    if (strstr(request->url, "/api/auth") != NULL) {
        log_message("DEBUG", "Handling auth endpoint");
        
        // 从请求体解析用户名和密码 (简化)
        if (authenticate("admin", "password")) {
            response->status_code = 200;
            response->body = str_copy("{\"status\": \"authenticated\"}");
        } else {
            response->status_code = 401;
            response->body = str_copy("{\"error\": \"unauthorized\"}");
        }
    }
    else if (strstr(request->url, "/api/user") != NULL) {
        log_message("DEBUG", "Handling user endpoint");
        
        // 查询用户信息
        UserInfo* user = query_user("admin");
        if (user != NULL) {
            response->status_code = 200;
            char body[256];
            snprintf(body, sizeof(body), 
                     "{\"id\": %d, \"username\": \"%s\", \"email\": \"%s\"}",
                     user->id, user->username, user->email);
            response->body = str_copy(body);
            free_user_info(user);
        } else {
            response->status_code = 404;
            response->body = str_copy("{\"error\": \"user not found\"}");
        }
    }
    else {
        response->status_code = 404;
        response->body = str_copy("{\"error\": \"not found\"}");
    }
    
    response->body_length = strlen(response->body);
    return response;
}

HttpRequest* parse_request(const char* raw_request) {
    log_message("DEBUG", "Parsing HTTP request");
    
    HttpRequest* request = (HttpRequest*)safe_malloc(sizeof(HttpRequest));
    
    // 简化解析：提取方法和 URL
    if (strncmp(raw_request, "GET", 3) == 0) {
        request->method = HTTP_GET;
    } else if (strncmp(raw_request, "POST", 4) == 0) {
        request->method = HTTP_POST;
    } else if (strncmp(raw_request, "PUT", 3) == 0) {
        request->method = HTTP_PUT;
    } else if (strncmp(raw_request, "DELETE", 6) == 0) {
        request->method = HTTP_DELETE;
    }
    
    // 提取 URL (简化)
    const char* url_start = strchr(raw_request, ' ');
    if (url_start != NULL) {
        url_start++;
        const char* url_end = strchr(url_start, ' ');
        if (url_end != NULL) {
            size_t url_len = url_end - url_start;
            request->url = (char*)safe_malloc(url_len + 1);
            strncpy(request->url, url_start, url_len);
            request->url[url_len] = '\0';
        }
    }
    
    request->headers = NULL;
    request->body = NULL;
    request->body_length = 0;
    
    return request;
}

char* serialize_response(HttpResponse* response) {
    log_message("DEBUG", "Serializing HTTP response");
    
    char* result = (char*)safe_malloc(1024);
    snprintf(result, 1024,
             "HTTP/1.1 %d OK\r\n%s\r\n\r\n%s",
             response->status_code,
             response->headers ? response->headers : "",
             response->body ? response->body : "");
    
    return result;
}

// 工具函数
char* url_encode(const char* str) {
    log_message("DEBUG", "URL encoding string");
    // 简化实现
    return str_copy(str);
}

char* url_decode(const char* str) {
    log_message("DEBUG", "URL decoding string");
    // 简化实现
    return str_copy(str);
}

void set_header(HttpRequest* req, const char* name, const char* value) {
    log_formatted("DEBUG", "Setting header: %s: %s", name, value);
    
    char header[256];
    snprintf(header, sizeof(header), "%s: %s", name, value);
    
    if (req->headers == NULL) {
        req->headers = str_copy(header);
    } else {
        char* new_headers = str_concat(req->headers, "\r\n");
        char* final_headers = str_concat(new_headers, header);
        safe_free(req->headers);
        safe_free(new_headers);
        req->headers = final_headers;
    }
}

