import plotly.graph_objects as go
import pandas as pd
import plotly.express as px # Added for bar chart

# Define color constants
ELECTRIC_BLUE = '#1f77b4'
DIESEL_ORANGE = '#ff7f0e'

def create_cumulative_tco_chart(electric_df: pd.DataFrame, diesel_df: pd.DataFrame, analysis_years: int) -> go.Figure:
    """
    Creates a Plotly line chart showing the cumulative TCO for electric and diesel vehicles.

    Args:
        electric_df: DataFrame with annual undiscounted costs for the electric vehicle.
                       Expected to have columns for cost components and 'Total'. Index is year (0-based).
        diesel_df: DataFrame with annual undiscounted costs for the diesel vehicle.
                     Expected to have columns for cost components and 'Total'. Index is year (0-based).
        analysis_years: The number of years in the analysis.

    Returns:
        A Plotly Figure object.
    """
    fig = go.Figure()

    # Use the Year column (1-based) for the x-axis
    years = list(range(1, analysis_years + 1))

    # Calculate cumulative sum on the 'Total' column
    electric_cumulative = electric_df['Total'].cumsum()
    diesel_cumulative = diesel_df['Total'].cumsum()

    # Add traces to the figure
    fig.add_trace(go.Scatter(
        x=years,
        y=electric_cumulative.values,
        mode='lines+markers',
        name='Electric Cumulative TCO',
        line=dict(color=ELECTRIC_BLUE), # Use constant
        hovertemplate='Year %{x}: Cum. TCO = $%{y:,.0f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=years,
        y=diesel_cumulative.values,
        mode='lines+markers',
        name='Diesel Cumulative TCO',
        line=dict(color=DIESEL_ORANGE), # Use constant
        hovertemplate='Year %{x}: Cum. TCO = $%{y:,.0f}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title='Cumulative Total Cost of Ownership (Undiscounted)',
        xaxis_title='Analysis Year',
        yaxis_title='Cumulative TCO (AUD)',
        yaxis_tickprefix='$',
        yaxis_tickformat=',.0f',
        legend_title='Vehicle Type',
        hovermode='x unified' # Shows hover info for both lines at the same x-value
    )

    return fig

def create_annual_cost_breakdown_chart(electric_df: pd.DataFrame, diesel_df: pd.DataFrame, analysis_years: int) -> go.Figure:
    """
    Creates a Plotly stacked bar chart showing the annual cost breakdown for both vehicles.

    Args:
        electric_df: DataFrame with annual undiscounted costs for the electric vehicle.
                       Expected columns: 'Year', cost components.
        diesel_df: DataFrame with annual undiscounted costs for the diesel vehicle.
                     Expected columns: 'Year', cost components.
        analysis_years: The number of years in the analysis.

    Returns:
        A Plotly Figure object.
    """
    # Prepare data for stacked bar chart
    # Melt DataFrames to long format: Year, VehicleType, CostComponent, Value
    ev_melted = electric_df.drop(columns=['Total']).melt(
        id_vars=['Year'], var_name='CostComponent', value_name='Cost (AUD)'
    )
    ev_melted['VehicleType'] = 'Electric'

    diesel_melted = diesel_df.drop(columns=['Total']).melt(
        id_vars=['Year'], var_name='CostComponent', value_name='Cost (AUD)'
    )
    diesel_melted['VehicleType'] = 'Diesel'

    combined_melted = pd.concat([ev_melted, diesel_melted])

    # Exclude zero or negative costs for clarity in stacked bar (esp. ResidualValue)
    # ResidualValue is better visualized separately or noted.
    plot_data = combined_melted[combined_melted['Cost (AUD)'] > 0]

    # Define a consistent color map if needed, or let Plotly handle it
    # color_discrete_map = {...} # Optional

    fig = px.bar(
        plot_data,
        x='Year',
        y='Cost (AUD)',
        color='CostComponent',
        facet_col='VehicleType', # Separate columns for EV and Diesel
        # barmode='stack', # Default for px.bar with color
        title='Annual Cost Breakdown (Undiscounted)',
        labels={'Cost (AUD)': 'Annual Cost (AUD)', 'Year': 'Analysis Year'},
        hover_data={'Cost (AUD)': ':,.0f'} # Format hover data
    )

    fig.update_layout(
        yaxis_tickprefix='$',
        yaxis_tickformat=',.0f',
        legend_title='Cost Component'
    )
    fig.update_xaxes(type='category') # Treat years as categories for distinct bars
    # Rename facet labels
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    return fig

def create_tco_comparison_bar_chart(electric_total: float, diesel_total: float) -> go.Figure:
    """
    Creates a simple bar chart comparing the total TCO of electric vs diesel.

    Args:
        electric_total: Total discounted TCO for the electric vehicle.
        diesel_total: Total discounted TCO for the diesel vehicle.

    Returns:
        A Plotly Figure object.
    """
    vehicles = ['Electric', 'Diesel']
    totals = [electric_total, diesel_total]

    fig = go.Figure(data=[
        go.Bar(
            x=vehicles,
            y=totals,
            text=[f'${t:,.0f}' for t in totals], # Display total on bar
            textposition='auto',
            marker_color=[ELECTRIC_BLUE, DIESEL_ORANGE] # Use constants
        )
    ])

    fig.update_layout(
        title='Total TCO Comparison (Discounted)',
        xaxis_title='Vehicle Type',
        yaxis_title='Total Cost of Ownership (AUD)',
        yaxis_tickprefix='$',
        yaxis_tickformat=',.0f'
    )

    return fig
