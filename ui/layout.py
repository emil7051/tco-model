"""
UI layout components for the TCO Model Streamlit application.

This module provides reusable layout components to create a consistent UI experience.
"""
import streamlit as st
from typing import List, Dict, Callable, Optional, Any, Union
import pandas as pd
import plotly.graph_objects as go


def create_page_container(title: str, description: Optional[str] = None,
                         icon: Optional[str] = None) -> None:
    """
    Create a standard page container with title and optional description.
    
    Args:
        title: The page title
        description: Optional description text
        icon: Optional emoji icon
    """
    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)
        
    if description:
        st.markdown(description)
    
    st.markdown("---")


def create_tabs(tab_names: List[str]) -> List:
    """
    Create a set of tabs with the given names.
    
    Args:
        tab_names: List of tab names
        
    Returns:
        List of tab objects that can be used with a with statement
    """
    return st.tabs(tab_names)


def create_columns(num_columns: int, widths: Optional[List[int]] = None) -> List:
    """
    Create a set of columns with optional custom widths.
    
    Args:
        num_columns: Number of columns to create
        widths: Optional list of relative widths (must sum to 1)
        
    Returns:
        List of column objects that can be used with a with statement
    """
    if widths:
        if len(widths) != num_columns:
            raise ValueError("Length of widths must match num_columns")
        if not (0.99 <= sum(widths) <= 1.01):  # Allow slight precision error
            raise ValueError("Widths must sum to approximately 1")
        return st.columns(widths)
    else:
        return st.columns(num_columns)


def create_metric_card(label: str, value: Union[float, str], 
                      delta: Optional[Union[float, str]] = None,
                      help_text: Optional[str] = None,
                      format_fn: Optional[Callable] = None) -> None:
    """
    Create a metric card to display a key value with optional delta.
    
    Args:
        label: Label for the metric
        value: Value to display
        delta: Optional delta value (positive or negative)
        help_text: Optional help text shown on hover
        format_fn: Optional function to format the value
    """
    formatted_value = format_fn(value) if format_fn else value
    
    metric_kwargs = {
        "label": label,
        "value": formatted_value
    }
    
    if delta is not None:
        metric_kwargs["delta"] = delta
        
    if help_text:
        metric_kwargs["help"] = help_text
        
    st.metric(**metric_kwargs)


def create_info_panel(title: str, content: str, is_expanded: bool = False) -> None:
    """
    Create an expandable information panel.
    
    Args:
        title: The panel title
        content: The panel content (markdown)
        is_expanded: Whether panel should be expanded by default
    """
    with st.expander(title, expanded=is_expanded):
        st.markdown(content)


def create_result_table(data: pd.DataFrame, 
                      title: Optional[str] = None,
                      caption: Optional[str] = None,
                      use_container_width: bool = True) -> None:
    """
    Create a styled table for displaying results.
    
    Args:
        data: DataFrame containing the data
        title: Optional title to display above the table
        caption: Optional caption to display below the table
        use_container_width: Whether to expand table to container width
    """
    if title:
        st.subheader(title)
        
    st.dataframe(data, use_container_width=use_container_width)
    
    if caption:
        st.caption(caption)


def create_result_chart(fig: go.Figure, 
                      title: Optional[str] = None,
                      caption: Optional[str] = None,
                      height: Optional[int] = None,
                      use_container_width: bool = True) -> None:
    """
    Create a standard chart container for displaying results.
    
    Args:
        fig: Plotly figure object
        title: Optional title to display above the chart
        caption: Optional caption to display below the chart
        height: Optional height for the chart
        use_container_width: Whether to expand chart to container width
    """
    if title:
        st.subheader(title)
    
    st.plotly_chart(fig, use_container_width=use_container_width, height=height)
    
    if caption:
        st.caption(caption)


def create_side_by_side_comparison(title_left: str, content_left: Any,
                                 title_right: str, content_right: Any,
                                 comparison_label: Optional[str] = None) -> None:
    """
    Create a side-by-side comparison layout.
    
    Args:
        title_left: Title for the left content
        content_left: Content to display on the left (can be a widget function)
        title_right: Title for the right content
        content_right: Content to display on the right (can be a widget function)
        comparison_label: Optional comparison text to show between columns
    """
    if comparison_label:
        st.subheader(comparison_label)
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(title_left)
        if callable(content_left):
            content_left()
        else:
            st.markdown(content_left)
            
    with col2:
        st.subheader(title_right)
        if callable(content_right):
            content_right()
        else:
            st.markdown(content_right)


def create_download_button(data: Any, file_name: str, label: str, 
                         mime: str = "text/csv",
                         help_text: Optional[str] = None) -> None:
    """
    Create a standard download button for export functionality.
    
    Args:
        data: Data to download
        file_name: Name of the download file
        label: Button label
        mime: MIME type of the data
        help_text: Optional help text for the button
    """
    download_kwargs = {
        "data": data,
        "file_name": file_name,
        "label": label,
        "mime": mime
    }
    
    if help_text:
        download_kwargs["help"] = help_text
        
    st.download_button(**download_kwargs)


def create_section_divider(title: Optional[str] = None) -> None:
    """
    Create a visual divider between sections with an optional title.
    
    Args:
        title: Optional section title
    """
    st.markdown("---")
    
    if title:
        st.subheader(title)
