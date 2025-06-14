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
    generate_comparison_narrative
)

class MockGraph:
    def __init__(self, nodes=None, edges=None):
        self._nodes = nodes if nodes is not None else []
        self._edges = edges if edges is not None else []
        # Simulate G.adj for degree calculation by get_top_n_central_nodes via analysis_results
        # The narrative functions themselves use number_of_nodes/edges and graph.nodes()
        # The actual graph.adj is used by networkx.degree_centrality, which is mocked in analysis_results

    def number_of_nodes(self): return len(self._nodes)
    def number_of_edges(self): return len(self._edges)
    def nodes(self): return self._nodes
    # Add adj property if any part of the narrative generator directly uses it (currently it doesn't)
    # It primarily relies on analysis_results for centrality.

class TestNarrativeGenerator(unittest.TestCase):

    def test_get_top_n_central_nodes(self):
        self.assertEqual(get_top_n_central_nodes(None, 'degree'), [])
        self.assertEqual(get_top_n_central_nodes({}, 'degree'), [])
        self.assertEqual(get_top_n_central_nodes({'pagerank': {}}, 'degree'), [])
        self.assertEqual(get_top_n_central_nodes({'degree': []}), []) # Not a dict
        self.assertEqual(get_top_n_central_nodes({'degree': {}}), [])

        analysis = {'degree': {'A': 0.5, 'B': 0.8, 'C': 0.2, 'D': 0.9, 'E': 0.0}}
        self.assertEqual(get_top_n_central_nodes(analysis, 'degree', 3), ['D (**0.90**)', 'B (**0.80**)', 'A (**0.50**)'])
        self.assertEqual(get_top_n_central_nodes(analysis, 'degree', 2), ['D (**0.90**)', 'B (**0.80**)'])
        self.assertEqual(get_top_n_central_nodes(analysis, 'degree', 5), ['D (**0.90**)', 'B (**0.80**)', 'A (**0.50**)', 'C (**0.20**)']) # E with 0 score is filtered

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
        self.assertNotIn("T3", narrative) # Because T3 score is 0 for degree

        analysis_high_betweenness = {
            'degree_centrality': {'T1': 0.5, 'T2': 0.8, 'T3': 0.5},
            'betweenness_centrality': {'T2': 0.25} # T2 has score > 0
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

        graph_nodes_no_edges = MockGraph(nodes=['T1', 'T2']) # KPIs use T1 and T2, but not together
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

        # Both empty
        narrative = generate_comparison_narrative(g_empty, g_empty, set(), set(), set())
        self.assertIn("0 table(s)** are common", narrative)
        self.assertIn("There are no tables directly shared", narrative)
        self.assertIn("0 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("schema is minimal", narrative) # Or all utilized
        self.assertIn("0 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("good alignment", narrative)

        # Schema has data, KPI empty
        narrative = generate_comparison_narrative(g_schema, g_empty, set(), {'A','B','C'}, set())
        self.assertIn("0 table(s)** are common", narrative)
        self.assertIn("3 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("Examples include **A, B, C**", narrative)
        self.assertIn("0 table(s)** are required for KPIs but are not found", narrative)

        # KPI has data, Schema empty
        narrative = generate_comparison_narrative(g_empty, g_kpi, set(), set(), {'B','C','D'})
        self.assertIn("0 table(s)** are common", narrative)
        self.assertIn("0 table(s)** are defined in the schema", narrative)
        self.assertIn("3 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("Examples include **B, C, D**", narrative)

        # Valid graphs with overlap
        common, schema_only, kpi_only = {'B','C'}, {'A'}, {'D'}
        narrative = generate_comparison_narrative(g_schema, g_kpi, common, schema_only, kpi_only)
        self.assertIn("2 table(s)** are common", narrative)
        self.assertIn("Key common tables include **B, C**", narrative)
        self.assertIn("1 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("Examples include **A**", narrative)
        self.assertIn("1 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("Examples include **D**", narrative)

        # All nodes common
        g_schema_all_common = MockGraph(nodes=['X','Y'])
        g_kpi_all_common = MockGraph(nodes=['X','Y'])
        narrative = generate_comparison_narrative(g_schema_all_common, g_kpi_all_common, {'X','Y'}, set(), set())
        self.assertIn("2 table(s)** are common", narrative)
        self.assertIn("0 table(s)** are defined in the schema but are not directly referenced", narrative)
        self.assertIn("tight coupling if the schema is comprehensive", narrative)
        self.assertIn("0 table(s)** are required for KPIs but are not found", narrative)
        self.assertIn("positive sign for data readiness", narrative)

if __name__ == '__main__':
    unittest.main()
