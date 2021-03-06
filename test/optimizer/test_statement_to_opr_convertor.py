# coding=utf-8
# Copyright 2018-2020 EVA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest

from mock import patch, MagicMock

from src.optimizer.statement_to_opr_convertor import StatementToPlanConvertor
from src.parser.select_statement import SelectStatement
from src.parser.table_ref import TableRef, TableInfo
from src.parser.create_udf_statement import CreateUDFStatement
from src.parser.insert_statement import InsertTableStatement
from src.parser.create_statement import CreateTableStatement
from src.parser.load_statement import LoadDataStatement


class StatementToOprTest(unittest.TestCase):
    @patch('src.optimizer.statement_to_opr_convertor.LogicalGet')
    @patch('src.optimizer.statement_to_opr_convertor.bind_dataset')
    def test_visit_table_ref_should_create_logical_get_opr(self, mock,
                                                           mock_lget):
        converter = StatementToPlanConvertor()
        table_ref = TableRef(TableInfo("test"))
        converter.visit_table_ref(table_ref)
        mock.assert_called_with(table_ref.table_info)
        mock_lget.assert_called_with(table_ref, mock.return_value)
        self.assertEqual(mock_lget.return_value, converter._plan)

    @patch('src.optimizer.statement_to_opr_convertor.LogicalGet')
    @patch('src.optimizer.statement_to_opr_convertor.bind_dataset')
    def test_visit_table_ref_populates_column_mapping(self, mock,
                                                      mock_lget):
        converter = StatementToPlanConvertor()
        converter._populate_column_map = MagicMock()
        table_ref = TableRef(TableInfo("test"))
        converter.visit_table_ref(table_ref)

        converter._populate_column_map.assert_called_with(mock.return_value)

    @patch('src.optimizer.statement_to_opr_convertor.LogicalFilter')
    @patch('src.optimizer.statement_to_opr_convertor.bind_predicate_expr')
    def test_visit_select_predicate_should_add_logical_filter(self, mock,
                                                              mock_lfilter):
        converter = StatementToPlanConvertor()
        select_predicate = MagicMock()
        converter._visit_select_predicate(select_predicate)

        mock_lfilter.assert_called_with(select_predicate)
        mock.assert_called_with(select_predicate, converter._column_map)
        mock_lfilter.return_value.append_child.assert_called()
        self.assertEqual(mock_lfilter.return_value, converter._plan)

    @patch('src.optimizer.statement_to_opr_convertor.LogicalProject')
    @patch('src.optimizer.statement_to_opr_convertor.bind_columns_expr')
    def test_visit_projection_should_add_logical_predicate(self, mock,
                                                           mock_lproject):
        converter = StatementToPlanConvertor()
        projects = MagicMock()

        converter._visit_projection(projects)

        mock_lproject.assert_called_with(projects)
        mock.assert_called_with(projects, converter._column_map)
        mock_lproject.return_value.append_child.assert_called()
        self.assertEqual(mock_lproject.return_value, converter._plan)

    def test_visit_select_should_call_appropriate_visit_methods(self):
        converter = StatementToPlanConvertor()
        converter.visit_table_ref = MagicMock()
        converter._visit_projection = MagicMock()
        converter._visit_select_predicate = MagicMock()

        statement = MagicMock()

        converter.visit_select(statement)

        converter.visit_table_ref.assert_called_with(statement.from_table)
        converter._visit_projection.assert_called_with(statement.target_list)
        converter._visit_select_predicate.assert_called_with(
            statement.where_clause)

    def test_visit_select_should_not_call_visits_for_null_values(self):
        converter = StatementToPlanConvertor()
        converter.visit_table_ref = MagicMock()
        converter._visit_projection = MagicMock()
        converter._visit_select_predicate = MagicMock()

        statement = SelectStatement()

        converter.visit_select(statement)

        converter.visit_table_ref.assert_not_called()
        converter._visit_projection.assert_not_called()
        converter._visit_select_predicate.assert_not_called()

    def test_populate_column_map_should_populate_correctly(self):
        converter = StatementToPlanConvertor()
        dataset = MagicMock()
        dataset.columns = [MagicMock() for i in range(5)]
        expected = {}
        for i, column in enumerate(dataset.columns):
            column.name = "NAME" + str(i)
            expected[column.name.lower()] = column

        converter._populate_column_map(dataset)

        self.assertEqual(converter._column_map, expected)

    @patch('src.optimizer.statement_to_opr_convertor.LogicalCreateUDF')
    @patch('src.optimizer.\
statement_to_opr_convertor.column_definition_to_udf_io')
    def test_visit_create_udf(self, mock, l_create_udf_mock):
        convertor = StatementToPlanConvertor()
        stmt = MagicMock()
        stmt.name = 'name'
        stmt.if_not_exists = True
        stmt.inputs = ['inp']
        stmt.outputs = ['out']
        stmt.impl_path = 'tmp.py'
        stmt.udf_type = 'classification'
        mock.side_effect = ['inp', 'out']
        convertor.visit_create_udf(stmt)
        mock.assert_any_call(stmt.inputs, True)
        mock.assert_any_call(stmt.outputs, False)
        l_create_udf_mock.assert_called_once()
        l_create_udf_mock.assert_called_with(
            stmt.name,
            stmt.if_not_exists,
            'inp',
            'out',
            stmt.impl_path,
            stmt.udf_type)

    def test_visit_should_call_create_udf(self):
        stmt = MagicMock(spec=CreateUDFStatement)
        convertor = StatementToPlanConvertor()
        mock = MagicMock()
        convertor.visit_create_udf = mock

        convertor.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_visit_should_call_insert(self):
        stmt = MagicMock(spec=InsertTableStatement)
        convertor = StatementToPlanConvertor()
        mock = MagicMock()
        convertor.visit_insert = mock

        convertor.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_visit_should_call_create(self):
        stmt = MagicMock(spec=CreateTableStatement)
        convertor = StatementToPlanConvertor()
        mock = MagicMock()
        convertor.visit_create = mock

        convertor.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_visit_should_call_load_data(self):
        stmt = MagicMock(spec=LoadDataStatement)
        convertor = StatementToPlanConvertor()
        mock = MagicMock()
        convertor.visit_load_data = mock

        convertor.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    @patch('src.optimizer.statement_to_opr_convertor.LogicalLoadData')
    @patch('src.optimizer.statement_to_opr_convertor.bind_dataset')
    @patch('src.optimizer.statement_to_opr_convertor.create_video_metadata')
    def test_visit_load_data_when_bind_returns_valid(
            self, mock_create, mock_bind, mock_load):
        mock_bind.return_value = MagicMock()
        table_ref = TableRef(TableInfo("test"))
        stmt = MagicMock(table=table_ref, path='path')
        StatementToPlanConvertor().visit_load_data(stmt)
        mock_bind.assert_called_once_with(table_ref.table_info)
        mock_load.assert_called_once_with(mock_bind.return_value, 'path')
        mock_create.assert_not_called()

    @patch('src.optimizer.statement_to_opr_convertor.LogicalLoadData')
    @patch('src.optimizer.statement_to_opr_convertor.bind_dataset')
    @patch('src.optimizer.statement_to_opr_convertor.create_video_metadata')
    def test_visit_load_data_when_bind_returns_None(
            self, mock_create, mock_bind, mock_load):
        mock_bind.return_value = None
        table_ref = TableRef(TableInfo("test"))
        stmt = MagicMock(table=table_ref, path='path')
        StatementToPlanConvertor().visit_load_data(stmt)
        mock_create.assert_called_once_with(table_ref.table_info.table_name)
        mock_bind.assert_called_with(table_ref.table_info)
        mock_load.assert_called_with(mock_create.return_value, 'path')
