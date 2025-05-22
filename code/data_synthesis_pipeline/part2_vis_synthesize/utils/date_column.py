import pandas as pd
from datetime import datetime
import re

def parse_date_columns(df, date_cols=None):
    """
    Parse columns that contain date strings to datetime type
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input DataFrame
    date_cols : list, optional
        List of column names that should be treated as dates.
        If None, will try to automatically detect date columns
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with date columns parsed to datetime
    """
    # If date_cols is not provided, try to detect date columns
    if date_cols is None:
        date_cols = detect_date_columns(df)
    
    # Try to convert each detected date column
    for col in date_cols:
        if col in df.columns:
            try:
                # First try pandas to_datetime with error handling
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # If more than 80% of the values were successfully parsed, keep the conversion
                if df[col].notna().mean() < 0.8:
                    print(f"Warning: Column '{col}' had too many parsing failures, skipping conversion")
                    # Revert to original data
                    df[col] = df[col].astype('object')
                else:
                    print(f"Successfully converted column '{col}' to datetime")
            except Exception as e:
                print(f"Failed to convert column '{col}' to datetime: {e}")
    
    return df

def detect_date_columns(df, sample_size=100):
    """
    Attempt to detect columns that contain date values
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input DataFrame
    sample_size : int, optional
        Number of rows to sample for date detection
        
    Returns:
    --------
    list
        List of column names that appear to contain dates
    """
    date_cols = []
    
    # Common date patterns to check
    date_patterns = [
        # YYYY-MM-DD
        r'^\d{4}-\d{1,2}-\d{1,2}$',
        # MM/DD/YYYY
        r'^\d{1,2}/\d{1,2}/\d{4}$',
        # DD/MM/YYYY
        r'^\d{1,2}/\d{1,2}/\d{4}$',
        # MM-DD-YYYY
        r'^\d{1,2}-\d{1,2}-\d{4}$',
        # YYYY/MM/DD
        r'^\d{4}/\d{1,2}/\d{1,2}$',
        # Month DD, YYYY
        r'^[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}$',
    ]
    
    # Column name patterns that suggest dates
    date_name_patterns = [
        'date', 'dt', 'day', 'month', 'year', 'time'
    ]
    
    # Get a sample of the DataFrame
    sample_df = df.head(min(sample_size, len(df)))
    
    # Check each column
    for col in df.columns:
        # Check if column name suggests a date
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in date_name_patterns):
            date_cols.append(col)
            continue
        
        # Skip numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        
        # Check if values match date patterns
        if df[col].dtype == 'object':
            # Convert to string to ensure we can check patterns
            sample_values = sample_df[col].astype(str)
            
            # Calculate what percentage of values match date patterns
            match_count = 0
            for value in sample_values:
                if any(re.match(pattern, value.strip()) for pattern in date_patterns):
                    match_count += 1
            
            match_percentage = match_count / len(sample_values) if len(sample_values) > 0 else 0
            
            # If more than 70% of values match date patterns, consider it a date column
            if match_percentage > 0.7:
                date_cols.append(col)
    
    return date_cols

def load_and_parse_csv(file_path, date_cols=None):
    """
    Load a CSV file and parse date columns
    
    Parameters:
    -----------
    file_path : str
        Path to the CSV file
    date_cols : list, optional
        List of column names that should be treated as dates.
        If None, will try to automatically detect date columns
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with date columns parsed to datetime
    """
    # Load the CSV
    df = pd.read_csv(file_path)
    
    # Parse dates
    df = parse_date_columns(df, date_cols)
    
    return df


# Example usage
# Example usage
if __name__ == "__main__":
    # Example 1: Let the function detect date columns
    df = load_and_parse_csv("example.csv")
    print("Example 1 - Automatic detection - DataFrame dtypes:")
    print(df.dtypes)
    print("\n")
    
    # Example 2: Specify date columns explicitly
    df = load_and_parse_csv("example.csv", date_cols=["date"])
    print("Example 2 - Explicit date columns - DataFrame dtypes:")
    print(df.dtypes)
    print("\n")
    
    # Example 3: Parse dates in an existing DataFrame
    df = pd.read_csv("example.csv")
    print("Before parsing - DataFrame dtypes:")
    print(df.dtypes)
    print("\n")
    
    df = parse_date_columns(df)
    print("After parsing - DataFrame dtypes:")
    print(df.dtypes)