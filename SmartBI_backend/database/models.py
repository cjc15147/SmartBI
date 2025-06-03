from sqlalchemy import Column, Integer, String, DateTime, BigInteger, SmallInteger, Float, JSON, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.sql import func
from .connection import DatabaseConnection

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='用户id')
    userAccount = Column(String(256), nullable=False, index=True, comment='账号')
    userPassword = Column(String(512), nullable=False, comment='密码')
    userName = Column(String(256), comment='用户昵称')
    userAvatar = Column(String(1024), comment='用户头像')
    userRole = Column(String(256), nullable=False, default='user', comment='用户角色：user/admin')
    createTime = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updateTime = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    isDelete = Column(SmallInteger, nullable=False, default=0, comment='是否删除')

class DataCenter(Base):
    """机房数据表"""
    __tablename__ = 'data_centers'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_name = Column(String(256), nullable=False, comment='报账点名称')
    contract_code = Column(String(256), nullable=False, comment='合同编码')
    contract_name = Column(String(256), nullable=False, comment='合同名称')
    contract_start = Column(DateTime, nullable=False, comment='合同期始')
    contract_end = Column(DateTime, nullable=False, comment='合同期终')
    annual_rent = Column(Float, nullable=False, comment='合同年租金')
    total_rent = Column(Float, nullable=False, comment='合同总金额')
    area = Column(Float, nullable=False, comment='机房面积')
    longitude = Column(Float, nullable=False, comment='经度')
    latitude = Column(Float, nullable=False, comment='纬度')
    create_time = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    update_time = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

class RentAnalysis(Base):
    """租金分析记录表"""
    __tablename__ = 'rent_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    center_lat = Column(Float, nullable=False, comment='中心点纬度')
    center_lng = Column(Float, nullable=False, comment='中心点经度')
    radius = Column(Integer, nullable=False, comment='分析半径(米)')
    result = Column(JSON, comment='分析结果')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

class Chart(Base):
    """图表数据表"""
    __tablename__ = 'chart'
    
    id = Column(BigInteger, primary_key=True, comment='主键')
    name = Column(String(128), nullable=True, comment='名称')
    goal = Column(Text, nullable=True, comment='分析目标')
    chart_data = Column(Text, nullable=True, comment='图表数据')
    chart_type = Column(String(128), nullable=True, comment='图表类型')
    gen_chart = Column(Text, nullable=True, comment='生成的图表数据')
    gen_result = Column(Text, nullable=True, comment='生成的分析结论')
    status = Column(String(128), nullable=True, comment='任务状态')
    exec_message = Column(Text, nullable=True, comment='执行信息')
    user_id = Column(BigInteger, nullable=False, comment='用户id')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_delete = Column(SmallInteger, nullable=False, default=0, comment='是否删除') 