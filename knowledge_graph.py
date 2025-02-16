import networkx as nx
from typing import List, Dict, Tuple
import threading

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.should_stop = False
        self.progress = 0
        self.lock = threading.Lock()

    def add_entities(self, entities: List[Dict], progress_callback=None):
        with self.lock:
            if self.should_stop:
                return not self.should_stop
        total = len(entities)
        
        for i, entity in enumerate(entities):
            if self.should_stop:
                break
                
            self.graph.add_node(entity['entity'], type=entity['type'])
            
            if progress_callback:
                self.progress = (i + 1) / total * 100
                progress_callback(self.progress)
        
        return not self.should_stop

    def add_relations(self, relations: List[Tuple], progress_callback=None):
        with self.lock:
            if self.should_stop:
                return not self.should_stop
        total = len(relations)
        
        for i, relation in enumerate(relations):
            if self.should_stop:
                break
                
            self.graph.add_edge(relation[0], relation[2], relation=relation[1])
            
            if progress_callback:
                self.progress = (i + 1) / total * 100
                progress_callback(self.progress)
        
        return not self.should_stop

    def stop_analysis(self):
        with self.lock:
            self.should_stop = True

    def get_progress(self):
        with self.lock:
            return self.progress

    def to_dict(self):
        return nx.node_link_data(self.graph)