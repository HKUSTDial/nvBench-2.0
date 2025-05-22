import random
random.seed(0)

import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("generate_metadata.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

T = "temporal"
Q = "quantitative"
C = "category"

database_dir = "./database_csv_filtered/"
save_metadata = {}
total_csv_processed = 0

def process_csv_file(filename):
    """Process a single CSV file to extract metadata without ambiguity."""
    global total_csv_processed

    filepath = os.path.join(database_dir, filename)
    try:
        # Read CSV with optimized settings
        df = pd.read_csv(filepath, parse_dates=True, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read {filename}: {e}")
        return None

    # Type assignment and value examples in a single pass
    field_by_type = {T: [], Q: [], C: []}
    type_by_field = {}
    data_value_example = {}
    unique_value_num = {}

    for column in df.columns:
        # Type assignment
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            field_by_type[T].append(column)
            type_by_field[column] = T
        elif column == "id" or column.endswith("_id"):
            field_by_type[C].append(column)
            type_by_field[column] = C
        elif pd.api.types.is_numeric_dtype(df[column]):
            field_by_type[Q].append(column)
            type_by_field[column] = Q
        else:
            field_by_type[C].append(column)
            type_by_field[column] = C

        # Value examples
        if type_by_field[column] == Q:
            value_list = [df[column].min(), df[column].median(), df[column].max()]
            # Convert NumPy types to native Python types
            value_list = [float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v for v in value_list]
            value_list = [int(v) if isinstance(v, float) and v.is_integer() else v for v in value_list]
            data_value_example[column] = value_list
        elif type_by_field[column] == T:
            value_list = [df[column].min(), df[column].median(), df[column].max()]
            value_list = [v.strftime('%Y-%m-%d') if pd.notnull(v) else None for v in value_list]
            data_value_example[column] = value_list
        elif type_by_field[column] == C:
            unique_values = df[column].dropna().unique()
            num_samples = min(3, len(unique_values))
            sampled_values = random.sample(list(unique_values), num_samples) if num_samples > 0 else []
            data_value_example[column] = sampled_values

        # Unique value count - Convert NumPy types to native Python types
        unique_value_num[column] = int(df[column].nunique())

    total_csv_processed += 1

    return filename, {
        "field_list": list(df.columns),
        "field_by_type": field_by_type,
        "type_by_field": type_by_field,
        "data_value_example": data_value_example,
        "ignore_column_list": [],
        "unique_value_num": unique_value_num,
    }

def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)

def main():
    # Get CSV files
    csv_files = [f for f in os.listdir(database_dir) if f.endswith('.csv')]
    logger.info(f"Found {len(csv_files)} CSV files to process")

    # Process CSVs in parallel
    global save_metadata
    total_csv_processed = 0  # Local counter
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = tqdm(
            executor.map(process_csv_file, csv_files),
            total=len(csv_files),
            desc="Processing CSV files"
        )
        for result in results:
            if result:
                filename, metadata = result
                save_metadata[filename] = metadata
                total_csv_processed += 1  # Increment when result is valid

    # Print summary
    logger.info(f"Total CSV processed: {total_csv_processed}")

    # Convert all numpy types to native Python types before serialization
    save_metadata = convert_numpy_types(save_metadata)

    # Save metadata
    with open("BIRD_metadata.json", "w") as json_file:
        json.dump(save_metadata, json_file, indent=2)
        logger.info("Metadata saved to BIRD_metadata.json")

if __name__ == "__main__":
    main()