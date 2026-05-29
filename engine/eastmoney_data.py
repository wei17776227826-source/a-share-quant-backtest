# -*- coding: utf-8 -*-
"""
从东方财富 API 获取 A 股/港股/美股实时数据
- 主数据源: 东方财富 push2his.eastmoney.com
- 备选数据源: 腾讯 gtimg (web.ifzq.gtimg.cn) — 东方财富失败时自动 fallback
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re
import time


def fetch_from_eastmoney(symbol, days=365):
    """
    从东方财富 API 获取股票历史数据（主数据源）

    参数:
        symbol: 股票代码
            A股: 600519（茅台）、000001（平安）
        days: 天数

    返回:
        DataFrame or None
    """
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

    try:
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
    except Exception as e:
        print("东方财富数据获取失败: {}".format(e))
        return None


def fetch_from_tencent(symbol, days=365):
    """
    从腾讯 gtimg API 获取股票历史数据（备选数据源）

    参数:
        symbol: A 股代码，如 600519
        days: 天数

    返回:
        DataFrame or None
    """
    # 腾讯接口使用 sz/sh 前缀
    if symbol.startswith('6'):
        tencent_symbol = 'sh{}'.format(symbol)
    elif symbol.startswith(('0', '3')):
        tencent_symbol = 'sz{}'.format(symbol)
    else:
        return None

    url = 'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
    params = {
        'param': '{},day,,,{},qfq'.format(tencent_symbol, days),
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()

        if data.get('code') != 0:
            return None

        stock_data = data.get('data', {}).get(tencent_symbol, {})
        klines = stock_data.get('qfqday', [])
        if not klines:
            # 部分接口用 day 而不是 qfqday
            klines = stock_data.get('day', [])

        if not klines:
            return None

        rows = []
        for kline in klines:
            # 腾讯格式: [日期, 开盘, 收盘, 最高, 最低, 成交量]
            # 注意腾讯格式是: 日期, open, close, high, low, volume
            # 与东方财富不同（open, close, high, low）
            # 最后一条可能是分红信息 dict，跳过
            if not isinstance(kline, list) or len(kline) < 6:
                continue

            date_str = kline[0]
            open_p = float(kline[1])
            close_p = float(kline[2])
            high_p = float(kline[3])
            low_p = float(kline[4])
            volume = int(float(kline[5]))

            rows.append({
                'date': date_str,
                'open': open_p,
                'close': close_p,
                'high': high_p,
                'low': low_p,
                'volume': volume,
                'amount': 0.0,  # 腾讯接口不直接提供成交额
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        print("从腾讯 gtimg 获取 {} 数据成功，共 {} 条".format(symbol, len(df)))
        return df
    except Exception as e:
        print("腾讯 gtimg 数据获取失败: {}".format(e))
        return None


def fetch_data(symbol, days=365):
    """
    获取股票历史数据，带自动 fallback

    优先使用东方财富，失败时自动切换到腾讯 gtimg

    参数:
        symbol: 股票代码
        days: 天数

    返回:
        DataFrame or None
    """
    # 先试东方财富
    df = fetch_from_eastmoney(symbol, days)
    if df is not None and len(df) > 0:
        print("从东方财富获取 {} 数据成功，共 {} 条".format(symbol, len(df)))
        return df

    # 东方财富失败，尝试腾讯
    print("东方财富获取 {} 失败，切换到腾讯 gtimg...".format(symbol))
    time.sleep(0.5)  # 稍等避免请求过快
    df = fetch_from_tencent(symbol, days)
    if df is not None and len(df) > 0:
        return df

    # 都失败了
    print("所有数据源获取 {} 均失败".format(symbol))
    return None


def get_secid(symbol):
    """将股票代码转换为东方财富 secid 格式"""
    symbol = symbol.strip()

    # 美股 (带后缀)
    if symbol.endswith('.SS'):
        return '1.{}'.format(symbol.replace('.SS', ''))
    if symbol.endswith('.SZ'):
        return '0.{}'.format(symbol.replace('.SZ', ''))
    if symbol.endswith('.HK'):
        return '128.{}'.format(symbol.replace('.HK', ''))

    # 美股 - 用新浪接口
    if symbol.endswith('.O') or symbol.endswith('.NS'):
        return None  # 美股走新浪

    # 智能判断
    # 6开头 = 上交所
    if symbol.startswith('6'):
        return '1.{}'.format(symbol)
    # 0/3开头 = 深交所
    if symbol.startswith(('0', '3')):
        return '0.{}'.format(symbol)

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

    import warnings
    warnings.warn("美股 {} 暂不支持，请使用 A 股代码".format(symbol))
    return None


class ChineseDataLoader:
    """数据加载器 - 支持东方财富 A 股数据（含腾讯 fallback）"""

    @staticmethod
    def fetch_data(symbol, days=365):
        """
        获取真实行情数据

        A 股示例: 600519（贵州茅台）、000001（平安银行）、300750（宁德时代）
        """
        df = fetch_data(symbol, days)
        if df is not None:
            return df
        raise ValueError("未获取到 {} 的数据，请检查股票代码是否正确".format(symbol))


if __name__ == '__main__':
    # 测试
    for code in ['600519', '000001', '300750']:
        df = fetch_data(code, 60)
        if df is not None:
            print("{}: {} 条, {} ~ {}, 收盘 {:.2f}".format(
                code, len(df), str(df['date'].iloc[0])[:10],
                str(df['date'].iloc[-1])[:10], df['close'].iloc[-1]
            ))
        else:
            print("{}: 获取失败".format(code))
