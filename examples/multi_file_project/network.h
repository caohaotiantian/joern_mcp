/**
 * 网络模块 - 头文件
 * 
 * 调用链: init_network -> log_message (utils)
 *         send_request -> log_message (utils)
 */

#ifndef NETWORK_H
#define NETWORK_H

#include <stddef.h>

// HTTP 方法
typedef enum {
    HTTP_GET,
    HTTP_POST,
    HTTP_PUT,
    HTTP_DELETE
} HttpMethod;

// HTTP 请求
typedef struct {
    HttpMethod method;
    char* url;
    char* headers;
    char* body;
    size_t body_length;
} HttpRequest;

// HTTP 响应
typedef struct {
    int status_code;
    char* headers;
    char* body;
    size_t body_length;
} HttpResponse;

// 网络初始化和关闭
int init_network(const char* bind_addr, int port);
void close_network(void);
int is_network_ready(void);

// HTTP 客户端
HttpResponse* send_request(HttpRequest* request);
HttpResponse* http_get(const char* url);
HttpResponse* http_post(const char* url, const char* body);
void free_response(HttpResponse* response);

// HTTP 服务器
int start_server(void);
int stop_server(void);
void handle_connection(int client_fd);

// 请求处理
HttpResponse* process_request(HttpRequest* request);
HttpRequest* parse_request(const char* raw_request);
char* serialize_response(HttpResponse* response);

// 工具函数
char* url_encode(const char* str);
char* url_decode(const char* str);
void set_header(HttpRequest* req, const char* name, const char* value);

#endif // NETWORK_H

