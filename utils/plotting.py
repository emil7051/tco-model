import plotly.graph_objects as go
import pandas as pd
import plotly.express as px # Added for bar chart
from typing import List

# Application-specific imports (assuming types are defined in financial or a common types module)
# If not, define them here or import appropriately.
from utils.financial import AUD, Years # Import custom types

# Define color constants
ELECTRIC_BLUE = '#1f77b4'
DIESEL_ORANGE = '#ff7f0e'

def create_cumulative_tco_chart(electric_df: pd.DataFrame, diesel_df: pd.DataFrame, analysis_years: Years) -> go.Figure:
    """
    Creates a Plotly line chart showing the cumulative TCO for electric and diesel vehicles.

    Args:
        electric_df: DataFrame with annual undiscounted costs for the electric vehicle.
                       Expected to have columns for cost components and 'Total' (implicitly AUD).
                       Index should represent years (0-based).
        diesel_df: DataFrame with annual undiscounted costs for the diesel vehicle.
                     Expected to have columns for cost components and 'Total' (implicitly AUD).
                     Index should represent years (0-based).
        analysis_years: The number of years in the analysis.

    Returns:
        A Plotly Figure object.
    """
    fig = go.Figure()

    # Create a 1-based year list for the x-axis
    years: List[int] = list(range(1, analysis_years + 1))

    # Calculate cumulative sum on the 'Total' column
    # Ensure the column exists and handle potential errors if needed
    electric_cumulative: pd.Series = electric_df['Total'].cumsum()
    diesel_cumulative: pd.Series = diesel_df['Total'].cumsum()

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

def create_annual_cost_breakdown_chart(electric_df: pd.DataFrame, diesel_df: pd.DataFrame, analysis_years: Years) -> go.Figure:
    """
    Creates a Plotly stacked bar chart showing the annual cost breakdown for both vehicles.

    Args:
        electric_df: DataFrame with annual undiscounted costs (implicitly AUD) for the electric vehicle.
                       Expected columns: 'Year', cost components.
        diesel_df: DataFrame with annual undiscounted costs (implicitly AUD) for the diesel vehicle.
                     Expected columns: 'Year', cost components.
        analysis_years: The number of years in the analysis (unused in current plot logic but good context).

    Returns:
        A Plotly Figure object.
    """
    # Prepare data for stacked bar chart
    # Melt DataFrames to long format: Year, VehicleType, CostComponent, Value
    # Assuming 'Year' is a column, reset index if it's the index
    ev_df_reset = electric_df.reset_index().rename(columns={'index': 'Year_Index'})
    diesel_df_reset = diesel_df.reset_index().rename(columns={'index': 'Year_Index'})
    # Add 1 to Year_Index if it was 0-based
    ev_df_reset['Year'] = ev_df_reset['Year_Index'] + 1
    diesel_df_reset['Year'] = diesel_df_reset['Year_Index'] + 1

    ev_melted = ev_df_reset.drop(columns=['Total', 'Year_Index']).melt(
        id_vars=['Year'], var_name='CostComponent', value_name='Cost (AUD)'
    )
    ev_melted['VehicleType'] = 'Electric'

    diesel_melted = diesel_df_reset.drop(columns=['Total', 'Year_Index']).melt(
        id_vars=['Year'], var_name='CostComponent', value_name='Cost (AUD)'
    )
    diesel_melted['VehicleType'] = 'Diesel'

    combined_melted = pd.concat([ev_melted, diesel_melted])

    # Exclude zero or negative costs for clarity in stacked bar (esp. ResidualValue)
    # ResidualValue is often negative (a gain) and distorts stacked bars.
    plot_data = combined_melted[combined_melted['Cost (AUD)'] > 0].copy()

    # Define a consistent color map if needed, or let Plotly handle it
    # color_discrete_map = {...} # Optional

    fig = px.bar(
        plot_data,
        x='Year',
        y='Cost (AUD)',
        color='CostComponent',
        facet_col='VehicleType', # Separate columns for EV and Diesel
        # barmode='stack', # Default for px.bar with color
        title='Annual Cost Breakdown (Undiscounted Positive Costs)',
        labels={'Cost (AUD)': 'Annual Cost (AUD)', 'Year': 'Analysis Year'},
        hover_data={'Cost (AUD)': ':,.0f'} # Format hover data
    )

    fig.update_layout(
        yaxis_tickprefix='$',
        yaxis_tickformat=',.0f',
        legend_title='Cost Component'
    )
    # Ensure x-axis ticks cover all years in the range if needed
    # fig.update_xaxes(type='category', categoryorder='array', categoryarray=list(range(1, analysis_years + 1)))
    fig.update_xaxes(type='category') # Treat years as categories for distinct bars
    # Rename facet labels for clarity
    fig.for_each_annotation(lambda a: a.update(text=a.text.replace("VehicleType=", "")))

    return fig

def create_tco_comparison_bar_chart(electric_total: AUD, diesel_total: AUD) -> go.Figure:
    """
    Creates a simple bar chart comparing the total TCO of electric vs diesel.

    Args:
        electric_total: Total discounted TCO (AUD) for the electric vehicle.
        diesel_total: Total discounted TCO (AUD) for the diesel vehicle.

    Returns:
        A Plotly Figure object.
    """
    vehicles: List[str] = ['Electric', 'Diesel']
    totals: List[AUD] = [electric_total, diesel_total]
    # Convert AUD to float for plotting if Plotly requires primitive types
    totals_float: List[float] = [float(t) for t in totals]

    fig = go.Figure(data=[
        go.Bar(
            x=vehicles,
            y=totals_float,
            text=[f'${t:,.0f}' for t in totals_float], # Display total on bar
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
