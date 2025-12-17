"""
省实未来汽车 - 多模态AI视觉辅助驾驶系统（视觉避障组）
主系统集成，整合所有模块，实现完整的实时视觉避障与道路风险预警系统
"""

from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到Python路径
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 导入标准库
import argparse
import time
import cv2
import numpy as np
import yaml
from PyQt5.QtWidgets import QApplication

# 导入项目模块
from src.camera import StereoCamera
from src.detection import YOLODetector
from src.segmentation import UNetSegmenter
from src.stereo import StereoMatcher
from src.fusion import InfoFusion
from src.risk import RiskAssessor, RoadRiskAssessor, TTCEstimator
from src.interface import BrakeInterface
from src.audio import VoiceAlert
from src.display import PyQtDisplay


class VisualObstacleAvoidanceSystem:
    """实时视觉避障与道路风险预警系统主类"""

    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化系统

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)

        # 初始化各个模块
        print("初始化相机模块...")
        self.camera = StereoCamera(config_path)

        print("初始化检测模块...")
        self.detector = YOLODetector(self.config["models"]["yolo_model"], config_path)

        print("初始化分割模块...")
        self.segmenter = UNetSegmenter(self.config["models"]["unet_model"], config_path)

        print("初始化立体匹配模块...")
        self.stereo_matcher = StereoMatcher(config_path)

        print("初始化信息融合模块...")
        self.info_fusion = InfoFusion(config_path)

        print("初始化碰撞风险评估模块...")
        self.risk_assessor = RiskAssessor(config_path)

        print("初始化道路风险预警模块...")
        self.road_risk_assessor = RoadRiskAssessor(config_path)

        print("初始化TTC估算模块...")
        ttc_config = self.config.get('ttc_estimation', {})
        self.ttc_estimator = TTCEstimator(
            ego_speed=ttc_config.get('default_ego_speed', 5.0),
            history_size=ttc_config.get('history_size', 10),
            min_frames_for_ttc=ttc_config.get('min_frames_for_ttc', 2)
        )

        print("初始化接口模块...")
        self.brake_interface = BrakeInterface()

        print("初始化语音提示模块...")
        voice_config = self.config.get('voice_alert', {})
        self.voice_alert = VoiceAlert(enabled=voice_config.get('enabled', True))

        print("初始化显示模块...")
        self.display = PyQtDisplay(config_path)
        self.display.set_process_callback(self.process_frame_for_display)

        # 性能统计
        self.frame_count = 0
        self.fps = 0.0
        self.last_time = time.time()
        self.last_road_risk_time = {}  # 记录上次风险提示时间，避免重复提示

        # 运行标志
        self.running = False

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def process_frame(self, left_image: np.ndarray, right_image: np.ndarray) -> dict:
        """
        处理单帧图像

        Args:
            left_image: 左图像
            right_image: 右图像

        Returns:
            处理结果字典
        """
        start_time = time.time()

        # 1. YOLO目标检测（person, car, bicycle）
        detections = self.detector.detect(left_image)

        # 2. U-Net场景分割（识别路面、车道线、天空等）
        # 对整个图像进行分割
        full_segmentation_mask = self.segmenter.segment_full_image(left_image)

        # 对每个检测到的目标进行精细分割
        segmentation_masks = []
        for detection in detections:
            mask = self.segmenter.segment(left_image, detection["bbox"])
            segmentation_masks.append(mask)

        # 3. 立体匹配和深度计算
        disparity, depth_map = self.stereo_matcher.compute_disparity_and_depth(
            left_image, right_image
        )

        # 4. 信息融合
        fused_objects = self.info_fusion.fuse_detection_and_depth(
            detections, segmentation_masks, depth_map
        )

        # 5. 过滤无效障碍物（20米有效范围）
        filtered_objects = self.info_fusion.filter_by_depth(
            fused_objects, min_depth=0.1, max_depth=20.0
        )

        # 6. TTC估算
        objects_with_ttc = self.ttc_estimator.estimate_ttc(filtered_objects)

        # 7. 碰撞风险评估
        risk_info = self.risk_assessor.assess_risk(objects_with_ttc)

        # 8. 道路风险预警
        road_risks = self.road_risk_assessor.assess_all_risks(
            left_image,
            full_segmentation_mask,
            detections
        )

        # 9. 处理风险预警和语音提示
        self._handle_risk_alerts(road_risks, objects_with_ttc, risk_info)

        # 10. 触发刹车（如果需要）
        if risk_info["should_brake"]:
            self.brake_interface.brake_interface(risk_info["risk_level"])

        # 计算处理时间
        process_time = time.time() - start_time

        # 更新FPS
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time

        return {
            "detections": detections,
            "segmentation_masks": segmentation_masks,
            "full_segmentation_mask": full_segmentation_mask,
            "disparity": disparity,
            "depth_map": depth_map,
            "objects": objects_with_ttc,
            "risk_info": risk_info,
            "road_risks": road_risks,
            "process_time": process_time,
            "fps": self.fps,
        }

    def process_frame_for_display(self):
        """
        为显示模块提供处理函数
        返回 (frame, results)
        """
        if not self.running:
            return None, {}

        # 读取图像
        left_img, right_img = self.camera.read()

        if left_img is None or right_img is None:
            return None, {}

        # 处理帧
        results = self.process_frame(left_img, right_img)

        # 返回左图像（用于显示）
        return left_img, results

    def _handle_risk_alerts(
        self,
        road_risks: dict,
        objects_with_ttc: list,
        risk_info: dict
    ):
        """
        处理风险预警和语音提示

        Args:
            road_risks: 道路风险信息
            objects_with_ttc: 带TTC的障碍物列表
            risk_info: 碰撞风险信息
        """
        current_time = time.time()
        alert_cooldown = 3.0  # 提示冷却时间（秒）

        # 中长期风险提示
        long_term = road_risks.get('long_term', {})
        if long_term.get('low_visibility'):
            if current_time - self.last_road_risk_time.get('low_visibility', 0) > alert_cooldown:
                self.voice_alert.alert_low_visibility()
                self.last_road_risk_time['low_visibility'] = current_time

        if long_term.get('wet_road'):
            if current_time - self.last_road_risk_time.get('wet_road', 0) > alert_cooldown:
                self.voice_alert.alert_wet_road()
                self.last_road_risk_time['wet_road'] = current_time

        # 短期风险提示
        short_term = road_risks.get('short_term', {})
        if short_term.get('curve'):
            if current_time - self.last_road_risk_time.get('curve', 0) > alert_cooldown:
                self.voice_alert.alert_curve()
                self.last_road_risk_time['curve'] = current_time

        if short_term.get('narrow_road'):
            if current_time - self.last_road_risk_time.get('narrow_road', 0) > alert_cooldown:
                self.voice_alert.alert_narrow_road()
                self.last_road_risk_time['narrow_road'] = current_time

        # TTC紧急警报
        nearest_obj = self.ttc_estimator.get_nearest_object_ttc(objects_with_ttc)
        if nearest_obj and nearest_obj.get('ttc_valid'):
            ttc = nearest_obj.get('ttc', 0.0)
            ttc_config = self.config.get('ttc_estimation', {})
            emergency_threshold = ttc_config.get('emergency_threshold', 3.0)

            if self.ttc_estimator.trigger_brake_alert(ttc, emergency_threshold):
                if current_time - self.last_road_risk_time.get('ttc_warning', 0) > 1.0:
                    self.voice_alert.alert_ttc_warning(ttc)
                    self.last_road_risk_time['ttc_warning'] = current_time

        # 障碍物危险警报
        if risk_info.get('risk_level') == 'danger':
            if current_time - self.last_road_risk_time.get('obstacle_danger', 0) > 1.0:
                self.voice_alert.alert_obstacle_danger()
                self.last_road_risk_time['obstacle_danger'] = current_time
        elif risk_info.get('risk_level') == 'warning':
            if current_time - self.last_road_risk_time.get('obstacle_warning', 0) > 2.0:
                self.voice_alert.alert_obstacle_warning()
                self.last_road_risk_time['obstacle_warning'] = current_time

    def run(self, left_camera_id: int = 0, right_camera_id: int = 1):
        """
        运行主循环

        Args:
            left_camera_id: 左相机设备ID
            right_camera_id: 右相机设备ID
        """
        print("打开相机...")
        self.camera.open(left_camera_id, right_camera_id)

        self.running = True
        print("系统启动，开始处理...")

        # 启动PyQt应用
        app = QApplication(sys.argv)
        self.display.show()

        try:
            # 运行Qt事件循环
            sys.exit(app.exec_())
        except KeyboardInterrupt:
            print("\n收到中断信号，正在关闭...")
        except Exception as e:
            print(f"运行时错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()

    def shutdown(self):
        """关闭系统"""
        print("正在关闭系统...")
        self.running = False
        self.camera.release()
        print("系统已关闭")

    def run_with_images(self, left_image_path: str, right_image_path: str):
        """
        使用图像文件运行（用于测试）

        Args:
            left_image_path: 左图像路径
            right_image_path: 右图像路径
        """
        left_img = cv2.imread(left_image_path)
        right_img = cv2.imread(right_image_path)

        if left_img is None or right_img is None:
            raise ValueError("无法读取图像文件")

        result = self.process_frame(left_img, right_img)
        print(f"处理完成: {len(result['objects'])} 个障碍物")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="省实未来汽车 - 视觉避障与道路风险预警系统"
    )
    parser.add_argument(
        "--config", type=str, default="configs/system_config.yaml", help="配置文件路径"
    )
    parser.add_argument("--left-camera", type=int, default=0, help="左相机设备ID")
    parser.add_argument("--right-camera", type=int, default=1, help="右相机设备ID")
    parser.add_argument(
        "--test-image-left", type=str, default=None, help="测试用左图像路径"
    )
    parser.add_argument(
        "--test-image-right", type=str, default=None, help="测试用右图像路径"
    )

    return parser.parse_args()


def main():
    """主函数"""
    try:
        print("=" * 60)
        print("省实未来汽车 - 视觉避障与道路风险预警系统")
        print("=" * 60)
        sys.stdout.flush()

        args = parse_args()
        print(f"配置文件: {args.config}")
        print(f"左摄像头ID: {args.left_camera}")
        print(f"右摄像头ID: {args.right_camera}")
        sys.stdout.flush()

        # 创建系统实例
        print("\n正在初始化系统...")
        sys.stdout.flush()
        system = VisualObstacleAvoidanceSystem(args.config)

        # 运行系统
        if args.test_image_left and args.test_image_right:
            # 测试模式：使用图像文件
            print("\n使用测试图像:")
            print(f"  左图像: {args.test_image_left}")
            print(f"  右图像: {args.test_image_right}")
            sys.stdout.flush()
            system.run_with_images(args.test_image_left, args.test_image_right)
        else:
            # 正常模式：使用相机
            print("\n启动双目摄像头模式...")
            sys.stdout.flush()
            system.run(args.left_camera, args.right_camera)

    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
