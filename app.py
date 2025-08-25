import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# --- 1. Load and Prepare Data ---
# This section corresponds to the ETL and data prep phase.
# In a real-world scenario, this might connect to a database.
try:
    fact_financials = pd.read_csv('fact_financials.csv')
    dim_date = pd.read_csv('dim_date.csv')
    dim_business_line = pd.read_csv('dim_business_line.csv')
    dim_region = pd.read_csv('dim_region.csv')
except FileNotFoundError:
    print("ERROR: Data files not found. Please run the `create_data.py` script first.")
    exit()

# Merge tables to create a single analysis-ready DataFrame
df = pd.merge(fact_financials, dim_date, on='date_key')
df = pd.merge(df, dim_business_line, on='business_line_key')
df = pd.merge(df, dim_region, on='region_key')

# Convert date column to datetime objects for proper time-series plotting
df['full_date'] = pd.to_datetime(df['full_date'])

# Aggregate data by month for a cleaner top-level view
df_monthly = df.groupby(['year', 'month', 'month_name', 'line_name', 'region_name']).agg({
    'earned_premium': 'sum',
    'incurred_loss': 'sum',
    'developed_loss': 'sum' # Aggregate the new developed loss column
}).reset_index()

# Create a proper date for the start of each month for plotting
df_monthly['month_start_date'] = pd.to_datetime(df_monthly['year'].astype(str) + '-' + df_monthly['month'].astype(str) + '-01')

# Calculate the two types of Loss Ratios
df_monthly['reported_loss_ratio'] = (df_monthly['incurred_loss'] / df_monthly['earned_premium'])
df_monthly['developed_loss_ratio'] = (df_monthly['developed_loss'] / df_monthly['earned_premium'])


# --- 2. Initialize the Dash App ---
app = dash.Dash(__name__)
server = app.server

# --- 3. Define the App Layout ---
# Color Palette and styling
colors = {
    'background': '#f0f2f5',
    'text': '#2c3e50',
    'primary': '#2980b9',
    'accent': '#c0392b',
    'white': '#ffffff',
    'light-grey': '#ecf0f1'
}
plotly_colors = ['#3498db', '#e67e22', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c', '#34495e']

app.layout = html.Div(style={'backgroundColor': colors['background'], 'fontFamily': 'Segoe UI, Arial, sans-serif', 'color': colors['text']}, children=[

    # Header
    html.Div(style={'backgroundColor': colors['primary'], 'padding': '20px 30px', 'color': colors['white']}, children=[
        html.H1(
            children='P&C Insurance Loss Ratio Dashboard',
            style={'textAlign': 'center', 'margin': '0', 'fontSize': '2.5em'}
        ),
        html.P(
            children='An interactive tool for analyzing actuarial loss trends.',
            style={'textAlign': 'center', 'margin': '10px 0 0', 'fontSize': '1.2em', 'opacity': '0.9'}
        ),
    ]),

    # Main Content
    html.Div(style={'padding': '30px'}, children=[
        
        # --- UPDATED: Explanatory Section ---
        html.Details([
            html.Summary('About this Dashboard & Actuarial Concepts', style={'fontSize': '1.2em', 'fontWeight': '600', 'cursor': 'pointer', 'marginBottom': '10px'}),
            dcc.Markdown('''
                ### Understanding the P&C Loss Ratio
                The **Loss Ratio** is a critical KPI in insurance, showing the proportion of premiums used to pay claims. This dashboard visualizes two key perspectives on this metric, reflecting concepts from actuarial science.

                - **"As Reported" Loss Ratio:** This is the initial estimate based on claims reported to the company. It's a useful early indicator but can be volatile and may not reflect the true final cost, as some claims take a long time to settle.
                - **"Developed Ultimate" Loss Ratio:** This is a refined estimate that projects the final, or "ultimate," cost of claims after they have had time to develop. Actuaries use methods like the **Chain-Ladder** technique to create these projections by analyzing historical payment patterns. This dashboard simulates this process to provide a more mature view of profitability.

                ### How to Use This Dashboard
                1.  **Use the Filters** to select business lines, regions, and a date range for your analysis.
                2.  **Toggle the Methodology** to switch between the 'As Reported' and 'Developed Ultimate' views. Observe how the loss ratios change; this difference is known as **loss development**.
                3.  **Analyze the Charts** to identify trends and compare performance across different business lines.
                4.  **Review the KPI Cards** for a high-level summary of the selected data. The "Development Impact" card shows the overall change from the reported to the developed loss ratio.
                5.  **Explore the Data Table** for a transparent, detailed view of the underlying numbers powering the visualizations.
            ''', style={'backgroundColor': colors['white'], 'padding': '20px', 'borderRadius': '8px', 'border': f"1px solid {colors['light-grey']}"})
        ], style={'marginBottom': '30px'}),

        # Filters Panel
        html.Div(style={'backgroundColor': colors['white'], 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'marginBottom': '30px', 'display': 'flex', 'flexWrap': 'wrap', 'gap': '25px', 'alignItems': 'center'}, children=[
            html.Div(style={'flex': '1 1 200px'}, children=[
                html.Label('Business Line', style={'fontWeight': '600'}),
                dcc.Dropdown(id='business-line-filter', options=[{'label': i, 'value': i} for i in sorted(df_monthly['line_name'].unique())], value=list(df_monthly['line_name'].unique()), multi=True, style={'marginTop': '8px'}),
            ]),
            html.Div(style={'flex': '1 1 200px'}, children=[
                html.Label('Region', style={'fontWeight': '600'}),
                dcc.Dropdown(id='region-filter', options=[{'label': i, 'value': i} for i in sorted(df_monthly['region_name'].unique())], value=list(df_monthly['region_name'].unique()), multi=True, style={'marginTop': '8px'}),
            ]),
            html.Div(style={'flex': '2 1 350px'}, children=[
                html.Label('Date Range', style={'fontWeight': '600'}),
                dcc.DatePickerRange(id='date-picker-range', min_date_allowed=df_monthly['month_start_date'].min(), max_date_allowed=df_monthly['month_start_date'].max(), start_date=df_monthly['month_start_date'].min(), end_date=df_monthly['month_start_date'].max(), style={'width': '100%', 'marginTop': '8px'}),
            ]),
            # --- NEW: Loss Ratio Type Toggle ---
            html.Div(style={'flex': '1 1 200px'}, children=[
                html.Label('Loss Ratio Methodology', style={'fontWeight': '600'}),
                dcc.RadioItems(
                    id='loss-ratio-type',
                    options=[
                        {'label': 'As Reported', 'value': 'reported_loss_ratio'},
                        {'label': 'Developed Ultimate', 'value': 'developed_loss_ratio'}
                    ],
                    value='reported_loss_ratio',
                    labelStyle={'display': 'block', 'marginTop': '5px'}
                ),
            ]),
        ]),
        
        # --- NEW: KPI Cards Section ---
        html.Div(id='kpi-cards', style={'display': 'flex', 'gap': '30px', 'marginBottom': '30px'}),

        # Visualizations Container
        html.Div(className='graphs-container', style={'marginBottom': '30px'}, children=[
            # Time Series Chart on its own row
            html.Div(style={'backgroundColor': colors['white'], 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'marginBottom': '30px'}, children=[
                dcc.Graph(id='loss-ratio-time-series')
            ]),
            # Comparative Bar Chart on its own row
            html.Div(style={'backgroundColor': colors['white'], 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='loss-ratio-comparison-bar')
            ]),
        ]),
        
        # Data Table Section
        html.Div(style={'backgroundColor': colors['white'], 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
            html.H3('Underlying Data Explorer', style={'marginBottom': '20px'}),
            dash_table.DataTable(
                id='data-table',
                columns=[],
                data=[],
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_header={'backgroundColor': colors['light-grey'], 'fontWeight': 'bold'},
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}]
            )
        ])
    ]),
])

# --- 4. Define Callbacks for Interactivity ---
@app.callback(
    [Output('loss-ratio-time-series', 'figure'),
     Output('loss-ratio-comparison-bar', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('kpi-cards', 'children')],
    [Input('business-line-filter', 'value'),
     Input('region-filter', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('loss-ratio-type', 'value')]
)
def update_dashboard(selected_lines, selected_regions, start_date, end_date, loss_ratio_type):
    # Filter data based on user selections
    filtered_df = df_monthly[
        (df_monthly['line_name'].isin(selected_lines)) &
        (df_monthly['region_name'].isin(selected_regions)) &
        (df_monthly['month_start_date'] >= start_date) &
        (df_monthly['month_start_date'] <= end_date)
    ].copy()

    # --- Create KPI Cards ---
    if not filtered_df.empty:
        overall_reported_lr = filtered_df['incurred_loss'].sum() / filtered_df['earned_premium'].sum()
        overall_developed_lr = filtered_df['developed_loss'].sum() / filtered_df['earned_premium'].sum()
        development_impact = overall_developed_lr - overall_reported_lr
    else:
        overall_reported_lr = overall_developed_lr = development_impact = 0

    kpi_cards = [
        html.Div(style={'flex': 1, 'backgroundColor': colors['white'], 'padding': '20px', 'borderRadius': '8px', 'textAlign': 'center', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
            html.H4('Overall Reported LR', style={'margin': 0, 'color': colors['primary']}),
            html.P(f"{overall_reported_lr:.2%}", style={'fontSize': '2em', 'margin': '10px 0 0'})
        ]),
        html.Div(style={'flex': 1, 'backgroundColor': colors['white'], 'padding': '20px', 'borderRadius': '8px', 'textAlign': 'center', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
            html.H4('Overall Developed LR', style={'margin': 0, 'color': colors['primary']}),
            html.P(f"{overall_developed_lr:.2%}", style={'fontSize': '2em', 'margin': '10px 0 0'})
        ]),
        html.Div(style={'flex': 1, 'backgroundColor': colors['white'], 'padding': '20px', 'borderRadius': '8px', 'textAlign': 'center', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
            html.H4('Development Impact', style={'margin': 0, 'color': development_impact >= 0 and colors['accent'] or '#2ecc71'}),
            html.P(f"{development_impact:+.2%}", style={'fontSize': '2em', 'margin': '10px 0 0'})
        ]),
    ]

    # --- Create Time Series Chart ---
    time_series_fig = px.line(filtered_df, x='month_start_date', y=loss_ratio_type, color='line_name', title='<b>Monthly Loss Ratio Trend by Business Line</b>', labels={'month_start_date': 'Date', loss_ratio_type: 'Loss Ratio', 'line_name': 'Business Line'}, markers=True, color_discrete_sequence=plotly_colors)
    time_series_fig.update_layout(yaxis_tickformat='.0%', legend_title_text='Business Lines', plot_bgcolor=colors['white'], paper_bgcolor=colors['white'], font_color=colors['text'], title_font_size=20, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    time_series_fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%B %Y}<br>Loss Ratio: %{y:.2%}<extra></extra>")

    # --- Create Comparative Bar Chart ---
    if loss_ratio_type == 'reported_loss_ratio':
        loss_col = 'incurred_loss'
    else:
        loss_col = 'developed_loss'
        
    comparison_df = filtered_df.groupby('line_name').apply(lambda x: (x[loss_col].sum() / x['earned_premium'].sum()) if x['earned_premium'].sum() != 0 else 0).rename('average_loss_ratio').reset_index().sort_values('average_loss_ratio', ascending=False)
    bar_fig = px.bar(comparison_df, x='average_loss_ratio', y='line_name', orientation='h', color='line_name', title=f'<b>Avg. Loss Ratio ({pd.to_datetime(start_date).year} - {pd.to_datetime(end_date).year})</b>', labels={'line_name': 'Business Line', 'average_loss_ratio': 'Average Loss Ratio'}, color_discrete_sequence=plotly_colors)
    bar_fig.update_layout(xaxis_tickformat='.0%', yaxis_title=None, showlegend=False, plot_bgcolor=colors['white'], paper_bgcolor=colors['white'], font_color=colors['text'], title_font_size=20)
    bar_fig.update_traces(hovertemplate="<b>%{y}</b><br>Avg. Loss Ratio: %{x:.2%}<extra></extra>")

    # --- Prepare Data for Table ---
    table_df = filtered_df[['month_start_date', 'line_name', 'region_name', 'earned_premium', 'incurred_loss', 'developed_loss', 'reported_loss_ratio', 'developed_loss_ratio']].copy()
    table_df['month_start_date'] = table_df['month_start_date'].dt.strftime('%Y-%m-%d')
    for col in ['earned_premium', 'incurred_loss', 'developed_loss']:
        table_df[col] = table_df[col].map('${:,.2f}'.format)
    for col in ['reported_loss_ratio', 'developed_loss_ratio']:
        table_df[col] = table_df[col].map('{:.2%}'.format)
    
    table_columns = [{"name": i.replace('_', ' ').title(), "id": i} for i in table_df.columns]
    table_data = table_df.to_dict('records')

    return time_series_fig, bar_fig, table_data, table_columns, kpi_cards

# --- 5. Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
