import networkx as nx
from itertools import combinations

def build_schema_network(parsed_schema_data: list) -> nx.Graph:
    """
    Builds a network graph from parsed schema data.
    Nodes are tables, and edges represent shared fields between tables within the same domain.
    """
    graph = nx.Graph()
    for domain in parsed_schema_data:
        domain_name = domain.get("domain_name", "UnknownDomain")
        tables_in_domain = domain.get("tables", [])

        # Add all tables from the current domain as nodes
        for table_data in tables_in_domain:
            table_name = table_data.get("table_name")
            if table_name:
                # Prefix with domain_name to ensure uniqueness if table names can repeat across domains
                # However, the problem description implies table_name itself is the node.
                # For now, let's assume table_name is unique enough or the first one encountered takes precedence.
                # If issues arise, we can change node_id to f"{domain_name}.{table_name}"
                graph.add_node(table_name)

        # Identify shared fields within the current domain to create edges
        field_to_tables_map = {}
        for table_data in tables_in_domain:
            table_name = table_data.get("table_name")
            if not table_name:
                continue

            fields = table_data.get("fields", [])
            for field_data in fields:
                field_name = field_data.get("field_name")
                if field_name:
                    if field_name not in field_to_tables_map:
                        field_to_tables_map[field_name] = []
                    if table_name not in field_to_tables_map[field_name]: # Avoid duplicate table entries for the same field
                        field_to_tables_map[field_name].append(table_name)

        # Add edges for tables sharing fields within the same domain
        for field_name, tables_with_field in field_to_tables_map.items():
            if len(tables_with_field) > 1:
                # Add edges between all pairs of tables that share this field
                for table1, table2 in combinations(tables_with_field, 2):
                    graph.add_edge(table1, table2, shared_field=field_name, domain=domain_name)

    return graph

def build_kpi_network(parsed_kpi_data: list) -> nx.Graph:
    """
    Builds a network graph from parsed KPI data.
    Nodes are tables, and edges represent that tables are required together for a KPI.
    """
    graph = nx.Graph()
    for kpi in parsed_kpi_data:
        kpi_name = kpi.get("kpi_name", "UnknownKPI")
        required_tables_data = kpi.get("data_required", [])

        current_kpi_tables = []
        for req_table_info in required_tables_data:
            table_name = req_table_info.get("table_name")
            if table_name:
                graph.add_node(table_name) # Add table as a node
                if table_name not in current_kpi_tables: # Ensure uniqueness for edge creation
                    current_kpi_tables.append(table_name)

        # If this KPI requires two or more tables, add edges between all unique pairs of these tables
        if len(current_kpi_tables) > 1:
            for table1, table2 in combinations(current_kpi_tables, 2):
                # Check if edge already exists to avoid duplicate attributes if multiple KPIs share the same pair
                if graph.has_edge(table1, table2):
                    # If edge exists, append KPI name to existing attribute
                    if "kpi_links" in graph[table1][table2]:
                         if kpi_name not in graph[table1][table2]["kpi_links"]:
                            graph[table1][table2]["kpi_links"].append(kpi_name)
                    else:
                        graph[table1][table2]["kpi_links"] = [kpi_name]
                else:
                    graph.add_edge(table1, table2, kpi_links=[kpi_name])

    return graph
