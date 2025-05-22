import os
import sqlite3
import pandas as pd
from pathlib import Path

def explore_sqlite_databases(base_path):
    """
    Explore all SQLite databases in the given directory structure.
    For each database, list tables, number of rows, number of columns, and column names.
    
    Args:
        base_path (str): Path to the main database directory
    """
    # Convert base_path to a Path object for easier handling
    base_dir = Path(base_path)
    
    # Create a list to store all database info for final report
    all_db_info = []
    
    # Find all directories that might contain databases
    directories = [d for d in base_dir.iterdir() if d.is_dir()]
    
    print(f"Found {len(directories)} potential database directories")
    
    # Process each directory
    for directory in directories:
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
                cursor = conn.cursor()
                
                # Get all tables in the database
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [table[0] for table in cursor.fetchall()]
                
                if not tables:
                    print(f"  No tables found in {db_name}")
                    continue
                
                print(f"  Found {len(tables)} tables in {db_name}")
                
                # For each table, get row count, column count, and column names
                for table in tables:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    row_count = cursor.fetchone()[0]
                    
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table});")
                    columns = cursor.fetchall()
                    column_count = len(columns)
                    column_names = [col[1] for col in columns]
                    
                    # Print the information
                    print(f"  Table: {table}")
                    print(f"    Rows: {row_count}")
                    print(f"    Columns: {column_count}")
                    print(f"    Column names: {', '.join(column_names)}")
                    
                    # Store info for final report
                    all_db_info.append({
                        'Database': db_name,
                        'Table': table,
                        'Rows': row_count,
                        'Columns': column_count,
                        'Column Names': ', '.join(column_names)
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
    db_directory = "./database"
    
    print(f"Starting exploration of databases in {db_directory}")
    result_df = explore_sqlite_databases(db_directory)
    
    if result_df is not None:
        # Display the summary
        print("\n\nSummary of all databases:")
        print(result_df)
        
        # Optionally save to CSV
        result_df.to_csv("database_summary.csv", index=False)
        print("Summary saved to database_summary.csv")