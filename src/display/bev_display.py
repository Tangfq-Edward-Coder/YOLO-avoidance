"""
3D雷达界面（鸟瞰图显示）
使用Pygame实现实时渲染
"""
from __future__ import annotations

import pygame
import numpy as np
from typing import List, Dict, Optional
import yaml
import math


class BEVDisplay:
    """鸟瞰图显示类"""
    
    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化显示界面
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        display_config = self.config['display']
        
        # 窗口参数
        self.window_width = display_config['window_width']
        self.window_height = display_config['window_height']
        self.bev_range = display_config['bev_range']
        self.ego_position = tuple(display_config['ego_position'])
        self.target_fps = display_config['target_fps']
        
        # 初始化Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Real-time Visual Obstacle Avoidance System - Bird's Eye View")
        self.clock = pygame.time.Clock()
        
        # 颜色定义
        self.colors = {
            'background': (20, 20, 30),
            'grid': (50, 50, 60),
            'ego': (0, 255, 0),
            'safe': (0, 255, 0),
            'warning': (255, 255, 0),
            'danger': (255, 0, 0),
            'text': (255, 255, 255),
            'axis': (100, 100, 100)
        }
        
        # 字体
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # 像素到米的转换比例
        self.pixels_per_meter = min(
            self.window_width / (2 * self.bev_range),
            self.window_height / (2 * self.bev_range)
        )
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def world_to_screen(self, x: float, z: float) -> tuple[int, int]:
        """
        将世界坐标转换为屏幕坐标
        
        Args:
            x: 世界x坐标（米，向右为正）
            z: 世界z坐标（米，向前为正）
        
        Returns:
            (screen_x, screen_y): 屏幕坐标
        """
        # 相机坐标系：x向右，y向下，z向前
        # 屏幕坐标系：x向右，y向下
        screen_x = int(self.ego_position[0] + x * self.pixels_per_meter)
        screen_y = int(self.ego_position[1] - z * self.pixels_per_meter)  # z向前，屏幕y向下
        
        return screen_x, screen_y
    
    def draw_grid(self):
        """绘制网格"""
        center_x, center_y = self.ego_position
        
        # 绘制主要网格线
        grid_spacing = 2.0  # 米
        num_lines = int(self.bev_range / grid_spacing)
        
        for i in range(-num_lines, num_lines + 1):
            x = i * grid_spacing
            start_x, start_y = self.world_to_screen(x, -self.bev_range)
            end_x, end_y = self.world_to_screen(x, self.bev_range)
            pygame.draw.line(
                self.screen, self.colors['grid'],
                (start_x, start_y), (end_x, end_y), 1
            )
            
            z = i * grid_spacing
            start_x, start_y = self.world_to_screen(-self.bev_range, z)
            end_x, end_y = self.world_to_screen(self.bev_range, z)
            pygame.draw.line(
                self.screen, self.colors['grid'],
                (start_x, start_y), (end_x, end_y), 1
            )
    
    def draw_ego_vehicle(self):
        """绘制自车"""
        center_x, center_y = self.ego_position
        
        # 绘制自车矩形（假设1.8m宽，4.5m长）
        width_px = int(1.8 * self.pixels_per_meter)
        length_px = int(4.5 * self.pixels_per_meter)
        
        rect = pygame.Rect(
            center_x - width_px // 2,
            center_y - length_px // 2,
            width_px,
            length_px
        )
        pygame.draw.rect(self.screen, self.colors['ego'], rect, 2)
        
        # 绘制方向箭头
        arrow_length = length_px // 2
        arrow_end_x = center_x
        arrow_end_y = center_y - arrow_length
        pygame.draw.line(
            self.screen, self.colors['ego'],
            (center_x, center_y), (arrow_end_x, arrow_end_y), 3
        )
    
    def draw_object(self, obj: Dict):
        """
        绘制障碍物
        
        Args:
            obj: 障碍物信息
        """
        x, y, z = obj['3d_position']
        depth = obj['depth']
        
        # 确定颜色
        if depth <= 1.0:
            color = self.colors['danger']
        elif depth <= 2.0:
            color = self.colors['warning']
        else:
            color = self.colors['safe']
        
        # 转换为屏幕坐标
        screen_x, screen_y = self.world_to_screen(x, z)
        
        # 根据距离绘制不同大小的圆
        radius = max(5, int(20 / (depth + 0.5)))
        pygame.draw.circle(self.screen, color, (screen_x, screen_y), radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), radius, 1)
        
        # 绘制距离标签
        distance_text = f"{depth:.2f}m"
        text_surface = self.small_font.render(distance_text, True, self.colors['text'])
        text_rect = text_surface.get_rect(center=(screen_x, screen_y - radius - 10))
        self.screen.blit(text_surface, text_rect)
        
        # 绘制类别标签
        class_name = obj.get('class_name', 'obstacle')
        class_surface = self.small_font.render(class_name, True, self.colors['text'])
        class_rect = class_surface.get_rect(center=(screen_x, screen_y + radius + 10))
        self.screen.blit(class_surface, class_rect)
    
    def draw_info_panel(self, risk_info: Dict, fps: float, num_objects: int):
        """
        绘制信息面板
        
        Args:
            risk_info: 风险评估信息
            fps: 当前帧率
            num_objects: 检测到的障碍物数量
        """
        # 背景
        panel_rect = pygame.Rect(10, 10, 300, 150)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2)
        
        # 风险等级
        risk_level = risk_info.get('risk_level', 'safe')
        risk_score = risk_info.get('risk_score', 0.0)
        
        if risk_level == 'danger':
            risk_color = self.colors['danger']
        elif risk_level == 'warning':
            risk_color = self.colors['warning']
        else:
            risk_color = self.colors['safe']
        
        risk_text = f"Risk Level: {risk_level.upper()}"
        risk_surface = self.font.render(risk_text, True, risk_color)
        self.screen.blit(risk_surface, (20, 20))
        
        # Risk Score
        score_text = f"Risk Score: {risk_score:.2f}"
        score_surface = self.font.render(score_text, True, self.colors['text'])
        self.screen.blit(score_surface, (20, 50))
        
        # Number of Objects
        objects_text = f"Objects: {num_objects}"
        objects_surface = self.font.render(objects_text, True, self.colors['text'])
        self.screen.blit(objects_surface, (20, 80))
        
        # FPS
        fps_text = f"FPS: {fps:.1f}"
        fps_surface = self.font.render(fps_text, True, self.colors['text'])
        self.screen.blit(fps_surface, (20, 110))
        
        # Brake Status
        should_brake = risk_info.get('should_brake', False)
        if should_brake:
            brake_text = "Brake: Active"
            brake_color = self.colors['danger']
        else:
            brake_text = "Brake: Inactive"
            brake_color = self.colors['safe']
        
        brake_surface = self.font.render(brake_text, True, brake_color)
        self.screen.blit(brake_surface, (20, 140))
    
    def update(
        self,
        objects: List[Dict],
        risk_info: Dict,
        fps: float
    ):
        """
        更新显示
        
        Args:
            objects: 障碍物列表
            risk_info: 风险评估信息
            fps: 当前帧率
        """
        # 清空屏幕
        self.screen.fill(self.colors['background'])
        
        # 绘制网格
        self.draw_grid()
        
        # 绘制自车
        self.draw_ego_vehicle()
        
        # 绘制障碍物
        for obj in objects:
            self.draw_object(obj)
        
        # 绘制信息面板
        self.draw_info_panel(risk_info, fps, len(objects))
        
        # 更新显示
        pygame.display.flip()
        self.clock.tick(self.target_fps)
    
    def handle_events(self) -> bool:
        """
        处理事件
        
        Returns:
            是否继续运行
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    def close(self):
        """关闭显示"""
        pygame.quit()

