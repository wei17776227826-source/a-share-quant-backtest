# -*- coding: utf-8 -*-
"""
产业链研究引擎 - 完整版（集成数据源 + 评分 + 报告生成）

接收行业/主题 → 拆解产业链层级 → 搜索并映射 A 股公司
→ 获取真实财务数据 → 瓶颈评分 → 生成研究报告
"""

import json
from datetime import datetime

from engine.industry_chains import (
    INDUSTRY_CHAINS, get_industry_chain, get_chain_layers, get_chain_summary
)
from engine.industry_sources import IndustrySourceSearcher
from engine.industry_scorer import scorer
from engine.industry_report_generator import report_generator


# ===== 预定义的公司-层级映射 =====
# 首次运行时使用预定义映射，后续可扩展为自动搜索匹配

COMPANY_LAYER_MAP = {
    # === AI 半导体 ===
    "ai_semiconductor": {
        "memory_interconnect": [
            {"symbol": "688008.SH", "name": "澜起科技", "desc": "DDR5/MRDIMM/PCIe/CXL 互连芯片"},
            {"symbol": "688525.SH", "name": "佰维存储", "desc": "存储芯片/内存模组"},
        ],
        "cmp_thinning": [
            {"symbol": "688120.SH", "name": "华海清科", "desc": "CMP/减薄/边抛/划切设备"},
        ],
        "etching": [
            {"symbol": "688012.SH", "name": "中微公司", "desc": "高深宽比刻蚀/薄膜沉积设备"},
            {"symbol": "002371.SZ", "name": "北方华创", "desc": "刻蚀/薄膜/清洗/炉管设备"},
        ],
        "cmp_consumables": [
            {"symbol": "688019.SH", "name": "安集科技", "desc": "CMP 抛光液/湿电子化学品/电镀添加剂"},
            {"symbol": "300604.SZ", "name": "长川科技", "desc": "测试设备/分选机"},
        ],
        "advanced_packaging": [
            {"symbol": "002156.SZ", "name": "通富微电", "desc": "AI/HPC 封测/先进封装（FCBGA/Chiplet）"},
            {"symbol": "600584.SH", "name": "长电科技", "desc": "全球第三大封测代工（OSAT）"},
            {"symbol": "688362.SH", "name": "甬矽电子", "desc": "先进封装（FC/BGA/SiP）"},
        ],
        "eda_ip": [
            {"symbol": "688206.SH", "name": "概伦电子", "desc": "EDA/半导体器件建模/仿真"},
            {"symbol": "301095.SZ", "name": "广立微", "desc": "EDA/测试芯片/良率分析"},
            {"symbol": "688107.SH", "name": "芯原股份", "desc": "芯片设计 IP/设计服务"},
        ],
        "ai_compute_chip": [
            {"symbol": "688041.SH", "name": "海光信息", "desc": "x86 兼容 CPU/AI 加速处理器"},
            {"symbol": "688256.SH", "name": "寒武纪", "desc": "AI 芯片/智能计算卡"},
            {"symbol": "603893.SH", "name": "瑞芯微", "desc": "SoC/AIoT 芯片"},
        ],
        "equipment_parts": [
            {"symbol": "688200.SH", "name": "华峰测控", "desc": "半导体测试机（STS 系列）"},
            {"symbol": "300567.SZ", "name": "精测电子", "desc": "半导体/面板检测设备"},
        ],
        "substrate_pcb": [
            {"symbol": "002916.SZ", "name": "深南电路", "desc": "PCB/封装基板"},
        ],
    },
}


class IndustryResearchEngine:
    """产业链研究引擎（增强版）"""

    def __init__(self):
        self.research_results = {}
        self.searcher = IndustrySourceSearcher()

    def get_available_chains(self):
        chains = []
        for chain_id in INDUSTRY_CHAINS:
            summary = get_chain_summary(chain_id)
            if summary:
                chains.append(summary)
        return chains

    def get_chain_layers_detail(self, industry_id):
        layers = get_chain_layers(industry_id)
        chain = get_industry_chain(industry_id)
        if not chain:
            return None
        return {
            "id": industry_id,
            "name": chain["name"],
            "description": chain["description"],
            "market": chain["market"],
            "layers": layers,
            "keywords": chain["keywords"],
        }

    def research(self, industry_id, use_ai_report=True):
        """
        执行产业链研究（增强版）

        参数:
            industry_id: 产业链 ID
            use_ai_report: 是否生成 AI 研究报告

        返回:
            dict: 研究报告
        """
        chain = get_industry_chain(industry_id)
        if not chain:
            return {"error": "产业链 '{0}' 不存在".format(industry_id)}

        layers = get_chain_layers(industry_id)
        layer_companies = self._get_companies_for_layers(industry_id, layers)

        for layer in layer_companies:
            for company in layer["companies"]:
                company["layer_id"] = layer["layer_id"]
                company["layer_name"] = layer["layer_name"]

        # ===== 新：获取真实财务数据 + 证据 + 评分 =====
        company_items = []
        for layer in layer_companies:
            for company in layer["companies"]:
                try:
                    fin = self.searcher.get_financial_summary(company["symbol"], 180)
                except Exception:
                    fin = {}
                try:
                    ev = self.searcher.extract_evidence_from_price(company["symbol"], 180)
                except Exception:
                    ev = []
                score = scorer.score_company(
                    company,
                    {"layer_name": layer["layer_name"], "layer_rank": layer["layer_rank"]},
                    evidence=ev,
                    financial=fin,
                )
                company["financial"] = fin
                company["evidence"] = ev
                company["score"] = score

                company_items.append({
                    "company": company,
                    "layer_id": layer["layer_id"],
                    "layer_name": layer["layer_name"],
                    "financial": fin,
                    "evidence": ev,
                    "score": score,
                })

        # 生成报告
        report_id = "report_{0}_{1}".format(
            industry_id, datetime.now().strftime('%Y%m%d%H%M%S')
        )

        report = {
            "id": report_id,
            "industry_id": industry_id,
            "industry_name": chain["name"],
            "description": chain["description"],
            "market": chain["market"],
            "created_at": datetime.now().isoformat(),
            "layers": layer_companies,
            "summary": self._generate_summary(chain, layer_companies),
            "keywords": chain["keywords"],
            "source_hints": chain["source_hints"],
        }

        # 生成 AI 研究报告（如果启用）
        if use_ai_report:
            research_data = {
                "industry_id": industry_id,
                "total_companies": sum(l["company_count"] for l in layer_companies),
                "company_items": company_items,
            }
            try:
                ai_report = report_generator.generate(industry_id, research_data)
                report["ai_report"] = ai_report
            except Exception as e:
                report["ai_report"] = {"error": str(e)}

        self.research_results[report_id] = report
        return report

    def get_report(self, report_id):
        return self.research_results.get(report_id)

    def _get_companies_for_layers(self, industry_id, layers):
        industry_map = COMPANY_LAYER_MAP.get(industry_id, {})
        result = []
        for layer in layers:
            layer_id = layer["id"]
            companies = industry_map.get(layer_id, [])
            result.append({
                "layer_id": layer_id,
                "layer_name": layer["name"],
                "layer_rank": layer["rank"],
                "company_count": len(companies),
                "companies": companies,
            })
        return result

    def _generate_summary(self, chain, layer_companies):
        total = sum(l["company_count"] for l in layer_companies)
        names = [l["layer_name"] for l in layer_companies]
        return {
            "total_layers": len(layer_companies),
            "total_companies": total,
            "layer_chain": " -> ".join(names),
        }

    def search_company_in_industry(self, industry_id, keyword):
        chain = get_industry_chain(industry_id)
        if not chain:
            return []
        industry_map = COMPANY_LAYER_MAP.get(industry_id, {})
        results = []
        for layer_id, companies in industry_map.items():
            for company in companies:
                if (keyword.lower() in company["name"].lower() or
                    keyword.lower() in company["symbol"].lower() or
                    keyword.lower() in company["desc"].lower()):
                    layer_name = None
                    for l in chain["layers"]:
                        if l["id"] == layer_id:
                            layer_name = l["name"]
                            break
                    results.append({
                        "company": company,
                        "layer_id": layer_id,
                        "layer_name": layer_name,
                    })
        return results


engine = IndustryResearchEngine()
