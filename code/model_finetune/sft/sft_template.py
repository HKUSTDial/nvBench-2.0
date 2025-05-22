SFT_PROMPT_STEP_TEMPLATE = """
You are a good data visualization expert. Given an ambiguous/incomplete Natural Language Query, a Data Table, your task is to recommend visualization charts corresponding to the ambiguous/incomplete NL Query. You need to think step by step in xml format and output the step-answer in JSON format.

# Input:
## Data Table:
### Table Columns:
{table_columns}
### Column Examples:
{column_examples}
### Unique Value Counts:
{unique_value_counts}

## Natural Language Query:
{nl_query}

# Output:
{output}
"""

STEP_BY_STEP_OUTPUT_TEMPLATE = """
<step_1>
<step_name>Extract Data Columns and Filters from NL Query</step_name>
<thinking>
{step_1_thinking}
</thinking>
<answer>
{step_1_answer}
</answer>
</step_1>
<step_2>
<step_name>Extract Data Transformation from NL Query</step_name>
<thinking>
{step_2_thinking}
</thinking>
<answer>
{step_2_answer}
</answer>
</step_2>
<step_3>
<step_name>Select Chart Type from NL Query</step_name>
<thinking>
{step_3_thinking}
</thinking>
<answer>
{step_3_answer}
</answer>
</step_3>
<step_4>
<step_name>Chart Channel Mapping</step_name>
<thinking>
{step_4_thinking}
</thinking>
<answer>
{step_4_answer}
</answer>
</step_4>
<step_5>
<step_name>Add Implicit Data Channels</step_name>
<thinking>
{step_5_thinking}
</thinking>
<answer>
{step_5_answer}
</answer>
</step_5>
<step_6>
<step_name>Add Implicit Data Transformation and Complete Chart with Data Filters</step_name>
<thinking>
{step_6_thinking}
</thinking>
<answer>
{step_6_answer}
</answer>
</step_6>
"""
SFT_PROMPT_TEMPLATE = """
You are a good data visualization expert. Given an ambiguous/incomplete Natural Language Query, a Data Table, your task is to recommend visualization charts corresponding to the ambiguous/incomplete NL Query. You need to output in JSON format.

# Input:
## Data Table:
### Table Columns:
{table_columns}
### Column Examples:
{column_examples}
### Unique Value Counts:
{unique_value_counts}

## Natural Language Query:
{nl_query}

# Output:
{output}
"""
