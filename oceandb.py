from logs import Info, Warning, Debug, Error, Critical  # noqa: F401
import sqlite3  # noqa: F401


class OceanDB:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(f"{db_name}.sqlite")
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def insert_data(self, table_name, values):
        placeholders = ",".join(["?"] * len(values))
        sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        self.cursor.execute(sql, values)
        self.commit()

    def select_data(self, table_name, conditions=None):
        query = f"SELECT * FROM {table_name}"

        if conditions:
            conditions_str = " AND ".join(
                [f"{key} = '{value}'" for key, value in conditions.items()]
            )
            query += f" WHERE {conditions_str}"

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def update_data(self, table_name, update_data, conditions=None):
        query = f"UPDATE {table_name} SET "

        # Construct the SET part of the query with the update_data dictionary
        set_values = ", ".join(
            [f"{key} = '{value}'" for key, value in update_data.items()]
        )
        query += set_values

        # Add a WHERE clause if conditions are provided
        if conditions:
            conditions_str = " AND ".join(
                [f"{key} = '{value}'" for key, value in conditions.items()]
            )
            query += f" WHERE {conditions_str}"

        # Execute the update query
        self.cursor.execute(query)
        self.commit()

    def delete_data(self, table_name, conditions=None):
        query = f"DELETE FROM {table_name}"

        # Add a WHERE clause if conditions are provided
        if conditions:
            conditions_str = " AND ".join(
                [f"{key} = '{value}'" for key, value in conditions.items()]
            )
            query += f" WHERE {conditions_str}"

        # Execute the delete query
        self.cursor.execute(query)
        self.commit()
    
    def close(self):
        self.conn.close()