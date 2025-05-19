#!/usr/bin/env python
"""
启动RiverInfos应用程序
"""
import os
import subprocess
import sys

def main():
    """主函数"""
    # 确保当前目录是项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 运行Streamlit应用
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    try:
        print("启动RiverInfos应用程序...")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n应用程序已停止")
    except Exception as e:
        print(f"启动应用程序时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 