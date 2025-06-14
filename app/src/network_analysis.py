import networkx as nx

def analyze_network(graph: nx.Graph) -> dict:
    """
    Performs centrality analysis on a given networkx graph.

    Args:
        graph: A networkx.Graph object.

    Returns:
        A dictionary containing the calculated centrality measures.
        Returns an empty dictionary if the graph is None or has no nodes.
    """
    if graph is None or not graph.nodes():
        print("Graph is empty or None. Cannot perform analysis.")
        return {}

    analysis_results = {}

    try:
        analysis_results['degree_centrality'] = nx.degree_centrality(graph)
        analysis_results['betweenness_centrality'] = nx.betweenness_centrality(graph)
        analysis_results['closeness_centrality'] = nx.closeness_centrality(graph)
        # Eigenvector centrality can sometimes fail on certain graph structures if not connected
        # or other numerical issues. Add a try-except block for it.
        try:
            analysis_results['eigenvector_centrality'] = nx.eigenvector_centrality(graph, max_iter=1000, tol=1e-06)
        except nx.NetworkXError as e:
            print(f"Could not calculate Eigenvector Centrality: {e}. Setting to empty dict.")
            analysis_results['eigenvector_centrality'] = {}
        except nx.NetworkXPointlessConcept:
             print("Graph is pointless (e.g. empty or all nodes isolated) for Eigenvector Centrality. Setting to empty dict.")
             analysis_results['eigenvector_centrality'] = {}


    except Exception as e:
        print(f"An error occurred during network analysis: {e}")
        # Return any results gathered so far, or an empty dict if a major error occurred early.
        return analysis_results if analysis_results else {}

    return analysis_results

# Placeholder for other analysis functions if needed later
# def detect_communities(graph):
#     pass

# def calculate_network_density(graph):
#     pass

def calculate_average_centrality(analysis_results, centrality_key='degree_centrality'):
    """
    Calculates the average centrality score from the analysis results.

    Args:
        analysis_results (dict): The dictionary output from analyze_network.
        centrality_key (str): The key for the specific centrality measure
                             (e.g., 'degree_centrality').

    Returns:
        float: The average centrality score, or None if data is unavailable or empty.
    """
    if not analysis_results or not isinstance(analysis_results, dict):
        return None

    centrality_data = analysis_results.get(centrality_key)
    if not centrality_data or not isinstance(centrality_data, dict) or not centrality_data.values():
        # Handles empty dict or dict with no values
        return None

    try:
        # Ensure all values are numbers, filter out non-numeric if any (should not happen with current analyze_network)
        scores = [score for score in centrality_data.values() if isinstance(score, (int, float))]
        if not scores:
            return None # No numeric scores found
        return sum(scores) / len(scores)
    except TypeError:
        # Should not happen if centrality_data.values() are numbers
        return None
