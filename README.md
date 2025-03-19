# 校园网登录工具

这是一个用于安徽大学校园网自动登录的工具。它提供了以下功能：

- 图形化界面，方便操作
- 系统托盘运行，不占用桌面空间
- 自动保持连接
- 开机自启动
- 配置文件保存账号密码

![image](https://github.com/user-attachments/assets/8e3d63f8-7f2e-4100-9517-2463ac0bf7ef)

## 安装

1. 下载最新的发布版本
2. 运行 `ahu_network_tool.exe`

## 使用说明

1. 输入校园网账号和密码
2. 点击"登录"按钮进行连接
3. 可选择是否开机自启和保持连接
4. 最小化后会自动隐藏到系统托盘
5. 双击托盘图标可重新打开主界面

## 开发环境

- Python 3.8+
- 依赖包见 requirements.txt

## 从源码构建

1. 克隆仓库
```bash
git clone https://github.com/yourusername/ahu-network-tool.git
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 打包成exe
```bash
pyinstaller --noconsole --onefile --icon=icon.ico ahu_network_tool.py
```

## 注意事项

- 本工具仅供学习交流使用
- 请勿将账号密码分享给他人
- 使用过程中遇到问题请提交 Issue 