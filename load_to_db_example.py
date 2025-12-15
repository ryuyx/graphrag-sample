import pandas as pd
import os
from pathlib import Path

# 设定 output 目录路径
OUTPUT_DIR = Path("output")

def load_parquet_files():
    """
    读取 GraphRAG 生成的 Parquet 文件并展示如何处理数据
    """
    
    # 常见的数据表文件
    files = [
        "entities.parquet",
        "relationships.parquet",
        "communities.parquet",
        "community_reports.parquet",
        "text_units.parquet"
    ]
    
    for file_name in files:
        file_path = OUTPUT_DIR / file_name
        if not file_path.exists():
            print(f"Warning: {file_name} not found.")
            continue
            
        print(f"\n--- Loading {file_name} ---")
        df = pd.read_parquet(file_path)
        
        # 这里可以添加代码将 df 数据写入你的数据库
        # 例如: df.to_sql('entities', con=engine, if_exists='replace')
        
        print(f"Columns: {df.columns.tolist()}")
        print(f"Row count: {len(df)}")
        print(df.head(2))

if __name__ == "__main__":
    load_parquet_files()
