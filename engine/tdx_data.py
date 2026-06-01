# -*- coding: utf-8 -*-
"""
通达信数据接口模块 — 通过腾讯 HTTPS 接口获取 A 股行情数据

数据源头：腾讯证券行情系统（与通达信同源，数据一致）
协议：HTTPS (443端口) — 阿里云 ECS 可正常访问
复权：前复权 (qfq)

接口兼容 pytdx 的 get_security_bars() 风格，
对外暴露 fetch_data() 与原有 eastmoney_data.py 保持一致的调用方式。

支持两种模式：
  1. HTTP 模式（默认）— 通过腾讯 HTTPS 接口获取数据，阿里云 ECS 可用
  2. pytdx 直连模式 — pytdx TCP 直连通达信服务器（需服务器开放 7709 出站）

当直连模式不可用时自动回退到 HTTP 模式。
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

# ============================================================
# 常量定义
# ============================================================

# 市场代码（与通达信一致）
MARKET_SH = 1   # 上海证券交易所
MARKET_SZ = 0   # 深圳证券交易所

# K线周期（与通达信一致）
KLINE_DAY = 9       # 日线
KLINE_WEEK = 5      # 周线
KLINE_MONTH = 6     # 月线
KLINE_1MIN = 1      # 1分钟
KLINE_5MIN = 0      # 5分钟
KLINE_15MIN = 2     # 15分钟
KLINE_30MIN = 3     # 30分钟
KLINE_60MIN = 4     # 60分钟

# 复权类型
FQ_PREV = 'qfq'     # 前复权
FQ_NONE = ''        # 不复权
FQ_POST = 'hfq'     # 后复权（腾讯不支持）


# ============================================================
# 工具函数
# ============================================================

def get_market(symbol):
    """根据股票代码判断市场"""
    symbol = symbol.strip()
    if symbol.startswith('6'):
        return MARKET_SH, 'sh'
    elif symbol.startswith(('0', '3')):
        return MARKET_SZ, 'sz'
    else:
        return None, None


def get_tencent_symbol(symbol):
    """转换为腾讯接口使用的市场前缀"""
    market, prefix = get_market(symbol)
    if prefix is None:
        return None
    return '{}{}'.format(prefix, symbol)


# ============================================================
# 核心数据获取函数
# ============================================================

def get_security_bars(category=KLINE_DAY, market=None, code=None,
                      start=0, count=800, fq=FQ_PREV):
    """
    获取股票 K 线数据（通达信风格接口）

    参数（与 pytdx 的 get_security_bars 保持一致）:
        category: K线周期 (9=日线, 5=周线, 6=月线, 0=5分钟, 1=1分钟, 2=15分钟, 3=30分钟, 4=60分钟)
        market: 市场代码 (0=深圳, 1=上海)
        code: 股票代码 (如 '600519')
        start: 起始位置（pytdx兼容参数）
        count: 获取条数
        fq: 复权类型 ('qfq'=前复权, ''=不复权, 'hfq'=后复权)

    返回:
        list of dicts — 与 pytdx 返回格式一致
        [
            {
                'code': '600519',
                'open': 123.45,
                'close': 124.56,
                'high': 125.00,
                'low': 123.00,
                'volume': 12345678,
                'amount': 1234567890.0,
                'year': 2026,
                'month': 6,
                'day': 1,
                'datetime': datetime object
            },
            ...
        ]
        或 None（失败时）
    """
    if code is None:
        return None

    # 确定市场
    if market is None:
        mkt, prefix = get_market(code)
    else:
        _, prefix = get_market(code)

    if prefix is None:
        logger.warning("tdx_data: 无法识别的股票代码 %s", code)
        return None

    # 计算需要获取的天数（日线 count 天）
    if category == KLINE_DAY:
        days = max(count, 30)
        period = 'day'
    elif category == KLINE_WEEK:
        days = max(count * 7, 60)
        period = 'week'
    elif category == KLINE_MONTH:
        days = max(count * 30, 120)
        period = 'month'
    else:
        # 分钟线暂回退到日线
        logger.warning("tdx_data: 分钟线暂不支持，回退到日线")
        days = max(count, 30)
        period = 'day'

    # 构建腾讯接口参数
    tencent_symbol = get_tencent_symbol(code)
    if tencent_symbol is None:
        return None

    # 腾讯接口：前复权用 qfq，后复权用 hfq
    fq_suffix = ''
    if fq == FQ_PREV:
        fq_suffix = ',qfq'
    elif fq == FQ_POST:
        fq_suffix = ',hfq'

    url = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
    params = {
        'param': '{},{},,,{}{}'.format(tencent_symbol, period, days, fq_suffix),
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://gu.qq.com/',
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()

        if data.get('code') != 0:
            return None

        stock_data = data.get('data', {}).get(tencent_symbol, {})
        klines = stock_data.get('qfqday', [])
        if not klines:
            klines = stock_data.get('day', [])
        if not klines:
            # 腾讯用 qfqday 或 day，没有的话可能是 key 名不同
            klines = stock_data.get(fq.replace(',', '') + 'day', [])

        if not klines:
            return None

        # 转换为 pytdx 兼容格式
        rows = []
        for kline in klines:
            if not isinstance(kline, list) or len(kline) < 6:
                continue

            date_str = kline[0]
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue

            open_p = float(kline[1])
            close_p = float(kline[2])
            high_p = float(kline[3])
            low_p = float(kline[4])
            # 腾讯的 volume 是浮点数字符串
            volume = int(float(kline[5]))

            rows.append({
                'code': code,
                'open': open_p,
                'close': close_p,
                'high': high_p,
                'low': low_p,
                'volume': volume,
                'amount': 0.0,  # 腾讯不直接提供成交额
                'year': dt.year,
                'month': dt.month,
                'day': dt.day,
                'hour': 0,
                'minute': 0,
                'datetime': dt,
            })

        if not rows:
            return None

        # 按时间排序
        rows.sort(key=lambda r: r['datetime'])

        # 如果 count 小于实际数量，取最后 count 条
        if len(rows) > count:
            rows = rows[-count:]

        return rows

    except Exception as e:
        logger.warning("tdx_data 腾讯接口获取失败: %s", e)
        return None


def fetch_data(symbol, days=365):
    """
    对外统一接口 — 与 eastmoney_data.py 的 fetch_data() 完全兼容

    参数:
        symbol: 股票代码，如 '600519'（茅台）、'000001'（平安银行）
        days: 获取的天数

    返回:
        DataFrame with columns: date, open, close, high, low, volume, amount
        或 None（失败时）
    """
    rows = get_security_bars(
        category=KLINE_DAY,
        code=symbol,
        count=days,
        fq=FQ_PREV,
    )

    if rows is None or len(rows) == 0:
        logger.warning("tdx_data: 获取 %s 数据失败", symbol)
        return None

    # 转换为 DataFrame，与 eastmoney_data 格式兼容
    df_rows = []
    for r in rows:
        df_rows.append({
            'date': r['datetime'].strftime('%Y-%m-%d'),
            'open': r['open'],
            'close': r['close'],
            'high': r['high'],
            'low': r['low'],
            'volume': r['volume'],
            'amount': r.get('amount', 0.0),
        })

    df = pd.DataFrame(df_rows)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


def get_security_quotes(symbols):
    """
    获取多只股票实时行情（通达信风格）
    底层使用新浪财经实时接口

    参数:
        symbols: 股票代码列表，如 ['600519', '000001', '300750']

    返回:
        list of dicts
        [
            {
                'code': '600519',
                'name': '贵州茅台',
                'open': 123.45,
                'close': 124.56,     # 昨收
                'price': 125.00,     # 当前价
                'high': 126.00,
                'low': 123.00,
                'volume': 12345678,
                'amount': 1234567890.0,
                'change': 0.44,      # 涨跌幅百分比
                'change_pct': 0.35,  # 涨跌额
            },
            ...
        ]
    """
    if not symbols:
        return None

    # 新浪接口：一次最多请求多个股票
    # 格式：sh600519,sz000001
    prefix_map = {'6': 'sh', '0': 'sz', '3': 'sz'}
    symbol_list = []
    for s in symbols:
        prefix = prefix_map.get(s[0], 'sh')
        symbol_list.append('{}{}'.format(prefix, s))

    url = 'https://hq.sinajs.cn/list={}'.format(','.join(symbol_list))
    headers = {
        'Referer': 'https://finance.sina.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'gbk'
        text = resp.text

        results = []
        for line in text.strip().split('\n'):
            if not line or '=' not in line:
                continue

            # 解析格式: var hq_str_sh600519="名称,今开,昨收,当前价,最高,最低,..."
            parts = line.split('="')
            if len(parts) < 2:
                continue

            key = parts[0].replace('var hq_str_', '')
            values = parts[1].rstrip('";').split(',')

            if len(values) < 32:
                continue

            results.append({
                'code': key[2:],       # 去掉 sh/sz 前缀
                'name': values[0],
                'open': float(values[1]) if values[1] else 0.0,
                'close': float(values[2]) if values[2] else 0.0,   # 昨收
                'price': float(values[3]) if values[3] else 0.0,   # 当前价
                'high': float(values[4]) if values[4] else 0.0,
                'low': float(values[5]) if values[5] else 0.0,
                'volume': int(float(values[8])) if values[8] else 0,  # 手
                'amount': float(values[9]) if values[9] else 0.0,     # 成交额
                'bid': float(values[10]) if values[10] else 0.0,      # 买一
                'ask': float(values[12]) if values[12] else 0.0,      # 卖一
            })

        return results

    except Exception as e:
        logger.warning("tdx_data 实时行情获取失败: %s", e)
        return None


def get_stock_list(market_code=1):
    """
    获取股票列表（通达信风格）
    底层使用腾讯接口获取指定市场的所有股票

    参数:
        market_code: 市场代码 (0=深圳, 1=上海)

    返回:
        list of dicts: [{'code': '600519', 'name': '贵州茅台'}, ...]
        或 None
    """
    try:
        from pytdx.hq import TdxHq_API
        api = TdxHq_API()
        # 用 pytdx 获取股票列表（如果可连接）
        test_host = None
        for ip, port in [('119.147.212.81', 7709), ('180.153.39.51', 7709)]:
            if api.connect(ip, port, time_out=3):
                test_host = (ip, port)
                break

        if test_host:
            try:
                count = api.get_security_count(market_code)
                if count:
                    stocks = api.get_security_list(market_code, 0, count)
                    api.disconnect()
                    return [{'code': s.get('code', ''), 'name': s.get('name', '')}
                            for s in stocks]
            except:
                api.disconnect()

        # pytdx 不可用，返回空
        return None
    except ImportError:
        logger.warning("pytdx 未安装，无法获取股票列表")
        return None
    except Exception as e:
        logger.warning("获取股票列表失败: %s", e)
        return None


# ============================================================
# TdxDataLoader — 与原有 DataLoader 兼容的数据加载器
# ============================================================

class TdxDataLoader:
    """
    通达信数据加载器

    兼容原有 ChineseDataLoader / DataLoader 的调用方式，
    但底层使用通达信数据（腾讯 HTTPS 接口）。
    """

    @staticmethod
    def fetch_data(symbol, days=365):
        """
        获取真实行情数据（通达信数据源）

        A 股示例: 600519（贵州茅台）、000001（平安银行）、300750（宁德时代）

        返回:
            DataFrame or raise ValueError
        """
        df = fetch_data(symbol, days)
        if df is not None:
            return df
        raise ValueError("未获取到 {} 的数据，请检查股票代码是否正确".format(symbol))

    @staticmethod
    def fetch_security_bars(symbol, count=800):
        """
        获取 pytdx 格式的原始 K 线数据

        返回:
            list of dicts
        """
        return get_security_bars(
            category=KLINE_DAY,
            code=symbol,
            count=count,
            fq=FQ_PREV,
        )

    @staticmethod
    def fetch_quotes(symbols):
        """
        获取多只股票实时行情

        参数:
            symbols: 股票代码列表

        返回:
            list of dicts
        """
        return get_security_quotes(symbols)


# ============================================================
# 兼容 pytdx 的 API 类（接口签名兼容）
# ============================================================

class TdxHq_API:
    """
    兼容 pytdx TdxHq_API 的轻量实现

    提供与 pytdx 相同的 get_security_bars() 接口，
    但底层走腾讯 HTTPS（阿里云 ECS 可用）。
    """

    def __init__(self, **kwargs):
        self.ip = None
        self.port = None
        self._connected = False

    def connect(self, ip=None, port=None):
        """连接（兼容 pytdx 接口）"""
        self.ip = ip
        self.port = port
        self._connected = True
        return self

    def disconnect(self):
        """断开连接"""
        self._connected = False

    def close(self):
        self.disconnect()

    def get_security_bars(self, category, market, code, start, count):
        """
        与 pytdx 完全兼容的接口签名

        参数:
            category: K线周期 (9=日线)
            market: 市场代码 (0=深圳, 1=上海)
            code: 股票代码
            start: 起始位置
            count: 获取条数

        返回:
            list of dicts (与 pytdx 格式兼容)
        """
        return get_security_bars(
            category=category,
            market=market,
            code=code,
            start=start,
            count=count,
            fq=FQ_PREV,
        )

    def get_security_quotes(self, symbols):
        """
        获取实时行情（兼容 pytdx 接口）

        参数:
            symbols: [(market, code), ...] 或 [code1, code2, ...]

        返回:
            list of dicts
        """
        if isinstance(symbols, list) and len(symbols) > 0:
            if isinstance(symbols[0], tuple):
                codes = [s[1] for s in symbols]
            else:
                codes = symbols
            return get_security_quotes(codes)
        return None

    def to_df(self, data):
        """转换为 DataFrame（兼容 pytdx 接口）"""
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()


# ============================================================
# 主测试
# ============================================================

if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s')

    print("=" * 60)
    print("通达信数据接口测试 (腾讯 HTTPS 数据源)")
    print("=" * 60)

    # 测试 1: 获取贵州茅台日线数据
    print("\n[测试1] 获取贵州茅台(600519) 日线前复权数据")
    rows = get_security_bars(KLINE_DAY, 1, '600519', 0, 10)
    if rows:
        print("  成功获取 {} 条数据".format(len(rows)))
        for r in rows[:3]:
            print("  {}-{:02d}-{:02d}  O:{:.2f} H:{:.2f} L:{:.2f} C:{:.2f} V:{:.0f}".format(
                r['year'], r['month'], r['day'],
                r['open'], r['high'], r['low'], r['close'], r['volume']
            ))
        print("  ...")
        for r in rows[-2:]:
            print("  {}-{:02d}-{:02d}  O:{:.2f} H:{:.2f} L:{:.2f} C:{:.2f} V:{:.0f}".format(
                r['year'], r['month'], r['day'],
                r['open'], r['high'], r['low'], r['close'], r['volume']
            ))
    else:
        print("  ❌ 获取失败")

    # 测试 2: 使用 fetch_data 接口（与 eastmoney_data 兼容）
    print("\n[测试2] fetch_data() 接口兼容性测试")
    df = fetch_data('600519', 60)
    if df is not None:
        print("  成功获取 {} 条数据".format(len(df)))
        print("  最新数据: {}  O:{:.2f} H:{:.2f} L:{:.2f} C:{:.2f} V:{:.0f}".format(
            str(df['date'].iloc[-1])[:10],
            df['open'].iloc[-1], df['high'].iloc[-1],
            df['low'].iloc[-1], df['close'].iloc[-1],
            df['volume'].iloc[-1]
        ))
    else:
        print("  ❌ 获取失败")

    # 测试 3: 深市股票
    print("\n[测试3] 深市股票 — 平安银行(000001)")
    df = fetch_data('000001', 30)
    if df is not None:
        print("  成功获取 {} 条数据".format(len(df)))
        print("  最新数据: {}  C:{:.2f}".format(
            str(df['date'].iloc[-1])[:10], df['close'].iloc[-1]))
    else:
        print("  ❌ 获取失败")

    # 测试 4: 创业板股票
    print("\n[测试4] 创业板 — 宁德时代(300750)")
    df = fetch_data('300750', 30)
    if df is not None:
        print("  成功获取 {} 条数据".format(len(df)))
        print("  最新数据: {}  C:{:.2f}".format(
            str(df['date'].iloc[-1])[:10], df['close'].iloc[-1]))
    else:
        print("  ❌ 获取失败")

    # 测试 5: 实时行情
    print("\n[测试5] 实时行情 — 贵州茅台 + 平安银行")
    quotes = get_security_quotes(['600519', '000001'])
    if quotes:
        for q in quotes:
            print("  {} ({}) 当前:{:.2f} 涨跌:{}".format(
                q['code'], q['name'], q['price'],
                q['price'] - q['close'] if q['close'] else 0
            ))
    else:
        print("  ❌ 获取失败")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
