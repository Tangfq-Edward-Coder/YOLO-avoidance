#!/bin/bash
# 省实未来汽车 - 视觉避障系统环境配置脚本
# 自动化完成驱动安装、依赖库部署、Hailo运行时环境配置

set -e

echo "=========================================="
echo "省实未来汽车 - 视觉避障系统环境配置"
echo "=========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用sudo运行此脚本"
    exit 1
fi

# 1. 更新系统包
echo "[1/6] 更新系统包..."
apt-get update
apt-get upgrade -y

# 2. 安装基础依赖
echo "[2/6] 安装基础依赖..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    python3-opencv \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    curl

# 3. 安装语音提示依赖（espeak）
echo "[3/6] 安装语音提示依赖..."
apt-get install -y espeak espeak-data

# 4. 安装Hailo-8 SDK（如果存在）
echo "[4/6] 检查Hailo-8 SDK..."
if [ -d "/opt/hailo" ] || command -v hailo_platform &> /dev/null; then
    echo "检测到Hailo-8 SDK，跳过安装"
else
    echo "未检测到Hailo-8 SDK，请手动安装"
    echo "参考: https://hailo.ai/developer-zone/"
fi

# 5. 创建Python虚拟环境
echo "[5/6] 创建Python虚拟环境..."
PROJECT_DIR="/opt/visual_obstacle_avoidance"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
fi

# 激活虚拟环境并安装Python依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. 创建系统服务
echo "[6/6] 配置系统服务..."
SERVICE_FILE="/etc/systemd/system/visual-obstacle-avoidance.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=省实未来汽车 - 视觉避障与道路风险预警系统
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/src/main.py --left-camera 0 --right-camera 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "系统服务已创建，使用以下命令启用："
echo "  sudo systemctl enable visual-obstacle-avoidance.service"
echo "  sudo systemctl start visual-obstacle-avoidance.service"

echo ""
echo "=========================================="
echo "环境配置完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 配置相机标定参数（运行 scripts/calibrate_stereo.py）"
echo "2. 更新配置文件 configs/system_config.yaml"
echo "3. 将模型文件放入 models/ 目录"
echo "4. 运行 start_system.sh 启动系统"

