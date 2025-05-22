import os
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import cProfile
import re
import csv
import logging

# Set random seed for reproducibility
import random
random.seed(0)

# Directory paths
database_dir = "./database_csv/"
filtered_database_dir = "./database_csv_filtered/"

# Create the filtered directory if it doesn't exist
os.makedirs(filtered_database_dir, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename="csv_processing_errors.log",
    level=logging.INFO,  # Log both errors and skipped files
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to count words in a string (unchanged)
def count_words(text):
    if not isinstance(text, str):
        return 0
    return len(re.findall(r'\b\w+\b', text))

# Function to process a single CSV file
def process_csv_file(filename, profile=False):
    if profile:
        cProfile.runctx('process_csv_file_inner(filename)', globals(), {'filename': filename}, filename=f'profile_{filename}.prof')
    else:
        process_csv_file_inner(filename)

def process_csv_file_inner(filename):
    # Check if filtered file already exists
    filtered_path = os.path.join(filtered_database_dir, filename)
    if os.path.exists(filtered_path):
        logging.info(f"Skipping {filename}: Filtered file already exists in {filtered_database_dir}")
        print(f"Skipping {filename}: Filtered file already exists.")
        return

    try:
        # Define columns to ignore
        ignore_cols = ['long', 'lat', 'lng', 'longitude', 'latitude']
        # Attempt to read CSV with robust parameters
        try:
            df = pd.read_csv(
                os.path.join(database_dir, filename),
                usecols=lambda x: x.lower() not in ignore_cols,
                dtype={'id': str},  # Simplified dtype for 'id' column
                low_memory=False,
                quoting=csv.QUOTE_ALL,  # Quote all fields to handle delimiters
                encoding='utf-8'
            )
        except UnicodeDecodeError:
            # Fallback to latin1 encoding if UTF-8 fails
            df = pd.read_csv(
                os.path.join(database_dir, filename),
                usecols=lambda x: x.lower() not in ignore_cols,
                dtype={'id': str},
                low_memory=False,
                quoting=csv.QUOTE_ALL,
                encoding='latin1'
            )
        except pd.errors.ParserError:
            # Fallback to Python engine for malformed CSVs
            df = pd.read_csv(
                os.path.join(database_dir, filename),
                usecols=lambda x: x.lower() not in ignore_cols,
                dtype={'id': str},
                quoting=csv.QUOTE_ALL,
                encoding='utf-8',
                engine='python'  # Removed low_memory as it's not supported
            )

        # Clean column names
        df.columns = [name.lower().replace(" ", "_").replace("-", "_") for name in df.columns]

        # Convert ID columns to string
        for name in df.columns:
            if name == "id" or name.endswith("_id"):
                df[name] = df[name].astype(str)

        # Convert date columns selectively
        keywords = ["date", "year", "month"]
        for name in df.columns:
            if any(keyword in name.lower() for keyword in keywords):
                sample = df[name].dropna().head(5)
                # Skip if sample is empty
                if sample.empty:
                    continue
                # Convert to string and check for date format (e.g., YYYY-MM-DD)
                if df[name].dtype == "object" or sample.astype(str).str.match(r'\d{4}-\d{2}-\d{2}').all():
                    df[name] = pd.to_datetime(df[name], format='%Y-%m-%d', errors='coerce')

        # Drop columns with all NaN
        df.dropna(axis=1, how='all', inplace=True)

        # Identify columns to drop
        threshold = 0.8 * len(df)
        # Vectorized NaN check
        na_columns = df.columns[df.isna().sum() > threshold]

        # Vectorized long text check
        long_text_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                char_lengths = df[col].astype(str).str.len()
                if (char_lengths > 100).sum() > threshold:
                    long_text_columns.append(col)

        # also drop columns of pictures/documents
        binary_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                # Get non-null values (consider scanning more rows or all if feasible)
                sample = df[col].dropna().astype(str)
                if not sample.empty:
                    # Check for binary data indicators
                    # 1. File extensions (images, documents, etc.)
                    # 2. URLs
                    # 3. XML/JSON-like structures
                    # 4. Hexadecimal data (e.g., 0xD0CF11E0 or long hex strings)
                    # 5. Non-printable characters (common in binary data)
                    if (
                        # File extensions
                        sample.str.contains(r'\.jpg|\.png|\.gif|\.jpeg|\.pdf|\.doc|\.docx|\.xls|\.xlsx', case=False, regex=True).any() or
                        # URLs
                        sample.str.contains(r'http://|https://', case=False, regex=True).any() or
                        # XML/JSON-like structures
                        sample.str.contains(r'^\s*<.*>|^\s*\{.*\}', case=False, regex=True).any() or
                        # Hexadecimal data (with or without 0x prefix, case-insensitive)
                        sample.str.contains(r'^(?:0x)?[0-9a-fA-F]{8,}', case=False, regex=True).any() or
                        # Non-printable characters (indicative of binary data)
                        sample.str.contains(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]', regex=True).any()
                    ):
                        binary_columns.append(col)
                        logging.info(f"Column '{col}' flagged as binary. Sample: {sample.head(5).tolist()}")

        # Combine all drops
        columns_to_drop = list(set(na_columns) | set(long_text_columns) | set(binary_columns))
        df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

        # Save filtered DataFrame only if it has at least 1 column and 1 row
        if not df.empty and len(df.columns) > 0:
            df.to_csv(os.path.join(filtered_database_dir, filename), index=False)
        else:
            logging.info(f"Skipping {filename}: DataFrame has no data after filtering")

    except Exception as e:
        # Log error and skip file
        logging.error(f"Failed to process {filename}: {str(e)}")
        print(f"Error processing {filename}: {str(e)}. See csv_processing_errors.log for details.")

# Process all CSV files in parallel using ProcessPoolExecutor
def main():
    csv_files = [f for f in os.listdir(database_dir) if f.endswith('.csv')]
    with ProcessPoolExecutor(max_workers=4) as executor:  # Adjust max_workers based on CPU cores
        futures = [executor.submit(process_csv_file, filename) for filename in csv_files]
        for _ in tqdm(futures, desc="Processing CSV files"):
            _.result()  # Wait for all futures to complete

if __name__ == "__main__":
    main()