# -*- coding: utf-8 -*-
"""
产业链评分器 - 基于 Serenity.skill 的瓶颈控制力评分逻辑

评分维度（0-5分）：
  - demand_inflection: 需求拐点强度
  - architecture_coupling: 架构耦合度
  - chokepoint_severity: 卡点严重程度
  - supplier_concentration: 供应商集中度
  - expansion_difficulty: 扩产难度
  - evidence_quality: 证据质量（基于真实财务数据）
  - valuation_disconnect: 估值偏差（基于 PE/PB）
  - catalyst_timing: 催化剂时机（基于技术面）

扣分项（基于财务数据）：
  - dilution_financing: 融资风险
  - liquidity: 流动性风险
  - hype_risk: 炒作风险
  - cyclicality: 周期性风险
"""

# 评分权重（与 serenity_scorecard.py 一致）
WEIGHTS = {
    "demand_inflection": 15,
    "architecture_coupling": 10,
    "chokepoint_severity": 15,
    "supplier_concentration": 12,
    "expansion_difficulty": 12,
    "evidence_quality": 15,
    "valuation_disconnect": 11,
    "catalyst_timing": 10,
}

PENALTY_MULTIPLIER = 2.0

# 产业链默认基准评分（按层级排名）
LAYER_BASE_SCORES = {
    1: {"demand_inflection": 5, "architecture_coupling": 5, "chokepoint_severity": 5,
        "supplier_concentration": 5, "expansion_difficulty": 5},
    2: {"demand_inflection": 4, "architecture_coupling": 4, "chokepoint_severity": 4,
        "supplier_concentration": 4, "expansion_difficulty": 4},
    3: {"demand_inflection": 4, "architecture_coupling": 4, "chokepoint_severity": 4,
        "supplier_concentration": 3, "expansion_difficulty": 4},
    4: {"demand_inflection": 3, "architecture_coupling": 3, "chokepoint_severity": 3,
        "supplier_concentration": 3, "expansion_difficulty": 3},
    5: {"demand_inflection": 3, "architecture_coupling": 3, "chokepoint_severity": 3,
        "supplier_concentration": 3, "expansion_difficulty": 3},
}


class IndustryScorer:
    """产业链评分器"""

    def score_company(self, company_info, layer_info, evidence=None, financial=None):
        """
        对公司进行瓶颈控制力评分（加入真实财务数据）

        参数:
            company_info: dict - 公司信息（symbol, name, desc）
            layer_info: dict - 所属层级信息（layer_name, layer_rank）
            evidence: list - 证据列表
            financial: dict - 财务摘要（由 IndustrySourceSearcher 提供）

        返回:
            dict: 评分结果
        """
        factors = self._assess_factors(company_info, layer_info, financial or {})
        penalties = self._assess_penalties(financial or {})
        return self._calculate_score(company_info, factors, penalties, evidence or [])

    def rank_companies(self, companies_with_info):
        """对多个公司进行排序"""
        scored = []
        for item in companies_with_info:
            result = self.score_company(
                item.get("company", {}),
                item.get("layer", {}),
                item.get("evidence", []),
                item.get("financial", {}),
            )
            scored.append(result)
        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored

    def _assess_factors(self, company, layer, financial):
        """基于公司信息+层级位置+真实财务数据评估各维度"""
        factors = {}
        desc = (company.get("desc", "") + " " + company.get("name", "")).lower()
        layer_rank = layer.get("layer_rank", 5) if layer else 5

        # --- 基于层级位置的基准分 ---
        base = LAYER_BASE_SCORES.get(layer_rank, LAYER_BASE_SCORES.get(5))

        # demand_inflection: 需求拐点
        # 基准来自层级 + 关键词加分
        score = base["demand_inflection"]
        ai_kw = ["ai", "芯片", "半导体", "算力", "hbm", "先进封装", "cpo", "光模块", "互连"]
        score += sum(0.5 for kw in ai_kw if kw in desc)
        factors["demand_inflection"] = min(5, max(1, score))

        # architecture_coupling: 架构耦合度
        factors["architecture_coupling"] = base["architecture_coupling"]

        # chokepoint_severity: 卡点严重程度
        score = base["chokepoint_severity"]
        ch_kw = ["互连", "设备", "耗材", "eda", "ip", "封测", "测试", "减薄", "刻蚀"]
        score += sum(0.5 for kw in ch_kw if kw in desc)
        factors["chokepoint_severity"] = min(5, max(1, score))

        # supplier_concentration: 供应商集中度
        factors["supplier_concentration"] = base["supplier_concentration"]

        # expansion_difficulty: 扩产难度
        factors["expansion_difficulty"] = base["expansion_difficulty"]

        # --- 基于真实财务数据的评分 ---

        # evidence_quality: 证据质量
        # 从财务数据中提取信号
        ev_score = 1
        if financial.get("bullish_aligned"):
            ev_score += 1  # 均线多头排列 +1
        if financial.get("volume_ratio") and financial["volume_ratio"] > 1.2:
            ev_score += 1  # 放量 +1
        if financial.get("change_pct_20d") and financial["change_pct_20d"] > 5:
            ev_score += 1  # 20日涨幅 >5%
        if financial.get("pe_ttm") and financial["pe_ttm"] > 0:
            ev_score += 1  # 有PE数据
        if financial.get("market_cap") and financial["market_cap"] > 1e9:
            ev_score += 0.5  # 有市值数据
        factors["evidence_quality"] = min(5, max(1, ev_score))

        # valuation_disconnect: 估值偏差
        # 高PE = 可能有估值偏差空间（市场还未充分定价）
        pe = financial.get("pe_ttm")
        if pe and pe > 100:
            factors["valuation_disconnect"] = 4
        elif pe and pe > 50:
            factors["valuation_disconnect"] = 3
        elif pe and pe > 20:
            factors["valuation_disconnect"] = 2
        elif pe and pe > 0:
            factors["valuation_disconnect"] = 1
        else:
            factors["valuation_disconnect"] = 3  # 无数据默认中等

        # catalyst_timing: 催化剂时机
        # 从价格表现推断
        c20 = financial.get("change_pct_20d")
        vol = financial.get("volatility_20d")
        if c20 is not None:
            if -5 <= c20 <= 5 and vol and vol < 3:
                factors["catalyst_timing"] = 2  # 横盘低波动，等待催化剂
            elif c20 > 20:
                factors["catalyst_timing"] = 4  # 强势
            elif c20 > 10:
                factors["catalyst_timing"] = 3
            elif c20 < -15:
                factors["catalyst_timing"] = 4  # 超跌反弹机会
            else:
                factors["catalyst_timing"] = 2
        else:
            factors["catalyst_timing"] = 3

        return factors

    def _assess_penalties(self, financial):
        """基于财务数据评估扣分项"""
        penalties = {
            "dilution_financing": 0,
            "governance": 0,
            "geopolitics": 0,
            "liquidity": 0,
            "hype_risk": 0,
            "accounting_quality": 0,
            "cyclicality": 0,
            "alternative_design_risk": 0,
        }

        # liquidity: 大市值=高流动性，小市值=低流动性
        mc = financial.get("market_cap")
        if mc and mc < 5e9:  # 小于50亿
            penalties["liquidity"] = 3
        elif mc and mc < 2e10:  # 小于200亿
            penalties["liquidity"] = 1

        # hype_risk: PE超高 = 可能有炒作风险
        pe = financial.get("pe_ttm")
        if pe and pe > 500:
            penalties["hype_risk"] = 3
        elif pe and pe > 200:
            penalties["hype_risk"] = 1

        # volatility: 高波动=高风险
        vol = financial.get("volatility_20d")
        if vol and vol > 6:
            penalties["cyclicality"] = 2
        elif vol and vol > 4:
            penalties["cyclicality"] = 1

        # 20日跌幅大 = 可能是周期性/行业风险
        c20 = financial.get("change_pct_20d")
        if c20 and c20 < -15:
            penalties["cyclicality"] += 1

        return penalties

    def _calculate_score(self, company, factors, penalties, evidence):
        """计算最终得分"""
        factor_details = {}
        total = 0.0

        for key, weight in WEIGHTS.items():
            rating = factors.get(key, 0)
            points = rating / 5.0 * weight
            factor_details[key] = {
                "rating": rating,
                "weight": weight,
                "points": round(points, 2),
            }
            total += points

        penalty_details = {}
        penalty_total = 0.0
        for key, value in penalties.items():
            points = value * PENALTY_MULTIPLIER
            penalty_details[key] = {"rating": value, "points": round(points, 2)}
            penalty_total += points

        final_score = max(0.0, min(100.0, total - penalty_total))

        if final_score >= 80:
            verdict = "高优先研究"
        elif final_score >= 65:
            verdict = "优先研究"
        elif final_score >= 50:
            verdict = "值得跟踪"
        else:
            verdict = "线索/低优先级"

        return {
            "ticker": company.get("symbol", ""),
            "company": company.get("name", ""),
            "market": "A股",
            "raw_factor_points": round(total, 2),
            "penalty_points": round(penalty_total, 2),
            "final_score": round(final_score, 2),
            "verdict": verdict,
            "factor_details": factor_details,
            "penalty_details": penalty_details,
            "evidence": evidence,
        }


# 全局评分器实例
scorer = IndustryScorer()
