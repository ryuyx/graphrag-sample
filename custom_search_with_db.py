import asyncio
import pandas as pd
import os
from graphrag.api.query import global_search, local_search
from graphrag.config.load_config import load_config
from pathlib import Path
from dotenv import load_dotenv

# 假设这是你从数据库加载数据的函数
def load_data_from_my_db():
    """
    模拟从数据库读取数据并转换为 GraphRAG 需要的 DataFrame 格式。
    这里为了演示，我们直接读取 Parquet 文件，但在实际场景中，
    你会在这里执行 SQL 查询: SELECT * FROM entities ...
    """
    print("正在从数据库加载数据 (模拟)...")
    
    # 必须加载的表
    # 注意：列名必须与 GraphRAG 生成的 Parquet 文件一致
    return {
        "nodes": pd.read_parquet("output/entities.parquet"),
        "entities": pd.read_parquet("output/entities.parquet"),
        "community_reports": pd.read_parquet("output/community_reports.parquet"),
        "text_units": pd.read_parquet("output/text_units.parquet"),
        "relationships": pd.read_parquet("output/relationships.parquet"),
        # "covariates": pd.read_parquet("output/covariates.parquet") # 如果启用了 claim extraction
    }

async def run_custom_search():
    load_dotenv()
    
    # 1. 加载配置 (为了获取 LLM 设置)
    config = load_config(Path("."), "settings.yaml")
    
    # 2. 从你的数据库加载数据到内存 DataFrame
    data = load_data_from_my_db()
    
    # 3. 构建上下文数据
    # GraphRAG 的搜索函数需要特定的 DataFrame 输入
    # 你需要确保从数据库读出的数据包含必要的列 (如 id, title, description, weight, rank 等)
    
    print("\n--- 执行全局搜索 (Global Search) ---")
    # 全局搜索主要依赖: community_reports, entities
    result = await global_search(
        config=config,
        nodes=data["nodes"],
        entities=data["entities"],
        community_reports=data["community_reports"],
        query="这个数据集里的主要人物有哪些？",
        community_level=2,
        response_type="Multiple Paragraphs"
    )
    print(f"回答:\n{result.response}")

    print("\n--- 执行局部搜索 (Local Search) ---")
    # 局部搜索主要依赖: text_units, relationships, entities
    result = await local_search(
        config=config,
        nodes=data["nodes"],
        entities=data["entities"],
        community_reports=data["community_reports"],
        text_units=data["text_units"],
        relationships=data["relationships"],
        covariates=None,
        query="谁是 Scrooge?",
        response_type="Multiple Paragraphs"
    )
    print(f"回答:\n{result.response}")

if __name__ == "__main__":
    asyncio.run(run_custom_search())
