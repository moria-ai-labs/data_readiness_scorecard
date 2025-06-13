import os
import sys

if __name__ == '__main__':
    # This block ensures that when app.py is run directly (e.g., python app/app.py),
    # Python can correctly resolve imports relative to the 'app' package.
    # It adds the project's root directory (the parent directory of 'app') to sys.path.
    # This allows Python's import system to find the 'app' package itself,
    # and then subsequently resolve relative imports like '.src'.

    # Path to the directory containing this script (app.py), e.g., /path/to/project/app
    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the project root directory, e.g., /path/to/project
    project_root = os.path.dirname(current_script_dir)

    # Add project_root to sys.path if it's not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Additionally, if app.py is run as the main script, __package__ might be None.
    # For relative imports (`from .src ...`) to work reliably in this scenario,
    # __package__ should ideally be set to the name of the package ('app').
    # However, modifying __package__ directly can be tricky and might have side effects.
    # The sys.path modification above is usually sufficient if the imports are
    # structured as `from app.src import ...` or if relative imports work once `app` is findable.
    # Given the existing imports are `from .src import ...`, ensuring `app`'s parent is in
    # sys.path makes `app` discoverable as a top-level package.
    # If `app.py` is then implicitly part of this discoverable `app` package,
    # the relative imports should resolve.

    # If issues persist, one might need to change imports from `from .src` to `from app.src`
    # after this sys.path modification. For now, we keep `from .src` as per previous steps.

import dash
from dash import dcc, html, dash_table # Updated imports
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import base64
import io
import json
import plotly.graph_objects as go
import networkx as nx

# Use absolute imports from the project root (which is added to sys.path)
from app.src import data_parser as dp
from app.src import network_builder as nb
from app.src import network_analysis as na


# Initialize the Dash application
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Data Readiness Scorecard"

# --- Global Styles ---
app_title_style = {'textAlign': 'center', 'color': '#007BFF', 'marginBottom': '20px'}
upload_style = {
    'width': '100%', 'height': '60px', 'lineHeight': '60px',
    'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
    'textAlign': 'center', 'margin': '10px 0px' # Adjusted margin for consistency
}
tab_content_style = {'padding': '10px'}
error_message_style = {'color': 'red', 'margin': '10px', 'padding': '10px', 'border': '1px solid red', 'borderRadius': '5px'}


# --- Layout Helper Functions ---
def create_schema_tab_layout():
    return html.Div([
        html.Div(id='schema-error-message', style=error_message_style),
        dcc.Loading(id="loading-schema-graph", children=[dcc.Graph(id='schema-network-graph')], type="circle"),
        html.Hr(),
        html.H4("Centrality Measures"),
        dcc.Loading(id="loading-schema-centrality", children=[html.Div(id='schema-centrality-table')], type="circle"),
    ], style=tab_content_style)

def create_kpi_tab_layout():
    return html.Div([
        html.Div(id='kpi-error-message', style=error_message_style),
        dcc.Loading(id="loading-kpi-graph", children=[dcc.Graph(id='kpi-network-graph')], type="circle"),
        html.Hr(),
        html.H4("Centrality Measures"),
        dcc.Loading(id="loading-kpi-centrality", children=[html.Div(id='kpi-centrality-table')], type="circle"),
    ], style=tab_content_style)

def create_comparison_tab_layout():
    return html.Div([
        html.Div(id='comparison-error-message', style=error_message_style),
        html.H4("Network Comparison Summary"),
        dcc.Loading(id="loading-comparison-summary", children=[html.Div(id='comparison-summary-stats')], type="circle"),
        html.Hr(),
        html.Div([
            html.Div([
                html.H5("Schema Network"),
                dcc.Loading(id="loading-comparison-schema-graph", children=[dcc.Graph(id='comparison-schema-graph')], type="circle")
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '5px'}),
            html.Div([
                html.H5("KPI Network"),
                dcc.Loading(id="loading-comparison-kpi-graph", children=[dcc.Graph(id='comparison-kpi-graph')], type="circle")
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '5px'})
        ], style={'display': 'flex', 'flexDirection': 'row'})
    ], style=tab_content_style)

# Define the application layout
app.layout = html.Div([
    html.H1("Data Readiness Scorecard", style=app_title_style),
    html.Div([
        html.Div([ # Wrapper div for schema upload
            dcc.Upload(
                id='upload-schema-data',
                children=html.Div(['Drag and Drop or ', html.A('Select Schema JSON File')]),
                style=upload_style,
                multiple=False
            ),
        ], style={'width': '45%'}),
        html.Div([ # Wrapper div for kpi upload
            dcc.Upload(
                id='upload-kpi-data',
                children=html.Div(['Drag and Drop or ', html.A('Select KPI JSON File')]),
                style=upload_style,
                multiple=False
            ),
        ], style={'width': '45%'}),
    ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-around', 'marginBottom': '20px'}),

    dcc.Tabs(id='tabs-main', value='tab-schema-analysis', children=[
        dcc.Tab(label='Schema Network Analysis', value='tab-schema-analysis'),
        dcc.Tab(label='KPI Network Analysis', value='tab-kpi-analysis'),
        dcc.Tab(label='Network Comparison', value='tab-comparison'),
    ]),
    html.Div(id='tabs-content-main')
])


# --- Callbacks ---

# Callback to render main tab content
@app.callback(
    Output('tabs-content-main', 'children'),
    Input('tabs-main', 'value')
)
def render_tab_content(tab_value):
    if tab_value == 'tab-schema-analysis':
        return create_schema_tab_layout()
    elif tab_value == 'tab-kpi-analysis':
        return create_kpi_tab_layout()
    elif tab_value == 'tab-comparison':
        return create_comparison_tab_layout()
    return html.Div([html.H3("Select a tab")])


# --- Helper function for graph visualization ---
def create_network_figure(graph, graph_title="Network Visualization", node_color='#ADD8E6', layout_seed=42, edge_hover_texts_custom=None, fixed_positions=None):
    if not graph or not graph.nodes():
        fig = go.Figure()
        fig.update_layout(
            title_text=f"{graph_title} - No data to display",
            xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False, 'visible': False},
            yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False, 'visible': False},
            showlegend=False,
            plot_bgcolor='white',
            annotations=[dict(text="No data to display or network is empty.", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)]
        )
        return fig

    if fixed_positions:
        pos = fixed_positions
        # Ensure all nodes in the current graph have positions if fixed_positions is used
        # If a node from `graph` is not in `fixed_positions`, spring_layout might be needed for those
        # For simplicity, assume fixed_positions contains all necessary nodes from `graph`
        # Or, filter pos: pos = {k: v for k, v in fixed_positions.items() if k in graph.nodes()}
        # However, spring_layout on a subgraph might differ too much.
        # Best to ensure fixed_positions is comprehensive for the nodes in `graph`.
        # Current logic iterates graph.nodes() and graph.edges(), so missing nodes in pos would error.
        # Let's assume `fixed_positions` is correctly prepared by the caller for the given `graph`.
    else:
        pos = nx.spring_layout(graph, seed=layout_seed, k=0.9)

    edge_x = []
    edge_y = []
    edge_hover_texts_final = []
    for i, edge in enumerate(graph.edges(data=True)):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        if edge_hover_texts_custom and i < len(edge_hover_texts_custom):
             # custom hover texts are provided per edge (pair + None)
            edge_hover_texts_final.extend([edge_hover_texts_custom[i*3], edge_hover_texts_custom[i*3+1], None])
        else: # Default hover text if not provided
            edge_hover_texts_final.extend([f"Edge: {edge[0]} - {edge[1]}", f"Edge: {edge[0]} - {edge[1]}", None])


    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.7, color='#888'),
        hoverinfo='text',
        hovertext=edge_hover_texts_final,
        mode='lines')

    node_x = []
    node_y = []
    node_texts = []
    node_hover_texts = []
    node_sizes = []
    for node, adjacencies in graph.adjacency():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_texts.append(node)
        node_hover_texts.append(f"Table: {node}<br># Connections: {len(adjacencies)}")
        node_sizes.append(len(adjacencies) * 5 + 10)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_texts,
        textposition="top center",
        hoverinfo='text',
        hovertext=node_hover_texts,
        marker=dict(
            showscale=False,
            size=node_sizes,
            sizemode='diameter',
            color=node_color,
            line_width=2
        )
    )

    fig_layout = go.Layout(
        title={'text': graph_title, 'font': {'size': 16}}, # Corrected title font setting
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    return go.Figure(data=[edge_trace, node_trace], layout=fig_layout)


# Callback for Schema Analysis Tab
@app.callback(
    [Output('schema-network-graph', 'figure'),
     Output('schema-centrality-table', 'children'),
     Output('schema-error-message', 'children')],
    [Input('upload-schema-data', 'contents')],
    [State('upload-schema-data', 'filename')]
)
def update_schema_analysis_tab(contents, filename):
    fig = go.Figure()
    centrality_div = html.Div()
    error_message = None

    if contents is None:
        raise PreventUpdate

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        json_data_str = decoded.decode('utf-8')
        parsed_data = dp.parse_schema_json(json_data_str) # Renamed for clarity

        if not parsed_data:
            error_message = html.Div(f"Error processing file {filename}: Schema data could not be parsed or is empty.")
            return fig, centrality_div, error_message

        graph = nb.build_schema_network(parsed_data) # Renamed for clarity

        if not parsed_data:
            error_message = html.Div(f"Error processing Schema file {filename}: Data could not be parsed or is empty.")
            return fig, html.P("No schema data to analyze."), error_message

        graph = nb.build_schema_network(parsed_data)

        # Generate custom hover texts for schema graph edges
        schema_edge_hover_texts = []
        if graph.nodes():
            for edge in graph.edges(data=True):
                hover_text = f"Edge: {edge[0]} - {edge[1]}<br>"
                if 'shared_field' in edge[2]:
                    hover_text += f"Shared Field: {edge[2]['shared_field']}<br>"
                if 'domain' in edge[2]:
                    hover_text += f"Domain: {edge[2]['domain']}"
                schema_edge_hover_texts.extend([hover_text, hover_text, None]) # Add for both ends of segment and for the None

        fig = create_network_figure(graph, "Schema Network Visualization", '#ADD8E6', 42, schema_edge_hover_texts)
        if not graph.nodes(): # If graph is empty after building (e.g. no tables in schema)
             centrality_div = html.P("Schema network is empty, no centrality measures to display.")
             # fig would already have a "No data" message from create_network_figure
        else:
            analysis_results = na.analyze_network(graph)
            if analysis_results:
                tables_data = []
                metric_keys = [k for k in ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality'] if k in analysis_results and analysis_results[k]]
                headers = ["Table Name"] + [key.replace('_', ' ').title() for key in metric_keys]

                all_nodes = set()
                for metric_name in metric_keys:
                    metric_data = analysis_results.get(metric_name, {})
                    if isinstance(metric_data, dict):
                        all_nodes.update(metric_data.keys())

                sorted_nodes = sorted(list(all_nodes))

                for node in sorted_nodes:
                    row = {'Table Name': node}
                    for metric_name in metric_keys:
                        values_dict = analysis_results.get(metric_name, {})
                        col_name = metric_name.replace('_', ' ').title()
                        value = values_dict.get(node, 'N/A')
                        row[col_name] = f"{value:.4f}" if isinstance(value, float) else str(value)
                    tables_data.append(row)

                centrality_table = dash_table.DataTable(
                    id='schema-centrality-metrics-table',
                    columns=[{"name": i, "id": i} for i in headers],
                    data=tables_data,
                    page_size=10,
                    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                    style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial', 'fontSize': '12px'},
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
                    ],
                    sort_action="native",
                )
                centrality_div = html.Div([centrality_table])
            else: # This else corresponds to 'if analysis_results:'
                centrality_div = html.P("Centrality analysis did not return any results for the schema network.")


    except json.JSONDecodeError as e:
        error_message = html.Div(f"Error decoding JSON from Schema file {filename}: {str(e)}")
        fig = go.Figure().update_layout(title_text="Error in Schema data processing")
        centrality_div = html.P("Cannot calculate centrality due to schema data error.")
    except ValueError as e:
        error_message = html.Div(f"Error processing Schema file {filename}: {str(e)}")
        fig = go.Figure().update_layout(title_text="Error in Schema data processing")
        centrality_div = html.P("Cannot calculate centrality due to schema data error.")
    except Exception as e:
        error_message = html.Div(f"An unexpected error occurred with Schema file {filename}: {str(e)}")
        fig = go.Figure().update_layout(title_text="Error in Schema data processing")
        centrality_div = html.P("Cannot calculate centrality due to schema data error.")

    return fig, centrality_div, error_message


# Callback for KPI Analysis Tab
@app.callback(
    [Output('kpi-network-graph', 'figure'),
     Output('kpi-centrality-table', 'children'),
     Output('kpi-error-message', 'children')],
    [Input('upload-kpi-data', 'contents')],
    [State('upload-kpi-data', 'filename')]
)
def update_kpi_analysis_tab(contents, filename):
    fig = go.Figure()
    centrality_div = html.Div()
    error_message = None

    if contents is None:
        raise PreventUpdate

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        json_data_str = decoded.decode('utf-8')
        parsed_data = dp.parse_kpi_json(json_data_str) # Use KPI parser

        if not parsed_data:
            error_message = html.Div(f"Error processing file {filename}: KPI data could not be parsed or is empty.")
            return fig, centrality_div, error_message

        graph = nb.build_kpi_network(parsed_data) # Use KPI network builder

        if not parsed_data:
            error_message = html.Div(f"Error processing KPI file {filename}: Data could not be parsed or is empty.")
            return fig, html.P("No KPI data to analyze."), error_message

        graph = nb.build_kpi_network(parsed_data)

        # Generate custom hover texts for KPI graph edges
        kpi_edge_hover_texts = []
        if graph.nodes():
            for edge in graph.edges(data=True):
                kpi_links = edge[2].get('kpi_links', [])
                hover_text = f"Edge: {edge[0]} - {edge[1]}<br>KPIs: {', '.join(kpi_links)}"
                kpi_edge_hover_texts.extend([hover_text, hover_text, None])

        fig = create_network_figure(graph, "KPI Network Visualization", '#FFB6C1', 42, kpi_edge_hover_texts)
        if not graph.nodes(): # If graph is empty after building
            centrality_div = html.P("KPI network is empty, no centrality measures to display.")
        else: # This else belongs to the if not graph.nodes() from KPI section
            analysis_results = na.analyze_network(graph)
            if analysis_results: # This if is for analysis_results
                tables_data = []
                metric_keys = [k for k in ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality'] if k in analysis_results and analysis_results[k]]
                headers = ["Table Name"] + [key.replace('_', ' ').title() for key in metric_keys]

                all_nodes = set()
                for metric_name in metric_keys:
                    metric_data = analysis_results.get(metric_name, {})
                    if isinstance(metric_data, dict):
                        all_nodes.update(metric_data.keys())

                sorted_nodes = sorted(list(all_nodes))

                for node in sorted_nodes:
                    row = {'Table Name': node}
                    for metric_name in metric_keys:
                        values_dict = analysis_results.get(metric_name, {})
                        col_name = metric_name.replace('_', ' ').title()
                        value = values_dict.get(node, 'N/A')
                        row[col_name] = f"{value:.4f}" if isinstance(value, float) else str(value)
                    tables_data.append(row)

                centrality_table = dash_table.DataTable(
                    id='kpi-centrality-metrics-table', # Different ID
                    columns=[{"name": i, "id": i} for i in headers],
                    data=tables_data,
                    page_size=10,
                    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                    style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial', 'fontSize': '12px'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}],
                    sort_action="native",
                )
                centrality_div = html.Div([centrality_table])
            else: # This else corresponds to 'if analysis_results:'
                centrality_div = html.P("Centrality analysis did not return any results for KPI network.")

    except json.JSONDecodeError as e:
        error_message = html.Div(f"Error decoding JSON from KPI file {filename}: {str(e)}")
        fig = go.Figure().update_layout(title_text="Error in KPI data processing")
        centrality_div = html.P("Cannot calculate centrality due to KPI data error.")
    except ValueError as e:
        error_message = html.Div(f"Error processing KPI file {filename}: {str(e)}")
        fig = go.Figure().update_layout(title_text="Error in KPI data processing")
        centrality_div = html.P("Cannot calculate centrality due to KPI data error.")
    except Exception as e:
        error_message = html.Div(f"An unexpected error occurred with KPI file {filename}: {str(e)}")
        fig = go.Figure().update_layout(title_text="Error in KPI data processing")
        centrality_div = html.P("Cannot calculate centrality due to KPI data error.")

    return fig, centrality_div, error_message

# Callback for Comparison Tab
@app.callback(
    [Output('comparison-summary-stats', 'children'),
     Output('comparison-schema-graph', 'figure'),
     Output('comparison-kpi-graph', 'figure'),
     Output('comparison-error-message', 'children')],
    [Input('upload-schema-data', 'contents'),
     Input('upload-kpi-data', 'contents')],
    [State('upload-schema-data', 'filename'),
     State('upload-kpi-data', 'filename')]
)
def update_comparison_tab(schema_contents, kpi_contents, schema_filename, kpi_filename):
    summary_div_children = [html.P("Please upload both Schema and KPI JSON files to see the comparison.", style={'textAlign': 'center'})]
    # Initialize with empty figures that might show "No data" title from create_network_figure
    schema_fig = create_network_figure(None, "Schema Network") # Default empty state
    kpi_fig = create_network_figure(None, "KPI Network")       # Default empty state
    error_message_list = []
    schema_graph = None # Ensure it's defined in outer scope
    kpi_graph = None    # Ensure it's defined in outer scope


    if not schema_contents and not kpi_contents:
        # If neither file is present, keep the initial message and empty figures
        return summary_div_children, schema_fig, kpi_fig, None

    # Process Schema Data
    if schema_contents:
        try:
            s_content_type, s_content_string = schema_contents.split(',')
            s_decoded = base64.b64decode(s_content_string)
            s_json_data_str = s_decoded.decode('utf-8')
            parsed_schema = dp.parse_schema_json(s_json_data_str)
            if not parsed_schema:
                raise ValueError("Schema data could not be parsed or is empty.")
            schema_graph = nb.build_schema_network(parsed_schema)
        except Exception as e:
            error_message_list.append(html.P(f"Error processing Schema file ({schema_filename}): {str(e)}"))
            schema_graph = None # Ensure graph is None on error

    # Process KPI Data
    if kpi_contents:
        try:
            k_content_type, k_content_string = kpi_contents.split(',')
            k_decoded = base64.b64decode(k_content_string)
            k_json_data_str = k_decoded.decode('utf-8')
            parsed_kpis = dp.parse_kpi_json(k_json_data_str)
            if not parsed_kpis:
                raise ValueError("KPI data could not be parsed or is empty.")
            kpi_graph = nb.build_kpi_network(parsed_kpis)
        except Exception as e:
            error_message_list.append(html.P(f"Error processing KPI file ({kpi_filename}): {str(e)}"))
            kpi_graph = None # Ensure graph is None on error

    common_node_positions = None
    # Attempt to create common layout only if both graphs are valid and non-empty
    if schema_graph and schema_graph.nodes() and kpi_graph and kpi_graph.nodes():
        all_nodes = set(schema_graph.nodes()) | set(kpi_graph.nodes())
        combined_layout_graph = nx.Graph()
        combined_layout_graph.add_nodes_from(list(all_nodes))
        # Add edges from both graphs to inform the layout
        combined_layout_graph.add_edges_from(schema_graph.edges())
        combined_layout_graph.add_edges_from(kpi_graph.edges())
        # Ensure enough iterations for potentially larger combined graph
        common_node_positions = nx.spring_layout(combined_layout_graph, seed=42, k=0.9, iterations=50)


    # Generate figures using common_node_positions if available
    if schema_graph: # Only generate if schema_graph was successfully built
        schema_edge_hover_texts = []
        if schema_graph.nodes():
            for edge in schema_graph.edges(data=True):
                hover_text = f"Edge: {edge[0]} - {edge[1]}<br>"
                if 'shared_field' in edge[2]: hover_text += f"Shared Field: {edge[2]['shared_field']}<br>"
                if 'domain' in edge[2]: hover_text += f"Domain: {edge[2]['domain']}"
                schema_edge_hover_texts.extend([hover_text, hover_text, None])
        schema_fig = create_network_figure(schema_graph, "Schema Network", '#ADD8E6', 42, schema_edge_hover_texts, fixed_positions=common_node_positions)

    if kpi_graph: # Only generate if kpi_graph was successfully built
        kpi_edge_hover_texts = []
        if kpi_graph.nodes():
            for edge in kpi_graph.edges(data=True):
                kpi_links = edge[2].get('kpi_links', [])
                hover_text = f"Edge: {edge[0]} - {edge[1]}<br>KPIs: {', '.join(kpi_links)}"
                kpi_edge_hover_texts.extend([hover_text, hover_text, None])
        kpi_fig = create_network_figure(kpi_graph, "KPI Network", '#FFB6C1', 42, kpi_edge_hover_texts, fixed_positions=common_node_positions)

    # Perform Comparison if both graphs were successfully built (even if one is empty now, graph objects exist)
    if schema_graph is not None and kpi_graph is not None:
        summary_div_children = [] # Clear initial "upload both" message
        schema_nodes = set(schema_graph.nodes())
        kpi_nodes = set(kpi_graph.nodes())
        common_nodes = schema_nodes & kpi_nodes
        schema_only_nodes = schema_nodes - kpi_nodes
        kpi_only_nodes = kpi_nodes - schema_nodes

        summary_div_children.extend([
            html.P(f"Total Tables in Schema: {len(schema_nodes)}"),
            html.P(f"Total Tables in KPI: {len(kpi_nodes)}"),
            html.H5("Common Tables:"),
            html.Ul([html.Li(node) for node in sorted(list(common_nodes))]) if common_nodes else html.P("None"),
            html.H5("Tables Only in Schema:"),
            html.Ul([html.Li(node) for node in sorted(list(schema_only_nodes))]) if schema_only_nodes else html.P("None"),
            html.H5("Tables Only in KPI:"),
            html.Ul([html.Li(node) for node in sorted(list(kpi_only_nodes))]) if kpi_only_nodes else html.P("None"),
        ])
    elif schema_contents and kpi_contents: # Both files uploaded, but one or both graphs failed
        if not error_message_list: # If no specific errors were caught but graphs are not available
             error_message_list.append(html.P("Could not generate comparison. One or both networks are empty or failed to process."))
        summary_div_children = [] # No summary if graphs aren't comparable

    # Final error message div
    final_error_message = html.Div(error_message_list) if error_message_list else None

    return summary_div_children, schema_fig, kpi_fig, final_error_message
    # Removed duplicated block that was here


# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) # Changed to app.run
