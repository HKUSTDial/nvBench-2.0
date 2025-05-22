import json 
example ={"input": "\n#INPUT:\nData Schema: ['invoice_number', 'order_id', 'invoice_date']\nValue Example: {'invoice_number': [1, 5, 15], 'order_id': [3, 10, 14], 'invoice_date': ['2018-02-28 19:01:06', '2018-03-19 22:38:10', '2018-03-23 04:59:28']}\nNL Query: I want to display a scatter plot of invoice_number.\n",
        "output": [
            {
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
        ],
        "action_list": [
            "mark scatter",
            "column invoice_number"
        ],
        "nl_query": "I want to display a scatter plot of invoice_number.",
        "csv_file": "customers_and_invoices@invoices.csv",
        "steps": {
            "step_1": {
                "name": "step 1: data selection",
                "answer": {
                    "column_list": [
                        {
                            "field": "invoice_number",
                            "ambiguous": True
                        }
                    ],
                    "filter_list": []
                }
            },
            "step_2": {
                "name": "step 2: data transformation",
                "answer": []
            },
            "step_3": {
                "name": "step 3: chart selection",
                "answer": [
                    "point"
                ]
            },
            "step_4": {
                "name": "step 4: channel mapping",
                "answer": [
                    {
                        "mark": "point",
                        "encoding": {
                            "x": {
                                "field": "invoice_number"
                            }
                        }
                    }
                ]
            },
            "step_5": {
                "name": "step 5: chart completion",
                "answer": [
                    {
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
            }
        }
    }

sys_content = "You are an intelligent assistant. You only answer with #OUTPUT."
prompt = """You are a good data analysist. In a task of generating Vega-Lite charts based on the input natural language query, the input query might be ambiguous or vague, so at most 5 different charts can be answers to capture the ambiguity in the query.
Your task is to give reasoning process based on the step-by-step answers.
Please fill the Step by Step reasoning process.
Output Format:
#OUTPUT: 
NL Query: I want to display a scatter plot of invoice_number.
step 1: data selection
# answer: 
# reasoning:
step 2: data transformation
# answer: 
# reasoning:
step 3: chart selection
# answer: 
# reasoning:
step 4: channel mapping
# answer: 
# reasoning:
step 5: chart completion
# answer: 
# reasoning:
"""


example_input = prompt + example["input"]
for step, step_dict in example["steps"].items():
    example_input += step_dict["name"] + "\n"
    example_input += "# answer: "
    example_input += json.dumps(step_dict["answer"])
    example_input += "\n"

print(example_input)