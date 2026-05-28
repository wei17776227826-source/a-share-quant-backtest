# -*- coding: utf-8 -*-
"""
从东方财富 API 获取 A 股/港股/美股实时数据
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re


def fetch_from_eastmoney(symbol, days=365):
    """
    从东方财富 API 获取股票历史数据

    参数:
        symbol: 股票代码
            A股: 600519（茅台）、000001（平安）
            美股: 用 yahoo 格式
           港股: 00700（腾讯）
        days: 天数

    返回:
        DataFrame or None
    """
    # 东方财富 K 线接口
    # secid: 0.000001 (深交所), 1.600519 (上交所)
    secid = get_secid(symbol)
    if secid is None:
        return None

    end_date = datetime.today().strftime('%Y%m%d')
    start_date = (datetime.today() - timedelta(days=days)).strftime('%Y%m%d')

    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'ut': '7eea3edcaed734bea9c8f5d91c4b8e2b',
        'klt': '101',  # 日K
        'fqt': '1',    # 前复权
        'secid': secid,
        'beg': start_date,
        'end': end_date,
    }

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get('data') is None or data['data'].get('klines') is None:
        return None

    klines = data['data']['klines']
    rows = []
    for line in klines:
        parts = line.split(',')
        # 日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
        rows.append({
            'date': parts[0],
            'open': float(parts[1]),
            'close': float(parts[2]),
            'high': float(parts[3]),
            'low': float(parts[4]),
            'volume': int(parts[5]),
            'amount': float(parts[6]),
        })

    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


def get_secid(symbol):
    """将股票代码转换为东方财富 secid 格式"""
    symbol = symbol.strip()

    # 美股 (带后缀)
    if symbol.endswith('.SS'):
        return f'1.{symbol.replace(".SS", "")}'
    if symbol.endswith('.SZ'):
        return f'0.{symbol.replace(".SZ", "")}'
    if symbol.endswith('.HK'):
        return f'128.{symbol.replace(".HK", "")}'

    # 美股 - 用新浪接口
    if symbol.endswith('.O') or symbol.endswith('.NS'):
        return None  # 美股走新浪

    # 智能判断
    # 6开头 = 上交所
    if symbol.startswith('6'):
        return f'1.{symbol}'
    # 0/3开头 = 深交所
    if symbol.startswith(('0', '3')):
        return f'0.{symbol}'

    return None


def fetch_us_stock(symbol, days=365):
    """从新浪财经获取美股数据"""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    url = 'https://quotes.sina.com.cn/api/quotes.php'
    params = {
        'dotype': 'last',
        'cb': 'callback',
        'symbol': symbol,
    }

    # 直接用 yahoo 国内替代 - 用 akshare 替代不了，试试 e投接口
    import warnings
    warnings.warn(f"美股 {symbol} 暂不支持，请使用 A 股代码")
    return None


class ChineseDataLoader:
    """数据加载器 - 支持东方财富 A 股数据"""

    @staticmethod
    def fetch_data(symbol, days=365):
        """
        获取真实行情数据

        A 股示例: 600519（贵州茅台）、000001（平安银行）、300750（宁德时代）
        """
        df = fetch_from_eastmoney(symbol, days)
        if df is not None:
            return df
        raise ValueError(f"未获取到 {symbol} 的数据，请检查股票代码是否正确")


if __name__ == '__main__':
    # 测试
    for code in ['600519', '000001', '300750']:
        df = fetch_from_eastmoney(code, 30)
        if df is not None:
            print(f"{code}: {len(df)} 条, {str(df['date'].iloc[0])[:10]} ~ {str(df['date'].iloc[-1])[:10]}, 收盘 {df['close'].iloc[-1]:.2f}")
