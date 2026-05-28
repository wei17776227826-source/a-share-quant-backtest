# -*- coding: utf-8 -*-
"""
数据库会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, BacktestResult, Strategy

import os
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'database', 'quant.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_username(db, username):
    """通过用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db, user_id):
    """通过 ID 获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db, username, hashed_password):
    """创建用户"""
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_backtest_result(db, user_id, **kwargs):
    """保存回测结果"""
    result = BacktestResult(user_id=user_id, **kwargs)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_user_backtests(db, user_id, limit=20, offset=0):
    """获取用户的所有回测结果"""
    return (db.query(BacktestResult)
            .filter(BacktestResult.user_id == user_id)
            .order_by(BacktestResult.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all())


def get_backtest_by_id(db, result_id):
    """通过 ID 获取回测结果"""
    return db.query(BacktestResult).filter(BacktestResult.id == result_id).first()


def save_strategy(db, user_id, **kwargs):
    """保存策略"""
    strategy = Strategy(user_id=user_id, **kwargs)
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


def get_user_strategies(db, user_id):
    """获取用户的所有策略"""
    return (db.query(Strategy)
            .filter(Strategy.user_id == user_id)
            .order_by(Strategy.created_at.desc())
            .all())


def get_strategy_by_id(db, strategy_id):
    """通过 ID 获取策略"""
    return db.query(Strategy).filter(Strategy.id == strategy_id).first()


def update_strategy(db, strategy_id, user_id, **kwargs):
    """更新策略"""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id, Strategy.user_id == user_id
    ).first()
    if not strategy:
        return None
    for key, value in kwargs.items():
        if hasattr(strategy, key):
            setattr(strategy, key, value)
    db.commit()
    db.refresh(strategy)
    return strategy


def delete_strategy(db, strategy_id, user_id):
    """删除策略"""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id, Strategy.user_id == user_id
    ).first()
    if not strategy:
        return False
    db.delete(strategy)
    db.commit()
    return True
