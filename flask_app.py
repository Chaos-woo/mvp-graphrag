import argparse
from flask import Flask, request, jsonify
import streamlit as st
from preprocessor import Preprocessor
from knowledge_graph import KnowledgeGraph
import os
from werkzeug.utils import secure_filename
import pandas as pd
import docx
import threading
import logging

from query_processor import QueryProcessor
from streamlit_app import STREAMLIT_APP_PORT, STREAMLIT_BASE_PATH, streamlit_ui, FLASK_APP_PORT, FLASK_BASE_PATH

# 解析命令行参数
parser = argparse.ArgumentParser(description='启动Flask应用')
parser.add_argument('--port', type=int, default=FLASK_APP_PORT, help='Flask应用端口号')
parser.add_argument('--host', type=str, default='0.0.0.0', help='Flask应用主机地址')
parser.add_argument('--debug', type=bool, default=False, help='是否启用调试模式')

flask_app = Flask(__name__)

# 文件上传配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'docx', 'xlsx'}
flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 全局任务状态
task_status = {
    'is_running': False,
    'progress': 0,
    'graph': None,
    'preprocessor': None
}
task_lock = threading.Lock()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_content(filepath):
    if filepath.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    elif filepath.endswith('.docx'):
        doc = docx.Document(filepath)
        return '\n'.join([para.text for para in doc.paragraphs])
    elif filepath.endswith('.xlsx'):
        df = pd.read_excel(filepath)
        return df.to_string()
    return ''

def analyze_task(text):
    global task_status
    # 初始化模块
    with task_lock:
        task_status['is_running'] = True
        task_status['progress'] = 0
        task_status['graph'] = KnowledgeGraph()
        task_status['preprocessor'] = Preprocessor()

    preprocessor = task_status['preprocessor']

    def progress_callback(progress, phase=0):
        """
        phase: 0 - 预处理阶段，1 - 知识图谱构建阶段
        """
        with task_lock:
            # 预处理阶段占50%，知识图谱构建阶段占50%
            task_status['progress'] = (progress * 0.5) + (phase * 50)

    # 预处理
    preprocess_result = preprocessor.process(text, progress_callback=progress_callback)
    if preprocess_result != None:
        unique_entities, relations = preprocess_result

        # 构建知识图谱
        task_status['graph'].add_entities(unique_entities, lambda p: progress_callback(p, 1))
        task_status['graph'].add_relations(relations, lambda p: progress_callback(p, 1))

    with task_lock:
        task_status['is_running'] = False

@flask_app.route(f'{FLASK_BASE_PATH}/analyze', methods=['POST'])
def analyze():
    # 获取输入文本或文件
    text = request.form.get('text', '')
    file = request.files.get('file')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text = read_file_content(filepath)

    if not text:
        return jsonify({'error': 'No input provided'}), 400

    # 启动异步任务
    thread = threading.Thread(target=analyze_task, daemon=True, args=(text,))
    thread.start()

    return jsonify({'status': 'started'}), 200

@flask_app.route(f'{FLASK_BASE_PATH}/progress', methods=['GET'])
def get_progress():
    with task_lock:
        return jsonify({
            'is_running': task_status['is_running'],
            'progress': task_status['progress']
        })

@flask_app.route(f'{FLASK_BASE_PATH}/stop', methods=['POST'])
def stop_analysis():
    with task_lock:
        if task_status['graph']:
            task_status['graph'].stop_analysis()
            task_status['preprocessor'].stop_analysis()
            task_status['is_running'] = False
            task_status['progress'] = 0
    return jsonify({'status': 'stopped'})

@flask_app.route(f'{FLASK_BASE_PATH}/query', methods=['POST'])
def query():
    data = request.get_json()
    query_text = data.get('query', '')

    if not query_text:
        return jsonify({'error': 'No query provided'}), 400

    # 初始化查询处理器
    graph: KnowledgeGraph = task_status['graph']
    query_processor = QueryProcessor(graph)

    # 处理查询
    result = query_processor.process_query(query_text)
    return jsonify({'result': result})

@flask_app.route(f'{FLASK_BASE_PATH}/graph', methods=['GET'])
def get_graph():
    with task_lock:
        if not task_status['graph']:
            return jsonify({'error': 'Graph not available'}), 404
        
        graph_data = task_status['graph'].to_dict()
        logging.info(f"{jsonify(graph_data)}")
        return jsonify(graph_data)

if __name__ == "__main__":
    args = parser.parse_args()
    
    # 启动Flask应用
    flask_app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )