T = "temporal"
Q = "quantitative"
C = "category"

mark_enc_type_dict_wo_none = {
    'bar': {
        'x': [Q, T, C],
        'y': [Q],
        'color': [C],
        'size': [],
        'column': [C]
    },
    'line': {
        'x': [Q, T],
        'y': [Q],
        'color': [C],
        'size': [],
        'column': [C]
    },
    # 'area': {
    #     'x': [Q, T],
    #     'y': [Q],
    #     'color': [C],
    #     'size': [],
        # 'column': [C]
    # },
    "pie": {
        'x': [],
        'y': [Q],
        'color': [C],
        'size': [],
        'column': [C]
    },
    'scatter': {
        'x': [Q],
        'y': [Q],
        'color': [C],
        'size': [Q],
        'column': [C]
    },
    'heatmap': {
        'x': [Q, T, C],
        'y': [Q, C],
        'color': [Q],
        'size': [],
        'column': [C]
    },
    'boxplot': {
        'x': [C],
        'y': [Q],
        'color': [],
        'size': [],
        'column': [C]
    }
}

none_mark = {
    'x': [], 
    'y': [],
    'color': [],
    'size': [],
    'column': [] 
}

for enc in none_mark.keys():
    for mark in mark_enc_type_dict_wo_none.keys():
        none_mark[enc] += mark_enc_type_dict_wo_none[mark][enc]
    none_mark[enc] = list(set(none_mark[enc]))

mark_enc_type_dict = mark_enc_type_dict_wo_none
mark_enc_type_dict['[NONE]'] = none_mark

# print(mark_enc_type_dict.keys())

mark_bin_dict = {
    "bar": {
        'x': [Q, T],
        'y': [],
        'color': [],
        'size': [],
        'column': []
    },
    "line": {
        'x': [Q, T],
        'y': [],
        'color': [],
        'size': [],
        'column': []
    },
    # "area": {
    #     'x': [Q, T],
    #     'y': [],
    #     'color': [],
    #     'size': [],
    #     'column': []
    # },
    "pie": {
        'x': [],
        'y': [],
        'color': [],
        'size': [],
        'column': []
    },
    "scatter": {
        'x': [],
        'y': [],
        'color': [],
        'size': [],
        'column': []
    },
    "boxplot": {
        'x': [],
        'y': [],
        'color': [],
        'size': [],
        'column': []
    },
    "heatmap": {
        'x': [Q],
        'y': [Q],
        'color': [],
        'size': [],
        'column': []
    },
    "[NONE]": {
        'x': [Q, T],
        'y': [Q],
        'color': [],
        'size': [],
        'column': []
    }
}


mark_aggregate_dict = {
    "bar": ["y"], 
    "line": ["y"],
    # "area": ["y"],
    "pie": ["y"],
    "scatter": ["size"],
    "boxplot": [],
    "heatmap": ["color"],
    "[NONE]": ["y", "color", "size"]
}

# mark_sort_dict = {
#     "bar": {
#         'x': [],
#         'y': [Q],
#         'color': [],
#         'size': [],
#         'column': []
#     },
#     "line": {
#         'x': [],
#         'y': [],
#         'color': [],
#         'size': [],
#         'column': []
#     },
#     # "area": {
#     #     'x': [],
#     #     'y': [Q],
#     #     'color': [],
#     #     'size': [],
#     #     'column': []
#     # },
#     "pie": {
#         'x': [],
#         'y': [Q],
#         'color': [],
#         'size': [],
#         'column': []
#     },
#     "scatter": {
#         'x': [],
#         'y': [],
#         'color': [],
#         'size': [],
#         'column': []
#     },
#     "boxplot": {
#         'x': [],
#         'y': [],
#         'color': [],
#         'size': [],
#         'column': []
#     },
#     "heatmap": {
#         'x': [],
#         'y': [],
#         'color': [],
#         'size': [],
#         'column': []
#     },
# }