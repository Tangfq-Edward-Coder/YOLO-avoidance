"""
配置文件工具函数
用于处理配置文件中的表达式和特殊值
"""
from __future__ import annotations

from typing import Any, List


def parse_config_value(value: Any) -> float:
    """
    解析配置值，支持表达式字符串（如 "-1/0.12"）
    
    Args:
        value: 配置值，可能是数字或表达式字符串
    
    Returns:
        解析后的浮点数
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # 如果是表达式字符串（包含运算符）
        if '/' in value or '*' in value or '+' in value or '-' in value:
            try:
                # 安全地计算表达式
                return float(eval(value))
            except (ValueError, SyntaxError):
                # 如果计算失败，尝试直接转换
                return float(value)
        else:
            return float(value)
    
    return float(value)


def parse_matrix(matrix: List[List[Any]]) -> List[List[float]]:
    """
    解析矩阵配置，处理其中的表达式字符串
    
    Args:
        matrix: 矩阵配置（二维列表）
    
    Returns:
        解析后的浮点数矩阵
    """
    result = []
    for row in matrix:
        processed_row = [parse_config_value(val) for val in row]
        result.append(processed_row)
    return result

