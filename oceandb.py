import json
from logs import Info, Warning, Debug, Error, Critical  # noqa: F401
import sqlite3  # noqa: F401

class OceanDB:
    """
    A simple SQLite database wrapper for basic CRUD operations.

    Args:
        db_name (str): The name of the database.

    Attributes:
        db_name (str): The name of the database.
        conn (sqlite3.Connection): The SQLite database connection.
        cursor (sqlite3.Cursor): The database cursor.

    Methods:
        commit(): Commit the changes to the database.
        table_exists(table_name: str) -> bool: Check if a table exists in the database.
        insert_data(table_name: str, values: tuple): Insert data into the specified table.
        select_data(table_name: str, conditions: dict = None) -> list: Retrieve data from the specified table.
        update_data(table_name: str, update_data: dict, conditions: dict = None): Update data in the specified table.
        delete_data(table_name: str, conditions: dict = None): Delete data from the specified table.
        close(): Close the database connection.
        check_and_migrate_schema(json_file: str = "db.json"): Check for schema changes and migrate if needed.
        migrate_schema_and_data(new_schema: dict): Migrate schema and data.

    """

    def __init__(self, db_name: str) -> None:
        """
        Initialize the OceanDB instance.

        Args:
            db_name (str): The name of the database.
        """
        self.db_name = db_name
        self.conn = sqlite3.connect(f"{db_name}.sqlite")
        self.cursor = self.conn.cursor()
        Info(f"Connected to {db_name}.sqlite!")
        self.check_and_migrate_schema()

    def check_and_migrate_schema(self, json_file: str = "db.json"):
        """
        Check for schema changes and migrate if needed.

        Args:
            json_file (str): The path to the JSON file containing the desired schema.

        """
        # Read the current JSON schema
        with open(json_file, "r") as f:
            new_schema = json.load(f)

        # Check if the existing schema matches the JSON schema
        existing_schema = {}
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = self.cursor.fetchall()
        for table in tables:
            table_name = table[0]
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            existing_schema[table_name] = {col[1]: col[2] for col in columns}

        if existing_schema != new_schema:
            # Migrate the schema and data
            self.migrate_schema_and_data(new_schema)

    def migrate_schema_and_data(self, new_schema):
        """
        Migrate schema and data.

        Args:
            new_schema (dict): The desired schema.

        """
        for table, columns in new_schema.items():
            if not self.table_exists(table):
                # Table does not exist, create it
                sql = f"CREATE TABLE IF NOT EXISTS {table} ("
                for name, type in columns.items():
                    sql += f"{name} {type}, "
                sql = sql[:-2] + ")"
                self.cursor.execute(sql)

                # Migrate data
                self.cursor.execute(f"INSERT INTO {table} SELECT * FROM {table}_temp")
                self.cursor.execute(f"DROP TABLE IF EXISTS {table}_temp")

                self.commit()

    def commit(self) -> None:
        """
        Commit changes to the database.
        """
        self.conn.commit()

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name (str): The name of the table.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name = '{table_name}'"
        )
        return bool(self.cursor.fetchone())

    def insert_data(self, table_name: str, values: tuple) -> None:
        """
        Insert data into the specified table.

        Args:
            table_name (str): The name of the table.
            values (tuple): The values to be inserted.
        """
        placeholders = ",".join(["?" for _ in values])
        sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        self.cursor.execute(sql, values)
        self.commit()

    def select_data(self, table_name: str, conditions: dict = None) -> list:  # type: ignore
        """
        Retrieve data from the specified table.

        Args:
            table_name (str): The name of the table.
            conditions (dict): Conditions to filter the results.

        Returns:
            list: A list of tuples representing the selected data.
        """
        query = f"SELECT * FROM {table_name}"

        if conditions:
            conditions_str = " AND ".join([f"{key} = ?" for key in conditions])
            query += f" WHERE {conditions_str}"

        self.cursor.execute(query, tuple(conditions.values()) if conditions else ())
        return self.cursor.fetchall()

    def update_data(
        self,
        table_name: str,
        update_data: dict,
        conditions: dict = None,  # type: ignore
    ) -> None:
        """
        Update data in the specified table.

        Args:
            table_name (str): The name of the table.
            update_data (dict): The data to be updated.
            conditions (dict): Conditions to filter the update.

        """
        query = f"UPDATE {table_name} SET "

        set_values = ", ".join([f"{key} = ?" for key in update_data])
        query += set_values

        if conditions:
            conditions_str = " AND ".join([f"{key} = ?" for key in conditions])
            query += f" WHERE {conditions_str}"

        self.cursor.execute(
            query,
            tuple(update_data.values()) + tuple(conditions.values())
            if conditions
            else tuple(update_data.values()),
        )
        self.commit()

    def delete_data(self, table_name: str, conditions: dict = None) -> None:  # type: ignore
        """
        Delete data from the specified table.

        Args:
            table_name (str): The name of the table.
            conditions (dict): Conditions to filter the deletion.
        """
        query = f"DELETE FROM {table_name}"

        if conditions:
            conditions_str = " AND ".join([f"{key} = ?" for key in conditions])
            query += f" WHERE {conditions_str}"

        self.cursor.execute(query, tuple(conditions.values()) if conditions else ())
        self.commit()
        Warning(f"Deleted data from {table_name}")

    def close(self) -> None:
        """
        Close the database connection.
        """
        self.conn.close()
        Info(f"Closed database {self.db_name}")
