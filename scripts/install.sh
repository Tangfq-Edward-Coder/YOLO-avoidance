#!/bin/bash
# 快速安装脚本
# 用于在树莓派上快速安装系统依赖

set -e

echo "=========================================="
echo "实时视觉避障系统 - 安装脚本"
echo "=========================================="

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then 
   echo "请不要使用root用户运行此脚本"
   exit 1
fi

# 更新系统
echo "更新系统包..."
sudo apt update
sudo apt upgrade -y

# 安装基础工具
echo "安装基础工具..."
sudo apt install -y git wget curl vim build-essential

# 安装Python环境
echo "安装Python环境..."
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装系统依赖
echo "安装系统依赖..."
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y python3-pygame
sudo apt install -y python3-yaml

# 安装GStreamer（可选）
echo "安装GStreamer..."
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly python3-gst-1.0

# 创建虚拟环境
echo "创建Python虚拟环境..."
if [ ! -d "$HOME/obstacle_avoidance_env" ]; then
    python3 -m venv ~/obstacle_avoidance_env
    echo "虚拟环境已创建: ~/obstacle_avoidance_env"
else
    echo "虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境并安装Python包
echo "安装Python依赖..."
source ~/obstacle_avoidance_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 配置用户权限
echo "配置用户权限..."
sudo usermod -a -G video $USER
echo "已将用户 $USER 添加到video组"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p ~/YCTarget/models
mkdir -p ~/YCTarget/logs
mkdir -p ~/YCTarget/calibration_images

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 重新登录以使权限生效，或运行: newgrp video"
echo "2. 进行相机标定: python scripts/calibrate_stereo.py --images-dir ./calibration_images"
echo "3. 配置 configs/system_config.yaml"
echo "4. 将模型文件放入 models/ 目录"
echo "5. 运行系统: python src/main.py"
echo ""
echo "详细文档请参考: docs/DEPLOYMENT.md"
echo ""

