# Data Readiness Scorecard App

## Overview

The Data Readiness Scorecard App is a Python-based web application designed to help users analyze and understand their data landscape. It processes schema definitions and Key Performance Indicator (KPI) data requirements, visualizes them as networks, and provides a comparison to highlight relationships, dependencies, and potential data gaps.

**Purpose:**
*   Visualize the structure of your database schema.
*   Understand how tables are interconnected based on shared fields.
*   Analyze which tables are crucial for supporting your KPIs.
*   Compare your defined schema against actual KPI data needs to identify commonalities, schema-only tables, and KPI-only tables (potential gaps).
*   Assess overall data readiness and pinpoint key tables through network centrality measures.

**Technology Stack:**
*   Python
*   Plotly Dash (for the web interface)
*   NetworkX (for network graph creation and analysis)

## Setup and Installation

Follow these steps to set up and run the application locally:

1.  **Prerequisites:**
    *   Python 3.7 or newer.

2.  **Clone the Repository (Optional):**
    *   If you have cloned a Git repository containing this application, navigate into the repository's root directory. Otherwise, ensure all project files are in a single main directory.
    *   To clone the repository, use the command: `git clone https://github.com/your-username/your-repository-name.git` (replace with the actual URL).

3.  **Create a Virtual Environment:**
    *   It's highly recommended to use a virtual environment to manage dependencies.
    *   Open your terminal or command prompt in the project's root directory.
    *   Run: `python -m venv venv`

4.  **Activate the Virtual Environment:**
    *   On macOS and Linux: `source venv/bin/activate`
    *   On Windows: `venv\Scripts\activate`

5.  **Install Dependencies:**
    *   Ensure your virtual environment is active.
    *   Install the required Python packages: `pip install -r requirements.txt`

## Preparing Your Data

The application requires two JSON files as input: a Schema JSON and a KPI JSON.

### Schema JSON File

This file defines the structure of your data sources, including domains, tables, and fields.

**Required Format Overview:**
The file should be a JSON list, where each item represents a "domain." Each domain contains a list of "tables," and each table contains a list of "fields."

**Minimal Valid Example:**
```json
[
  {
    "domain_name": "Customer",
    "domain_description": "Information about customers and their activities",
    "department": "Sales & Marketing",
    "tables": [
      {
        "table_name": "Customers",
        "table_description": "Core customer profile data",
        "fields": [
          {"field_name": "customer_id", "field_description": "Unique identifier for a customer", "data_type": "INT", "constraints": "PRIMARY KEY"},
          {"field_name": "customer_name", "field_description": "Name of the customer", "data_type": "VARCHAR"},
          {"field_name": "email", "field_description": "Customer's email address", "data_type": "VARCHAR"}
        ]
      },
      {
        "table_name": "Orders",
        "table_description": "Details of customer orders",
        "fields": [
          {"field_name": "order_id", "field_description": "Unique identifier for an order", "data_type": "INT", "constraints": "PRIMARY KEY"},
          {"field_name": "customer_id", "field_description": "Foreign key referencing the Customers table", "data_type": "INT"},
          {"field_name": "order_date", "field_description": "Date when the order was placed", "data_type": "DATE"},
          {"field_name": "order_value", "field_description": "Total monetary value of the order", "data_type": "DECIMAL"}
        ]
      }
    ]
  },
  {
    "domain_name": "Marketing",
    "tables": [
      {
        "table_name": "Campaigns",
        "fields": [
          {"field_name": "campaign_id", "data_type": "INT"},
          {"field_name": "campaign_name", "data_type": "VARCHAR"}
        ]
      }
    ]
  }
]
```

### KPI JSON File

This file defines your Key Performance Indicators (KPIs) and specifies which data (tables and fields) they require.

**Required Format Overview:**
The file should be a JSON list, where each item represents a KPI. Each KPI must have a `kpi_name` and a `data_required` list. Each item in `data_required` specifies a table (and optionally, domain and field) needed for the KPI.

**Minimal Valid Example:**
```json
[
  {
    "kpi_name": "Average Order Value (AOV)",
    "department": "Sales",
    "report_name": "Monthly Sales Review",
    "cadence": "Monthly",
    "description": "Calculates the average monetary value of customer orders.",
    "data_required": [
      {"domain_name": "Customer", "table_name": "Orders", "field_name": "order_value"},
      {"domain_name": "Customer", "table_name": "Orders", "field_name": "order_id"}
    ]
  },
  {
    "kpi_name": "Customer Acquisition Cost (CAC)",
    "department": "Marketing",
    "description": "Cost to acquire a new customer.",
    "data_required": [
      {"domain_name": "Marketing", "table_name": "Campaigns", "field_name": "total_spend"},
      {"domain_name": "Customer", "table_name": "Customers", "field_name": "customer_id"},
      {"domain_name": "Customer", "table_name": "Orders", "field_name": "customer_id"}
    ]
  }
]
```

## Running the Application

1.  Ensure your virtual environment is activated and all dependencies are installed.
2.  Navigate to the project's root directory in your terminal.
3.  Run the application using the command: `python app/app.py`
4.  Open your web browser and go to `http://127.0.0.1:8050/` (or `http://0.0.0.0:8050/` if accessing from another device on your network).

## Using the Application

### File Uploads
On the main page, you will see two upload components:
*   **Select Schema JSON File:** Use this to upload your prepared Schema JSON file.
*   **Select KPI JSON File:** Use this to upload your prepared KPI JSON file.
You can click on these components to browse for your files or drag and drop the files onto them.

### Tabs Overview

Once files are uploaded, the application will populate the analysis tabs:

#### Schema Network Analysis Tab
*   **Purpose:** Visualizes the structure of your schema, highlighting relationships between tables based on shared fields.
*   **Network Graph:**
    *   Nodes (circles) represent tables from your schema.
    *   Edges (lines) connect tables that are in the same domain and share one or more common field names.
    *   **Hovering:**
        *   Hover over a node (table) to see its name and the number of direct connections (degree).
        *   Hover over an edge to see the shared field name and the domain it belongs to.
    *   Node size is proportional to its degree centrality (more connections = larger node).
*   **Centrality Measures:** This section displays a table with various network centrality scores for each table:
    *   **Degree Centrality:** Indicates how many direct connections a table has. Higher values mean the table shares fields with many other tables within its domain.
    *   **Betweenness Centrality:** Measures how often a table lies on the shortest path between other tables. A high score suggests the table acts as a bridge or connector.
    *   **Closeness Centrality:** Indicates how close a table is to all other tables in the network. Higher values mean it's more central and can quickly reach other tables.
    *   **Eigenvector Centrality:** Measures a table's influence within the network. A high score means a table is connected to other highly connected/influential tables.

#### KPI Network Analysis Tab
*   **Purpose:** Visualizes how tables are interconnected based on the data requirements of your KPIs.
*   **Network Graph:**
    *   Nodes (circles) represent tables required by your KPIs.
    *   Edges (lines) connect tables that are required together for the same KPI.
    *   **Hovering:**
        *   Hover over a node (table) to see its name and the number of direct connections.
        *   Hover over an edge to see the list of KPIs that link the two connected tables.
    *   Node size is proportional to its degree centrality.
*   **Centrality Measures:** Similar to the Schema tab, this table shows centrality scores for tables based on their role in the KPI data dependency network. This can help identify tables that are critical for multiple KPIs.

#### Network Comparison Tab
*   **Purpose:** Provides a direct comparison between your defined schema structure and your KPI data requirements.
*   **Side-by-side Graphs:** Displays the Schema Network and KPI Network visualizations next to each other for easy visual comparison.
*   **Summary Statistics:**
    *   **Total Tables (Schema/KPI):** The number of unique tables found in your schema file and KPI file, respectively.
    *   **Common Tables:** A list of tables that are present in both your schema definition and are required by at least one KPI. These are typically well-utilized tables.
    *   **Tables only in Schema:** A list of tables that are defined in your schema but are not explicitly required by any of the KPIs in your KPI file. These might be underutilized, legacy, or foundational tables not directly queried by these specific KPIs.
    *   **Tables only in KPI:** A list of tables that are required by your KPIs but are not found in your schema file. This is a critical section as it may indicate:
        *   Missing tables in your schema definition.
        *   Typos in table names in either file.
        *   KPIs relying on data sources not yet formally documented in the schema.

## Troubleshooting

*   **"Error processing file..." / "Error decoding JSON..."**:
    *   Ensure the uploaded file is a valid JSON. You can use an online JSON linter or validator to check its syntax.
    *   Verify that the JSON structure matches the examples provided in the "Preparing Your Data" section (e.g., correct field names like `domain_name`, `tables`, `fields` for schema; `kpi_name`, `data_required` for KPIs).
    *   Check for common JSON errors like missing commas, trailing commas, or incorrect bracket usage.
*   **"No data to display" / Empty Graphs or Tables**:
    *   Make sure your schema file actually defines tables and fields.
    *   Ensure your KPI file lists `data_required` for KPIs.
    *   If the graph is empty but you expect data, there might be no shared fields (for schema network) or no KPIs requiring multiple tables (for KPI network).
*   **Page Not Loading / "This site can’t be reached"**:
    *   Confirm that you have started the application by running `python app/app.py` in your terminal.
    *   Check the terminal output for any error messages that might have occurred during startup.
    *   Ensure no other application is using port `8050` on your machine.

## Project Structure
```
.
├── app/
│   ├── app.py            # Main Dash application script
│   ├── src/              # Backend logic modules
│   │   ├── __init__.py
│   │   ├── data_parser.py    # Parses and validates input JSON
│   │   ├── network_builder.py# Builds network graphs
│   │   └── network_analysis.py # Calculates network metrics
│   ├── assets/           # (Optional) For CSS, images if not using inline styles
│   └── components/       # (Optional) For custom Dash components
├── tests/                # Unit tests
│   ├── __init__.py
│   ├── test_app_basic.py
│   ├── test_data_parser.py   # (Example, if created)
│   ├── test_network_builder.py
│   └── test_network_analysis.py
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

This structure helps organize the application, with the main Dash app logic in `app/app.py`, core processing functions in `app/src/`, and tests in the `tests/` directory at the project root.
