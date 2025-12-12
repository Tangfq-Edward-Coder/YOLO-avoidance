"""
刹车接口模块
提供软件刹车指令接口
"""
from __future__ import annotations

from typing import Optional
import threading
import time
import numpy as np


class BrakeInterface:
    """刹车接口类"""
    
    def __init__(self):
        """初始化刹车接口"""
        self.brake_flag = False
        self.brake_level = 0.0  # 0.0-1.0
        self.lock = threading.Lock()
        self.callbacks = []
    
    def trigger_brake(self, risk_level: str = "danger", brake_level: float = 1.0):
        """
        触发刹车
        
        Args:
            risk_level: 风险等级 ('safe', 'warning', 'danger')
            brake_level: 刹车力度 (0.0-1.0)
        """
        with self.lock:
            self.brake_flag = True
            self.brake_level = max(0.0, min(1.0, brake_level))
        
        # 调用所有注册的回调函数
        for callback in self.callbacks:
            try:
                callback(risk_level, brake_level)
            except Exception as e:
                print(f"刹车回调函数执行错误: {e}")
    
    def release_brake(self):
        """释放刹车"""
        with self.lock:
            self.brake_flag = False
            self.brake_level = 0.0
    
    def get_brake_status(self) -> tuple[bool, float]:
        """
        获取刹车状态
        
        Returns:
            (is_braking, brake_level): 是否在刹车和刹车力度
        """
        with self.lock:
            return self.brake_flag, self.brake_level
    
    def register_callback(self, callback):
        """
        注册刹车回调函数
        
        Args:
            callback: 回调函数，接收 (risk_level, brake_level) 参数
        """
        self.callbacks.append(callback)
    
    def brake_interface(self, risk_level: str):
        """
        刹车接口函数（符合技术方案要求）
        
        Args:
            risk_level: 风险等级
        """
        if risk_level == "danger":
            self.trigger_brake("danger", 1.0)
        elif risk_level == "warning":
            self.trigger_brake("warning", 0.5)
        else:
            self.release_brake()


class RadarFusionInterface:
    """雷达融合接口类"""
    
    def __init__(self):
        """初始化雷达融合接口"""
        self.radar_objects = []
        self.lock = threading.Lock()
    
    def update_radar_data(self, radar_objects_list: list):
        """
        更新雷达数据（符合技术方案要求）
        
        Args:
            radar_objects_list: 雷达目标列表，每个元素包含:
                {
                    'distance': float,  # 距离（米）
                    'velocity': float,  # 速度（米/秒）
                    'azimuth': float,   # 方位角（度）
                    'elevation': float  # 俯仰角（度，可选）
                }
        """
        with self.lock:
            self.radar_objects = radar_objects_list.copy()
    
    def get_radar_objects(self) -> list:
        """
        获取当前雷达目标列表
        
        Returns:
            雷达目标列表
        """
        with self.lock:
            return self.radar_objects.copy()
    
    def fuse_with_vision(
        self,
        vision_objects: list,
        max_association_distance: float = 1.0
    ) -> list:
        """
        将视觉目标与雷达目标进行数据关联
        
        Args:
            vision_objects: 视觉检测到的障碍物列表
            max_association_distance: 最大关联距离（米）
        
        Returns:
            融合后的目标列表
        """
        radar_objects = self.get_radar_objects()
        
        if not radar_objects:
            return vision_objects
        
        fused_objects = []
        
        # 简单的最近邻关联算法
        for vision_obj in vision_objects:
            vx, vy, vz = vision_obj['3d_position']
            vision_distance = vision_obj['depth']
            
            # 找到最近的雷达目标
            min_dist = float('inf')
            associated_radar = None
            
            for radar_obj in radar_objects:
                radar_dist = radar_obj['distance']
                radar_azimuth = np.radians(radar_obj['azimuth'])
                
                # 计算雷达目标在相机坐标系中的位置
                radar_x = radar_dist * np.sin(radar_azimuth)
                radar_z = radar_dist * np.cos(radar_azimuth)
                
                # 计算距离
                dist = np.sqrt((vx - radar_x)**2 + (vz - radar_z)**2)
                
                if dist < min_dist and dist < max_association_distance:
                    min_dist = dist
                    associated_radar = radar_obj
            
            # 创建融合对象
            fused_obj = vision_obj.copy()
            if associated_radar is not None:
                fused_obj['radar_fused'] = True
                fused_obj['radar_distance'] = associated_radar['distance']
                fused_obj['radar_velocity'] = associated_radar.get('velocity', 0.0)
                # 使用雷达距离更新深度（更准确）
                fused_obj['depth'] = associated_radar['distance']
            else:
                fused_obj['radar_fused'] = False
            
            fused_objects.append(fused_obj)
        
        return fused_objects

