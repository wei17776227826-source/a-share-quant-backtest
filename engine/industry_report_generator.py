# -*- coding: utf-8 -*-
"""
AI 研究报告生成器 - 基于收集到的真实数据生成 Serenity 风格研究报告

根据财务数据、价格证据、公告信息等自动生成：
  1. 产业链全景分析
  2. 各层级瓶颈判断
  3. 公司竞争力评估
  4. 风险与机会提示
  5. 下一步研究方向
"""

from datetime import datetime
from engine.industry_chains import get_industry_chain, get_chain_layers


class ReportGenerator:
    """研究报告生成器"""

    def generate(self, industry_id, research_data):
        """
        生成完整的产业链研究报告

        参数:
            industry_id: 产业链 ID
            research_data: dict - 研究数据，包含 layers（各层级公司）、
                          financials（财务数据）、scores（评分）等

        返回:
            dict: 包含 markdown 格式报告的完整数据
        """
        chain = get_industry_chain(industry_id)
        if not chain:
            return {"error": "产业链不存在"}

        # 生成各层级分析
        layer_analyses = self._analyze_layers(chain, research_data, industry_id)

        # 生成瓶颈判断
        bottleneck_analysis = self._analyze_bottlenecks(layer_analyses)

        # 生成公司排名
        company_rankings = self._rank_companies(research_data)

        # 生成风险提示
        risks = self._analyze_risks(research_data)

        # 生成下一步方向
        next_steps = self._suggest_next_steps(bottleneck_analysis, company_rankings)

        # 组装完整报告
        report = {
            "title": "{0} 产业链深度研究报告".format(chain["name"]),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "market": chain["market"],
            "industry_name": chain["name"],
            "summary": self._generate_summary(chain, bottleneck_analysis, company_rankings),
            "chain_overview": {
                "description": chain["description"],
                "layer_count": len(chain["layers"]),
                "total_companies": research_data.get("total_companies", 0),
                "layer_chain": " → ".join([l["name"] for l in get_chain_layers(industry_id)]),
            },
            "bottleneck_analysis": bottleneck_analysis,
            "layer_analyses": layer_analyses,
            "company_rankings": company_rankings,
            "risks": risks,
            "next_steps": next_steps,
            "keywords": chain.get("keywords", []),
            "source_hints": chain.get("source_hints", []),
        }

        # 生成 markdown 文本
        report["markdown"] = self._render_markdown(report)

        return report

    def _analyze_layers(self, chain, research_data, industry_id):
        """逐层分析"""
        analyses = []
        layers = get_chain_layers(industry_id)

        for layer in layers:
            # 找出该层级的公司
            layer_companies = []
            for item in research_data.get("company_items", []):
                if item.get("layer_id") == layer["id"]:
                    layer_companies.append(item)

            # 分析该层级
            analysis = {
                "layer_id": layer["id"],
                "layer_name": layer["name"],
                "rank": layer["rank"],
                "company_count": len(layer_companies),
                "companies": [],
            }

            for item in layer_companies:
                company = item.get("company", {})
                financial = item.get("financial", {})
                score = item.get("score", {})
                evidence = item.get("evidence", [])

                company_analysis = {
                    "name": company.get("name", ""),
                    "symbol": company.get("symbol", ""),
                    "description": company.get("desc", ""),
                    "score": score.get("final_score", 0),
                    "verdict": score.get("verdict", ""),
                    "financial_signals": self._extract_financial_signals(financial),
                    "key_evidence": [e.get("claim", "") for e in evidence[:3]],
                    "strength_text": self._generate_company_strength(company, financial, score),
                }
                analysis["companies"].append(company_analysis)

            # 生成该层级的总评
            analysis["assessment"] = self._generate_layer_assessment(
                layer, analysis["companies"]
            )

            analyses.append(analysis)

        return analyses

    def _extract_financial_signals(self, financial):
        """提取财务信号摘要"""
        signals = []
        if financial.get("bullish_aligned"):
            signals.append("均线多头排列")
        vr = financial.get("volume_ratio")
        if vr:
            if vr > 1.5:
                signals.append("放量{0}倍".format(vr))
            elif vr < 0.6:
                signals.append("缩量至{0}".format(vr))
        c20 = financial.get("change_pct_20d")
        if c20 is not None:
            if c20 > 10:
                signals.append("20日涨{0}%".format(c20))
            elif c20 < -10:
                signals.append("20日跌{0}%".format(abs(c20)))
        pe = financial.get("pe_ttm")
        if pe and pe > 0:
            signals.append("PE={0}".format(round(pe)))
        return signals

    def _generate_company_strength(self, company, financial, score):
        """生成单家公司分析文本"""
        parts = []
        name = company.get("name", "")
        desc = company.get("desc", "")
        verdict = score.get("verdict", "")

        parts.append("{0}（{1}）".format(name, desc))

        if financial.get("bullish_aligned"):
            parts.append("技术上处于多头趋势")
        else:
            parts.append("技术面处于调整状态")

        c20 = financial.get("change_pct_20d")
        if c20 is not None:
            parts.append("近20日{0}{1}%".format(
                "涨" if c20 > 0 else "跌", abs(round(c20, 1))
            ))

        score_val = score.get("final_score", 0)
        parts.append("综合评分 {0}/100 — {1}".format(score_val, verdict))

        return "，".join(parts)

    def _generate_layer_assessment(self, layer, companies):
        """生成层级总评"""
        if not companies:
            return "此层级暂无映射公司，属于待扩展区域"

        # 判断层级是否关键
        rank = layer["rank"]
        avg_score = sum(c.get("score", 0) for c in companies) / len(companies)

        if rank <= 3:
            base = "上游核心层级"
        elif rank <= 6:
            base = "中游关键层级"
        else:
            base = "下游配套层级"

        return "{0}，覆盖 {1} 家公司，平均评分 {2}/100".format(
            base, len(companies), round(avg_score, 1)
        )

    def _analyze_bottlenecks(self, layer_analyses):
        """分析全产业链的瓶颈点"""
        bottlenecks = []

        for layer in layer_analyses:
            if not layer["companies"]:
                continue

            # 排名越靠前的层级越可能是瓶颈
            rank = layer["rank"]
            company_count = layer["company_count"]

            # 公司越少 + 层级越靠前 = 瓶颈越严重
            if rank <= 3 and company_count <= 2:
                bottlenecks.append({
                    "layer_id": layer["layer_id"],
                    "layer_name": layer["layer_name"],
                    "severity": "高",
                    "reason": "上游层级，可投资标的仅{0}家，供给稀缺".format(company_count),
                    "companies": [c["name"] for c in layer["companies"]],
                })
            elif rank <= 5 and company_count <= 3:
                bottlenecks.append({
                    "layer_id": layer["layer_id"],
                    "layer_name": layer["layer_name"],
                    "severity": "中",
                    "reason": "中游关键层，标的数量有限（{0}家）".format(company_count),
                    "companies": [c["name"] for c in layer["companies"]],
                })
            elif rank <= 7 and company_count <= 5:
                bottlenecks.append({
                    "layer_id": layer["layer_id"],
                    "layer_name": layer["layer_name"],
                    "severity": "低",
                    "reason": "有一定关注价值，{0}家公司可供筛选".format(company_count),
                    "companies": [c["name"] for c in layer["companies"]],
                })

        return bottlenecks

    def _rank_companies(self, research_data):
        """对所有公司进行跨层级排序"""
        all_companies = []
        for item in research_data.get("company_items", []):
            score = item.get("score", {})
            company = item.get("company", {})
            all_companies.append({
                "name": company.get("name", ""),
                "symbol": company.get("symbol", ""),
                "layer_name": item.get("layer_name", ""),
                "score": score.get("final_score", 0),
                "verdict": score.get("verdict", ""),
                "financial_signals": self._extract_financial_signals(
                    item.get("financial", {})
                ),
            })

        all_companies.sort(key=lambda x: x["score"], reverse=True)
        return all_companies

    def _analyze_risks(self, research_data):
        """分析风险点"""
        risks = {
            "market_risk": [],
            "company_risk": [],
            "technical_risk": [],
        }

        for item in research_data.get("company_items", []):
            financial = item.get("financial", {})
            company = item.get("company", {})

            pe = financial.get("pe_ttm")
            if pe and pe > 200:
                risks["company_risk"].append(
                    "{0} PE 高达 {1}，估值压力大".format(company.get("name", ""), round(pe))
                )
            c20 = financial.get("change_pct_20d")
            if c20 and c20 < -15:
                risks["market_risk"].append(
                    "{0} 近20日跌幅 {1}%，短期承压".format(
                        company.get("name", ""), abs(round(c20, 1))
                    )
                )
        return risks

    def _suggest_next_steps(self, bottlenecks, rankings):
        """建议下一步研究方向"""
        steps = []

        if bottlenecks:
            top = bottlenecks[0]
            steps.append("优先研究 {0} 层：{1}".format(
                top["layer_name"], top["reason"]
            ))

        if rankings:
            top3 = rankings[:3]
            names = "、".join([r["name"] for r in top3])
            steps.append("重点跟踪标的：{0}".format(names))

        steps.extend([
            "查看公司最新财报/公告，验证收入结构和客户认证",
            "关注产业链上下游的产能扩张计划和订单情况",
            "持续跟踪行业政策变化和技术路线演进",
        ])

        return steps

    def _generate_summary(self, chain, bottlenecks, rankings):
        """生成报告摘要"""
        lines = []
        lines.append("{0} 产业链共 {1} 个层级".format(
            chain["name"], len(chain["layers"])
        ))

        if bottlenecks:
            high = [b for b in bottlenecks if b["severity"] == "高"]
            if high:
                lines.append("核心瓶颈：{0}".format(
                    "、".join([h["layer_name"] for h in high])
                ))

        if rankings:
            top = rankings[0]
            lines.append("优先研究标的：{0}（评分 {1}）".format(
                top["name"], top["score"]
            ))

        return "；".join(lines)

    def _render_markdown(self, report):
        """将报告渲染为 Markdown 格式"""
        lines = [
            "# {0}".format(report["title"]),
            "",
            "> 生成时间：{0} ｜ 市场：{1}".format(
                report["generated_at"], report["market"]
            ),
            "",
            "---",
            "",
            "## 摘要",
            "",
            report["summary"],
            "",
            "---",
            "",
            "## 产业链全景",
            "",
            report["chain_overview"]["description"],
            "",
            "产业链层链：`{0}`".format(report["chain_overview"]["layer_chain"]),
            "",
            "共 {0} 个层级，{1} 家上市公司已映射。".format(
                report["chain_overview"]["layer_count"],
                report["chain_overview"]["total_companies"],
            ),
            "",
            "---",
            "",
            "## 瓶颈分析",
            "",
        ]

        if report["bottleneck_analysis"]:
            for b in report["bottleneck_analysis"]:
                lines.extend([
                    "### [{0}] {1}".format(b["severity"], b["layer_name"]),
                    "",
                    b["reason"],
                    "",
                    "相关公司：{0}".format("、".join(b["companies"])),
                    "",
                ])
        else:
            lines.extend(["当前未识别出明显瓶颈点。", ""])

        lines.extend([
            "---",
            "",
            "## 层级分析",
            "",
        ])

        for layer in report["layer_analyses"]:
            lines.extend([
                "### {0}（#{1}）".format(layer["layer_name"], layer["rank"]),
                "",
                layer["assessment"],
                "",
            ])
            for c in layer["companies"]:
                lines.extend([
                    "**{0}**（{1}）".format(c["name"], c["symbol"]),
                    "",
                    "- {0}".format(c["strength_text"]),
                ])
                if c["financial_signals"]:
                    lines.append("- 信号：{0}".format("、".join(c["financial_signals"])))
                if c["key_evidence"]:
                    for ev in c["key_evidence"][:2]:
                        lines.append("- {0}".format(ev))
                lines.append("")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 公司排序",
            "",
            "| 排名 | 标的 | 层级 | 评分 | 判定 | 信号 |",
            "|---|---|---|---|---|---|",
        ])

        for idx, c in enumerate(report["company_rankings"][:10], 1):
            sig_str = "、".join(c["financial_signals"][:3]) if c["financial_signals"] else "-"
            lines.append("| {0} | {1} | {2} | {3} | {4} | {5} |".format(
                idx, c["name"], c["layer_name"],
                c["score"], c["verdict"], sig_str
            ))

        lines.extend([
            "",
            "---",
            "",
            "## 风险提示",
            "",
        ])

        if report["risks"]["market_risk"] or report["risks"]["company_risk"]:
            if report["risks"]["market_risk"]:
                lines.extend(["**市场风险**", ""])
                for r in report["risks"]["market_risk"]:
                    lines.append("- {0}".format(r))
                lines.append("")
            if report["risks"]["company_risk"]:
                lines.extend(["**公司风险**", ""])
                for r in report["risks"]["company_risk"]:
                    lines.append("- {0}".format(r))
                lines.append("")
        else:
            lines.extend(["_暂无显著风险信号_", ""])

        lines.extend([
            "---",
            "",
            "## 下一步研究",
            "",
        ])
        for idx, step in enumerate(report["next_steps"], 1):
            lines.append("{0}. {1}".format(idx, step))

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**关键词：** {0}".format(
            "、".join(report.get("keywords", []))
        ))
        lines.append("")
        lines.append("**建议数据源：** {0}".format(
            "、".join(report.get("source_hints", []))
        ))

        return "\n".join(lines)


# 全局实例
report_generator = ReportGenerator()
