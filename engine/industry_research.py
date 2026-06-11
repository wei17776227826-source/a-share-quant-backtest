# -*- coding: utf-8 -*-
"""
产业链研究引擎 - 基于 Serenity.skill 方法论

接收行业/主题 → 拆解产业链层级 → 搜索并映射 A 股公司 → 评分排序 → 生成报告
"""

import json
from datetime import datetime

from engine.industry_chains import (
    INDUSTRY_CHAINS, get_industry_chain, get_chain_layers, get_chain_summary
)


# 预定义的公司 - 按层级映射（A 股 AI 半导体示例）
# 实际运行时可通过搜索扩展
COMPANY_LAYER_MAP = {
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
    }
}


class IndustryResearchEngine:
    """产业链研究引擎"""

    def __init__(self):
        self.research_results = {}  # 内存缓存研究报告

    def get_available_chains(self):
        """获取所有可用的产业链摘要"""
        chains = []
        for chain_id in INDUSTRY_CHAINS:
            summary = get_chain_summary(chain_id)
            if summary:
                chains.append(summary)
        return chains

    def get_chain_layers_detail(self, industry_id):
        """获取产业链层级详情"""
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

    def research(self, industry_id):
        """
        执行产业链研究

        参数:
            industry_id: 产业链 ID

        返回:
            dict: 研究报告
        """
        chain = get_industry_chain(industry_id)
        if not chain:
            return {"error": "产业链 '{0}' 不存在".format(industry_id)}

        # 1. 获取产业链层级
        layers = get_chain_layers(industry_id)

        # 2. 获取各层级的公司映射
        layer_companies = self._get_companies_for_layers(industry_id, layers)

        # 3. 为每家公司构建简介信息
        for layer in layer_companies:
            for company in layer["companies"]:
                company["layer_id"] = layer["layer_id"]
                company["layer_name"] = layer["layer_name"]

        # 4. 生成研究报告
        report = {
            "id": "report_{0}_{1}".format(
                industry_id, datetime.now().strftime('%Y%m%d%H%M%S')
            ),
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

        # 缓存报告
        self.research_results[report["id"]] = report

        return report

    def get_report(self, report_id):
        """获取已生成的研究报告"""
        return self.research_results.get(report_id)

    def _get_companies_for_layers(self, industry_id, layers):
        """获取各层级对应的公司列表"""
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
        """生成研究报告摘要"""
        total_companies = sum(l["company_count"] for l in layer_companies)
        layer_names = [l["layer_name"] for l in layer_companies]

        return {
            "total_layers": len(layer_companies),
            "total_companies": total_companies,
            "layer_chain": " -> ".join(layer_names),
        }

    def search_company_in_industry(self, industry_id, keyword):
        """在产业链中搜索公司"""
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


# 全局研究引擎实例
engine = IndustryResearchEngine()
