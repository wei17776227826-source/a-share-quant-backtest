# -*- coding: utf-8 -*-
"""
回测引擎 - 核心回测逻辑
"""
import pandas as pd
import numpy as np
import math


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

            # 处理买入信号（空仓时买入）
            if signal == 1 and position == 0:
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

            # 处理卖出信号（持仓时卖出）
            elif signal == -1 and position > 0:
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


# 方便直接运行测试
if __name__ == '__main__':
    from data_loader import DataLoader
    from strategy_base import DualMAStrategy, RSIStrategy, MACDStrategy, BollingerStrategy

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
