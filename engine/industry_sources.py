# -*- coding: utf-8 -*-
"""
产业链数据源搜索器 - 从公开数据源获取公司证据和财务数据

数据源：
  1. 腾讯 gtimg / Baostock — 行情数据
  2. 东方财富 — 公司概况、财务指标（阿里云可能受限，自动 fallback）
  3. 模拟数据 — 当所有数据源不可用时

证据包含：财务指标、价格趋势、公告线索、专利线索、招投标线索
"""

import json
import urllib.request
import ssl
import time
from datetime import datetime, timedelta

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

try:
    from engine.data_loader import DataLoader
except ImportError:
    DataLoader = None


# SSL 上下文（跳过证书验证）
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def _urlopen(url, timeout=10):
    """带 SSL 和 User-Agent 的 URL 请求"""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
        }
    )
    return urllib.request.urlopen(req, context=_ssl_ctx, timeout=timeout)


def safe_float(val, default=None):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def clean_symbol(symbol):
    """清理股票代码格式（去掉 .SH/.SZ 后缀）"""
    return symbol.replace(".SH", "").replace(".SZ", "")


class IndustrySourceSearcher:
    """产业链数据源搜索器"""

    def __init__(self):
        self.data_loader = None
        if DataLoader:
            for src in ["baostock", "tencent"]:
                try:
                    self.data_loader = DataLoader(data_source=src)
                    # 验证可用
                    test = self.data_loader.fetch_real_data("600519", 5)
                    if test is not None and len(test) > 0:
                        break
                except Exception:
                    self.data_loader = None

    # ============================================================
    # 1. 财务数据抓取
    # ============================================================

    def get_financial_summary(self, symbol, days=365):
        """获取公司财务摘要 — 从行情数据提取可计算指标"""
        if not self.data_loader:
            return {"error": "数据加载器不可用", "symbol": symbol}

        sym = clean_symbol(symbol)

        try:
            df = self.data_loader.fetch_real_data(sym, days)
            if df is None or len(df) == 0:
                return {"error": "未获取到数据", "symbol": symbol}

            result = {
                "symbol": symbol,
                "days": len(df),
                "start_date": str(df["date"].iloc[0])[:10] if "date" in df.columns else "",
                "end_date": str(df["date"].iloc[-1])[:10] if "date" in df.columns else "",
            }

            close = df["close"].values if "close" in df.columns else None
            volume = df["volume"].values if "volume" in df.columns else None
            high = df["high"].values if "high" in df.columns else None
            low = df["low"].values if "low" in df.columns else None

            if close is not None and len(close) > 0:
                result["latest_close"] = safe_float(close[-1])
                result["highest"] = safe_float(high.max()) if high is not None else None
                result["lowest"] = safe_float(low.min()) if low is not None else None
                latest = safe_float(close[-1])
                first = safe_float(close[0])
                if latest and first and first > 0:
                    result["change_pct_ytd"] = round((latest / first - 1) * 100, 2)

                if len(close) >= 20:
                    c20 = safe_float(close[-1])
                    c20_ago = safe_float(close[-20])
                    if c20 and c20_ago and c20_ago > 0:
                        result["change_pct_20d"] = round((c20 / c20_ago - 1) * 100, 2)
                if len(close) >= 60:
                    c60 = safe_float(close[-1])
                    c60_ago = safe_float(close[-60])
                    if c60 and c60_ago and c60_ago > 0:
                        result["change_pct_60d"] = round((c60 / c60_ago - 1) * 100, 2)

                if high is not None and low is not None and np is not None:
                    avg_amp = np.mean((high - low) / close * 100)
                    result["avg_amplitude_pct"] = round(float(avg_amp), 2)

            # 均线
            for rk, col in [("ma5","MA5"),("ma10","MA10"),("ma20","MA20"),("ma60","MA60")]:
                if col in df.columns and len(df) > 0:
                    val = df[col].iloc[-1]
                    result[rk] = safe_float(val)

            # 多头排列
            if all(result.get(k) for k in ["ma5","ma10","ma20","ma60"]):
                result["bullish_aligned"] = (
                    result["ma5"] > result["ma10"] > result["ma20"] > result["ma60"]
                )

            # 量比
            if volume is not None and len(volume) >= 20 and np is not None:
                vol_5 = float(np.mean(volume[-5:]))
                vol_20 = float(np.mean(volume[-20:]))
                result["avg_volume_5"] = vol_5
                result["avg_volume_20"] = vol_20
                if vol_20 > 0:
                    result["volume_ratio"] = round(vol_5 / vol_20, 2)

            # 波动率
            if close is not None and len(close) >= 21 and np is not None:
                rets = np.diff(close[-21:]) / close[-21:-1]
                result["volatility_20d"] = round(float(np.std(rets) * 100), 2)

            # 补充东方财富概况（如果可用）
            profile = self._fetch_company_profile(sym)
            if profile:
                result.update(profile)

            return result

        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    def _fetch_company_profile(self, symbol):
        """从东方财富获取公司概况"""
        try:
            secid = self._get_secid(symbol)
            if not secid:
                return None
            url = ("https://push2.eastmoney.com/api/qt/stock/get"
                   "?secid={0}&fields=f57,f58,f84,f85,f100,f116,f117,f162,f167").format(secid)
            resp = _urlopen(url, timeout=5)
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("data"):
                d = data["data"]
                return {
                    "market_cap": safe_float(d.get("f116")),
                    "pe_ttm": safe_float(d.get("f162")),
                    "pb": safe_float(d.get("f167")),
                    "industry": d.get("f57", ""),
                }
        except Exception:
            pass
        return None

    def _get_secid(self, symbol):
        sym = clean_symbol(symbol)
        if sym.startswith("6"):
            return "1.{}".format(sym)
        elif sym.startswith(("0", "3")):
            return "0.{}".format(sym)
        return None

    # ============================================================
    # 2. 公告搜索
    # ============================================================

    def search_announcements(self, symbol, keyword=None, limit=10):
        """从东方财富搜索公司公告"""
        results = []
        try:
            secid = self._get_secid(symbol)
            if not secid:
                return self._fallback_ann(symbol, keyword)
            url = ("https://np-anotice-stock.eastmoney.com/api/security/ann/"
                   "?sr=-1&page_size={0}&page_index=1&ann_type=A"
                   "&stock_list={1}&f_node=1&s_node=0").format(limit, secid)
            resp = _urlopen(url, timeout=8)
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("data") and data["data"].get("list"):
                for item in data["data"]["list"][:limit]:
                    title = item.get("title", "")
                    if keyword and keyword.lower() not in title.lower():
                        continue
                    results.append({
                        "title": title,
                        "date": str(item.get("notice_date", ""))[:10],
                        "type": "公告",
                    })
        except Exception:
            return self._fallback_ann(symbol, keyword)
        return {"symbol": symbol, "keyword": keyword, "source": "东方财富公告",
                "results": results, "total": len(results)}

    def _fallback_ann(self, symbol, keyword=None):
        return {"symbol": symbol, "keyword": keyword, "source": "公告搜索",
                "results": [], "total": 0,
                "note": "东方财富公告 API 当前不可用，建议访问巨潮资讯网 www.cninfo.com.cn"}

    # ============================================================
    # 3. 价格证据提取
    # ============================================================

    def extract_evidence_from_price(self, symbol, days=365):
        """从价格数据中提取投资证据信号"""
        evidences = []
        fin = self.get_financial_summary(symbol, days)
        if "error" in fin:
            return evidences

        if fin.get("bullish_aligned"):
            evidences.append({"claim": "均线多头排列（MA5>MA10>MA20>MA60），中期趋势向上",
                              "source": "行情数据", "strength": "strong"})

        vr = fin.get("volume_ratio")
        if vr:
            if vr > 1.5:
                evidences.append({"claim": "近5日成交量是20日均量的{0}倍，放量明显".format(vr),
                                  "source": "行情数据", "strength": "medium"})
            elif vr < 0.6:
                evidences.append({"claim": "近5日成交量仅20日均量的{0}倍，缩量整理".format(vr),
                                  "source": "行情数据", "strength": "medium"})

        c20 = fin.get("change_pct_20d")
        if c20 is not None:
            if c20 > 10:
                evidences.append({"claim": "近20日涨幅 {0}%，短线走强".format(c20),
                                  "source": "行情数据", "strength": "medium"})
            elif c20 < -10:
                evidences.append({"claim": "近20日跌幅 {0}%，短线承压".format(c20),
                                  "source": "行情数据", "strength": "medium"})

        vol = fin.get("volatility_20d")
        if vol and vol > 5:
            evidences.append({"claim": "20日波动率 {0}%，高波动标的".format(vol),
                              "source": "行情数据", "strength": "weak"})

        return evidences

    # ============================================================
    # 4-5. 占位搜索
    # ============================================================

    def search_patents(self, symbol, keyword=None):
        return {"symbol": symbol, "keyword": keyword, "source": "国家知识产权局",
                "results": [], "total": 0,
                "note": "专利搜索待接入，建议访问 https://pss-system.cponline.cnipa.gov.cn"}

    def search_bidding(self, symbol, keyword=None):
        return {"symbol": symbol, "keyword": keyword, "source": "中国招标投标公共服务平台",
                "results": [], "total": 0,
                "note": "招投标搜索待接入，建议访问 http://www.cebpubservice.com"}

    # ============================================================
    # 6. 综合证据收集
    # ============================================================

    def collect_all_evidence(self, symbol, days=365):
        """综合收集所有证据"""
        financial = self.get_financial_summary(symbol, days)
        price_evidence = self.extract_evidence_from_price(symbol, days)
        announcements = self.search_announcements(symbol, limit=5)
        return {
            "symbol": symbol,
            "financial": financial,
            "price_evidence": price_evidence,
            "announcements": announcements,
            "evidence_count": len(price_evidence),
        }


if pd is None:
    import sys
    sys.stderr.write("警告: pandas 未安装\n")
if np is None:
    import sys
    sys.stderr.write("警告: numpy 未安装\n")
