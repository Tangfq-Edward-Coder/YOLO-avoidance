#!/bin/bash
# 省实未来汽车 - 视觉避障系统一键启动脚本
# 实现上电后系统自启动，并自动加载所有服务

set -e

echo "=========================================="
echo "省实未来汽车 - 视觉避障系统启动"
echo "=========================================="

# 项目目录
PROJECT_DIR="/opt/visual_obstacle_avoidance"
CONFIG_FILE="$PROJECT_DIR/configs/system_config.yaml"

# 检查项目目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "错误: 项目目录不存在: $PROJECT_DIR"
    echo "请先运行 setup.sh 进行环境配置"
    exit 1
fi

cd "$PROJECT_DIR"

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "警告: 配置文件不存在: $CONFIG_FILE"
    echo "使用默认配置"
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "错误: Python虚拟环境不存在"
    echo "请先运行 setup.sh 进行环境配置"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查模型文件
if [ ! -f "models/yolo_obstacle.hef" ] && [ ! -f "models/yolo_obstacle.onnx" ]; then
    echo "警告: YOLO模型文件不存在"
    echo "请将模型文件放入 models/ 目录"
fi

if [ ! -f "models/unet_obstacle.hef" ] && [ ! -f "models/unet_obstacle.onnx" ]; then
    echo "警告: U-Net模型文件不存在"
    echo "请将模型文件放入 models/ 目录"
fi

# 启动系统
echo "启动系统..."
echo "配置文件: $CONFIG_FILE"
echo "左摄像头: 0"
echo "右摄像头: 1"
echo ""

python src/main.py \
    --config "$CONFIG_FILE" \
    --left-camera 0 \
    --right-camera 1

echo ""
echo "系统已退出"

