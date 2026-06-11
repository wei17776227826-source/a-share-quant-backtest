# -*- coding: utf-8 -*-
"""
产业链评分器 - 基于 Serenity.skill 的瓶颈控制力评分逻辑

评分维度（0-5分）：
  - demand_inflection: 需求拐点强度
  - architecture_coupling: 架构耦合度
  - chokepoint_severity: 卡点严重程度
  - supplier_concentration: 供应商集中度
  - expansion_difficulty: 扩产难度
  - evidence_quality: 证据质量
  - valuation_disconnect: 估值偏差
  - catalyst_timing: 催化剂时机

扣分项：
  - dilution_financing, governance, geopolitics, liquidity, etc.
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


class IndustryScorer:
    """产业链评分器"""

    def score_company(self, company_info, layer_info, evidence=None):
        """
        对公司进行瓶颈控制力评分

        参数:
            company_info: dict - 公司信息（symbol, name, desc）
            layer_info: dict - 所属层级信息（layer_name, layer_rank）
            evidence: list - 证据列表

        返回:
            dict: 评分结果
        """
        factors = self._assess_factors(company_info, layer_info)
        penalties = self._assess_penalties(company_info)
        return self._calculate_score(company_info, factors, penalties, evidence or [])

    def rank_companies(self, companies_with_info):
        """
        对多个公司进行排序

        参数:
            companies_with_info: list of dict -
                [{"company": {...}, "layer": {...}, "evidence": [...]}, ...]

        返回:
            list: 排序后的公司列表（带分数）
        """
        scored = []
        for item in companies_with_info:
            result = self.score_company(
                item.get("company", {}),
                item.get("layer", {}),
                item.get("evidence", []),
            )
            scored.append(result)

        # 按最终分数降序排列
        scored.sort(key=lambda x: x["final_score"], reverse=True)

        return scored

    def _assess_factors(self, company, layer):
        """根据公司信息和层级位置评估各维度分数"""
        factors = {}
        desc = (company.get("desc", "") + " " + company.get("name", "")).lower()

        # demand_inflection: 需求拐点
        # AI/半导体相关需求旺盛
        ai_keywords = ["ai", "芯片", "半导体", "算力", "hbm", "先进封装", "cpo", "光模块"]
        score = min(5, sum(1 for kw in ai_keywords if kw in desc))
        factors["demand_inflection"] = max(1, score)

        # architecture_coupling: 架构耦合度
        # 越靠近上游设备/材料/芯片，耦合度越高
        layer_rank = layer.get("layer_rank", 5) if layer else 5
        factors["architecture_coupling"] = max(1, min(5, 6 - layer_rank // 2))

        # chokepoint_severity: 卡点严重程度
        # 描述中包含"互连""设备""耗材"等关键词表示更接近卡点
        chokepoint_kw = ["互连", "设备", "耗材", "eda", "ip", "封测", "测试"]
        score = sum(1 for kw in chokepoint_kw if kw in desc)
        factors["chokepoint_severity"] = max(1, min(5, score + 1))

        # supplier_concentration: 供应商集中度
        # 假设上游设备/材料供应商更集中
        factors["supplier_concentration"] = max(1, min(5, 4 - layer_rank // 4))

        # expansion_difficulty: 扩产难度
        # 半导体设备/材料扩产周期长
        hard_expand_kw = ["设备", "材料", "芯片", "封装", "cxl", "互连"]
        score = sum(1 for kw in hard_expand_kw if kw in desc)
        factors["expansion_difficulty"] = max(1, min(5, score + 2))

        # evidence_quality: 证据质量（默认中等，后续从真实数据改进）
        factors["evidence_quality"] = 3

        # valuation_disconnect: 估值偏差（默认中等）
        factors["valuation_disconnect"] = 3

        # catalyst_timing: 催化剂时机
        factors["catalyst_timing"] = 3

        return factors

    def _assess_penalties(self, company):
        """评估扣分项（默认无扣分，后续可基于财务数据改进）"""
        return {
            "dilution_financing": 0,
            "governance": 0,
            "geopolitics": 0,
            "liquidity": 0,
            "hype_risk": 0,
            "accounting_quality": 0,
            "cyclicality": 0,
            "alternative_design_risk": 0,
        }

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

        if final_score >= 85:
            verdict = "Top research priority"
        elif final_score >= 70:
            verdict = "High research priority"
        elif final_score >= 55:
            verdict = "Worth tracking"
        else:
            verdict = "Early lead or low priority"

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
