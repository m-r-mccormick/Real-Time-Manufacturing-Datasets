import datetime
from typing import List

import pymysql  # pip install PyMySQL==1.1.1


class MesDriver:

    def __init__(self, host: str, database: str, user: str, password: str, port: int = None):
        if not isinstance(host, str):
            raise TypeError('host must be a string')
        self._host = host

        if not isinstance(database, str):
            raise TypeError('database must be a string')
        self._database = database

        if not isinstance(user, str):
            raise TypeError('user must be a string')
        self._user = user

        if not isinstance(password, str):
            raise TypeError('password must be a string')
        self._password = password

        if port is None:
            self._port = 3306
        if not isinstance(port, int):
            raise TypeError('port must be an integer')
        self._port = port

        self._connection: pymysql.Connection | None = None

    def connect(self):
        self._connection = pymysql.connect(
            host=self._host,
            database=self._database,
            user=self._user,
            password=self._password,
            port=self._port,
        )
        if not self.is_connected():
            raise ConnectionError('Database connection failed')

    def disconnect(self):
        self._connection.close()
        self._connection = None

    def is_connected(self):
        if self._connection is None:
            return False
        return self._connection.open
        #return self._connection.is_connected()

    def row_replace_into(self, table: str, row_id: str, row: dict):
        if not isinstance(table, str):
            raise TypeError('table must be a string')
        if not isinstance(row_id, str):
            raise TypeError('row_id must be a string')
        if not isinstance(row, dict):
            raise TypeError('row must be a Dict[str, object]')
        if not all(isinstance(k, str) for k in row.keys()):
            raise TypeError('row must be a Dict[str, object]')

        columns = list(row.keys())

        column_names = 'RowId,'
        values = f'%s,'
        data = [row_id]
        for column_name in row.keys():
            column_names += f' `{column_name}`,'
            values += f' %s,'
            col_data = row[column_name]
            if isinstance(col_data, str):
                try:
                    col_data = datetime.datetime.fromisoformat(col_data)
                except Exception as ex:
                    pass
            data.append(col_data)
        column_names = column_names.rstrip(',')
        values = values.rstrip(',')

        # INSERT INTO is used to insert new records into a table
        #   If a row with the same primary key exists, it will throw an error
        #   https://www.w3schools.com/sql/sql_insert.asp

        # sql = f"""
        #     INSERT INTO `{table}` ({column_names})
        #     VALUES ({values})
        # """

        # UPDATE is used to modify existing records in the table
        #   If the target row doesn't already exist, MySQL will execute the update
        #   without generatin an error, but no rows will be affected. This means
        #   that the command will complete successfully, but it will report that
        #   zero rows were matched and zero rows were updated
        #   https://www.w3schools.com/sql/sql_update.asp

        # REPLACE works exactly like INSERT, except that if an old row in the
        #   table has the same value as a new row for a PRIMARY KEY or a
        #   UNIQUE index, the old row is deleted before the new row is inserted.
        # https://dev.mysql.com/doc/refman/8.4/en/replace.html

        sql = f"""
            REPLACE INTO `{table}` ({column_names})
            VALUES ({values})
        """

        cursor = self._connection.cursor()
        cursor.execute(sql, data)
        if cursor.rowcount == 0:
            print(f'Could replace into table "{table}" row_id: "{row_id}"')
        else:
            print(f'Replaced into table "{table}" row_id: "{row_id}"')
        self._connection.commit()

    def row_delete(self, table: str, row_id: str):
        if not isinstance(table, str):
            raise TypeError('table must be a string')
        if not isinstance(row_id, str):
            raise TypeError('row_id must be a string')

        sql = f"DELETE FROM `{table}` WHERE RowId = '{row_id}'"

        cursor = self._connection.cursor()
        cursor.execute(sql)
        if cursor.rowcount == 0:
            print(f'Could delete from table "{table}" row_id: "{row_id}"')
        else:
            print(f'Deleted from table "{table}" row_id: "{row_id}"')
        self._connection.commit()

    def table_exists(self, name: str) -> bool:
        if not isinstance(name, str):
            raise TypeError('name must be a string')

        if not self.is_connected():
            raise Exception('Not connected to database')

        cursor = self._connection.cursor()
        cursor.execute(f"SHOW TABLES LIKE '{name}'")
        result = cursor.fetchone()
        return result is not None

    def table_drop_if_exists(self, name: str):
        if not isinstance(name, str):
            raise TypeError('name must be a string')

        cursor = self._connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {name}")
        if self.table_exists(name):
            print(f'Could not drop table: "{name}"')
        else:
            print(f'Dropped table: "{name}"')
        self._connection.commit()

    def table_create_if_doesnt_exist(self, name: str, columns: List[dict]):
        if not isinstance(name, str):
            raise TypeError('name must be a string')
        if not isinstance(columns, list):
            raise TypeError('columns must be a List[Dict[str, object]]')
        if not all(isinstance(c, dict) for c in columns):
            raise TypeError('columns must be a List[Dict[str, object]]')
        if not all(all(isinstance(k, str) for k in c.keys()) for c in columns):
            raise TypeError('columns must be a List[Dict[str, object]]')

        if not self.is_connected():
            raise Exception('Not connected to database')

        query = f'CREATE TABLE IF NOT EXISTS {name} (\n'
        query += f'RowId VARCHAR(255) PRIMARY KEY,\n'
        for column in columns:
            if 'Name' not in column:
                raise ValueError(f'Column does not contain Name')
            column_name = column['Name']
            if not isinstance(column_name, str):
                raise TypeError('column name must be a string')

            if 'Type' not in column:
                raise ValueError(f'Column {name} does not contain Type')
            column_type = column['Type']
            if not isinstance(column_type, str):
                raise TypeError('column type must be a string')

            # if 'Nullable' not in column:
            #     raise ValueError(f'Column {name} does not contain Nullable')
            # column_nullable = column['Nullable']
            # column_nullable = True
            # if not isinstance(column_nullable, bool):
            #     raise TypeError('column nullable must be a boolean')
            #
            # nullable = ''
            # if not column_nullable:
            #     nullable = 'NOT NULL'

            query += f'`{column_name}` {column_type},\n'
        # Remove the last comma
        query = query.rstrip(',\n') + '\n'
        query += ')'

        cursor = self._connection.cursor()
        cursor.execute(query)

        if not self.table_exists(name):
            print(f'Error: Could not create table: "{name}"')
        # else:
        #     print(f'Created table: "{name}"')

        #print('success')


