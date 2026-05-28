# -*- coding: utf-8 -*-
"""
量化回测系统 - Dash Web 应用
使用 Plotly/Dash 框架重构，无 HTML 模板
"""
import os
import sys
import json
import requests

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash
from dash import dcc, html, Input, Output, State, callback, ctx, no_update, ClientsideFunction
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

API_BASE = "http://localhost:8000"
STRATEGY_NAMES = {
    "dual_ma": "双均线策略",
    "rsi": "RSI 策略",
    "macd": "MACD 策略",
    "bollinger": "布林带策略",
}

# ===== 暗色主题样式 =====
DARK = {
    "bg": "#1a1a2e",
    "card": "rgba(255,255,255,0.03)",
    "border": "rgba(255,255,255,0.08)",
    "text": "#e0e0e0",
    "text_dim": "rgba(255,255,255,0.5)",
    "accent": "#6366f1",
    "success": "#22c55e",
    "danger": "#ef4444",
    "card_hover": "rgba(255,255,255,0.06)",
}

CARD_STYLE = {
    "background": DARK["card"],
    "border": f"1px solid {DARK['border']}",
    "borderRadius": "16px",
    "padding": "24px",
    "marginBottom": "20px",
}

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
PLOTLY_THEME = {
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": DARK["text_dim"], "size": 12},
    "xaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zerolinecolor": "rgba(255,255,255,0.1)"},
    "yaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zerolinecolor": "rgba(255,255,255,0.1)"},
}

# ===== 工具函数 =====

def api_get(path, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(f"{API_BASE}{path}", headers=headers, timeout=10)
        return r.json() if r.ok else {"error": r.status_code, "detail": r.text}
    except Exception as e:
        return {"error": -1, "detail": str(e)}


def api_post(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, headers=headers, timeout=30)
        return r.json() if r.ok else {"error": r.status_code, "detail": r.text}
    except Exception as e:
        return {"error": -1, "detail": str(e)}


def api_delete(path, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.delete(f"{API_BASE}{path}", headers=headers, timeout=10)
        return r.json() if r.ok else {"error": r.status_code, "detail": r.text}
    except Exception as e:
        return {"error": -1, "detail": str(e)}


def fmt_pct(v):
    return f"{v * 100:.2f}%" if v is not None else "-"


def fmt_num(v):
    return f"{v:.2f}" if v is not None else "-"


def strategy_badge(t):
    colors = {"dual_ma": "#818cf8", "rsi": "#4ade80", "macd": "#facc15", "bollinger": "#f87171"}
    c = colors.get(t, "#6366f1")
    return html.Span(STRATEGY_NAMES.get(t, t), style={
        "background": f"{c}22", "color": c, "padding": "2px 10px",
        "borderRadius": "10px", "fontSize": "12px"
    })


# ===== 初始化 Dash =====
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="量化回测系统",
)

server = app.server

# ===== 导航栏 =====
NAV_ITEMS = [
    ("📈 仪表盘", "dashboard"),
    ("🔄 回测分析", "backtest"),
    ("📋 历史结果", "results"),
    ("⚙️ 策略管理", "strategies"),
]

def navbar():
    return dbc.Navbar(
        dbc.Container([
            html.A("📊 量化回测", className="navbar-brand",
                   style={"fontWeight": "700", "fontSize": "18px", "color": "#fff"}),
            dbc.Nav(
                [dbc.NavItem(dbc.NavLink(label, id=f"nav-{key}", href="#",
                                          className="nav-link-custom"))
                 for label, key in NAV_ITEMS],
                className="ms-auto", navbar=True,
            ),
            html.Span(id="user-display", style={
                "color": DARK["text_dim"], "fontSize": "14px", "marginLeft": "20px"
            }),
            dbc.Button("退出", id="btn-logout", color="link", size="sm",
                       style={"color": DARK["text_dim"], "marginLeft": "10px"}),
        ]),
        dark=True, color="dark",
        style={"borderBottom": f"1px solid {DARK['border']}", "marginBottom": "20px"},
    )


# ===== 页面布局 =====

# -- 登录页 --
def login_page():
    return html.Div([
        html.Div([
            html.H2("量化回测系统", style={"textAlign": "center", "color": "#fff",
                                          "fontSize": "28px", "fontWeight": "700"}),
            html.P("专业的量化交易策略分析平台", style={
                "textAlign": "center", "color": DARK["text_dim"], "fontSize": "14px",
                "marginBottom": "30px"
            }),
            dbc.Tabs([
                dbc.Tab(label="登录", tab_id="login"),
                dbc.Tab(label="注册", tab_id="register"),
            ], id="auth-tabs", active_tab="login",
               style={"marginBottom": "20px"}),

            html.Div(id="login-form", children=[
                dbc.Label("用户名"), dbc.Input(id="login-user", placeholder="请输入用户名",
                                               className="mb-2", type="text"),
                dbc.Label("密码"), dbc.Input(id="login-pass", placeholder="请输入密码",
                                             className="mb-3", type="password"),
                dbc.Button("登录", id="btn-login", color="primary", className="w-100"),
            ]),
            html.Div(id="register-form", children=[
                dbc.Label("用户名"), dbc.Input(id="reg-user", placeholder="请输入用户名",
                                               className="mb-2", type="text"),
                dbc.Label("密码"), dbc.Input(id="reg-pass", placeholder="请输入密码",
                                             className="mb-3", type="password"),
                dbc.Button("注册", id="btn-register", color="success", className="w-100"),
            ]),
            html.Div(id="auth-msg", style={
                "color": "#ef4444", "fontSize": "13px", "textAlign": "center",
                "marginTop": "12px"
            }),
        ], style={
            "maxWidth": "420px", "margin": "100px auto",
            "background": "rgba(255,255,255,0.05)", "backdropFilter": "blur(20px)",
            "border": f"1px solid {DARK['border']}", "borderRadius": "20px",
            "padding": "40px",
        }),
    ], style={
        "minHeight": "100vh",
        "background": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
    })


# -- 仪表盘 --
def dashboard_page():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("总回测次数", className="card-subtitle",
                            style={"color": DARK["text_dim"]}),
                    html.H3(id="stat-total", children="-",
                            style={"color": "#fff", "fontWeight": "700"}),
                ])
            ], style=CARD_STYLE), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("平均收益率", className="card-subtitle",
                            style={"color": DARK["text_dim"]}),
                    html.H3(id="stat-avg-return", children="-",
                            style={"color": "#fff", "fontWeight": "700"}),
                    html.Small("所有策略", style={"color": DARK["text_dim"]}),
                ])
            ], style=CARD_STYLE), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("最好策略", className="card-subtitle",
                            style={"color": DARK["text_dim"]}),
                    html.H3(id="stat-best", children="-",
                            style={"color": "#fff", "fontWeight": "700"}),
                    html.Small(id="stat-best-ret", style={"color": DARK["text_dim"]}),
                ])
            ], style=CARD_STYLE), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("平均夏普比率", className="card-subtitle",
                            style={"color": DARK["text_dim"]}),
                    html.H3(id="stat-avg-sharpe", children="-",
                            style={"color": "#fff", "fontWeight": "700"}),
                ])
            ], style=CARD_STYLE), width=3),
        ], className="mb-4"),

        dbc.Card([
            dbc.CardBody([
                html.H5("策略表现对比", style={"color": "#fff", "marginBottom": "16px"}),
                dcc.Graph(id="chart-compare", config=PLOTLY_CONFIG),
            ])
        ], style=CARD_STYLE),

        dbc.Card([
            dbc.CardBody([
                html.H5("最近回测结果", style={"color": "#fff", "marginBottom": "16px"}),
                html.Div(id="recent-table"),
            ])
        ], style=CARD_STYLE),
    ])


# -- 回测分析 --
def backtest_page():
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("回测参数", style={"color": "#fff", "marginBottom": "16px"}),
                    dbc.Label("策略类型"),
                    dcc.Dropdown(id="bt-strategy",
                                 options=[
                                     {"label": "双均线策略", "value": "dual_ma"},
                                     {"label": "RSI 策略", "value": "rsi"},
                                     {"label": "MACD 策略", "value": "macd"},
                                     {"label": "布林带策略", "value": "bollinger"},
                                 ], value="dual_ma",
                                 style={"color": "#000", "marginBottom": "12px"}),
                    dbc.Label("标的代码"),
                    dbc.Input(id="bt-symbol", value="TEST", className="mb-2"),
                    dbc.Label("回测天数"),
                    dbc.Input(id="bt-days", type="number", value=365, className="mb-2"),
                    dbc.Label("初始资金"),
                    dbc.Input(id="bt-capital", type="number", value=100000, className="mb-3"),
                    html.Div(id="bt-params", children=[
                        dbc.Label("短期均线周期"),
                        dbc.Input(id="bt-short", type="number", value=5, className="mb-2"),
                        dbc.Label("长期均线周期"),
                        dbc.Input(id="bt-long", type="number", value=20, className="mb-3"),
                    ]),
                    dbc.Button("🚀 运行回测", id="btn-run-bt", color="primary", className="w-100"),
                    html.Div(id="bt-loading", style={
                        "textAlign": "center", "padding": "20px", "display": "none"
                    }, children=[dbc.Spinner(size="sm"), " 回测进行中..."]),
                    html.Div(id="bt-error", style={
                        "color": "#ef4444", "fontSize": "13px", "marginTop": "8px", "display": "none"
                    }),
                ])
            ], style=CARD_STYLE),
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("策略说明", style={"color": "#fff", "marginBottom": "12px"}),
                    html.Div(id="bt-desc", children=[
                        html.P([html.B("双均线策略：", style={"color": "#818cf8"}),
                                "MA5 上穿 MA20 买入，下穿卖出。趋势跟踪策略。"])
                    ], style={"color": DARK["text_dim"], "fontSize": "14px", "lineHeight": "1.8"}),
                ])
            ], style=CARD_STYLE),

            html.Div(id="bt-result", style={"display": "none"}, children=[
                dbc.Card([
                    dbc.CardBody([
                        html.H5("回测结果", style={"color": "#fff", "marginBottom": "16px"}),
                        dbc.Row(id="bt-metrics", className="mb-3"),
                        dcc.Graph(id="bt-equity-chart", config=PLOTLY_CONFIG),
                    ])
                ], style=CARD_STYLE),
                dbc.Card([
                    dbc.CardBody([
                        html.H5("交易记录", style={"color": "#fff", "marginBottom": "12px"}),
                        html.Div(id="bt-trades", style={"maxHeight": "300px", "overflowY": "auto"}),
                    ])
                ], style=CARD_STYLE),
            ]),
        ], width=8),
    ])


# -- 历史结果 --
def results_page():
    return html.Div([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H5("历史回测结果", style={"color": "#fff", "display": "inline"}),
                    dbc.Button("+ 新建回测", id="btn-new-bt", color="primary", size="sm",
                               style={"float": "right"}),
                ], style={"marginBottom": "16px"}),
                html.Div(id="results-table"),
            ])
        ], style=CARD_STYLE),

        html.Div(id="result-detail", style={"display": "none"}, children=[
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H5(id="detail-title", style={"color": "#fff", "display": "inline"}),
                        dbc.Button("关闭", id="btn-close-detail", color="secondary", size="sm",
                                   style={"float": "right"}),
                    ], style={"marginBottom": "16px"}),
                    dbc.Row(id="detail-metrics", className="mb-3"),
                    dcc.Graph(id="detail-chart", config=PLOTLY_CONFIG),
                    html.Div(id="detail-trades", style={"maxHeight": "300px", "overflowY": "auto"}),
                ])
            ], style=CARD_STYLE),
        ]),
    ])


# -- 策略管理 --
def strategies_page():
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📦 内置策略", style={"color": "#fff", "marginBottom": "16px"}),
                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.Div("📈", style={"fontSize": "28px", "textAlign": "center"}),
                                html.H6("双均线策略", style={"textAlign": "center", "marginTop": "8px"}),
                                html.P("MA5/MA20 交叉", style={
                                    "textAlign": "center", "color": DARK["text_dim"], "fontSize": "12px"
                                }),
                            ])
                        ], style={"background": "rgba(255,255,255,0.03)", "border": f"1px solid {DARK['border']}",
                                  "borderRadius": "12px", "textAlign": "center"}), width=3),
                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.Div("📊", style={"fontSize": "28px", "textAlign": "center"}),
                                html.H6("RSI 策略", style={"textAlign": "center", "marginTop": "8px"}),
                                html.P("超买超卖信号", style={
                                    "textAlign": "center", "color": DARK["text_dim"], "fontSize": "12px"
                                }),
                            ])
                        ], style={"background": "rgba(255,255,255,0.03)", "border": f"1px solid {DARK['border']}",
                                  "borderRadius": "12px", "textAlign": "center"}), width=3),
                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.Div("📉", style={"fontSize": "28px", "textAlign": "center"}),
                                html.H6("MACD 策略", style={"textAlign": "center", "marginTop": "8px"}),
                                html.P("趋势跟踪", style={
                                    "textAlign": "center", "color": DARK["text_dim"], "fontSize": "12px"
                                }),
                            ])
                        ], style={"background": "rgba(255,255,255,0.03)", "border": f"1px solid {DARK['border']}",
                                  "borderRadius": "12px", "textAlign": "center"}), width=3),
                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.Div("📐", style={"fontSize": "28px", "textAlign": "center"}),
                                html.H6("布林带策略", style={"textAlign": "center", "marginTop": "8px"}),
                                html.P("均值回归", style={
                                    "textAlign": "center", "color": DARK["text_dim"], "fontSize": "12px"
                                }),
                            ])
                        ], style={"background": "rgba(255,255,255,0.03)", "border": f"1px solid {DARK['border']}",
                                  "borderRadius": "12px", "textAlign": "center"}), width=3),
                    ]),
                ])
            ], style=CARD_STYLE),
        ], width=12),
    ], className="mb-4") + [
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("➕ 保存自定义策略", style={"color": "#fff", "marginBottom": "16px"}),
                        dbc.Label("策略名称"),
                        dbc.Input(id="strat-name", placeholder="我的优化策略", className="mb-2"),
                        dbc.Label("描述"),
                        dbc.Textarea(id="strat-desc", placeholder="策略思路...", className="mb-2"),
                        dbc.Label("基础策略类型"),
                        dcc.Dropdown(id="strat-type",
                                     options=[
                                         {"label": "双均线策略", "value": "dual_ma"},
                                         {"label": "RSI 策略", "value": "rsi"},
                                         {"label": "MACD 策略", "value": "macd"},
                                         {"label": "布林带策略", "value": "bollinger"},
                                     ], value="dual_ma",
                                     style={"color": "#000", "marginBottom": "16px"}),
                        dbc.Button("💾 保存策略", id="btn-save-strat", color="primary", className="w-100"),
                        html.Div(id="strat-save-msg", style={
                            "color": "#22c55e", "fontSize": "13px", "marginTop": "8px", "display": "none"
                        }),
                    ])
                ], style=CARD_STYLE),
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📚 我的策略", style={"color": "#fff", "marginBottom": "16px"}),
                        html.Div(id="my-strategies"),
                    ])
                ], style=CARD_STYLE),
            ], width=8),
        ]),
    ]


# ===== 主布局 =====
app.layout = html.Div([
    dcc.Store(id="token-store", storage_type="local"),
    dcc.Store(id="user-store", storage_type="local"),
    dcc.Location(id="url", refresh=False),
    html.Div(id="nav-area"),
    html.Div(id="page-content", style={"minHeight": "calc(100vh - 80px)"}),
])


# ===== Callbacks =====

# 页面路由
@app.callback(
    [Output("page-content", "children"),
     Output("nav-area", "children"),
     Output("url", "pathname")],
    [Input("url", "pathname"),
     Input("token-store", "data")],
)
def route_page(pathname, token):
    nav_ctx = ctx.triggered_id if hasattr(ctx, 'triggered_id') else None

    if not token:
        if nav_ctx:
            return no_update, no_update, "/login"
        return login_page(), "", "/login"

    nav = navbar()
    if pathname == "/backtest":
        return backtest_page(), nav, pathname
    elif pathname == "/results":
        return results_page(), nav, pathname
    elif pathname == "/strategies":
        return strategies_page(), nav, pathname
    else:
        return dashboard_page(), nav, "/dashboard"


# 导航栏点击 — 用单个回调处理所有导航按钮
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    [Input("nav-dashboard", "n_clicks"),
     Input("nav-backtest", "n_clicks"),
     Input("nav-results", "n_clicks"),
     Input("nav-strategies", "n_clicks"),
     Input("btn-logout", "n_clicks")],
    prevent_initial_call=True,
)
def nav_click(n_dash, n_bt, n_res, n_strat, n_logout):
    trig = ctx.triggered_id
    if trig == "btn-logout":
        return "/login"
    page_map = {
        "nav-dashboard": "/dashboard",
        "nav-backtest": "/backtest",
        "nav-results": "/results",
        "nav-strategies": "/strategies",
    }
    return page_map.get(trig, "/dashboard")


# 退出时清除 token
@app.callback(
    Output("token-store", "data", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def clear_token_on_logout(pathname):
    if pathname == "/login":
        return None
    return no_update


# ===== 登录/注册 =====
@app.callback(
    Output("auth-msg", "children"),
    Input("btn-login", "n_clicks"),
    [State("login-user", "value"), State("login-pass", "value")],
    prevent_initial_call=True,
)
def do_login(n, user, pwd):
    if not user or not pwd:
        return "请输入用户名和密码"
    data = api_post("/api/auth/login", {"username": user, "password": pwd})
    if "access_token" in data:
        # 通过 dcc.Store callback 无法直接返回多个 output 给 Store，用 js 方式
        # 用 dcc.Location 配合 search/refresh
        return html.Div([
            html.Script(f"""
                localStorage.setItem('token', '{data["access_token"]}');
                localStorage.setItem('username', '{data["username"]}');
                window.location.href = '/dashboard';
            """),
        ])
    return data.get("detail", "登录失败")


@app.callback(
    Output("auth-msg", "children", allow_duplicate=True),
    Input("btn-register", "n_clicks"),
    [State("reg-user", "value"), State("reg-pass", "value")],
    prevent_initial_call=True,
)
def do_register(n, user, pwd):
    if not user or not pwd:
        return "请输入用户名和密码"
    data = api_post("/api/auth/register", {"username": user, "password": pwd})
    if "access_token" in data:
        return html.Div([
            html.Script(f"""
                localStorage.setItem('token', '{data["access_token"]}');
                localStorage.setItem('username', '{data["username"]}');
                window.location.href = '/dashboard';
            """),
        ])
    return data.get("detail", "注册失败")


# ===== 登录/注册页面 Tabs 切换 =====
@app.callback(
    [Output("login-form", "style"),
     Output("register-form", "style")],
    Input("auth-tabs", "active_tab"),
)
def toggle_auth_form(tab):
    hide = {"display": "none"}
    show = {}
    if tab == "login":
        return show, hide
    return hide, show


# ===== 策略选择切换参数和说明 =====
@app.callback(
    [Output("bt-params", "children"),
     Output("bt-desc", "children")],
    Input("bt-strategy", "value"),
)
def update_bt_params(strategy):
    descs = {
        "dual_ma": html.P([html.B("双均线策略：", style={"color": "#818cf8"}),
                           "MA5 上穿 MA20 买入，下穿卖出。趋势跟踪策略，适合趋势行情。"]),
        "rsi": html.P([html.B("RSI 策略：", style={"color": "#4ade80"}),
                       "RSI < 30 超卖买入，RSI > 70 超买卖出。震荡行情有效。"]),
        "macd": html.P([html.B("MACD 策略：", style={"color": "#facc15"}),
                        "MACD 上穿信号线买入，下穿卖出。经典趋势指标。"]),
        "bollinger": html.P([html.B("布林带策略：", style={"color": "#f87171"}),
                             "跌破下轨买入，突破上轨卖出。均值回归策略。"]),
    }

    if strategy == "dual_ma":
        params = [
            dbc.Label("短期均线周期"),
            dbc.Input(id="bt-short", type="number", value=5, className="mb-2"),
            dbc.Label("长期均线周期"),
            dbc.Input(id="bt-long", type="number", value=20, className="mb-3"),
        ]
    elif strategy == "rsi":
        params = [
            dbc.Label("RSI 周期"),
            dbc.Input(id="rsi-period", type="number", value=14, className="mb-2"),
            dbc.Label("超卖阈值"),
            dbc.Input(id="rsi-oversold", type="number", value=30, className="mb-2"),
            dbc.Label("超买阈值"),
            dbc.Input(id="rsi-overbought", type="number", value=70, className="mb-3"),
        ]
    else:
        params = [html.P("无需额外参数", style={"color": DARK["text_dim"], "fontSize": "13px"})]

    return params, descs.get(strategy, "")


# ===== 运行回测 =====
@app.callback(
    [Output("bt-result", "style"),
     Output("bt-metrics", "children"),
     Output("bt-equity-chart", "figure"),
     Output("bt-trades", "children"),
     Output("bt-error", "children"),
     Output("bt-error", "style"),
     Output("bt-loading", "style")],
    Input("btn-run-bt", "n_clicks"),
    [State("bt-strategy", "value"),
     State("bt-symbol", "value"),
     State("bt-days", "value"),
     State("bt-capital", "value"),
     State("bt-short", "value"),
     State("bt-long", "value"),
     State("rsi-period", "value"),
     State("rsi-oversold", "value"),
     State("rsi-overbought", "value"),
     State("token-store", "data")],
    prevent_initial_call=True,
)
def run_backtest(n, strategy, symbol, days, capital,
                 short_period, long_period, rsi_period, rsi_oversold, rsi_overbought,
                 token):
    if not token:
        return {"display": "none"}, no_update, no_update, no_update, "请先登录", {"color": "#ef4444", "fontSize": "13px", "marginTop": "8px", "display": "block"}, {"display": "none"}

    params = {}
    if strategy == "dual_ma":
        params = {"short_period": int(short_period or 5), "long_period": int(long_period or 20)}
    elif strategy == "rsi":
        params = {"period": int(rsi_period or 14), "oversold": int(rsi_oversold or 30), "overbought": int(rsi_overbought or 70)}

    payload = {
        "strategy_type": strategy,
        "symbol": symbol or "TEST",
        "days": int(days or 365),
        "initial_capital": float(capital or 100000),
        "parameters": params,
    }

    data = api_post("/api/backtest/run", payload, token=token)
    if "error" in data:
        return {"display": "none"}, no_update, no_update, no_update, data.get("detail", "回测失败"), {"color": "#ef4444", "fontSize": "13px", "marginTop": "8px", "display": "block"}, {"display": "none"}

    # 指标卡片
    is_pos = data.get("total_return", 0) >= 0
    metrics = dbc.Row([
        dbc.Col(metric_card("总收益率", f"{data['total_return']*100:.2f}%", is_pos), width=2),
        dbc.Col(metric_card("年化收益率", f"{data['annual_return']*100:.2f}%", data.get("annual_return", 0) >= 0), width=2),
        dbc.Col(metric_card("最大回撤", f"{data['max_drawdown']*100:.2f}%", False), width=2),
        dbc.Col(metric_card("夏普比率", f"{data['sharpe_ratio']:.2f}", True), width=2),
        dbc.Col(metric_card("交易次数", str(data['total_trades']), True), width=2),
        dbc.Col(metric_card("胜率", f"{data['win_rate']*100:.1f}%", data.get("win_rate", 0) >= 0.5), width=2),
    ])

    # 权益曲线
    ec = data.get("equity_curve", [])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[e["date"][:10] for e in ec],
        y=[e["equity"] for e in ec],
        mode="lines",
        name="权益曲线",
        line=dict(color="#6366f1", width=2),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.1)",
    ))
    fig.update_layout(
        title=dict(text="权益曲线", font=dict(color="#fff", size=14)),
        **PLOTLY_THEME,
        margin=dict(l=20, r=20, t=40, b=20),
        height=300,
        hovermode="x unified",
    )

    # 交易记录
    trades = data.get("trades", [])
    trade_rows = []
    for t in trades:
        color = "#22c55e" if t["action"] == "buy" else "#ef4444"
        label = "买入" if t["action"] == "buy" else "卖出"
        pnl_color = "#22c55e" if t.get("pnl", 0) >= 0 else "#ef4444"
        trade_rows.append(html.Tr([
            html.Td(t["date"][:10], style={"fontSize": "12px"}),
            html.Td(label, style={"color": color}),
            html.Td(f"{t['price']:.2f}"),
            html.Td(str(t["shares"])),
            html.Td(f"{t['pnl']:.2f}", style={"color": pnl_color}),
            html.Td(f"{t['cumulative_pnl']:.2f}"),
        ]))

    trade_table = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("日期"), html.Th("操作"), html.Th("价格"),
            html.Th("数量"), html.Th("盈亏"), html.Th("累计盈亏"),
        ]))] + [html.Tbody(trade_rows)],
        striped=False, hover=True, dark=True, size="sm",
        style={"fontSize": "13px"},
    ) if trade_rows else html.P("无交易记录", style={"color": DARK["text_dim"], "textAlign": "center", "padding": "20px"})

    return {"display": "block"}, metrics, fig, trade_table, "", {"display": "none"}, {"display": "none"}


def metric_card(label, value, is_positive=True):
    color = DARK["success"] if is_positive else DARK["danger"]
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.P(label, style={"color": DARK["text_dim"], "fontSize": "12px", "marginBottom": "4px"}),
            html.H5(value, style={"color": color if label not in ["夏普比率", "交易次数"] else "#fff",
                                  "fontWeight": "700", "margin": "0"}),
        ])
    ], style={"background": "rgba(255,255,255,0.03)", "border": f"1px solid {DARK['border']}",
              "borderRadius": "10px", "textAlign": "center", "padding": "4px"}),)


# ===== 仪表盘数据加载 =====
@app.callback(
    [Output("stat-total", "children"),
     Output("stat-avg-return", "children"),
     Output("stat-avg-return", "style"),
     Output("stat-best", "children"),
     Output("stat-best-ret", "children"),
     Output("stat-avg-sharpe", "children"),
     Output("chart-compare", "figure"),
     Output("recent-table", "children")],
    Input("url", "pathname"),
    State("token-store", "data"),
)
def load_dashboard(pathname, token):
    if pathname != "/dashboard" or not token:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    data = api_get("/api/backtest/results", token=token)
    results = data.get("results", [])

    if not results:
        empty_fig = go.Figure()
        empty_fig.update_layout(**PLOTLY_THEME, height=300,
                                annotations=[dict(text="暂无回测数据", showarrow=False,
                                                  font=dict(color=DARK["text_dim"], size=14))])
        empty = html.P([html.Span("暂无回测数据，去 ", style={"color": DARK["text_dim"]}),
                        html.A("新建回测", href="/backtest", style={"color": DARK["accent"]})],
                       style={"textAlign": "center", "padding": "40px"})
        return "0", "-", {"color": DARK["text_dim"], "fontWeight": "700"}, "-", "", "-", empty_fig, empty

    total = len(results)
    returns = [r["total_return"] for r in results]
    avg_ret = sum(returns) / len(returns)
    avg_ret_color = DARK["success"] if avg_ret >= 0 else DARK["danger"]

    best = max(results, key=lambda r: r["total_return"])
    sharps = [r["sharpe_ratio"] for r in results]
    avg_sharpe = sum(sharps) / len(sharps)

    # 对比图
    fig = go.Figure()
    types = list(set(r["strategy_type"] for r in results))
    for t in types:
        t_returns = [r["total_return"] * 100 for r in results if r["strategy_type"] == t]
        fig.add_trace(go.Bar(
            name=STRATEGY_NAMES.get(t, t),
            x=[STRATEGY_NAMES.get(t, t)],
            y=[sum(t_returns) / len(t_returns) if t_returns else 0],
            marker_color={"dual_ma": "#818cf8", "rsi": "#4ade80", "macd": "#facc15", "bollinger": "#f87171"}.get(t, "#6366f1"),
            text=[f"{sum(t_returns)/len(t_returns):.1f}%"],
            textposition="outside",
        ))
    fig.update_layout(
        **PLOTLY_THEME, height=300, showlegend=False,
        margin=dict(l=20, r=20, t=10, b=20),
        yaxis=dict(title="收益率 (%)", gridcolor="rgba(255,255,255,0.05)"),
    )

    # 最近回测表
    rows = []
    for r in results[:10]:
        ret_cls = DARK["success"] if r["total_return"] >= 0 else DARK["danger"]
        wr_cls = DARK["success"] if r["win_rate"] >= 0.5 else DARK["danger"]
        rows.append(html.Tr([
            html.Td(strategy_badge(r["strategy_type"])),
            html.Td(r.get("symbol", "")),
            html.Td(f"{r['total_return']*100:.2f}%", style={"color": ret_cls}),
            html.Td(f"{r['annual_return']*100:.2f}%"),
            html.Td(f"{r['max_drawdown']*100:.2f}%", style={"color": DARK["danger"]}),
            html.Td(f"{r['sharpe_ratio']:.2f}"),
            html.Td(str(r["total_trades"])),
            html.Td(f"{r['win_rate']*100:.1f}%", style={"color": wr_cls}),
            html.Td((r.get("created_at", "") or "")[:10], style={"fontSize": "12px", "color": DARK["text_dim"]}),
        ]))

    table = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("策略"), html.Th("标的"), html.Th("收益率"),
            html.Th("年化"), html.Th("最大回撤"), html.Th("夏普"),
            html.Th("交易"), html.Th("胜率"), html.Th("时间"),
        ]))] + [html.Tbody(rows)],
        striped=False, hover=True, dark=True, size="sm",
        style={"fontSize": "13px"},
    )

    return (str(total),
            f"{avg_ret*100:.2f}%", {"color": avg_ret_color, "fontWeight": "700"},
            STRATEGY_NAMES.get(best["strategy_type"], best["strategy_type"]),
            f"收益率: {best['total_return']*100:.2f}%",
            f"{avg_sharpe:.2f}",
            fig, table)


# ===== 历史结果 =====
@app.callback(
    Output("results-table", "children"),
    Input("url", "pathname"),
    State("token-store", "data"),
)
def load_results(pathname, token):
    if pathname != "/results" or not token:
        return no_update

    data = api_get("/api/backtest/results", token=token)
    results = data.get("results", [])

    if not results:
        return html.P([html.Span("暂无回测记录，去 ", style={"color": DARK["text_dim"]}),
                       html.A("新建回测", href="/backtest", style={"color": DARK["accent"]})],
                      style={"textAlign": "center", "padding": "40px"})

    rows = []
    for r in results:
        ret_cls = DARK["success"] if r["total_return"] >= 0 else DARK["danger"]
        rows.append(html.Tr([
            html.Td(strategy_badge(r["strategy_type"])),
            html.Td(r.get("symbol", "")),
            html.Td(f"{r['total_return']*100:.2f}%", style={"color": ret_cls}),
            html.Td(f"{r['annual_return']*100:.2f}%"),
            html.Td(f"{r['max_drawdown']*100:.2f}%", style={"color": DARK["danger"]}),
            html.Td(f"{r['sharpe_ratio']:.2f}"),
            html.Td(str(r["total_trades"])),
            html.Td(f"{r['win_rate']*100:.1f}%"),
            html.Td((r.get("created_at", "") or "")[:10], style={"fontSize": "12px", "color": DARK["text_dim"]}),
            html.Td([
                dbc.Button("详情", id={"type": "detail-btn", "index": r["id"]},
                           color="primary", size="sm", className="me-1"),
                dbc.Button("删除", id={"type": "del-btn", "index": r["id"]},
                           color="danger", size="sm"),
            ]),
        ]))

    return dbc.Table(
        [html.Thead(html.Tr([
            html.Th("策略"), html.Th("标的"), html.Th("收益率"),
            html.Th("年化"), html.Th("最大回撤"), html.Th("夏普"),
            html.Th("交易"), html.Th("胜率"), html.Th("时间"), html.Th("操作"),
        ]))] + [html.Tbody(rows)],
        striped=False, hover=True, dark=True, size="sm",
        style={"fontSize": "13px"},
    )


# ===== 策略管理 =====
@app.callback(
    Output("my-strategies", "children"),
    Input("url", "pathname"),
    State("token-store", "data"),
)
def load_strategies(pathname, token):
    if pathname != "/strategies" or not token:
        return no_update

    data = api_get("/api/strategies", token=token)
    strategies = data.get("strategies", [])

    if not strategies:
        return html.P("暂无保存的自定义策略", style={
            "color": DARK["text_dim"], "textAlign": "center", "padding": "40px"
        })

    rows = []
    for s in strategies:
        rows.append(html.Tr([
            html.Td(s["name"], style={"fontWeight": "600"}),
            html.Td(strategy_badge(s["strategy_type"])),
            html.Td(s.get("description", "-"), style={"color": DARK["text_dim"]}),
            html.Td((s.get("created_at", "") or "")[:10], style={"fontSize": "12px", "color": DARK["text_dim"]}),
        ]))

    return dbc.Table(
        [html.Thead(html.Tr([
            html.Th("名称"), html.Th("类型"), html.Th("描述"), html.Th("创建时间"),
        ]))] + [html.Tbody(rows)],
        striped=False, hover=True, dark=True, size="sm",
        style={"fontSize": "13px"},
    )


@app.callback(
    Output("strat-save-msg", "children"),
    Output("strat-save-msg", "style"),
    Input("btn-save-strat", "n_clicks"),
    [State("strat-name", "value"),
     State("strat-desc", "value"),
     State("strat-type", "value"),
     State("token-store", "data")],
    prevent_initial_call=True,
)
def save_strategy(n, name, desc, s_type, token):
    if not token:
        return "请先登录", {"color": "#ef4444", "fontSize": "13px", "marginTop": "8px", "display": "block"}
    if not name:
        return "请输入策略名称", {"color": "#ef4444", "fontSize": "13px", "marginTop": "8px", "display": "block"}

    data = api_post("/api/strategies", {
        "name": name, "description": desc or "", "strategy_type": s_type, "parameters": {},
    }, token=token)

    if "error" in data:
        return data.get("detail", "保存失败"), {"color": "#ef4444", "fontSize": "13px", "marginTop": "8px", "display": "block"}

    return "策略保存成功！", {"color": "#22c55e", "fontSize": "13px", "marginTop": "8px", "display": "block"}


# ===== 启动 =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
