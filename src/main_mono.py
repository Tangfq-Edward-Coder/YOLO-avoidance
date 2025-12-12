"""
单目模式主程序
用于Windows调试，使用单目摄像头
"""

from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到Python路径
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import argparse
import time
import cv2
import numpy as np
import yaml

from src.camera.mono_camera import MonoCamera
from src.detection import YOLODetector
from src.stereo.mono_depth_estimator import MonoDepthEstimator
from src.fusion import InfoFusion
from src.risk import RiskAssessor
from src.interface import BrakeInterface, RadarFusionInterface
from src.display import BEVDisplay, OpenCVDisplay

# 可选导入分割模块
try:
    from src.segmentation import UNetSegmenter

    SEGMENTATION_AVAILABLE = True
except ImportError:
    SEGMENTATION_AVAILABLE = False
    print("Warning: Segmentation module not available, skipping segmentation")


class MonoObstacleAvoidanceSystem:
    """单目模式实时视觉避障系统主类"""

    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化系统

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)

        # 初始化各个模块
        import sys

        print("Initializing monocular camera module...")
        sys.stdout.flush()
        camera_config = self.config["camera"]
        self.camera = MonoCamera(
            camera_id=0,
            image_width=camera_config["image_width"],
            image_height=camera_config["image_height"],
        )

        print("Initializing detection module...")
        sys.stdout.flush()
        # 使用默认YOLO模型（如果HEF不存在）
        yolo_model = self.config["models"]["yolo_model"]
        print(f"  Model path: {yolo_model}")
        sys.stdout.flush()

        if not Path(yolo_model).exists():
            print(
                f"  Warning: Model file {yolo_model} not found, using default YOLOv8n model"
            )
            yolo_model = "yolov8n.pt"
            sys.stdout.flush()

        try:
            print("  Initializing detector (may download model on first run)...")
            sys.stdout.flush()
            self.detector = YOLODetector(yolo_model, config_path)
            print("  ✓ Detector initialized successfully")
            sys.stdout.flush()
        except Exception as e:
            print(f"  ✗ Detector initialization failed: {e}")
            import traceback

            traceback.print_exc()
            sys.stdout.flush()
            print("  Trying default model...")
            sys.stdout.flush()
            try:
                self.detector = YOLODetector("yolov8n.pt", config_path)
                print("  ✓ Default model loaded successfully")
                sys.stdout.flush()
            except Exception as e2:
                print(f"  ✗ Default model also failed: {e2}")
                import traceback

                traceback.print_exc()
                raise

        print("Initializing segmentation module...")
        # 分割模块可选（如果模型不存在可以跳过）
        self.use_segmentation = False
        if SEGMENTATION_AVAILABLE:
            unet_model = self.config["models"]["unet_model"]
            if Path(unet_model).exists():
                try:
                    self.segmenter = UNetSegmenter(unet_model, config_path)
                    self.use_segmentation = True
                    print("   ✓ Segmentation module enabled")
                    sys.stdout.flush()
                except Exception as e:
                    print(
                        f"   Segmentation module initialization failed: {e}, skipping segmentation"
                    )
                    self.use_segmentation = False
            else:
                print(
                    f"   Warning: Segmentation model {unet_model} not found, skipping segmentation"
                )
                self.use_segmentation = False
        else:
            print("   Segmentation module not available, skipping segmentation")

        print("Initializing depth estimation module...")
        self.depth_estimator = MonoDepthEstimator(
            focal_length=camera_config["focal_length"]
        )

        print("Initializing information fusion module...")
        self.info_fusion = InfoFusion(config_path)

        print("Initializing risk assessment module...")
        self.risk_assessor = RiskAssessor(config_path)

        print("Initializing interface module...")
        self.brake_interface = BrakeInterface()
        self.radar_fusion = RadarFusionInterface()

        # 显示模式：'opencv', 'bev', 或 'both'（同时显示两个）
        self.display_mode = getattr(self, "display_mode", "bev")

        print(f"Initializing display module (mode: {self.display_mode})...")
        if self.display_mode == "opencv":
            self.display = OpenCVDisplay(config_path)
            self.bev_display = None
        elif self.display_mode == "both":
            # 同时初始化两个显示模块
            self.display = OpenCVDisplay(config_path)
            self.bev_display = BEVDisplay(config_path)
            print("  ✓ OpenCV display initialized")
            print("  ✓ BEV display initialized")
        else:
            self.display = BEVDisplay(config_path)
            self.bev_display = None

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

    def process_frame(self, image: np.ndarray) -> dict:
        """
        处理单帧图像

        Args:
            image: 输入图像

        Returns:
            处理结果字典
        """
        start_time = time.time()

        # 1. YOLO目标检测
        detections = self.detector.detect(image)

        # 2. U-Net精细分割（可选）
        segmentation_masks = []
        if self.use_segmentation:
            for detection in detections:
                try:
                    mask = self.segmenter.segment(image, detection["bbox"])
                    segmentation_masks.append(mask)
                except Exception as e:
                    print(f"Segmentation failed: {e}")
                    # 创建简单掩膜
                    x1, y1, x2, y2 = [int(v) for v in detection["bbox"]]
                    mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
                    mask[y1:y2, x1:x2] = 255
                    segmentation_masks.append(mask)
        else:
            # 如果没有分割模块，使用bbox创建简单掩膜
            for detection in detections:
                x1, y1, x2, y2 = [int(v) for v in detection["bbox"]]
                mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
                mask[y1:y2, x1:x2] = 255
                segmentation_masks.append(mask)

        # 3. 单目深度估计
        disparity, depth_map = self.depth_estimator.compute_disparity_and_depth(
            image, image, detections
        )

        # 4. 信息融合
        fused_objects = self.info_fusion.fuse_detection_and_depth(
            detections, segmentation_masks, depth_map
        )

        # 5. 过滤无效障碍物
        filtered_objects = self.info_fusion.filter_by_depth(
            fused_objects, min_depth=0.5, max_depth=10.0
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

    def run(self, camera_id: int = 0):
        """
        运行主循环

        Args:
            camera_id: 相机设备ID
        """
        print(f"Opening monocular camera (ID: {camera_id})...")
        self.camera.camera_id = camera_id
        self.camera.open()

        self.running = True
        print("System started, processing...")
        print("Press ESC to exit")

        try:
            while self.running:
                # 读取图像
                left_img, right_img = self.camera.read()

                if left_img is None:
                    print("Warning: Unable to read image")
                    time.sleep(0.1)
                    continue

                # 处理帧
                result = self.process_frame(left_img)

                # 更新FPS
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_time)
                    self.frame_count = 0
                    self.last_time = current_time

                # 更新显示
                if self.display_mode == "opencv":
                    # OpenCV显示需要传入原始图像
                    continue_running = self.display.update(
                        left_img, result["objects"], result["risk_info"], self.fps
                    )
                    if not continue_running:
                        break
                elif self.display_mode == "both":
                    # 同时更新两个显示
                    # OpenCV显示（视频流+标注）
                    continue_running_opencv = self.display.update(
                        left_img, result["objects"], result["risk_info"], self.fps
                    )
                    # BEV显示（鸟瞰图）
                    self.bev_display.update(
                        result["objects"], result["risk_info"], self.fps
                    )
                    # 处理BEV事件
                    continue_running_bev = self.bev_display.handle_events()

                    if not continue_running_opencv or not continue_running_bev:
                        break
                else:
                    # BEV显示（鸟瞰图）
                    self.display.update(
                        result["objects"], result["risk_info"], self.fps
                    )
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
            print("\nInterrupt signal received, shutting down...")
        except Exception as e:
            print(f"Runtime error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.shutdown()

    def shutdown(self):
        """关闭系统"""
        print("Shutting down system...")
        self.running = False
        self.camera.release()
        self.display.close()
        if self.bev_display is not None:
            self.bev_display.close()
        print("System closed")

    def run_with_image(self, image_path: str):
        """
        使用图像文件运行（用于测试）

        Args:
            image_path: 图像路径
        """
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError("无法读取图像文件")

        result = self.process_frame(image)

        # 显示结果
        if self.display_mode == "opencv":
            # OpenCV显示
            while True:
                continue_running = self.display.update(
                    image, result["objects"], result["risk_info"], 0.0
                )
                if not continue_running:
                    break
                time.sleep(0.03)  # 约30 FPS
        elif self.display_mode == "both":
            # 同时显示两个界面
            while True:
                # OpenCV显示
                continue_running_opencv = self.display.update(
                    image, result["objects"], result["risk_info"], 0.0
                )
                # BEV显示
                self.bev_display.update(result["objects"], result["risk_info"], 0.0)
                continue_running_bev = self.bev_display.handle_events()

                if not continue_running_opencv or not continue_running_bev:
                    break
                time.sleep(0.03)  # 约30 FPS
        else:
            # BEV显示（鸟瞰图）
            self.display.update(result["objects"], result["risk_info"], 0.0)
            # 等待用户关闭
            while self.display.handle_events():
                time.sleep(0.1)

        self.display.close()
        if self.bev_display is not None:
            self.bev_display.close()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Real-time Visual Obstacle Avoidance System - Monocular Mode (Windows Debug)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/system_config_mono.yaml",
        help="Configuration file path",
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID")
    parser.add_argument("--test-image", type=str, default=None, help="Test image path")
    parser.add_argument(
        "--display",
        type=str,
        default="bev",
        choices=["opencv", "bev", "both"],
        help="Display mode: 'opencv' (OpenCV video stream+annotations), 'bev' (Pygame bird's eye view, default), or 'both' (both displays)",
    )

    return parser.parse_args()


def main():
    """主函数"""
    import sys

    try:
        print("=" * 60)
        print("Real-time Visual Obstacle Avoidance System - Monocular Mode")
        print("=" * 60)
        sys.stdout.flush()

        args = parse_args()
        print(f"Config file: {args.config}")
        print(f"Camera ID: {args.camera}")
        print(f"Display mode: {args.display}")
        sys.stdout.flush()

        # 创建系统实例
        print("\nInitializing system...")
        sys.stdout.flush()
        system = MonoObstacleAvoidanceSystem(args.config)
        # 设置显示模式
        system.display_mode = args.display
        # 根据显示模式重新初始化显示模块
        if args.display == "opencv":
            system.display.close()  # 关闭之前初始化的BEV显示
            system.display = OpenCVDisplay(args.config)
            system.bev_display = None
        elif args.display == "both":
            # 同时初始化两个显示模块
            system.display.close()  # 关闭之前初始化的BEV显示
            system.display = OpenCVDisplay(args.config)
            system.bev_display = BEVDisplay(args.config)
            print("  ✓ Dual display mode enabled (OpenCV + BEV)")
        else:
            system.display.close()  # 关闭之前初始化的显示
            system.display = BEVDisplay(args.config)
            system.bev_display = None

        # 运行系统
        if args.test_image:
            # 测试模式：使用图像文件
            print(f"\nUsing test image: {args.test_image}")
            sys.stdout.flush()
            system.run_with_image(args.test_image)
        else:
            # 正常模式：使用相机
            print("\nStarting camera mode...")
            sys.stdout.flush()
            system.run(args.camera)

    except KeyboardInterrupt:
        print("\n\nUser interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
