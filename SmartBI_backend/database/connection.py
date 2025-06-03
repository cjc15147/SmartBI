from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import logging
from typing import Generator
import time
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None
    _engine = None
    _SessionLocal = None
    Base = declarative_base()
    _max_retries = 3
    _retry_delay = 1  # 秒

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._initialize_connection()
        return cls._instance

    @classmethod
    def _initialize_connection(cls):
        retries = 0
        while retries < cls._max_retries:
            try:
                # 配置数据库连接
                DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/smartbi"
                logger.info(f"Connecting to database: {DATABASE_URL}")
                
                cls._engine = create_engine(
                    DATABASE_URL,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_pre_ping=True,  # 添加连接检查
                    connect_args={
                        'connect_timeout': 10  # 连接超时时间
                    }
                )
                
                # 测试连接
                with cls._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                
                cls._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._engine)
                return
                
            except SQLAlchemyError as e:
                retries += 1
                logger.error(f"Failed to connect to database (attempt {retries}/{cls._max_retries}): {str(e)}")
                if retries < cls._max_retries:
                    time.sleep(cls._retry_delay)
                else:
                    raise Exception(f"Failed to connect to database after {cls._max_retries} attempts: {str(e)}")

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls._initialize_connection()
        return cls._engine

    @classmethod
    def get_session(cls):
        if cls._SessionLocal is None:
            cls._initialize_connection()
        try:
            db = cls._SessionLocal()
            # 测试连接
            db.execute(text("SELECT 1"))
            return db
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database session: {str(e)}")
            if db:
                db.close()
            raise

    @classmethod
    def get_base(cls):
        return cls.Base

def get_db() -> Generator:
    """
    获取数据库会话的依赖注入函数
    """
    db = None
    try:
        db = DatabaseConnection.get_session()
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        if db:
            db.close() 