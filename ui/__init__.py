"""
UI package for the TCO Model application.

This package provides a modular, widget-based approach to building the application UI.

Package Structure:
-----------------
/ui
  __init__.py         - Package initialization
  input_manager.py    - Facade for input widgets
  output_manager.py   - Facade for output widgets
  state.py            - Session state management
  /widgets            - UI widget components
    __init__.py
    base.py           - Base widget classes
    /input_widgets    - Input UI elements
      __init__.py
      sidebar.py      - Sidebar widget containers
      general.py      - General parameter widgets
      vehicle_inputs.py - Vehicle parameter widgets
      cost_inputs.py  - Cost parameter widgets
    /output_widgets   - Output UI elements
      __init__.py
      base.py         - Base output widget classes
      chart_widget.py - Chart visualization widgets
      table_widget.py - Table visualization widgets
      summary_widget.py - Summary metrics widgets
      sensitivity_widget.py - Sensitivity analysis widgets
  /layouts            - Layout managers
    __init__.py
    tab_layout.py     - Tab-based layouts
    side_by_side_layout.py - Side-by-side comparison layouts
    responsive_layout.py - Responsive layouts for different screen sizes
    
Key Components:
--------------
- BaseWidget: Abstract base class for all UI widgets
- SidebarWidget: Base class for sidebar sections
- OutputWidget: Base class for result display widgets
- Layout Managers: Classes for organizing widgets in different layouts
- Managers: Facades that simplify working with multiple widgets
"""

# Import the main facades for easier access
from ui.input_manager import create_input_sidebar
from ui.output_manager import create_output_dashboard

__all__ = [
    'create_input_sidebar',
    'create_output_dashboard'
]
