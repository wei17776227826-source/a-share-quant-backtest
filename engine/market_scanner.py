# -*- coding: utf-8 -*-
"""
全市场扫描器 - 对 A 股每只股票运行 OMS 筛选条件
"""
import numpy as np
import pandas as pd
import time
from .eastmoney_data import fetch_data
from .data_loader import DataLoader


class MarketScanner:
    """市场扫描器，对给定日期的所有股票运行 OMS 筛选条件"""

    def __init__(self, cache_enabled=True):
        self.loader = DataLoader()
        self.cache_enabled = cache_enabled
        self._kline_cache = {}  # symbol -> DataFrame (历史K线 + 指标)

    def clear_cache(self):
        """清空数据缓存"""
        self._kline_cache = {}

    def scan(self, date, stocks, change_low=3.0, change_high=5.0,
             volume_ratio_min=1.0, volume_stack_ratio=1.2,
             progress_callback=None):
        """
        对给定日期扫描所有股票，筛选符合条件的股票

        参数:
            date: datetime or str，扫描目标日期
            stocks: list of dict [{code, name, market}, ...]
            change_low/change_high: 涨跌幅区间(%)
            volume_ratio_min: 量比下限
            volume_stack_ratio: 持续放量阈值
            progress_callback: 回调函数 func(current, total, msg)，可选

        返回:
            list of dict: [{code, name, price, reason}, ...]
        """
        results = []
        total = len(stocks)

        # 缓存：同一批次扫描只获取一次K线数据
        for idx, stock in enumerate(stocks):
            code = stock['code']
            name = stock['name']

            if progress_callback:
                progress_callback(idx + 1, total, "正在扫描 {} {}".format(code, name))

            try:
                # 获取K线数据（带缓存）
                df = self._get_kline_data(code)

                if df is None or len(df) < 60:
                    continue

                # 找到目标日期在数据中的位置
                target_date_str = str(date)[:10]
                date_mask = df['date'].astype(str).str.startswith(target_date_str)

                if not date_mask.any():
                    # 非交易日，跳过
                    continue

                target_idx = date_mask.values.argmax()
                target_row = df.iloc[target_idx]

                # 提取交易日前60个交易日的数据用于计算
                start_idx = max(0, target_idx - 59)
                sub_df = df.iloc[start_idx:target_idx + 1].copy().reset_index(drop=True)

                # 对子集计算指标
                sub_df = self.loader.calculate_indicators(sub_df)

                # 运行 OMS 筛选条件
                passed, reason = self._check_oms_filters(
                    sub_df, change_low, change_high, volume_ratio_min, volume_stack_ratio
                )

                if passed:
                    price = float(target_row['close'])
                    results.append({
                        'code': code,
                        'name': name,
                        'price': price,
                        'reason': reason,
                    })

            except Exception as e:
                # 单只股票失败不影响整体
                if progress_callback:
                    progress_callback(idx + 1, total, "{} 扫描失败: {}".format(code, e))
                continue

        # 按代码排序
        results.sort(key=lambda x: x['code'])
        return results

    def _get_kline_data(self, code, days=120):
        """
        获取股票K线数据（带缓存）

        参数:
            code: 股票代码
            days: 获取多少天的数据

        返回:
            DataFrame or None
        """
        if self.cache_enabled and code in self._kline_cache:
            return self._kline_cache[code]

        df = fetch_data(code, days)

        if df is not None and len(df) > 0:
            df = df.sort_values('date').reset_index(drop=True)
            if self.cache_enabled:
                self._kline_cache[code] = df

        return df

    def _check_oms_filters(self, df, change_low, change_high,
                           volume_ratio_min, volume_stack_ratio):
        """
        OMS 8步筛选条件的核心检查函数

        参数:
            df: DataFrame，包含至少60个完整交易日的数据和指标
            change_low/change_high: 涨跌幅区间(%)
            volume_ratio_min: 量比下限
            volume_stack_ratio: 持续放量阈值

        返回:
            (passed: bool, reason: str)
        """
        if df is None or len(df) < 2:
            return False, "数据不足"

        last = df.iloc[-1]
        close = float(last['close'])

        # ---- Filter 1: 涨跌幅 ----
        close_prev = float(df.iloc[-2]['close']) if len(df) >= 2 else close
        change_pct = (close / close_prev - 1) * 100

        if change_pct < change_low or change_pct > change_high:
            return False, "涨跌幅 {:.2f}% 不在 [{:.1f}%, {:.1f}%] 区间".format(
                change_pct, change_low, change_high
            )

        # ---- Filter 2: 量比（当日量 / 前5日均量）----
        volume = float(last['volume'])
        if len(df) >= 6:
            vol5 = df['volume'].iloc[-6:-1].mean()
        else:
            vol5 = volume

        if vol5 > 0:
            volume_ratio = volume / vol5
        else:
            volume_ratio = 0

        if volume_ratio <= volume_ratio_min:
            return False, "量比 {:.2f} 不大于 {}".format(volume_ratio, volume_ratio_min)

        # ---- Filter 5: 持续放量（近5日均量 > 近20日均量 * volume_stack_ratio）----
        if len(df) >= 20:
            vol5_mean = df['volume'].iloc[-5:].mean()
            vol20_mean = df['volume'].iloc[-20:].mean()
        else:
            vol5_mean = df['volume'].mean()
            vol20_mean = df['volume'].mean()

        if vol20_mean > 0 and vol5_mean <= vol20_mean * volume_stack_ratio:
            return False, "持续放量不满足 (近5日均量/{:.0f} < 近20日均量/{:.0f} * {})".format(
                vol5_mean, vol20_mean, volume_stack_ratio
            )

        # ---- 台阶式放量（近5日中 ≥60% 交易日成交量递增）----
        if len(df) >= 5:
            last5_vol = df['volume'].iloc[-5:].values
            up_count = sum(1 for j in range(1, len(last5_vol)) if last5_vol[j] > last5_vol[j-1])
            step_ratio = up_count / 5.0
            if step_ratio < 0.6:
                return False, "台阶式放量不满足 (递增比例 {:.0%} < 60%)".format(step_ratio)

        # ---- Filter 6: 均线多头排列 ----
        ma5 = float(last.get('MA5', np.nan)) if 'MA5' in df.columns else np.nan
        ma10 = float(last.get('MA10', np.nan)) if 'MA10' in df.columns else np.nan
        ma20 = float(last.get('MA20', np.nan)) if 'MA20' in df.columns else np.nan
        ma60 = float(last.get('MA60', np.nan)) if 'MA60' in df.columns else np.nan

        if any(np.isnan(x) for x in [ma5, ma10, ma20, ma60]):
            return False, "均线数据不足"

        if not (ma5 > ma10 > ma20 > ma60):
            return False, "均线非多头排列 (MA5={:.2f}, MA10={:.2f}, MA20={:.2f}, MA60={:.2f})".format(
                ma5, ma10, ma20, ma60
            )

        if not (close > ma5):
            return False, "收盘价 {:.2f} 未站上 MA5 {:.2f}".format(close, ma5)

        reasons = []
        reasons.append("涨跌幅 {:.2f}%".format(change_pct))
        reasons.append("量比 {:.2f}".format(volume_ratio))
        if vol20_mean > 0:
            reasons.append("持续放量 {:.2f}x".format(vol5_mean / vol20_mean))
        reasons.append("均线多头排列")

        return True, ", ".join(reasons)


# 简化版单日检查（供外部调用）
def check_stock_oms(code, days=120, change_low=3.0, change_high=5.0,
                    volume_ratio_min=1.0, volume_stack_ratio=1.2):
    """
    对单只股票检查 OMS 条件（基于最新交易日数据）

    返回:
        (passed: bool, reason: str, price: float)
    """
    from .data_loader import DataLoader
    from .eastmoney_data import fetch_data

    df = fetch_data(code, days)
    if df is None or len(df) == 0:
        return False, "获取数据失败", 0.0

    df = df.sort_values('date').reset_index(drop=True)
    loader = DataLoader()
    df = loader.calculate_indicators(df)

    scanner = MarketScanner()
    passed, reason = scanner._check_oms_filters(
        df, change_low, change_high, volume_ratio_min, volume_stack_ratio
    )
    price = float(df.iloc[-1]['close']) if len(df) > 0 else 0.0

    return passed, reason, price


if __name__ == '__main__':
    # 测试
    from .stock_pool import get_all_stocks

    print("获取全市场股票列表...")
    stocks = get_all_stocks()

    print("扫描最新交易日...")
    scanner = MarketScanner(cache_enabled=True)
    results = scanner.scan(
        pd.Timestamp.today(), stocks[:50],  # 先测50只
        change_low=3.0, change_high=5.0,
        volume_ratio_min=1.0, volume_stack_ratio=1.2,
    )

    print("\n扫描结果: {} 只符合条件".format(len(results)))
    for r in results:
        print("  {} {} 价格:{:.2f} - {}".format(r['code'], r['name'], r['price'], r['reason']))
