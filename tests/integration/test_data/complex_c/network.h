/*
 * 网络处理头文件
 */

#ifndef NETWORK_H
#define NETWORK_H

#include <stddef.h>

/**
 * 初始化网络
 * @return 0表示成功，非0表示错误
 */
int init_network(void);

/**
 * 清理网络资源
 */
void cleanup_network(void);

/**
 * 从网络接收数据
 * @return 接收到的数据（需要调用者释放），NULL表示失败
 */
char* receive_network_data(void);

/**
 * 发送网络数据
 * @param data 要发送的数据
 * @param length 数据长度
 * @return 0表示成功，非0表示错误
 */
int send_network_data(const char *data, size_t length);

/**
 * 建立网络连接
 * @param host 主机名
 * @param port 端口号
 * @return 0表示成功，非0表示错误
 */
int connect_to_server(const char *host, int port);

#endif /* NETWORK_H */

