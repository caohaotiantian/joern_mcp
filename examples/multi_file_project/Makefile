# 多文件测试项目 Makefile

CC = gcc
CFLAGS = -Wall -Wextra -g -I.
LDFLAGS = 

# 源文件
SRCS = main.c auth.c database.c network.c utils.c
OBJS = $(SRCS:.c=.o)
TARGET = app

# 默认目标
all: $(TARGET)

# 链接
$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^

# 编译规则
%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

# 依赖关系
main.o: main.c auth.h database.h network.h utils.h
auth.o: auth.c auth.h database.h utils.h
database.o: database.c database.h utils.h
network.o: network.c network.h utils.h auth.h database.h
utils.o: utils.c utils.h

# 清理
clean:
	rm -f $(OBJS) $(TARGET)

# 重新编译
rebuild: clean all

.PHONY: all clean rebuild

