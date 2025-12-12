"""
双目相机标定脚本
用于获取相机内参、畸变系数和立体校正参数
"""
from __future__ import annotations

import argparse
import cv2
import numpy as np
import yaml
from pathlib import Path
import glob


def calibrate_stereo(
    images_dir: str,
    board_width: int,
    board_height: int,
    square_size: float,
    output_file: str = "calibration_result.yaml"
):
    """
    执行双目相机标定
    
    Args:
        images_dir: 标定图像目录
        board_width: 棋盘格宽度（内角点数）
        board_height: 棋盘格高度（内角点数）
        square_size: 方格尺寸（米）
        output_file: 输出文件路径
    """
    # 准备对象点
    objp = np.zeros((board_width * board_height, 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_width, 0:board_height].T.reshape(-1, 2)
    objp *= square_size
    
    # 存储对象点和图像点
    objpoints = []  # 3D点
    imgpoints_left = []  # 左图像点
    imgpoints_right = []  # 右图像点
    
    # 查找标定图像
    left_images = sorted(glob.glob(f"{images_dir}/left_*.jpg"))
    right_images = sorted(glob.glob(f"{images_dir}/right_*.jpg"))
    
    if len(left_images) != len(right_images):
        raise ValueError("左右图像数量不匹配")
    
    print(f"找到 {len(left_images)} 对图像")
    
    # 处理每对图像
    for i, (left_path, right_path) in enumerate(zip(left_images, right_images)):
        print(f"处理图像对 {i+1}/{len(left_images)}: {Path(left_path).name}")
        
        left_img = cv2.imread(left_path)
        right_img = cv2.imread(right_path)
        
        if left_img is None or right_img is None:
            print(f"  警告: 无法读取图像，跳过")
            continue
        
        left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
        
        # 查找角点
        ret_left, corners_left = cv2.findChessboardCorners(
            left_gray, (board_width, board_height), None
        )
        ret_right, corners_right = cv2.findChessboardCorners(
            right_gray, (board_width, board_height), None
        )
        
        if ret_left and ret_right:
            objpoints.append(objp)
            
            # 细化角点
            corners_left = cv2.cornerSubPix(
                left_gray, corners_left, (11, 11), (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )
            corners_right = cv2.cornerSubPix(
                right_gray, corners_right, (11, 11), (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )
            
            imgpoints_left.append(corners_left)
            imgpoints_right.append(corners_right)
            
            print(f"  ✓ 找到角点")
        else:
            print(f"  ✗ 未找到角点")
    
    if len(objpoints) < 10:
        raise ValueError(f"有效图像对数量不足 ({len(objpoints)} < 10)，需要至少10对")
    
    print(f"\n使用 {len(objpoints)} 对有效图像进行标定...")
    
    # 单目标定（左相机）
    ret_left, mtx_left, dist_left, rvecs_left, tvecs_left = cv2.calibrateCamera(
        objpoints, imgpoints_left, left_gray.shape[::-1], None, None
    )
    
    # 单目标定（右相机）
    ret_right, mtx_right, dist_right, rvecs_right, tvecs_right = cv2.calibrateCamera(
        objpoints, imgpoints_right, right_gray.shape[::-1], None, None
    )
    
    # 立体标定
    ret_stereo, mtx_left, dist_left, mtx_right, dist_right, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints_left, imgpoints_right,
        mtx_left, dist_left, mtx_right, dist_right,
        left_gray.shape[::-1],
        flags=cv2.CALIB_FIX_INTRINSIC
    )
    
    print(f"\n标定完成!")
    print(f"左相机重投影误差: {ret_left:.4f}")
    print(f"右相机重投影误差: {ret_right:.4f}")
    print(f"立体标定误差: {ret_stereo:.4f}")
    
    # 立体校正
    R1, R2, P1, P2, Q, validPixROI1, validPixROI2 = cv2.stereoRectify(
        mtx_left, dist_left, mtx_right, dist_right,
        left_gray.shape[::-1], R, T
    )
    
    # 保存结果
    result = {
        'left_camera_matrix': mtx_left.tolist(),
        'right_camera_matrix': mtx_right.tolist(),
        'left_dist_coeffs': dist_left.tolist(),
        'right_dist_coeffs': dist_right.tolist(),
        'R': R.tolist(),
        'T': T.tolist(),
        'R1': R1.tolist(),
        'R2': R2.tolist(),
        'P1': P1.tolist(),
        'P2': P2.tolist(),
        'Q': Q.tolist(),
        'image_width': left_gray.shape[1],
        'image_height': left_gray.shape[0],
        'baseline': np.linalg.norm(T),
        'focal_length': (mtx_left[0, 0] + mtx_left[1, 1]) / 2
    }
    
    with open(output_file, 'w') as f:
        yaml.dump(result, f, default_flow_style=False)
    
    print(f"\n结果已保存到: {output_file}")
    print(f"基线距离: {result['baseline']:.4f} 米")
    print(f"焦距: {result['focal_length']:.2f} 像素")


def main():
    parser = argparse.ArgumentParser(description="双目相机标定")
    parser.add_argument("--images-dir", type=str, required=True, help="标定图像目录")
    parser.add_argument("--board-width", type=int, default=9, help="棋盘格宽度（内角点数）")
    parser.add_argument("--board-height", type=int, default=6, help="棋盘格高度（内角点数）")
    parser.add_argument("--square-size", type=float, default=0.025, help="方格尺寸（米）")
    parser.add_argument("--output", type=str, default="calibration_result.yaml", help="输出文件")
    
    args = parser.parse_args()
    
    calibrate_stereo(
        args.images_dir,
        args.board_width,
        args.board_height,
        args.square_size,
        args.output
    )


if __name__ == "__main__":
    main()

