# -*- coding: utf-8 -*-
"""
产业链模板定义 - 基于 Serenity.skill 方法论

每个产业链包含：
  - name: 产业链中文名称
  - layers: 产业链层级（按供需关系从上游到下游排列）
  - keywords: 搜索关键词（用于公司映射）
  - source_hints: 数据源提示
  - description: 产业链描述
"""

INDUSTRY_CHAINS = {
    "ai_semiconductor": {
        "name": "AI 半导体",
        "description": "AI 芯片设计、制造、封装、测试、材料、设备的完整产业链",
        "market": "A股",
        "layers": [
            {"id": "memory_interconnect", "name": "内存互连芯片", "rank": 1},
            {"id": "cmp_thinning", "name": "CMP/减薄设备", "rank": 2},
            {"id": "etching", "name": "关键刻蚀设备", "rank": 3},
            {"id": "cmp_consumables", "name": "CMP/电镀耗材", "rank": 4},
            {"id": "advanced_packaging", "name": "先进封测", "rank": 5},
            {"id": "eda_ip", "name": "EDA/IP", "rank": 6},
            {"id": "ai_compute_chip", "name": "AI 算力芯片", "rank": 7},
            {"id": "optical_comm", "name": "光通信模块/材料", "rank": 8},
            {"id": "equipment_parts", "name": "设备零部件", "rank": 9},
            {"id": "substrate_pcb", "name": "基板/PCB/CCL", "rank": 10},
        ],
        "keywords": [
            "AI芯片", "半导体", "算力", "HBM", "先进封装", "CMP", "刻蚀",
            "光模块", "EDA", "IP授权", "硅片", "光刻", "封测"
        ],
        "source_hints": ["年报", "季报", "招投标", "专利", "互动易", "交易所问询函"],
    },
    "advanced_packaging": {
        "name": "先进封装",
        "description": "Chiplet、2.5D/3D 封装、HBM 封装、FOWLP 等先进封装产业链",
        "market": "A股",
        "layers": [
            {"id": "packaging_equipment", "name": "封装设备", "rank": 1},
            {"id": "packaging_materials", "name": "封装材料", "rank": 2},
            {"id": "osat", "name": "封测代工(OSAT)", "rank": 3},
            {"id": "substrate", "name": "封装基板", "rank": 4},
            {"id": "testing", "name": "测试服务", "rank": 5},
        ],
        "keywords": [
            "先进封装", "Chiplet", "2.5D封装", "3D封装", "HBM封装",
            "FOWLP", "FCBGA", "bumping", "TSV", "硅通孔"
        ],
        "source_hints": ["年报", "季报", "招投标", "公告", "客户认证"],
    },
    "cpo": {
        "name": "CPO/光通信",
        "description": "共封装光学(CPO)、光模块、光芯片、光纤光缆产业链",
        "market": "A股",
        "layers": [
            {"id": "optical_chip", "name": "光芯片/电芯片", "rank": 1},
            {"id": "cpo_module", "name": "CPO 模块封装", "rank": 2},
            {"id": "optical_module", "name": "光模块", "rank": 3},
            {"id": "optical_fiber", "name": "光纤光缆", "rank": 4},
            {"id": "optical_device", "name": "光无源器件", "rank": 5},
        ],
        "keywords": [
            "CPO", "共封装光学", "光模块", "光芯片", "硅光", "SiPho",
            "800G", "1.6T", "相干光", "EML", "VCSEL"
        ],
        "source_hints": ["年报", "季报", "招投标", "公告", "客户认证"],
    },
    "robotics": {
        "name": "人形机器人",
        "description": "人形机器人核心零部件、整机、系统集成产业链",
        "market": "A股",
        "layers": [
            {"id": "reducer", "name": "精密减速器", "rank": 1},
            {"id": "motor_drive", "name": "电机/驱动", "rank": 2},
            {"id": "sensor", "name": "传感器", "rank": 3},
            {"id": "controller", "name": "控制器/芯片", "rank": 4},
            {"id": "battery", "name": "电池/电源", "rank": 5},
            {"id": "body_integration", "name": "整机集成", "rank": 6},
        ],
        "keywords": [
            "人形机器人", "机器人", "减速器", "伺服电机", "力矩传感器",
            "灵巧手", "滚柱丝杠", "空心杯电机"
        ],
        "source_hints": ["年报", "季报", "公告", "客户认证", "招投标"],
    },
    "power_equipment": {
        "name": "电力设备（AI 算力电源）",
        "description": "AI 数据中心电源、变压器、开关设备、冷却系统产业链",
        "market": "A股",
        "layers": [
            {"id": "power_chip", "name": "功率芯片/器件", "rank": 1},
            {"id": "transformer", "name": "变压器/电感", "rank": 2},
            {"id": "switchgear", "name": "开关设备", "rank": 3},
            {"id": "cooling", "name": "液冷/散热", "rank": 4},
            {"id": "ups", "name": "UPS/备用电源", "rank": 5},
            {"id": "cable", "name": "电力电缆", "rank": 6},
        ],
        "keywords": [
            "数据中心电源", "AI电源", "变压器", "液冷", "散热",
            "IGBT", "SiC", "UPS", "HVDC", "服务器电源"
        ],
        "source_hints": ["年报", "季报", "招投标", "公告", "环评/能评"],
    },
    "defense_electronics": {
        "name": "军工电子",
        "description": "国防信息化、军用电子元器件、雷达/通信/导航产业链",
        "market": "A股",
        "layers": [
            {"id": "military_chip", "name": "军用芯片/FPGA", "rank": 1},
            {"id": "radar", "name": "雷达/电子对抗", "rank": 2},
            {"id": "comm_nav", "name": "军用通信/导航", "rank": 3},
            {"id": "connector", "name": "军用连接器", "rank": 4},
            {"id": "components", "name": "军用被动元器件", "rank": 5},
        ],
        "keywords": [
            "军工电子", "国防信息化", "雷达", "军用芯片", "FPGA",
            "连接器", "电子对抗", "军用通信"
        ],
        "source_hints": ["年报", "季报", "公告", "招投标", "专利"],
    },
    "biotech_manufacturing": {
        "name": "生物制造",
        "description": "合成生物学、生物发酵、酶催化、生物基材料产业链",
        "market": "A股",
        "layers": [
            {"id": "synthetic_bio", "name": "合成生物学平台", "rank": 1},
            {"id": "fermentation", "name": "生物发酵", "rank": 2},
            {"id": "enzyme", "name": "酶/催化剂", "rank": 3},
            {"id": "bio_material", "name": "生物基材料", "rank": 4},
            {"id": "biomedical", "name": "生物医药中间体", "rank": 5},
        ],
        "keywords": [
            "合成生物学", "生物制造", "生物发酵", "酶催化", "生物基",
            "PHA", "PLA", "氨基酸", "胶原蛋白"
        ],
        "source_hints": ["年报", "季报", "公告", "专利", "环评/能评"],
    },
}


def get_all_industry_ids():
    """获取所有产业链 ID"""
    return list(INDUSTRY_CHAINS.keys())


def get_industry_chain(industry_id):
    """获取产业链模板"""
    return INDUSTRY_CHAINS.get(industry_id)


def get_chain_layers(industry_id):
    """获取产业链的层级列表"""
    chain = get_industry_chain(industry_id)
    if not chain:
        return []
    return sorted(chain["layers"], key=lambda x: x["rank"])


def get_chain_summary(industry_id):
    """获取产业链摘要信息"""
    chain = get_industry_chain(industry_id)
    if not chain:
        return None
    return {
        "id": industry_id,
        "name": chain["name"],
        "description": chain["description"],
        "market": chain["market"],
        "layer_count": len(chain["layers"]),
        "keywords": chain["keywords"],
    }
