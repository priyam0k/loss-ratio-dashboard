import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
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
    'incurred_loss': 'sum'
}).reset_index()

# Create a proper date for the start of each month for plotting
df_monthly['month_start_date'] = pd.to_datetime(df_monthly['year'].astype(str) + '-' + df_monthly['month'].astype(str) + '-01')

# Calculate the Loss Ratio - THE CORE METRIC
df_monthly['loss_ratio'] = (df_monthly['incurred_loss'] / df_monthly['earned_premium'])


# --- 2. Initialize the Dash App ---
app = dash.Dash(__name__)
server = app.server

# --- 3. Define the App Layout ---
# This is the user interface of your dashboard.

# Color Palette
colors = {
    'background': '#f0f2f5',
    'text': '#2c3e50',
    'primary': '#3498db',
    'accent': '#e67e22',
    'white': '#ffffff',
    'light-grey': '#cccccc'
}

# Plotly color sequence for charts
plotly_colors = ['#3498db', '#e67e22', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c', '#34495e']


app.layout = html.Div(style={'backgroundColor': colors['background'], 'fontFamily': 'Segoe UI, Arial, sans-serif', 'color': colors['text']}, children=[

    # Header
    html.Div(style={'backgroundColor': colors['primary'], 'padding': '20px 30px', 'color': colors['white']}, children=[
        html.H1(
            children='P&C Insurance Loss Ratio Dashboard',
            style={'textAlign': 'center', 'margin': '0', 'fontSize': '2.5em'}
        ),
        html.P(
            children='An interactive tool to visualize loss ratio trends by business line and region.',
            style={'textAlign': 'center', 'margin': '10px 0 0', 'fontSize': '1.2em', 'opacity': '0.9'}
        ),
    ]),

    # Main Content
    html.Div(style={'padding': '30px'}, children=[
        # Filters Panel
        html.Div(style={'backgroundColor': colors['white'], 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'marginBottom': '30px', 'display': 'flex', 'flexWrap': 'wrap', 'gap': '25px', 'alignItems': 'center'}, children=[

            # Business Line Filter
            html.Div(style={'flex': '1 1 250px'}, children=[
                html.Label('Business Line', style={'fontWeight': '600', 'color': colors['text']}),
                dcc.Dropdown(
                    id='business-line-filter',
                    options=[{'label': line, 'value': line} for line in sorted(df_monthly['line_name'].unique())],
                    value=list(df_monthly['line_name'].unique()), # Default to all lines
                    multi=True,
                    style={'marginTop': '8px'}
                ),
            ]),

            # Region Filter
            html.Div(style={'flex': '1 1 250px'}, children=[
                html.Label('Region', style={'fontWeight': '600', 'color': colors['text']}),
                dcc.Dropdown(
                    id='region-filter',
                    options=[{'label': region, 'value': region} for region in sorted(df_monthly['region_name'].unique())],
                    value=list(df_monthly['region_name'].unique()), # Default to all regions
                    multi=True,
                    style={'marginTop': '8px'}
                ),
            ]),

            # Date Range Filter
            html.Div(style={'flex': '2 1 400px'}, children=[
                html.Label('Date Range', style={'fontWeight': '600', 'color': colors['text']}),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    min_date_allowed=df_monthly['month_start_date'].min(),
                    max_date_allowed=df_monthly['month_start_date'].max(),
                    start_date=df_monthly['month_start_date'].min(),
                    end_date=df_monthly['month_start_date'].max(),
                    style={'width': '100%', 'marginTop': '8px'}
                ),
            ]),
        ]),

        # Visualizations Container
        html.Div(className='graphs-container', style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '30px'}, children=[

            # Left side: Time Series Chart
            html.Div(style={'flex': '2 1 600px', 'backgroundColor': colors['white'], 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='loss-ratio-time-series')
            ]),

            # Right side: Comparative Bar Chart
            html.Div(style={'flex': '1 1 300px', 'backgroundColor': colors['white'], 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='loss-ratio-comparison-bar')
            ]),
        ]),
    ]),
])
# --- 4. Define Callbacks for Interactivity ---
# This is the "brain" of the dashboard. It connects the filters to the graphs.
@app.callback(
    [Output('loss-ratio-time-series', 'figure'),
     Output('loss-ratio-comparison-bar', 'figure')],
    [Input('business-line-filter', 'value'),
     Input('region-filter', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_graphs(selected_lines, selected_regions, start_date, end_date):
    # Filter data based on user selections
    filtered_df = df_monthly[
        (df_monthly['line_name'].isin(selected_lines)) &
        (df_monthly['region_name'].isin(selected_regions)) &
        (df_monthly['month_start_date'] >= start_date) &
        (df_monthly['month_start_date'] <= end_date)
    ]

    # --- Create Time Series Chart ---
    time_series_fig = px.line(
        filtered_df,
        x='month_start_date',
        y='loss_ratio',
        color='line_name',
        title='<b>Monthly Loss Ratio Trend by Business Line</b>',
        labels={'month_start_date': 'Date', 'loss_ratio': 'Loss Ratio', 'line_name': 'Business Line'},
        markers=True,
        color_discrete_sequence=plotly_colors
    )
    time_series_fig.update_layout(
        yaxis_tickformat='.0%', # Format y-axis as percentage
        legend_title_text='Business Lines',
        plot_bgcolor=colors['white'],
        paper_bgcolor=colors['white'],
        font_color=colors['text'],
        title_font_size=20,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    # Customize hover data for more context (Task 4.4)
    time_series_fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%B %Y}<br>Loss Ratio: %{y:.2%}<extra></extra>"
    )

    # --- Create Comparative Bar Chart ---
    # Calculate the average loss ratio for the selected period for comparison
    comparison_df = filtered_df.groupby('line_name').apply(
        lambda x: (x['incurred_loss'].sum() / x['earned_premium'].sum()) if x['earned_premium'].sum() != 0 else 0
    ).rename('average_loss_ratio').reset_index()
    comparison_df = comparison_df.sort_values('average_loss_ratio', ascending=False)
    
    bar_fig = px.bar(
        comparison_df,
        x='average_loss_ratio',
        y='line_name',
        orientation='h',
        color='line_name',
        title=f'<b>Avg. Loss Ratio ({pd.to_datetime(start_date).year} - {pd.to_datetime(end_date).year})</b>',
        labels={'line_name': 'Business Line', 'average_loss_ratio': 'Average Loss Ratio'},
        color_discrete_sequence=plotly_colors
    )
    bar_fig.update_layout(
        xaxis_tickformat='.0%',
        yaxis_title=None,
        showlegend=False,
        plot_bgcolor=colors['white'],
        paper_bgcolor=colors['white'],
        font_color=colors['text'],
        title_font_size=20
    )
    bar_fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Avg. Loss Ratio: %{x:.2%}<extra></extra>"
    )

    return time_series_fig, bar_fig


# --- 5. Run the App ---
if __name__ == '__main__':
    app.run(debug=True)

