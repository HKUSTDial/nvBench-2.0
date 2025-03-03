# nvBench 2.

The nvBench 2.0 dataset is organized in JSON format with the following structure:

- `nvBench2.0/train.json`: Training data samples (6,302 queries)
- `nvBench2.0/dev.json`: Development/validation data samples (788 queries)
- `nvBench2.0/test.json`: Test data samples (788 queries)
- `database/`: Source data tables
  - CSV format tables included
  - SQLite format tables available in [databases.zip](https://github.com/TsinghuaDatabaseGroup/nvBench/blob/main/databases.zip)



# Dataset Format

The dataset is stored in JSON format with the following structure:

```json
{
  "csv_file": "string",           // Name of the source CSV file
  "nl_query": "string",           // Natural language query
  "table_schema": {               // Database schema information
    "table_columns": [],          // List of column names
    "column_examples": {},        // Example values for each column
    "unique_value_counts": {}     // Count of unique values per column
  },
  "steps": {                      // Step-by-step reasoning process
    "step_1": {
      "reasoning": "string",      // Reasoning for data selection
      "answer": {}
    },
    "step_2": {}, // Data transformation reasoning
    "step_3": {}, // Chart type reasoning  
    "step_4": {}, // Channel mapping reasoning
    "step_5": {}, // Multiple visualization synthesis
    "step_6": {}  // Final visualization configurations
  },
  "gold_answer": []              // Ground truth visualization specifications
}
```
