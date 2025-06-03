from apscheduler.schedulers.background import BackgroundScheduler
from database.connection import DatabaseConnection
from datetime import datetime

scheduler = BackgroundScheduler()

def process_user_data():
    """
    示例定时任务：处理用户数据
    可以在这里添加大表处理为小表的逻辑
    """
    db = DatabaseConnection.get_session()
    try:
        # 这里添加数据处理逻辑
        print(f"Processing user data at {datetime.now()}")
    finally:
        db.close()

# 添加定时任务
scheduler.add_job(process_user_data, 'interval', hours=24)

# 启动调度器
def start_scheduler():
    scheduler.start() 