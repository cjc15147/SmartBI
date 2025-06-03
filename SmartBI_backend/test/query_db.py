import sqlite3
import os
import pandas as pd

def query_database():
    # 获取数据库文件路径
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.db")
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    
    try:
        # 查询表结构
        print("\n=== 表结构 ===")
        table_info = pd.read_sql_query("PRAGMA table_info(data_centers);", conn)
        print(table_info)
        
        # 查询数据总数
        print("\n=== 数据总数 ===")
        count = pd.read_sql_query("SELECT COUNT(*) as count FROM data_centers;", conn)
        print(f"总记录数: {count['count'].iloc[0]}")
        
        # 查询前5条数据
        print("\n=== 前5条数据 ===")
        data = pd.read_sql_query("""
            SELECT 
                id,
                report_name as 报账点名称,
                contract_code as 合同编码,
                annual_rent as 合同年租金,
                area as 机房面积,
                longitude as 经度,
                latitude as 纬度
            FROM data_centers 
            LIMIT 5;
        """, conn)
        print(data)
        
        # 查询一些统计信息
        print("\n=== 统计信息 ===")
        stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as 总记录数,
                AVG(annual_rent) as 平均年租金,
                AVG(area) as 平均面积,
                MIN(annual_rent) as 最小年租金,
                MAX(annual_rent) as 最大年租金
            FROM data_centers;
        """, conn)
        print(stats)
        
    finally:
        conn.close()

if __name__ == "__main__":
    query_database() 