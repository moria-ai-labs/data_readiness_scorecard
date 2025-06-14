import networkx as nx # Though not directly used in this initial scaffold, good for type hinting if added

def get_top_n_central_nodes(analysis_results, centrality_key='degree_centrality', n=3):
    """Helper to get top N nodes by a centrality measure."""
    if not analysis_results or centrality_key not in analysis_results:
        return []

    centrality_data = analysis_results.get(centrality_key, {})
    if not isinstance(centrality_data, dict) or not centrality_data:
        return []

    sorted_nodes = sorted(centrality_data.items(), key=lambda item: item[1], reverse=True)

    top_nodes = [f"{node} (**{score:.2f}**)" for node, score in sorted_nodes[:n] if score > 0] # Corrected: parenthesis inside bold
    return top_nodes

def generate_schema_narrative(graph, analysis_results):
    if graph is None:
        return "Schema data is not available or failed to process. Cannot generate schema narrative."

    num_tables = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    narrative = f"The schema network describes **{num_tables} table(s)** with **{num_edges} potential relationships** (based on shared field names within the same domain).\n\n"

    if num_tables == 0:
        narrative += "The schema network is currently empty."
        return narrative

    if num_edges == 0 and num_tables > 0:
        narrative += "No direct relationships between tables (based on shared field names within domains) were detected in the provided schema data.\n\n"

    narrative += "Centrality analysis can help identify key tables. Degree centrality measures how many direct connections a table has.\n"
    top_degree_nodes = get_top_n_central_nodes(analysis_results, 'degree_centrality', 3)
    if top_degree_nodes:
        narrative += "Key tables by direct connectivity (degree centrality score):\n"
        for item in top_degree_nodes:
            narrative += f"- {item}\n"
        narrative += "\n"
    else:
        if analysis_results and 'degree_centrality' in analysis_results:
             narrative += "All tables have zero direct connections or degree centrality data is not available.\n\n"
        else:
            narrative += "No degree centrality information available for the schema network.\n\n"

    top_betweenness_nodes = get_top_n_central_nodes(analysis_results, 'betweenness_centrality', 1)
    if top_betweenness_nodes and float(top_betweenness_nodes[0].split('(')[-1].replace(')','').replace('*','')) > 0:
        narrative += f"Notably, {top_betweenness_nodes[0].split(' (')[0]} shows high betweenness centrality **({top_betweenness_nodes[0].split('(')[-1].replace(')','').replace('*','')})**, suggesting it may act as a crucial bridge connecting different groups of tables within a domain.\n\n"

    return narrative

def generate_kpi_narrative(graph, analysis_results):
    if graph is None:
        return "KPI data is not available or failed to process. Cannot generate KPI narrative."

    num_tables = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    narrative = f"The KPI network indicates that **{num_tables} table(s)** are involved in the uploaded KPIs, with **{num_edges} link(s)** indicating tables are co-required for KPIs.\n\n"

    if num_tables == 0:
        narrative += "No tables appear to be required by the uploaded KPIs, or the KPI network is empty."
        return narrative

    if num_edges == 0 and num_tables > 0:
        narrative += "No tables were found to be co-required for the same KPIs, or each KPI requires only a single table.\n\n"

    narrative += "Degree centrality in this context highlights tables that are frequently required alongside other tables for various KPIs.\n"
    top_degree_nodes = get_top_n_central_nodes(analysis_results, 'degree_centrality', 3)
    if top_degree_nodes:
        narrative += "Key tables by co-occurrence in KPIs (degree centrality score):\n"
        for item in top_degree_nodes:
            narrative += f"- {item}\n"
        narrative += "\n"
    else:
        if analysis_results and 'degree_centrality' in analysis_results:
            narrative += "All tables involved in KPIs have zero co-occurrence links or degree centrality data is not available.\n\n"
        else:
            narrative += "No degree centrality information available for the KPI network.\n\n"

    return narrative

def generate_comparison_narrative(schema_graph, kpi_graph, common_nodes, schema_only_nodes, kpi_only_nodes):
    if schema_graph is None and kpi_graph is None:
        return "Comparison narrative cannot be generated as neither schema nor KPI data is available or processed successfully."
    if schema_graph is None:
        return "Comparison narrative cannot be fully generated as schema data is missing or failed to process. Please check KPI narrative for KPI-specific insights."
    if kpi_graph is None:
        return "Comparison narrative cannot be fully generated as KPI data is missing or failed to process. Please check Schema narrative for schema-specific insights."

    narrative = "A comparative analysis between the schema structure and KPI data requirements offers valuable insights into data landscape alignment:\n\n"

    common_nodes_list = sorted(list(common_nodes))
    schema_only_nodes_list = sorted(list(schema_only_nodes))
    kpi_only_nodes_list = sorted(list(kpi_only_nodes))

    narrative += f"- **{len(common_nodes_list)} table(s)** are common to both the defined schema and KPI requirements. "
    if common_nodes_list:
        narrative += f"Key common tables include **{', '.join(common_nodes_list[:3])}**{', among others' if len(common_nodes_list) > 3 else ''}.\n"
    else:
        narrative += "There are no tables directly shared between the schema definition and KPI requirements based on the provided data. This could indicate a significant misalignment or that the datasets describe entirely different table sets.\n"

    narrative += f"- **{len(schema_only_nodes_list)} table(s)** are defined in the schema but are not directly referenced by the uploaded KPIs. "
    if schema_only_nodes_list:
        narrative += f"Examples include **{', '.join(schema_only_nodes_list[:3])}**{', among others' if len(schema_only_nodes_list) > 3 else ''}. "
        narrative += "These might represent underutilized data assets, areas for future KPI development, or foundational tables that support other tables used in KPIs, even if not directly named.\n"
    else:
        narrative += "This suggests all defined schema tables are utilized in KPIs, or the schema is minimal. This indicates a tight coupling if the schema is comprehensive.\n"

    narrative += f"- **{len(kpi_only_nodes_list)} table(s)** are required for KPIs but are not found in the provided schema mapping. "
    if kpi_only_nodes_list:
        narrative += f"Examples include **{', '.join(kpi_only_nodes_list[:3])}**{', among others' if len(kpi_only_nodes_list) > 3 else ''}. "
        narrative += "These highlight potential data gaps or tables that need to be formally documented. Ensuring these tables are well-defined and integrated into the schema is crucial for data governance and robust reporting.\n"
    else:
        narrative += "This indicates good alignment, with all KPI data requirements seemingly covered by the provided schema definitions. This is a positive sign for data readiness regarding KPI fulfillment.\n"

    return narrative

def generate_executive_summary_narrative(parsed_kpi_data, kpi_only_nodes_set):
    """
    Generates a narrative listing KPIs that may be uncomputable due to
    their required tables being in the kpi_only_nodes_set.

    Args:
        parsed_kpi_data (list): The raw parsed list of KPI dictionaries
                               (output from data_parser.parse_kpi_json).
        kpi_only_nodes_set (set): A set of table names that are required by KPIs
                                  but not found in the schema.

    Returns:
        str: A markdown formatted string with the narrative.
    """
    if not parsed_kpi_data:
        return "No KPI data was provided or parsed successfully."

    if not kpi_only_nodes_set:
        return "All KPIs appear to have their required tables defined in the schema based on table name matching."

    at_risk_kpis = []
    for kpi_item in parsed_kpi_data:
        kpi_name = kpi_item.get("kpi_name", "Unnamed KPI")
        data_required = kpi_item.get("data_required", [])

        missing_tables_for_this_kpi = []
        for req_item in data_required:
            table_name = req_item.get("table_name")
            if table_name and table_name in kpi_only_nodes_set:
                missing_tables_for_this_kpi.append(table_name)

        if missing_tables_for_this_kpi:
            unique_missing_tables = sorted(list(set(missing_tables_for_this_kpi)))
            at_risk_kpis.append({
                "name": kpi_name,
                "missing_tables": ", ".join(unique_missing_tables)
            })

    if not at_risk_kpis:
         return "All KPIs appear to have their required tables defined in the schema based on table name matching."


    narrative = "The following KPIs may be **uncomputable or at risk** due to required tables not being found in the schema definitions:\n"
    for kpi_info in at_risk_kpis:
        narrative += f"- **{kpi_info['name']}**: Requires missing table(s): *{kpi_info['missing_tables']}*\n"

    narrative += "\nThis highlights a need to define these tables in the schema or verify the KPI data requirements."
    return narrative

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    class MockGraph:
        def __init__(self, nodes=None, edges=None):
            self._nodes = nodes if nodes is not None else []
            self._edges = edges if edges is not None else []
        def number_of_nodes(self): return len(self._nodes)
        def number_of_edges(self): return len(self._edges)
        def nodes(self): return self._nodes
        def adj(self):
            adj_dict = {node: {} for node in self._nodes}
            for u, v in self._edges:
                adj_dict[u][v] = {}
                adj_dict[v][u] = {}
            return adj_dict

    mock_schema_analysis_full = {
        'degree_centrality': {'TableA': 0.8, 'TableB': 0.6, 'TableC': 0.5, 'TableD': 0.3},
        'betweenness_centrality': {'TableA': 0.0, 'TableB': 0.5, 'TableC': 0.0, 'TableD': 0.0}
    }
    mock_kpi_analysis_full = {
        'degree_centrality': {'TableB': 0.7, 'TableC': 0.9, 'TableE': 0.5}
    }
    mock_schema_analysis_empty = { 'degree_centrality': {} }
    mock_kpi_analysis_empty = { 'degree_centrality': {} }

    schema_graph_obj_full = MockGraph(nodes=['TableA', 'TableB', 'TableC', 'TableD'], edges=[('TableA','TableB'), ('TableB','TableC')])
    kpi_graph_obj_full = MockGraph(nodes=['TableB', 'TableC', 'TableE'], edges=[('TableB','TableC')])
    empty_graph = MockGraph()

    print("--- Schema Narrative (Full Data) ---")
    print(generate_schema_narrative(schema_graph_obj_full, mock_schema_analysis_full))
    print("\n--- KPI Narrative (Full Data) ---")
    print(generate_kpi_narrative(kpi_graph_obj_full, mock_kpi_analysis_full))
    print("\n--- Comparison Narrative (Full Data) ---")
    print(generate_comparison_narrative(
        schema_graph_obj_full, kpi_graph_obj_full,
        common_nodes={'TableB', 'TableC'},
        schema_only_nodes={'TableA', 'TableD'},
        kpi_only_nodes={'TableE'}
    ))

    print("\n--- Schema Narrative (Empty Graph) ---")
    print(generate_schema_narrative(empty_graph, mock_schema_analysis_empty))
    print("\n--- KPI Narrative (Empty Graph) ---")
    print(generate_kpi_narrative(empty_graph, mock_kpi_analysis_empty))
    print("\n--- Comparison Narrative (One Empty Graph) ---")
    print(generate_comparison_narrative(
        schema_graph_obj_full, empty_graph,
        common_nodes=set(),
        schema_only_nodes=set(schema_graph_obj_full.nodes()),
        kpi_only_nodes=set()
    ))
    print("\n--- Comparison Narrative (Both Empty Graphs) ---")
    print(generate_comparison_narrative(
        empty_graph, empty_graph,
        common_nodes=set(),
        schema_only_nodes=set(),
        kpi_only_nodes=set()
    ))
    print("\n--- Schema Narrative (Graph with no edges) ---")
    no_edge_graph = MockGraph(nodes=['X','Y','Z'])
    print(generate_schema_narrative(no_edge_graph, {'degree_centrality': {'X':0,'Y':0,'Z':0}}))

    print("\n--- Get Top N (with zero scores) ---")
    print(get_top_n_central_nodes({'degree_centrality': {'A':0, 'B':0}}, n=2))
    print("\n--- Get Top N (some positive) ---")
    print(get_top_n_central_nodes({'degree_centrality': {'A':0.5, 'B':0, 'C':0.8}}, n=3))

    print("\n--- Executive Summary Narrative (KPIs at Risk) ---")
    sample_kpi_data_for_exec = [
        {"kpi_name": "Sales Growth Q1", "data_required": [{"table_name": "Sales"}, {"table_name": "Calendar"}]},
        {"kpi_name": "Marketing ROI", "data_required": [{"table_name": "Campaigns"}, {"table_name": "Expenses_Marketing"}]},
        {"kpi_name": "Customer Churn", "data_required": [{"table_name": "Customers"}, {"table_name": "Subscriptions"}]}
    ]
    kpi_only_tables_for_exec = {"Expenses_Marketing", "Subscriptions", "NonExistentTable"}
    print(generate_executive_summary_narrative(sample_kpi_data_for_exec, kpi_only_tables_for_exec))

    kpi_only_tables_empty_for_exec = set()
    print(generate_executive_summary_narrative(sample_kpi_data_for_exec, kpi_only_tables_empty_for_exec))

    no_kpi_data_for_exec = []
    print(generate_executive_summary_narrative(no_kpi_data_for_exec, kpi_only_tables_for_exec))
