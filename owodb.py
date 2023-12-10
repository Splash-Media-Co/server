# owodb.py
import json
import os
from logs import Info, Warning, Debug, Error, Critical

class OwODB:
    """"Your average homie that identifies as a JSON DB."""
    def __init__(self, db_name):
        self.db_name = db_name
        self.db_path = f"{db_name}.json"
        self.data = {}
        self.load_data()

    def load_data(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as file:
                self.data = json.load(file)

    def save_data(self):
        with open(self.db_path, 'w') as file:
            json.dump(self.data, file, indent=2)

    def create_table(self, table_name, columns):
        if table_name not in self.data:
            self.data[table_name] = {'columns': columns, 'data': []}
            self.save_data()
            Info(f"Table '{table_name}' created successfully.")
        else:
            Warning(f"Table '{table_name}' already exists.")

    def insert_data(self, table_name, values):
        if table_name in self.data:
            if len(values) == len(self.data[table_name]['columns']):
                row = dict(zip(self.data[table_name]['columns'], values))
                self.data[table_name]['data'].append(row)
                self.save_data()
                Info("Data inserted successfully.")
            else:
                Error("Number of values does not match the number of columns.")
        else:
            Warning(f"Table '{table_name}' does not exist.")

    def select_data(self, table_name, conditions=None):
        if table_name in self.data:
            result = self.data[table_name]['data']
            if conditions:
                result = [row for row in result if all(row.get(col) == value for col, value in conditions.items())]
            return result
        else:
            Warning(f"Table '{table_name}' does not exist.")
            return []

    def update_data(self, table_name, set_values, conditions=None):
        if table_name in self.data:
            for row in self.data[table_name]['data']:
                if conditions and not all(row.get(col) == value for col, value in conditions.items()):
                    continue
                for col, value in set_values.items():
                    if col in row:
                        row[col] = value
            self.save_data()
            Info("Data updated successfully.")
        else:
            Warning(f"Table '{table_name}' does not exist.")

    def delete_data(self, table_name, conditions=None):
        if table_name in self.data:
            if conditions:
                self.data[table_name]['data'] = [row for row in self.data[table_name]['data']
                                                 if not all(row.get(col) == value for col, value in conditions.items())]
            else:
                self.data[table_name]['data'] = []
            self.save_data()
            Info("Data deleted successfully.")
        else:
            Warning(f"Table '{table_name}' does not exist.")
