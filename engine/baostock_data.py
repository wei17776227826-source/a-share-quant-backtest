# -*- coding: utf-8 -*-
"""
Baostock 数据源模块 — 免费开源 A 股行情数据

Baostock (http://baostock.com) 提供规范化的 A 股历史行情数据：
- 日/周/月 K 线，5/15/30/60 分钟线
- 前复权/后复权/不复权
- 支持指数、板块数据
- 支持交易日历查询
- 国内服务器友好，阿里云 ECS 可正常使用

与现有 tdx_data / eastmoney_data 保持一致的 fetch_data() 接口。
兼容 DataLoader 基类。

依赖: pip install baostock
      Python 3.6+ (本服务器 Python 3.6 已验证可用)
"""
import pandas as pd
import numpy as np
import baostock as bs
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================
# 常量定义
# ============================================================

# Baostock 市场代码前缀
BS_SH = 'sh'  # 上海证券交易所
BS_SZ = 'sz'  # 深圳证券交易所

# 复权类型
ADJUST_NONE = '1'     # 不复权
ADJUST_FORWARD = '2'  # 前复权（推荐用于回测）
ADJUST_BACKWARD = '3' # 后复权

# K 线周期
FREQ_DAY = 'd'    # 日线
FREQ_WEEK = 'w'   # 周线
FREQ_MONTH = 'm'  # 月线
FREQ_5MIN = '5'   # 5分钟
FREQ_15MIN = '15' # 15分钟
FREQ_30MIN = '30' # 30分钟
FREQ_60MIN = '60' # 60分钟

# ============================================================
# Baostock 会话管理（单例模式）
# ============================================================

_bs_logged_in = False


def _ensure_login():
    """确保 Baostock 已登录（懒登录，单例）"""
    global _bs_logged_in
    if not _bs_logged_in:
        lg = bs.login()
        if lg.error_code != '0':
            raise ConnectionError("Baostock 登录失败: {}".format(lg.error_msg))
        _bs_logged_in = True
        logger.info("Baostock 登录成功")


def logout():
    """登出 Baostock"""
    global _bs_logged_in
    if _bs_logged_in:
        bs.logout()
        _bs_logged_in = False
        logger.info("Baostock 已登出")


# ============================================================
# 工具函数
# ============================================================

def get_bs_code(symbol):
    """
    将 A 股代码转换为 Baostock 格式

    参数:
        symbol: 纯数字代码，如 '600519', '000001'

    返回:
        str: 'sh.600519' 或 'sz.000001'
    """
    symbol = symbol.strip()
    if symbol.startswith('6'):
        return 'sh.{}'.format(symbol)
    elif symbol.startswith(('0', '3')):
        return 'sz.{}'.format(symbol)
    elif symbol.startswith(('4', '8')):
        return 'bj.{}'.format(symbol)  # 北交所
    else:
        logger.warning("baostock_data: 无法识别的股票代码 %s", symbol)
        return None


# ============================================================
# 核心数据获取函数
# ============================================================

def fetch_data(symbol, days=365):
    """
    对外统一接口 — 与 tdx_data.fetch_data() / eastmoney_data.fetch_data() 完全兼容

    从 Baostock 获取 A 股历史日K线数据（前复权）

    参数:
        symbol: 股票代码，如 '600519'（贵州茅台）、'000001'（平安银行）
        days: 获取多少个自然日的数据（实际返回交易日数据）

    返回:
        DataFrame with columns: date, open, close, high, low, volume, amount
        或 None（失败时）
    """
    try:
        _ensure_login()
    except ConnectionError as e:
        logger.error("Baostock 连接失败: %s", e)
        return None

    bs_code = get_bs_code(symbol)
    if bs_code is None:
        return None

    # 计算日期范围
    end = datetime.today()
    start = end - timedelta(days=days)

    end_str = end.strftime('%Y-%m-%d')
    start_str = start.strftime('%Y-%m-%d')

    try:
        # 查询日K线数据（前复权）
        rs = bs.query_history_k_data_plus(
            bs_code,
            fields='date,open,high,low,close,volume,amount',
            start_date=start_str,
            end_date=end_str,
            frequency=FREQ_DAY,
            adjustflag=ADJUST_FORWARD,  # 前复权
        )

        if rs.error_code != '0':
            logger.warning("Baostock 查询失败 [%s]: %s", symbol, rs.error_msg)
            return None

        # 提取数据
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())

        if not data_list:
            logger.warning("Baostock: %s 无数据", symbol)
            return None

        # 转换为 DataFrame
        df = pd.DataFrame(data_list, columns=rs.fields)

        # 类型转换
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 日期转换
        df['date'] = pd.to_datetime(df['date'])

        # 排序
        df = df.sort_values('date').reset_index(drop=True)

        # 过滤无效行
        df = df.dropna(subset=['open', 'close'])

        if len(df) == 0:
            return None

        logger.info("Baostock 获取 %s 成功，共 %s 条数据", symbol, len(df))
        return df

    except Exception as e:
        logger.error("Baostock 获取 %s 异常: %s", symbol, e)
        return None


def fetch_data_no_adjust(symbol, days=365):
    """
    获取不复权的原始数据

    参数:
        symbol: 股票代码
        days: 天数

    返回:
        DataFrame or None
    """
    try:
        _ensure_login()
    except ConnectionError as e:
        return None

    bs_code = get_bs_code(symbol)
    if bs_code is None:
        return None

    end = datetime.today()
    start = end - timedelta(days=days)

    try:
        rs = bs.query_history_k_data_plus(
            bs_code,
            fields='date,open,high,low,close,preclose,volume,amount,peTTM,pbMRQ',
            start_date=start.strftime('%Y-%m-%d'),
            end_date=end.strftime('%Y-%m-%d'),
            frequency=FREQ_DAY,
            adjustflag=ADJUST_NONE,  # 不复权
        )

        if rs.error_code != '0':
            return None

        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())

        if not data_list:
            return None

        df = pd.DataFrame(data_list, columns=rs.fields)
        numeric_cols = ['open', 'high', 'low', 'close', 'preclose',
                        'volume', 'amount', 'peTTM', 'pbMRQ']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        return df

    except Exception as e:
        logger.error("Baostock 不复权获取异常: %s", e)
        return None


# ============================================================
# 高级功能：交易日历、指数、股票列表
# ============================================================

def get_trade_cal(start_date=None, end_date=None):
    """
    获取 A 股交易日历

    参数:
        start_date: str, '2026-01-01' 或 None（默认一年前）
        end_date: str, '2026-06-04' 或 None（默认今天）

    返回:
        list of str: ['2026-01-02', '2026-01-03', ...]
    """
    try:
        _ensure_login()
    except ConnectionError:
        return None

    if start_date is None:
        start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')

    try:
        rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
        if rs.error_code != '0':
            return None

        trade_dates = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            # row: [日期, 是否交易日: '0'否 '1'是]
            if len(row) >= 2 and row[1] == '1':
                trade_dates.append(row[0])

        return trade_dates
    except Exception as e:
        logger.error("获取交易日历失败: %s", e)
        return None


def get_stock_list():
    """
    从 Baostock 获取全市场 A 股列表

    返回:
        list of dict: [{code, name, market}, ...]
    """
    try:
        _ensure_login()
    except ConnectionError:
        return None

    try:
        rs = bs.query_all_stock(day=datetime.today().strftime('%Y-%m-%d'))
        if rs.error_code != '0':
            return None

        stocks = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            # row: [code, tradeStatus, code_name]
            if len(row) < 3:
                continue
            code = row[0]  # 'sh.600519' 格式
            status = row[1]
            name = row[2]

            if status != '1':  # 仅包含交易中的股票
                continue

            # 只保留 A 股
            if not code.startswith(('sh.', 'sz.')):
                continue

            # 提取纯数字代码
            market_prefix = code[:2]  # 'sh' or 'sz'
            pure_code = code[3:]      # '600519'

            stocks.append({
                'code': pure_code,
                'name': name,
                'market': market_prefix,
            })

        logger.info("Baostock 获取 A 股列表: %s 只", len(stocks))
        return stocks
    except Exception as e:
        logger.error("Baostock 获取股票列表失败: %s", e)
        return None


def get_index_data(index_code='sh.000001', days=365):
    """
    获取指数行情数据（上证指数/深证成指/创业板指等）

    参数:
        index_code: 指数代码
            'sh.000001' 上证指数
            'sz.399001' 深证成指
            'sz.399006' 创业板指
            'sh.000688' 科创50
        days: 天数

    返回:
        DataFrame or None
    """
    try:
        _ensure_login()
    except ConnectionError:
        return None

    end = datetime.today()
    start = end - timedelta(days=days)

    try:
        rs = bs.query_history_k_data_plus(
            index_code,
            fields='date,open,high,low,close,volume,amount',
            start_date=start.strftime('%Y-%m-%d'),
            end_date=end.strftime('%Y-%m-%d'),
            frequency=FREQ_DAY,
        )

        if rs.error_code != '0':
            return None

        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())

        if not data_list:
            return None

        df = pd.DataFrame(data_list, columns=rs.fields)
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        return df
    except Exception as e:
        logger.error("Baostock 获取指数数据失败: %s", e)
        return None


# ============================================================
# 兼容现有 DataLoader 的数据加载器类
# ============================================================

class BaostockDataLoader:
    """
    Baostock 数据加载器

    兼容现有 DataLoader / ChineseDataLoader / TdxDataLoader 的调用方式，
    底层使用 Baostock 数据源。
    """

    @staticmethod
    def fetch_data(symbol, days=365):
        """
        获取真实行情数据（Baostock 数据源）

        参数:
            symbol: A 股代码，如 '600519'（茅台）、'000001'（平安银行）
            days: 获取多少天的历史数据

        返回:
            DataFrame or raise ValueError
        """
        df = fetch_data(symbol, days)
        if df is not None and len(df) > 0:
            return df
        raise ValueError("Baostock: 未获取到 {} 的数据，请检查股票代码是否正确".format(symbol))

    @staticmethod
    def fetch_data_no_adjust(symbol, days=365):
        """获取不复权数据"""
        df = fetch_data_no_adjust(symbol, days)
        if df is not None and len(df) > 0:
            return df
        raise ValueError("Baostock: 未获取到 {} 的不复权数据".format(symbol))

    @staticmethod
    def get_stock_list():
        """获取 A 股列表"""
        return get_stock_list()

    @staticmethod
    def get_index(index_code, days=365):
        """获取指数数据"""
        return get_index_data(index_code, days)

    @staticmethod
    def get_trade_dates(start_date, end_date):
        """获取交易日历"""
        return get_trade_cal(start_date, end_date)


# ============================================================
# 数据源统一接口（多数据源自动 fallback）
# ============================================================

def fetch_from_multi_source(symbol, days=365, sources=None):
    """
    多数据源自动 fallback 获取

    参数:
        symbol: 股票代码
        days: 天数
        sources: 数据源优先级列表，如 ['baostock', 'tencent', 'eastmoney']
                 默认: ['baostock', 'tencent']
                 说明: Baostock 在阿里云 ECS 上工作稳定，推荐作为首选

    返回:
        DataFrame or None
    """
    if sources is None:
        sources = ['baostock', 'tencent']

    for source in sources:
        df = None
        try:
            if source == 'baostock':
                df = fetch_data(symbol, days)
            elif source == 'tencent':
                from .tdx_data import fetch_data as fetch_tencent
                df = fetch_tencent(symbol, days)
            elif source == 'eastmoney':
                from .eastmoney_data import fetch_data as fetch_eastmoney
                df = fetch_eastmoney(symbol, days)
        except Exception as e:
            logger.warning("数据源 %s 获取 %s 失败: %s", source, symbol, e)
            continue

        if df is not None and len(df) > 0:
            logger.info("从数据源 %s 获取 %s 成功，共 %s 条", source, symbol, len(df))
            return df

    logger.error("所有数据源获取 %s 均失败", symbol)
    return None


# ============================================================
# 测试入口
# ============================================================

if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )

    test_codes = ['600519', '000001', '300750', '601318', '002415']

    print("=" * 60)
    print("Baostock 数据源测试")
    print("=" * 60)

    # 测试1: 日K线数据
    print("\n1. 获取前复权日K线数据:")
    for code in test_codes[:3]:
        df = fetch_data(code, 60)
        if df is not None:
            print("  {}: {} 条, {} ~ {}, 收盘 {:.2f}".format(
                code, len(df),
                df['date'].iloc[0].strftime('%Y-%m-%d'),
                df['date'].iloc[-1].strftime('%Y-%m-%d'),
                df['close'].iloc[-1]
            ))
        else:
            print("  {}: 获取失败".format(code))

    # 测试2: 交易日历
    print("\n2. 获取交易日历:")
    trade_dates = get_trade_cal('2026-01-01', '2026-01-31')
    if trade_dates:
        print("  2026年1月交易日: {} 天".format(len(trade_dates)))
        print("  首日: {}, 末日: {}".format(trade_dates[0], trade_dates[-1]))

    # 测试3: 指数数据
    print("\n3. 获取指数数据:")
    df_idx = get_index_data('sh.000001', 60)
    if df_idx is not None:
        print("  上证指数: {} 条, 最新收盘 {:.2f}".format(
            len(df_idx), df_idx['close'].iloc[-1]
        ))

    bs.logout()
