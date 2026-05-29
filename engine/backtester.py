# -*- coding: utf-8 -*-
"""
回测引擎 - 核心回测逻辑
"""
import pandas as pd
import numpy as np
import math
import time
from datetime import datetime, timedelta


class Backtester:
    """回测引擎类"""

    def __init__(self, strategy, data, initial_capital=100000):
        """
        初始化回测引擎

        参数:
            strategy: StrategyBase 实例，交易策略
            data: DataFrame，包含 OHLCV 数据和技术指标
            initial_capital: 初始资金
        """
        self.strategy = strategy
        self.data = data.copy() if data is not None else None
        self.initial_capital = initial_capital

    def run(self):
        """
        执行回测

        返回:
            dict，包含回测结果：
                - total_return: 总收益率
                - annual_return: 年化收益率
                - max_drawdown: 最大回撤
                - sharpe_ratio: 夏普比率（年化，无风险利率 0.03）
                - total_trades: 总交易次数
                - win_rate: 胜率
                - trades: list of dict (date, action, price, shares, pnl, cumulative_pnl)
                - equity_curve: list of dict (date, equity)
        """
        if self.data is None or len(self.data) == 0:
            return self._empty_result()

        # 生成交易信号
        signals = self.strategy.generate_signals(self.data)

        # 执行回测
        capital = float(self.initial_capital)
        position = 0  # 持仓股数
        position_cost = 0.0  # 持仓成本

        trades = []
        equity_curve = []
        cumulative_pnl = 0.0

        close_prices = self.data['close'].values
        dates = self.data['date'].values

        for i in range(len(self.data)):
            current_price = float(close_prices[i])
            current_date = dates[i]

            signal = signals[i]

            # ---- 先处理卖出信号 ----
            # 支持 -1（普通卖出）和 -2（卖出后今日还要买入）
            if (signal in (-1, -2)) and position > 0:
                sell_value = position * current_price
                pnl = sell_value - (position * position_cost)
                cumulative_pnl += pnl

                capital += sell_value

                trades.append({
                    'date': str(current_date),
                    'action': 'sell',
                    'price': round(current_price, 2),
                    'shares': position,
                    'pnl': round(pnl, 2),
                    'cumulative_pnl': round(cumulative_pnl, 2)
                })

                position = 0
                position_cost = 0.0

            # ---- 再处理买入信号 ----
            if (signal in (1, -2)) and position == 0:
                # 全仓买入
                shares = int(capital // current_price)
                if shares > 0:
                    cost = shares * current_price
                    capital -= cost
                    position = shares
                    position_cost = current_price

                    trades.append({
                        'date': str(current_date),
                        'action': 'buy',
                        'price': round(current_price, 2),
                        'shares': shares,
                        'pnl': 0.0,
                        'cumulative_pnl': cumulative_pnl
                    })

            # 计算当前权益
            current_equity = capital + position * current_price
            equity_curve.append({
                'date': str(current_date),
                'equity': round(current_equity, 2)
            })

        # 最终平仓（如果有持仓）
        if position > 0:
            final_price = float(close_prices[-1])
            sell_value = position * final_price
            pnl = sell_value - (position * position_cost)
            cumulative_pnl += pnl

            capital += sell_value

            trades.append({
                'date': str(dates[-1]),
                'action': 'sell',
                'price': round(final_price, 2),
                'shares': position,
                'pnl': round(pnl, 2),
                'cumulative_pnl': round(cumulative_pnl, 2)
            })

            position = 0
            # 更新最后一期权益
            equity_curve[-1]['equity'] = round(capital, 2)

        # 统计交易
        sell_trades = [t for t in trades if t['action'] == 'sell']
        total_trades = len(sell_trades)
        winning_trades = len([t for t in sell_trades if t['pnl'] > 0])
        win_rate = float(winning_trades) / total_trades if total_trades > 0 else 0.0

        # 计算回测指标
        metrics = self._calculate_metrics(equity_curve)
        metrics['total_trades'] = total_trades
        metrics['win_rate'] = round(win_rate, 4)

        result = {
            'total_return': metrics['total_return'],
            'annual_return': metrics['annual_return'],
            'max_drawdown': metrics['max_drawdown'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'total_trades': total_trades,
            'win_rate': round(win_rate, 4),
            'trades': trades,
            'equity_curve': equity_curve
        }

        return result

    def _calculate_metrics(self, equity_curve):
        """
        计算回测绩效指标

        参数:
            equity_curve: list of dict (date, equity)

        返回:
            dict: total_return, annual_return, max_drawdown, sharpe_ratio, total_trades, win_rate
        """
        if len(equity_curve) < 2:
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'total_trades': 0,
                'win_rate': 0.0
            }

        equities = np.array([e['equity'] for e in equity_curve])
        initial = float(self.initial_capital)
        final = equities[-1]

        # 总收益率
        total_return = (final - initial) / initial

        # 年化收益率（假设 252 个交易日）
        days = len(equity_curve)
        annual_return = (1 + total_return) ** (252.0 / days) - 1.0

        # 最大回撤
        peak = np.maximum.accumulate(equities)
        drawdowns = (peak - equities) / peak
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        # 夏普比率（年化，无风险利率 0.03）
        daily_returns = np.diff(equities) / equities[:-1]
        rf_daily = 0.03 / 252.0
        excess_returns = daily_returns - rf_daily
        if len(excess_returns) > 0 and np.std(excess_returns) > 0:
            sharpe_ratio = float(np.mean(excess_returns) / np.std(excess_returns) * math.sqrt(252))
        else:
            sharpe_ratio = 0.0

        # 统计交易
        # 从 trades 列表中统计卖出交易来计算胜率
        # 这里我们通过 equity_curve 间接统计 — 实际胜率在 run() 中通过 trades 计算
        # 当前方法用 trades_list 传进来不方便，这里先返回 0，run 中会覆盖
        total_trades = 0
        win_rate = 0.0

        return {
            'total_return': round(total_return, 4),
            'annual_return': round(annual_return, 4),
            'max_drawdown': round(max_drawdown, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'total_trades': total_trades,
            'win_rate': win_rate
        }

    def _empty_result(self):
        """返回空结果"""
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'trades': [],
            'equity_curve': [{'date': '', 'equity': float(self.initial_capital)}]
        }


class MultiAssetBacktester:
    """
    多资产回测引擎 - 每日扫描全市场选股，买入一篮子股票，次日卖出

    核心逻辑：
    - 每个交易日扫描全市场所有 A 股
    - 对每只股票运行 OMS 筛选条件
    - 符合条件的股票等权重买入
    - 次日全部卖出
    """

    def __init__(self, scanner, stock_pool, initial_capital=100000.0,
                 oms_params=None, max_stocks=20):
        """
        参数:
            scanner: MarketScanner 实例
            stock_pool: list of dict [{code, name, market}, ...]
            initial_capital: 初始资金
            oms_params: dict，OMS 筛选参数
                {change_low, change_high, volume_ratio_min, volume_stack_ratio}
            max_stocks: 每日最多买入股票数量
        """
        self.scanner = scanner
        self.stock_pool = stock_pool
        self.initial_capital = initial_capital
        self.oms_params = oms_params or {}
        self.max_stocks = max_stocks

    def run(self, days=20):
        """
        执行全市场扫描回测

        参数:
            days: 回测最近多少个交易日

        返回:
            dict，包含回测结果
        """
        # 1. 获取全市场股票列表
        print("全市场股票总数: {} 只".format(len(self.stock_pool)))

        # 2. 确定回测日期范围
        dates = self._get_trading_dates(days)
        if not dates or len(dates) < 2:
            return self._empty_result()

        print("回测日期范围: {} -> {} ({} 个交易日)".format(
            str(dates[0])[:10], str(dates[-1])[:10], len(dates)
        ))

        # 3. 执行每日扫描→选股→买入→次日卖出的循环
        capital = float(self.initial_capital)
        position_value = {}  # code -> {shares, cost_price, name}

        trades = []
        equity_curve = []
        daily_holdings = []  # 每日持仓记录
        cumulative_pnl = 0.0

        for date_idx, date in enumerate(dates):
            date_str = str(date)[:10]
            print("\n交易日 {} ({}/{})".format(date_str, date_idx + 1, len(dates)))

            # ---- 先卖出昨日持仓 ----
            if position_value:
                sell_total = 0.0
                for code, pos in list(position_value.items()):
                    # 获取当日价格
                    price = self._get_stock_price(code, date)
                    if price is None or price <= 0:
                        # 停牌或数据缺失，按持仓成本卖出
                        price = pos['cost_price']
                        print("  警告: {} 获取不到 {} 价格，按成本价卖出".format(date_str, code))

                    sell_value = pos['shares'] * price
                    pnl = sell_value - (pos['shares'] * pos['cost_price'])
                    cumulative_pnl += pnl

                    capital += sell_value
                    sell_total += sell_value

                    trades.append({
                        'date': date_str,
                        'action': 'sell',
                        'symbol': code,
                        'name': pos['name'],
                        'price': round(price, 2),
                        'shares': pos['shares'],
                        'pnl': round(pnl, 2),
                        'cumulative_pnl': round(cumulative_pnl, 2),
                    })

                print("  卖出 {} 只股票，回收资金 {:.2f}".format(
                    len(position_value), sell_total
                ))
                position_value = {}

            # ---- 扫描选股 ----
            print("  扫描选股中...")
            candidates = self.scanner.scan(
                date, self.stock_pool,
                change_low=self.oms_params.get('change_low', 3.0),
                change_high=self.oms_params.get('change_high', 5.0),
                volume_ratio_min=self.oms_params.get('volume_ratio_min', 1.0),
                volume_stack_ratio=self.oms_params.get('volume_stack_ratio', 1.2),
            )

            # 限制买入数量
            candidates = candidates[:self.max_stocks]

            if not candidates:
                print("  无符合条件的股票，空仓")
                daily_holdings.append({
                    'date': date_str,
                    'holdings': [],
                    'count': 0,
                })
                current_equity = capital
                equity_curve.append({
                    'date': date_str,
                    'equity': round(current_equity, 2),
                })
                continue

            print("  符合条件 {} 只".format(len(candidates)))

            # ---- 买入股票（等权重分配）----
            buy_total = 0.0
            position_value = {}

            # 等权重分配：每只股票分配相同资金
            per_stock_capital = capital / len(candidates)

            for c in candidates:
                code = c['code']
                name = c['name']
                price = c['price']

                if price <= 0:
                    continue

                # 计算买入股数
                buy_amount = min(per_stock_capital, capital)
                shares = int(buy_amount // price)
                if shares <= 0:
                    continue

                cost = shares * price
                capital -= cost
                buy_total += cost

                position_value[code] = {
                    'shares': shares,
                    'cost_price': price,
                    'name': name,
                }

                trades.append({
                    'date': date_str,
                    'action': 'buy',
                    'symbol': code,
                    'name': name,
                    'price': round(price, 2),
                    'shares': shares,
                    'pnl': 0.0,
                    'cumulative_pnl': round(cumulative_pnl, 2),
                })

            print("  买入 {} 只股票，花费 {:.2f}".format(
                len(position_value), buy_total
            ))

            # 记录每日持仓
            holdings_list = [
                {'code': code, 'name': pos['name'],
                 'shares': pos['shares'],
                 'cost_price': round(pos['cost_price'], 2)}
                for code, pos in position_value.items()
            ]
            daily_holdings.append({
                'date': date_str,
                'holdings': holdings_list,
                'count': len(holdings_list),
            })

            # 计算当前权益
            current_equity = capital
            equity_curve.append({
                'date': date_str,
                'equity': round(current_equity, 2),
            })

        print("\n回测结束，最终资金: {:.2f}".format(capital))

        # 4. 计算回测指标
        return self._calculate_results(trades, equity_curve)

    def _get_stock_price(self, code, date):
        """
        获取某只股票在特定日期的收盘价
        从 scanner 的缓存中获取
        """
        df = self.scanner._get_kline_data(code, 120)
        if df is None or len(df) == 0:
            return None

        date_str = str(date)[:10]
        mask = df['date'].astype(str).str.startswith(date_str)
        if not mask.any():
            return None

        idx = mask.values.argmax()
        return float(df.iloc[idx]['close'])

    def _get_trading_dates(self, count):
        """
        获取最近 count 个交易日
        取全市场第一只股票的数据中的日期作为交易日历

        如果获取失败，使用过去的工作日作为近似
        """
        # 尝试从一个股票获取交易日信息
        test_codes = ['600519', '000001', '601318', '600036']
        for code in test_codes:
            df = self.scanner._get_kline_data(code, count + 60)
            if df is not None and len(df) >= count:
                dates = sorted(df['date'].unique())
                if len(dates) >= count:
                    return list(dates[-count:])

        # 回退：使用工作日
        print("警告: 无法获取交易日历，使用工作日近似")
        today = datetime.now()
        dates = []
        d = today
        while len(dates) < count:
            if d.weekday() < 5:  # 周一到周五
                dates.append(pd.Timestamp(d))
            d -= timedelta(days=1)
        return list(reversed(dates))[-count:]

    def _calculate_results(self, trades, equity_curve):
        """计算回测结果指标"""
        if len(equity_curve) < 2:
            return self._empty_result()

        equities = np.array([e['equity'] for e in equity_curve])
        initial = float(self.initial_capital)
        final = equities[-1]

        # 总收益率
        total_return = (final - initial) / initial

        # 年化收益率
        days = len(equity_curve)
        annual_return = (1 + total_return) ** (252.0 / max(days, 1)) - 1.0

        # 最大回撤
        peak = np.maximum.accumulate(equities)
        drawdowns = (peak - equities) / peak
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        # 夏普比率
        daily_returns = np.diff(equities) / equities[:-1]
        rf_daily = 0.03 / 252.0
        excess_returns = daily_returns - rf_daily
        if len(excess_returns) > 0 and np.std(excess_returns) > 0:
            sharpe_ratio = float(np.mean(excess_returns) / np.std(excess_returns) * math.sqrt(252))
        else:
            sharpe_ratio = 0.0

        # 交易统计
        sell_trades = [t for t in trades if t['action'] == 'sell']
        total_trades = len(sell_trades)
        winning_trades = len([t for t in sell_trades if t['pnl'] > 0])
        win_rate = float(winning_trades) / total_trades if total_trades > 0 else 0.0

        return {
            'total_return': round(total_return, 4),
            'annual_return': round(annual_return, 4),
            'max_drawdown': round(max_drawdown, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'total_trades': total_trades,
            'win_rate': round(win_rate, 4),
            'trades': trades,
            'equity_curve': equity_curve,
        }

    def _empty_result(self):
        """返回空结果"""
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'trades': [],
            'equity_curve': [{'date': '', 'equity': float(self.initial_capital)}],
        }


# 方便直接运行测试
if __name__ == '__main__':
    from data_loader import DataLoader
    from strategy_base import DualMAStrategy, RSIStrategy, MACDStrategy, BollingerStrategy, OMSStrategy
    from stock_pool import get_all_stocks
    from market_scanner import MarketScanner

    # 测试 1：原有单资产回测
    print("=" * 60)
    print("测试1: 单资产回测")
    print("=" * 60)
    loader = DataLoader()
    df = loader.generate_sample_data('TEST', 365)

    print("数据行数: {}".format(len(df)))
    print("列: {}".format(list(df.columns)))
    print()

    strategies = [
        DualMAStrategy(),
        RSIStrategy(),
        MACDStrategy(),
        BollingerStrategy()
    ]

    for strat in strategies:
        bt = Backtester(strat, df, initial_capital=100000)
        result = bt.run()
        print("=== {} ===".format(strat.name))
        print("  总收益率: {:.2%}".format(result['total_return']))
        print("  年化收益率: {:.2%}".format(result['annual_return']))
        print("  最大回撤: {:.2%}".format(result['max_drawdown']))
        print("  夏普比率: {:.4f}".format(result['sharpe_ratio']))
        print("  交易次数: {}".format(result['total_trades']))
        print("  胜率: {:.2%}".format(result['win_rate']))
        print("  交易明细: {} 条".format(len(result['trades'])))
        print("  权益曲线: {} 条".format(len(result['equity_curve'])))
        print()

    # 测试 2：全市场扫描回测（使用模拟小数据）
    print("=" * 60)
    print("测试2: 全市场扫描回测")
    print("=" * 60)

    # 用几只测试股票
    test_stocks = [
        {'code': '600519', 'name': '贵州茅台', 'market': 'sh'},
        {'code': '000001', 'name': '平安银行', 'market': 'sz'},
        {'code': '300750', 'name': '宁德时代', 'market': 'sz'},
    ]

    scanner = MarketScanner(cache_enabled=True)
    bt_multi = MultiAssetBacktester(
        scanner=scanner,
        stock_pool=test_stocks,
        initial_capital=100000.0,
        oms_params={
            'change_low': 3.0,
            'change_high': 5.0,
            'volume_ratio_min': 1.0,
            'volume_stack_ratio': 1.2,
        },
        max_stocks=5,
    )
    result = bt_multi.run(days=5)  # 只测5个交易日
    print("\n=== 全市场回测结果 ===")
    print("  总收益率: {:.2%}".format(result['total_return']))
    print("  年化收益率: {:.2%}".format(result['annual_return']))
    print("  最大回撤: {:.2%}".format(result['max_drawdown']))
    print("  夏普比率: {:.4f}".format(result['sharpe_ratio']))
    print("  交易次数: {}".format(result['total_trades']))
    print("  胜率: {:.2%}".format(result['win_rate']))
    print("  交易明细: {} 条".format(len(result['trades'])))
    for t in result['trades']:
        print("    {} {} {} {}@{:.2f} x{}".format(
            t['date'], t['action'], t.get('symbol', ''),
            t.get('name', ''), t['price'], t['shares']
        ))
