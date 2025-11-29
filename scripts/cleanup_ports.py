#!/usr/bin/env python
"""清理Joern相关的端口占用"""

import subprocess
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from joern_mcp.utils.port_utils import get_port_info, kill_process_on_port


def check_joern_ports():
    """检查Joern常用端口范围"""
    logger.info("检查Joern Server常用端口...")

    # Joern常用端口范围
    port_ranges = [
        (8080, 8090, "默认端口范围"),
        (8100, 8200, "测试端口范围"),
        (20000, 30000, "随机端口范围"),
    ]

    occupied_ports = []

    for start, end, desc in port_ranges:
        logger.info(f"扫描 {desc}: {start}-{end}")

        for port in range(start, min(end, start + 100)):  # 限制扫描数量
            info = get_port_info(port)
            if info:
                logger.warning(f"端口 {port} 被占用: {info}")
                occupied_ports.append((port, info))

    return occupied_ports


def kill_joern_processes():
    """终止所有Joern相关进程"""
    logger.info("查找Joern进程...")

    try:
        # macOS/Linux
        result = subprocess.run(
            ["pgrep", "-f", "joern"], capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            logger.info(f"找到 {len(pids)} 个Joern进程")

            for pid in pids:
                try:
                    logger.info(f"终止进程 PID: {pid}")
                    subprocess.run(["kill", "-9", pid], timeout=5)
                except Exception as e:
                    logger.error(f"无法终止进程 {pid}: {e}")

            return True

        else:
            logger.info("未找到Joern进程")
            return False

    except Exception as e:
        logger.error(f"查找Joern进程失败: {e}")
        return False


def cleanup_specific_ports(ports: list[int]):
    """清理指定的端口"""
    for port in ports:
        logger.info(f"清理端口 {port}...")
        info = get_port_info(port)

        if info:
            logger.warning(f"端口 {port} 被占用: {info}")
            if kill_process_on_port(port):
                logger.success(f"端口 {port} 已清理")
            else:
                logger.error(f"无法清理端口 {port}")
        else:
            logger.info(f"端口 {port} 未被占用")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Joern端口清理工具")
    logger.info("=" * 60)

    # 1. 检查常用端口
    occupied = check_joern_ports()

    if not occupied:
        logger.success("✅ 未发现占用的端口")
    else:
        logger.warning(f"⚠️  发现 {len(occupied)} 个被占用的端口")

    # 2. 查找并终止Joern进程
    logger.info("\n" + "=" * 60)
    logger.info("清理Joern进程")
    logger.info("=" * 60)

    if kill_joern_processes():
        logger.success("✅ Joern进程已清理")
    else:
        logger.info("ℹ️  无需清理")

    # 3. 清理特定端口（如果有命令行参数）
    if len(sys.argv) > 1:
        logger.info("\n" + "=" * 60)
        logger.info("清理指定端口")
        logger.info("=" * 60)

        ports = [int(p) for p in sys.argv[1:]]
        cleanup_specific_ports(ports)

    logger.info("\n" + "=" * 60)
    logger.success("✅ 清理完成")
    logger.info("=" * 60)
    logger.info("\n提示:")
    logger.info("  - 如需清理特定端口: python cleanup_ports.py 8080 8081")
    logger.info("  - 如需查看端口占用: lsof -i :端口号")
    logger.info("  - 如需手动终止进程: kill -9 PID")


if __name__ == "__main__":
    main()
