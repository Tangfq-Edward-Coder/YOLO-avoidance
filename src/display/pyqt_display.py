"""
PyQt5显示模块
实时显示摄像头画面、检测结果、风险预警等信息
"""
from __future__ import annotations

import sys
import cv2
import numpy as np
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
import yaml


class VideoThread(QThread):
    """视频处理线程"""
    frame_ready = pyqtSignal(np.ndarray, dict)
    
    def __init__(self, process_callback):
        super().__init__()
        self.process_callback = process_callback
        self.running = True
    
    def run(self):
        """运行视频处理循环"""
        while self.running:
            if self.process_callback:
                frame, results = self.process_callback()
                if frame is not None:
                    self.frame_ready.emit(frame, results)
            self.msleep(33)  # 约30 FPS
    
    def stop(self):
        """停止线程"""
        self.running = False


class PyQtDisplay(QMainWindow):
    """PyQt5主显示窗口"""
    
    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化显示窗口
        
        Args:
            config_path: 配置文件路径
        """
        super().__init__()
        self.config = self._load_config(config_path)
        self.display_config = self.config.get('display', {})
        
        self.window_width = self.display_config.get('window_width', 1280)
        self.window_height = self.display_config.get('window_height', 720)
        
        self.init_ui()
        self.video_thread = None
        self.process_callback = None
        
        # 风险状态
        self.risk_states = {
            'low_visibility': False,
            'wet_road': False,
            'curve': False,
            'narrow_road': False,
            'ttc_warning': False,
            'obstacle_danger': False
        }
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("省实未来汽车 - 视觉避障与道路风险预警系统")
        self.setGeometry(100, 100, self.window_width, self.window_height)
        
        # 主窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 左侧：视频显示区域
        left_panel = QVBoxLayout()
        
        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid gray;")
        left_panel.addWidget(self.video_label)
        
        # FPS显示
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.fps_label.setStyleSheet("color: green;")
        left_panel.addWidget(self.fps_label)
        
        main_layout.addLayout(left_panel, 2)
        
        # 右侧：信息面板
        right_panel = QVBoxLayout()
        
        # 风险预警区域
        risk_title = QLabel("风险预警")
        risk_title.setFont(QFont("Arial", 14, QFont.Bold))
        right_panel.addWidget(risk_title)
        
        # 中长期风险
        self.long_term_label = QLabel("中长期风险：无")
        self.long_term_label.setFont(QFont("Arial", 11))
        right_panel.addWidget(self.long_term_label)
        
        # 短期风险
        self.short_term_label = QLabel("短期风险：无")
        self.short_term_label.setFont(QFont("Arial", 11))
        right_panel.addWidget(self.short_term_label)
        
        # TTC显示
        self.ttc_label = QLabel("TTC: --")
        self.ttc_label.setFont(QFont("Arial", 12, QFont.Bold))
        right_panel.addWidget(self.ttc_label)
        
        # 检测信息
        self.detection_label = QLabel("检测目标数：0")
        self.detection_label.setFont(QFont("Arial", 10))
        right_panel.addWidget(self.detection_label)
        
        # 日志区域
        log_title = QLabel("系统日志")
        log_title.setFont(QFont("Arial", 12, QFont.Bold))
        right_panel.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        right_panel.addWidget(self.log_text)
        
        # 控制按钮
        self.start_button = QPushButton("开始")
        self.start_button.clicked.connect(self.start_processing)
        right_panel.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        right_panel.addWidget(self.stop_button)
        
        right_panel.addStretch()
        main_layout.addLayout(right_panel, 1)
    
    def set_process_callback(self, callback):
        """
        设置处理回调函数
        
        Args:
            callback: 回调函数，返回 (frame, results)
        """
        self.process_callback = callback
    
    def start_processing(self):
        """开始处理"""
        if self.process_callback is None:
            self.log("错误：未设置处理回调函数")
            return
        
        self.video_thread = VideoThread(self.process_callback)
        self.video_thread.frame_ready.connect(self.update_frame)
        self.video_thread.start()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log("系统启动")
    
    def stop_processing(self):
        """停止处理"""
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread.wait()
            self.video_thread = None
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log("系统停止")
    
    def update_frame(self, frame: np.ndarray, results: Dict):
        """
        更新显示帧
        
        Args:
            frame: 图像帧
            results: 处理结果
        """
        # 绘制检测框和标注
        annotated_frame = self._draw_annotations(frame.copy(), results)
        
        # 转换为QImage
        height, width, channel = annotated_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(annotated_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # 缩放以适应显示区域
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
        
        # 更新信息显示
        self._update_info(results)
    
    def _draw_annotations(self, frame: np.ndarray, results: Dict) -> np.ndarray:
        """
        在图像上绘制标注
        
        Args:
            frame: 原始图像
            results: 处理结果
        
        Returns:
            标注后的图像
        """
        detections = results.get('detections', [])
        objects = results.get('objects', [])
        risk_info = results.get('risk_info', {})
        
        # 绘制检测框
        for i, detection in enumerate(detections):
            bbox = detection.get('bbox', [])
            if len(bbox) >= 4:
                x1, y1, x2, y2 = map(int, bbox[:4])
                class_name = detection.get('class', 'unknown')
                confidence = detection.get('confidence', 0.0)
                
                # 获取对应的对象信息
                obj_info = objects[i] if i < len(objects) else {}
                depth = obj_info.get('depth', 0.0)
                ttc = obj_info.get('ttc', None)
                
                # 选择颜色
                risk_level = obj_info.get('risk_level', 'safe')
                if risk_level == 'danger':
                    color = (0, 0, 255)  # 红色
                elif risk_level == 'warning':
                    color = (0, 165, 255)  # 橙色
                else:
                    color = (0, 255, 0)  # 绿色
                
                # 绘制边界框
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # 绘制标签
                label = f"{class_name} {confidence:.2f}"
                if depth > 0:
                    label += f" {depth:.2f}m"
                if ttc is not None:
                    label += f" TTC:{ttc:.1f}s"
                
                # 标签背景
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    frame,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    color,
                    -1
                )
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
        
        return frame
    
    def _update_info(self, results: Dict):
        """更新信息显示"""
        # FPS
        fps = results.get('fps', 0.0)
        self.fps_label.setText(f"FPS: {fps:.1f}")
        
        # 检测数量
        detections = results.get('detections', [])
        self.detection_label.setText(f"检测目标数：{len(detections)}")
        
        # 风险信息
        road_risks = results.get('road_risks', {})
        long_term = road_risks.get('long_term', {})
        short_term = road_risks.get('short_term', {})
        
        # 中长期风险
        long_term_text = "中长期风险："
        if long_term.get('low_visibility'):
            long_term_text += "低能见度 "
            self.risk_states['low_visibility'] = True
        else:
            self.risk_states['low_visibility'] = False
        
        if long_term.get('wet_road'):
            long_term_text += "路面湿滑 "
            self.risk_states['wet_road'] = True
        else:
            self.risk_states['wet_road'] = False
        
        if long_term_text == "中长期风险：":
            long_term_text += "无"
        
        self.long_term_label.setText(long_term_text)
        if long_term.get('low_visibility') or long_term.get('wet_road'):
            self.long_term_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.long_term_label.setStyleSheet("color: black;")
        
        # 短期风险
        short_term_text = "短期风险："
        if short_term.get('curve'):
            short_term_text += "弯道 "
            self.risk_states['curve'] = True
        else:
            self.risk_states['curve'] = False
        
        if short_term.get('narrow_road'):
            short_term_text += "狭窄路段 "
            self.risk_states['narrow_road'] = True
        else:
            self.risk_states['narrow_road'] = False
        
        if short_term_text == "短期风险：":
            short_term_text += "无"
        
        self.short_term_label.setText(short_term_text)
        if short_term.get('curve') or short_term.get('narrow_road'):
            self.short_term_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.short_term_label.setStyleSheet("color: black;")
        
        # TTC
        objects = results.get('objects', [])
        nearest_obj = None
        for obj in objects:
            if obj.get('ttc_valid', False):
                if nearest_obj is None or obj.get('depth', float('inf')) < nearest_obj.get('depth', float('inf')):
                    nearest_obj = obj
        
        if nearest_obj and nearest_obj.get('ttc_valid'):
            ttc = nearest_obj.get('ttc', 0.0)
            self.ttc_label.setText(f"TTC: {ttc:.2f}秒")
            if ttc <= 3.0:
                self.ttc_label.setStyleSheet("color: red; font-weight: bold;")
                self.risk_states['ttc_warning'] = True
            else:
                self.ttc_label.setStyleSheet("color: orange;")
                self.risk_states['ttc_warning'] = False
        else:
            self.ttc_label.setText("TTC: --")
            self.ttc_label.setStyleSheet("color: black;")
            self.risk_states['ttc_warning'] = False
    
    def log(self, message: str):
        """
        添加日志
        
        Args:
            message: 日志消息
        """
        self.log_text.append(message)
        # 限制日志行数
        if self.log_text.document().blockCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.MoveAnchor, 1)
            cursor.movePosition(cursor.Start, cursor.KeepAnchor)
            cursor.removeSelectedText()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_processing()
        event.accept()

