# Streamlit UI Design Plan

This document outlines the user interface design for the Australian Heavy Vehicle TCO Modeller Streamlit application, providing visual mockups, component layouts, and interaction patterns.

## 1. Overview

The UI is designed to provide an intuitive, interactive experience that allows users to adjust TCO parameters and immediately see the impact on results. The interface follows a clean, professional aesthetic with a focus on data clarity and visual hierarchy.

### 1.1 Design Principles

1. **Clarity** - Present complex TCO data in an accessible, understandable format
2. **Interactivity** - Provide immediate feedback as users adjust parameters
3. **Progressive Disclosure** - Start with key parameters, allow expansion to more detailed options
4. **Visual Hierarchy** - Guide attention to the most important information
5. **Consistency** - Maintain consistent styling and interaction patterns throughout

### 1.2 Key User Journeys

1. **Quick Comparison** - Compare BET vs Diesel TCO with minimal parameter adjustments
2. **Detailed Analysis** - Perform in-depth TCO analysis with customized parameters
3. **Scenario Management** - Save, load, and compare different scenarios
4. **Result Export** - Export findings for use in reports or presentations

## 2. Page Layout

The application uses a standard Streamlit layout with sidebar for inputs and main area for results.

### 2.1 Layout Wireframe

```
┌───────────────────────────────────────────────────────────────────────┐
│ Australian Heavy Vehicle TCO Modeller                                  │
├───────────┬───────────────────────────────────────────────────────────┤
│           │                                                           │
│           │ ┌─────────────────────────────────────────────────────┐  │
│           │ │ Key Metrics (Summary Cards)                         │  │
│ Parameter │ └─────────────────────────────────────────────────────┘  │
│ Inputs    │                                                           │
│ (Sidebar) │ ┌─────────────────────────────────────────────────────┐  │
│           │ │ Visualization Area (Tabs)                           │  │
│           │ │                                                     │  │
│           │ │ ┌─────────┐┌─────────┐┌─────────┐┌─────────┐       │  │
│           │ │ │Cumulative││Cost     ││Sensitivi││Detailed │       │  │
│           │ │ │TCO       ││Breakdown││ty       ││Data     │       │  │
│           │ │ └─────────┘└─────────┘└─────────┘└─────────┘       │  │
│           │ │                                                     │  │
│           │ │ [Active Tab Content]                                │  │
│           │ │                                                     │  │
│           │ │                                                     │  │
│           │ │                                                     │  │
│           │ │                                                     │  │
│           │ │                                                     │  │
│           │ └─────────────────────────────────────────────────────┘  │
│           │                                                           │
└───────────┴───────────────────────────────────────────────────────────┘
```

### 2.2 Component Overview

1. **Header** - Application title and brief description
2. **Sidebar** - Parameter input controls organized in expandable sections
3. **Key Metrics Area** - Summary cards showing critical TCO metrics
4. **Visualization Tabs** - Tabbed interface for different visualizations
5. **Active Visualization** - Current visualization (charts, tables)
6. **Footer** - Export options, about information, and additional links

## 3. Input Controls

The sidebar contains all input parameters organized in logical groups using expandable sections.

### 3.1 Input Sections

1. **General Parameters**
   - Vehicle Type (Selectbox): "Rigid", "Articulated"
   - Analysis Years (Number inputs): Start Year, End Year
   - Scenario Name (Text input)

2. **Economic Parameters** (Expandable)
   - Discount Rate (Slider): 0-15%
   - Inflation Rate (Slider): 0-10%
   - Financing Method (Radio): "Cash", "Loan"
   - Loan Parameters (conditional on Financing Method)
     - Loan Term (Slider): 1-10 years
     - Interest Rate (Slider): 0-15%
     - Down Payment (Slider): 0-100%

3. **Operational Parameters** (Expandable)
   - Annual Kilometres (Number input): 10,000-200,000

4. **Electric Vehicle Parameters** (Expandable)
   - Vehicle Model (Text input)
   - Purchase Price (Number input): A$100,000-1,000,000
   - Battery Capacity (Number input): 50-1,000 kWh
   - Energy Consumption (Number input): 0.5-3.0 kWh/km
   - Maintenance Cost (Number input): A$0.01-0.50/km

5. **Diesel Vehicle Parameters** (Expandable)
   - Vehicle Model (Text input)
   - Purchase Price (Number input): A$50,000-500,000
   - Fuel Consumption (Number input): 10-100 L/100km
   - Maintenance Cost (Number input): A$0.05-0.50/km

6. **Energy Costs** (Expandable)
   - Electricity Price (2025 & 2040) (Number inputs)
   - Diesel Price (2025 & 2040) (Number inputs)

7. **Infrastructure Costs** (Expandable)
   - Charger Hardware Cost (Number input)
   - Installation Cost (Number input)
   - Charger Lifespan (Slider)

8. **Battery Replacement** (Expandable)
   - Enable Replacement (Checkbox)
   - Replacement Method (Radio, conditional)
   - Replacement Parameters (conditional)

9. **Residual Values** (Expandable)
   - Electric Residual Value % (Slider)
   - Diesel Residual Value % (Slider)

### 3.2 Input Control Mockup

```
┌─────────────────────────────┐
│ Input Parameters            │
│                             │
│ [ Scenario Name          ]  │
│                             │
│ Vehicle Type: [Articulated▼]│
│                             │
│ Start Year: [2025] [+][-]   │
│ End Year:   [2040] [+][-]   │
│                             │
│ ┌─────────────────────────┐ │
│ │ Economic Parameters    ▼│ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Operational Parameters ▼│ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Electric Vehicle       ▼│ │
│ │ Parameters              │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Diesel Vehicle         ▼│ │
│ │ Parameters              │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Energy Costs           ▼│ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Infrastructure Costs   ▼│ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Battery Replacement    ▼│ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Residual Values        ▼│ │
│ └─────────────────────────┘ │
│                             │
│ [  Save Scenario  ]         │
│                             │
│ [Load Saved Scenario ▼]     │
│                             │
└─────────────────────────────┘
```

### 3.3 Input Control Implementation Details

#### Default Values

Default values for each input will be loaded from configuration files based on the selected vehicle type. Configuration files will be stored in YAML format for easy editing.

#### Expandable Sections

Expandable sections will be implemented using `st.expander()`:

```python
with st.sidebar.expander("Economic Parameters", expanded=False):
    discount_rate = st.slider(
        "Discount Rate (%)", 
        min_value=0.0, 
        max_value=15.0, 
        value=7.0, 
        step=0.1,
        format="%.1f"
    ) / 100.0
    
    # Additional economic parameters...
```

#### Conditional Controls

Conditional controls will be implemented using logic based on previous inputs:

```python
financing_method = st.selectbox(
    "Financing Method",
    options=["Loan", "Cash"],
    index=0
).lower()

if financing_method == "loan":
    loan_term = st.slider(
        "Loan Term (years)", 
        min_value=1, 
        max_value=10, 
        value=5,
        step=1
    )
    
    # Additional loan parameters...
```

#### Help Text

Each input will include help text using the `help` parameter to provide context and guidance:

```python
electric_vehicle_energy_consumption = st.number_input(
    "Energy Consumption (kWh/km)",
    min_value=0.5,
    max_value=3.0,
    value=1.5,
    step=0.1,
    format="%.2f",
    help="Average energy consumption in kilowatt-hours per kilometre. Typically 0.9-1.0 for rigid trucks and 1.5-2.0 for articulated trucks."
)
```

## 4. Output Visualizations

The main area displays results through several visualizations organized in tabs.

### 4.1 Key Metrics Area

A row of summary metrics displayed prominently at the top:

```
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ 15-Year Electric  │  │ 15-Year Diesel    │  │ TCO Parity Point  │
│ TCO               │  │ TCO               │  │                   │
│                   │  │                   │  │                   │
│ $1,250,000        │  │ $1,400,000        │  │ Year 2031         │
│ 10.7% vs Diesel▼  │  │                   │  │                   │
└───────────────────┘  └───────────────────┘  └───────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Levelized Cost per Kilometre                                    │
│                                                                 │
│ Electric: $1.04/km | Diesel: $1.17/km | 11.1% savings▼         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Cumulative TCO Chart

A line chart showing cumulative discounted costs over time:

```
┌─────────────────────────────────────────────────────────────────┐
│ Cumulative TCO Comparison (2025-2040)                           │
│                                                                 │
│ $1,400k │                                          ●            │
│         │                                     ●────             │
│         │                                ●────                  │
│         │                           ●────                       │
│ $1,200k │                      ●────                            │
│         │                 ●────                                 │
│         │            ●────                                      │
│         │       ●────                                           │
│ $1,000k │  ●────                                     ●          │
│         │ ●                                     ●────           │
│         │                                 ●────                 │
│         │                            ●────                      │
│  $800k │                        ●────                           │
│         │                  ●────                                │
│         │              ●────                                    │
│         │          ●────                                        │
│  $600k │      ●────                                             │
│         │  ●────                                                │
│         │ ●                                                     │
│         │                                                       │
│  $400k │                                                        │
│         │                            ◆ Parity Point (2031)      │
│         │                                                       │
│         │                                                       │
│  $200k │                                                        │
│         │                                                       │
│         │                                                       │
│       $0 │───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───│
│           2025  '27  '29  '31  '33  '35  '37  '39                 │
│                                                                   │
│         ● Electric   ● Diesel   ◆ Parity Point                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Cost Breakdown Chart

A stacked bar chart showing cost breakdown by component:

```
┌─────────────────────────────────────────────────────────────────┐
│ 15-Year Cost Breakdown by Component                             │
│                                                                 │
│ $1,400k │                                                       │
│         │                      ┌──────────┐                     │
│         │                      │Residual  │                     │
│ $1,200k │                      │Value     │                     │
│         │                      ├──────────┤                     │
│         │                      │Registration                    │
│ $1,000k │                      ├──────────┤                     │
│         │                      │Insurance │                     │
│         │                      ├──────────┤                     │
│  $800k │                      │Battery   │                     │
│         │  ┌──────────┐        │Replacement                     │
│         │  │Residual  │        ├──────────┤                     │
│  $600k │  │Value     │        │Infrastructure                  │
│         │  ├──────────┤        ├──────────┤                     │
│         │  │Registration        │Maintenance                     │
│  $400k │  ├──────────┤        ├──────────┤                     │
│         │  │Insurance │        │          │                     │
│         │  ├──────────┤        │Energy    │                     │
│  $200k │  │          │        │          │                     │
│         │  │Fuel      │        ├──────────┤                     │
│         │  │          │        │Acquisition                     │
│       $0 │  ├──────────┤        │          │                     │
│         │  │Acquisition        └──────────┘                     │
│         │  └──────────┘                                         │
│         │     Diesel            Electric                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Sensitivity Analysis Chart

A tornado chart showing the impact of parameter variations on TCO difference:

```
┌─────────────────────────────────────────────────────────────────┐
│ Sensitivity Analysis: Impact on TCO Difference (Electric-Diesel)│
│                                                                 │
│                 │                    │                          │
│ Diesel Price    ┣━━━━━━━━━━━━━━━━━━━┫                          │
│                 │                    │                          │
│ Annual Mileage  ┣━━━━━━━━━━━━━━━━━━┫                           │
│                 │                    │                          │
│ Battery Cost    ┣━━━━━━━━━━━┫                                  │
│                 │                    │                          │
│ Electricity Price┣━━━━━━━━┫                                     │
│                 │                    │                          │
│ Discount Rate   ┣━━━━┫                                         │
│                 │                    │                          │
│              -$200k    -$100k     $0    +$100k    +$200k       │
│                                                                 │
│             ■ Low Case   ■ High Case                           │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 Detailed Data Tab

A table view showing yearly cost breakdown:

```
┌─────────────────────────────────────────────────────────────────┐
│ Detailed Annual Costs                                           │
│                                                                 │
│ [ Electric Vehicle ▼ ][ Diesel Vehicle  ]                       │
│                                                                 │
│ ┌──────┬────────────┬────────┬─────────┬────────┬────────────┐ │
│ │ Year │ Acquisition│ Energy │Mainten. │ Infra. │    Total   │ │
│ ├──────┼────────────┼────────┼─────────┼────────┼────────────┤ │
│ │ 2025 │  $80,000   │ $6,400 │ $3,200  │$10,000 │  $99,600   │ │
│ │ 2026 │  $80,000   │ $6,350 │ $3,200  │$10,000 │  $99,550   │ │
│ │ 2027 │  $80,000   │ $6,300 │ $3,200  │$10,000 │  $99,500   │ │
│ │ 2028 │  $80,000   │ $6,250 │ $3,200  │$10,000 │  $99,450   │ │
│ │ 2029 │  $80,000   │ $6,200 │ $3,200  │$10,000 │  $99,400   │ │
│ │ ...  │    ...     │  ...   │   ...   │  ...   │    ...     │ │
│ │ 2040 │    $0      │ $5,900 │ $3,200  │   $0   │  -$30,000  │ │
│ └──────┴────────────┴────────┴─────────┴────────┴────────────┘ │
│                                                                 │
│ [ Download CSV ]  [ Download Excel ]                            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.6 Visualization Implementation Details

Each visualization will be implemented using Plotly:

```python
def create_cumulative_tco_chart(results: Dict[str, Any]) -> go.Figure:
    """Create a cumulative TCO comparison chart."""
    electric_total = results['electric_total']
    diesel_total = results['diesel_total']
    
    # Calculate cumulative sums
    electric_cumulative = electric_total['total'].cumsum()
    diesel_cumulative = diesel_total['total'].cumsum()
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=electric_total.index,
        y=electric_cumulative,
        mode='lines',
        name='Electric',
        line=dict(color='#00CC96', width=3)
    ))
    
    # More implementation details...
    
    return fig
```

## 5. Interaction Patterns

### 5.1 Input-to-Output Flow

1. User adjusts parameters in the sidebar
2. Each adjustment automatically triggers recalculation
3. Results update in real-time
4. Charts and metrics reflect the new calculation

This flow is implemented using Streamlit's automatic re-run on input change:

```python
# app.py
def main():
    # Setup page
    st.set_page_config(page_title="Australian Heavy Vehicle TCO Modeller", layout="wide")
    
    # Create layout
    create_layout()
    
    # Collect inputs (this triggers recalculation when changed)
    scenario_params = create_input_sidebar()
    
    # Create scenario and calculate TCO
    scenario = Scenario(**scenario_params)
    calculator = TCOCalculator()
    results = calculator.calculate(scenario)
    
    # Display results
    display_results(results)

# This pattern ensures the app recalculates and updates when inputs change
```

### 5.2 Scenario Management

Users can save and load scenarios:

1. **Saving**: User adjusts parameters and clicks "Save Scenario"
2. **Loading**: User selects a previously saved scenario from dropdown

Implementation:

```python
# In create_input_sidebar()
if st.sidebar.button("Save Scenario"):
    scenario = Scenario(**params)
    scenario_dir = os.path.join("config", "scenarios")
    os.makedirs(scenario_dir, exist_ok=True)
    
    filepath = os.path.join(scenario_dir, f"{scenario_name}.yaml")
    scenario.to_file(filepath)
    st.sidebar.success(f"Scenario saved to {filepath}")

# Scenario loading
available_scenarios = get_available_scenarios()
if available_scenarios:
    selected_scenario = st.sidebar.selectbox(
        "Load Saved Scenario",
        options=[""] + available_scenarios,
        index=0
    )
    
    if selected_scenario:
        scenario_data = load_scenario(selected_scenario)
        # Update input controls with loaded data
        # This could use session state to persist between reruns
```

### 5.3 Result Export

Users can export results in different formats:

1. **CSV Export**: Tabular data for spreadsheet analysis
2. **Excel Export**: Formatted workbook with multiple sheets

Implementation:

```python
# In detailed data tab
csv_data = pd.concat(
    [electric_total, diesel_total], 
    keys=['Electric', 'Diesel'], 
    axis=1
).to_csv(index=True).encode('utf-8')

st.download_button(
    label="Download CSV",
    data=csv_data,
    file_name="tco_results.csv",
    mime="text/csv",
)

# Excel export would use a utility function
if st.button("Download Excel"):
    excel_buffer = export_results_to_excel(results)
    st.download_button(
        label="Download Excel",
        data=excel_buffer,
        file_name="tco_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
```

## 6. State Management

### 6.1 Session State Usage

Streamlit's session state will be used to persist state between reruns:

```python
# ui/state.py
def initialize_session_state():
    """Initialize session state with default values."""
    if 'vehicle_type' not in st.session_state:
        st.session_state.vehicle_type = "Rigid"
    
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = None
    
    if 'comparison_scenario' not in st.session_state:
        st.session_state.comparison_scenario = None
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = None
    
    # Additional state variables
```

### 6.2 State Updates

State will be updated in response to user actions:

```python
# When loading a scenario
def load_scenario_to_state(scenario_name):
    """Load a scenario and update session state."""
    scenario_data = load_scenario(scenario_name)
    st.session_state.current_scenario = scenario_data
    
    # Update input widget values
    for key, value in scenario_data.items():
        if key in st.session_state:
            st.session_state[key] = value
    
    # Force rerun to update UI
    st.rerun()
```

### 6.3 Caching

Performance optimization will use Streamlit's caching mechanisms:

```python
@st.cache_data
def calculate_tco(scenario_params):
    """Cache TCO calculation results."""
    scenario = Scenario(**scenario_params)
    calculator = TCOCalculator()
    return calculator.calculate(scenario)

@st.cache_resource
def load_default_config():
    """Cache configuration data loading."""
    return load_config()
```

## 7. Responsive Design Considerations

### 7.1 Mobile Compatibility

While the primary focus is on desktop/tablet usage, the UI will adapt to smaller screens:

```python
# app.py
def create_layout():
    """Create responsive layout based on screen size."""
    # Check if on mobile
    is_mobile = st.session_state.get('_is_mobile', False)
    
    # On mobile, stack components vertically
    if is_mobile:
        st.title("Australian Heavy Vehicle TCO Modeller")
        
        # Create expandable inputs section
        with st.expander("Input Parameters", expanded=False):
            scenario_params = create_input_controls()
        
        # Display results in main area
        display_results(results)
    else:
        # Desktop layout with sidebar
        st.title("Australian Heavy Vehicle TCO Modeller")
        scenario_params = create_input_sidebar()
        display_results(results)
```

### 7.2 Layout Adaptation

For complex visualizations, the layout will adapt:

```python
def create_metric_row(results):
    """Create responsive metric display."""
    # On larger screens, use columns
    if st.session_state.get('_screen_width', 1200) >= 768:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(...)
        
        with col2:
            st.metric(...)
        
        with col3:
            st.metric(...)
    else:
        # On smaller screens, stack vertically
        st.metric(...)
        st.metric(...)
        st.metric(...)
```

## 8. Styling and Visual Identity

### 8.1 Color Scheme

The application will use a consistent color scheme:

- **Primary Colors**:
  - Electric: `#00CC96` (Green)
  - Diesel: `#EF553B` (Red/Orange)

- **UI Colors**:
  - Headings: `#1E88E5` (Blue)
  - Accents: `#FFC107` (Amber)
  - Background: `#F8F9FA` (Light Gray)
  - Text: `#212529` (Dark Gray)

### 8.2 Typography

The application will use Streamlit's default fonts with consistent styling:

```python
# Custom header styling
st.markdown("""
<style>
h1 {
    color: #1E88E5;
    font-weight: 600;
}
h2 {
    color: #1E88E5;
    font-weight: 500;
}
.metric-label {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
```

### 8.3 Chart Styling

All charts will use a consistent visual style:

```python
# Consistent chart theming
def apply_chart_styling(fig):
    """Apply consistent styling to Plotly charts."""
    fig.update_layout(
        font=dict(family="Arial, sans-serif", size=12),
        plot_bgcolor='rgba(248, 249, 250, 1)',
        paper_bgcolor='rgba(248, 249, 250, 1)',
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        colorway=['#00CC96', '#EF553B', '#636EFA', '#FFA15A', '#AB63FA'],
        template='plotly_white'
    )
    return fig
```

## 9. Implementation Strategy

### 9.1 Component Development Sequence

1. **Core Layout** - Basic page structure and sidebar
2. **Input Controls** - Parameter collection mechanisms
3. **Basic Visualization** - Initial chart implementation
4. **Full Result Display** - Complete visualization set
5. **State Management** - Session state and caching
6. **Advanced Features** - Scenario management, export options

### 9.2 Testing Strategy

1. **Component Testing** - Test each UI component in isolation
2. **Integration Testing** - Test input-to-output flow
3. **User Testing** - Gather feedback on usability and clarity

### 9.3 Performance Optimization

1. **Selective Recalculation** - Use caching to avoid redundant calculations
2. **Lazy Loading** - Load components only when needed
3. **Efficient Data Handling** - Minimize data transformations

## 10. Future UI Enhancements

Future versions of the UI may include:

1. **Dashboard Mode** - A simplified view for quick insights
2. **Scenario Comparison** - Side-by-side comparison of multiple scenarios
3. **Interactive Sensitivity Analysis** - Direct parameter adjustment in sensitivity charts
4. **Fleet-Level Analysis** - Expanded interface for multi-vehicle analysis
5. **Map Integration** - Route visualization and geographic analysis
6. **Timeline View** - Visual fleet transition planning tool

## Conclusion

This UI design plan provides a comprehensive blueprint for implementing an effective, user-friendly interface for the Australian Heavy Vehicle TCO Modeller. By following this plan, the development process will be more efficient and the resulting application will provide a valuable tool for stakeholders evaluating heavy vehicle electrification options.
