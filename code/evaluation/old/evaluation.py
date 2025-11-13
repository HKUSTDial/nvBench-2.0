import numpy as np
from typing import List, Callable, Dict, Any, Union
import json
import ast
import re
from utils import reverse_axes_if_needed, normalize_chart_order, deep_compare_charts
import os

# metadata_file = "../data/nvbench2_metadata.json"
metadata_file = "/home/luotianqi/github/HKUSTDial/nvBench2.0/nvBench2.0-data-gen/data_generation/part1.nvbench_tables/nvbench_metadata.json"
# Load the JSON data
with open(metadata_file, 'r') as f:
    all_metadata = json.load(f)

# def evaluate_metrics(
#     dataset,
#     compare_fn: Callable[[Any, Any], bool],
#     k_values: List[int] = [1, 3, 5]
# ) -> Dict[str, Dict[int, float]]:
#     """
#     Evaluates Hit@K, Recall@K, Precision@K, and F1@K for NL-to-visualization tasks.
    
#     Args:
#         model_outputs: List of model predictions for each input [Y1, Y2, ..., YN]
#                       where each Yn is a list of predicted answers [y1, y2, ...]
#         golden_answers: List of golden answers for each input [G1, G2, ..., GN]
#                       where each Gn is a list of correct answers [g1, g2, ...]
#         compare_fn: Function that compares if a prediction matches a golden answer
#         k_values: List of K values to evaluate metrics at
        
#     Returns:
#         Dictionary containing results for each metric at each K value
#     """

#     n_samples = len(dataset)
#     results = {
#         "hit": {k: 0.0 for k in k_values},
#         "recall": {k: 0.0 for k in k_values},
#         "precision": {k: 0.0 for k in k_values},
#         "f1": {k: 0.0 for k in k_values}
#     }
    
#     for i in range(n_samples):
#         Y = dataset[i]["model_predict"]
#         G = dataset[i]["ground_truth"]
#         csv_filename = dataset[i]["csv_filename"]
#         metadata = all_metadata[csv_filename]

#         # proprocess 包括 reverse x/y 和 re-order
#         Y = preprocess_charts(Y, metadata)
#         G = preprocess_charts(G, metadata)
        
#         # Skip samples with no golden answers to avoid division by zero
#         if len(G) == 0:
#             n_samples -= 1
#             continue
            
#         for k in k_values:
#             # Take only top-k predictions
#             Y_k = Y[:k] if len(Y) >= k else Y
            
#             # Calculate intersection by comparing each prediction with each golden answer
#             intersection = 0
#             matched_golden = set()
#             matched_pred = set()
            
#             for y_idx, y in enumerate(Y_k):
#                 for g_idx, g in enumerate(G):
#                     if g_idx not in matched_golden and y_idx not in matched_pred and compare_fn(y, g):
#                         intersection += 1
#                         matched_golden.add(g_idx)
#                         matched_pred.add(y_idx)
#                         break
            
#             # Calculate Hit@K (1 if at least one correct prediction, 0 otherwise)
#             hit_k = 1.0 if intersection > 0 else 0.0
#             results["hit"][k] += hit_k
            
#             # Calculate Recall@K
#             recall_k = intersection / len(G)
#             results["recall"][k] += recall_k
            
#             # Calculate Precision@K (handle empty Y_k case to avoid division by zero)
#             precision_k = intersection / len(Y_k) if len(Y_k) > 0 else 0.0
#             results["precision"][k] += precision_k
            
#             # Calculate F1@K
#             if precision_k + recall_k > 0:
#                 f1_k = 2 * (precision_k * recall_k) / (precision_k + recall_k)
#             else:
#                 f1_k = 0.0
#             results["f1"][k] += f1_k
    
#     # Calculate averages
#     if n_samples > 0:
#         for metric in results:
#             for k in k_values:
#                 results[metric][k] /= n_samples
    
#     return results

def evaluate_metrics(
    dataset,
    compare_fn: Callable[[Any, Any], bool],
    k_values: List[int] = [1, 3, 5],
    predict_file: str = None
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
        predict_file: Path to the predictions file, used to determine where to save low precision samples
        
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
    
    # List to store samples where precision is not 1
    low_precision_samples = []
    
    for i in range(n_samples):
        Y = dataset[i]["model_predict"]
        G = dataset[i]["ground_truth"]
        csv_filename = dataset[i]["csv_filename"]
        nl_query = dataset[i]["nl_query"]
        metadata = all_metadata[csv_filename]

        # Check if Y is not a list, and if so, initialize it as an empty list
        if not isinstance(Y, list):
            Y = []
            
        # proprocess 包括 reverse x/y 和 re-order
        try:
            Y = preprocess_charts(Y, metadata)
            G = preprocess_charts(G, metadata)
        except Exception as e:
            # If preprocessing fails, use original charts
            print(f"Error during preprocessing: {e}")
            pass
        
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
                    try:
                        compare_result = compare_fn(y, g)
                    except Exception as e:
                        # If there's any error during comparison, set result to false
                        compare_result = False
                        # Optional: you can log the error if needed
                        print(f"Error comparing charts: {e}")

                    if g_idx not in matched_golden and y_idx not in matched_pred and compare_result:
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
            
            # If precision is not 1, save the sample
            if precision_k < 1.0:
                sample_info = {
                    "csv_filename": csv_filename,
                    "nl_query": nl_query,
                    "ground_truth": G,
                    "prediction": Y_k,
                    "ground_truth_num": len(G),
                    "prediction_num": len(Y_k),
                    "precision": precision_k,
                    "recall": recall_k,
                    "k": k
                }
                low_precision_samples.append(sample_info)
            
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
    
    # Save samples with low precision to a JSON file
    if low_precision_samples and predict_file:
        # Get the directory of the predictions file
        output_dir = os.path.dirname(predict_file)
        output_file = os.path.join(output_dir, "low_precision_samples.json")
        with open(output_file, "w") as f:
            json.dump(low_precision_samples, f, indent=2)
        print(f"Saved {len(low_precision_samples)} samples with precision < 1 to {output_file}")
    
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


def parse_chart(chart):
    chart_dict = None
    try:
    # First try json.loads which is safer for parsing JSON
    
        chart_dict = json.loads(chart)
    except json.JSONDecodeError:
        try:
            # Fall back to ast.literal_eval only if needed
            chart_dict = ast.literal_eval(chart)
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing chart: {e}")
            # print(f"Chart content: {chart[:100]}...")  # Print part of the chart for debugging

    return chart_dict


# def preprocess_charts(charts: List[Dict], metadata: Dict) -> List[Dict]:
#     """
#     对图表列表进行预处理:
#     1. 反转坐标轴（如果需要）
#     2. 标准化图表顺序
#     （(已省略）3. 移除重复项）
#     """
#     processed_charts = []
#     for chart in charts:
#         if isinstance(chart, str):
#             chart = parse_chart(chart)

#         # 反转坐标轴（如果需要）
#         chart = reverse_axes_if_needed(chart, metadata)
#         # 标准化图表顺序
#         chart = normalize_chart_order(chart)
#         processed_charts.append(chart)
    
#     # # 移除重复项
#     # processed_charts = remove_duplicates(processed_charts)

#     return processed_charts
def preprocess_charts(charts: List[Dict], metadata: Dict) -> List[Dict]:
    """
    对图表列表进行预处理:
    1. 反转坐标轴（如果需要）
    2. 标准化图表顺序
    （(已省略）3. 移除重复项）
    """
    processed_charts = []
    for chart in charts:
        try:
            # 反转坐标轴（如果需要）
            chart = reverse_axes_if_needed(chart, metadata)
            # 标准化图表顺序
            chart = normalize_chart_order(chart)
        except Exception as e:
            print(f"Error processing chart: {e}")

        processed_charts.append(chart)

    # # 移除重复项
    # processed_charts = remove_duplicates(processed_charts)

    return processed_charts

# if prediction is in step_6, extract the answer
# else, return the prediction
# <step_6>\n<step_name>...</step_name>\n<thinking>...</thinking>\n<answer>...</answer>\n</step_6>
def extract_answer_from_step_6(prediction):
    step_6_match = re.search(r"<step_6>(.*?)</step_6>", prediction, re.DOTALL)
    if step_6_match:
        step_6 = step_6_match.group(1)
        answer_match = re.search(r"<answer>(.*?)</answer>", step_6, re.DOTALL)
        if answer_match:
            return answer_match.group(1).strip()
    return prediction

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
    # Sample data
    test_file = "/home/luotianqi/github/HKUSTDial/nvBench2.github.io/data/nvbench2.0/test.json"
    test_dataset = [(item["csv_file"], item["nl_query"], json.loads(item["gold_answer"])) for item in json.load(open(test_file, "r"))]
    
    predictions = []
    predict_file = "/home/luotianqi/github/HKUSTDial/nvBench2.0/nvBench2.0-hpc-boyan/finetune_jsonl/step-dpo/new_output/Qwen2.5-7B-SFT-WITH-THINKING-FUSED-STEP-DPO-170/predictions.jsonl"
    
    for line in open(predict_file, "r"):
        try:
            pred_answer = json.loads(line)["prediction"]
            pred_answer = extract_answer_from_step_6(pred_answer)
            predictions.append(json.loads(pred_answer))
        except Exception as e:
            predictions.append([])
    
    dataset = [
        {
            "csv_filename": csv_file,
            "nl_query": nl_query,
            "model_predict": prediction,
            "ground_truth": gold_answer
        }
        for (csv_file, nl_query, gold_answer), prediction in zip(test_dataset, predictions)
    ]
    
    # Calculate metrics
    results = evaluate_metrics(dataset, example_compare_fn, predict_file=predict_file)
    
    # Print results
    print("Evaluation Results:")
    print_evaluation_results(results)
