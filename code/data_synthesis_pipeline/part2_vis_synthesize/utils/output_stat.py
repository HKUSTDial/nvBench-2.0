import json
import os
from collections import defaultdict
from typing import Dict, Any, Tuple

def analyze_mark_statistics(directory: str = ".") -> Tuple[Dict[str, int], Dict[str, int], Dict[int, int]]:
    """
    Analyze mark type statistics and k values from JSON files in the specified directory.
    
    Args:
        directory (str): Directory containing JSON files to analyze
        
    Returns:
        Tuple[Dict[str, int], Dict[str, int], Dict[int, int]]: Input mark, output mark, and k-value statistics
    """
    # Initialize statistics dictionaries with default count of 0
    input_mark_stat = defaultdict(int)
    output_mark_stat = defaultdict(int)
    k_stat = defaultdict(int)  # New dictionary for k statistics
    
    # Process each JSON file in the directory
    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(directory, filename)
        # try:
        # Load JSON file
        with open(file_path, 'r') as f:
            solutions = json.load(f)
        
        # Process each solution in the file
        for solution_id, solution in solutions.items():
            # Record k value statistics
            k_value = solution["k"]
            if k_value is not None:
                k_stat[k_value] += 1

            # Process input mark type from chart_config
            chart_config = solution["chart_config"]
            if "view" in chart_config:
                for view in chart_config["view"]:
                    for mark in view["mark"]:
                        input_mark_type = mark["type"] if "type" in mark else "[NONE]"
                        input_mark_stat[input_mark_type] += 1
            
            # Process output mark type from result
            result = solution["result"]
            existing_spec = []
            for model_id, model in result.items():
                if not isinstance(model, dict):  # Skip if not a dictionary
                    continue
                
                spec = model["spec"]
                for view in spec["view"]:
                    for mark in view["mark"]:
                        if "type" in mark:  # Only consider if type exists in mark
                            output_mark_stat[mark["type"]] += 1
                
                if str(spec) not in existing_spec:
                    existing_spec.append(str(spec))
                else:
                    print(f"Filename: {filename}")
                    print(f"Solution ID: {solution_id}")
                    print(f"Solution: {solution}")
                    exit()
                        
        # except Exception as e:
        #     print(f"Error processing {filename}: {str(e)}")
        #     continue

    return input_mark_stat, output_mark_stat, k_stat

def print_statistics(input_stats: Dict[str, int], output_stats: Dict[str, int], k_stats: Dict[int, int]):
    """
    Print the mark type and k-value statistics in a formatted way.
    """
    print("\nInput Mark Type Statistics:")
    print("-" * 30)
    total_input = sum(input_stats.values())
    for mark_type, count in sorted(input_stats.items()):
        percentage = (count / total_input * 100) if total_input > 0 else 0
        print(f"{mark_type:<15} {count:>5} ({percentage:>6.2f}%)")
    
    print("\nOutput Mark Type Statistics:")
    print("-" * 30)
    total_output = sum(output_stats.values())
    for mark_type, count in sorted(output_stats.items()):
        percentage = (count / total_output * 100) if total_output > 0 else 0
        print(f"{mark_type:<15} {count:>5} ({percentage:>6.2f}%)")

    print("\nK-Value Statistics:")
    print("-" * 30)
    total_k = sum(k_stats.values())
    for k_value, count in sorted(k_stats.items()):
        percentage = (count / total_k * 100) if total_k > 0 else 0
        print(f"k={k_value:<13} {count:>5} ({percentage:>6.2f}%)")

def main():
    # Get current directory
    # current_dir = os.getcwd()
    current_dir = "./vis_output_multiprocess/"
    
    # Analyze statistics
    input_stats, output_stats, k_stats = analyze_mark_statistics(current_dir)
    
    # Print results
    print_statistics(input_stats, output_stats, k_stats)
    
    # # Optionally save results to a JSON file
    # statistics = {
    #     "input_mark_statistics": dict(input_stats),
    #     "output_mark_statistics": dict(output_stats),
    #     "k_statistics": dict(k_stats)
    # }
    # with open("mark_statistics.json", "w") as f:
    #     json.dump(statistics, f, indent=2)

if __name__ == "__main__":
    main()