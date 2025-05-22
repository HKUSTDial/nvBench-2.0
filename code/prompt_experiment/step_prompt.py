import json
import ast
from gpt_call import call_gpt_3_5, call_qwen

sys_content = "You are an intelligent assistant."
# Task:
prompt = """You are a good data visualization expert. Given an ambiguous/incomplete Natural Language Query, a Data Table, your task is to to generate 1 to 5 different visualization charts corresponding for the ambiguous/incomplete NL Query. Please think step by step.

# Instructions:
Step 1: Extract Data Columns and Filters from NL Query.
- First, identify the relevant columns (fields) mentioned in the NL query. If there are more than one possible column mappings for one phrase in the NL query (e.g., name -> first_name/last_name), we define this case as an "ambiguous" case, and you need to output all possible columns, and tag the ambiguity in this step answer.
- Second, identify the data filters (conditions) mentioned in the NL query if they exist. Otherwise, leave the filter answer as empty list.
- The output for this step is a column list and a filter list.e.g.{"step_1": {"reasoning": "reasoning for step 1", "answer": {"column_list": [], "filter_list": []}}}

Step 2: Extract Data Transformation from NL Query. 
- Identify the data transformation mentioned in the NL Query.
- Possible transformation includes three kind of operations=(aggregat;bin;sort).
- Aggregation operation includes three types: 'sum', 'mean', 'count', e.g., {"field": "price","aggregate": "mean"}.
- Note: aggregation 'count' can be considered as a special computed data column to fill in Quantitative (Q) channel, and it must not include a `field`, e.g.{"x": {"field": "product"}, "y": {"aggregate": "count"}} means y is the counted row number for each product. However, e.g., {"theta": "product", "aggregate": "count"} is a bad case because it incorrectly includes a field and a'count' aggregation.
- Bin operation on Quantitative Columns indicating the binned size, e.g. {"field": "price", "bin": {"maxbins": 10}}, which means the price will be grouped to 10 bins.
- Bin operation on Temporal Columns is called the timeUnit, e.g. {"field": "date", "timeUnit": "year"}, which means unit(bin) the date by year.
- Sort operation includes 'ascending' or 'descending', e.g. {"field": "price", "sort": "ascending"}.
- Note that there are possible one or more transformations in the NL query.
- The output for this step is a transformation list. e.g.{"step_2": {"reasoning": "reasoning for step 2", "answer": []}}

Step 3: Select Chart Type from NL Query. 
- Possible chart type=(bar, line, arc, point, rect, boxplot). Note that 'arc' is identical to the pie chart, and 'rect' is identical to the heatmap chart.
- If the NL Query mentions one exact chart type, select the single chart type.
- Else if the NL Query does not mention the chart type, but indicate a data analysis task in (trend;distribution;correlation), infer the possible chart types by (task:chart)=(trend:[bar,line]; distribution:[bar,arc,line,boxplot]; correlation:[point,heatmap]).
- Otherwise, when no hints for chart type are mentioned in the NL query, all chart types are possible.
- The output for this step is a chart type list. e.g.{"step_3": {"reasoning": "reasoning for step 3", "answer": []}}

Step 4: Chart Channel Mapping.
- This subtask maps the selected data columns (from step 1) and data transformations (from step 2) to the chosen chart types (from step 3), assigning data to appropriate visual encoding channels. These channels include: 'x' for horizontal axis values, 'y' for vertical axis values, 'theta' for angular positions in pie charts, 'color' for representing data through different colors (either categorical distinctions or continuous value scales as in heatmaps), and 'size' for representing data magnitude through point sizes in scatter plots.
- Note that, there are obligatory or optional channels, follow the defination (chart:channel)=(bar:[x*,y*,color]; line:[x*,y*,color]; arc:[color*,theta*]; point:[x*,y*,color,size]; rect:[x*,y*,color*]; boxplot:[x*,y*]), where the channels with * obligatory, the channels without * are optional.
- There are only three different column types: Category (C), Quantitative (Q), and Temporal (T), where C, Q and T is the abbreviations for types. Importantly, there are fixed valid column types for specific chart channels, defined by `chart: [channel:type]`:
-- bar: [x:C/Q/T,y:Q,color:C];
-- line: [x:C/Q/T,y:Q,color:C];
-- arc: [color:C,theta:Q];
-- point: [x:Q,y:Q,color:C,size:Q];
-- rect: [x:C/Q/T,y:C/Q,color:Q];
-- boxplot: [x:C,y:Q])
- Note: aggregation 'count' can be considered as a special computed data column to fill in Quantitative (Q) channel, and it must not include a `field`, e.g.{"x": {"field": "product"}, "y": {"aggregate": "count"}} means y is the counted row number for each product. However, e.g., {"theta": "product", "aggregate": "count"} is a bad case  because it incorrectly includes a field and a'count' aggregation.
- You should also consider basic channel mapping feasibility, e.g., do not make category num for x/y/color be too many(>20), which would be a bad visualization.
- The output for this step is a chart channel mapping list. e.g.{"step_4": {"reasoning": "reasoning for step 4", "answer": []}}

Step 5: Add implicit data channels.
- First, check if all obligatory chart channels defined in step 4 are filled with columns. If not, you need to complete the obligatory chart channels with additional columns from data table.
- Second, if there are optional chart channles defined in step 4 for the specific chart type, you need to think all possible conbinations of optional channels. 
- Special Note: 
-- Aggregation 'count' can be considered as a special computed data column to fill in Quantitative (Q) channel, so it should be considered in this step at proper cases.
-- Sorting is mapped to chart encoding channels rather than fields. For example, from step 2, a transformation like sort {"field": "price", "sort": "ascending"} when mapped to a bar chart becomes {"x":{"field": "product", "sort": "y"}, "y":{"field":"price"}}. This means the x-axis (showing products) is sorted according to the y-values in ascending order, where y represents price. Similarly, {"field": "price", "sort": "descending"} would be mapped as {"x":{"field": "product", "sort": "-y"}, "y":{"field":"price"}}, where the minus sign indicates descending order.
- When you select additional columns to fill in the chart channels, you also need to follow the chart:[channel:type] definition and basic channel mapping feasibility mentioned in step 4.
- The answer is based on previous step 4 answer, with a possible chart channel completing. If there are no needed obligatory chart channels to complete, just output the same answer as step 4.
- The output for this step is a chart channel mapping list. e.g.{"step_5": {"reasoning": "reasoning for step 5", "answer": []}}

Step 6: Add implicit data transformation and complete chart with data filters.
- Implicit data transformation refers to the transformations are not mentioned in the NL query, but are helpful to generate valid chart.
- First, add implicit transformation following basic feasibility rules (if needed): 
-- For bar chart, if x is a quantitative column with too many numbers (>20), x should be binned.
-- For bar chart, if x have duplicated values or x is binned, then y should be aggregated.
-- (Other feasibility rules you think properly)
- Second, add data filter from step 1 (if exists) to complete the final chart list. Please recommend 1 to 5 different charts corresponding for the ambiguous/incomplete NL Query. 
- The output for this step is a chart list. e.g.{"step_6": {"reasoning": "reasoning for step 6", "answer": [{vega chart 1}, {vega chart 2}, ...]}}
--Here are some examples of Vega-Lite Chart: (mark can be bar, line, arc, point, rect, boxplot)
--- e.g.1 a bar chart with average sale number over binned price, bin num is 10, filter by date > year 2000: {"mark": "bar", "encoding": {"x": {"field": "price", "bin": {"maxbins":10}}, "y": {"field": "sale_number", "aggregate": "mean"}}, "transform": [{"filter": {"field": "date", "gte": {"year": 2000}}}]}
--- e.g.2 a pie chart with average price over area, filter by product type is notebook or pencil: {"mark": "arc", "encoding": {"color": {"field": "area"}, "theta": {"field": "price", "aggregate": "mean"}}, "transform": [{"filter": {"field": "product_type", "oneOf": ["notebook", "pencil"]}}]}
--- e.g.3 a heatmap with date on x (binned by year), area on y, sum of sale number on color, filter by 120 <= price <= 200: {"mark": "rect", "encoding": {"x": {"field": "date", "timeUnit": "year"}, "y": {"field": "area"}, "color": {"field": "sale_number", "aggregate": "sum"}}, "transform": [{"filter": {"field": "price", "range": [120, 200]}}]} 
--- e.g.4 a line chart showing the count of products over product categories, filter by date < year 2000, and sort by the count of products in descending order: {"mark": "line", "encoding": {"x": {"field": "product", "sort": "-y"}, "y": {"aggregate": "count"}}, "transform": [{"filter": {"field": "date", "lte": {"year": 2000}}}]}

"""

simple_prompt= """You are a good data visualization expert. Given an ambiguous/incomplete Natural Language Query, a Data Table, your task is to to generate 1 to 5 different visualization charts corresponding for the ambiguous/incomplete NL Query. Please think step by step.
# Instructions:
Step 1: Extract Data Columns and Filters from NL Query.
- First, identify the relevant columns (fields) mentioned in the NL query. 
- Second, identify the data filters (conditions) mentioned in the NL query if they exist. Otherwise, leave the filter answer as empty list.

Step 2: Extract Data Transformation from NL Query. 
- Identify the data transformation mentioned in the NL Query.operations=(aggregat;bin;sort).

Step 3: Select Chart Type from NL Query. 
- Possible chart type=(bar, line, arc, point, rect, boxplot). Note that 'arc' is identical to the pie chart, and 'rect' is identical to the heatmap chart.

Step 4: Chart Channel Mapping.
- This subtask maps the selected data columns (from step 1) and data transformations (from step 2) to the chosen chart types (from step 3), assigning data to appropriate visual encoding channels. 
- Note that, there are obligatory or optional channels, follow the defination (chart:channel)=(bar:[x*,y*,color]; line:[x*,y*,color]; arc:[color*,theta*]; point:[x*,y*,color,size]; rect:[x*,y*,color*]; boxplot:[x*,y*]), where the channels with * obligatory, the channels without * are optional.
- Note: aggregation 'count' can be considered as a special computed data column to fill in Quantitative (Q) channel, and it must not include a `field`, e.g.{"x": {"field": "product"}, "y": {"aggregate": "count"}} means y is the counted row number for each product. 
- you can consider chart with or without optional channels.
- Output a chart list of all possible channel mappings.

Step 5: Add implicit data channelmapping.
- Implicit data channel mapping means if the selected data columns are not enough to complete a chart's channels, you need to complete the chart channels with additional columns from data table.
- Output a chart list of all possible channel mappings.

Step 6: Add implicit data transformation and complete chart with data filters.
- Implicit data transformation refers to the transformations are not mentioned in the NL query, but are helpful to generate valid chart. 
- First, add implicit transformation following basic feasibility rules (if needed): 
-- For bar chart, if x is a quantitative column with too many numbers (>20), x should be binned.
-- For bar chart, if x have duplicated values or x is binned, then y should be aggregated.
-- (Other feasibility rules you think properly)
- Second, add data filter from step 1 (if exists) to complete the final chart list. 
- Output a chart list of all possible channel mappings along with the filters.
--Here are some examples of Vega-Lite Chart: (mark can be bar, line, arc, point, rect, boxplot)
--- e.g.1 a bar chart with average sale number over binned price, bin num is 10, filter by date > year 2000: {"mark": "bar", "encoding": {"x": {"field": "price", "bin": {"maxbins":10}}, "y": {"field": "sale_number", "aggregate": "mean"}}, "transform": [{"filter": {"field": "date", "gte": {"year": 2000}}}]}
"""

very_simple_prompt = """You are a good data visualization expert. Given an ambiguous/incomplete Natural Language Query and a Data Table, please recommend 1 to 5 different charts corresponding for the ambiguous/incomplete NL Query. Please think step by step. 
"""

simple_step_example = """# Here is an example answer, but it is not complete, you need to fill in the reasoning process for each step. 
Your output must strictly follow the JSON format shown in this example, with "thinking_steps" and "final_output" as the root level keys.
Note that final_output should generate 1 to 5 different visualization charts to cover the possible answer space for ambiguous/incomplete NL Query. Try to explore different combinations of channels and transformations to provide diverse and meaningful visualizations:
## INPUT:\nData Schema: ['player_id', 'birth_year', 'birth_month', 'birth_day', 'birth_country', 'birth_state', 'birth_city', 'death_year', 'death_month', 'death_day', 'death_country', 'death_state', 'death_city', 'weight', 'height']\nValue Example: {'player_id': ['aardsda01', 'muirjo01', 'zychto01'], 'birth_year': ['1970-01-01 00:00:00.000001820', '1970-01-01 00:00:00.000001955', '1970-01-01 00:00:00.000001995'], 'birth_month': ['1970-01-01 00:00:00.000000001', '1970-01-01 00:00:00.000000004', '1970-01-01 00:00:00.000000012'], 'birth_day': [1.0, 17.0, 31.0], 'birth_country': ['Afghanistan', 'Belize', 'Viet Nam'], 'birth_state': ['AB', 'Dodescanese Isl.', 'Zulia'], 'birth_city': ['Aberdeen', 'Childress', 'Zion'], 'death_year': ['1970-01-01 00:00:00.000001872', '1970-01-01 00:00:00.000001923', '1970-01-01 00:00:00.000002016'], 'death_month': ['1970-01-01 00:00:00.000000001', '1970-01-01 00:00:00.000000009', '1970-01-01 00:00:00.000000012'], 'death_day': [1.0, 29.0, 31.0], 'death_country': ['American Samoa', 'Cuba', 'Venezuela'], 'death_state': ['AB', 'TN', 'Zulia'], 'death_city': ['Aberdeen', 'Albemarle', 'Zimmerman'], 'weight': [65.0, 206.0, 320.0], 'height': [43.0, 67.0, 83.0]}\nUnique Value Num: {'player_id': 18846, 'birth_year': 165, 'birth_month': 12, 'birth_day': 31, 'birth_country': 52, 'birth_state': 245, 'birth_city': 4713, 'death_year': 145, 'death_month': 12, 'death_day': 31, 'death_country': 23, 'death_state': 92, 'death_city': 2553, 'weight': 131, 'height': 22}\nNL Query: Please mark a scatter plot with columns for birth day, birth city, and day, aggregating the sum of the day while filtering for birth city within Neath, Farnhamville, and Tunstall, and filtering for death day less than or equal to 25.0.
## output:```json
{
    "thining_steps":"You fill in the reasoning process for each step.",
    "final_output": [
        {
            "mark": "point",
            "encoding": {
                "x": {"field": "birth_day"},
                "color": {"field": "birth_city"},
                "size": {"field": "death_day", "aggregate": "sum"},
                "y": {"field": "height"}
            },
            "transform": [
                {"filter": {"field": "birth_city", "oneOf": ["Neath", "Farnhamville", "Tunstall"]}},
                {"filter": {"field": "death_day", "lte": 25.0}}
            ]
        },
        {
            "mark": "point",
            "encoding": {
                "x": {"field": "birth_day"},
                "color": {"field": "birth_city"},
                "size": {"field": "death_day", "aggregate": "sum"},
                "y": {"field": "weight"}
            },
            "transform": [
                {"filter": {"field": "birth_city", "oneOf": ["Neath", "Farnhamville", "Tunstall"]}},
                {"filter": {"field": "death_day", "lte": 25.0}}
            ]
        }
    ]
}```
"""


vega_example = """#Here are some examples of Vega-Lite Chart: (mark can be bar, line, arc, point, rect, boxplot)
--- e.g.1 a bar chart with average sale number over binned price, bin num is 10, filter by date > year 2000: {"mark": "bar", "encoding": {"x": {"field": "price", "bin": {"maxbins":10}}, "y": {"field": "sale_number", "aggregate": "mean"}}, "transform": [{"filter": {"field": "date", "gte": {"year": 2000}}}]}
--- e.g.2 a pie chart with average price over area, filter by product type is notebook or pencil: {"mark": "arc", "encoding": {"color": {"field": "area"}, "theta": {"field": "price", "aggregate": "mean"}}, "transform": [{"filter": {"field": "product_type", "oneOf": ["notebook", "pencil"]}}]}
--- e.g.3 a heatmap with date on x (binned by year), area on y, sum of sale number on color, filter by 120 <= price <= 200: {"mark": "rect", "encoding": {"x": {"field": "date", "timeUnit": "year"}, "y": {"field": "area"}, "color": {"field": "sale_number", "aggregate": "sum"}}, "transform": [{"filter": {"field": "price", "range": [120, 200]}}]} 
--- e.g.4 a line chart showing the count of products over product categories, filter by date < year 2000, and sort by the count of products in descending order: {"mark": "line", "encoding": {"x": {"field": "product", "sort": "-y"}, "y": {"aggregate": "count"}}, "transform": [{"filter": {"field": "date", "lte": {"year": 2000}}}]}
"""

step_example = """
# Here is an example of step-level answer, but it is not complete, you need to fill in the reasoning and answer for each step:
## INPUT:\nData Schema: ['player_id', 'birth_year', 'birth_month', 'birth_day', 'birth_country', 'birth_state', 'birth_city', 'death_year', 'death_month', 'death_day', 'death_country', 'death_state', 'death_city', 'weight', 'height']\nValue Example: {'player_id': ['aardsda01', 'muirjo01', 'zychto01'], 'birth_year': ['1970-01-01 00:00:00.000001820', '1970-01-01 00:00:00.000001955', '1970-01-01 00:00:00.000001995'], 'birth_month': ['1970-01-01 00:00:00.000000001', '1970-01-01 00:00:00.000000004', '1970-01-01 00:00:00.000000012'], 'birth_day': [1.0, 17.0, 31.0], 'birth_country': ['Afghanistan', 'Belize', 'Viet Nam'], 'birth_state': ['AB', 'Dodescanese Isl.', 'Zulia'], 'birth_city': ['Aberdeen', 'Childress', 'Zion'], 'death_year': ['1970-01-01 00:00:00.000001872', '1970-01-01 00:00:00.000001923', '1970-01-01 00:00:00.000002016'], 'death_month': ['1970-01-01 00:00:00.000000001', '1970-01-01 00:00:00.000000009', '1970-01-01 00:00:00.000000012'], 'death_day': [1.0, 29.0, 31.0], 'death_country': ['American Samoa', 'Cuba', 'Venezuela'], 'death_state': ['AB', 'TN', 'Zulia'], 'death_city': ['Aberdeen', 'Albemarle', 'Zimmerman'], 'weight': [65.0, 206.0, 320.0], 'height': [43.0, 67.0, 83.0]}\nUnique Value Num: {'player_id': 18846, 'birth_year': 165, 'birth_month': 12, 'birth_day': 31, 'birth_country': 52, 'birth_state': 245, 'birth_city': 4713, 'death_year': 145, 'death_month': 12, 'death_day': 31, 'death_country': 23, 'death_state': 92, 'death_city': 2553, 'weight': 131, 'height': 22}\nNL Query: Please mark a scatter plot with columns for birth day, birth city, and day, aggregating the sum of the day while filtering for birth city within Neath, Farnhamville, and Tunstall, and filtering for death day less than or equal to 25.0.
## output:```json
{
    "step_1": {
        "reasoning": "...",
        "answer": {
            "column_list": [
                {"field": "birth_day", "ambiguous": false},
                {"field": "birth_city", "ambiguous": false},
                {"field": ["birth_day", "death_day"], "ambiguous": true},
                {"field": "death_day", "ambiguous": false}
            ],
            "filter_list": [
                {"field": "birth_city", "oneOf": ["Neath", "Farnhamville", "Tunstall"]},
                {"field": "death_day", "lte": 25.0}
            ]
        },
    "step_2": {
        "reasoning": "...",
        "answer": [{"field": ["birth_day", "death_day"], "aggregate": "sum"}]
    },
    "step_3": {
        "reasoning": "...",
        "answer": ["point"]
    },
    "step_4": {
        "reasoning": "...",
        "answer": [{
            "mark": "point",
            "encoding": {
                "x": {"field": "birth_day"},
                "color": {"field": "birth_city"},
                "size": {"field": "death_day", "aggregate": "sum"}
            }
        ]
    },
    "step_5": {
        "reasoning": "...",
        "answer": [
            {
                "mark": "point",
                "encoding": {
                    "x": {"field": "birth_day"},
                    "color": {"field": "birth_city"},
                    "size": {"field": "death_day", "aggregate": "sum"},
                    "y": {"field": "height"}
                }
            },
            {
                "mark": "point",
                "encoding": {
                    "x": {"field": "birth_day"},
                    "color": {"field": "birth_city"},
                    "size": {"field": "death_day", "aggregate": "sum"},
                    "y": {"field": "weight"}
                }
            }
        ]
    },
    "step_6": {
        "reasoning": "...",
        "answer": [
            {
                "mark": "point",
                "encoding": {
                    "x": {"field": "birth_day"},
                    "color": {"field": "birth_city"},
                    "size": {"field": "death_day", "aggregate": "sum"},
                    "y": {"field": "height"}
                },
                "transform": [
                    {"filter": {"field": "birth_city", "oneOf": ["Neath", "Farnhamville", "Tunstall"]}},
                    {"filter": {"field": "death_day", "lte": 25.0}}
                ]
            },
            {
                "mark": "point",
                "encoding": {
                    "x": {"field": "birth_day"},
                    "color": {"field": "birth_city"},
                    "size": {"field": "death_day", "aggregate": "sum"},
                    "y": {"field": "weight"}
                },
                "transform": [
                    {"filter": {"field": "birth_city", "oneOf": ["Neath", "Farnhamville", "Tunstall"]}},
                    {"filter": {"field": "death_day", "lte": 25.0}}
                ]
            }
        ]
    }
}```
"""
# print(prompt)
# exit()


# 输入 sys_content + prompt + example_vl + input
# 输出 result

input = "\n#INPUT:\nData Schema: ['invoice_number', 'order_id', 'invoice_date']\nValue Example: {'invoice_number': [1, 5, 15], 'order_id': [3, 10, 14], 'invoice_date': ['2018-02-28 19:01:06', '2018-03-19 22:38:10', '2018-03-23 04:59:28']}\nNL Query: I want to display a scatter plot of invoice_number.\n"
#input = "\n#INPUT:\nData Schema: ['employeeid', 'name', 'position', 'registered', 'ssn']\nValue Example: {'employeeid': [101, 102, 103], 'name': ['Carla Espinosa', 'Laverne Roberts', 'Paul Flowers'], 'position': ['Head Nurse', 'Nurse'], 'registered': [0, 1], 'ssn': [111111110, 222222220, 333333330]}\nUnique Value Num: {'employeeid': 3, 'name': 3, 'position': 2, 'registered': 2, 'ssn': 3}\nNL Query: How can I create a pie chart using ssn?\n"
#input = "\n#INPUT:\nData Schema: ['customer_event_id', 'customer_id', 'date_moved_in', 'property_id', 'resident_id', 'thing_id']\nValue Example: {'customer_event_id': [70, 606, 817], 'customer_id': [4, 16, 91], 'date_moved_in': ['2015-03-27 12:00:00', '2016-09-27 12:00:00'], 'property_id': [107, 748, 954], 'resident_id': [10, 23, 88], 'thing_id': [1, 46, 92]}\nUnique Value Num: {'customer_event_id': 13, 'customer_id': 8, 'date_moved_in': 2, 'property_id': 10, 'resident_id': 13, 'thing_id': 9}\nNL Query: I want to display the resident_id and thing_id.\n"
        
#input = "\n#INPUT:\nData Schema: ['year', 'team_id', 'league_id', 'player_id', 'g_all', 'gs', 'g_batting', 'g_defense', 'g_p', 'g_c', 'g_1b', 'g_2b', 'g_3b', 'g_ss', 'g_lf', 'g_cf', 'g_rf', 'g_of', 'g_dh', 'g_ph', 'g_pr']\nValue Example: {'year': ['1970-01-01 00:00:00.000001871', '1970-01-01 00:00:00.000001933', '1970-01-01 00:00:00.000002015'], 'team_id': ['ALT', 'ANA', 'WSU'], 'league_id': ['AA', 'AL', 'UA'], 'player_id': ['aardsda01', 'watkibo01', 'zychto01'], 'g_all': [0.0, 75.0, 165.0], 'gs': [0.0, 159.0, 163.0], 'g_batting': [0, 17, 165], 'g_defense': [0.0, 151.0, 165.0], 'g_p': [0, 52, 106], 'g_c': [0, 25, 160], 'g_1b': [0, 120, 162], 'g_2b': [0, 106, 163], 'g_3b': [0, 73, 164], 'g_ss': [0, 85, 165], 'g_lf': [0, 53, 163], 'g_cf': [0, 62, 162], 'g_rf': [0, 41, 162], 'g_of': [0, 145, 164], 'g_dh': [0.0, 120.0, 162.0], 'g_ph': [0.0, 49.0, 95.0], 'g_pr': [0.0, 74.0, 92.0]}\nUnique Value Num: {'year': 145, 'team_id': 151, 'league_id': 7, 'player_id': 18660, 'g_all': 166, 'gs': 164, 'g_batting': 166, 'g_defense': 166, 'g_p': 95, 'g_c': 157, 'g_1b': 163, 'g_2b': 164, 'g_3b': 165, 'g_ss': 166, 'g_lf': 164, 'g_cf': 163, 'g_rf': 163, 'g_of': 165, 'g_dh': 157, 'g_ph': 93, 'g_pr': 49}\nNL Query: I want to mark g_lf as a pie chart.\n"
#input = "INPUT:\nData Schema: ['player_id', 'birth_year', 'birth_month', 'birth_day', 'birth_country', 'birth_state', 'birth_city', 'death_year', 'death_month', 'death_day', 'death_country', 'death_state', 'death_city', 'weight', 'height']\nValue Example: {'player_id': ['aardsda01', 'muirjo01', 'zychto01'], 'birth_year': ['1970-01-01 00:00:00.000001820', '1970-01-01 00:00:00.000001955', '1970-01-01 00:00:00.000001995'], 'birth_month': ['1970-01-01 00:00:00.000000001', '1970-01-01 00:00:00.000000004', '1970-01-01 00:00:00.000000012'], 'birth_day': [1.0, 17.0, 31.0], 'birth_country': ['Afghanistan', 'Belize', 'Viet Nam'], 'birth_state': ['AB', 'Dodescanese Isl.', 'Zulia'], 'birth_city': ['Aberdeen', 'Childress', 'Zion'], 'death_year': ['1970-01-01 00:00:00.000001872', '1970-01-01 00:00:00.000001923', '1970-01-01 00:00:00.000002016'], 'death_month': ['1970-01-01 00:00:00.000000001', '1970-01-01 00:00:00.000000009', '1970-01-01 00:00:00.000000012'], 'death_day': [1.0, 29.0, 31.0], 'death_country': ['American Samoa', 'Cuba', 'Venezuela'], 'death_state': ['AB', 'TN', 'Zulia'], 'death_city': ['Aberdeen', 'Albemarle', 'Zimmerman'], 'weight': [65.0, 206.0, 320.0], 'height': [43.0, 67.0, 83.0]}\nUnique Value Num: {'player_id': 18846, 'birth_year': 165, 'birth_month': 12, 'birth_day': 31, 'birth_country': 52, 'birth_state': 245, 'birth_city': 4713, 'death_year': 145, 'death_month': 12, 'death_day': 31, 'death_country': 23, 'death_state': 92, 'death_city': 2553, 'weight': 131, 'height': 22}\nNL Query: Please mark a scatter plot with columns for birth day, birth city, and day, aggregating the sum of the day while filtering for birth city within Neath, Farnhamville, and Tunstall, and filtering for death day less than or equal to 25.0."  


# # evaluate
# combined_input = sys_content + simple_prompt + simple_step_example + input
# print(combined_input)
# #print(combined_input)
# result = call_qwen(combined_input)
# print(result)


# # 提取 JSON 字符串
# json_result = result[0].split('```json\n')[1].split('```')[0].strip()  # 提取 JSON 部分
# json_result = json.loads(json_result)
# # # 将单引号替换为双引号
# # # json_result = json_result.replace("'", '"')
# # # # 使用 ast.literal_eval 解析 JSON 字符串
# # # json_result = ast.literal_eval(json_result)
# # # json_result = normalize_string(json_result)
# print(json_result)
# print(type(json_result))

