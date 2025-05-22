from gpt_call import call_gpt_3_5, call_deepseek_r1_official, call_qwen
import ast

sys_content = "You are an intelligent assistant. You only answer with #OUTPUT."
prompt = """You are a good data visualization expert. Given an ambiguous/incomplete Natural Language Query and a Data Table, please recommend 1 to 5 different charts corresponding for the ambiguous/incomplete NL Query. Ensure the following constraints are respected:
# Output format(JSON array): \n#OUTPUT:[\n{vega chart 1},\n{vega chart 2},\n ...]
# Each Vega chart must only include the following three keys(mark, encoding, transform):
## mark (chart type)
- Possible chart type=(bar, line, arc, point, rect, boxplot). Note that 'arc' is identical to the pie chart, and 'rect' is identical to the heatmap chart.
- If the NL Query mentions one exact chart type, select the single chart type.
- Else if the NL Query does not mention the chart type, but indicate a data analysis task in (trend;distribution;correlation), infer the possible chart types by (task:chart)=(trend:[bar,line]; distribution:[bar,arc,line,boxplot]; correlation:[point,heatmap]).
- Otherwise, when no hints for chart type are mentioned in the NL query, all chart types are possible.
## encoding (with only `field`, `aggregate`, `sort`, `bin` and `timeUnit` within the channels in the encoding)
- Note that, there are obligatory or optional channels, follow the defination (chart:channel)=(bar:[x*,y*,color]; line:[x*,y*,color]; arc:[color*,theta*]; point:[x*,y*,color,size]; rect:[x*,y*,color*]; boxplot:[x*,y*]), where the channels with * obligatory, the channels without * are optional.
- In the encoding channels, you can use `field` to Refer the column name in the data table, e.g., {"x":{"field": "sales"}}.
- In the encoding channels, you can use three kind of operations=(aggregat;bin;sort):
-- `aggregate`: Includes three types: 'sum', 'mean', 'count'.
--- e.g., {"field": "price","aggregate": "mean"} means compute the average price.
--- e.g., {"field": "price","aggregate": "sum"} means compute the total price.
--- For `count`, it is treated as a special computed column, which will occupy a Quantitative (Q) channel, and it must not include a `field`. e.g., {"x": {"field": "product"}, "y": {"aggregate": "count"}} means the y-axis will represent the count of rows for each product.
-- `sort`: If sort is explicitly requested in the NL query, `sort` should be done within the encoding using channels like `x`, `-x`, `y`, `-y`, `theta`, or `-theta`. 
--- e.g., {"x":{"field": "product", "sort": "y"}, "y":{"field":"price"}}. This means the x-axis (showing products) is sorted according to the y-values in ascending order, where y represents price.
--- e.g., {"theta":{"field": "price"}, "color":{"field":"product", "sort": "-theta"}} menas the color (showing products) is sorted according to the theta-values in descending order.
-- `bin`: Used for  Quantitative Columns indicating the binned size.
--- e.g. {"field": "price", "bin": {"maxbins": 10}}, which means the price will be grouped to 10 bins. 
--- Bin operation on Temporal Columns is called the timeUnit, e.g. {"field": "date", "timeUnit": "year"}, which means unit(bin) the date by year.
- Note that there may be none, one, or more operations in the NL query.
## transform
- The `transform` field should only include `filter` if explicitly mentioned in the NL query. Otherwise, omit the `transform` in vega chart.
- e.g., if the NL query specifies filters like "price > 10" and "product is either pen or paper", the transform will look like this: "transform": [{"filter":  {"field": "price", "gte": 10}}, {"filter":  {"field": "product", "oneof": [pen, paper]}}] 
- Note that there may be none, one, or more filter in the NL query."""

simple_prompt = """You are a good data visualization expert. Given an ambiguous/incomplete Natural Language Query and a Data Table, please recommend 1 to 5 different charts corresponding for the ambiguous/incomplete NL Query. Ensure to strictly follow the output format.
# Output format(JSON array): \n#OUTPUT:[\n{vega chart 1},\n{vega chart 2},\n ...]\n"""

# example vegalite
example_vl = """# EXAMPLE Vega-Lite Chart: (mark can be bar, line, arc, point, rect, boxplot)
## e.g.1 a bar chart with average sale number over binned price, bin num is 10, filter by date > year 2000.
- {"mark": "bar", "encoding": {"x": {"field": "price", "bin": {"maxbins":10}}, "y": {"field": "sale_number", "aggregate": "mean"}}, "transform": [{"filter": {"field": "date", "gte": {"year": 2000}}}]}
## e.g.2 a pie chart with average price over area, filter by product type is notebook or pencil.
- {"mark": "arc", "encoding": {"color": {"field": "area"}, "theta": {"field": "price", "aggregate": "mean"}}, "transform": [{"filter": {"field": "product_type", "oneOf": ["notebook", "pencil"]}}]}
## e.g.3 a heatmap with date on x (binned by year), area on y, sum of sale number on color, filter by 120 <= price <= 200.
- {"mark": "rect", "encoding": {"x": {"field": "date", "timeUnit": "year"}, "y": {"field": "area"}, "color": {"field": "sale_number", "aggregate": "sum"}}, "transform": [{"filter": {"field": "price", "range": [120, 200]}}]} 
## e.g.4 a line chart showing the count of products over product categories, filter by date < year 2000, and sort by the count of products in descending order.
- {"mark": "line", "encoding": {"x": {"field": "product", "sort": "-y"}, "y": {"aggregate": "count"}}, "transform": [{"filter": {"field": "date", "lte": {"year": 2000}}}]}
"""
example_vl_bar = """# EXAMPLE Vega-Lite Chart: (mark can be bar, line, arc, point, rect, boxplot)
## e.g.1 a bar chart with average sale number over binned price, bin num is 10, filter by date > year 2000.
- {"mark": "bar", "encoding": {"x": {"field": "price", "bin": {"maxbins":10}}, "y": {"field": "sale_number", "aggregate": "mean"}}, "transform": [{"filter": {"field": "date", "gte": {"year": 2000}}}]}
"""


# 输入 sys_content + prompt + example_vl + input
# 输出 result
input = "\n#INPUT:\nData Schema: ['student_course_id', 'course_id', 'student_enrolment_id']\nValue Example: {'student_course_id': [0, 9860, 83814225], 'course_id': [2, 10, 14], 'student_enrolment_id': [2, 9, 14]}\nUnique Value Num: {'student_course_id': 15, 'course_id': 10, 'student_enrolment_id': 9}\nNL Query: Show a line chart for course_id.\n"

#input = "\n#INPUT:\nData Schema: ['invoice_number', 'order_id', 'invoice_date']\nValue Example: {'invoice_number': [1, 5, 15], 'order_id': [3, 10, 14], 'invoice_date': ['2018-02-28 19:01:06', '2018-03-19 22:38:10', '2018-03-23 04:59:28']}\nNL Query: I want to display a scatter plot of invoice_number.\n"
output = [{
                "mark": "point",
                "encoding": {
                    "x": {
                        "field": "invoice_number"
                    },
                    "y": {
                        "field": "order_id"
                    }
                }
            },
            {
                "mark": "point",
                "encoding": {
                    "x": {
                        "field": "invoice_number"
                    },
                    "size": {
                        "aggregate": "count"
                    },
                    "y": {
                        "field": "order_id"
                    }
                }
            },
            {
                "mark": "point",
                "encoding": {
                    "x": {
                        "field": "invoice_number"
                    },
                    "color": {
                        "field": "invoice_date"
                    },
                    "size": {
                        "aggregate": "count"
                    },
                    "y": {
                        "field": "order_id"
                    }
                }
            },
            {
                "mark": "point",
                "encoding": {
                    "x": {
                        "field": "invoice_number"
                    },
                    "color": {
                        "field": "invoice_date"
                    },
                    "y": {
                        "field": "order_id"
                    }
                }
            }
        ]

# evaluate
combined_input = sys_content + simple_prompt + example_vl + input
result = call_qwen(combined_input)
result = result[0].split("#OUTPUT:")[1]
print(result)
