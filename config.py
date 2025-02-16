import os
from dotenv import load_dotenv

os.environ['OPENAI_API_KEY'] = 'sk-sxpqrpyhivyjaicexrdnehqknolpnokwndfxwykbxwfbtyku'
os.environ['CHAT_MODEL'] = 'Pro/deepseek-ai/DeepSeek-V3'
os.environ['CHAT_MODEL_HOST'] = 'https://api.siliconflow.cn/v1'

os.environ['EMBEDDING_API_KEY'] = 'sk-sxpqrpyhivyjaicexrdnehqknolpnokwndfxwykbxwfbtyku'
os.environ['EMBEDDING_MODEL'] = 'BAAI/bge-m3'
os.environ['EMBEDDING_MODEL_HOST'] = 'https://api.siliconflow.cn/v1'

# 加载环境变量
load_dotenv()

class Config:
    # OpenAI Chat配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('CHAT_MODEL', "gpt-4")  # 可根据需要调整
    CHAT_MODEL_HOST = os.getenv('CHAT_MODEL_HOST', "https://api.openai.com/v1")  # Chat模型host
    
    # 图配置
    GRAPH_TYPE = "networkx"  # 当前使用networkx
    
    # 预处理配置
    ENTITY_SIMILARITY_THRESHOLD = 0.9  # 实体去重相似度阈值
    RELATION_SIMILARITY_THRESHOLD = 0.8  # 关系去重相似度阈值
    
    # 向量配置
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', "text-embedding-3-small")  # OpenAI embedding模型
    EMBEDDING_MODEL_HOST = os.getenv('EMBEDDING_MODEL_HOST', "https://api.openai.com/v1")  # Embedding模型host
    EMBEDDING_API_KEY = os.getenv('EMBEDDING_API_KEY')  # Embedding API key