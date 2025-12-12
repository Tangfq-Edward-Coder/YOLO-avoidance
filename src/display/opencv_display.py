"""
OpenCV视频流显示模块
用于Windows单目模式，实时显示视频流并标注障碍物
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import List, Dict, Optional
import yaml


class OpenCVDisplay:
    """OpenCV视频流显示类，支持实时标注障碍物"""
    
    def __init__(self, config_path: str = "configs/system_config_mono.yaml"):
        """
        初始化OpenCV显示
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        display_config = self.config.get('display', {})
        
        # 窗口参数
        self.window_name = "Real-time Visual Obstacle Avoidance System"
        self.image_width = self.config['camera']['image_width']
        self.image_height = self.config['camera']['image_height']
        
        # 颜色定义（BGR格式）
        self.colors = {
            'safe': (0, 255, 0),      # 绿色
            'warning': (0, 255, 255),  # 黄色
            'danger': (0, 0, 255),     # 红色
            'text': (255, 255, 255),   # 白色
            'background': (0, 0, 0)    # 黑色
        }
        
        # 字体参数
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        self.line_thickness = 2
        
        # 创建窗口
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.image_width, self.image_height)
        
        # 状态信息
        self.fps = 0.0
        self.frame_count = 0
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_color_by_risk(self, depth: float, danger_dist: float = 1.0, 
                           warning_dist: float = 2.0) -> tuple:
        """
        根据距离获取颜色
        
        Args:
            depth: 距离（米）
            danger_dist: 危险距离阈值
            warning_dist: 警告距离阈值
        
        Returns:
            BGR颜色元组
        """
        if depth <= danger_dist:
            return self.colors['danger']
        elif depth <= warning_dist:
            return self.colors['warning']
        else:
            return self.colors['safe']
    
    def draw_detection(self, image: np.ndarray, obj: Dict) -> np.ndarray:
        """
        在图像上绘制单个障碍物标注
        
        Args:
            image: 输入图像
            obj: 障碍物信息，包含 bbox, depth, class_name, confidence 等
        
        Returns:
            标注后的图像
        """
        bbox = obj['bbox']
        depth = obj.get('depth', 0.0)
        class_name = obj.get('class_name', 'obstacle')
        confidence = obj.get('confidence', 0.0)
        
        x1, y1, x2, y2 = [int(v) for v in bbox]
        
        # 根据距离确定颜色
        color = self._get_color_by_risk(depth)
        
        # 绘制边界框
        cv2.rectangle(image, (x1, y1), (x2, y2), color, self.line_thickness)
        
        # 准备标签文本
        label = f"{class_name} {confidence:.2f}"
        depth_text = f"{depth:.2f}m"
        
        # 计算文本大小
        (label_width, label_height), baseline = cv2.getTextSize(
            label, self.font, self.font_scale, self.font_thickness
        )
        
        # 绘制标签背景
        cv2.rectangle(
            image,
            (x1, y1 - label_height - baseline - 5),
            (x1 + label_width, y1),
            color,
            -1
        )
        
        # 绘制标签文本
        cv2.putText(
            image,
            label,
            (x1, y1 - baseline - 2),
            self.font,
            self.font_scale,
            self.colors['text'],
            self.font_thickness,
            cv2.LINE_AA
        )
        
        # 绘制距离文本（在边界框下方）
        (depth_width, depth_height), depth_baseline = cv2.getTextSize(
            depth_text, self.font, self.font_scale, self.font_thickness
        )
        
        cv2.putText(
            image,
            depth_text,
            (x1, y2 + depth_height + 5),
            self.font,
            self.font_scale,
            color,
            self.font_thickness,
            cv2.LINE_AA
        )
        
        return image
    
    def draw_info_panel(self, image: np.ndarray, risk_info: Dict, 
                       num_objects: int) -> np.ndarray:
        """
        在图像上绘制信息面板
        
        Args:
            image: 输入图像
            risk_info: 风险评估信息
            num_objects: 障碍物数量
        
        Returns:
            添加信息面板后的图像
        """
        h, w = image.shape[:2]
        
        # 信息面板位置和大小
        panel_height = 120
        panel_y = 10
        panel_x = 10
        panel_width = 300
        
        # 绘制半透明背景
        overlay = image.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # 绘制边框
        cv2.rectangle(
            image,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (100, 100, 100),
            2
        )
        
        # 准备文本信息
        risk_level = risk_info.get('risk_level', 'safe')
        risk_score = risk_info.get('risk_score', 0.0)
        should_brake = risk_info.get('should_brake', False)
        
        # 确定风险颜色
        if risk_level == 'danger':
            risk_color = self.colors['danger']
        elif risk_level == 'warning':
            risk_color = self.colors['warning']
        else:
            risk_color = self.colors['safe']
        
        # 绘制文本
        y_offset = panel_y + 25
        line_height = 25
        
        # Risk Level
        cv2.putText(
            image,
            f"Risk Level: {risk_level.upper()}",
            (panel_x + 10, y_offset),
            self.font,
            self.font_scale,
            risk_color,
            self.font_thickness,
            cv2.LINE_AA
        )
        
        # Risk Score
        y_offset += line_height
        cv2.putText(
            image,
            f"Risk Score: {risk_score:.2f}",
            (panel_x + 10, y_offset),
            self.font,
            self.font_scale,
            self.colors['text'],
            self.font_thickness,
            cv2.LINE_AA
        )
        
        # Number of Objects
        y_offset += line_height
        cv2.putText(
            image,
            f"Objects: {num_objects}",
            (panel_x + 10, y_offset),
            self.font,
            self.font_scale,
            self.colors['text'],
            self.font_thickness,
            cv2.LINE_AA
        )
        
        # FPS
        y_offset += line_height
        cv2.putText(
            image,
            f"FPS: {self.fps:.1f}",
            (panel_x + 10, y_offset),
            self.font,
            self.font_scale,
            self.colors['text'],
            self.font_thickness,
            cv2.LINE_AA
        )
        
        # Brake Status
        if should_brake:
            brake_text = "Brake: Active"
            brake_color = self.colors['danger']
        else:
            brake_text = "Brake: Inactive"
            brake_color = self.colors['safe']
        
        y_offset += line_height
        cv2.putText(
            image,
            brake_text,
            (panel_x + 10, y_offset),
            self.font,
            self.font_scale,
            brake_color,
            self.font_thickness,
            cv2.LINE_AA
        )
        
        return image
    
    def update(self, image: np.ndarray, objects: List[Dict], 
               risk_info: Dict, fps: float = 0.0) -> bool:
        """
        更新显示
        
        Args:
            image: 输入图像（BGR格式）
            objects: 障碍物列表
            risk_info: 风险评估信息
            fps: 当前帧率
        
        Returns:
            是否继续运行（False表示用户按了ESC）
        """
        self.fps = fps
        
        # 复制图像以避免修改原图
        display_image = image.copy()
        
        # 绘制所有障碍物
        for obj in objects:
            display_image = self.draw_detection(display_image, obj)
        
        # 绘制信息面板
        display_image = self.draw_info_panel(
            display_image, risk_info, len(objects)
        )
        
        # 显示图像
        cv2.imshow(self.window_name, display_image)
        
        # 检查按键
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC键
            return False
        
        return True
    
    def close(self):
        """关闭显示"""
        cv2.destroyAllWindows()

