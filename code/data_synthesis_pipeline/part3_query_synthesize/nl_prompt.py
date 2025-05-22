step_prompt = """# Task: Generate 3 Natural Language Queries for Data Visualization
## Overview:
You will create three natural language queries (command, question, and statement) based on a given data schema and action list. Each query must incorporate ALL information from the action list without introducing extra elements.

## Input Format:
The input will contain a data schema and an action list with operations like mark, column, bin, aggregation, sort, and filter.

## Process (4 Steps):

### Step 1: Interpret Visualization Type
- If the action list contains a "mark" operation, rephrase it using natural terminology
- You can randomly choose from the examples but not limited to the examples:
  * "bar chart," -> "bar chart", "bars", "column chart," "histogram" (for frequency), etc.
  * "line chart," -> "line chart", "lines", "trend line," "time series", etc.
  * "scatter plot," -> "scatter points", "points", "dot plot," "correlation points", etc.
  * "pie chart," -> "pie chart", "circular chart," "proportion wheel," "sector diagram", etc.
  * "heatmap," -> "heat map", "color matrix," "density plot", etc.
  * "boxplot," -> "box plot", "range plot," "distribution box", etc.

### Step 2: Rephrase Data Columns
- For each "column" operation, rephrase using natural language
- For columns NOT marked [AMBI], use clear synonyms without introducing ambiguity
  * Example: "column last_name" → "family name," "surname" (but not just "name")
- For columns marked [AMBI], create intentionally ambiguous phrasing
  * Example: "column [AMBI]name" → "player" (when schema has first_name/last_name but no general name)

### Step 3: Rephrase Data Transformations
- For each aggregation operation, use natural language equivalents:
  * "aggregation sum revenue" → "total revenue," "combined revenue"
  * "aggregation average rating" → "average rating," "mean score"
  * "aggregation count customer_id" → "number of customers," "customer count"
- For bin operations, use time-based or range-based terminology:
  * "bin month date" → "monthly," "by month," "grouped by month"
  * "bin 10 price" → "price ranges," "price groups of 10"
- For sort operations, use ordering language:
  * "sort ascending price" → "from lowest to highest price"
  * "sort descending sales" → "from highest to lowest sales"

### Step 4: Rephrase Filter Conditions
- For each filter operation, use natural comparisons and prepositions:
  * "filter price > 50" → "above $50," "over $50," "exceeding $50"
  * "filter category = 'Electronics'" → "in Electronics," "Electronics category"
  * "filter date between 2020-01-01 and 2020-12-31" → "during 2020," "in 2020"

## Final Answer Construction:
Combine the rephrased elements from steps 1-4 to create three natural language queries:
1. Command-style: Direct instruction (e.g., "Plot the total sales by month for products priced over $50")
2. Question-style: Inquiry format (e.g., "What was the average rating for movies released during 2020?")
3. Statement-style: Declarative format (e.g., "Distribution of customer count by region in a pie chart.")

## Special Note:
Always prioritize natural language over technical terms. Avoid using words like "aggregation," "filter," "bin," etc. in your final queries.

## Output Format:

# OUTPUT:
## Step 1: ...
## Step 2: ...
## Step 3: ...
## Step 4: ...
## Final Output:
{
"command": "",
"question": "",
"statement": ""
}

# INPUT:
"""