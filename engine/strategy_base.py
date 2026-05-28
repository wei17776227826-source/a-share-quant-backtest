# -*- coding: utf-8 -*-
"""
策略基类和内置策略
"""
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod


class StrategyBase(ABC):
    """策略抽象基类"""

    def __init__(self, name="基础策略"):
        self.name = name

    @abstractmethod
    def generate_signals(self, df):
        """
        生成交易信号

        参数:
            df: DataFrame，包含价格和技术指标数据

        返回:
            signals: numpy array, 1=买入, -1=卖出, 0=持有
        """
        pass


class DualMAStrategy(StrategyBase):
    """双均线策略 - MA5 上穿 MA20 买入，下穿卖出"""

    def __init__(self, short_period=5, long_period=20):
        super().__init__("双均线策略")
        self.short_period = short_period
        self.long_period = long_period

    def generate_signals(self, df):
        signals = np.zeros(len(df))

        short_ma_col = 'MA{}'.format(self.short_period)
        long_ma_col = 'MA{}'.format(self.long_period)

        if short_ma_col not in df.columns or long_ma_col not in df.columns:
            print("警告: 数据缺少 {} 或 {} 列".format(short_ma_col, long_ma_col))
            return signals

        short_ma = df[short_ma_col].values
        long_ma = df[long_ma_col].values

        for i in range(1, len(df)):
            if pd.isna(short_ma[i]) or pd.isna(long_ma[i]):
                continue

            # 上穿：前一日短均线 <= 长均线，今日短均线 > 长均线
            if (not pd.isna(short_ma[i-1]) and not pd.isna(long_ma[i-1])
                    and short_ma[i-1] <= long_ma[i-1]
                    and short_ma[i] > long_ma[i]):
                signals[i] = 1
            # 下穿：前一日短均线 >= 长均线，今日短均线 < 长均线
            elif (not pd.isna(short_ma[i-1]) and not pd.isna(long_ma[i-1])
                  and short_ma[i-1] >= long_ma[i-1]
                  and short_ma[i] < long_ma[i]):
                signals[i] = -1

        return signals


class RSIStrategy(StrategyBase):
    """RSI 策略 - RSI < 30 买入，RSI > 70 卖出"""

    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__("RSI 策略")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df):
        signals = np.zeros(len(df))

        rsi_col = 'RSI'
        if rsi_col not in df.columns:
            print("警告: 数据缺少 {} 列".format(rsi_col))
            return signals

        rsi = df[rsi_col].values

        for i in range(len(df)):
            if pd.isna(rsi[i]):
                continue

            if rsi[i] < self.oversold:
                signals[i] = 1
            elif rsi[i] > self.overbought:
                signals[i] = -1

        return signals


class MACDStrategy(StrategyBase):
    """MACD 策略 - MACD 上穿信号线买入，下穿卖出"""

    def __init__(self):
        super().__init__("MACD 策略")

    def generate_signals(self, df):
        signals = np.zeros(len(df))

        if 'MACD' not in df.columns or 'Signal' not in df.columns:
            print("警告: 数据缺少 MACD 或 Signal 列")
            return signals

        macd = df['MACD'].values
        signal = df['Signal'].values

        for i in range(1, len(df)):
            if pd.isna(macd[i]) or pd.isna(signal[i]):
                continue

            # 上穿
            if (not pd.isna(macd[i-1]) and not pd.isna(signal[i-1])
                    and macd[i-1] <= signal[i-1]
                    and macd[i] > signal[i]):
                signals[i] = 1
            # 下穿
            elif (not pd.isna(macd[i-1]) and not pd.isna(signal[i-1])
                  and macd[i-1] >= signal[i-1]
                  and macd[i] < signal[i]):
                signals[i] = -1

        return signals


class BollingerStrategy(StrategyBase):
    """布林带策略 - 跌破下轨买入，突破上轨卖出"""

    def __init__(self):
        super().__init__("布林带策略")

    def generate_signals(self, df):
        signals = np.zeros(len(df))

        if 'BB_Upper' not in df.columns or 'BB_Lower' not in df.columns:
            print("警告: 数据缺少 BB_Upper 或 BB_Lower 列")
            return signals

        close = df['close'].values
        upper = df['BB_Upper'].values
        lower = df['BB_Lower'].values

        for i in range(len(df)):
            if pd.isna(upper[i]) or pd.isna(lower[i]):
                continue

            # 跌破下轨买入
            if close[i] < lower[i]:
                signals[i] = 1
            # 突破上轨卖出
            elif close[i] > upper[i]:
                signals[i] = -1

        return signals
