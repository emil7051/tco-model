# AI Collaboration Workflow

This document provides a structured approach to effectively collaborating with AI assistance in Cursor while developing the Australian Heavy Vehicle TCO Modeller. It outlines best practices, prompt strategies, and workflows to maximize productivity and code quality.

## 1. Understanding AI-Assisted Development

### 1.1 AI Assistance Capabilities

Modern AI coding assistants in tools like Cursor can:

1. **Generate Code** - Create new implementations based on requirements
2. **Explain Code** - Provide insights into existing code
3. **Debug Issues** - Help identify and fix problems
4. **Refactor Code** - Improve code structure and quality
5. **Document Code** - Generate documentation and comments
6. **Provide Guidance** - Offer architectural and design advice

### 1.2 Key Benefits of AI Collaboration

1. **Accelerated Development** - Reduce time spent on boilerplate code
2. **Knowledge Augmentation** - Access expertise in unfamiliar domains
3. **Quality Improvement** - Get alternative perspectives and approaches
4. **Learning Opportunity** - Understand new patterns and techniques
5. **Reduced Context Switching** - Get answers without leaving your editor

### 1.3 Limitations to Be Aware Of

1. **Contextual Understanding** - AI may miss project-specific context
2. **Domain Knowledge Gaps** - AI may have incomplete knowledge of specific domains
3. **Hallucinations** - AI may sometimes generate plausible but incorrect information
4. **Security Considerations** - Be cautious with sensitive code or data
5. **Overreliance Risk** - Maintain critical thinking and code review practices

## 2. Setting Up Your Environment

### 2.1 Cursor Configuration

Configure Cursor for optimal AI collaboration:

1. **Set Up Project Context**
   - Use the "Project Context" feature to add project documentation
   - Include architecture documents, requirements, and design specs
   - This helps the AI understand your project better

2. **Configure AI Models**
   - Select appropriate model based on your needs
   - Balance between speed and capability

3. **Enable Useful Features**
   - Enable auto-completion
   - Set up keyboard shortcuts for common AI interactions
   - Configure code formatting and linting

### 2.2 Project Organization for AI Collaboration

Structure your project to facilitate AI collaboration:

1. **Clear Directory Structure**
   - Follow the structure outlined in the Code Structure Plan
   - Keep related files together for better context

2. **Documentation Proximity**
   - Keep relevant documentation close to code
   - Use docstrings and comments for context

3. **Module Interfaces**
   - Define clear interfaces between components
   - Use type hints and descriptive naming

## 3. Effective Prompting Strategies

### 3.1 General Prompting Principles

1. **Be Specific and Detailed**
   - Provide clear requirements and constraints
   - Specify expected inputs, outputs, and behaviors
   - Mention relevant frameworks and libraries

2. **Provide Context**
   - Reference existing code and architecture
   - Explain the purpose and role of the requested code
   - Mention any specific patterns or conventions to follow

3. **Use Iterative Refinement**
   - Start with a high-level request
   - Gradually refine based on the results
   - Ask for specific improvements or alternatives

4. **Ask for Explanations**
   - Request explanations for complex logic
   - Ask about design decisions and trade-offs
   - Seek clarification when necessary

### 3.2 Example Prompts for Different Tasks

#### Code Generation

```
I need to implement the AcquisitionCost class for my TCO model.

Context:
- It inherits from the CostComponent abstract class
- It needs to implement the calculate_annual_cost method
- It should handle both cash purchases and loan financing
- For cash purchases, the full cost is applied in year 0
- For loan financing, there's a down payment in year 0 and then loan payments for the loan term

Specifically, the calculate_annual_cost method should:
1. Take parameters: year, vehicle, and params dictionary
2. Check if the year is the start year (params['start_year'])
3. Check the financing method (params['financing_method'])
4. Calculate the appropriate cost for that year

Please include handling for different loan terms, interest rates, and down payment percentages from the params dictionary.
```

#### Code Explanation

```
I'm trying to understand this TCO calculation logic. Can you explain how the discounting is being applied in this code block?

```python
def _calculate_total_costs(self, annual_costs: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
    """Apply discounting and calculate total costs."""
    years = annual_costs.index
    discount_factors = pd.Series(
        [(1 / (1 + scenario.discount_rate)) ** (year - scenario.start_year) for year in years],
        index=years
    )
    
    # Apply discount factors to all cost columns
    discounted_costs = annual_costs.multiply(discount_factors, axis=0)
    
    return discounted_costs
```

Specifically, I want to understand:
1. How the discount factors are calculated
2. How they are applied to the annual costs
3. Whether this implementation correctly handles the time value of money
```

#### Debugging

```
I'm getting unexpected results from my battery degradation calculation. The degradation seems too rapid.

Here's my current implementation:

```python
def calculate_battery_degradation(self, age: int, total_mileage: float) -> float:
    """
    Calculate battery capacity degradation factor.
    
    Args:
        age: Battery age in years
        total_mileage: Total kilometres driven
        
    Returns:
        Remaining capacity as a fraction of original (0-1)
    """
    cycle_degradation = min(1.0, total_mileage / (self.battery_capacity * 500))
    calendar_degradation = min(1.0, age / 20)
    
    # Combined degradation (typically 80% after 8 years or 160,000 km)
    remaining_capacity = 1.0 - (0.7 * cycle_degradation + 0.3 * calendar_degradation)
    return max(0.0, remaining_capacity)
```

For a 300 kWh battery after 5 years and 300,000 km, I'm getting a remaining capacity of about 65%, which seems too low based on industry data. Can you help identify what might be wrong and suggest improvements?
```

#### Refactoring

```
I'd like to refactor my scenario loading/saving functionality to be more maintainable and handle edge cases better.

Here's my current implementation:

```python
def load_scenario(scenario_name: str) -> Dict[str, Any]:
    """Load a scenario from a file."""
    scenario_dir = os.path.join('config', 'scenarios')
    filepath = os.path.join(scenario_dir, f"{scenario_name}.yaml")
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    raise FileNotFoundError(f"Scenario file not found: {scenario_name}")

def save_scenario(scenario_name: str, scenario_data: Dict[str, Any]) -> str:
    """Save a scenario to a file."""
    scenario_dir = os.path.join('config', 'scenarios')
    os.makedirs(scenario_dir, exist_ok=True)
    
    filepath = os.path.join(scenario_dir, f"{scenario_name}.yaml")
    
    with open(filepath, 'w') as f:
        yaml.dump(scenario_data, f, default_flow_style=False)
    
    return filepath
```

I'd like to improve it by:
1. Adding better error handling
2. Supporting different file formats (maybe JSON as an alternative)
3. Validating the scenario data before saving
4. Adding versioning capability for backward compatibility

Can you refactor this code with these improvements?
```

#### Documentation

```
Can you generate comprehensive docstrings for my TCOCalculator class?

```python
class TCOCalculator:
    """Calculates Total Cost of Ownership for vehicles over a specified period."""
    
    def __init__(self):
        """Initialize the TCO Calculator."""
        self.components = {
            'acquisition': AcquisitionCost(),
            'energy': EnergyCost(),
            'maintenance': MaintenanceCost(),
            'infrastructure': InfrastructureCost(),
            'battery_replacement': BatteryReplacementCost(),
            'insurance': InsuranceCost(),
            'registration': RegistrationCost(),
            'residual_value': ResidualValue()
        }
    
    def calculate(self, scenario: Scenario) -> Dict:
        # Implementation details...
    
    def _calculate_annual_costs(self, vehicle: Vehicle, scenario: Scenario, is_electric: bool) -> pd.DataFrame:
        # Implementation details...
    
    def _calculate_total_costs(self, annual_costs: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
        # Implementation details...
    
    def _find_parity_year(self, electric_costs: pd.DataFrame, diesel_costs: pd.DataFrame) -> Optional[int]:
        # Implementation details...
    
    def _calculate_lcod(self, total_costs: pd.DataFrame, annual_mileage: float) -> float:
        # Implementation details...
```

Please follow the NumPy docstring format with Parameters, Returns, and Examples sections where appropriate.
```

### 3.3 Project-Specific Prompt Templates

Use these templates tailored to the Australian Heavy Vehicle TCO Modeller:

#### Vehicle Class Implementation Template

```
I need to implement the [VehicleType] class for my TCO model.

Requirements:
- It should inherit from the base Vehicle class
- It needs to override the calculate_energy_consumption method
- It needs to override the calculate_energy_cost method
- It should add the following specific attributes and methods:
  [List specific attributes and methods]

The class should follow the structure in the Model Design Specifications document, specifically the [relevant section reference].

Additional context:
- Energy consumption is measured in [units]
- Calculations should account for [specific considerations]
```

#### Cost Component Implementation Template

```
I need to implement the [ComponentName] class for the TCO model.

Requirements:
- It should inherit from the CostComponent abstract class
- It needs to implement the calculate_annual_cost method
- It should handle the following scenarios:
  [List specific scenarios]

Implementation details:
- For year [X], it should [behavior description]
- It should use the following formula: [formula description]
- Edge cases to consider: [list edge cases]

This component relates to the [relevant section] in the Model Design Specifications document.
```

#### Streamlit UI Component Template

```
I need to implement a Streamlit [component type] for the TCO modeller UI.

Requirements:
- It should display [description of what to display]
- It should be placed in the [location] of the UI
- It should update when [trigger conditions]
- It should handle the following user interactions:
  [List interactions]

Design considerations:
- Follow the style guidelines in the UI Design Plan
- Use the color scheme: [color details]
- Ensure accessibility with clear labels and instructions

The component should integrate with the existing code by [integration details].
```

## 4. Collaborative Development Workflow

### 4.1 AI-Assisted Task Breakdown

Break down development tasks to work effectively with AI:

1. **Architectural Design** (Human-Led, AI-Assisted)
   - Define high-level architecture and components
   - Use AI to review and suggest improvements
   - Document design decisions

2. **Interface Definition** (Collaborative)
   - Define key interfaces and data structures
   - Use AI to generate interface definitions
   - Refine interfaces based on implementation needs

3. **Component Implementation** (AI-Assisted)
   - Generate initial implementations with AI
   - Review, test, and refine implementations
   - Focus on complex business logic

4. **Testing** (Collaborative)
   - Define test requirements
   - Use AI to generate test cases
   - Human review for coverage and edge cases

5. **Documentation** (AI-Assisted)
   - Use AI to generate initial documentation
   - Human review for accuracy and completeness
   - Maintain consistency across documents

### 4.2 Step-by-Step Development Process

Follow this process for each component:

1. **Requirements Clarification**
   - Clearly define what the component should do
   - Identify inputs, outputs, and behaviors
   - Reference relevant sections of the PRD

2. **Initial Implementation**
   - Prompt AI to generate a first implementation
   - Review for correctness and adherence to requirements
   - Identify areas needing refinement

3. **Iterative Refinement**
   - Address specific issues with targeted prompts
   - Request explanations for complex logic
   - Ask for alternative approaches if needed

4. **Testing and Validation**
   - Prompt AI to generate tests
   - Implement additional tests for edge cases
   - Verify component works correctly

5. **Integration**
   - Connect component to the larger system
   - Prompt AI for help with integration issues
   - Test integration points

6. **Documentation**
   - Request AI-generated documentation
   - Review and enhance documentation
   - Ensure consistency with other components

### 4.3 Example Development Sequence

Here's an example of developing the `EnergyCost` component:

1. **Requirements Clarification**
   - Review the Model Design Specifications section on Energy Cost
   - Identify the calculation formula and required parameters
   - Note any special handling for different vehicle types

2. **Initial Implementation**
   ```
   I need to implement the EnergyCost class for my TCO model. This class should:
   
   1. Inherit from the CostComponent abstract class
   2. Implement the calculate_annual_cost method
   3. Calculate energy costs differently based on vehicle type (Electric vs Diesel)
   4. Use the formulas specified in the Model Design Specifications section 2.2
   
   For electric vehicles, it should use the annual distance, energy consumption rate (kWh/km), and electricity price.
   For diesel vehicles, it should use the annual distance, fuel consumption rate (L/km), and diesel price.
   
   The energy prices should come from the params dictionary, which contains year-specific price projections.
   ```

3. **Iterative Refinement**
   ```
   Thanks for the implementation. I have a few refinements:
   
   1. The code assumes a single electricity price, but we need to handle year-specific prices from the params dictionary.
   2. We should add better error handling if the energy price for a specific year is not found.
   3. Can you add more detailed comments explaining the calculation logic?
   ```

4. **Testing and Validation**
   ```
   Now I need unit tests for the EnergyCost class. Please create a comprehensive test suite that:
   
   1. Tests both electric and diesel vehicles
   2. Tests with different energy prices and consumption rates
   3. Tests edge cases (zero distance, missing price data, etc.)
   4. Verifies the calculations match expected results
   ```

5. **Integration**
   ```
   I'm integrating the EnergyCost component into the TCOCalculator. I'm seeing an issue where the energy cost calculation seems to be using the wrong year's price data. Can you help me debug this integration issue?
   
   Here's how I'm calling it in the TCOCalculator:
   
   ```python
   # Current integration code...
   ```
   ```

6. **Documentation**
   ```
   Can you generate comprehensive documentation for the EnergyCost class? Include:
   
   1. Class purpose and overview
   2. Detailed method descriptions
   3. Parameter explanations
   4. Examples of typical usage
   5. Notes on any assumptions or limitations
   ```

## 5. AI-Assisted Code Review

### 5.1 Using AI for Self-Review

Leverage AI to review your own code:

1. **Functionality Review**
   ```
   I've implemented the BatteryReplacementCost component. Can you review it for:
   
   1. Correctness in implementing the battery replacement logic
   2. Proper handling of different replacement scenarios (fixed year vs capacity threshold)
   3. Any potential edge cases I might have missed
   
   ```python
   # Implementation code...
   ```
   ```

2. **Style and Consistency Review**
   ```
   Can you review this code for style and consistency with the rest of the project?
   
   Specifically check for:
   1. Adherence to Python PEP 8 style guidelines
   2. Consistency with our project's naming conventions
   3. Appropriate use of docstrings and comments
   
   ```python
   # Implementation code...
   ```
   ```

3. **Performance Review**
   ```
   I'm concerned about the performance of this calculation method. Can you review it for potential optimization opportunities?
   
   ```python
   # Implementation code...
   ```
   
   The method will be called frequently during TCO calculations, so efficiency is important.
   ```

### 5.2 Collaborative Review Process

Combine AI and human review:

1. **Initial AI Review**
   - Submit code for AI review using templates above
   - Address obvious issues identified by AI

2. **Human Review**
   - Conduct human code review focusing on business logic
   - Pay attention to areas where AI might be limited

3. **Final AI Polish**
   - Use AI to help with final refinements
   - Focus on documentation and edge cases

### 5.3 Review Checklist

Use this checklist with AI assistance:

1. **Functionality**
   - Does the code correctly implement requirements?
   - Are all edge cases handled?
   - Is error handling appropriate?

2. **Code Quality**
   - Is the code readable and maintainable?
   - Are functions and methods appropriately sized?
   - Is there appropriate abstraction and encapsulation?

3. **Performance**
   - Are there any obvious performance issues?
   - Is memory usage efficient?
   - Are there opportunities for caching or optimization?

4. **Testing**
   - Is test coverage adequate?
   - Are edge cases tested?
   - Are tests readable and maintainable?

5. **Documentation**
   - Are docstrings complete and accurate?
   - Is complex logic explained?
   - Are public APIs well-documented?

## 6. Troubleshooting AI Collaboration

### 6.1 Common Challenges and Solutions

#### Challenge: Incomplete or Incorrect Context

**Solution:**
- Provide more specific context in your prompt
- Reference specific file names, class names, and requirements
- Share relevant code snippets that show the surrounding context

Example:
```
I'm working on the BatteryReplacementCost class in tco_model/components.py. It needs to work with the ElectricVehicle class in tco_model/vehicles.py, which has this battery degradation method:

```python
def calculate_battery_degradation(self, age: int, total_mileage: float) -> float:
    # Implementation details...
```

The BatteryReplacementCost should use this method to determine when replacement is needed based on the scenario.
```

#### Challenge: Generated Code Doesn't Follow Project Patterns

**Solution:**
- Explicitly mention the patterns to follow
- Provide examples of existing code that follows the pattern
- Ask for a revision to match the pattern

Example:
```
The implementation you provided is good functionally, but it doesn't follow our project's error handling pattern. In our project, we use custom exceptions defined in tco_model/exceptions.py and wrap external API calls in try/except blocks like this:

```python
try:
    # Operation that might fail
except ExternalError as e:
    raise ModelError(f"Operation failed: {str(e)}") from e
```

Can you revise your implementation to follow this pattern?
```

#### Challenge: AI Generates Overly Complex Solutions

**Solution:**
- Specify a preference for simplicity
- Ask for alternatives with explanations
- Request a simpler approach for specific parts

Example:
```
The solution you provided seems more complex than necessary. We prefer simpler, more maintainable approaches in this project. Can you provide a simpler alternative that:

1. Uses standard library functions where possible
2. Reduces the number of nested conditionals
3. Follows the principle of "explicit is better than implicit"
```

#### Challenge: AI Misunderstands Domain-Specific Terms

**Solution:**
- Define terms explicitly
- Provide examples of correct usage
- Reference documentation for clarification

Example:
```
In my previous prompt, there seems to be a misunderstanding about what "battery degradation" means in our context. In our TCO model, battery degradation refers specifically to the reduction in usable capacity over time and usage, not physical degradation or failure.

For clarity:
- Battery capacity starts at 100% when new
- It gradually decreases due to cycling (usage) and calendar aging
- When capacity drops below a threshold (e.g., 70%), a replacement may be triggered

Can you revise your implementation with this understanding?
```

### 6.2 Improving AI Responses

Techniques to get better AI assistance:

1. **Use Chain-of-Thought Prompting**
   - Ask the AI to work through the problem step by step
   - Break complex tasks into smaller logical parts

   Example:
   ```
   I need to implement the TCO parity point calculation. Let's break this down:
   
   1. First, we need to calculate cumulative costs for both vehicle types
   2. Then, we need to find the year where the electric cumulative cost becomes lower than diesel
   3. Finally, we need to handle cases where parity doesn't occur
   
   Can you help me implement this step by step?
   ```

2. **Request Multiple Approaches**
   - Ask for alternative implementations
   - Compare different approaches for clarity and efficiency

   Example:
   ```
   Can you provide two different approaches to implementing the residual value calculation?
   
   1. A straightforward approach using a simple formula
   2. A more sophisticated approach that accounts for different factors
   
   Explain the trade-offs between these approaches.
   ```

3. **Use Iterative Refinement**
   - Start with a basic implementation
   - Gradually improve specific aspects
   - Build complexity incrementally

   Example:
   ```
   Let's start with a basic implementation of the sensitivity analysis function.
   
   Once we have that working, we'll refine it to handle:
   1. Different parameter ranges
   2. Custom sensitivity metrics
   3. Visualization of results
   ```

## 7. Special Considerations for Streamlit Development

### 7.1 AI-Assisted Streamlit Best Practices

Leverage AI to implement Streamlit best practices:

1. **State Management**
   - Use AI to generate proper session state handling
   - Review state initialization and updates

   Example Prompt:
   ```
   I need to implement session state management for my Streamlit app. Specifically, I need to:
   
   1. Initialize state variables for the current scenario and results
   2. Update state when a user loads a saved scenario
   3. Preserve state between reruns when parameters change
   
   Can you provide an implementation following Streamlit best practices?
   ```

2. **Performance Optimization**
   - Use AI to identify caching opportunities
   - Request implementation of caching decorators

   Example Prompt:
   ```
   My Streamlit app is performing TCO calculations that are computationally expensive. Can you help me implement proper caching using Streamlit's caching decorators?
   
   These functions are particularly slow and would benefit from caching:
   
   ```python
   def calculate_tco(scenario_params):
       # Expensive calculation...
   
   def load_config():
       # Expensive loading operation...
   ```
   
   Please explain which caching decorator is most appropriate for each and why.
   ```

3. **UI Layout and Components**
   - Use AI to generate layout code
   - Request responsive design implementations

   Example Prompt:
   ```
   I need to create a responsive layout for my Streamlit TCO calculator that:
   
   1. Shows summary metrics in a row of cards at the top
   2. Displays the main visualizations in a tabbed interface
   3. Adapts well to different screen sizes
   
   Can you provide the Streamlit code to implement this layout?
   ```

### 7.2 Handling Streamlit Specific Challenges

Get AI help for common Streamlit challenges:

1. **Widget Key Management**
   - Use AI to implement consistent key strategies
   - Troubleshoot widget state issues

   Example Prompt:
   ```
   I'm having an issue with Streamlit widgets re-initializing on each rerun. Can you help me implement a proper key strategy for these input widgets?
   
   ```python
   # Current implementation with issues
   vehicle_type = st.selectbox("Vehicle Type", options=["Rigid", "Articulated"])
   annual_mileage = st.number_input("Annual Kilometres", min_value=10000, max_value=200000)
   ```
   
   I want the widgets to maintain their values when other parts of the UI change.
   ```

2. **Callback Function Implementation**
   - Use AI to generate Streamlit callback functions
   - Ensure correct state updates

   Example Prompt:
   ```
   I need to implement a callback for when the user clicks the "Save Scenario" button. The callback should:
   
   1. Get the current parameter values from the UI
   2. Create a Scenario object
   3. Save it to a file
   4. Show a success message
   
   Can you implement this callback function for Streamlit?
   ```

3. **Form Submission Handling**
   - Get AI help with form implementation
   - Address common form submission issues

   Example Prompt:
   ```
   I want to group my input parameters into a form to avoid constant recalculation. Can you show me how to:
   
   1. Create a form with the vehicle parameters
   2. Add a submit button
   3. Process the form data only on submission
   4. Update the rest of the UI based on the submitted values
   ```

## 8. Project-Specific AI Collaboration Tips

### 8.1 TCO Model Implementation Tips

Tips specific to implementing the TCO model:

1. **Mathematical Formula Implementation**
   - Ask AI to translate mathematical formulas into code
   - Verify correctness with test cases

   Example Prompt:
   ```
   I need to implement the Levelized Cost of Driving (LCOD) calculation as defined in the Model Design Specifications:
   
   LCOD = TCO / (Sum of discounted annual distances)
   
   The mathematical formula is:
   
   LCOD = ∑(C_t / (1+r)^t) / ∑(D_t / (1+r)^t)
   
   Where:
   - C_t is the total cost in year t
   - D_t is the distance traveled in year t
   - r is the discount rate
   
   Can you implement this in Python, using pandas for the series operations?
   ```

2. **Time Series Handling**
   - Get AI help with pandas operations
   - Request efficient implementations for year-based calculations

   Example Prompt:
   ```
   I need to implement year-based calculations for my TCO model using pandas. Specifically, I need to:
   
   1. Create a DataFrame with years as the index (2025-2040)
   2. Calculate costs for each year based on different parameters
   3. Apply year-specific prices from a dictionary of projections
   4. Calculate cumulative and discounted values
   
   Can you show me an efficient way to implement this?
   ```

3. **Sensitivity Analysis Implementation**
   - Use AI to generate parameter variation logic
   - Request visualization code for tornado charts

   Example Prompt:
   ```
   I need to implement a sensitivity analysis function that:
   
   1. Takes a baseline scenario
   2. Varies each key parameter (e.g., ±20%)
   3. Calculates the TCO for each variation
   4. Returns the impact on TCO difference (Electric - Diesel)
   
   Can you implement this function and also provide Plotly code to create a tornado chart from the results?
   ```

### 8.2 UI Implementation Tips

Tips for implementing the Streamlit UI:

1. **Chart Implementation**
   - Request Plotly implementation for specific visualizations
   - Ask for customization based on UI design

   Example Prompt:
   ```
   I need to implement the cumulative TCO chart as described in the UI Design Plan section 4.2. The chart should:
   
   1. Show cumulative costs over time for both electric and diesel
   2. Mark the parity point with a special marker
   3. Use the specified color scheme (Electric: #00CC96, Diesel: #EF553B)
   4. Include proper formatting for currency values
   
   Can you provide the Plotly and Streamlit code to implement this?
   ```

2. **Input Form Organization**
   - Get AI help with organizing inputs logically
   - Request expandable sections implementation

   Example Prompt:
   ```
   I need to organize my TCO calculator inputs following the UI Design Plan section 3.1. Can you implement the sidebar input controls with:
   
   1. Expandable sections for different parameter groups
   2. Appropriate input widgets for each parameter type
   3. Default values and validation
   4. Help text for complex parameters
   
   Focus specifically on the "Electric Vehicle Parameters" and "Diesel Vehicle Parameters" sections.
   ```

3. **Results Display**
   - Use AI to generate result formatting code
   - Request implementation of summary metrics

   Example Prompt:
   ```
   I need to implement the Key Metrics Area as described in the UI Design Plan section 4.1. This should:
   
   1. Display summary metrics in a row at the top
   2. Include 15-Year TCO values for both vehicle types
   3. Show the TCO parity point year
   4. Display the Levelized Cost per Kilometre with comparison
   
   Can you provide the Streamlit code to implement this display?
   ```

### 8.3 Data Management Tips

Tips for managing data and configuration:

1. **Configuration File Handling**
   - Request code for loading and parsing YAML configurations
   - Get help with configuration validation

   Example Prompt:
   ```
   I need to implement functions to load and validate configuration data from YAML files, including:
   
   1. Vehicle specifications
   2. Energy price projections
   3. Battery cost projections
   
   The functions should handle missing files, validate required fields, and provide default values where appropriate.
   
   Can you implement these functions following the structure in the Code Structure Plan?
   ```

2. **Scenario Management**
   - Use AI to implement scenario saving/loading
   - Request robust error handling

   Example Prompt:
   ```
   I need to enhance the scenario management functionality to:
   
   1. Save scenarios to YAML files with proper formatting
   2. Load scenarios from files with validation
   3. List available saved scenarios
   4. Handle errors gracefully with user-friendly messages
   
   Can you implement these functions based on the Code Structure Plan?
   ```

3. **Result Export**
   - Get AI help with exporting results to different formats
   - Request formatting and organization implementations

   Example Prompt:
   ```
   I need to implement functions to export TCO results to:
   
   1. CSV format for simple data analysis
   2. Excel format with multiple sheets and formatting
   
   The Excel export should include:
   - A summary sheet with key metrics
   - Detailed sheets for electric and diesel costs
   - Formatting for currency values and percentages
   
   Can you implement these export functions?
   ```

## 9. Continuous Learning and Improvement

### 9.1 Building a Knowledge Base

Develop a project-specific knowledge base:

1. **Document Successful Prompts**
   - Save prompts that yielded good results
   - Organize by task type and component

2. **Create Prompt Templates**
   - Develop standardized templates for common tasks
   - Refine based on what works best

3. **Maintain Code Examples**
   - Collect exemplary implementations
   - Use as references for future development

### 9.2 Refining Your Approach

Continuously improve your AI collaboration:

1. **Review and Reflect**
   - Analyze which approaches worked well
   - Identify areas for improvement

2. **Experiment with Different Styles**
   - Try different prompting techniques
   - Test varying levels of detail and structure

3. **Incorporate Feedback**
   - Adjust based on code review feedback
   - Learn from collaboration experiences

### 9.3 Staying Current

Keep up-to-date with AI capabilities:

1. **Follow AI Tool Updates**
   - Monitor Cursor release notes and updates
   - Explore new features and capabilities

2. **Learn from Community**
   - Participate in forums and discussions
   - Share and gather effective practices

3. **Apply New Techniques**
   - Incorporate new prompting strategies
   - Experiment with emerging best practices

## Conclusion

Effective collaboration with AI assistants in Cursor can significantly accelerate the development of the Australian Heavy Vehicle TCO Modeller. By following the strategies outlined in this document, you can maximize productivity, maintain code quality, and create a powerful tool for analyzing total cost of ownership for heavy vehicles in Australia.

Remember that AI assistance is a tool to enhance your capabilities, not replace critical thinking and domain expertise. Combine AI's strengths in code generation and pattern recognition with your understanding of the business requirements and Australian context to create a robust, accurate, and user-friendly TCO modelling application.
