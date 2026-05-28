# -*- coding: utf-8 -*-
"""
FastAPI 主应用 - 量化回测系统 Web API
"""
import json
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from web.auth import (
    verify_password, get_password_hash, create_access_token, get_current_user, oauth2_scheme
)
from web.database import (
    get_db, get_user_by_username, create_user,
    save_backtest_result, get_user_backtests, get_backtest_by_id,
    save_strategy, get_user_strategies, get_strategy_by_id,
    update_strategy as update_strategy_db,
    delete_strategy as delete_strategy_db,
)
from database.models import User
from engine.data_loader import DataLoader
from engine.backtester import Backtester
from engine.strategy_base import (
    DualMAStrategy, RSIStrategy, MACDStrategy, BollingerStrategy, OMSStrategy
)

app = FastAPI(title="量化回测系统", version="2.0.0")

# 挂载 React 前端构建产物
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="frontend_assets")

# 挂载静态文件和模板
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# 策略工厂
STRATEGY_MAP = {
    "dual_ma": lambda p: DualMAStrategy(
        int(p.get("short_period", 5)),
        int(p.get("long_period", 20))
    ),
    "rsi": lambda p: RSIStrategy(
        int(p.get("period", 14)),
        int(p.get("oversold", 30)),
        int(p.get("overbought", 70))
    ),
    "macd": lambda p: MACDStrategy(),
    "bollinger": lambda p: BollingerStrategy(),
    "oms": lambda p: OMSStrategy(
        change_low=float(p.get("change_low", 3.0)),
        change_high=float(p.get("change_high", 5.0)),
        volume_ratio_min=float(p.get("volume_ratio_min", 1.0)),
        volume_stack_ratio=float(p.get("volume_stack_ratio", 1.2)),
    ),
}

STRATEGY_NAMES = {
    "dual_ma": "双均线策略",
    "rsi": "RSI 策略",
    "macd": "MACD 策略",
    "bollinger": "布林带策略",
    "oms": "尾盘动量隔夜策略",
}


# ===== 数据模型 =====

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RunBacktestRequest(BaseModel):
    strategy_type: str
    symbol: str = "TEST"
    days: int = 365
    initial_capital: float = 100000.0
    parameters: dict = {}
    data_source: str = "real"  # "real" 真实数据, "sample" 模拟数据


class SaveStrategyRequest(BaseModel):
    name: str
    description: str = ""
    strategy_type: str = "dual_ma"
    parameters: dict = {}
    workflow_config: str = "{}"  # 画布配置 JSON 字符串


class UpdateStrategyRequest(BaseModel):
    name: str = None
    description: str = None
    strategy_type: str = None
    parameters: dict = None
    workflow_config: str = None


# ===== API 路由 =====

# React SPA - 返回前端入口页面
frontend_index = os.path.join(frontend_dist, "index.html") if os.path.exists(frontend_dist) else None

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str, request: Request):
    # API 请求不处理（由其他路由匹配）
    if full_path.startswith("api/") or full_path.startswith("assets/"):
        raise HTTPException(status_code=404)
    # 返回 React index.html
    if frontend_index and os.path.exists(frontend_index):
        from starlette.responses import FileResponse
        return FileResponse(frontend_index)
    # 回退到 Jinja2 模板
    return templates.TemplateResponse("index.html", {"request": request})


# ===== 认证 API =====

@app.post("/api/auth/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    if len(req.username) < 2 or len(req.password) < 4:
        raise HTTPException(status_code=400, detail="用户名至少2个字符，密码至少4个字符")

    existing = get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    hashed = get_password_hash(req.password)
    user = create_user(db, req.username, hashed)

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.post("/api/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = get_user_by_username(db, req.username)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.get("/api/auth/me")
async def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    user = get_current_user(db, token)
    return {"id": user.id, "username": user.username, "created_at": str(user.created_at)}


# ===== 回测 API =====

@app.post("/api/backtest/run")
async def run_backtest(
    req: RunBacktestRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """运行回测"""
    user = get_current_user(db, token)

    if req.strategy_type not in STRATEGY_MAP:
        raise HTTPException(status_code=400, detail="未知策略类型: {}".format(req.strategy_type))

    try:
        # 获取数据
        loader = DataLoader()
        if req.data_source == "real":
            df = loader.fetch_real_data(req.symbol, req.days)
        else:
            df = loader.generate_sample_data(req.symbol, req.days)

        # 创建策略
        strategy = STRATEGY_MAP[req.strategy_type](req.parameters)

        # 运行回测
        backtester = Backtester(strategy, df, initial_capital=req.initial_capital)
        result = backtester.run()

        # 保存到数据库
        saved = save_backtest_result(
            db, user_id=user.id,
            strategy_type=req.strategy_type,
            symbol=req.symbol,
            start_date=str(df['date'].iloc[0])[:10],
            end_date=str(df['date'].iloc[-1])[:10],
            initial_capital=req.initial_capital,
            parameters=json.dumps(req.parameters),
            total_return=result['total_return'],
            annual_return=result['annual_return'],
            max_drawdown=result['max_drawdown'],
            sharpe_ratio=result['sharpe_ratio'],
            total_trades=result['total_trades'],
            win_rate=result['win_rate'],
            trades=json.dumps(result['trades']),
            equity_curve=json.dumps(result['equity_curve']),
        )

        return {
            "id": saved.id,
            "strategy_name": STRATEGY_NAMES.get(req.strategy_type, req.strategy_type),
            "strategy_type": req.strategy_type,
            "symbol": req.symbol,
            "total_return": result['total_return'],
            "annual_return": result['annual_return'],
            "max_drawdown": result['max_drawdown'],
            "sharpe_ratio": result['sharpe_ratio'],
            "total_trades": result['total_trades'],
            "win_rate": result['win_rate'],
            "trades": result['trades'],
            "equity_curve": result['equity_curve'],
            "created_at": str(saved.created_at),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="回测执行失败: {}".format(str(e)))


# ===== 行情数据 API =====

@app.get("/api/market/kline")
async def get_kline(symbol: str, days: int = 365):
    """获取 K 线数据"""
    try:
        loader = DataLoader()
        df = loader.fetch_real_data(symbol, days)
        klines = []
        for _, row in df.iterrows():
            klines.append({
                "date": str(row["date"])[:10],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
                "ma5": float(row["MA5"]) if pd.notna(row.get("MA5")) else None,
                "ma10": float(row["MA10"]) if pd.notna(row.get("MA10")) else None,
                "ma20": float(row["MA20"]) if pd.notna(row.get("MA20")) else None,
            })
        return {"symbol": symbol, "klines": klines, "total": len(klines)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/backtest/results")
async def list_results(
    limit: int = 20,
    offset: int = 0,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用户回测列表"""
    user = get_current_user(db, token)
    results = get_user_backtests(db, user.id, limit=limit, offset=offset)

    data = []
    for r in results:
        data.append({
            "id": r.id,
            "strategy_type": r.strategy_type,
            "strategy_name": STRATEGY_NAMES.get(r.strategy_type, r.strategy_type),
            "symbol": r.symbol,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "total_return": r.total_return,
            "annual_return": r.annual_return,
            "max_drawdown": r.max_drawdown,
            "sharpe_ratio": r.sharpe_ratio,
            "total_trades": r.total_trades,
            "win_rate": r.win_rate,
            "created_at": str(r.created_at),
        })

    return {"results": data, "total": len(data)}


@app.get("/api/backtest/results/{result_id}")
async def get_result(
    result_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取回测详情"""
    user = get_current_user(db, token)
    r = get_backtest_by_id(db, result_id)

    if r is None:
        raise HTTPException(status_code=404, detail="回测结果不存在")
    if r.user_id != user.id and user.username != "admin":
        raise HTTPException(status_code=403, detail="无权访问此回测结果")

    return {
        "id": r.id,
        "strategy_type": r.strategy_type,
        "strategy_name": STRATEGY_NAMES.get(r.strategy_type, r.strategy_type),
        "symbol": r.symbol,
        "start_date": r.start_date,
        "end_date": r.end_date,
        "initial_capital": r.initial_capital,
        "parameters": json.loads(r.parameters) if r.parameters else {},
        "total_return": r.total_return,
        "annual_return": r.annual_return,
        "max_drawdown": r.max_drawdown,
        "sharpe_ratio": r.sharpe_ratio,
        "total_trades": r.total_trades,
        "win_rate": r.win_rate,
        "trades": json.loads(r.trades) if r.trades else [],
        "equity_curve": json.loads(r.equity_curve) if r.equity_curve else [],
        "created_at": str(r.created_at),
    }


@app.delete("/api/backtest/results/{result_id}")
async def delete_result(
    result_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除回测结果"""
    user = get_current_user(db, token)
    r = get_backtest_by_id(db, result_id)
    if r is None:
        raise HTTPException(status_code=404, detail="回测结果不存在")
    if r.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权删除此回测结果")
    db.delete(r)
    db.commit()
    return {"message": "删除成功"}


# ===== 策略管理 API =====

@app.post("/api/strategies")
async def create_strategy(
    req: SaveStrategyRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """创建策略"""
    user = get_current_user(db, token)
    s = save_strategy(
        db, user_id=user.id,
        name=req.name,
        description=req.description,
        strategy_type=req.strategy_type,
        parameters=json.dumps(req.parameters),
        workflow_config=req.workflow_config,
    )
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "strategy_type": s.strategy_type,
        "parameters": req.parameters,
        "workflow_config": json.loads(s.workflow_config) if isinstance(s.workflow_config, str) else s.workflow_config,
        "created_at": str(s.created_at),
        "updated_at": str(s.updated_at) if s.updated_at else None,
    }


@app.get("/api/strategies")
async def list_strategies(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用户策略列表"""
    user = get_current_user(db, token)
    strategies = get_user_strategies(db, user.id)
    data = []
    for s in strategies:
        data.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "strategy_type": s.strategy_type,
            "parameters": json.loads(s.parameters) if s.parameters else {},
            "created_at": str(s.created_at),
            "updated_at": str(s.updated_at) if s.updated_at else None,
        })
    return {"strategies": data}


@app.get("/api/strategies/{strategy_id}")
async def get_strategy(
    strategy_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取策略详情"""
    user = get_current_user(db, token)
    s = get_strategy_by_id(db, strategy_id)
    if s is None:
        raise HTTPException(status_code=404, detail="策略不存在")
    if s.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问此策略")
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "strategy_type": s.strategy_type,
        "parameters": json.loads(s.parameters) if s.parameters else {},
        "workflow_config": json.loads(s.workflow_config) if isinstance(s.workflow_config, str) and s.workflow_config != "{}" else {},
        "created_at": str(s.created_at),
        "updated_at": str(s.updated_at) if s.updated_at else None,
    }


@app.put("/api/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    req: UpdateStrategyRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新策略"""
    user = get_current_user(db, token)
    update_data = {}
    if req.name is not None:
        update_data["name"] = req.name
    if req.description is not None:
        update_data["description"] = req.description
    if req.strategy_type is not None:
        update_data["strategy_type"] = req.strategy_type
    if req.parameters is not None:
        update_data["parameters"] = json.dumps(req.parameters)
    if req.workflow_config is not None:
        update_data["workflow_config"] = req.workflow_config

    result = update_strategy_db(db, strategy_id, user.id, **update_data)
    if result is None:
        raise HTTPException(status_code=404, detail="策略不存在或无权限")
    return {
        "id": result.id,
        "name": result.name,
        "description": result.description,
        "strategy_type": result.strategy_type,
        "parameters": json.loads(result.parameters) if result.parameters else {},
        "workflow_config": json.loads(result.workflow_config) if isinstance(result.workflow_config, str) and result.workflow_config != "{}" else {},
        "updated_at": str(result.updated_at) if result.updated_at else None,
    }


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除策略"""
    user = get_current_user(db, token)
    success = delete_strategy_db(db, strategy_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="策略不存在或无权限")
    return {"message": "删除成功"}


# ===== 数据看板 API =====

@app.get("/api/dashboard/summary")
async def dashboard_summary(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取看板统计数据"""
    user = get_current_user(db, token)
    results = get_user_backtests(db, user.id, limit=100)

    total_backtests = len(results)
    total_strategies = len(get_user_strategies(db, user.id))

    # 统计收益
    returns = [r.total_return for r in results if r.total_return is not None]
    avg_return = sum(returns) / len(returns) if returns else 0
    best_return = max(returns) if returns else 0
    worst_return = min(returns) if returns else 0
    positive_count = sum(1 for r in returns if r > 0)
    win_rate = positive_count / len(returns) * 100 if returns else 0

    # 最近5条回测
    recent = []
    for r in results[:5]:
        recent.append({
            "id": r.id,
            "symbol": r.symbol,
            "strategy_name": STRATEGY_NAMES.get(r.strategy_type, r.strategy_type),
            "total_return": r.total_return,
            "total_trades": r.total_trades,
            "created_at": str(r.created_at)[:10],
        })

    # 按策略类型分组收益
    type_returns = {}
    for r in results:
        name = STRATEGY_NAMES.get(r.strategy_type, r.strategy_type)
        if name not in type_returns:
            type_returns[name] = []
        if r.total_return is not None:
            type_returns[name].append(r.total_return)

    strategy_perf = [
        {"name": name, "avg_return": round(sum(v)/len(v)*100, 2), "count": len(v)}
        for name, v in type_returns.items()
    ]

    # 按股票统计
    symbol_returns = {}
    for r in results:
        sym = r.symbol or "未知"
        if sym not in symbol_returns:
            symbol_returns[sym] = []
        if r.total_return is not None:
            symbol_returns[sym].append(r.total_return)

    symbol_perf = [
        {"symbol": sym, "avg_return": round(sum(v)/len(v)*100, 2), "count": len(v)}
        for sym, v in sorted(symbol_returns.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:10]
    ]

    return {
        "total_backtests": total_backtests,
        "total_strategies": total_strategies,
        "avg_return": round(avg_return * 100, 2),
        "best_return": round(best_return * 100, 2),
        "worst_return": round(worst_return * 100, 2),
        "win_rate": round(win_rate, 1),
        "recent": recent,
        "strategy_perf": strategy_perf,
        "symbol_perf": symbol_perf,
    }


# ===== 启动 =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
