"""
主系统集成
整合所有模块，实现完整的实时视觉避障系统
"""

from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到Python路径
# 注意：必须在导入src模块之前设置路径
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 导入标准库
import argparse
import time
import cv2
import numpy as np
import yaml

# 导入项目模块（必须在路径设置之后）
from src.camera import StereoCamera
from src.detection import YOLODetector
from src.segmentation import UNetSegmenter
from src.stereo import StereoMatcher
from src.fusion import InfoFusion
from src.risk import RiskAssessor
from src.interface import BrakeInterface, RadarFusionInterface
from src.display import BEVDisplay


class ObstacleAvoidanceSystem:
    """实时视觉避障系统主类"""

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

        print("初始化风险评估模块...")
        self.risk_assessor = RiskAssessor(config_path)

        print("初始化接口模块...")
        self.brake_interface = BrakeInterface()
        self.radar_fusion = RadarFusionInterface()

        print("初始化显示模块...")
        self.display = BEVDisplay(config_path)

        # 性能统计
        self.frame_count = 0
        self.fps = 0.0
        self.last_time = time.time()

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

        # 1. YOLO目标检测
        detections = self.detector.detect(left_image)

        # 2. U-Net精细分割（对每个检测到的目标）
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

        # 5. 过滤无效障碍物
        filtered_objects = self.info_fusion.filter_by_depth(
            fused_objects, min_depth=0.1, max_depth=10.0
        )

        # 6. 雷达融合（如果有雷达数据）
        if len(self.radar_fusion.get_radar_objects()) > 0:
            filtered_objects = self.radar_fusion.fuse_with_vision(filtered_objects)

        # 7. 碰撞风险评估
        risk_info = self.risk_assessor.assess_risk(filtered_objects)

        # 8. 触发刹车（如果需要）
        if risk_info["should_brake"]:
            self.brake_interface.brake_interface(risk_info["risk_level"])
        else:
            self.brake_interface.release_brake()

        # 计算处理时间
        process_time = time.time() - start_time

        return {
            "detections": detections,
            "segmentation_masks": segmentation_masks,
            "disparity": disparity,
            "depth_map": depth_map,
            "objects": filtered_objects,
            "risk_info": risk_info,
            "process_time": process_time,
        }

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

        try:
            while self.running:
                # 读取图像
                left_img, right_img = self.camera.read()

                if left_img is None or right_img is None:
                    print("警告: 无法读取图像")
                    time.sleep(0.1)
                    continue

                # 处理帧
                result = self.process_frame(left_img, right_img)

                # 更新FPS
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_time)
                    self.frame_count = 0
                    self.last_time = current_time

                # 更新显示
                self.display.update(result["objects"], result["risk_info"], self.fps)

                # 处理事件
                if not self.display.handle_events():
                    break

                # 打印性能信息
                if self.frame_count % 30 == 0:
                    print(
                        f"FPS: {self.fps:.2f}, "
                        f"处理时间: {result['process_time'] * 1000:.2f}ms, "
                        f"障碍物数: {len(result['objects'])}"
                    )

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
        self.display.close()
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

        # 显示结果
        self.display.update(result["objects"], result["risk_info"], 0.0)

        # 等待用户关闭
        while self.display.handle_events():
            time.sleep(0.1)

        self.display.close()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="基于树莓派与Hailo-8的实时视觉避障系统"
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
    import sys

    try:
        print("=" * 60)
        print("实时视觉避障系统 - 双目模式")
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
        system = ObstacleAvoidanceSystem(args.config)

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
