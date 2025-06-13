import sys
import os
import unittest

# Add the parent directory (project root) to sys.path to reliably find the 'app' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.src import network_builder as nb # For building graphs for test

class TestAppCallbacksLogic(unittest.TestCase):

    def test_comparison_logic_node_sets(self):
        # Sample data (minimal, just enough to create nodes)
        sample_schema_data = [
            {"domain_name": "Domain1", "tables": [
                {"table_name": "TableA", "fields": [{"field_name": "id"}]},
                {"table_name": "TableB", "fields": [{"field_name": "id"}]},
                {"table_name": "TableC", "fields": [{"field_name": "id"}]}, # Schema only
            ]}
        ]

        sample_kpi_data = [
            {"kpi_name": "KPI1", "data_required": [
                {"table_name": "TableA"}, # Common
                {"table_name": "TableB"}  # Common
            ]},
            {"kpi_name": "KPI2", "data_required": [
                {"table_name": "TableD"}  # KPI only
            ]}
        ]

        schema_graph = nb.build_schema_network(sample_schema_data)
        kpi_graph = nb.build_kpi_network(sample_kpi_data)

        schema_nodes = set(schema_graph.nodes())
        kpi_nodes = set(kpi_graph.nodes())

        common_nodes = schema_nodes.intersection(kpi_nodes)
        schema_only_nodes = schema_nodes.difference(kpi_nodes)
        kpi_only_nodes = kpi_nodes.difference(schema_nodes)

        self.assertEqual(schema_nodes, {"TableA", "TableB", "TableC"})
        self.assertEqual(kpi_nodes, {"TableA", "TableB", "TableD"})

        self.assertEqual(common_nodes, {"TableA", "TableB"})
        self.assertEqual(len(common_nodes), 2)

        self.assertEqual(schema_only_nodes, {"TableC"})
        self.assertEqual(len(schema_only_nodes), 1)

        self.assertEqual(kpi_only_nodes, {"TableD"})
        self.assertEqual(len(kpi_only_nodes), 1)

    # More tests could be added here for other extractable logic from callbacks if any.

if __name__ == '__main__':
    unittest.main()
