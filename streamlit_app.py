from networkx import edges
import streamlit as st
import requests
from pyvis.network import Network
from streamlit_chat import message
from streamlit_autorefresh import st_autorefresh
import networkx as nx

FLASK_APP_PORT = 9200
STREAMLIT_APP_PORT = 9201
STREAMLIT_BASE_PATH = "/graph-rag"
FLASK_BASE_PATH = "/graph-rag/api"

# Flask API地址
DOMAIN = f"http://localhost:{FLASK_APP_PORT}"
API_URL = f"{DOMAIN}/{FLASK_BASE_PATH}"

def check_analysis_status():
    try:
        response = requests.get(f"{API_URL}/progress")
        if response.status_code == 200:
            return response.json()
        return {'is_running': False, 'progress': 0}
    except:
        return {'is_running': False, 'progress': 0}

def start_analysis(text_input, uploaded_file):
    data = {'text': text_input}
    files = None
    
    if uploaded_file is not None:
        files = {'file': uploaded_file}
    
    # 开始分析任务
    response = requests.post(f"{API_URL}/analyze", data=data, files=files)
    return response.status_code == 200

def stop_analysis():
    response = requests.post(f"{API_URL}/stop")
    return response.status_code == 200

def get_graph():
    response = requests.get(f"{API_URL}/graph")
    if response.status_code == 200:
        return response.json()
    return None

def query_graph_rag(query):
    response = requests.post(f"{API_URL}/query", json={'query': query})
    if response.status_code == 200:
        return response.json()['result']
    return None

def visualize_graph(graph_data):
    if not graph_data:
        return
    
    G = nx.node_link_graph(graph_data, edges="links")
    net = Network(
        height="600px", 
        width="100%", 
        notebook=True
        )
    net.from_nx(G)
    
    net.show("graph.html")
    st.components.v1.html(open("graph.html", 'r', encoding='utf-8').read(), height=600)

def streamlit_ui():
    count = st_autorefresh(interval=3 * 1000, key="dataframerefresh")
    st.write(f"最后刷新时间: {count}")
    st.title("知识图谱分析系统")

    if 'user_past' not in st.session_state:
        st.session_state.user_past = []
    if 'generated' not in st.session_state:
        st.session_state.generated = []

    # 文件上传
    uploaded_file = st.file_uploader("上传文件", type=['txt', 'docx', 'xlsx'])
    text_input = st.text_area("或直接输入文本进行分析", height=200)

    # 分析控制
    status = check_analysis_status()
    if status['is_running']:
        if st.button("停止分析"):
            if stop_analysis():
                st.success("分析已停止")
            else:
                st.error("停止分析失败")
    else:
        if st.button("开始分析") and (text_input.strip() or uploaded_file is not None):
            if start_analysis(text_input=text_input, uploaded_file=uploaded_file):
                st.success("分析已开始")
            else:
                st.error("分析启动失败")

    # 进度条
    if status['is_running']:
        st.progress(status['progress'] / 100, f"分析进度: {status['progress']:.1f}%")
    else:
        if status['progress'] == 100:
            st.success("知识图谱分析完成")
            st.balloons()

    # 可视化
    graph_data = get_graph()
    if graph_data:
        st.write("知识图谱可视化")
        visualize_graph(graph_data)

    def on_input_change():
        query = st.session_state.user_input
        if query:
            st.session_state.user_past.append(query)
            generated = query_graph_rag(query)
            if generated:
                st.session_state.generated.append(generated)
            else:
                st.session_state.generated.append("服务异常，请重试")
        
    # 聊天界面
    st.subheader("知识图谱查询")
    chat_placeholder = st.empty()

    with chat_placeholder.container(height=500):    
        for i in range(len(st.session_state['generated'])):                
            message(st.session_state['user_past'][i], is_user=True, key=f"{i}_user")
            message(
                st.session_state['generated'][i], 
                key=f"{i}", 
                allow_html=True,
            )

    with st.container():
        st.text_input("输入查询问题:", on_change=on_input_change, key="user_input", )

