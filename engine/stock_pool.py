# -*- coding: utf-8 -*-
"""
A 股全市场股票列表获取工具
从新浪财经接口获取所有 A 股列表（沪市 + 深市）
"""
import requests
import json
import time


def get_all_stocks(retry=3, delay=1.0):
    """
    从新浪财经获取全市场 A 股列表

    返回:
        list of dict: [{code, name, market}, ...]
        market: 'sh' 上交所, 'sz' 深交所
    """
    stocks = []

    # 沪市 A 股
    try:
        sh_stocks = _fetch_from_sina('sh_a', retry, delay)
        for s in sh_stocks:
            s['market'] = 'sh'
        stocks.extend(sh_stocks)
        print("沪市 A 股 {} 只".format(len(sh_stocks)))
    except Exception as e:
        print("获取沪市 A 股列表失败: {}".format(e))

    # 深市 A 股（主板 + 中小板 + 创业板）
    for node in ['sz_a']:
        try:
            sz_stocks = _fetch_from_sina(node, retry, delay)
            for s in sz_stocks:
                s['market'] = 'sz'
            stocks.extend(sz_stocks)
            print("深市 A 股 {} 只".format(len(sz_stocks)))
        except Exception as e:
            print("获取深市 A 股列表失败: {}".format(e))

    # 去重（按 code 去重）
    seen = set()
    unique_stocks = []
    for s in stocks:
        if s['code'] not in seen:
            seen.add(s['code'])
            unique_stocks.append(s)

    print("全市场 A 股总计: {} 只（去重后）".format(len(unique_stocks)))
    return unique_stocks


def _fetch_from_sina(node, retry=3, delay=1.0):
    """
    从新浪财经接口获取某个板块的股票列表

    参数:
        node: 'sh_a' 或 'sz_a'
        retry: 重试次数
        delay: 重试间隔（秒）

    返回:
        list of dict: [{code, name}, ...]
    """
    base_url = (
        'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php'
        '/Market_Center.getHQNodeData'
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn',
        'Accept': '*/*',
    }

    all_stocks = []
    page = 1
    page_size = 100  # 每页最多 100 条
    max_pages = 60   # 安全上限（5000/100 = 50）

    for attempt in range(retry):
        try:
            page = 1
            while page <= max_pages:
                params = {
                    'page': str(page),
                    'num': str(page_size),
                    'sort': 'code',
                    'asc': '1',
                    'node': node,
                    'symbol': '',
                    '_': str(int(time.time() * 1000)),
                }

                resp = requests.get(base_url, params=params, headers=headers, timeout=15)
                raw = resp.text

                if not raw or raw.strip() == '':
                    break

                # 新浪返回 JSON 或空
                # 如果返回空数组或 null，说明没有更多数据
                if raw.strip() in ('null', '[]', ''):
                    break

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    # 尝试清理特殊字符
                    cleaned = raw.replace('"', '"').replace("'", '"')
                    # 新浪有时返回非标准JSON，用更宽松的方式解析
                    data = json.loads(cleaned)

                if not data or not isinstance(data, list):
                    break

                if len(data) == 0:
                    break

                for item in data:
                    code = str(item.get('code', '')).strip()
                    name = str(item.get('name', '')).strip()
                    if code and name:
                        all_stocks.append({
                            'code': code,
                            'name': name,
                        })

                # 如果返回数量小于 page_size，说明已到最后一页
                if len(data) < page_size:
                    break

                page += 1
                time.sleep(0.3)  # 避免请求过快

            # 成功获取
            if all_stocks:
                break

        except Exception as e:
            print("新浪接口请求失败(node={}, attempt={}): {}".format(node, attempt + 1, e))
            if attempt < retry - 1:
                time.sleep(delay)
            continue

    return all_stocks


# 测试
if __name__ == '__main__':
    stocks = get_all_stocks()
    print("\n前 10 只股票:")
    for s in stocks[:10]:
        print("  {} {} ({})".format(s['code'], s['name'], s['market']))
    print("... 共 {} 只".format(len(stocks)))
