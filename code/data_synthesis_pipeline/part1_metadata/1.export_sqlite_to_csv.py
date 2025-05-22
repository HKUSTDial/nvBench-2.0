import os
import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def export_sqlite_to_csv(base_path, output_dir="./database_csv"):
    """
    Explore all SQLite databases in the given directory structure and
    export all tables to CSV files in the format: output_dir/database@table.csv
    Skip tables if their CSV files already exist.
    
    Args:
        base_path (str): Path to the main database directory
        output_dir (str): Directory where CSV files will be saved
    """
    # Convert paths to Path objects for easier handling
    base_dir = Path(base_path)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create a list to store all database info for final report
    all_db_info = []
    
    # Find all directories that might contain databases
    directories = [d for d in base_dir.iterdir() if d.is_dir()]
    
    print(f"Found {len(directories)} potential database directories")
    
    # Process each directory
    for directory in tqdm(directories):
        # Look for SQLite files in this directory
        sqlite_files = list(directory.glob("*.sqlite"))
        
        for sqlite_file in sqlite_files:
            db_path = sqlite_file
            db_name = sqlite_file.stem
            
            print(f"\nExploring database: {db_name}")
            print("-" * 50)
            
            try:
                # Connect to the database
                conn = sqlite3.connect(db_path)
                
                # Get all tables in the database
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [table[0] for table in cursor.fetchall()]
                
                if not tables:
                    print(f"  No tables found in {db_name}")
                    continue
                
                print(f"  Found {len(tables)} tables in {db_name}")
                
                # For each table, export to CSV if it has rows and CSV doesn't exist
                for table in tables:
                    # Create CSV filename using the specified format
                    csv_filename = f"{db_name}@{table}.csv"
                    csv_path = output_path / csv_filename
                    
                    # Check if CSV file already exists
                    if csv_path.exists():
                        print(f"  Table: {table}")
                        print(f"    CSV already exists at {csv_path} - Skipping")
                        continue
                    
                    # Escape table name with square brackets
                    escaped_table = f"[{table}]"
                    # Get data using pandas
                    df = pd.read_sql_query(f"SELECT * FROM {escaped_table}", conn)
                    
                    # Get row and column counts
                    row_count = len(df)
                    column_count = len(df.columns)
                    column_names = ", ".join(df.columns.tolist())
                    
                    # Skip empty tables
                    if row_count == 0:
                        print(f"  Table: {table}")
                        print(f"    Rows: {row_count} - Skipping empty table")
                        continue
                    
                    # Export to CSV
                    df.to_csv(csv_path, index=False)
                    
                    # Print the information
                    print(f"  Table: {table}")
                    print(f"    Rows: {row_count}")
                    print(f"    Columns: {column_count}")
                    print(f"    Exported to: {csv_path}")
                    
                    # Store info for final report
                    all_db_info.append({
                        'Database': db_name,
                        'Table': table,
                        'Rows': row_count,
                        'Columns': column_count,
                        'Column Names': column_names,
                        'CSV Path': str(csv_path)
                    })
                    
            except sqlite3.Error as e:
                print(f"  Error accessing {db_name}: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
    
    # Create a DataFrame with all the collected information
    if all_db_info:
        df = pd.DataFrame(all_db_info)
        return df
    else:
        print("No database information collected.")
        return None

# Example usage
if __name__ == "__main__":
    # Replace with your actual database directory path
    db_directory = "/home/luotianqi/BIRD/data/train/train_databases"
    csv_output_dir = "./database_csv"
    
    print(f"Starting export of databases in {db_directory} to {csv_output_dir}")
    result_df = export_sqlite_to_csv(db_directory, csv_output_dir)
    
    if result_df is not None:
        # Display the summary
        print("\n\nSummary of all exported tables:")
        print(result_df)
        
        # Save summary to CSV
        summary_path = Path(csv_output_dir) / "export_summary.csv"
        result_df.to_csv(summary_path, index=False)
        print(f"Export summary saved to {summary_path}")