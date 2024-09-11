import pandas as pd
from datetime import datetime
from pulp import LpProblem, LpMaximize, LpVariable, lpSum
from typing import Union, Dict

# Constants
DATE_FORMAT = '%d.%m.%Y'

def calculate_age(birthdate: Union[str, pd.Timestamp]) -> int:
    """
    Calculate age based on birthdate, including cases where the age is negative (i.e., unborn children).
    Handles both string and pd.Timestamp formats.
    """
    if isinstance(birthdate, str):
        birthdate = datetime.strptime(birthdate, DATE_FORMAT)
    elif isinstance(birthdate, pd.Timestamp):
        birthdate = birthdate.to_pydatetime()
        
    today = datetime.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def optimize_group_assignment(df: pd.DataFrame, group_capacities: Dict[str, int], 
                              points_weight: float = 1, age_distribution_weight: float = 0, 
                              gender_balance_weight: float = 0, age_balance_weight: float = 0,
                              min_age_limits: Dict[str, int] = None, max_age_limits: Dict[str, int] = None,
                              abs_diff_gender_penalty: float = 1.0, abs_diff_age_penalty: float = 1.0) -> pd.DataFrame:
    """
    Optimizes group assignments based on points, age, and gender distribution.
    Includes optional age constraints (min and max age per group), penalties for gender balance and age balance.
    
    Parameters:
        - df: The input DataFrame with members data.
        - group_capacities: Dictionary with group capacities.
        - points_weight: Weight for points optimization.
        - age_distribution_weight: Weight for balancing age distribution.
        - gender_balance_weight: Weight for balancing gender distribution.
        - age_balance_weight: Weight for balancing age across groups.
        - min_age_limits: Dictionary of minimum age limits per group.
        - max_age_limits: Dictionary of maximum age limits per group.
        - abs_diff_gender_penalty: Penalty for gender balance differences.
        - abs_diff_age_penalty: Penalty for age balance differences.
    
    Returns:
        - A DataFrame with optimized group assignments.
    """
    df_opt = df.copy()

    # Validate input data
    required_columns = ['Gruppe', 'Age', 'Geschlecht', 'Gesamtpunkte']
    if not all(col in df_opt.columns for col in required_columns):
        raise ValueError(f"DataFrame must contain the following columns: {required_columns}")
    
    # Filter for unassigned children
    unassigned_indices = df_opt[df_opt['Gruppe'].isnull()].index.tolist()
    
    # Group and demographic variables
    groups = list(group_capacities.keys())
    age_classes = df_opt['Age'].unique()
    genders = df_opt['Geschlecht'].unique()

    # Initialize the optimization problem
    prob = LpProblem("Group_Assignment", LpMaximize)

    # Decision variables: x[i][j] = 1 if child i is assigned to group j
    x = LpVariable.dicts("assign", ((i, j) for i in unassigned_indices for j in groups), cat='Binary')

    # Helper variables for diversity and penalties
    s = LpVariable.dicts("s", ((k, j) for k in age_classes for j in groups), lowBound=0)
    t = LpVariable.dicts("t", (j for j in groups), lowBound=0)

    # Variables for absolute differences in gender and age distribution
    abs_diff_gender = LpVariable.dicts("abs_diff_gender", ((k, j) for k in age_classes for j in groups), lowBound=0)
    abs_diff_age = LpVariable.dicts("abs_diff_age", (j for j in groups), lowBound=0)

    # Objective function: maximize total points and enforce diversity goals
    prob += (
        points_weight * lpSum([df_opt.loc[i, 'Gesamtpunkte'] * x[(i, j)] for i in unassigned_indices for j in groups])
        - gender_balance_weight * abs_diff_gender_penalty * lpSum([abs_diff_gender[(k, j)] for k in age_classes for j in groups])
        - age_balance_weight * abs_diff_age_penalty * lpSum([abs_diff_age[j] for j in groups])
    )

    # Constraint: each child is assigned to exactly one group
    for i in unassigned_indices:
        prob += lpSum([x[(i, j)] for j in groups]) == 1

    # Constraint: group capacities are not exceeded
    for j in groups:
        assigned_in_group = df_opt[df_opt['Gruppe'] == j].shape[0]
        prob += lpSum([x[(i, j)] for i in unassigned_indices]) + assigned_in_group <= group_capacities[j]

    # Gender distribution constraint (if gender_balance_weight > 0)
    if gender_balance_weight > 0:
        for j in groups:
            for k in age_classes:
                male_count = lpSum([x[(i, j)] for i in unassigned_indices if df_opt.loc[i, 'Geschlecht'] == 'männlich' and df_opt.loc[i, 'Age'] == k])
                female_count = lpSum([x[(i, j)] for i in unassigned_indices if df_opt.loc[i, 'Geschlecht'] == 'weiblich' and df_opt.loc[i, 'Age'] == k])
                
                # Absolute value constraints for gender balance
                prob += abs_diff_gender[(k, j)] >= male_count - female_count
                prob += abs_diff_gender[(k, j)] >= female_count - male_count
                prob += s[(k, j)] >= abs_diff_gender[(k, j)]  # Linking helper variable to objective

    # Age distribution constraint (if age_balance_weight > 0)
    if age_balance_weight > 0:
        for j in groups:
            total_count = lpSum([x[(i, j)] for i in unassigned_indices])
            for k in age_classes:
                age_count = lpSum([x[(i, j)] for i in unassigned_indices if df_opt.loc[i, 'Age'] == k])

                # Absolute value constraints for age balance
                prob += abs_diff_age[j] >= age_count - total_count
                prob += abs_diff_age[j] >= total_count - age_count
                prob += t[j] >= abs_diff_age[j]  # Linking helper variable to objective

    # Min/Max age constraints (optional)
    if min_age_limits:
        for j in groups:
            if j in min_age_limits:
                min_age = min_age_limits[j]
                prob += lpSum([x[(i, j)] for i in unassigned_indices if df_opt.loc[i, 'Age'] < min_age]) == 0

    if max_age_limits:
        for j in groups:
            if j in max_age_limits:
                max_age = max_age_limits[j]
                prob += lpSum([x[(i, j)] for i in unassigned_indices if df_opt.loc[i, 'Age'] > max_age]) == 0

    # Solve the optimization problem
    prob.solve()

    # Update the DataFrame with the results
    current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    for i in unassigned_indices:
        for j in groups:
            if x[(i, j)].varValue == 1:
                df_opt.at[i, 'Gruppe'] = j
                df_opt.at[i, 'Geändert'] = current_time
                df_opt.at[i, 'Geändert von'] = 'Optimization algorithm'

    return df_opt
