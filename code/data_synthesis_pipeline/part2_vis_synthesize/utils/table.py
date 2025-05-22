import pandas as pd
from datetime import datetime
import json
import os
import draco

T = "temporal"
Q = "quantitative"
C = "category"

default_ambi_metadata_path = "../part1.database_tables/BIRD_metadata_AMBI.json"

class TableInfo(object):
    def __init__(self, csv_path: str = None, ambi_metadata_path=default_ambi_metadata_path):
        self.csv_path = csv_path
        with open(ambi_metadata_path, 'r') as f:
            csv_metadata = json.load(f)
        # Load the CSV metadata for the given CSV path
        filename = os.path.basename(self.csv_path)
        if filename in csv_metadata:
            self.field_by_type = csv_metadata[filename]["field_by_type"]
            self.type_by_field = csv_metadata[filename]["type_by_field"]
            self.field_list = csv_metadata[filename]["field_list"]
            self.field_by_type_ambi = csv_metadata[filename]["field_by_type_ambi"]
            self.ambi_column_pairs = csv_metadata[filename]["ambiguous_pairs"]
            self.ignore_column_list = csv_metadata[filename]["ignore_column_list"]
            self.unique_value_num = csv_metadata[filename]["unique_value_num"]
        
        # self.set_data_schema()

    def get_data_schema(self, more_ignore_column_list=[]):
        # Load DataFrame from CSV path
        # print(self.csv_path)
        df = pd.read_csv(self.csv_path)
        
        # set column type
        # flag = False
        for column in self.field_list:
            if self.type_by_field[column] == T: 
                df[column] = pd.to_datetime(df[column], errors='coerce')  # set column type to datetime 64
            elif self.type_by_field[column] == C: 
                df[column] = df[column].astype(str)  # set column type to string
            # if column in more_ignore_column_list or column in self.ignore_column_list:
            #     print(more_ignore_column_list)
            #     print(self.ignore_column_list)
            #     flag = True

        df.drop(columns=self.ignore_column_list, inplace=True, errors='ignore')  # Remove columns in ignore_column_list

        df.drop(columns=more_ignore_column_list, inplace=True, errors='ignore')

        # Convert DataFrame to draco data schema
        data_schema = draco.schema_from_dataframe(df)

        # if flag:
        #     print(data_schema)
        #     exit()
        return data_schema
