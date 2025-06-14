import sys
import os
import unittest
import networkx as nx

# Add the parent directory (/app) to sys.path to find the 'app' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.src.network_analysis import analyze_network

class TestNetworkAnalysis(unittest.TestCase):

    def test_analyze_network_empty_graph(self):
        graph = nx.Graph()
        results = analyze_network(graph)
        self.assertEqual(results, {})

    def test_analyze_network_none_graph(self):
        results = analyze_network(None)
        self.assertEqual(results, {})

    def test_analyze_network_simple_graph(self):
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("A", "C"), ("B", "C"), ("C", "D")])

        results = analyze_network(graph)

        self.assertIsInstance(results, dict)
        self.assertIn('degree_centrality', results)
        self.assertIsInstance(results['degree_centrality'], dict)
        self.assertIn('betweenness_centrality', results)
        self.assertIsInstance(results['betweenness_centrality'], dict)
        self.assertIn('closeness_centrality', results)
        self.assertIsInstance(results['closeness_centrality'], dict)
        self.assertIn('eigenvector_centrality', results)
        self.assertIsInstance(results['eigenvector_centrality'], dict)

        # Check if all nodes are present in the centrality results (if not empty)
        nodes = ["A", "B", "C", "D"]
        for measure, R_DEBUG_IF_ABSENT_FROM_ALL_NODE_MEASURES in results.items():
            if isinstance(R_DEBUG_IF_ABSENT_FROM_ALL_NODE_MEASURES, dict) and R_DEBUG_IF_ABSENT_FROM_ALL_NODE_MEASURES: # Check if it's a non-empty dict
                for node in nodes:
                    self.assertIn(node, R_DEBUG_IF_ABSENT_FROM_ALL_NODE_MEASURES, f"Node {node} missing from {measure}")

    def test_analyze_network_graph_with_isolated_nodes_for_eigenvector(self):
        # Eigenvector centrality is not well-defined for graphs with no edges
        # or for disconnected components if not handled carefully by implementation.
        # nx.eigenvector_centrality handles disconnected graphs by returning 0 for isolated nodes
        # or nodes in components with no edges.
        # A graph that is "pointless" (e.g. no edges) will raise NetworkXPointlessConcept
        graph = nx.Graph()
        graph.add_node("A")
        graph.add_node("B")
        results = analyze_network(graph)
        self.assertIn('eigenvector_centrality', results)
        # For a graph with nodes but no edges, networkx eigenvector_centrality
        # might return a default uniform centrality rather than an empty dict or raising PointlessConcept.
        # We should check that the nodes are present in the result.
        self.assertIsInstance(results['eigenvector_centrality'], dict)
        if graph.nodes(): # If there are nodes
            self.assertTrue(len(results['eigenvector_centrality']) == len(graph.nodes()))
            for node in graph.nodes():
                self.assertIn(node, results['eigenvector_centrality'])
        else: # Should be empty if graph had no nodes (though analyze_network handles this earlier)
            self.assertEqual(results['eigenvector_centrality'], {})


    def test_analyze_network_disconnected_graph(self):
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("C", "D")]) # Two disconnected components
        results = analyze_network(graph)
        self.assertIsInstance(results, dict)
        self.assertIn('degree_centrality', results)
        self.assertIn('A', results['degree_centrality'])
        self.assertIn('C', results['degree_centrality'])
        self.assertIn('eigenvector_centrality', results)
        # Eigenvector centrality for disconnected graphs: values might be zero for some components
        # but the keys should still be there for all nodes.
        if results['eigenvector_centrality']: # It might be empty if an error was caught during its calculation.
            self.assertIn('A', results['eigenvector_centrality'])
            self.assertIn('C', results['eigenvector_centrality'])

from app.src.network_analysis import calculate_average_centrality

class TestCalculateAverageCentrality(unittest.TestCase):
    def test_calculate_average_centrality_empty_or_none(self):
        self.assertIsNone(calculate_average_centrality(None, 'degree_centrality'))
        self.assertIsNone(calculate_average_centrality({}, 'degree_centrality'))
        self.assertIsNone(calculate_average_centrality({'degree_centrality': {}}, 'degree_centrality'))
        self.assertIsNone(calculate_average_centrality({'other_key': {'a': 1}}, 'degree_centrality'))

    def test_calculate_average_centrality_valid_data(self):
        analysis_results = {'degree_centrality': {'a': 0.5, 'b': 1.0, 'c': 0.0}}
        self.assertAlmostEqual(calculate_average_centrality(analysis_results, 'degree_centrality'), 0.5)

        analysis_results = {'degree_centrality': {'a': 1, 'b': 2, 'c': 3}}
        self.assertAlmostEqual(calculate_average_centrality(analysis_results, 'degree_centrality'), 2.0)

    def test_calculate_average_centrality_non_numeric_scores(self):
        # Current implementation filters out non-numeric scores
        analysis_results = {'degree_centrality': {'a': 'text', 'b': 1.0}}
        self.assertAlmostEqual(calculate_average_centrality(analysis_results, 'degree_centrality'), 1.0)

        analysis_results = {'degree_centrality': {'a': 'text', 'b': 'another_text'}}
        self.assertIsNone(calculate_average_centrality(analysis_results, 'degree_centrality')) # No numeric scores

    def test_calculate_average_centrality_with_other_metrics(self):
        analysis_results = {
            'degree_centrality': {'a': 0.5, 'b': 1.0},
            'betweenness_centrality': {'a': 0.1, 'b': 0.2}
        }
        self.assertAlmostEqual(calculate_average_centrality(analysis_results, 'degree_centrality'), 0.75)
        self.assertAlmostEqual(calculate_average_centrality(analysis_results, 'betweenness_centrality'), 0.15)


if __name__ == '__main__':
    unittest.main()
