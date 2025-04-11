# Model Design Specifications

This document provides detailed specifications for the TCO calculation model, including the mathematical formulations, assumptions, data sources, and validation approaches.

## 1. TCO Framework Overview

The Total Cost of Ownership (TCO) model follows a comprehensive accounting approach that captures all significant costs incurred over the entire vehicle lifecycle from acquisition to disposal. The model implements a discounted cash flow methodology to account for the time value of money.

### 1.1 Mathematical Framework

The core TCO calculation follows this formula:

$$TCO = \sum_{t=0}^{T} \frac{C_t}{(1+r)^t}$$

Where:
- $TCO$ is the total cost of ownership in present value terms
- $C_t$ is the total cost in year $t$
- $r$ is the real discount rate
- $T$ is the analysis period in years (typically 15 years)

The annual cost $C_t$ is the sum of the component costs:

$$C_t = C_{acq,t} + C_{eng,t} + C_{maint,t} + C_{infra,t} + C_{batt,t} + C_{ins,t} + C_{reg,t} - C_{resid,t}$$

Where:
- $C_{acq,t}$ is the acquisition cost (vehicle purchase, financing)
- $C_{eng,t}$ is the energy cost (electricity or diesel)
- $C_{maint,t}$ is the maintenance and repair cost
- $C_{infra,t}$ is the infrastructure cost (charging equipment for BETs)
- $C_{batt,t}$ is the battery replacement cost (for BETs)
- $C_{ins,t}$ is the insurance cost
- $C_{reg,t}$ is the registration and road user charge
- $C_{resid,t}$ is the residual value (only applied in the final year)

### 1.2 Levelized Cost of Driving

The model also calculates the Levelized Cost of Driving (LCOD) in $ per km:

$$LCOD = \frac{TCO}{\sum_{t=0}^{T} \frac{D_t}{(1+r)^t}}$$

Where $D_t$ is the annual distance travelled in year $t$.

## 2. Cost Component Specifications

Each cost component follows specific calculation methodologies, described below.

### 2.1 Acquisition Cost

#### 2.1.1 Cash Purchase

For a cash purchase, the full cost is applied in year 0:

$$C_{acq,0} = P$$

Where $P$ is the vehicle purchase price.

#### 2.1.2 Loan Financing

For loan financing, the costs are distributed according to the loan terms:

$$C_{acq,0} = P \times d$$

$$C_{acq,t} = \frac{P \times (1-d) \times i \times (1+i)^n}{(1+i)^n - 1} \text{ for } 1 \leq t \leq n$$

Where:
- $P$ is the vehicle purchase price
- $d$ is the down payment percentage
- $i$ is the annual interest rate
- $n$ is the loan term in years

#### 2.1.3 Default Values

| Parameter | Electric Vehicle | Diesel Vehicle | Source |
|-----------|------------------|----------------|--------|
| Purchase Price (Rigid) | A$400,000 | A$200,000 | Industry reports [1] |
| Purchase Price (Articulated) | A$600,000 | A$300,000 | Industry reports [1] |
| Loan Term | 5 years | 5 years | Common practice |
| Interest Rate | 7% | 7% | Current market rates |
| Down Payment | 20% | 20% | Common practice |

### 2.2 Energy Cost

#### 2.2.1 Electric Vehicles

For BETs, the annual energy cost is:

$$C_{eng,t} = D_t \times e_{BET} \times p_{elec,t}$$

Where:
- $D_t$ is the annual distance in km
- $e_{BET}$ is the energy consumption in kWh/km
- $p_{elec,t}$ is the electricity price in $/kWh in year $t$

#### 2.2.2 Diesel Vehicles

For diesel vehicles, the annual energy cost is:

$$C_{eng,t} = D_t \times e_{ICE} \times p_{diesel,t}$$

Where:
- $D_t$ is the annual distance in km
- $e_{ICE}$ is the fuel consumption in L/km
- $p_{diesel,t}$ is the diesel price in $/L in year $t$

#### 2.2.3 Default Values

| Parameter | Value | Source |
|-----------|-------|--------|
| Electric Energy Consumption (Rigid) | 0.9 kWh/km | Literature review [2] |
| Electric Energy Consumption (Articulated) | 1.5 kWh/km | Literature review [2] |
| Diesel Fuel Consumption (Rigid) | 30 L/100km | ABS data [3] |
| Diesel Fuel Consumption (Articulated) | 50 L/100km | ABS data [3] |
| Electricity Price (2025) | $0.20/kWh | Current market rates |
| Diesel Price (2025) | $1.70/L | Current market rates |

### 2.3 Maintenance Cost

#### 2.3.1 Calculation Method

Maintenance costs are calculated based on distance driven:

$$C_{maint,t} = D_t \times m$$

Where:
- $D_t$ is the annual distance in km
- $m$ is the maintenance cost per km

#### 2.3.2 Default Values

| Parameter | Value | Source |
|-----------|-------|--------|
| Electric Maintenance Cost | $0.08/km | Industry estimates [4] |
| Diesel Maintenance Cost | $0.15/km | Industry estimates [4] |

### 2.4 Infrastructure Cost

#### 2.4.1 Calculation Method

For BETs, charging infrastructure costs are amortized over the infrastructure's lifetime:

$$C_{infra,t} = \frac{C_{charger} + C_{install}}{L_{charger}} \text{ for } 0 \leq t < L_{charger}$$

Where:
- $C_{charger}$ is the charger hardware cost
- $C_{install}$ is the installation cost
- $L_{charger}$ is the charger lifespan in years

For diesel vehicles, this cost is typically zero (using existing refueling infrastructure).

#### 2.4.2 Default Values

| Parameter | Value | Source |
|-----------|-------|--------|
| Charger Hardware Cost | $50,000 | Industry quotes [5] |
| Installation Cost | $50,000 | Industry quotes [5] |
| Charger Lifespan | 10 years | Manufacturer specifications |

### 2.5 Battery Replacement Cost

#### 2.5.1 Calculation Method

Battery replacement costs are applied in the year when replacement occurs:

$$C_{batt,t} = \begin{cases}
B_{cap} \times p_{batt,t} & \text{if } t = t_{replace} \\
0 & \text{otherwise}
\end{cases}$$

Where:
- $B_{cap}$ is the battery capacity in kWh
- $p_{batt,t}$ is the battery price per kWh in year $t$
- $t_{replace}$ is the replacement year

The replacement year can be determined either by a fixed schedule or by a capacity threshold:

$$t_{replace} = \begin{cases}
t_{fixed} & \text{if using fixed schedule} \\
\min\{t | C_{rem}(t) < C_{threshold}\} & \text{if using capacity threshold}
\end{cases}$$

Where:
- $t_{fixed}$ is the predetermined replacement year
- $C_{rem}(t)$ is the remaining battery capacity at year $t$
- $C_{threshold}$ is the capacity threshold (e.g., 70%)

#### 2.5.2 Battery Degradation Model

The remaining battery capacity is modeled as:

$$C_{rem}(t) = 1.0 - (w_{cycle} \times d_{cycle}(t) + w_{cal} \times d_{cal}(t))$$

Where:
- $w_{cycle}$ is the weighting for cycle degradation (typically 0.7)
- $d_{cycle}(t)$ is the cycle degradation factor
- $w_{cal}$ is the weighting for calendar degradation (typically 0.3)
- $d_{cal}(t)$ is the calendar degradation factor

The cycle degradation is calculated based on total energy throughput:

$$d_{cycle}(t) = \min\left(1.0, \frac{D_{total}(t) \times e_{BET}}{B_{cap} \times N_{cycles}}\right)$$

Where:
- $D_{total}(t)$ is the total distance driven up to year $t$
- $N_{cycles}$ is the rated cycle life of the battery (typically 1000-2000)

The calendar degradation is time-based:

$$d_{cal}(t) = \min\left(1.0, \frac{t}{L_{batt}}\right)$$

Where $L_{batt}$ is the calendar life of the battery (typically 15-20 years).

#### 2.5.3 Default Values

| Parameter | Value | Source |
|-----------|-------|--------|
| Battery Price (2025) | $170/kWh | Industry projections [6] |
| Battery Price (2030) | $100/kWh | Industry projections [6] |
| Battery Price (2040) | $60/kWh | Industry projections [6] |
| Battery Capacity (Rigid) | 300 kWh | Manufacturer specifications |
| Battery Capacity (Articulated) | 500 kWh | Manufacturer specifications |
| Capacity Threshold | 70% | Industry practice |
| Typical Replacement Year | 8 | Based on warranty periods |

### 2.6 Insurance Cost

#### 2.6.1 Calculation Method

Insurance costs are typically proportional to vehicle value:

$$C_{ins,t} = P \times (1-d_t) \times i_{ins}$$

Where:
- $P$ is the initial vehicle purchase price
- $d_t$ is the depreciation factor at year $t$
- $i_{ins}$ is the insurance rate as a percentage of vehicle value

#### 2.6.2 Default Values

| Parameter | Value | Source |
|-----------|-------|--------|
| Insurance Rate (Electric) | 5% | Industry estimates [7] |
| Insurance Rate (Diesel) | 5% | Industry estimates [7] |

### 2.7 Registration Cost

#### 2.7.1 Calculation Method

Registration costs are applied annually:

$$C_{reg,t} = R$$

Where $R$ is the annual registration cost.

#### 2.7.2 Default Values

| Parameter | Value | Source |
|-----------|-------|--------|
| Annual Registration (Rigid) | $3,000 | State registration schedules |
| Annual Registration (Articulated) | $5,000 | State registration schedules |

### 2.8 Residual Value

#### 2.8.1 Calculation Method

Residual value is applied as a negative cost in the final year:

$$C_{resid,T} = -P \times r_T$$

Where:
- $P$ is the initial vehicle purchase price
- $r_T$ is the residual value percentage at year $T$

#### 2.8.2 Default Values

| Parameter | Value | Source |
|-----------|-------|--------|
| Electric Residual Value (15 years) | 10-15% | Industry estimates [8] |
| Diesel Residual Value (15 years) | 10% | Industry estimates [8] |

## 3. Scenario Management

The model supports scenario management through a structured approach:

### 3.1 Scenario Parameters

Each scenario contains a comprehensive set of parameters that fully define a TCO calculation:

1. **General Parameters**:
   - Scenario name and description
   - Analysis period (start and end years)
   - Vehicle type (rigid or articulated)

2. **Economic Parameters**:
   - Discount rate
   - Inflation rate
   - Financing method and terms

3. **Operational Parameters**:
   - Annual mileage
   - Usage pattern (e.g., urban, regional, long-haul)

4. **Vehicle Parameters**:
   - Electric and diesel vehicle specifications
   - Purchase prices
   - Energy consumption rates

5. **Energy Parameters**:
   - Electricity price projections
   - Diesel price projections

6. **Infrastructure Parameters**:
   - Charger specifications
   - Installation costs

7. **Battery Parameters**:
   - Battery replacement settings
   - Battery cost projections

8. **Residual Parameters**:
   - Residual value percentages

### 3.2 Scenario Storage Format

Scenarios are stored in YAML format for human readability and easy editing:

```yaml
name: "Urban Delivery Scenario"
description: "Analysis of urban delivery trucks with high utilization"
start_year: 2025
end_year: 2040

# Economic parameters
discount_rate: 0.07
inflation_rate: 0.025
financing_method: "loan"
loan_term: 5
interest_rate: 0.07
down_payment_pct: 0.2

# Operational parameters
annual_mileage: 40000

# Vehicle parameters
electric_vehicle_name: "Electric Rigid Truck"
electric_vehicle_price: 400000
electric_vehicle_battery_capacity: 300
electric_vehicle_energy_consumption: 0.9

diesel_vehicle_name: "Diesel Rigid Truck"
diesel_vehicle_price: 200000
diesel_vehicle_fuel_consumption: 30

# (Additional parameters...)
```

### 3.3 Predefined Scenarios

The model includes several predefined scenarios:

1. **Urban Delivery**:
   - Rigid trucks
   - 40,000 km/year
   - Urban driving cycle (lower consumption)
   - Overnight depot charging

2. **Regional Distribution**:
   - Rigid or articulated trucks
   - 60,000 km/year
   - Mixed driving cycle
   - Primarily depot charging with some public charging

3. **Long-Haul**:
   - Articulated trucks
   - 100,000 km/year
   - Highway driving cycle (higher consumption)
   - Mix of depot and public charging

## 4. Sensitivity Analysis

The model includes sensitivity analysis capabilities to identify the most influential parameters:

### 4.1 One-at-a-Time Sensitivity Analysis

This approach varies each parameter individually while holding others constant:

1. Define a baseline scenario
2. Select parameters for sensitivity testing
3. Define variation range for each parameter (e.g., ±20%)
4. Calculate TCO for each parameter variation
5. Compare results to identify influential parameters

### 4.2 Key Parameters for Sensitivity Analysis

The model focuses on these key parameters for sensitivity analysis:

1. **Energy Prices**:
   - Diesel price
   - Electricity price

2. **Vehicle Utilization**:
   - Annual mileage

3. **Vehicle Costs**:
   - BET purchase price
   - Diesel purchase price

4. **Battery Parameters**:
   - Battery replacement cost
   - Battery lifespan

5. **Financial Parameters**:
   - Discount rate
   - Financing terms

6. **Operational Costs**:
   - Maintenance costs

### 4.3 Tornado Chart Visualization

Results are presented in a tornado chart format, showing the impact on TCO difference (BET - Diesel) for each parameter variation.

## 5. Data Sources and Validation

### 5.1 Primary Data Sources

The model uses data from various authoritative sources:

1. **Vehicle Specifications**:
   - Manufacturer published data
   - Industry reports
   - Australian case studies

2. **Energy Prices**:
   - Australian Energy Market Operator (AEMO) projections
   - Australian Petroleum Statistics
   - Industry forecasts

3. **Operational Parameters**:
   - Australian Bureau of Statistics transport surveys
   - Fleet operator data
   - Industry benchmarks

4. **Cost Components**:
   - Industry research reports
   - Academic studies
   - Australian Trucking Association data

### 5.2 Validation Approaches

The model is validated through several methods:

1. **Benchmarking**:
   - Comparison with published TCO studies
   - Alignment with industry estimates
   - Verification against real-world fleet data where available

2. **Consistency Checks**:
   - Internal logic verification
   - Physical/economic plausibility checks
   - Boundary condition testing

3. **Sensitivity Testing**:
   - Identifying unreasonable model behavior
   - Ensuring robust results across parameter ranges

4. **Expert Review**:
   - Consultation with industry experts
   - Peer review of methodology

## 6. Future Enhancements

The model is designed to accommodate future enhancements:

1. **Additional Powertrain Options**:
   - Hydrogen fuel cell vehicles
   - Hybrid electric vehicles
   - Renewable natural gas vehicles

2. **Advanced Operational Modeling**:
   - Route-specific analysis
   - Variable annual utilization
   - Seasonal variation effects

3. **Enhanced Battery Modeling**:
   - Chemistry-specific degradation models
   - Fast-charging impact modeling
   - Temperature effects

4. **Fleet-Level Analysis**:
   - Multi-vehicle fleet optimization
   - Mixed fleet transition strategies
   - Infrastructure sharing optimization

5. **Policy Impact Assessment**:
   - Carbon pricing scenarios
   - ZEV mandate impacts
   - Road user charging reforms

## References

[1] Electric Vehicle Council reports on heavy vehicle costs (2022-2024)  
[2] International Council on Clean Transportation (ICCT) - Total Cost of Ownership for Heavy Trucks (2023)  
[3] Australian Bureau of Statistics - Survey of Motor Vehicle Use (2022)  
[4] Australian Trucking Association - Maintenance Benchmarking Study (2023)  
[5] Infrastructure Australia - EV Charging Infrastructure Market Study (2024)  
[6] BloombergNEF Battery Price Survey (2023)  
[7] Insurance Council of Australia - Commercial Vehicle Insurance Data (2023)  
[8] Truck Industry Council - Residual Value Forecasts (2023)
