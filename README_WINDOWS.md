# Windows调试版快速指南

> 💡 **提示**: 这是Windows环境下的单目模式调试版本，用于开发测试。生产环境请使用树莓派双目模式。

## 🚀 快速开始

### 方法1: 使用批处理脚本（推荐）

```bash
# 双击运行批处理脚本
run_mono.bat
```

### 方法2: 直接运行

```bash
# 默认模式（BEV鸟瞰图）
python src/main_mono.py --camera 0

# OpenCV显示模式（实时视频流+障碍物标注）
python src/main_mono.py --camera 0 --display opencv

# 双显示模式（同时显示OpenCV和BEV）
python src/main_mono.py --camera 0 --display both
```

### 方法3: 使用模块方式

```bash
python -m src.main_mono --camera 0 --display opencv
```

### 方法4: 手动运行

```bash
# 1. 激活虚拟环境（如果使用）
venv\Scripts\activate

# 2. 安装依赖（首次运行）
pip install -r requirements.txt

# 3. 运行系统（选择显示方式）
python src/main_mono.py --camera 0 --display opencv  # OpenCV显示
python src/main_mono.py --camera 0 --display bev     # BEV显示（默认）
python src/main_mono.py --camera 0 --display both    # 双显示
```

## 命令行参数

```bash
# 使用默认摄像头（ID=0，BEV显示）
python src/main_mono.py

# 指定摄像头ID
python src/main_mono.py --camera 1

# 选择显示模式
python src/main_mono.py --camera 0 --display opencv  # OpenCV显示
python src/main_mono.py --camera 0 --display bev     # BEV显示
python src/main_mono.py --camera 0 --display both    # 双显示

# 使用自定义配置文件
python src/main_mono.py --config configs/system_config_mono.yaml

# 使用测试图像
python src/main_mono.py --test-image test.jpg --display opencv
```

## 显示模式说明

| 模式 | 说明 | 特点 |
|------|------|------|
| **bev** (默认) | Pygame鸟瞰图 | 3D雷达界面，障碍物位置可视化 |
| **opencv** | OpenCV视频流 | 实时视频流+障碍物标注，信息面板 |
| **both** | 双显示 | 同时显示OpenCV和BEV两个窗口 |

## ✨ 功能说明

### ✅ 支持的功能

| 功能 | 说明 |
|------|------|
| **实时目标检测** | 使用YOLO检测障碍物，支持多种类别 |
| **深度估计** | 基于检测框大小估计深度（单目模式） |
| **风险评估** | 碰撞风险评估，自动触发刹车决策 |
| **可视化显示** | 两种显示模式可选：<br>- OpenCV：实时视频流+障碍物标注<br>- Pygame：鸟瞰图界面 |
| **障碍物标注** | 边界框、类别、置信度、距离信息实时显示 |
| **刹车接口** | 软件刹车接口，支持回调函数 |

### ⚠️ 限制说明

| 限制项 | 说明 |
|--------|------|
| **深度精度** | 单目模式下深度估计精度较低（约10-20%误差） |
| **立体匹配** | 不支持（需要双目摄像头） |
| **Hailo加速** | Windows不支持Hailo-8，使用CPU/GPU推理 |

## 💻 系统要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Windows 10/11 |
| **Python** | 3.11+ |
| **摄像头** | USB或内置摄像头 |
| **内存** | 至少4GB RAM |
| **GPU** | 可选，推荐使用GPU加速（CUDA） |

## ❓ 常见问题

### Q1: ModuleNotFoundError: No module named 'src'

**状态**: ✅ 已修复

**解决方案**:
- 代码已自动处理路径问题，直接运行即可
- 如果仍然出现，确保在项目根目录运行
- 或使用模块方式: `python -m src.main_mono`

### Q2: 摄像头无法打开

**解决方案**:
```bash
# 尝试不同的摄像头ID
python src/main_mono.py --camera 0
python src/main_mono.py --camera 1
python src/main_mono.py --camera 2
```

**检查步骤**:
1. 确认摄像头未被其他程序占用
2. 检查设备管理器中的摄像头驱动
3. 尝试重启电脑

### Q3: 模型下载慢或失败

**原因**: YOLO首次运行会自动下载预训练模型（约6MB）

**解决方案**:
- 确保网络连接正常
- 使用VPN或代理（如果网络受限）
- 手动下载模型文件到项目目录

### Q4: PowerShell没有输出

**原因**: PowerShell可能抑制了输出

**解决方案**:
```bash
# 方法1: 使用CMD
cmd /c "python src/main_mono.py --camera 0"

# 方法2: 重定向到文件
python src/main_mono.py --camera 0 > output.log 2>&1
type output.log

# 方法3: 在IDE中运行（推荐）
# 直接在VSCode/PyCharm中运行
```

### Q5: 性能问题（FPS低）

**优化建议**:
1. **降低分辨率**: 修改 `configs/system_config_mono.yaml` 中的图像尺寸
2. **提高检测阈值**: 减少检测目标数量
3. **使用GPU加速**: 如果安装了CUDA版本的PyTorch
4. **关闭不必要的程序**: 释放系统资源

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [Windows调试文档](docs/WINDOWS_DEBUG.md) | 详细的Windows调试说明和故障排除 |
| [完整部署文档](docs/DEPLOYMENT.md) | 树莓派部署完整指南 |
| [API文档](docs/API.md) | 完整的API接口说明 |
| [快速参考](docs/QUICK_REFERENCE.md) | 常用命令和配置快速参考 |
| [主README](README.md) | 项目主文档 |

## 🎯 下一步

完成Windows调试后，可以部署到树莓派生产环境：

1. ✅ **功能验证**: 在Windows上完成功能测试
2. 📐 **相机标定**: 参考 `docs/DEPLOYMENT.md` 进行双目相机标定
3. 🔄 **模型转换**: 将模型转换为HEF格式以使用Hailo-8加速
4. 🚀 **部署上线**: 在树莓派上部署完整系统

---

💡 **提示**: Windows调试模式主要用于功能开发和测试，生产环境建议使用树莓派双目模式以获得最佳性能和精度。

