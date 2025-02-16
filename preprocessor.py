import threading
from typing import List, Dict, Tuple
import openai
import numpy as np
from config import Config

class Preprocessor:
    def __init__(self):
        self.openai_client = openai.OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.CHAT_MODEL_HOST
        )
        self.openai_embedding_client = openai.OpenAI(
            api_key=Config.EMBEDDING_API_KEY,
            base_url=Config.EMBEDDING_MODEL_HOST
        )
        self.should_stop = False
        self.lock = threading.Lock()
        self.progress = 0
        self.total_steps = 4  # 总处理步骤数

    def process(self, text: str, file_data: bytes = None, progress_callback=None) -> Tuple[List[Dict], List[Tuple]]:
        """
        完整的预处理流程，支持大文本和文件数据处理
        Args:
            text: 直接传入的文本内容
            file_data: 文件数据，如果提供则优先使用
            progress_callback: 进度回调函数
        """
        self.progress = 0
        if progress_callback:
            progress_callback(self.progress)
        
        def check_should_stop():
            with self.lock:
                return self.should_stop

        # 如果提供了文件数据，则解码为文本
        if file_data:
            text = file_data.decode('utf-8')

        if check_should_stop():
            return None
        
        # 将大文本分割成chunk
        chunks = self._split_text_into_chunks(text)
        self.progress = 1/self.total_steps
        if progress_callback:
            progress_callback(self.progress * 100)

        if check_should_stop():
            return None
        
        # 处理每个chunk
        all_entities = []
        all_relations = []
        chunk_count = len(chunks)
        for i, chunk in enumerate(chunks):
            # 提取实体
            entities = self.extract_entities(chunk)
            self.progress = (2 + i/chunk_count)/self.total_steps
            if progress_callback:
                progress_callback(self.progress * 100)
            if check_should_stop():
                return None

            # 去重实体
            entities = self.deduplicate_entities(entities)
            self.progress = (2 + i/chunk_count)/self.total_steps
            if progress_callback:
                progress_callback(self.progress * 100)
            if check_should_stop():
                return None
                        
            # 提取关系
            relations = self.extract_relations(chunk, entities)
            self.progress = (2 + i/chunk_count)/self.total_steps
            if progress_callback:
                progress_callback(self.progress * 100)
            if check_should_stop():
                return None
                          
            # 去重关系
            relations = self.deduplicate_relations(relations)
            self.progress = (2 + i/chunk_count)/self.total_steps
            if progress_callback:
                progress_callback(self.progress * 100)
            if check_should_stop():
                return None
                         
            all_entities.extend(entities)
            all_relations.extend(relations)
        
        if check_should_stop():
            return None   

        # 最终去重
        all_entities = self.deduplicate_entities(all_entities)
        self.progress = 3/self.total_steps
        if progress_callback:
            progress_callback(self.progress * 100)
        if check_should_stop():
            return None  
                
        all_relations = self.deduplicate_relations(all_relations)
        self.progress = 4/self.total_steps
        if progress_callback:
            progress_callback(self.progress * 100)
        if check_should_stop():
            return None       
         
        return all_entities, all_relations

    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """
        将大文本分割成适当大小的chunk，支持多语言环境
        """
        # 多语言句子分隔符
        sentence_delimiters = [
            '.', '。', '．',  # 句号
            '?', '？',       # 问号
            '!', '！',       # 感叹号
            ';', '；',       # 分号
            '\n', '\r\n',    # 换行符
            '…', '...',      # 省略号
            '—', '―',        # 破折号
            '·', '•',        # 项目符号
            '、', '，',      # 逗号
            '：', ':'        # 冒号
        ]
        
        chunks = []
        while len(text) > max_chunk_size:
            # 找到最后一个句子分隔符的位置
            split_pos = -1
            for delimiter in sentence_delimiters:
                pos = text.rfind(delimiter, 0, max_chunk_size)
                if pos > split_pos:
                    split_pos = pos
            
            # 如果没有找到合适的分隔符，则在最大长度处分割
            if split_pos == -1:
                split_pos = max_chunk_size
                # 确保不会在多字节字符中间分割
                while split_pos > 0 and not text[split_pos].isascii():
                    split_pos -= 1
            
            # 添加chunk并移除已处理部分
            chunks.append(text[:split_pos + 1].strip())
            text = text[split_pos + 1:].strip()
        
        # 添加剩余文本
        if text:
            chunks.append(text.strip())
        
        return chunks

    def extract_entities(self, text: str) -> List[Dict]:
        """
        使用OpenAI提取实体
        """
        prompt = f"""
        请从以下文本中提取实体，不返回任何提示文本和解释文本：
        {text}
        返回格式：[{{"entity": "实体名称", "type": "实体类型"}}]
        """
        response = self.openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return eval(response.choices[0].message.content)
    
    def extract_relations(self, text: str, entities: List[Dict]) -> List[Tuple]:
        """
        使用OpenAI提取实体关系
        """
        prompt = f"""
        给定文本：{text}
        和实体列表：{entities}
        请提取实体之间的关系，不返回任何提示文本和解释文本
        返回格式：[("实体1","关系","实体2")]
        """
        response = self.openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return eval(response.choices[0].message.content)
    
    def deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        使用余弦相似度去重合并实体
        """
        if not entities:
            return []
            
        # 获取所有实体的embedding
        embeddings = {}
        for entity in entities:
            response = self.openai_client.embeddings.create(
                input=entity['entity'],
                model=Config.EMBEDDING_MODEL
            )
            embeddings[entity['entity']] = np.array(response.data[0].embedding)
            
        # 计算余弦相似度并合并相似实体
        unique_entities = []
        processed = set()
        
        for i, entity in enumerate(entities):
            if entity['entity'] in processed:
                continue
                
            # 找到相似实体
            similar_entities = [entity]
            for j in range(i + 1, len(entities)):
                if entities[j]['entity'] in processed:
                    continue
                    
                # 计算余弦相似度
                vec1 = embeddings[entity['entity']]
                vec2 = embeddings[entities[j]['entity']]
                similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                
                if similarity > Config.ENTITY_SIMILARITY_THRESHOLD:
                    similar_entities.append(entities[j])
                    processed.add(entities[j]['entity'])
                    
            # 合并相似实体
            merged_entity = {
                'entity': entity['entity'],
                'type': entity['type'],
                'aliases': [e['entity'] for e in similar_entities[1:]]
            }
            unique_entities.append(merged_entity)
            processed.add(entity['entity'])
            
        return unique_entities

    def deduplicate_relations(self, relations: List[Tuple]) -> List[Tuple]:
        """
        使用余弦相似度去重合并关系
        """
        if not relations:
            return []

        # 获取所有关系的embedding
        embeddings = {}
        for relation in relations:
            relation_str = f"{relation[0]} {relation[1]} {relation[2]}"
            response = self.openai_embedding_client.embeddings.create(
                input=relation_str,
                model=Config.EMBEDDING_MODEL
            )
            embeddings[relation_str] = np.array(response.data[0].embedding)

        # 计算余弦相似度并合并相似关系
        unique_relations = []
        processed = set()

        for i, relation in enumerate(relations):
            relation_str = f"{relation[0]} {relation[1]} {relation[2]}"
            if relation_str in processed:
                continue

            # 找到相似关系
            similar_relations = [relation]
            for j in range(i + 1, len(relations)):
                other_relation_str = f"{relations[j][0]} {relations[j][1]} {relations[j][2]}"
                if other_relation_str in processed:
                    continue

                # 计算余弦相似度
                vec1 = embeddings[relation_str]
                vec2 = embeddings[other_relation_str]
                similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

                if similarity > Config.RELATION_SIMILARITY_THRESHOLD:
                    similar_relations.append(relations[j])
                    processed.add(other_relation_str)

            # 选择第一个关系作为代表
            unique_relations.append(similar_relations[0])
            processed.add(relation_str)

        return unique_relations
    
    def stop_analysis(self):
        with self.lock:
            self.should_stop = True