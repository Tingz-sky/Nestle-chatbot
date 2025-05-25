# 雀巢AI聊天机器人

一个基于Azure OpenAI和Neo4j的智能聊天机器人，可以回答关于雀巢产品和信息的问题。

## 技术架构

该项目使用以下技术：

- **Web爬虫**：使用Selenium爬取雀巢网站内容
- **Neo4j图数据库**：存储结构化的产品和内容信息
- **Azure Cognitive Search**：提供高效的向量搜索
- **Azure OpenAI**：为聊天机器人提供自然语言理解和生成能力
- **RAG (Retrieval-Augmented Generation)**：结合检索和生成，提供准确的回答

## 项目设置

### 前提条件

1. Python 3.8+
2. Neo4j数据库
3. Azure OpenAI服务
4. Azure Cognitive Search服务

### 安装步骤

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 设置环境变量：
   ```bash
   source setup_env.sh
   ```
   请确保先在`setup_env.sh`中填入您的API密钥和端点信息

4. 启动应用程序：
   ```bash
   cd backend
   python main.py
   ```

### 数据初始化

首次运行时，需要爬取网站内容并构建图数据库：

```bash
curl -X POST http://localhost:8000/api/refresh-content
```

## 使用方法

启动应用后，可以通过以下API与聊天机器人交互：

- `POST /api/chat`：发送查询并获取回复
- `POST /api/refresh-content`：刷新内容数据
- `GET /api/status`：检查服务状态

## RAG工作流程

1. 用户发送查询
2. 系统首先在Neo4j图数据库中搜索相关信息
3. 如果找不到，则使用Azure Cognitive Search进行向量搜索
4. 将检索到的内容发送给Azure OpenAI进行上下文理解和回答生成
5. 返回格式化的回答，并提供信息来源引用

## 项目结构

```
├── backend/
│   ├── services/
│   │   ├── web_scraper.py     # 网站爬虫
│   │   ├── graph_service.py   # Neo4j图数据库服务
│   │   ├── search_service.py  # Azure搜索服务
│   │   └── openai_service.py  # Azure OpenAI服务
│   ├── main.py                # 主应用程序
│   └── data/                  # 爬取的数据存储
├── frontend/                  # 前端代码(如有)
├── setup_env.sh               # 环境变量设置
└── README.md                  # 项目说明
```

## License

This project is licensed under the MIT License.

## Acknowledgements

- Nestlé for providing the content and inspiration for this project.
- Azure for the cloud infrastructure and AI services.

## Security Update

This project now uses Azure Key Vault to securely store sensitive information instead of hardcoding them in environment files. The following secrets are stored in Key Vault:

- AZURE-SEARCH-KEY
- NEO4J-PASSWORD
- AZURE-OPENAI-KEY

## Setup

### Azure Key Vault Setup

1. Create an Azure Key Vault resource if you don't have one already:

```bash
az keyvault create --name nestlechatbot-kv --resource-group YOUR_RESOURCE_GROUP --location YOUR_LOCATION
```

2. Add your secrets to the Key Vault:

```bash
az keyvault secret set --vault-name nestlechatbot-kv --name "AZURE-SEARCH-KEY" --value "your-search-key"
az keyvault secret set --vault-name nestlechatbot-kv --name "NEO4J-PASSWORD" --value "your-neo4j-password"
az keyvault secret set --vault-name nestlechatbot-kv --name "AZURE-OPENAI-KEY" --value "your-openai-key"
```

3. Ensure your development environment has proper access to the Key Vault:

```bash
az keyvault set-policy --name nestlechatbot-kv --upn your-email@example.com --secret-permissions get list
```

For deployed applications, use managed identities for secure access.

### Environment Setup

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Configure your environment variables in `setup_env.sh`:

```bash
source setup_env.sh
```

## Running the Application

### Start the Backend Server

```bash
python run.py --backend
```

### Start the Frontend Development Server

```bash
python run.py --frontend
```

### Update Data

To scrape new data and update the knowledge base:

```bash
python run.py --scrape --update-index --build-graph
```

## Architecture

This chatbot uses a combination of:

- Azure OpenAI for natural language processing
- Azure Cognitive Search for document retrieval
- Neo4j graph database for knowledge representation
- FastAPI backend
- React frontend

## Development

### Project Structure

```
.
├── backend/            # FastAPI backend
├── frontend/           # React frontend
├── data/               # Scraped and processed data
├── setup_env.sh        # Environment configuration
├── run.py              # Main entry point
└── requirements.txt    # Python dependencies
``` 