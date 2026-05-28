# -*- coding: utf-8 -*-
"""
数据库模型 - 用户、回测结果、策略
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    backtests = relationship("BacktestResult", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


class BacktestResult(Base):
    """回测结果表"""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    strategy_type = Column(String)
    symbol = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    initial_capital = Column(Float)
    parameters = Column(Text)  # JSON

    total_return = Column(Float)
    annual_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    total_trades = Column(Integer)
    win_rate = Column(Float)
    trades = Column(Text)  # JSON
    equity_curve = Column(Text)  # JSON

    created_at = Column(DateTime, default=datetime.now)

    # 关联
    user = relationship("User", back_populates="backtests")

    def __repr__(self):
        return f"<BacktestResult {self.id}>"


class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    name = Column(String)
    description = Column(String)
    strategy_type = Column(String)
    parameters = Column(Text)  # JSON

    created_at = Column(DateTime, default=datetime.now)

    # 关联
    user = relationship("User", back_populates="strategies")

    def __repr__(self):
        return f"<Strategy {self.name}>"


if __name__ == "__main__":
    engine = create_engine("sqlite:///quant.db")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")
