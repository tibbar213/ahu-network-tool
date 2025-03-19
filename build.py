import PyInstaller.__main__
import os
from PIL import Image

def create_ico():
    """创建图标文件"""
    if not os.path.exists('icon.ico'):
        # 创建一个蓝色背景的图标
        icon = Image.new('RGB', (64, 64), "#1976D2")
        icon.save('icon.ico')

def build():
    """打包应用"""
    create_ico()
    
    PyInstaller.__main__.run([
        'ahu_network_tool.py',
        '--name=校园网登录工具',
        '--noconsole',
        '--onefile',
        '--icon=icon.ico',
        '--add-data=icon.ico;.',
        '--clean'
    ])

if __name__ == '__main__':
    build() 