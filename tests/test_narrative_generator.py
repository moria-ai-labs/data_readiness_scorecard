import os
import sys
import unittest

# Add project root to sys.path to allow direct import of app.src modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.src.narrative_generator import (
    get_top_n_central_nodes,
    generate_schema_narrative,
    generate_kpi_narrative,
    generate_comparison_narrative,
    generate_executive_summary_narrative # Added import
)

class MockGraph:
    def __init__(self, nodes=None, edges=None):
        self._nodes = nodes if nodes is not None else []
        self._edges = edges if edges is not None else []

    def number_of_nodes(self): return len(self._nodes)
    def number_of_edges(self): return len(self._edges)
    def nodes(self): return self._nodes

class TestNarrativeGenerator(unittest.TestCase):

    def test_get_top_n_central_nodes(self):
        self.assertEqual(get_top_n_central_nodes(None, 'degree'), [])
        self.assertEqual(get_top_n_central_nodes({}, 'degree'), [])
        self.assertEqual(get_top_n_central_nodes({'pagerank': {}}, 'degree'), [])
        self.assertEqual(get_top_n_central_nodes({'degree': []}), [])
        self.assertEqual(get_top_n_central_nodes({'degree': {}}), [])

        analysis = {'degree': {'A': 0.5, 'B': 0.8, 'C': 0.2, 'D': 0.9, 'E': 0.0}}
        self.assertEqual(get_top_n_central_nodes(analysis, 'degree', 3), ['D (**0.90**)', 'B (**0.80**)', 'A (**0.50**)'])
        self.assertEqual(get_top_n_central_nodes(analysis, 'degree', 2), ['D (**0.90**)', 'B (**0.80**)'])
        self.assertEqual(get_top_n_central_nodes(analysis, 'degree', 5), ['D (**0.90**)', 'B (**0.80**)', 'A (**0.50**)', 'C (**0.20**)'])

        analysis_with_zeros = {'degree': {'A': 0.0, 'B': 0.0}}
        self.assertEqual(get_top_n_central_nodes(analysis_with_zeros, 'degree', 2), [])


    def test_generate_schema_narrative(self):
        self.assertIn("Schema data is not available", generate_schema_narrative(None, {}))

        empty_graph = MockGraph()
        self.assertIn("schema network is currently empty", generate_schema_narrative(empty_graph, {}))

        graph_nodes_no_edges = MockGraph(nodes=['T1', 'T2'])
        narrative = generate_schema_narrative(graph_nodes_no_edges, {})
        self.assertIn("2 table(s)", narrative)
        self.assertIn("0 potential relationships", narrative)
        self.assertIn("No direct relationships between tables", narrative)
        self.assertIn("No degree centrality information available", narrative)

        graph_with_data = MockGraph(nodes=['T1', 'T2', 'T3'], edges=[('T1','T2')])
        analysis = {
            'degree_centrality': {'T1': 0.5, 'T2': 0.5, 'T3': 0.0},
            'betweenness_centrality': {'T1': 0.0, 'T2': 0.0, 'T3': 0.0}
        }
        narrative = generate_schema_narrative(graph_with_data, analysis)
        self.assertIn("3 table(s)", narrative)
        self.assertIn("1 potential relationship", narrative)
        self.assertIn("Key tables by direct connectivity", narrative)
        self.assertIn("- T1 (**0.50**)", narrative)
        self.assertIn("- T2 (**0.50**)", narrative)
        self.assertNotIn("T3", narrative)

        analysis_high_betweenness = {
            'degree_centrality': {'T1': 0.5, 'T2': 0.8, 'T3': 0.5},
            'betweenness_centrality': {'T2': 0.25}
        }
        narrative = generate_schema_narrative(graph_with_data, analysis_high_betweenness)
        self.assertIn("Key tables by direct connectivity", narrative)
        self.assertIn("- T2 (**0.80**)", narrative)
        self.assertIn("Notably, T2 shows high betweenness centrality", narrative)
        self.assertIn("(0.25)", narrative)


    def test_generate_kpi_narrative(self):
        self.assertIn("KPI data is not available", generate_kpi_narrative(None, {}))

        empty_graph = MockGraph()
        self.assertIn("KPI network is empty", generate_kpi_narrative(empty_graph, {}))

        graph_nodes_no_edges = MockGraph(nodes=['T1', 'T2'])
        narrative = generate_kpi_narrative(graph_nodes_no_edges, {})
        self.assertIn("2 table(s)", narrative)
        self.assertIn("0 link(s)", narrative)
        self.assertIn("No tables were found to be co-required", narrative)
        self.assertIn("No degree centrality information available", narrative)

        graph_with_data = MockGraph(nodes=['T1', 'T2', 'T3'], edges=[('T1','T2')])
        analysis = {'degree_centrality': {'T1': 0.5, 'T2': 0.5, 'T3': 0.0}}
        narrative = generate_kpi_narrative(graph_with_data, analysis)
        self.assertIn("3 table(s)", narrative)
        self.assertIn("1 link(s)", narrative)
        self.assertIn("Key tables by co-occurrence", narrative)
        self.assertIn("- T1 (**0.50**)", narrative)
        self.assertIn("- T2 (**0.50**)", narrative)


    def test_generate_comparison_narrative(self):
        g_empty = MockGraph()
        g_schema = MockGraph(nodes=['A', 'B', 'C'], edges=[('A','B')])
        g_kpi = MockGraph(nodes=['B', 'C', 'D'], edges=[('B','C')])

        self.assertIn("neither schema nor KPI data is available", generate_comparison_narrative(None, None, set(), set(), set()))
        self.assertIn("schema data is missing", generate_comparison_narrative(None, g_kpi, set(), set(), set()))
        self.assertIn("KPI data is missing", generate_comparison_narrative(g_schema, None, set(), set(), set()))

        narrative = generate_comparison_narrative(g_empty, g_empty, set(), set(), set())
        self.assertIn("0 table(s)** are common", narrative)
        self.assertIn("There are no tables directly shared", narrative)
        self.assertIn("0 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("schema is minimal", narrative)
        self.assertIn("0 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("good alignment", narrative)

        narrative = generate_comparison_narrative(g_schema, g_empty, set(), {'A','B','C'}, set())
        self.assertIn("0 table(s)** are common", narrative)
        self.assertIn("3 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("Examples include **A, B, C**", narrative)
        self.assertIn("0 table(s)** are required for KPIs but are not found", narrative)

        narrative = generate_comparison_narrative(g_empty, g_kpi, set(), set(), {'B','C','D'})
        self.assertIn("0 table(s)** are common", narrative)
        self.assertIn("0 table(s)** are defined in the schema", narrative)
        self.assertIn("3 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("Examples include **B, C, D**", narrative)

        common, schema_only, kpi_only = {'B','C'}, {'A'}, {'D'}
        narrative = generate_comparison_narrative(g_schema, g_kpi, common, schema_only, kpi_only)
        self.assertIn("2 table(s)** are common", narrative)
        self.assertIn("Key common tables include **B, C**", narrative)
        self.assertIn("1 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("Examples include **A**", narrative)
        self.assertIn("1 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("Examples include **D**", narrative)

        g_schema_all_common = MockGraph(nodes=['X','Y'])
        g_kpi_all_common = MockGraph(nodes=['X','Y'])
        narrative = generate_comparison_narrative(g_schema_all_common, g_kpi_all_common, {'X','Y'}, set(), set())
        self.assertIn("2 table(s)** are common", narrative)
        self.assertIn("0 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("tight coupling if the schema is comprehensive", narrative)
        self.assertIn("0 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("positive sign for data readiness", narrative)

class TestGenerateExecutiveSummaryNarrative(unittest.TestCase):
    def test_no_kpi_data(self):
        self.assertIn("No KPI data was provided", generate_executive_summary_narrative(None, {'TableC'}))
        self.assertIn("No KPI data was provided", generate_executive_summary_narrative([], {'TableC'}))

    def test_no_kpi_only_nodes(self):
        kpi_data = [{"kpi_name": "KPI1", "data_required": [{"table_name": "TableA"}]}]
        self.assertIn("All KPIs appear to have their required tables defined", generate_executive_summary_narrative(kpi_data, set()))

    def test_kpi_only_nodes_not_in_kpis(self):
        kpi_data = [{"kpi_name": "KPI1", "data_required": [{"table_name": "TableA"}]}]
        kpi_only_nodes_set = {'TableB'}
        self.assertIn("All KPIs appear to have their required tables defined", generate_executive_summary_narrative(kpi_data, kpi_only_nodes_set))

    def test_kpis_at_risk(self):
        kpi_data = [
            {"kpi_name": "KPI Alpha", "data_required": [{"table_name": "Orders"}, {"table_name": "Customers_Internal"}]},
            {"kpi_name": "KPI Beta", "data_required": [{"table_name": "Sales"}, {"table_name": "Marketing_Spend"}]},
            {"kpi_name": "KPI Gamma", "data_required": [{"table_name": "Inventory"}]}
        ]
        kpi_only_nodes = {"Customers_Internal", "Marketing_Spend", "Logistics"}

        narrative = generate_executive_summary_narrative(kpi_data, kpi_only_nodes)
        self.assertIn("KPIs may be **uncomputable or at risk**", narrative)
        self.assertIn("- **KPI Alpha**: Requires missing table(s): *Customers_Internal*", narrative)
        self.assertIn("- **KPI Beta**: Requires missing table(s): *Marketing_Spend*", narrative)
        self.assertNotIn("KPI Gamma", narrative)
        self.assertNotIn("Logistics", narrative)

    def test_kpi_with_duplicate_missing_tables(self):
        kpi_data = [{"kpi_name": "KPI Zeta", "data_required": [{"table_name": "MissingTable"}, {"table_name": "MissingTable"}]}]
        kpi_only_nodes = {"MissingTable"}
        narrative = generate_executive_summary_narrative(kpi_data, kpi_only_nodes)
        self.assertIn("- **KPI Zeta**: Requires missing table(s): *MissingTable*", narrative)
        self.assertNotIn("MissingTable, MissingTable", narrative)

    def test_multiple_kpis_multiple_missing_tables(self):
        kpi_data = [
            {"kpi_name": "KPI One", "data_required": [{"table_name": "TableX"}, {"table_name": "TableY"}]},
            {"kpi_name": "KPI Two", "data_required": [{"table_name": "TableZ"}, {"table_name": "TableX"}]}
        ]
        kpi_only_nodes = {"TableX", "TableY", "TableZ"}
        narrative = generate_executive_summary_narrative(kpi_data, kpi_only_nodes)
        self.assertIn("- **KPI One**: Requires missing table(s): *TableX, TableY*", narrative)
        self.assertIn("- **KPI Two**: Requires missing table(s): *TableX, TableZ*", narrative)

if __name__ == '__main__':
    unittest.main()
