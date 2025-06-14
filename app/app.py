import os
import sys

if __name__ == '__main__':
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import base64
import io
import json
import plotly.graph_objects as go
import networkx as nx

# Use absolute imports from the project root
from app.src import data_parser as dp
from app.src import network_builder as nb
from app.src import network_analysis as na
from app.src import narrative_generator as ng


# Initialize the Dash application
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.MINTY]
)
app.title = "Data Readiness Scorecard"

# --- Global Styles ---
# (Styles remain the same)
app_title_style = {'textAlign': 'center', 'color': '#007BFF', 'marginBottom': '20px'}
upload_style = {
    'width': '100%', 'height': '60px', 'lineHeight': '60px',
    'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
    'textAlign': 'center', 'margin': '10px 0px'
}
tab_content_style = {'padding': '10px'}
error_message_style = {'color': 'red', 'margin': '10px', 'padding': '10px', 'border': '1px solid red', 'borderRadius': '5px'}

# --- Layout Helper Functions ---
# (Layout functions: create_schema_tab_layout, create_kpi_tab_layout,
#  create_comparison_tab_layout, create_narrative_summary_tab_layout remain unchanged from Turn 83 content,
#  as create_comparison_tab_layout was already updated in Turn 77 to include the combined graph placeholder)
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
                html.H5("Schema Network (Comparison View)"),
                dcc.Loading(id="loading-comparison-schema-graph", children=[dcc.Graph(id='comparison-schema-graph')], type="circle")
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '5px'}),
            html.Div([
                html.H5("KPI Network (Comparison View)"),
                dcc.Loading(id="loading-comparison-kpi-graph", children=[dcc.Graph(id='comparison-kpi-graph')], type="circle")
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '5px'})
        ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
        html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}),
        html.H4("Combined Network View (All Nodes & Edges)", style={'textAlign': 'center', 'marginBottom': '10px'}),
        dcc.Loading(
            id="loading-comparison-combined-graph",
            children=[dcc.Graph(id='comparison-combined-graph')],
            type="circle"
        )
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

# (app.layout definition remains unchanged from Turn 83 content)
app.layout = html.Div([
    html.Div(className='app-header', children=[
        html.Img(id='logo-img', src=app.get_asset_url('logo.jpg'), style={'height':'50px', 'marginRight':'15px', 'verticalAlign':'middle'}),
        html.H1("Data Readiness Scorecard", style={**app_title_style, 'display':'inline-block', 'verticalAlign':'middle'})
    ], style={'display':'flex', 'alignItems':'center', 'justifyContent':'center', 'marginBottom': '20px'}),
    html.Div([
        html.Div([
            dcc.Upload(id='upload-schema-data', children=html.Div(['Drag and Drop or ', html.A('Select Schema JSON File')]), style=upload_style, multiple=False),
        ], style={'width': '45%'}),
        html.Div([
            dcc.Upload(id='upload-kpi-data', children=html.Div(['Drag and Drop or ', html.A('Select KPI JSON File')]), style=upload_style, multiple=False),
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

# (render_tab_content callback remains unchanged from Turn 83 content)
@app.callback(Output('tabs-content-main', 'children'), Input('tabs-main', 'value'))
def render_tab_content(tab_value):
    if tab_value == 'tab-schema-analysis': return create_schema_tab_layout()
    elif tab_value == 'tab-kpi-analysis': return create_kpi_tab_layout()
    elif tab_value == 'tab-comparison': return create_comparison_tab_layout()
    elif tab_value == 'tab-narrative-summary': return create_narrative_summary_tab_layout()
    return html.Div([html.H3("Select a tab")])

# (create_network_figure function remains unchanged from Turn 83 content - it's the advanced one)
def create_network_figure(graph, graph_title="Network Visualization", node_color_input='#ADD8E6', layout_seed=42, fixed_positions=None, edge_hover_texts_custom=None, render_nodes_list=None):
    if render_nodes_list is None and (not graph or not graph.nodes()):
        fig = go.Figure()
        fig.update_layout(title_text=f"{graph_title} - No data to display", annotations=[dict(text="No data to display or network is empty.", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)], xaxis={'visible': False}, yaxis={'visible': False}, plot_bgcolor='white')
        return fig
    if render_nodes_list is not None and not render_nodes_list:
        fig = go.Figure()
        fig.update_layout(title_text=f"{graph_title} - No nodes to render", annotations=[dict(text="No nodes specified for rendering.", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)], xaxis={'visible': False}, yaxis={'visible': False}, plot_bgcolor='white')
        return fig
    nodes_to_iterate = render_nodes_list if render_nodes_list is not None else list(graph.nodes())
    if fixed_positions: pos = fixed_positions
    else:
        if graph and graph.nodes(): pos = nx.spring_layout(graph, seed=layout_seed, k=0.9, iterations=50)
        elif nodes_to_iterate:
            temp_layout_graph = nx.Graph(); temp_layout_graph.add_nodes_from(nodes_to_iterate)
            pos = nx.spring_layout(temp_layout_graph, seed=layout_seed, k=0.9, iterations=50)
        else: pos = {}
    edge_x_coords, edge_y_coords, edge_hover_texts_final = [], [], []
    if graph:
        for i, edge in enumerate(graph.edges(data=True)):
            if edge[0] not in pos or edge[1] not in pos: continue
            x0, y0 = pos[edge[0]]; x1, y1 = pos[edge[1]]
            edge_x_coords.extend([x0, x1, None]); edge_y_coords.extend([y0, y1, None])
            if edge_hover_texts_custom and i * 3 + 1 < len(edge_hover_texts_custom):
                edge_hover_texts_final.extend([edge_hover_texts_custom[i*3], edge_hover_texts_custom[i*3+1], None])
            else: edge_hover_texts_final.extend([f"Edge: {edge[0]} - {edge[1]}", f"Edge: {edge[0]} - {edge[1]}", None])
    edge_trace = go.Scatter(x=edge_x_coords, y=edge_y_coords, line=dict(width=0.7, color='#888'), hoverinfo='text', hovertext=edge_hover_texts_final, mode='lines')
    node_x_coords, node_y_coords, node_text_labels, node_hover_information, node_marker_sizes, node_marker_colors = [], [], [], [], [], []
    for i, node in enumerate(nodes_to_iterate):
        current_x, current_y = pos.get(node, (None, None))
        if current_x is None: continue
        node_x_coords.append(current_x); node_y_coords.append(current_y); node_text_labels.append(str(node))
        if isinstance(node_color_input, list): node_marker_colors.append(node_color_input[i] if i < len(node_color_input) else 'grey')
        else: node_marker_colors.append(node_color_input)
        is_active = graph and node in graph.nodes()
        if is_active:
            adjacencies = graph.adj.get(node, {}); num_connections = len(adjacencies)
            node_hover_information.append(f"Table: {node}<br># Connections: {num_connections}"); node_marker_sizes.append(num_connections * 5 + 10)
        else:
            node_hover_information.append(f"Table: {node}<br>(Contextual node; not in current dataset's connections)"); node_marker_sizes.append(7)
    node_trace = go.Scatter(x=node_x_coords, y=node_y_coords, mode='markers+text', text=node_text_labels, textposition="top center", hoverinfo='text', hovertext=node_hover_information, marker=dict(showscale=False, size=node_marker_sizes, sizemode='diameter', color=node_marker_colors, line_width=2))
    fig_layout = go.Layout(title={'text': graph_title, 'font': {'size': 16}}, showlegend=False, hovermode='closest', margin=dict(b=20,l=5,r=5,t=40), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), plot_bgcolor='white')
    return go.Figure(data=[edge_trace, node_trace], layout=fig_layout)

# (update_schema_analysis_tab and update_kpi_analysis_tab remain unchanged from Turn 83, they already use node_color_input and render_nodes_list=None)
@app.callback(
    [Output('schema-network-graph', 'figure'), Output('schema-centrality-table', 'children'), Output('schema-error-message', 'children')],
    [Input('upload-schema-data', 'contents')],
    [State('upload-schema-data', 'filename')]
)
def update_schema_analysis_tab(contents, filename):
    fig = go.Figure(); centrality_div = html.Div(); error_message = None
    if contents is None: raise PreventUpdate
    content_type, content_string = contents.split(','); decoded = base64.b64decode(content_string)
    try:
        json_data_str = decoded.decode('utf-8'); parsed_data = dp.parse_schema_json(json_data_str)
        if not parsed_data: raise ValueError("Schema data is empty or could not be parsed.")
        graph = nb.build_schema_network(parsed_data); schema_edge_hover_texts = []
        if graph.nodes():
            for edge in graph.edges(data=True):
                hover_text = f"Edge: {edge[0]} - {edge[1]}<br>"
                if 'shared_field' in edge[2]: hover_text += f"Shared Field: {edge[2]['shared_field']}<br>"
                if 'domain' in edge[2]: hover_text += f"Domain: {edge[2]['domain']}"
                schema_edge_hover_texts.extend([hover_text, hover_text, None])
        fig = create_network_figure(graph, "Schema Network Visualization", node_color_input='#ADD8E6', layout_seed=42, edge_hover_texts_custom=schema_edge_hover_texts, render_nodes_list=None)
        if not graph.nodes(): centrality_div = html.P("Schema network is empty, no centrality measures to display.")
        else:
            analysis_results = na.analyze_network(graph)
            if analysis_results:
                tables_data = []; metric_keys = [k for k in ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality'] if k in analysis_results and analysis_results[k]]
                headers = ["Table Name"] + [key.replace('_', ' ').title() for key in metric_keys]; all_nodes = set()
                for metric_name in metric_keys:
                    metric_data = analysis_results.get(metric_name, {});_ = [all_nodes.update(metric_data.keys()) if isinstance(metric_data, dict) else None]
                sorted_nodes = sorted(list(all_nodes))
                for node in sorted_nodes:
                    row = {'Table Name': node}
                    for metric_name in metric_keys:
                        values_dict = analysis_results.get(metric_name, {}); col_name = metric_name.replace('_', ' ').title(); value = values_dict.get(node, 'N/A')
                        row[col_name] = f"{value:.4f}" if isinstance(value, float) else str(value)
                    tables_data.append(row)
                centrality_table = dash_table.DataTable(id='schema-centrality-metrics-table', columns=[{"name": i, "id": i} for i in headers], data=tables_data, page_size=10, style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}, style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial', 'fontSize': '12px'}, style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}], sort_action="native")
                centrality_div = html.Div([centrality_table])
            else: centrality_div = html.P("Centrality analysis did not return any results for the schema network.")
    except Exception as e:
        error_message = html.Div(f"Error processing Schema file ({filename}): {str(e)}"); fig = go.Figure().update_layout(title_text="Error in Schema data processing"); centrality_div = html.P("Cannot calculate centrality due to schema data error.")
    return fig, centrality_div, error_message

@app.callback(
    [Output('kpi-network-graph', 'figure'), Output('kpi-centrality-table', 'children'), Output('kpi-error-message', 'children')],
    [Input('upload-kpi-data', 'contents')],
    [State('upload-kpi-data', 'filename')]
)
def update_kpi_analysis_tab(contents, filename):
    fig = go.Figure(); centrality_div = html.Div(); error_message = None
    if contents is None: raise PreventUpdate
    content_type, content_string = contents.split(','); decoded = base64.b64decode(content_string)
    try:
        json_data_str = decoded.decode('utf-8'); parsed_data = dp.parse_kpi_json(json_data_str)
        if not parsed_data: raise ValueError("KPI data is empty or could not be parsed.")
        graph = nb.build_kpi_network(parsed_data); kpi_edge_hover_texts = []
        if graph.nodes():
            for edge in graph.edges(data=True):
                kpi_links = edge[2].get('kpi_links', []); hover_text = f"Edge: {edge[0]} - {edge[1]}<br>KPIs: {', '.join(kpi_links)}"
                kpi_edge_hover_texts.extend([hover_text, hover_text, None])
        fig = create_network_figure(graph, "KPI Network Visualization", node_color_input='#FFB6C1', layout_seed=42, edge_hover_texts_custom=kpi_edge_hover_texts, render_nodes_list=None)
        if not graph.nodes(): centrality_div = html.P("KPI network is empty, no centrality measures to display.")
        else:
            analysis_results = na.analyze_network(graph)
            if analysis_results:
                tables_data = []; metric_keys = [k for k in ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality'] if k in analysis_results and analysis_results[k]]
                headers = ["Table Name"] + [key.replace('_', ' ').title() for key in metric_keys]; all_nodes = set()
                for metric_name in metric_keys:
                    metric_data = analysis_results.get(metric_name, {}); _ = [all_nodes.update(metric_data.keys()) if isinstance(metric_data, dict) else None]
                sorted_nodes = sorted(list(all_nodes))
                for node in sorted_nodes:
                    row = {'Table Name': node}
                    for metric_name in metric_keys:
                        values_dict = analysis_results.get(metric_name, {}); col_name = metric_name.replace('_', ' ').title(); value = values_dict.get(node, 'N/A')
                        row[col_name] = f"{value:.4f}" if isinstance(value, float) else str(value)
                    tables_data.append(row)
                centrality_table = dash_table.DataTable(id='kpi-centrality-metrics-table', columns=[{"name": i, "id": i} for i in headers], data=tables_data, page_size=10, style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}, style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial', 'fontSize': '12px'}, style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}], sort_action="native")
                centrality_div = html.Div([centrality_table])
            else: centrality_div = html.P("Centrality analysis did not return any results for KPI network.")
    except Exception as e:
        error_message = html.Div(f"Error processing KPI file ({filename}): {str(e)}"); fig = go.Figure().update_layout(title_text="Error in KPI data processing"); centrality_div = html.P("Cannot calculate centrality due to KPI data error.")
    return fig, centrality_div, error_message

# Callback for Comparison Tab
@app.callback(
    [Output('comparison-summary-stats', 'children'),
     Output('comparison-schema-graph', 'figure'),
     Output('comparison-kpi-graph', 'figure'),
     Output('comparison-combined-graph', 'figure'), # Added new output
     Output('comparison-error-message', 'children')],
    [Input('upload-schema-data', 'contents'),
     Input('upload-kpi-data', 'contents')],
    [State('upload-schema-data', 'filename'),
     State('upload-kpi-data', 'filename')]
)
def update_comparison_tab(schema_contents, kpi_contents, schema_filename, kpi_filename):
    summary_div_children = [html.P("Please upload both Schema and KPI JSON files to see the comparison.", style={'textAlign': 'center'})]
    error_message_list = []
    schema_graph, kpi_graph, combined_layout_graph = None, None, None # combined_layout_graph added
    schema_edge_hover_texts, kpi_edge_hover_texts = None, None

    # Initialize figures for all graphs
    schema_fig = create_network_figure(None, "Schema Network (Comparison View)", render_nodes_list=[])
    kpi_fig = create_network_figure(None, "KPI Network (Comparison View)", render_nodes_list=[])
    combined_fig = create_network_figure(None, "Combined Network View (All Nodes & Edges)", render_nodes_list=[])


    if not schema_contents and not kpi_contents:
        return summary_div_children, schema_fig, kpi_fig, combined_fig, None

    # Process Schema Data
    if schema_contents:
        try:
            s_content_type, s_content_string = schema_contents.split(',')
            s_decoded = base64.b64decode(s_content_string)
            s_json_data_str = s_decoded.decode('utf-8')
            parsed_schema = dp.parse_schema_json(s_json_data_str)
            if not parsed_schema: raise ValueError("Schema data could not be parsed or is empty.")
            schema_graph = nb.build_schema_network(parsed_schema)
            if schema_graph and schema_graph.nodes():
                schema_edge_hover_texts = []
                for edge in schema_graph.edges(data=True):
                    hover_text = f"Edge: {edge[0]} - {edge[1]}<br>"
                    if 'shared_field' in edge[2]: hover_text += f"Shared Field: {edge[2]['shared_field']}<br>"
                    if 'domain' in edge[2]: hover_text += f"Domain: {edge[2]['domain']}"
                    schema_edge_hover_texts.extend([hover_text, hover_text, None])
        except Exception as e:
            error_message_list.append(html.P(f"Error processing Schema file ({schema_filename}): {str(e)}")); schema_graph = None

    # Process KPI Data
    if kpi_contents:
        try:
            k_content_type, k_content_string = kpi_contents.split(',')
            k_decoded = base64.b64decode(k_content_string)
            k_json_data_str = k_decoded.decode('utf-8')
            parsed_kpis = dp.parse_kpi_json(k_json_data_str)
            if not parsed_kpis: raise ValueError("KPI data could not be parsed or is empty.")
            kpi_graph = nb.build_kpi_network(parsed_kpis)
            if kpi_graph and kpi_graph.nodes():
                kpi_edge_hover_texts = []
                for edge in kpi_graph.edges(data=True):
                    kpi_links = edge[2].get('kpi_links', [])
                    hover_text = f"Edge: {edge[0]} - {edge[1]}<br>KPIs: {', '.join(kpi_links)}"
                    kpi_edge_hover_texts.extend([hover_text, hover_text, None])
        except Exception as e:
            error_message_list.append(html.P(f"Error processing KPI file ({kpi_filename}): {str(e)}")); kpi_graph = None

    schema_nodes_set = set(schema_graph.nodes()) if schema_graph else set()
    kpi_nodes_set = set(kpi_graph.nodes()) if kpi_graph else set()
    all_nodes_list = sorted(list(schema_nodes_set | kpi_nodes_set))

    common_nodes_set = schema_nodes_set & kpi_nodes_set
    schema_only_nodes_set = schema_nodes_set - kpi_nodes_set
    kpi_only_nodes_set = kpi_nodes_set - schema_nodes_set

    common_node_positions = None
    ordered_node_colors = []

    if all_nodes_list:
        combined_layout_graph = nx.Graph()
        combined_layout_graph.add_nodes_from(all_nodes_list)
        if schema_graph:
            valid_schema_edges = [(u,v) for u,v in schema_graph.edges() if u in all_nodes_list and v in all_nodes_list]
            combined_layout_graph.add_edges_from(valid_schema_edges)
        if kpi_graph:
            valid_kpi_edges = [(u,v) for u,v in kpi_graph.edges() if u in all_nodes_list and v in all_nodes_list]
            combined_layout_graph.add_edges_from(valid_kpi_edges)
        common_node_positions = nx.spring_layout(combined_layout_graph, seed=42, k=0.9, iterations=50)

        for node in all_nodes_list:
            if node in common_nodes_set: ordered_node_colors.append('purple') # Common nodes
            elif node in schema_only_nodes_set: ordered_node_colors.append('#ADD8E6') # Schema-only (blue)
            elif node in kpi_only_nodes_set: ordered_node_colors.append('#FFB6C1') # KPI-only (pink)
            else: ordered_node_colors.append('grey') # Should not happen

    schema_fig = create_network_figure(graph=schema_graph, graph_title="Schema Network (Comparison View)", node_color_input='#ADD8E6', fixed_positions=common_node_positions, edge_hover_texts_custom=schema_edge_hover_texts, render_nodes_list=all_nodes_list)
    kpi_fig = create_network_figure(graph=kpi_graph, graph_title="KPI Network (Comparison View)", node_color_input='#FFB6C1', fixed_positions=common_node_positions, edge_hover_texts_custom=kpi_edge_hover_texts, render_nodes_list=all_nodes_list)

    if combined_layout_graph and combined_layout_graph.nodes() and common_node_positions:
         combined_fig = create_network_figure(
             graph=combined_layout_graph,
             graph_title="Combined Network View (All Nodes & Edges)",
             node_color_input=ordered_node_colors,
             fixed_positions=common_node_positions,
             edge_hover_texts_custom=None,
             render_nodes_list=all_nodes_list
         )
    else:
        combined_fig = create_network_figure(None, "Combined Network View (All Nodes & Edges)", render_nodes_list=[])

    if not error_message_list and (schema_graph is not None or kpi_graph is not None):
        summary_div_children = [html.P(f"Total Tables in Schema: {len(schema_nodes_set)}"), html.P(f"Total Tables in KPI: {len(kpi_nodes_set)}")]
        if schema_graph is not None and kpi_graph is not None:
            summary_div_children.extend([
                html.H5("Common Tables:"), html.Ul([html.Li(node) for node in sorted(list(common_nodes_set))]) if common_nodes_set else html.P("None"),
                html.H5("Tables Only in Schema:"), html.Ul([html.Li(node) for node in sorted(list(schema_only_nodes_set))]) if schema_only_nodes_set else html.P("None"),
                html.H5("Tables Only in KPI:"), html.Ul([html.Li(node) for node in sorted(list(kpi_only_nodes_set))]) if kpi_only_nodes_set else html.P("None"),
            ])
        elif not schema_contents and not kpi_contents:
             summary_div_children = [html.P("Please upload both Schema and KPI JSON files to see the comparison.", style={'textAlign': 'center'})]
    elif error_message_list:
        summary_div_children = []
    final_error_message = html.Div(error_message_list) if error_message_list else None
    return summary_div_children, schema_fig, kpi_fig, combined_fig, final_error_message

# (update_narrative_summary_tab remains unchanged)
@app.callback(
    [Output('narrative-summary-content', 'children'), Output('narrative-summary-error-message', 'children')],
    [Input('upload-schema-data', 'contents'), Input('upload-kpi-data', 'contents')],
    [State('upload-schema-data', 'filename'), State('upload-kpi-data', 'filename')]
)
def update_narrative_summary_tab(schema_contents, kpi_contents, schema_filename, kpi_filename):
    narrative_text = ""; error_message_children = []
    if schema_contents is None and kpi_contents is None:
        narrative_text = "Please upload both Schema and KPI JSON files to generate the narrative summary."; return narrative_text, None
    schema_graph, kpi_graph = None, None; schema_analysis, kpi_analysis = None, None
    if schema_contents:
        try:
            s_content_type, s_content_string = schema_contents.split(','); s_decoded = base64.b64decode(s_content_string); s_json_data_str = s_decoded.decode('utf-8')
            parsed_schema = dp.parse_schema_json(s_json_data_str)
            if not parsed_schema: raise ValueError("Schema data is empty or could not be parsed.")
            schema_graph = nb.build_schema_network(parsed_schema)
            if schema_graph.number_of_nodes() > 0: schema_analysis = na.analyze_network(schema_graph)
            else: schema_analysis = {}
        except Exception as e: error_message_children.append(html.P(f"Error processing Schema file ({schema_filename}): {str(e)}")); schema_graph = None
    else: error_message_children.append(html.P("Schema JSON file not uploaded. Some parts of the narrative may be incomplete or unavailable."))
    if kpi_contents:
        try:
            k_content_type, k_content_string = kpi_contents.split(','); k_decoded = base64.b64decode(k_content_string); k_json_data_str = k_decoded.decode('utf-8')
            parsed_kpis = dp.parse_kpi_json(k_json_data_str)
            if not parsed_kpis: raise ValueError("KPI data is empty or could not be parsed.")
            kpi_graph = nb.build_kpi_network(parsed_kpis)
            if kpi_graph.number_of_nodes() > 0: kpi_analysis = na.analyze_network(kpi_graph)
            else: kpi_analysis = {}
        except Exception as e: error_message_children.append(html.P(f"Error processing KPI file ({kpi_filename}): {str(e)}")); kpi_graph = None
    else: error_message_children.append(html.P("KPI JSON file not uploaded. Some parts of the narrative may be incomplete or unavailable."))
    schema_text = ng.generate_schema_narrative(schema_graph, schema_analysis if schema_analysis else {})
    kpi_text = ng.generate_kpi_narrative(kpi_graph, kpi_analysis if kpi_analysis else {})
    comp_text = "Comparison insights require both schema and KPI data to be successfully processed.\n"
    if schema_graph is not None and kpi_graph is not None:
        schema_nodes = set(schema_graph.nodes()); kpi_nodes = set(kpi_graph.nodes())
        common_nodes = schema_nodes & kpi_nodes; schema_only_nodes = schema_nodes - kpi_nodes; kpi_only_nodes = kpi_nodes - schema_nodes
        comp_text = ng.generate_comparison_narrative(schema_graph, kpi_graph, common_nodes, schema_only_nodes, kpi_only_nodes)
    elif error_message_children and not (schema_graph is not None and kpi_graph is not None) :
        comp_text = "Comparison narrative cannot be generated due to errors or missing data for one or both inputs."
    narrative_text = f"# Data Narrative Summary\n\n## Schema Overview\n{schema_text}\n\n## KPI Overview\n{kpi_text}\n\n## Comparison Insights\n{comp_text}"
    if (schema_contents and schema_graph is None and not any(f"Schema file ({schema_filename})" in str(p.children) for p in error_message_children if hasattr(p, 'children'))) or \
       (kpi_contents and kpi_graph is None and not any(f"KPI file ({kpi_filename})" in str(p.children) for p in error_message_children if hasattr(p, 'children'))):
        pass
    final_error_message_div = html.Div(error_message_children) if error_message_children else None
    return narrative_text, final_error_message_div

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
