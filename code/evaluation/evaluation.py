import os
import numpy as np
from typing import List, Callable, Dict, Any, Union
import json
import argparse

from utils import load_data, reverse_axes_if_needed, normalize_chart_order, deep_compare_charts

metadata_file = "raw_data/nvbench_metadata.json"
# Load the JSON data
all_metadata = load_data(metadata_file)

def evaluate_metrics(
    dataset,
    compare_fn: Callable[[Any, Any], bool],
    k_values: List[int] = [1, 3, 5]
) -> Dict[str, Dict[int, float]]:
    """
    Evaluates Hit@K, Recall@K, Precision@K, and F1@K for NL-to-visualization tasks.
    
    Args:
        model_outputs: List of model predictions for each input [Y1, Y2, ..., YN]
                      where each Yn is a list of predicted answers [y1, y2, ...]
        golden_answers: List of golden answers for each input [G1, G2, ..., GN]
                      where each Gn is a list of correct answers [g1, g2, ...]
        compare_fn: Function that compares if a prediction matches a golden answer
        k_values: List of K values to evaluate metrics at
        
    Returns:
        Dictionary containing results for each metric at each K value
    """

    n_samples = len(dataset)
    results = {
        "hit": {k: 0.0 for k in k_values},
        "recall": {k: 0.0 for k in k_values},
        "precision": {k: 0.0 for k in k_values},
        "f1": {k: 0.0 for k in k_values}
    }
    
    for i in range(n_samples):
        Y = dataset[i]["model_predict"]
        G = dataset[i]["ground_truth"]
        csv_filename = dataset[i]["csv_filename"]
        metadata = all_metadata[csv_filename]
        
        if not isinstance(Y, list):
            Y = [Y]
        if not isinstance(G, list):
            G = [G]

        # proprocess 包括 reverse x/y 和 re-order
        Y = preprocess_charts(Y, metadata)
        G = preprocess_charts(G, metadata)
        
        # Skip samples with no golden answers to avoid division by zero
        if len(G) == 0:
            n_samples -= 1
            continue
            
        for k in k_values:
            # Take only top-k predictions
            Y_k = Y[:k] if len(Y) >= k else Y
            
            # Calculate intersection by comparing each prediction with each golden answer
            intersection = 0
            matched_golden = set()
            matched_pred = set()
            
            for y_idx, y in enumerate(Y_k):
                for g_idx, g in enumerate(G):
                    if g_idx not in matched_golden and y_idx not in matched_pred and compare_fn(y, g):
                        intersection += 1
                        matched_golden.add(g_idx)
                        matched_pred.add(y_idx)
                        break
            
            # Calculate Hit@K (1 if at least one correct prediction, 0 otherwise)
            hit_k = 1.0 if intersection > 0 else 0.0
            results["hit"][k] += hit_k
            
            # Calculate Recall@K
            recall_k = intersection / len(G)
            results["recall"][k] += recall_k
            
            # Calculate Precision@K (handle empty Y_k case to avoid division by zero)
            precision_k = intersection / len(Y_k) if len(Y_k) > 0 else 0.0
            results["precision"][k] += precision_k
            
            # Calculate F1@K
            if precision_k + recall_k > 0:
                f1_k = 2 * (precision_k * recall_k) / (precision_k + recall_k)
            else:
                f1_k = 0.0
            results["f1"][k] += f1_k
    
    # Calculate averages
    if n_samples > 0:
        for metric in results:
            for k in k_values:
                results[metric][k] /= n_samples
    
    return results

def print_evaluation_results(results: Dict[str, Dict[int, float]]) -> None:
    """
    Prints evaluation results in a formatted table.
    
    Args:
        results: Dictionary containing results for each metric at each K value
    """
    metrics = list(results.keys())
    k_values = list(results[metrics[0]].keys())
    
    # Print header
    print(f"{'Metric':12}", end="")
    for k in k_values:
        print(f"K={k:<8}", end="")
    print()
    
    # Print separator
    print("-" * (12 + 8 * len(k_values)))
    
    # Print results for each metric
    for metric in metrics:
        print(f"{metric.capitalize():12}", end="")
        for k in k_values:
            print(f"{results[metric][k]:.4f}   ", end="")
        print()



def preprocess_charts(charts: List[Dict], metadata: Dict) -> List[Dict]:
    """
    对图表列表进行预处理:
    1. 反转坐标轴（如果需要）
    2. 标准化图表顺序
    （(已省略）3. 移除重复项）
    """
    processed_charts = []
    for chart in charts:
        if not isinstance(chart, dict):
            chart = None
            processed_charts.append(chart)
            continue
        # 反转坐标轴（如果需要）
        chart = reverse_axes_if_needed(chart, metadata)
        # 标准化图表顺序
        chart = normalize_chart_order(chart)
        processed_charts.append(chart)
    
    # # 移除重复项
    # processed_charts = remove_duplicates(processed_charts)

    return processed_charts

# Example usage with a simple comparison function
def example_compare_fn(pred, gold):
    """
    Simple comparison function that checks exact equality.
    In a real scenario, you would implement a more sophisticated comparison
    based on visualization equivalence.
    """
    return deep_compare_charts

# Example data
if __name__ == "__main__":
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='评估NL-to-visualization任务的性能')
    parser.add_argument('result_dir', type=str, help='结果文件夹的路径')
    
    args = parser.parse_args()
    
    raw_data_file = 'raw_data/test.json'
    raw_data = load_data(raw_data_file)
    print(f"Raw Data {raw_data_file} has {len(raw_data)} objects")
    
    RESULT_DIR = args.result_dir
    # 检查结果目录是否存在
    if not os.path.exists(RESULT_DIR):
        print(f"Error: result directory {RESULT_DIR} does not exist")
        exit(1)
    
    # 获取gpt35_result_ex1目录下的文件列表
    files = os.listdir(RESULT_DIR)
    # 打印文件数量
    print(f"result dir {RESULT_DIR} has {len(files)} files")
    
    # 从路径中提取ex_num和model_name
    # 处理路径末尾的斜杠
    clean_path = RESULT_DIR.rstrip('/')
    path_parts = clean_path.split("/")
    
    if len(path_parts) >= 2:
        result_folder = path_parts[-1]  # 获取最后一个文件夹名
        
        # 尝试提取ex_num
        if "_ex" in result_folder:
            ex_num = result_folder.split("_ex")[1].split("_")[0]
        else:
            ex_num = "1"  # 默认值
        
        # 尝试提取model_name
        model_name = path_parts[-1].split("_")[0]
    else:
        ex_num = "1"
        model_name = "unknown"
    
    print(f"ex_num: {ex_num}, model_name: {model_name}")
    
    # Initialize the dataset list
    dataset = []

    # 遍历 RESULT_DIR 文件夹中的所有文件
    for filename in os.listdir(RESULT_DIR):
        if filename.endswith(".json"):  # 假设每个文件都是 JSON 格式
            file_path = os.path.join(RESULT_DIR, filename)
            try:
                data = load_data(file_path)
                    
                # 获取 csv_filename, model_predict 和 ground_truth
                csv_filename = data.get("csv_file")
                if ex_num == "1":
                    model_predict = data.get(model_name+"_json", []) or [] # 确保model_predict是列表类型
                else:
                    if model_name+"_json" in data and data.get(model_name+"_json") is not None:
                        if isinstance(data.get(model_name+"_json"), dict):
                            model_predict = data.get(model_name+"_json", {}).get("final_output", [])
                        elif isinstance(data.get(model_name+"_json"), list):
                            model_predict = data.get(model_name+"_json", [])[0].get("final_output", [])
                    else:
                        model_predict = []
                
                ground_truth = json.loads(data.get("gold_answer", "[]"))
                #print(type(ground_truth))
                
                # 将数据添加到 dataset
                dataset.append({
                    "csv_filename": csv_filename,
                    "model_predict": model_predict,
                    "ground_truth": ground_truth
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Calculate metrics
    results = evaluate_metrics(dataset, example_compare_fn)
    
    # Print results
    print("Evaluation Results:")
    print_evaluation_results(results)