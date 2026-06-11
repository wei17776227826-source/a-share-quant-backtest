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
    # ===== 原有模板（保持兼容） =====
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

    # ===== 新增模板 =====
    "hbm_memory": {
        "name": "HBM/存储芯片",
        "description": "HBM 高带宽存储、DRAM/NAND 闪存、存算一体芯片产业链",
        "market": "A股",
        "layers": [
            {"id": "hbm_chip", "name": "HBM/DRAM 设计", "rank": 1},
            {"id": "hbm_packaging", "name": "HBM 封装/TSV", "rank": 2},
            {"id": "hbm_material", "name": "HBM 材料（EMC/Underfill）", "rank": 3},
            {"id": "hbm_test", "name": "HBM 测试/老化", "rank": 4},
            {"id": "nand_flash", "name": "NAND/闪存", "rank": 5},
        ],
        "keywords": [
            "HBM", "高带宽存储", "DRAM", "NAND", "存算一体", "TSV",
            "内存接口", "MRDIMM", "CXL", "DDR5"
        ],
        "source_hints": ["年报", "季报", "公告", "客户认证", "专利"],
    },
    "liquid_cooling": {
        "name": "液冷/散热",
        "description": "AI 数据中心液冷散热、服务器散热、热管理产业链",
        "market": "A股",
        "layers": [
            {"id": "coolant", "name": "冷却液/冷媒", "rank": 1},
            {"id": "cold_plate", "name": "冷板/换热器", "rank": 2},
            {"id": "cooling_module", "name": "液冷整机/模块", "rank": 3},
            {"id": "cooling_pump", "name": "泵/阀/管路", "rank": 4},
            {"id": "cooling_control", "name": "温控系统/传感器", "rank": 5},
        ],
        "keywords": [
            "液冷", "散热", "热管理", "冷板", "浸没式液冷", "CDU",
            "服务器散热", "AI散热", "相变冷却"
        ],
        "source_hints": ["年报", "季报", "公告", "招投标", "客户认证"],
    },
    "low_altitude_economy": {
        "name": "低空经济",
        "description": "eVTOL、无人机、低空管控、空天信息产业链",
        "market": "A股",
        "layers": [
            {"id": "evtol", "name": "eVTOL/飞行器整机", "rank": 1},
            {"id": "uav", "name": "无人机/机载系统", "rank": 2},
            {"id": "low_alt_control", "name": "低空管控/通信", "rank": 3},
            {"id": "low_alt_motor", "name": "航空电机/电驱", "rank": 4},
            {"id": "low_alt_battery", "name": "航空电池/能源", "rank": 5},
            {"id": "low_alt_material", "name": "航空复合材料", "rank": 6},
        ],
        "keywords": [
            "低空经济", "eVTOL", "飞行汽车", "无人机", "低空管控",
            "空域管理", "航空电机", "碳纤维"
        ],
        "source_hints": ["年报", "季报", "公告", "招投标", "政策文件"],
    },
    "new_energy_vehicle": {
        "name": "新能源汽车",
        "description": "新能源整车、三电系统（电池/电机/电控）、智能驾驶产业链",
        "market": "A股",
        "layers": [
            {"id": "battery_cell", "name": "动力电池/电芯", "rank": 1},
            {"id": "battery_material", "name": "电池材料（正极/负极/电解液/隔膜）", "rank": 2},
            {"id": "motor", "name": "驱动电机/电控", "rank": 3},
            {"id": "adas", "name": "智能驾驶/座舱芯片", "rank": 4},
            {"id": "chassis", "name": "底盘/线控制动", "rank": 5},
            {"id": "thermal", "name": "热管理系统", "rank": 6},
            {"id": "body_parts", "name": "车身/一体化压铸", "rank": 7},
        ],
        "keywords": [
            "新能源汽车", "锂电池", "固态电池", "智能驾驶", "自动驾驶",
            "800V", "碳化硅", "一体化压铸", "热管理"
        ],
        "source_hints": ["年报", "季报", "公告", "招投标", "客户认证"],
    },
    "quantum_computing": {
        "name": "量子计算",
        "description": "量子芯片、量子测控、量子软件、量子通信产业链",
        "market": "A股",
        "layers": [
            {"id": "quantum_chip", "name": "量子芯片/超导", "rank": 1},
            {"id": "quantum_control", "name": "量子测控系统", "rank": 2},
            {"id": "quantum_cryo", "name": "稀释制冷/低温", "rank": 3},
            {"id": "quantum_comm", "name": "量子通信/加密", "rank": 4},
            {"id": "quantum_software", "name": "量子软件/算法", "rank": 5},
        ],
        "keywords": [
            "量子计算", "量子芯片", "超导量子", "量子通信", "量子加密",
            "稀释制冷", "量子测控", "量子软件"
        ],
        "source_hints": ["年报", "公告", "专利", "政策文件"],
    },
}


def get_all_industry_ids():
    return list(INDUSTRY_CHAINS.keys())


def get_industry_chain(industry_id):
    return INDUSTRY_CHAINS.get(industry_id)


def get_chain_layers(industry_id):
    chain = get_industry_chain(industry_id)
    if not chain:
        return []
    return sorted(chain["layers"], key=lambda x: x["rank"])


def get_chain_summary(industry_id):
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
