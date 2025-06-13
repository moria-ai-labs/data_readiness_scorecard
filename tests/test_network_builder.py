import sys
import os
import unittest
import networkx as nx

# Add the parent directory (/app) to sys.path to find the 'app' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.src.network_builder import build_schema_network, build_kpi_network

class TestNetworkBuilder(unittest.TestCase):

    def test_build_schema_network_empty_input(self):
        graph = build_schema_network([])
        self.assertIsInstance(graph, nx.Graph)
        self.assertEqual(len(graph.nodes), 0)
        self.assertEqual(len(graph.edges), 0)

    def test_build_schema_network_single_domain_no_shared_fields(self):
        schema_data = [
            {
                "domain_name": "Sales",
                "tables": [
                    {"table_name": "Orders", "fields": [{"field_name": "order_id"}, {"field_name": "customer_id"}]},
                    {"table_name": "Products", "fields": [{"field_name": "product_id"}, {"field_name": "product_name"}]}
                ]
            }
        ]
        graph = build_schema_network(schema_data)
        self.assertIsInstance(graph, nx.Graph)
        self.assertEqual(len(graph.nodes), 2)
        self.assertIn("Orders", graph.nodes)
        self.assertIn("Products", graph.nodes)
        self.assertEqual(len(graph.edges), 0)

    def test_build_schema_network_single_domain_with_shared_fields(self):
        schema_data = [
            {
                "domain_name": "Sales",
                "tables": [
                    {"table_name": "Orders", "fields": [{"field_name": "order_id"}, {"field_name": "customer_id"}]},
                    {"table_name": "OrderItems", "fields": [{"field_name": "order_id"}, {"field_name": "product_id"}]},
                    {"table_name": "Customers", "fields": [{"field_name": "customer_id"}, {"field_name": "customer_name"}]}
                ]
            }
        ]
        graph = build_schema_network(schema_data)
        self.assertIsInstance(graph, nx.Graph)
        self.assertEqual(len(graph.nodes), 3)
        self.assertIn("Orders", graph.nodes)
        self.assertIn("OrderItems", graph.nodes)
        self.assertIn("Customers", graph.nodes)
        self.assertEqual(len(graph.edges), 2)
        self.assertTrue(graph.has_edge("Orders", "OrderItems"))
        self.assertEqual(graph["Orders"]["OrderItems"]["shared_field"], "order_id")
        self.assertTrue(graph.has_edge("Orders", "Customers"))
        self.assertEqual(graph["Orders"]["Customers"]["shared_field"], "customer_id")
        self.assertFalse(graph.has_edge("OrderItems", "Customers")) # No direct shared field in this setup

    def test_build_schema_network_multiple_domains_with_shared_fields(self):
        schema_data = [
            {
                "domain_name": "Sales",
                "tables": [
                    {"table_name": "SalesOrders", "fields": [{"field_name": "order_id"}, {"field_name": "item_id"}]},
                    {"table_name": "SalesOrderItems", "fields": [{"field_name": "order_id"}, {"field_name": "product_id"}]}
                ]
            },
            {
                "domain_name": "Inventory",
                "tables": [
                    {"table_name": "Products", "fields": [{"field_name": "product_id"}, {"field_name": "description"}]},
                    {"table_name": "StockLevels", "fields": [{"field_name": "product_id"}, {"field_name": "quantity"}]}
                ]
            }
        ]
        graph = build_schema_network(schema_data)
        self.assertEqual(len(graph.nodes), 4)
        self.assertTrue(graph.has_edge("SalesOrders", "SalesOrderItems"))
        self.assertEqual(graph["SalesOrders"]["SalesOrderItems"]["shared_field"], "order_id")
        self.assertEqual(graph["SalesOrders"]["SalesOrderItems"]["domain"], "Sales")
        self.assertTrue(graph.has_edge("Products", "StockLevels"))
        self.assertEqual(graph["Products"]["StockLevels"]["shared_field"], "product_id")
        self.assertEqual(graph["Products"]["StockLevels"]["domain"], "Inventory")
        # No edges between tables in different domains even if field names match
        self.assertFalse(graph.has_edge("SalesOrderItems", "Products"))

    def test_build_schema_network_table_with_no_fields(self):
        schema_data = [
            {
                "domain_name": "Sales",
                "tables": [
                    {"table_name": "Orders", "fields": [{"field_name": "order_id"}]},
                    {"table_name": "EmptyTable", "fields": []}
                ]
            }
        ]
        graph = build_schema_network(schema_data)
        self.assertIn("Orders", graph.nodes)
        self.assertIn("EmptyTable", graph.nodes)
        self.assertEqual(len(graph.edges), 0)

    def test_build_schema_network_field_in_multiple_tables(self):
        schema_data = [
            {
                "domain_name": "HR",
                "tables": [
                    {"table_name": "Employees", "fields": [{"field_name": "employee_id"}, {"field_name": "department_id"}]},
                    {"table_name": "Departments", "fields": [{"field_name": "department_id"}, {"field_name": "manager_id"}]},
                    {"table_name": "Salaries", "fields": [{"field_name": "employee_id"}, {"field_name": "salary_amount"}]}
                ]
            }
        ]
        graph = build_schema_network(schema_data)
        self.assertTrue(graph.has_edge("Employees", "Departments"))
        self.assertEqual(graph["Employees"]["Departments"]["shared_field"], "department_id")
        self.assertTrue(graph.has_edge("Employees", "Salaries"))
        self.assertEqual(graph["Employees"]["Salaries"]["shared_field"], "employee_id")
        # Ensure no edge between Departments and Salaries if they don't share a field directly
        self.assertFalse(graph.has_edge("Departments", "Salaries"))


    def test_build_kpi_network_empty_input(self):
        graph = build_kpi_network([])
        self.assertIsInstance(graph, nx.Graph)
        self.assertEqual(len(graph.nodes), 0)
        self.assertEqual(len(graph.edges), 0)

    def test_build_kpi_network_single_kpi_no_tables(self):
        kpi_data = [{"kpi_name": "TestKPI", "data_required": []}]
        graph = build_kpi_network(kpi_data)
        self.assertEqual(len(graph.nodes), 0)
        self.assertEqual(len(graph.edges), 0)

    def test_build_kpi_network_single_kpi_one_table(self):
        kpi_data = [
            {"kpi_name": "Revenue", "data_required": [{"domain_name": "Sales", "table_name": "Transactions"}]}
        ]
        graph = build_kpi_network(kpi_data)
        self.assertEqual(len(graph.nodes), 1)
        self.assertIn("Transactions", graph.nodes)
        self.assertEqual(len(graph.edges), 0)

    def test_build_kpi_network_single_kpi_multiple_tables(self):
        kpi_data = [
            {
                "kpi_name": "ProfitMargin",
                "data_required": [
                    {"domain_name": "Sales", "table_name": "SalesData"},
                    {"domain_name": "Finance", "table_name": "CostData"},
                    {"domain_name": "Marketing", "table_name": "CampaignInfo"}
                ]
            }
        ]
        graph = build_kpi_network(kpi_data)
        self.assertEqual(len(graph.nodes), 3)
        self.assertIn("SalesData", graph.nodes)
        self.assertIn("CostData", graph.nodes)
        self.assertIn("CampaignInfo", graph.nodes)
        self.assertEqual(len(graph.edges), 3) # combinations(3,2) = 3
        self.assertTrue(graph.has_edge("SalesData", "CostData"))
        self.assertEqual(graph["SalesData"]["CostData"]["kpi_links"], ["ProfitMargin"])
        self.assertTrue(graph.has_edge("SalesData", "CampaignInfo"))
        self.assertEqual(graph["SalesData"]["CampaignInfo"]["kpi_links"], ["ProfitMargin"])
        self.assertTrue(graph.has_edge("CostData", "CampaignInfo"))
        self.assertEqual(graph["CostData"]["CampaignInfo"]["kpi_links"], ["ProfitMargin"])

    def test_build_kpi_network_multiple_kpis_shared_tables(self):
        kpi_data = [
            {
                "kpi_name": "KPI1",
                "data_required": [
                    {"table_name": "TableA"},
                    {"table_name": "TableB"}
                ]
            },
            {
                "kpi_name": "KPI2",
                "data_required": [
                    {"table_name": "TableB"},
                    {"table_name": "TableC"}
                ]
            },
            {
                "kpi_name": "KPI3",
                "data_required": [
                    {"table_name": "TableA"},
                    {"table_name": "TableB"}, # KPI3 shares TableA and TableB with KPI1
                    {"table_name": "TableD"}
                ]
            }
        ]
        graph = build_kpi_network(kpi_data)
        self.assertEqual(len(graph.nodes), 4) # A, B, C, D
        self.assertIn("TableA", graph.nodes)
        self.assertIn("TableB", graph.nodes)
        self.assertIn("TableC", graph.nodes)
        self.assertIn("TableD", graph.nodes)

        self.assertTrue(graph.has_edge("TableA", "TableB"))
        self.assertIn("KPI1", graph["TableA"]["TableB"]["kpi_links"])
        self.assertIn("KPI3", graph["TableA"]["TableB"]["kpi_links"])
        self.assertEqual(len(graph["TableA"]["TableB"]["kpi_links"]), 2)

        self.assertTrue(graph.has_edge("TableB", "TableC"))
        self.assertEqual(graph["TableB"]["TableC"]["kpi_links"], ["KPI2"])

        self.assertTrue(graph.has_edge("TableA", "TableD"))
        self.assertEqual(graph["TableA"]["TableD"]["kpi_links"], ["KPI3"])

        self.assertTrue(graph.has_edge("TableB", "TableD"))
        self.assertEqual(graph["TableB"]["TableD"]["kpi_links"], ["KPI3"])

        # Check total number of edges: (A,B), (B,C), (A,D), (B,D)
        self.assertEqual(len(graph.edges), 4)


    def test_build_kpi_network_kpi_with_duplicate_tables_in_data_required(self):
        kpi_data = [
            {
                "kpi_name": "UniqueCheckKPI",
                "data_required": [
                    {"table_name": "TableX"},
                    {"table_name": "TableY"},
                    {"table_name": "TableX"} # Duplicate TableX
                ]
            }
        ]
        graph = build_kpi_network(kpi_data)
        self.assertEqual(len(graph.nodes), 2)
        self.assertIn("TableX", graph.nodes)
        self.assertIn("TableY", graph.nodes)
        self.assertEqual(len(graph.edges), 1)
        self.assertTrue(graph.has_edge("TableX", "TableY"))
        self.assertEqual(graph["TableX"]["TableY"]["kpi_links"], ["UniqueCheckKPI"])

if __name__ == '__main__':
    unittest.main()
