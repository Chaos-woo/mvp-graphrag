# MVP GraphRAG

MVP GraphRAG 是一个基于知识图谱的问答系统，结合了Flask和Streamlit框架，提供灵活的前后端交互体验。

## 功能特性

- 知识图谱构建与可视化
- 自然语言问答接口
- 支持Flask和Streamlit两种Web框架

## 安装指南

1. 克隆本仓库：
   ```bash
   git clone https://github.com/yourusername/mvp-graphrag.git
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用说明

### 前后端版本
```bash
python main.py
```

### Streamlit版本
```bash
streamlit run streamlit_app.py
```

## 项目结构

```
.
├── .gitignore
├── config.py
├── flask_app.py
├── graph.html
├── knowledge_graph.py
├── main.py
├── preprocessor.py
├── query_processor.py
├── requirements.txt
├── streamlit_app.py
├── docs/          # 文档目录
└── lib/           # 第三方库目录
```