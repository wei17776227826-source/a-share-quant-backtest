# -*- coding: utf-8 -*-
"""
产业链数据源搜索器 - 从公开数据源搜索公司证据
使用现有 DataLoader 获取财务数据，后续可扩展为搜索公告、专利、招投标等
"""
import json

try:
    from engine.data_loader import DataLoader
except ImportError:
    DataLoader = None


class IndustrySourceSearcher:
    """产业链数据源搜索器"""

    def __init__(self):
        self.data_loader = None
        if DataLoader:
            try:
                self.data_loader = DataLoader(data_source="tencent")
            except Exception:
                pass

    def get_financial_summary(self, symbol, days=365):
        """获取公司财务摘要"""
        if not self.data_loader:
            return {"error": "数据加载器不可用"}

        try:
            df = self.data_loader.fetch_real_data(symbol, days)
            if df is None or len(df) == 0:
                return {"error": "未获取到数据"}

            result = {
                "symbol": symbol,
                "days": len(df),
                "start_date": str(df["date"].iloc[0])[:10] if "date" in df.columns else "",
                "end_date": str(df["date"].iloc[-1])[:10] if "date" in df.columns else "",
            }

            # 价格信息
            if "close" in df.columns:
                result["latest_close"] = float(df["close"].iloc[-1])
                result["highest"] = float(df["high"].max())
                result["lowest"] = float(df["low"].min())
                result["change_pct"] = float(
                    (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
                )

            # 均线信息
            if "MA5" in df.columns and len(df) > 5:
                result["ma5"] = float(df["MA5"].iloc[-1]) if not pd.isna(df["MA5"].iloc[-1]) else None
            if "MA20" in df.columns and len(df) > 20:
                result["ma20"] = float(df["MA20"].iloc[-1]) if not pd.isna(df["MA20"].iloc[-1]) else None
                result["ma5_above_ma20"] = (
                    result.get("ma5") and result.get("ma20") and
                    result["ma5"] > result["ma20"]
                ) if result.get("ma5") else None

            # 成交量信息
            if "volume" in df.columns:
                vol = df["volume"].values
                result["avg_volume_5"] = float(vol[-5:].mean()) if len(vol) >= 5 else None
                result["avg_volume_20"] = float(vol[-20:].mean()) if len(vol) >= 20 else None
                if result.get("avg_volume_20") and result["avg_volume_20"] > 0:
                    result["volume_ratio"] = round(
                        result.get("avg_volume_5", 0) / result["avg_volume_20"], 2
                    )

            return result

        except Exception as e:
            return {"error": str(e)}

    def search_announcements(self, symbol, keyword=None):
        """
        搜索公司公告（占位 - 后续可对接东方财富/巨潮公告 API）
        目前返回模拟结果
        """
        return {
            "symbol": symbol,
            "keyword": keyword,
            "source": "公告搜索（待对接）",
            "results": [],
            "note": "公告搜索功能待接入东方财富/巨潮公告 API",
        }

    def search_patents(self, symbol, keyword=None):
        """
        搜索公司专利（占位）
        """
        return {
            "symbol": symbol,
            "keyword": keyword,
            "source": "专利搜索（待对接）",
            "results": [],
            "note": "专利搜索功能待接入国家知识产权局 API",
        }


try:
    import pandas as pd
except ImportError:
    pd = None
