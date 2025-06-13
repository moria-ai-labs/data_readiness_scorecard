import sys
import os
import unittest
import networkx as nx
import plotly.graph_objects as go

# Add the parent directory (project root) to sys.path to reliably find the 'app' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_network_figure # Import the function to be tested

class TestAppUtils(unittest.TestCase):

    def test_create_network_figure_empty_graph(self):
        G_empty = nx.Graph()
        fig = create_network_figure(G_empty, "Empty Test Graph", "blue", 42, [])

        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "Empty Test Graph - No data to display")
        self.assertTrue(fig.layout.annotations is not None and len(fig.layout.annotations) > 0)
        self.assertEqual(fig.layout.annotations[0].text, "No data to display or network is empty.")
        self.assertFalse(fig.data) # No data traces should be present

    def test_create_network_figure_none_graph(self):
        fig = create_network_figure(None, "None Test Graph", "blue", 42, [])

        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "None Test Graph - No data to display")
        self.assertTrue(fig.layout.annotations is not None and len(fig.layout.annotations) > 0)
        self.assertEqual(fig.layout.annotations[0].text, "No data to display or network is empty.")
        self.assertFalse(fig.data)

    def test_create_network_figure_simple_graph(self):
        G_simple = nx.Graph()
        G_simple.add_edges_from([("A", "B"), ("B", "C")])

        # Custom hover texts for edges: (A,B) then (B,C)
        # Each edge needs 3 entries in the hovertext list (start, end, None for middle of segment)
        edge_hover_texts = [
            "Custom: A-B", "Custom: A-B", None,
            "Custom: B-C", "Custom: B-C", None
        ]

        fig = create_network_figure(G_simple, "Simple Test Graph", "red", 42, edge_hover_texts_custom=edge_hover_texts)

        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "Simple Test Graph")
        self.assertEqual(len(fig.data), 2, "Should have one edge trace and one node trace")

        # Edge trace checks
        edge_trace = fig.data[0]
        self.assertEqual(edge_trace.mode, 'lines')
        self.assertEqual(len(edge_trace.x), G_simple.number_of_edges() * 3) # 2 edges * 3 points per edge segment
        self.assertEqual(edge_trace.hovertext, tuple(edge_hover_texts))


        # Node trace checks
        node_trace = fig.data[1]
        self.assertEqual(node_trace.mode, 'markers+text')
        self.assertEqual(node_trace.marker.color, 'red')
        self.assertEqual(len(node_trace.x), G_simple.number_of_nodes()) # Should have 3 nodes

        # Check node texts and hover texts (order depends on internal processing, so check presence)
        expected_nodes = {"A", "B", "C"}
        self.assertEqual(set(node_trace.text), expected_nodes)

        # Check node sizes (degree-based)
        # A:1, B:2, C:1. Sizes: 1*5+10=15, 2*5+10=20, 1*5+10=15
        # Order in trace might vary, so we check if these sizes are present
        expected_sizes = [15.0, 20.0, 15.0]
        # Note: plotly might store sizes as float even if calculated with int
        # Convert trace sizes to list of floats for comparison if necessary
        actual_sizes = list(node_trace.marker.size)
        self.assertCountEqual([float(s) for s in actual_sizes], expected_sizes)


    def test_create_network_figure_default_edge_hover(self):
        G = nx.Graph()
        G.add_edge("N1", "N2")
        fig = create_network_figure(G, "Default Hover Test") # No custom hover texts

        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 2)
        edge_trace = fig.data[0]
        # Expected default hover text for one edge
        expected_hover = ("Edge: N1 - N2", "Edge: N1 - N2", None)
        self.assertEqual(edge_trace.hovertext, expected_hover)

if __name__ == '__main__':
    unittest.main()
