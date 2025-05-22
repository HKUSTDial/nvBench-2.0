# Standard library imports
import ast
import json
import math
import os
import time
import concurrent.futures
from typing import List, Optional, Set, Tuple, Dict

# Third-party library imports
import numpy as np
import pandas as pd
from tqdm import tqdm
np.random.seed(0)

# Local/application imports
import draco
from asp import solve_chart, convert_format, process_ambiguous_pairs
from date_column import load_and_parse_csv
from state import State, VQLState, transform_state_to_chart_config
from table import TableInfo
from utils.print_utils import suppress_stdout

# Define directories
csv_dir = "../part1.database_tables/database_csv_filtered"
output_dir = "./vis_output/"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

class Node:
    def __init__(self, state: State, parent: Optional['Node'] = None, action: Optional[int] = None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children: dict[int, Node] = {}
        self.prior_probability = parent.state.get_state_action_prior(action) if parent else 1.0

    def expand(self):
        """Expand node by creating all possible child nodes"""
        all_actions = self.state.get_legal_actions()
        for action in all_actions:
            if action not in self.children:
                next_state = self.state.take_action(action)
                self.children[action] = Node(next_state, self, action)

    def random_select_child(self) -> tuple[int, 'Node']:
        """Select a child node randomly based on prior probabilities"""
        actions = list(self.children.keys())
        priors = [self.children[a].prior_probability for a in actions]
        priors = np.array(priors)
        priors /= priors.sum()  # Normalize probabilities
        selected_action = np.random.choice(actions, p=priors)
        return selected_action, self.children[selected_action]

class SolutionPath:
    def __init__(self, actions, score=0):
        self.actions = actions
        self.score = score

    def compute_similarity(self, other: 'SolutionPath') -> float:
        """Compute similarity score with another solution path"""
        self.actions_wo_filter = []
        for action in self.actions:
            if action.name not in ["filter", "[TERMINAL]"]:
                self.actions_wo_filter.append(action)
        
        length = min(len(self.actions_wo_filter), len(other.actions))
        common = 0
        for idx in range(len(self.actions_wo_filter)):
            a1 = self.actions_wo_filter[idx]
            a2 = other.actions[idx]
            if idx == 0:
                num = 2
            else:
                num = 2*(length-1)
            if (str(a1) == str(a2)) and ("none" not in str(a1).lower()):
                common += 1/num
        return common

class RandomSelectTree:
    def __init__(self, initial_state: State):
        self.initial_state = initial_state
        self.solutions: List[Dict] = []  # Changed to list of dicts
        self.root = Node(initial_state)

    def get_k_result(self, state: State) -> Tuple[int, any]:
        """Get the k value from the terminal state"""
        return state.get_k_value()  # Should return both k and result

    def get_total_similarity(self, solution_dict: Dict) -> float:
        """Calculate total similarity of a solution with all other solutions"""
        total_similarity = 0
        current_solution = solution_dict["solution_path"]
        for existing_solution_dict in self.solutions:
            if existing_solution_dict != solution_dict:
                total_similarity += current_solution.compute_similarity(
                    existing_solution_dict["solution_path"]
                )
        return total_similarity

    def remove_most_similar_solution(self):
        """Remove the solution that has highest total similarity with others"""
        if not self.solutions:
            return

        max_similarity = float('-inf')
        solution_to_remove = None

        for solution_dict in self.solutions:
            total_similarity = self.get_total_similarity(solution_dict)
            if total_similarity > max_similarity:
                max_similarity = total_similarity
                solution_to_remove = solution_dict

        if solution_to_remove:
            self.solutions.remove(solution_to_remove)

    def search(self, num_solutions: int, num_simulations: int) -> List[Dict]:
        """
        Search for diverse solutions using random selection
        
        Args:
            num_solutions: Maximum number of solutions to maintain
            num_simulations: Number of simulation runs
        """
        for _ in range(num_simulations):
            # Start from root
            node = self.root
            actions = []

            # Random selection until terminal state
            while not node.state.is_terminal():
                # Expand if no children
                if not node.children:
                    node.expand()

                # Random select based on prior probability
                action, node = node.random_select_child()
                actions.append(action)

            # Get k value and result from terminal state
            k, result = self.get_k_result(node.state)

            # If k is valid (2-5), create solution
            if 2 <= k <= 5:
                solution_path = SolutionPath(actions)
                solution_dict = {
                    "solution_path": solution_path,
                    "result": result
                }
                self.solutions.append(solution_dict)

                # If too many solutions, remove most similar one
                if len(self.solutions) > num_solutions:
                    self.remove_most_similar_solution()

        return self.solutions



def get_run_number(csv_path):
    """Calculate number of solutions and simulations based on CSV column count."""
    df = pd.read_csv(csv_path)
    num_solution = 2 * df.shape[1]
    num_simulation = max(10, 25 * num_solution)
    return num_solution, num_simulation

def resolve_pie_y_theta(actions):
    for action in actions:
        if action.name == "mark":
            if action.op != "pie":
                return actions
    
    new_actions = []        
    for action in actions:
        if action.name == "encoding" and action.op == "y":
            action.op = "theta"
        new_actions.append(action)
        
    return new_actions


def run_tree(csv_path="example.csv"):
    # Initialize
    table_info = TableInfo(csv_path)
    initial_state = VQLState(table_info, [], 0)
    num_solutions, num_simulations = get_run_number(csv_path)
    random_tree = RandomSelectTree(initial_state)

    # Search for solutions
    solutions = random_tree.search(num_solutions=num_solutions, num_simulations=num_simulations)

    save_solutions = {}
    idx = 0
    for solution in solutions:
        # Extract components from solution
        solution_path = solution["solution_path"]
        result = solution["result"]
        
        # Get k value from the terminal state
        k = len(result)

        cur_actions = resolve_pie_y_theta(solution_path.actions)

        # Create action list from solution path
        action_list = [str(action) for action in cur_actions]
        
        # Generate chart config from actions
        chart_config = transform_state_to_chart_config(cur_actions)
        
        # Create save solution dictionary
        save_solution = {
            "k": k,
            "action_list": action_list,
            "chart_config": chart_config,
            "result": result
        }
        
        # Add to save solutions
        save_solutions["solution_" + str(idx)] = save_solution
        idx += 1
    
    # Get the CSV filename without path and extension
    csv_filename = os.path.splitext(os.path.basename(csv_path))[0]
    
    # Save to JSON file
    output_path = os.path.join(output_dir, f"{csv_filename}.json")
    with open(output_path, "w") as json_file:
        json.dump(save_solutions, json_file, indent=2)
    
    return csv_filename

def process_file(filename):
    """Process a single CSV file and return results"""
    try:
        # Create output filename
        output_filename = filename.split('.')[0] + '.json'
        output_path = os.path.join(output_dir, output_filename)
        
        # Process file if output doesn't exist
        if not os.path.exists(output_path):
            with suppress_stdout():
                print(f"Processing {filename}...")
            csv_path = os.path.join(csv_dir, filename)
            processed_name = run_tree(csv_path)
            return f"Successfully processed {filename}"
        else:
            return f"Skipping {filename} - output already exists"
    except Exception as e:
        return f"Error processing {filename}: {str(e)}"

if __name__ == "__main__":
    # Get list of CSV files to process
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    total_files = len(csv_files)
    with suppress_stdout():
        print(f"Found {total_files} CSV files to process")
    
    # Set the maximum number of worker processes
    max_workers = os.cpu_count()
    with suppress_stdout():
        print(f"Using {max_workers} worker processes")
    
    # Process files in parallel using ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and get future objects
        future_to_file = {executor.submit(process_file, filename): filename for filename in csv_files}
        
        # Initialize counter for processed files
        processed_count = 0
        
        # Process results as they complete with a progress bar
        for future in tqdm(concurrent.futures.as_completed(future_to_file), 
                          total=len(future_to_file), 
                          desc="Processing files", 
                          unit="file"):
            filename = future_to_file[future]
            try:
                result = future.result()
                with suppress_stdout():
                    print(result)  # Print the status message returned by process_csv_file
                
                # Increment counter
                processed_count += 1
                with suppress_stdout():
                    print(f"Count: {processed_count}, Count/Total %: {(processed_count/total_files)*100:.1f}%")
                
            except Exception as exc:
                with suppress_stdout():
                    print(f"{filename} generated an exception: {exc}")
    
    with suppress_stdout():
        print(f"Processed {processed_count} files in total")

# python -u main_multiprocess.py 1> main.log 2> main.error.log &