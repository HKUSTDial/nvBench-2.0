import json
import os
import copy

def add_field_by_type_ambi():
    """
    Based on BIRD_metadata_w_ambiguity.json, add field_by_type_ambi to each table
    and save back to the original JSON file.
    
    The field_by_type_ambi is similar to field_by_type but includes ambiguous group names
    with the format [AMBI]groupname as additional values.
    """
    # Load the metadata with ambiguity information
    with open('BIRD_metadata_w_ambiguity.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Process each table
    for table_name, table_data in metadata.items():
        # Skip if the table doesn't have field_by_type
        if 'field_by_type' not in table_data:
            continue
        
        # Create a deep copy of field_by_type to start with
        field_by_type_ambi = copy.deepcopy(table_data['field_by_type'])

        # Rename ambiguous_columns_groups to ambiguous_pairs
        if 'ambiguous_columns_groups' in table_data:
            table_data['ambiguous_pairs'] = table_data['ambiguous_columns_groups']
            del table_data['ambiguous_columns_groups']
        
        # Add ambiguous group names if they exist
        if 'ambiguous_pairs' in table_data:
            for group_name, columns in table_data['ambiguous_pairs'].items():
                # Determine the type of the first column in the group
                # Assuming all columns in an ambiguous group have the same type
                if columns and len(columns) > 0:
                    first_col = columns[0]
                    if 'type_by_field' in table_data and first_col in table_data['type_by_field']:
                        col_type = table_data['type_by_field'][first_col]
                        # Add the ambiguous group name to the appropriate type list
                        if col_type in field_by_type_ambi:
                            field_by_type_ambi[col_type].append(f"[AMBI]{group_name}")
        
        # Add the new field_by_type_ambi to the table data
        table_data['field_by_type_ambi'] = field_by_type_ambi
    
    # Save the updated metadata back to the file
    with open('BIRD_metadata_AMBI.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print("Added field_by_type_ambi to all tables and saved to BIRD_metadata_AMBI.json")

if __name__ == "__main__":
    add_field_by_type_ambi()

# Example of the structure:
# "orchestra@show.csv": {
#     "field_list": [
#       "show_id",
#       "performance_id",
#       "if_first_show",
#       "result",
#       "attendance"
#     ],
#     "field_by_type": {
#       "temporal": [],
#       "quantitative": [
#         "attendance"
#       ],
#       "category": [
#         "show_id",
#         "performance_id",
#         "if_first_show",
#         "result"
#       ]
#     },
#     "type_by_field": {
#       "show_id": "category",
#       "performance_id": "category",
#       "if_first_show": "category",
#       "result": "category",
#       "attendance": "quantitative"
#     },
#     "field_by_type_ambi": {
#       "temporal": [],
#       "quantitative": [
#         "attendance"
#       ],
#       "category": [
#         "show_id",
#         "performance_id",
#         "if_first_show",
#         "result",
#         "[AMBI]id"
#       ]
#     },
#     "ambiguous_pairs": {
#       "id": [
#         "show_id",
#         "performance_id"
#       ]
#     },
#     "data_value_example": {