# -*- coding: utf-8 -*-
"""
数据加载器 - 支持通达信（腾讯HTTPS）A 股真实数据及生成模拟数据
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .tdx_data import fetch_data as fetch_from_tdx


class DataLoader:
    """数据加载器类"""

    def __init__(self):
        self.cache = {}

    def fetch_real_data(self, symbol, days=365):
        """
        获取真实 A 股数据（通达信数据源 - 腾讯 HTTPS 接口）

        参数:
            symbol: A 股代码，如 '600519'（茅台）、'000001'（平安银行）
            days: 获取多少天的历史数据

        返回:
            DataFrame with columns: date, open, high, low, close, volume, amount
        """
        df = fetch_from_tdx(symbol, days)
        if df is None:
            raise ValueError(f"未获取到 {symbol} 的数据，请检查股票代码是否正确")

        df = self.calculate_indicators(df)
        return df

    def generate_sample_data(self, symbol, days):
        """
        生成模拟股票数据（OHLCV）

        参数:
            symbol: 股票代码/名称
            days: 交易日天数

        返回:
            DataFrame with columns: date, open, high, low, close, volume
        """
        np.random.seed(42)
        dates = pd.date_range(end=datetime.today(), periods=days, freq='B')

        # 从 100 开始，每日变化 -3% 到 +3%
        price = 100.0
        closes = []
        for _ in range(days):
            change = np.random.uniform(-0.03, 0.03)
            price = price * (1 + change)
            closes.append(price)

        closes = np.array(closes)

        # 生成 OHLCV
        daily_range = np.random.uniform(0.005, 0.02, days)
        highs = closes * (1 + daily_range)
        lows = closes * (1 - daily_range)
        opens = lows + (highs - lows) * np.random.uniform(0.3, 0.7, days)
        volumes = np.random.randint(100000, 5000000, days)

        df = pd.DataFrame({
            'date': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        })

        # 计算技术指标
        df = self.calculate_indicators(df)

        return df

    def load_from_csv(self, filepath):
        """从本地 CSV 文件加载数据（预留功能）"""
        try:
            df = pd.read_csv(filepath)
            if 'date' not in df.columns:
                raise ValueError("CSV 文件缺少 date 列")
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            df = self.calculate_indicators(df)
            return df
        except Exception as e:
            print("CSV 加载失败: {}".format(e))
            return None

    def calculate_indicators(self, df):
        """
        计算常用技术指标：MA5, MA10, MA20, MA60, EMA12, EMA26,
        MACD, Signal, Histogram, RSI(14), Bollinger Bands(Upper/Middle/Lower)

        参数:
            df: DataFrame，包含 close 列

        返回:
            DataFrame，追加了指标列
        """
        if df is None or len(df) == 0:
            return df

        df = df.copy()
        close = df['close']

        # 移动平均线
        df['MA5'] = close.rolling(window=5).mean()
        df['MA10'] = close.rolling(window=10).mean()
        df['MA20'] = close.rolling(window=20).mean()
        df['MA60'] = close.rolling(window=60).mean()

        # EMA
        df['EMA12'] = close.ewm(span=12, adjust=False).mean()
        df['EMA26'] = close.ewm(span=26, adjust=False).mean()

        # MACD
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']

        # RSI(14)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(span=14, adjust=False).mean()
        avg_loss = loss.ewm(span=14, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands (20, 2)
        df['BB_Middle'] = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + 2 * bb_std
        df['BB_Lower'] = df['BB_Middle'] - 2 * bb_std

        return df
