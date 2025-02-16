import subprocess
import sys
import platform
import streamlit as st
from flask_app import flask_app, FLASK_APP_PORT, STREAMLIT_APP_PORT, streamlit_ui
from streamlit_app import STREAMLIT_BASE_PATH

# 全局变量存储Flask子进程
flask_process = None

def start_flask():
    global flask_process
    if flask_process != None:
        return

    # 跨平台兼容的命令行参数处理
    if platform.system() == "Windows":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        creationflags = 0
    
    # 启动Flask子进程并传递端口号
    flask_process = subprocess.Popen(
        [sys.executable, 'flask_app.py', f'--port={FLASK_APP_PORT}', '--host=0.0.0.0', f'--debug=True'],
        creationflags=creationflags
    )

def stop_flask():
    global flask_process
    if flask_process:
        flask_process.terminate()
        flask_process.wait()
        flask_process = None

def start_streamlit():
    if st.runtime.exists():
        streamlit_ui()
    else:
        from streamlit.web.cli import main
        import sys
        sys.argv = [
            "streamlit", "run", __file__,
            f"--server.port={STREAMLIT_APP_PORT}",
            f"--server.baseUrlPath={STREAMLIT_BASE_PATH}",
            "--server.headless=true"
        ]
        main()

import atexit

if __name__ == "__main__":
    # 启动Flask应用
    start_flask()
    
    # 注册退出处理函数
    atexit.register(stop_flask)

    # 启动Streamlit UI
    start_streamlit()
