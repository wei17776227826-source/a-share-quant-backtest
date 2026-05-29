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


class OMSStrategy(StrategyBase):
    """尾盘动量隔夜策略 (Overnight Momentum Strategy)

    源自 github.com/hunkguo/overnight_momentum_strategy
    核心逻辑：下午 14:30 选股，尾盘买入，次日冲高卖出。

    8 步筛选（回测使用 Filter 1-6）:
      1. 涨跌幅 3%-5%
      2. 量比 > 1（当日量 / 前 5 日均量）
      3. 换手率 5%-10%（无流通股本数据时跳过）
      4. 流通市值 50-200 亿（无流通股本数据时跳过）
      5. 持续放量 — 近5日均量 > 近20日均量 × 1.2
      6. 均线多头排列 — MA5 > MA10 > MA20 > MA60，收盘 > MA5
      7. (跳过) 分时强势 — 需日内数据，回测中无法模拟
      8. (跳过) 回踩均价线不破 — 需日内数据，回测中无法模拟

    信号模式：T 日满足条件 → 收盘买入(1) → T+1 日卖出(-1)
    """

    def __init__(self, change_low=3.0, change_high=5.0,
                 volume_ratio_min=1.0,
                 turnover_low=5.0, turnover_high=10.0,
                 float_mv_low=50e8, float_mv_high=200e8,
                 volume_stack_ratio=1.2,
                 use_turnover_filter=False, use_float_mv_filter=False):
        """
        参数:
            change_low/change_high: 涨跌幅区间（%）
            volume_ratio_min: 量比下限
            turnover_low/turnover_high: 换手率区间（%）- 仅当 use_turnover_filter=True 生效
            float_mv_low/float_mv_high: 流通市值区间（元）- 仅当 use_float_mv_filter=True 生效
            volume_stack_ratio: 放量判定（近5日均量/近20日均量）
            use_turnover_filter: 是否启用换手率筛选（需流通股本数据）
            use_float_mv_filter: 是否启用流通市值筛选（需流通股本数据）
        """
        super().__init__("尾盘动量隔夜策略")
        self.change_low = change_low
        self.change_high = change_high
        self.volume_ratio_min = volume_ratio_min
        self.turnover_low = turnover_low
        self.turnover_high = turnover_high
        self.float_mv_low = float_mv_low
        self.float_mv_high = float_mv_high
        self.volume_stack_ratio = volume_stack_ratio
        self.use_turnover_filter = use_turnover_filter
        self.use_float_mv_filter = use_float_mv_filter

    def generate_signals(self, df):
        """
        OMS 隔夜信号生成。

        OMS 是"隔夜持股"策略：T 日满足条件 → 收盘买入 → T+1 日卖出。
        每笔交易独立：买入信号出现在满足条件的 T 日，卖出信号出现在 T+1 日。
        如果连续多日满足条件，会生成多笔独立的"买入→次日卖出"交易对。

        参数:
            df: DataFrame，需要包含:
                - close, volume, high, low (OHLC)
                - MA5, MA10, MA20, MA60 (由 DataLoader.calculate_indicators 提供)

        返回:
            signals: numpy array, 1=买入(收盘), -1=卖出(收盘), 0=持有
        """
        signals = np.zeros(len(df))

        close = df['close'].values
        volume = df['volume'].values

        # ---- Filter 1: 涨跌幅 ----
        change_pct = np.full(len(df), np.nan)
        change_pct[1:] = (close[1:] / close[:-1] - 1) * 100

        # ---- Filter 2: 量比（当日量 / 前5日均量）----
        vol_series = df['volume']
        vol5_avg = vol_series.rolling(5).mean().shift(1).values
        volume_ratio = np.full(len(df), np.nan)
        mask_vr = (vol5_avg > 0) & (~np.isnan(vol5_avg))
        volume_ratio[mask_vr] = volume[mask_vr] / vol5_avg[mask_vr]

        # ---- Filter 3: 换手率（可选）----
        has_turnover = 'turnover' in df.columns

        # ---- Filter 5: 持续放量 ----
        vol5 = vol_series.rolling(5).mean().values
        vol20 = vol_series.rolling(20).mean().values
        volume_ok = np.full(len(df), False)
        mask_v = (~np.isnan(vol5)) & (~np.isnan(vol20)) & (vol20 > 0)
        volume_ok[mask_v] = vol5[mask_v] > vol20[mask_v] * self.volume_stack_ratio

        # 台阶式：近5日中 ≥60% 的成交量大于前一日
        step_ok = np.full(len(df), False)
        for i in range(5, len(df)):
            last5 = volume[i-4:i+1]
            up_count = sum(1 for j in range(1, len(last5)) if last5[j] > last5[j-1])
            step_ok[i] = (up_count / 5) >= 0.6

        # ---- Filter 6: 均线多头排列 ----
        ma5 = df['MA5'].values if 'MA5' in df.columns else np.full(len(df), np.nan)
        ma10 = df['MA10'].values if 'MA10' in df.columns else np.full(len(df), np.nan)
        ma20 = df['MA20'].values if 'MA20' in df.columns else np.full(len(df), np.nan)
        ma60 = df['MA60'].values if 'MA60' in df.columns else np.full(len(df), np.nan)

        ma_ok = np.full(len(df), False)
        mask_ma = (~np.isnan(ma5)) & (~np.isnan(ma10)) & (~np.isnan(ma20)) & (~np.isnan(ma60))
        ma_ok[mask_ma] = (
            (ma5[mask_ma] > ma10[mask_ma]) &
            (ma10[mask_ma] > ma20[mask_ma]) &
            (ma20[mask_ma] > ma60[mask_ma]) &
            (close[mask_ma] > ma5[mask_ma])
        )

        # 记录每一天是否满足买入条件
        buy_conditions = np.zeros(len(df), dtype=bool)

        for i in range(1, len(df)):
            if np.isnan(change_pct[i]):
                continue
            if not (self.change_low <= change_pct[i] <= self.change_high):
                continue
            if np.isnan(volume_ratio[i]) or volume_ratio[i] <= self.volume_ratio_min:
                continue
            if self.use_turnover_filter and has_turnover:
                turn = df['turnover'].values[i] if 'turnover' in df.columns else np.nan
                if np.isnan(turn) or not (self.turnover_low <= turn <= self.turnover_high):
                    continue
            if not volume_ok[i] or not step_ok[i]:
                continue
            if not ma_ok[i]:
                continue
            buy_conditions[i] = True

        # 生成信号
        # 原则：每笔交易独立。满足条件的 T 日买入(1)，T+1 日卖出(-1)。
        # 连续满足条件时：昨天买入的今天先卖出 → 再买入今天的 → 明天再卖出
        # 但回测引擎是状态机，同一天只能做方向相反的交易
        # 所以我们使用双信号方案：
        #   满足条件的 i → signals[i] = 1 (买入)
        #   i-1 满足条件 → signals[i] = -1 (卖出上一笔)
        # 回测引擎靠"持仓状态"来协调：先检查卖出（持仓时卖），再检查买入（空仓时买）
        # 通过对 backtester.py 的扫描顺序做调整来实现
        for i in range(len(df)):
            if buy_conditions[i]:
                signals[i] = 1

        for i in range(1, len(df)):
            if buy_conditions[i - 1]:
                if signals[i] == 1:
                    # 同一天：先卖后买 → 用 -2 表示"卖出且今日也满足条件"
                    signals[i] = -2
                else:
                    signals[i] = -1

        return signals


# ============================================================
# 新增策略：基于 GitHub 高胜率策略搜索
# ============================================================

class NReboundStrategy(StrategyBase):
    """N 字反弹策略

    源自 github.com/konodiodaaaaa1/N-Rebound
    核心逻辑：涨停后缩量回调不破启动位 → 再次拉升
    买点：涨停后回调 2-5 天，量比萎缩 < 0.8，收盘 > MA5
    卖点：止盈 +8% / 止损 -5% (T+1 场景隔日卖出)

    回测胜率参考：>51% (XGBoost 增强版)
    """

    def __init__(self, callback_pct=3.0, volume_shrink=0.8, rebound_threshold=0.02):
        """
        参数:
            callback_pct: 回调深度百分比（涨停后回调 %）
            volume_shrink: 量比萎缩阈值（当日量 / 涨停日量）
            rebound_threshold: 反弹启动阈值（收盘 > MA5 的幅度）
        """
        super().__init__("N 字反弹策略")
        self.callback_pct = callback_pct
        self.volume_shrink = volume_shrink
        self.rebound_threshold = rebound_threshold

    def generate_signals(self, df):
        signals = np.zeros(len(df))
        close = df['close'].values
        volume = df['volume'].values
        ma5 = df['MA5'].values if 'MA5' in df.columns else np.full(len(df), np.nan)

        # 寻找涨停日（涨幅 >= 9.8%）
        change_pct = np.full(len(df), np.nan)
        change_pct[1:] = (close[1:] / close[:-1] - 1) * 100

        for i in range(5, len(df)):
            # 涨停日
            if np.isnan(change_pct[i]) or change_pct[i] < 9.5:
                continue

            # 涨停日成交量
            limit_up_vol = volume[i]

            # 检查后续 2-5 天是否回调
            for j in range(i + 1, min(i + 6, len(df))):
                # 回调：价格下跌，量萎缩
                vol_ratio = volume[j] / limit_up_vol if limit_up_vol > 0 else 1.0

                if close[j] < close[i] * (1 - self.callback_pct / 100) and vol_ratio < self.volume_shrink:
                    # 同时检查收盘是否在 MA5 附近或之上（企稳）
                    if not np.isnan(ma5[j]) and close[j] >= ma5[j] * (1 - self.rebound_threshold):
                        signals[j] = 1  # 买入信号
                    break

        # 卖出：隔日卖出（T+1）
        for i in range(1, len(df)):
            if signals[i - 1] == 1:
                if signals[i] == 1:
                    signals[i] = -2  # 先卖后买
                else:
                    signals[i] = -1

        return signals


class GoldenCrossStrategy(StrategyBase):
    """多金叉共振策略

    源自 KHunter 项目
    核心逻辑：均线金叉 + MACD 金叉 + KDJ 金叉 三重确认买入
    技术面多指标共振，过滤虚假信号

    回测胜率参考：50-55%
    """

    def __init__(self, ma_short=5, ma_long=20):
        super().__init__("多金叉共振策略")
        self.ma_short = ma_short
        self.ma_long = ma_long

    def _calculate_kdj(self, df):
        """计算 KDJ 指标"""
        low = df['low'].values
        high = df['high'].values
        close = df['close'].values

        k_values = np.full(len(df), 50.0)
        d_values = np.full(len(df), 50.0)

        for i in range(9, len(df)):
            hhv = np.max(high[i - 8:i + 1])
            llv = np.min(low[i - 8:i + 1])
            if hhv - llv > 1e-8:
                rsv = (close[i] - llv) / (hhv - llv) * 100
            else:
                rsv = 50.0
            k_values[i] = 2.0 / 3 * k_values[i - 1] + 1.0 / 3 * rsv
            d_values[i] = 2.0 / 3 * d_values[i - 1] + 1.0 / 3 * k_values[i]

        return k_values, d_values

    def generate_signals(self, df):
        signals = np.zeros(len(df))

        close = df['close'].values
        short_ma_col = 'MA{}'.format(self.ma_short)
        long_ma_col = 'MA{}'.format(self.ma_long)

        if short_ma_col not in df.columns or long_ma_col not in df.columns:
            return signals

        short_ma = df[short_ma_col].values
        long_ma = df[long_ma_col].values

        # KDJ
        k, d = self._calculate_kdj(df)

        macd = df['MACD'].values if 'MACD' in df.columns else np.full(len(df), np.nan)
        signal = df['Signal'].values if 'Signal' in df.columns else np.full(len(df), np.nan)

        for i in range(1, len(df)):
            # 均线金叉
            ma_golden = (not np.isnan(short_ma[i - 1]) and not np.isnan(long_ma[i - 1])
                         and not np.isnan(short_ma[i]) and not np.isnan(long_ma[i])
                         and short_ma[i - 1] <= long_ma[i - 1]
                         and short_ma[i] > long_ma[i])

            # MACD 金叉
            macd_golden = (not np.isnan(macd[i - 1]) and not np.isnan(signal[i - 1])
                           and not np.isnan(macd[i]) and not np.isnan(signal[i])
                           and macd[i - 1] <= signal[i - 1]
                           and macd[i] > signal[i])

            # KDJ 金叉
            kdj_golden = (not np.isnan(k[i - 1]) and not np.isnan(d[i - 1])
                          and not np.isnan(k[i]) and not np.isnan(d[i])
                          and k[i - 1] <= d[i - 1] and k[i] > d[i]
                          and k[i] < 80)  # 避免超买区域

            # 三个金叉中至少两个共振
            golden_count = sum([ma_golden, macd_golden, kdj_golden])
            if golden_count >= 2:
                signals[i] = 1

            # 死叉卖出
            ma_dead = (not np.isnan(short_ma[i - 1]) and not np.isnan(long_ma[i - 1])
                       and not np.isnan(short_ma[i]) and not np.isnan(long_ma[i])
                       and short_ma[i - 1] >= long_ma[i - 1]
                       and short_ma[i] < long_ma[i])

            if ma_dead:
                signals[i] = -1

        return signals


class BreakoutStrategy(StrategyBase):
    """阻力位突破策略

    源自 KHunter 项目
    核心逻辑：股价突破近期高点（20 日新高）+ 放量确认
    突破关键阻力位后入场，趋势跟踪

    回测胜率参考：50-60%
    """

    def __init__(self, lookback=20, volume_multiplier=1.3, breakout_pct=0.01):
        """
        参数:
            lookback: 回看周期（突破近 N 日高点）
            volume_multiplier: 放量倍数（突破日量 / 前 N 日均量）
            breakout_pct: 突破确认幅度
        """
        super().__init__("阻力位突破策略")
        self.lookback = lookback
        self.volume_multiplier = volume_multiplier
        self.breakout_pct = breakout_pct

    def generate_signals(self, df):
        signals = np.zeros(len(df))
        close = df['close'].values
        volume = df['volume'].values

        # 计算前 N 日的最高价
        vol_avg = pd.Series(volume).rolling(self.lookback).mean().shift(1).values

        for i in range(self.lookback, len(df)):
            prev_high = np.max(close[i - self.lookback:i])
            prev_avg_vol = vol_avg[i]

            # 突破阻力位 + 放量确认
            if (close[i] > prev_high * (1 + self.breakout_pct)
                    and not np.isnan(prev_avg_vol)
                    and volume[i] > prev_avg_vol * self.volume_multiplier):
                signals[i] = 1

        # 止损卖出：跌破 MA20
        ma20 = df['MA20'].values if 'MA20' in df.columns else np.full(len(df), np.nan)
        for i in range(1, len(df)):
            if not np.isnan(ma20[i]) and close[i] < ma20[i]:
                if signals[i] == 1:
                    signals[i] = -2
                else:
                    signals[i] = -1

        return signals


class SqueezeStrategy(StrategyBase):
    """涨停回马枪策略

    源自 KHunter 项目
    核心逻辑：涨停后横盘整理（3-8 天），量能萎缩，然后放量突破
    捕捉强势股洗盘后的第二波拉升

    回测胜率参考：50-55%
    """

    def __init__(self, squeeze_days=5, max_squeeze_days=10, vol_shrink_pct=0.6):
        """
        参数:
            squeeze_days: 最短横盘天数
            max_squeeze_days: 最长横盘天数
            vol_shrink_pct: 横盘期成交量萎缩比例（相对涨停日）
        """
        super().__init__("涨停回马枪策略")
        self.squeeze_days = squeeze_days
        self.max_squeeze_days = max_squeeze_days
        self.vol_shrink_pct = vol_shrink_pct

    def generate_signals(self, df):
        signals = np.zeros(len(df))
        close = df['close'].values
        volume = df['volume'].values

        change_pct = np.full(len(df), np.nan)
        change_pct[1:] = (close[1:] / close[:-1] - 1) * 100

        for i in range(1, len(df)):
            # 寻找涨停日
            if np.isnan(change_pct[i]) or change_pct[i] < 9.5:
                continue

            limit_up_vol = volume[i]
            limit_up_close = close[i]

            # 检查后续横盘整理
            for end in range(i + self.squeeze_days, min(i + self.max_squeeze_days + 1, len(df))):
                squeeze_range = close[i + 1:end + 1]
                squeeze_vol = volume[i + 1:end + 1]

                # 横盘：价格在涨停日收盘 -3% ~ +3% 之间震荡
                price_in_range = all(
                    limit_up_close * 0.97 <= p <= limit_up_close * 1.03
                    for p in squeeze_range
                )

                # 缩量：横盘期最大量 < 涨停日量 × vol_shrink_pct
                vol_ok = np.max(squeeze_vol) <= limit_up_vol * self.vol_shrink_pct

                if price_in_range and vol_ok:
                    # 横盘结束日买入
                    signals[end] = 1
                    break

        # 隔日卖出（T+1）
        for i in range(1, len(df)):
            if signals[i - 1] == 1:
                if signals[i] == 1:
                    signals[i] = -2
                else:
                    signals[i] = -1

        return signals


class ContrarianStrategy(StrategyBase):
    """情绪极端反转策略

    源自 github.com/NadirAliOfficial/contrarian-trading-strategy + quant-strategies 市场情绪策略
    核心逻辑：RSI 超卖 + 布林带下轨 + 缩量 → 恐慌买入
    在极端情绪时逆势入场，抓取情绪修复反弹

    回测胜率参考：45-55%
    """

    def __init__(self, rsi_oversold=25, bb_factor=1.0, volume_shrink=0.7):
        """
        参数:
            rsi_oversold: RSI 超卖阈值
            bb_factor: 布林带下轨偏移因子（1.0=标准下轨）
            volume_shrink: 缩量阈值（当日量 / 前 20 日均量）
        """
        super().__init__("情绪极端反转策略")
        self.rsi_oversold = rsi_oversold
        self.bb_factor = bb_factor
        self.volume_shrink = volume_shrink

    def generate_signals(self, df):
        signals = np.zeros(len(df))
        close = df['close'].values
        volume = df['volume'].values

        rsi = df['RSI'].values if 'RSI' in df.columns else np.full(len(df), np.nan)
        bb_lower = df['BB_Lower'].values if 'BB_Lower' in df.columns else np.full(len(df), np.nan)

        vol_avg = pd.Series(volume).rolling(20).mean().values

        for i in range(20, len(df)):
            buy_signal = False

            # RSI 超卖
            if not np.isnan(rsi[i]) and rsi[i] < self.rsi_oversold:
                buy_signal = True

            # 价格跌破布林带下轨（更恐慌）
            if not np.isnan(bb_lower[i]) and close[i] < bb_lower[i] * (2 - self.bb_factor):
                buy_signal = True

            # 缩量确认（恐慌时量能萎缩）
            if not np.isnan(vol_avg[i]) and volume[i] > vol_avg[i] * self.volume_shrink:
                buy_signal = True

            # 至少满足两个条件
            conditions = 0
            if not np.isnan(rsi[i]) and rsi[i] < self.rsi_oversold:
                conditions += 1
            if not np.isnan(bb_lower[i]) and close[i] < bb_lower[i] * (2 - self.bb_factor):
                conditions += 1
            if not np.isnan(vol_avg[i]) and volume[i] < vol_avg[i] * self.volume_shrink:
                conditions += 1

            if conditions >= 2:
                signals[i] = 1

        # 卖出：反弹到布林带中轨或 RSI > 60
        bb_mid = df['BB_Middle'].values if 'BB_Middle' in df.columns else np.full(len(df), np.nan)
        for i in range(1, len(df)):
            sell_signal = False
            if not np.isnan(bb_mid[i]) and close[i] >= bb_mid[i]:
                sell_signal = True
            if not np.isnan(rsi[i]) and rsi[i] > 60:
                sell_signal = True

            if sell_signal:
                if signals[i] == 1:
                    signals[i] = -2
                elif signals[i] == 0:
                    signals[i] = -1

        return signals


class MATrendStrategy(StrategyBase):
    """均线多头排列趋势跟踪策略

    核心逻辑：MA5 > MA10 > MA20 > MA60 (多头排列) 买入
    均线死叉或跌破 MA60 卖出
    趋势跟踪，吃主升浪鱼身

    回测胜率参考：45-55% (高盈亏比补偿低胜率)
    """

    def __init__(self):
        super().__init__("均线趋势跟踪策略")

    def generate_signals(self, df):
        signals = np.zeros(len(df))
        close = df['close'].values

        ma5 = df['MA5'].values if 'MA5' in df.columns else np.full(len(df), np.nan)
        ma10 = df['MA10'].values if 'MA10' in df.columns else np.full(len(df), np.nan)
        ma20 = df['MA20'].values if 'MA20' in df.columns else np.full(len(df), np.nan)
        ma60 = df['MA60'].values if 'MA60' in df.columns else np.full(len(df), np.nan)

        for i in range(60, len(df)):
            # 多头排列买入
            if (not np.isnan(ma5[i]) and not np.isnan(ma10[i])
                and not np.isnan(ma20[i]) and not np.isnan(ma60[i])
                and close[i] > ma5[i] > ma10[i] > ma20[i] > ma60[i]):

                # 前一天不是多头排列（刚形成）
                if (np.isnan(ma5[i - 1]) or np.isnan(ma10[i - 1])
                    or np.isnan(ma20[i - 1]) or np.isnan(ma60[i - 1])
                    or not (close[i - 1] > ma5[i - 1] > ma10[i - 1] > ma20[i - 1] > ma60[i - 1])):
                    signals[i] = 1

            # 死叉或跌破 MA60 卖出
            if (not np.isnan(ma5[i]) and not np.isnan(ma10[i])
                and ma5[i] < ma10[i]):
                signals[i] = -1

            if not np.isnan(ma60[i]) and close[i] < ma60[i]:
                if signals[i] == 1:
                    signals[i] = -2
                else:
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
