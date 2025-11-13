from typing import List, Dict, Any
import json
import pandas as pd


def deep_compare_charts(chart1: Dict[str, Any], chart2: Dict[str, Any]) -> bool:
    """
    深度比较两个图表JSON对象是否相等，忽略键的顺序
    """
    # 如果两个输入都是字典类型
    if isinstance(chart1, dict) and isinstance(chart2, dict):
        # 首先比较字典长度是否相等
        if len(chart1) != len(chart2):
            return False
        # 检查chart1中的每个键值对是否都在chart2中存在且值相等
        return all(
            k in chart2 and deep_compare_charts(v, chart2[k])
            for k, v in chart1.items()
        )
    
    # 如果两个输入都是列表类型
    elif isinstance(chart1, list) and isinstance(chart2, list):
        # 首先比较列表长度是否相等
        if len(chart1) != len(chart2):
            return False
        # 检查chart1中的每个元素是否都能在chart2中找到匹配项
        return all(
            any(deep_compare_charts(x, y) for y in chart2)
            for x in chart1
        )
    
    # 如果是基本类型（字符串、数字等），直接比较值
    else:
        return chart1 == chart2

def load_data(data_file):
    """加载数据文件"""
    with open(data_file, 'r') as f:
        return json.load(f)

def reverse_axes_if_needed(chart, metadata):
    """根据字段类型判断是否需要反转 x 轴和 y 轴"""
    global reverse_count  # 声明使用全局变量

    if not chart:
        return chart
    
    # 检查是否同时存在x轴和y轴编码
    if not (chart.get('encoding', {}).get('x') and chart.get('encoding', {}).get('y')):
        return chart
        
    x_field = chart['encoding']['x'].get('field')
    y_field = chart['encoding']['y'].get('field')
    
    # 检查字段是否存在
    if not (x_field and y_field):
        return chart

    # # 如果字段是列表类型，取第一个元素
    # if isinstance(x_field, list):
    #     x_field = x_field[0]
    # if isinstance(y_field, list):
    #     y_field = y_field[0]

    # 获取字段类型
    x_type = metadata.get('type_by_field', {}).get(x_field, None)
    y_type = metadata.get('type_by_field', {}).get(y_field, None)
    
    #print(x_type, y_type)

    # 如果 x 轴和 y 轴都是定量类型
    if x_type == 'quantitative' and y_type == 'quantitative' and x_field > y_field:
        # 交换 x 和 y
        chart['encoding']['x'], chart['encoding']['y'] = chart['encoding']['y'], chart['encoding']['x']
        # reverse_count += 1  # 计数器加1
        #print("reverse x and y")
        return chart

    # 对于 mark 为 bar line boxplot 的情况 ***
    if chart['mark'] in ['bar', 'line', 'boxplot'] and x_type == 'quantitative' and y_type != 'quantitative':
        # 交换 x 和 y
        chart['encoding']['x'], chart['encoding']['y'] = chart['encoding']['y'], chart['encoding']['x']
        # reverse_count += 1  # 计数器加1
        #print("reverse x and y")
        return chart

    return chart

def normalize_chart_order(chart):
    """规范化Vega-Lite图表对象的顺序"""
    # 定义新的有序字典来存储规范化后的图表
    if not chart:
        return chart

    normalized = {}
    
    # 1. mark
    if 'mark' in chart:
        normalized['mark'] = chart['mark']
    
    # 2. encoding
    if 'encoding' in chart:
        normalized['encoding'] = {}
        # 按照指定顺序处理encoding中的channel
        channel_order = ['x', 'y', 'theta', 'color', 'size']
        for channel in channel_order:
            if channel in chart['encoding']:
                normalized['encoding'][channel] = {}
                # 按照指定顺序处理channel中的属性
                property_order = ['field', 'aggregate', 'bin', 'sort']
                for prop in property_order:
                    if prop in chart['encoding'][channel]:
                        normalized['encoding'][channel][prop] = chart['encoding'][channel][prop]
                
                # 添加其他未在顺序中指定的属性
                for key in chart['encoding'][channel]:
                    if key not in property_order:
                        normalized['encoding'][channel][key] = chart['encoding'][channel][key]

        # 添加其他未指定的channel ***
        for key in chart['encoding']:
            if key not in channel_order:
                normalized['encoding'][key] = chart['encoding'][key]
    
    # 3. transformation
    if 'transform' in chart:
        normalized['transform'] = []
        for transform in chart['transform']:
            if 'filter' in transform:
                normalized_filter = {}
                # 按照指定顺序处理filter中的操作符
                operator_order = ['equal', 'lt', 'lte', 'gt', 'gte', 'range', 'oneOf', 'valid']
                for op in operator_order:
                    if op in transform['filter']:
                        normalized_filter[op] = transform['filter'][op]
                
                # 添加其他未在顺序中指定的操作符
                for key in transform['filter']:
                    if key not in operator_order:
                        normalized_filter[key] = transform['filter'][key]
                
                normalized['transform'].append({'filter': normalized_filter})
    
    # 添加其他未在顺序中指定的顶层属性
    for key in chart:
        if key not in ['mark', 'encoding', 'transform']:
            normalized[key] = chart[key]
    
    return normalized

def remove_empty_values(chart_list):
    """删除图表中值为空的键值对"""
    def clean_dict(d):
        if not isinstance(d, dict):
            return d
        
        # 创建一个新字典来存储非空值
        result = {}
        for k, v in d.items():
            # 处理嵌套字典
            if isinstance(v, dict):
                cleaned = clean_dict(v)
                if cleaned:  # 如果清理后的字典非空
                    result[k] = cleaned
            # 处理列表
            elif isinstance(v, list):
                if v:  # 如果列表非空
                    cleaned = [clean_dict(item) if isinstance(item, dict) else item for item in v]
                    # 只保留非空的列表
                    cleaned = [item for item in cleaned if item]
                    if cleaned:
                        result[k] = cleaned
            # 处理其他非空值
            elif v is not None and v != "":
                result[k] = v
        
        return result

    # 处理列表中的每个图表
    cleaned_charts = []
    for chart in chart_list:
        cleaned_chart = clean_dict(chart)
        cleaned_charts.append(cleaned_chart)
    
    return cleaned_charts

def remove_duplicates(chart_list):
    """移除重复的图表，并统计重复次数"""
    global duplicate_count
    unique_charts = {}
    
    # 使用字典去重，键为图表的JSON字符串
    for chart in chart_list:
        chart_str = json.dumps(chart, sort_keys=True)
        if chart_str not in unique_charts:
            unique_charts[chart_str] = chart
        else:
            duplicate_count += 1
    
    return list(unique_charts.values())

def test_remove_empty_values():
    """测试remove_empty_values函数的示例"""
    # 测试数据
    test_charts = [{
        "mark": "point",
        "encoding": {
            "x": {
                "field": "invoice_number",
                "type": "",  # 空值
                "scale": {}  # 空字典
            },
            "y": {
                "field": "order_id",
                "aggregate": None,  # None值
                "bin": []  # 空列表
            }
        },
        "transform": []  # 空列表
    }]
    
    # 调用函数
    cleaned_charts = remove_empty_values(test_charts)
    
    # 打印结果
    print("\n测试 remove_empty_values 函数:")
    print("原始图表:", json.dumps(test_charts, indent=2, ensure_ascii=False))
    print("清理后的图表:", json.dumps(cleaned_charts, indent=2, ensure_ascii=False))

# def main():
#     # 加载数据和元数据
#     nvbench_data = load_data(nvBench2_file)
#     metadata_data = load_data(metadata_file)
    
#     # 遍历每个对象
#     for obj in nvbench_data:
#         csv_file = obj.get('csv_file')
#         metadata = metadata_data.get(csv_file, {})
#         chart_list = obj.get('output', [])

#         new_chart_list = []
#         for chart in chart_list:
#             # 1. 反转 x 轴和 y 轴
#             updated_chart = reverse_axes_if_needed(chart, metadata)
#             # 2. 规范化图表对象顺序
#             normalized_chart = normalize_chart_order(updated_chart)
#             new_chart_list.append(normalized_chart)
        
#         # 3. 删除空值的键值对
#         cleaned_chart_list = remove_empty_values(new_chart_list)
#         # 4. 去除重复图表
#         unique_chart_list = remove_duplicates(cleaned_chart_list)
#         # print(chart_list)
#         # print(new_chart_list)
#         #obj['output'] = unique_chart_list

#     print(f"\nTotal reversed charts: {reverse_count}")
#     print(f"Total duplicate charts: {duplicate_count}")

# if __name__ == "__main__":
#     main()
#     #test_remove_empty_values()
