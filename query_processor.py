import openai
import numpy as np
from typing import List, Dict
from config import Config
from knowledge_graph import KnowledgeGraph

class QueryProcessor:
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.openai_embedding_client = openai.OpenAI(
            api_key=Config.EMBEDDING_API_KEY,
            base_url=Config.EMBEDDING_MODEL_HOST
        )
        
    def get_query_embedding(self, query: str) -> np.ndarray:
        """
        获取查询的embedding
        """
        response = self.openai_embedding_client.embeddings.create(
            input=query,
            model=Config.EMBEDDING_MODEL
        )
        return np.array(response.data[0].embedding)
        
    def search_graph(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        在图和向量空间中进行检索
        """
        # TODO: 实现基于embedding的图检索
        # 目前先返回简单的图搜索结果
        entities = list(self.graph.graph.nodes)
        return [{"entity": entity} for entity in entities[:top_k]]
        
    def process_query(self, query: str) -> Dict:
        """
        处理用户查询
        """
        # 获取查询embedding
        query_embedding = self.get_query_embedding(query)
        
        # 在图和向量空间中进行检索
        results = self.search_graph(query)
        
        return {
            "query": query,
            "embedding": query_embedding.tolist(),
            "results": results
        }