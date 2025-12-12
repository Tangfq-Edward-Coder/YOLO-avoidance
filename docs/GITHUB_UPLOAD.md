# GitHub上传指南

本指南将帮助您将项目上传到GitHub。

## 📋 前置要求

1. **安装Git**
   - Windows: 下载并安装 [Git for Windows](https://git-scm.com/download/win)
   - 安装完成后，重启命令行工具

2. **GitHub账号**
   - 如果没有账号，请先注册 [GitHub账号](https://github.com/signup)

## 🚀 上传步骤

### 步骤1: 初始化Git仓库

在项目根目录打开命令行（PowerShell或CMD），执行：

```bash
# 初始化Git仓库
git init

# 配置用户信息（如果还没配置）
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 步骤2: 添加文件到Git

```bash
# 添加所有文件
git add .

# 检查要提交的文件（可选）
git status
```

### 步骤3: 创建初始提交

```bash
# 创建提交
git commit -m "Initial commit: Real-time Visual Obstacle Avoidance System"
```

### 步骤4: 在GitHub上创建仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角的 **"+"** 按钮，选择 **"New repository"**
3. 填写仓库信息：
   - **Repository name**: `YCTarget` (或您喜欢的名称)
   - **Description**: `Real-time Visual Obstacle Avoidance System based on Raspberry Pi and Hailo-8`
   - **Visibility**: 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"（因为我们已经有了）
4. 点击 **"Create repository"**

### 步骤5: 连接本地仓库到GitHub

GitHub会显示仓库URL，类似：`https://github.com/yourusername/YCTarget.git`

```bash
# 添加远程仓库（替换为您的实际URL）
git remote add origin https://github.com/yourusername/YCTarget.git

# 验证远程仓库
git remote -v
```

### 步骤6: 推送代码到GitHub

```bash
# 推送代码到GitHub（首次推送）
git branch -M main
git push -u origin main
```

如果提示输入用户名和密码：
- **用户名**: 您的GitHub用户名
- **密码**: 使用Personal Access Token（不是GitHub密码）
  - 如何创建Token: [GitHub Personal Access Token Guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

## 🔐 使用Personal Access Token（推荐）

GitHub已不再支持密码认证，需要使用Personal Access Token：

1. 登录GitHub，进入 **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. 点击 **"Generate new token"** → **"Generate new token (classic)"**
3. 填写信息：
   - **Note**: `YCTarget Project`
   - **Expiration**: 选择过期时间（建议90天或更长）
   - **Scopes**: 勾选 `repo`（完整仓库访问权限）
4. 点击 **"Generate token"**
5. **复制并保存Token**（只显示一次！）
6. 推送时，密码处输入这个Token

## 📝 后续更新

当您修改代码后，使用以下命令更新GitHub：

```bash
# 查看修改的文件
git status

# 添加修改的文件
git add .

# 提交修改
git commit -m "描述您的修改内容"

# 推送到GitHub
git push
```

## 🔍 验证上传

上传成功后，访问您的GitHub仓库URL，应该能看到所有文件。

## ⚠️ 注意事项

1. **不要上传敏感信息**：
   - API密钥
   - 密码
   - 个人配置信息
   - 大文件（>100MB）

2. **已忽略的文件**（.gitignore中已配置）：
   - `__pycache__/` - Python缓存文件
   - `*.pyc` - 编译的Python文件
   - `venv/` - 虚拟环境
   - `models/*.pt`, `models/*.onnx` - 模型文件
   - `*.log` - 日志文件
   - `yolov8n.pt` - YOLO模型文件

3. **如果需要上传模型文件**：
   - 使用 [Git LFS](https://git-lfs.github.com/) 上传大文件
   - 或使用GitHub Releases功能

## 🆘 常见问题

### Q: 提示 "remote origin already exists"
```bash
# 删除现有远程仓库
git remote remove origin

# 重新添加
git remote add origin https://github.com/yourusername/YCTarget.git
```

### Q: 推送时提示认证失败
- 确保使用Personal Access Token而不是密码
- 检查Token是否有`repo`权限
- 重新生成Token并重试

### Q: 想忽略已跟踪的文件
```bash
# 从Git中移除但保留本地文件
git rm --cached filename

# 然后更新.gitignore
# 最后提交
git commit -m "Remove tracked file"
```

## 📚 更多资源

- [Git官方文档](https://git-scm.com/doc)
- [GitHub文档](https://docs.github.com/)
- [Git教程](https://www.atlassian.com/git/tutorials)

---

**提示**: 如果遇到问题，可以查看Git错误信息，通常会有详细的解决方案。

