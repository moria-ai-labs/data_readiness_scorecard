import os
import sys

if __name__ == '__main__':
    # This block ensures that when app.py is run directly (e.g., python app/app.py),
    # Python can correctly resolve imports relative to the 'app' package.
    # It adds the project's root directory (the parent directory of 'app') to sys.path.
    # This allows Python's import system to find the 'app' package itself.
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import dash
import dash_bootstrap_components as dbc # Added import
from dash import dcc, html, dash_table
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
from app.src import narrative_generator as ng


# Initialize the Dash application
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.MINTY] # Changed theme to MINTY
)
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

def create_narrative_summary_tab_layout():
    return html.Div([
        html.Div(id='narrative-summary-error-message', style=error_message_style),
        dcc.Loading(
            id='loading-narrative-summary',
            children=[
                dcc.Markdown(id='narrative-summary-content', style={'whiteSpace': 'pre-wrap', 'padding': '15px', 'border': '1px solid #eee', 'borderRadius': '5px'})
            ],
            type="circle"
        )
    ], style=tab_content_style)

# Define the application layout
app.layout = html.Div([
    html.Div(className='app-header', children=[ # New header div
        html.Img(id='logo-img', src=app.get_asset_url('logo.jpg'), style={'height':'50px', 'marginRight':'15px', 'verticalAlign':'middle'}), # Changed to logo.jpg
        html.H1("Data Readiness Scorecard", style={**app_title_style, 'display':'inline-block', 'verticalAlign':'middle'}) # Moved H1, adjusted style for inline
    ], style={'display':'flex', 'alignItems':'center', 'justifyContent':'center', 'marginBottom': '20px'}), # Header div style

    html.Div([ # This was the previous first main Div for uploads
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
        dcc.Tab(label='Narrative Summary', value='tab-narrative-summary'),
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
    elif tab_value == 'tab-narrative-summary':
        return create_narrative_summary_tab_layout()
    return html.Div([html.H3("Select a tab")])


# --- Helper function for graph visualization (reverted) ---
# Note: This function signature matches the one from the revert, not the one with active/inactive node colors.
# If the subtask requires the more advanced create_network_figure, this would need to be adjusted.
# For now, proceeding with the signature that was present after the last revert.
def create_network_figure(graph, graph_title="Network Visualization", node_color='#ADD8E6', layout_seed=42, edge_hover_texts_custom=None):
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

    pos = nx.spring_layout(graph, seed=layout_seed, k=0.9) # Always calculate layout

    edge_x_coords = []
    edge_y_coords = []
    edge_hover_texts_final = []
    # Create edges only if graph exists and has nodes (implicitly, edges need nodes)
    if graph and graph.nodes():
        for i, edge in enumerate(graph.edges(data=True)):
            if edge[0] not in pos or edge[1] not in pos: # Ensure nodes are in layout
                continue
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x_coords.extend([x0, x1, None])
            edge_y_coords.extend([y0, y1, None])
            if edge_hover_texts_custom and i * 3 + 1 < len(edge_hover_texts_custom):
                edge_hover_texts_final.extend([edge_hover_texts_custom[i*3], edge_hover_texts_custom[i*3+1], None])
            else:
                edge_hover_texts_final.extend([f"Edge: {edge[0]} - {edge[1]}", f"Edge: {edge[0]} - {edge[1]}", None])

    edge_trace = go.Scatter(
        x=edge_x_coords, y=edge_y_coords,
        line=dict(width=0.7, color='#888'),
        hoverinfo='text',
        hovertext=edge_hover_texts_final,
        mode='lines')

    node_x_coords, node_y_coords, node_text_labels, node_hover_information = [], [], [], []
    node_marker_sizes = []

    # Iterate only over nodes present in the graph for drawing
    if graph and graph.nodes():
        for node, adjacencies in graph.adjacency():
            if node not in pos: # Ensure node is in layout
                continue
            current_x, current_y = pos[node]
            node_x_coords.append(current_x)
            node_y_coords.append(current_y)
            node_text_labels.append(str(node))
            num_connections = len(adjacencies)
            node_hover_information.append(f"Table: {node}<br># Connections: {num_connections}")
            node_marker_sizes.append(num_connections * 5 + 10)

    node_trace = go.Scatter(
        x=node_x_coords, y=node_y_coords,
        mode='markers+text',
        text=node_text_labels,
        textposition="top center",
        hoverinfo='text',
        hovertext=node_hover_information,
        marker=dict(
            showscale=False,
            size=node_marker_sizes,
            sizemode='diameter',
            color=node_color, # Single color for all nodes in this graph
            line_width=2
        )
    )

    fig_layout = go.Layout(
        title={'text': graph_title, 'font': {'size': 16}},
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
    summary_div_children = [html.P("Please upload both Schema and KPI JSON files to see the comparison.", style={'textAlign': 'center'})]
    error_message_list = []
    schema_graph, kpi_graph = None, None
    schema_edge_hover_texts, kpi_edge_hover_texts = None, None

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

            if schema_graph and schema_graph.nodes():
                schema_edge_hover_texts = []
                for edge in schema_graph.edges(data=True):
                    hover_text = f"Edge: {edge[0]} - {edge[1]}<br>"
                    if 'shared_field' in edge[2]: hover_text += f"Shared Field: {edge[2]['shared_field']}<br>"
                    if 'domain' in edge[2]: hover_text += f"Domain: {edge[2]['domain']}"
                    schema_edge_hover_texts.extend([hover_text, hover_text, None])
        except Exception as e:
            error_message_list.append(html.P(f"Error processing Schema file ({schema_filename}): {str(e)}"))
            schema_graph = None

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

            if kpi_graph and kpi_graph.nodes():
                kpi_edge_hover_texts = []
                for edge in kpi_graph.edges(data=True):
                    kpi_links = edge[2].get('kpi_links', [])
                    hover_text = f"Edge: {edge[0]} - {edge[1]}<br>KPIs: {', '.join(kpi_links)}"
                    kpi_edge_hover_texts.extend([hover_text, hover_text, None])
        except Exception as e:
            error_message_list.append(html.P(f"Error processing KPI file ({kpi_filename}): {str(e)}"))
            kpi_graph = None

    # Determine node sets for summary (this part is fine)
    schema_nodes_set = set(schema_graph.nodes()) if schema_graph else set()
    kpi_nodes_set = set(kpi_graph.nodes()) if kpi_graph else set()

    # Common layout calculation is removed.
    # common_node_positions = None # Ensure it's not used or defined from previous versions.

    # Generate figures - no fixed_positions passed
    schema_fig = create_network_figure(
        graph=schema_graph, graph_title="Schema Network (Comparison View)",
        node_color='#ADD8E6',
        edge_hover_texts_custom=schema_edge_hover_texts
    )
    kpi_fig = create_network_figure(
        graph=kpi_graph, graph_title="KPI Network (Comparison View)",
        node_color='#FFB6C1',
        edge_hover_texts_custom=kpi_edge_hover_texts
    )

    # Update Summary Statistics (this logic should be mostly the same as before)
    # This logic for summary_div_children remains largely the same,
    # as it depends on schema_nodes_set and kpi_nodes_set which are still calculated.
    if not error_message_list and (schema_graph is not None or kpi_graph is not None):
        summary_div_children = [
            html.P(f"Total Tables in Schema: {len(schema_nodes_set)}"),
            html.P(f"Total Tables in KPI: {len(kpi_nodes_set)}"),
        ]
        if schema_graph is not None and kpi_graph is not None:
            common_nodes = schema_nodes_set & kpi_nodes_set
            schema_only_nodes = schema_nodes_set - kpi_nodes_set
            kpi_only_nodes = kpi_nodes_set - schema_nodes_set
            summary_div_children.extend([
                html.H5("Common Tables:"),
                html.Ul([html.Li(node) for node in sorted(list(common_nodes))]) if common_nodes else html.P("None"),
                html.H5("Tables Only in Schema:"),
                html.Ul([html.Li(node) for node in sorted(list(schema_only_nodes))]) if schema_only_nodes else html.P("None"),
                html.H5("Tables Only in KPI:"),
                html.Ul([html.Li(node) for node in sorted(list(kpi_only_nodes))]) if kpi_only_nodes else html.P("None"),
            ])
        elif not schema_contents and not kpi_contents: # Back to initial state if both files are removed
             summary_div_children = [html.P("Please upload both Schema and KPI JSON files to see the comparison.", style={'textAlign': 'center'})]

    elif error_message_list: # If there were errors, don't show potentially misleading summary counts
        summary_div_children = [] # Errors will be shown in the main error div

    final_error_message = html.Div(error_message_list) if error_message_list else None
    return summary_div_children, schema_fig, kpi_fig, final_error_message


# Callback for Narrative Summary Tab
@app.callback(
    [Output('narrative-summary-content', 'children'),
     Output('narrative-summary-error-message', 'children')],
    [Input('upload-schema-data', 'contents'),
     Input('upload-kpi-data', 'contents')],
    [State('upload-schema-data', 'filename'),
     State('upload-kpi-data', 'filename')]
)
def update_narrative_summary_tab(schema_contents, kpi_contents, schema_filename, kpi_filename):
    narrative_text = ""
    error_message_children = []

    if schema_contents is None and kpi_contents is None:
        narrative_text = "Please upload both Schema and KPI JSON files to generate the narrative summary."
        return narrative_text, None

    schema_graph, kpi_graph = None, None
    schema_analysis, kpi_analysis = None, None

    if schema_contents:
        try:
            s_content_type, s_content_string = schema_contents.split(',')
            s_decoded = base64.b64decode(s_content_string)
            s_json_data_str = s_decoded.decode('utf-8')
            parsed_schema = dp.parse_schema_json(s_json_data_str)
            if not parsed_schema: raise ValueError("Schema data is empty or could not be parsed.")
            schema_graph = nb.build_schema_network(parsed_schema)
            if schema_graph.number_of_nodes() > 0:
               schema_analysis = na.analyze_network(schema_graph)
            else:
               schema_analysis = {}
        except Exception as e:
            error_message_children.append(html.P(f"Error processing Schema file ({schema_filename}): {str(e)}"))
            schema_graph = None
    else:
        error_message_children.append(html.P("Schema JSON file not uploaded. Some parts of the narrative may be incomplete or unavailable."))

    if kpi_contents:
        try:
            k_content_type, k_content_string = kpi_contents.split(',')
            k_decoded = base64.b64decode(k_content_string)
            k_json_data_str = k_decoded.decode('utf-8')
            parsed_kpis = dp.parse_kpi_json(k_json_data_str)
            if not parsed_kpis: raise ValueError("KPI data is empty or could not be parsed.")
            kpi_graph = nb.build_kpi_network(parsed_kpis)
            if kpi_graph.number_of_nodes() > 0:
               kpi_analysis = na.analyze_network(kpi_graph)
            else:
               kpi_analysis = {}
        except Exception as e:
            error_message_children.append(html.P(f"Error processing KPI file ({kpi_filename}): {str(e)}"))
            kpi_graph = None
    else:
        error_message_children.append(html.P("KPI JSON file not uploaded. Some parts of the narrative may be incomplete or unavailable."))

    # Generate Narrative
    # Proceed to generate narratives even if one part is missing, functions in ng should handle None inputs
    schema_text = ng.generate_schema_narrative(schema_graph, schema_analysis if schema_analysis else {})
    kpi_text = ng.generate_kpi_narrative(kpi_graph, kpi_analysis if kpi_analysis else {})

    comp_text = "Comparison insights require both schema and KPI data to be successfully processed.\n"
    if schema_graph is not None and kpi_graph is not None: # Both must be valid for comparison part
        schema_nodes = set(schema_graph.nodes())
        kpi_nodes = set(kpi_graph.nodes())
        common_nodes = schema_nodes & kpi_nodes
        schema_only_nodes = schema_nodes - kpi_nodes
        kpi_only_nodes = kpi_nodes - schema_nodes
        comp_text = ng.generate_comparison_narrative(schema_graph, kpi_graph, common_nodes, schema_only_nodes, kpi_only_nodes)
    elif error_message_children and not (schema_graph is not None and kpi_graph is not None) :
        # If there were errors and we can't do a full comparison
        comp_text = "Comparison narrative cannot be generated due to errors or missing data for one or both inputs."

    narrative_text = f"# Data Narrative Summary\n\n## Schema Overview\n{schema_text}\n\n## KPI Overview\n{kpi_text}\n\n## Comparison Insights\n{comp_text}"

    # If there were initial "file not uploaded" messages but then one file *was* processed, clear those initial messages.
    # Only show actual processing errors.
    if (schema_contents and schema_graph is None and not any(f"Schema file ({schema_filename})" in str(p.children) for p in error_message_children if hasattr(p, 'children'))) or \
       (kpi_contents and kpi_graph is None and not any(f"KPI file ({kpi_filename})" in str(p.children) for p in error_message_children if hasattr(p, 'children'))):
        # This means a file was provided, but graph is None (error), but no *specific* error for it was logged.
        # This case might be complex to get right, the current error logging is likely sufficient.
        pass


    final_error_message_div = html.Div(error_message_children) if error_message_children else None
    return narrative_text, final_error_message_div


# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) # Changed to app.run
