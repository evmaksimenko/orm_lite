import logging
import re

logging.basicConfig(level=logging.DEBUG)


def _clear_str(s):
    return ''.join([c for c in s if c not in '\\;"\'\n'])


class BaseCol():
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.type = kwargs.get('type', None)
        self.is_required = kwargs.get('required', False)
        self.is_pk = kwargs.get('pk', False)
        if self.is_pk:
            self.is_required = True
        self.is_fk = kwargs.get('fk', False)
        self.fk_ref_table = kwargs.get('fk_table', None)
        self.fk_ref_col = kwargs.get('fk_col', None)

    def name_to_create(self):
        s = '{} {}'.format(self.name, self.type)
        if self.is_pk:
            s = s + ' PRIMARY KEY'
        if self.is_required:
            s = s + ' NOT NULL'
        if self.is_fk:
            s = s + ',\nFOREIGN KEY ({}) REFERENCES {}({})'.format(
                self.name, self.fk_ref_table, self.fk_ref_col)
        return s


class Base():
    connection = None
    table_cols = None
    is_values_passed = False
    is_all_required = False
    parse_error = False
    values_list = []

    def _get_table_name(self):
        table_name = self.__class__.__dict__.get('__tablename__', None)
        return table_name

    def _get_table_cols(self):
        return [x for x in self.__class__.__dict__.keys()
                if not x.startswith('__')]

    def _check_tablename_connection(self):
        if not self._get_table_name() or not self.connection:
            print('__tablename__ or connection missed')
            return False
        return True

    def _parse_table_cols(self):
        if self.table_cols:
            return
        self.table_cols = []
        for col_name in self._get_table_cols():
            param = self.__class__.__dict__.get(col_name)
            col_req = False
            col_pk = False
            col_fk = False
            col_fk_table = None
            col_fk_col = None

            if len(param) == 0:
                continue
            col_type = _clear_str(param[0])
            if len(param) == 2:
                if param[1] == 'pk':
                    col_pk = True
                elif param[1] == 'required':
                    col_req = True
            elif len(param) > 2:
                if param[1] == 'fk' and ('.' in param[2]):
                    col_fk = True
                    col_fk_table = _clear_str((param[2]).split('.')[0])
                    col_fk_col = _clear_str((param[2]).split('.')[1])
            col = BaseCol(name=col_name, type=col_type, required=col_req,
                          pk=col_pk, fk=col_fk, fk_table=col_fk_table,
                          fk_col=col_fk_col)
            self.table_cols.append(col)

    def _filter_kwargs(self, **kwargs):
        str_type = [r'^TEXT$', r'^VARCHAR\(\d+\)$', r'^CHAR\(\d+\)$']
        is_values_passed = False
        values_list = []
        parse_error = False
        for col in self.table_cols:
            if col.name in kwargs.keys():
                value = None
                if col.type.upper() == 'INT':
                    try:
                        value = int(kwargs[col.name])
                    except ValueError:
                        print('Incorrect value type for {}({})'.format(
                            col.name, col.type))
                        parse_error = True
                        return
                    value = kwargs[col.name]
                else:
                    str_type_found = False
                    for s in str_type:
                        match = re.search(s, col.type.upper())
                        if match is not None:
                            str_type_found = True
                            value = "'" + str(kwargs[col.name]) + "'"
                            break
                    if not str_type_found:
                        print('Unrecognized type {}'.format(col.type))
                        parse_error = True
                        return

                values_list.append((col.name, value))
                is_values_passed = True
        is_all_required = True
        fln = [c[0] for c in values_list]
        for col in self.table_cols:
            if col.is_required and col.name not in fln:
                is_all_required = False
        return is_values_passed, values_list[:], is_all_required, \
            parse_error

    def _execute_sql(self, sql_stmt, error_msg):
        cur = self.connection.cursor()
        try:
            cur.execute(sql_stmt)
            self.connection.commit()
        except Exception as err:
            print('Error SQL query executing: {}'.format(error_msg))
            print(err)
        cur.close()

    def _execute_sql_with_result(self, sql_stmt, error_msg):
        cur = self.connection.cursor()
        res = None
        try:
            cur.execute(sql_stmt)
            res = cur.fetchall()
        except Exception as err:
            print('Error SQL query executing: {}'.format(error_msg))
            print(err)
        cur.close()
        return res

    def _set_conn_and_parse(self, **kwargs):
        self.connection = kwargs.get('connection', self.connection)
        self._parse_table_cols()
        self.is_values_passed, self.values_list, self.is_all_required, \
            self.parse_error = self._filter_kwargs(**kwargs)

    def __call__(self, **kwargs):
        self._set_conn_and_parse(**kwargs)
        return self

    def __init__(self, **kwargs):
        self._set_conn_and_parse(**kwargs)

    def add(self):
        if not self._check_tablename_connection():
            return
        if not self.is_all_required:
            print('Required fields missed')
            return
        if self.parse_error:
            print('Value parsing error')
            return
        cols = ', '.join(c[0] for c in self.values_list)
        values = ', '.join(str(c[1]) for c in self.values_list)
        sql_stmt = 'INSERT INTO {} ({}) VALUES ({});'.format(
            self._get_table_name(), cols, values)
        self._execute_sql(sql_stmt, 'add')

    def update(self, **kwargs):
        upd_is_values_passed, upd_values_list, upd_is_all_required, \
            upd_parse_error = self._filter_kwargs(**kwargs)
        if not upd_is_values_passed:
            print('Nothing to update')
            return
        if upd_parse_error or self.parse_error:
            print('Values parsing error')
            return
        if upd_values_list:
            upd_args = ', '.join(c[0] + " = " + str(c[1])
                                 for c in upd_values_list)
            sql_stmt = 'UPDATE {} SET {}'.format(
                self._get_table_name(), upd_args)
            if self.values_list:
                cond_args = ' AND '.join(c[0] + " = " + str(c[1])
                                         for c in self.values_list)
                sql_stmt += ' WHERE {}'.format(cond_args)
            sql_stmt += ';'
            self._execute_sql(sql_stmt, 'update')

    def delete(self):
        if not self._check_tablename_connection():
            return
        if self.parse_error:
            print('Value parsing error')
            return
        table_name = self._get_table_name()
        if not self.values_list:
            sql_stmt = 'DELETE FROM {};'.format(table_name)
        else:
            args = ', '.join(c[0] + '=' + str(c[1]) for c in self.values_list)
            sql_stmt = 'DELETE FROM {} WHERE {};'.format(table_name, args)
        self._execute_sql(sql_stmt, 'delete')

    def is_exists(self):
        if not self._check_tablename_connection():
            return
        table_name = self._get_table_name()
        sql_stmt = "SELECT name FROM sqlite_master WHERE name = '{}';".format(
            table_name)
        return self._execute_sql_with_result(sql_stmt, 'is_exists') != []

    def create(self):
        if not self._check_tablename_connection():
            return
        table_name = self._get_table_name()
        argstr = ', '.join(c.name_to_create() for c in self.table_cols)
        sql_stmt = 'CREATE TABLE IF NOT EXISTS {} ({});'.format(
            table_name, argstr)
        self._execute_sql(sql_stmt, 'create')

    def drop(self):
        if not self._check_tablename_connection():
            return
        table_name = self._get_table_name()
        sql_stmt = 'DROP TABLE IF EXISTS {};'.format(table_name)
        self._execute_sql(sql_stmt, 'drop')

    def select_all(self, select_cols='*'):
        if not self._check_tablename_connection():
            return
        sql_stmt = 'SELECT {} FROM {}'.format(
            select_cols, self._get_table_name())
        table_join = ''
        for col in self.table_cols:
            if col.is_fk:
                table_join += ' INNER JOIN {} ON {}.{}={}.{}'.format(
                    col.fk_ref_table, col.fk_ref_table, col.fk_ref_col,
                    self._get_table_name(), col.name)
        sql_stmt += table_join
        if self.is_values_passed:
            args = ', '.join(c[0] + '=' + str(c[1]) for c in self.values_list)
            sql_stmt += ' WHERE {}'.format(args)
        sql_stmt += ';'
        return self._execute_sql_with_result(sql_stmt, 'select_all')

    def select(self, *args):
        if not args:
            return self.select_all()
        else:
            cols_arg = []
            for arg in args:
                if '.' in arg:
                    cols_arg.append(arg)
                else:
                    cols_arg.append(self._get_table_name() + '.' + arg)
            return self.select_all(', '.join(cols_arg))
