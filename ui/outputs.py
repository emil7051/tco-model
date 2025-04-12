import streamlit as st
import pandas as pd
import logging
from io import BytesIO

# Import plotting functions
from utils.plotting import (
    create_cumulative_tco_chart,
    create_annual_cost_breakdown_chart,
    create_tco_comparison_bar_chart
)
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

@st.cache_data # Cache conversion to avoid recomputing on every interaction
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Converts a Pandas DataFrame to CSV bytes."""
    if df is None or df.empty:
        return b""
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def create_summary_df(results: dict) -> pd.DataFrame:
    """Creates a DataFrame summarizing the key TCO metrics."""
    summary_data = {
        "Metric": [
            "Total TCO (Discounted) - Electric",
            "Total TCO (Discounted) - Diesel",
            "LCOD (Electric)",
            "LCOD (Diesel)",
            "TCO Parity Year"
        ],
        "Value": [
            results.get('electric_total_tco'),
            results.get('diesel_total_tco'),
            results.get('electric_lcod'),
            results.get('diesel_lcod'),
            results.get('parity_year')
        ],
        "Unit": [
            "AUD",
            "AUD",
            "AUD/km",
            "AUD/km",
            "Year"
        ]
    }
    df = pd.DataFrame(summary_data)
    # Format currency and numbers for display in CSV
    df['Value'] = df.apply(lambda row: format_currency(row['Value']) if row['Unit'] == 'AUD' else (f"{row['Value']:.2f}" if row['Unit'] == 'AUD/km' else row['Value']), axis=1)
    return df

def format_currency(value):
    """Formats a number as currency (e.g., $1,234.56)."""
    if value is None or pd.isna(value):
        return "N/A"
    try:
        if isinstance(value, str):
            try:
                value = float(value.replace("$", "").replace(",", ""))
            except ValueError:
                return value
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        logger.debug(f"Could not format value '{value}' as currency.")
        return "N/A"

def _display_cost_table(df: pd.DataFrame | None, title: str, download_key: str, download_filename: str):
    """Helper function to display a cost DataFrame and its download button."""
    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
        st.markdown(f"**{title}**")
        # Apply formatting using st.dataframe's built-in capabilities if possible, 
        # or use style for more complex formatting.
        try:
            # Create a dictionary to format all numeric columns as currency
            formatters = {col: lambda x: format_currency(x) for col in df.select_dtypes(include='number').columns if col != 'Year'}
            # Format Year specifically if it exists
            if 'Year' in df.columns:
                formatters['Year'] = "{:.0f}".format
            
            st.dataframe(df.style.format(formatters, na_rep='-'), use_container_width=True)
        except Exception as e:
            logger.warning(f"Failed to apply style formatting to {title}: {e}. Falling back to default display.")
            st.dataframe(df, use_container_width=True) # Fallback
            
        csv_data = convert_df_to_csv(df)
        st.download_button(
            label=f"Download {title} (CSV)",
            data=csv_data,
            file_name=download_filename,
            mime="text/csv",
            key=download_key
        )
    else:
        st.warning(f"{title} data unavailable.")

def display_results(results: dict):
    """Displays the TCO calculation results, including metrics, charts, tables, and download options."""
    st.header("📊 Calculation Results")

    if not results:
        st.info("Run the calculation from the sidebar to see results.")
        return

    if results.get('error'):
        st.error(f"Calculation Failed: {results['error']}")
        if results.get('electric_annual_costs_undiscounted') is not None or results.get('diesel_annual_costs_undiscounted') is not None:
            st.warning("Displaying partial results where available.")
        else:
            return

    # Extract data
    electric_df_undisc = results.get('electric_annual_costs_undiscounted')
    diesel_df_undisc = results.get('diesel_annual_costs_undiscounted')
    electric_df_disc = results.get('electric_annual_costs_discounted')
    diesel_df_disc = results.get('diesel_annual_costs_discounted')
    total_tco_ev = results.get('electric_total_tco')
    total_tco_diesel = results.get('diesel_total_tco')
    lcod_ev = results.get('electric_lcod')
    lcod_diesel = results.get('diesel_lcod')
    parity_year = results.get('parity_year')
    analysis_years = results.get('analysis_years')

    # Check DataFrame validity
    ev_df_valid_undisc = electric_df_undisc is not None and isinstance(electric_df_undisc, pd.DataFrame) and not electric_df_undisc.empty
    diesel_df_valid_undisc = diesel_df_undisc is not None and isinstance(diesel_df_undisc, pd.DataFrame) and not diesel_df_undisc.empty
    ev_df_valid_disc = electric_df_disc is not None and isinstance(electric_df_disc, pd.DataFrame) and not electric_df_disc.empty
    diesel_df_valid_disc = diesel_df_disc is not None and isinstance(diesel_df_disc, pd.DataFrame) and not diesel_df_disc.empty

    # --- 1. Summary Metrics --- 
    st.subheader("📈 Summary Metrics")
    cols = st.columns([1.5, 1.5, 1])
    with cols[0]:
        st.metric(label="Total TCO (Electric - Discounted)", value=format_currency(total_tco_ev))
        st.metric(label="LCOD (Electric)", value=f"{lcod_ev:.2f} AUD/km" if lcod_ev is not None else "N/A", help="Levelized Cost of Driving (Total Discounted TCO / Total km)")
    with cols[1]:
        st.metric(label="Total TCO (Diesel - Discounted)", value=format_currency(total_tco_diesel))
        st.metric(label="LCOD (Diesel)", value=f"{lcod_diesel:.2f} AUD/km" if lcod_diesel is not None else "N/A", help="Levelized Cost of Driving (Total Discounted TCO / Total km)")
    with cols[2]:
        st.metric(label="TCO Parity Year", value=str(parity_year) if parity_year else "No Parity", help="First year where cumulative EV TCO ≤ Diesel TCO (based on undiscounted costs)")

    # --- Download Summary --- 
    summary_df = create_summary_df(results)
    summary_csv = convert_df_to_csv(summary_df)
    st.download_button(
        label="Download Summary Metrics (CSV)",
        data=summary_csv,
        file_name="tco_summary_metrics.csv",
        mime="text/csv",
        key="download-summary"
    )

    # --- 2. TCO Comparison Chart --- 
    st.subheader("📊 Total TCO Comparison")
    if total_tco_ev is not None and total_tco_diesel is not None:
        try:
            comparison_chart = create_tco_comparison_bar_chart(total_tco_ev, total_tco_diesel)
            st.plotly_chart(comparison_chart, use_container_width=True)
        except Exception as e:
            logger.error(f"Error generating TCO comparison chart: {e}", exc_info=True)
            st.error("Could not generate TCO comparison chart.")
    else:
        st.info("Total TCO comparison chart requires results for both vehicles.")

    # --- 3. Cumulative TCO Chart --- 
    st.subheader("📈 Cumulative TCO Over Time")
    if ev_df_valid_undisc and diesel_df_valid_undisc and analysis_years:
        try:
            cumulative_chart = create_cumulative_tco_chart(electric_df_undisc, diesel_df_undisc, analysis_years)
            st.plotly_chart(cumulative_chart, use_container_width=True)
        except Exception as e:
            logger.error(f"Error generating cumulative TCO chart: {e}", exc_info=True)
            st.error(f"Could not generate cumulative TCO chart: {e}")
    else:
        st.info("Cumulative TCO chart requires undiscounted annual results for both vehicles.")

    # --- 4. Annual Cost Breakdown Chart --- 
    st.subheader("📊 Annual Cost Breakdown")
    if ev_df_valid_undisc and diesel_df_valid_undisc and analysis_years:
        try:
            breakdown_chart = create_annual_cost_breakdown_chart(electric_df_undisc, diesel_df_undisc, analysis_years)
            st.plotly_chart(breakdown_chart, use_container_width=True)
            if 'ResidualValue' in electric_df_undisc.columns or 'ResidualValue' in diesel_df_undisc.columns:
                 if (electric_df_undisc['ResidualValue'] < 0).any() or (diesel_df_undisc['ResidualValue'] < 0).any():
                      st.caption("Note: Negative costs (e.g., Residual Value) are excluded from the breakdown chart for clarity.")
        except Exception as e:
            logger.error(f"Error generating annual breakdown chart: {e}", exc_info=True)
            st.error(f"Could not generate annual breakdown chart: {e}")
    else:
        st.info("Annual cost breakdown chart requires undiscounted annual results for both vehicles.")

    # --- 5. Detailed Annual Cost Tables & Downloads (Collapsible) --- 
    with st.expander("View/Download Detailed Annual Costs", expanded=False):
        tab1, tab2 = st.tabs(["Undiscounted Costs", "Discounted Costs"])

        with tab1:
            st.markdown("**Undiscounted Annual Costs**")
            col1, col2 = st.columns(2)
            with col1:
                _display_cost_table(
                    df=electric_df_undisc, 
                    title="Electric Vehicle", 
                    download_key="dl-ev-undisc", 
                    download_filename="ev_annual_undiscounted.csv"
                )
            with col2:
                _display_cost_table(
                    df=diesel_df_undisc, 
                    title="Diesel Vehicle", 
                    download_key="dl-diesel-undisc", 
                    download_filename="diesel_annual_undiscounted.csv"
                )

        with tab2:
            st.markdown("**Discounted Annual Costs** (Used for Total TCO calculation)")
            col3, col4 = st.columns(2)
            with col3:
                _display_cost_table(
                    df=electric_df_disc, 
                    title="Electric Vehicle", 
                    download_key="dl-ev-disc", 
                    download_filename="ev_annual_discounted.csv"
                )
            with col4:
                _display_cost_table(
                    df=diesel_df_disc, 
                    title="Diesel Vehicle", 
                    download_key="dl-diesel-disc", 
                    download_filename="diesel_annual_discounted.csv"
                )
