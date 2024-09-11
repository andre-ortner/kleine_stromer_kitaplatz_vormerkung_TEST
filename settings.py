import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def settings_page():
    """Settings page to manage groups, capacities, and optimization parameters using Ag-Grid."""
    st.title("Einstellungen")

    st.subheader("Gruppen und Kapazitäten verwalten")

    # Ensure the correct data types for the group management DataFrame
    if 'group_ages' not in st.session_state:
        st.session_state.group_ages = pd.DataFrame({
            'Group': ['Igel', 'Mäuse', 'Bären'],
            'Capacity': [5, 5, 5],
            'Min Age': [-5, -5, -5],
            'Max Age': [5, 5, 5]
        }).astype({'Group': 'object', 'Capacity': 'int', 'Min Age': 'int', 'Max Age': 'int'})

    # Create Ag-Grid options for the DataFrame
    gb = GridOptionsBuilder.from_dataframe(st.session_state.group_ages)
    gb.configure_default_column(editable=True)
    gb.configure_column("Group", editable=True)
    gb.configure_column("Capacity", editable=True, type=["numericColumn"], precision=0)
    gb.configure_column("Min Age", editable=True, type=["numericColumn"], precision=0)
    gb.configure_column("Max Age", editable=True, type=["numericColumn"], precision=0)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()

    # Display the Ag-Grid for managing groups
    response = AgGrid(
        st.session_state.group_ages,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        editable=True,
        height=300,
        reload_data=True
    )

    # Update the session state with the new data from the grid
    if response['data'] is not None:
        st.session_state.group_ages = pd.DataFrame(response['data'])

    # Delete selected groups if there are any selected rows
    selected_rows = response.get('selected_rows', None)  # Get selected rows or None if no selection
    if selected_rows is not None and len(selected_rows) > 0:  # Ensure selected_rows is not None and has content
        if st.button("Ausgewählte Gruppe(n) löschen"):
            selected_groups = [row['Group'] for row in selected_rows]
            st.session_state.group_ages = st.session_state.group_ages[~st.session_state.group_ages['Group'].isin(selected_groups)]
    
    # Add a new group via form with integer inputs
    st.subheader("Neue Gruppe hinzufügen")
    with st.form(key="new_group_form", clear_on_submit=True):
        new_group = st.text_input("Name der neuen Gruppe")
        new_capacity = st.number_input("Kapazität der neuen Gruppe", min_value=1, step=1, format='%d')  # Integer input
        new_min_age = st.number_input("Mindestalter der neuen Gruppe", min_value=-5, max_value=18, step=1, value=-5, format='%d')  # Integer input
        new_max_age = st.number_input("Höchstalter der neuen Gruppe", min_value=-5, max_value=18, step=1, value=5, format='%d')  # Integer input
        submit_new_group = st.form_submit_button("Neue Gruppe hinzufügen")

        if submit_new_group:
            if new_group in st.session_state.group_ages['Group'].values:
                st.warning(f"Gruppe '{new_group}' existiert bereits.")
            else:
                new_row = pd.DataFrame({
                    'Group': [new_group],
                    'Capacity': [new_capacity],
                    'Min Age': [new_min_age],
                    'Max Age': [new_max_age]
                }).astype({'Group': 'object', 'Capacity': 'int', 'Min Age': 'int', 'Max Age': 'int'})  # Ensure correct types
                st.session_state.group_ages = pd.concat([st.session_state.group_ages, new_row], ignore_index=True)

    st.subheader("Optimierungsparameter anpassen")

    # Adjust optimization parameters (all as integers)
    abs_diff_gender = st.slider("Absoluter Unterschied zwischen den Geschlechtern", min_value=0, max_value=10, value=5, step=1)  # Integer slider
    abs_diff_age = st.slider("Absoluter Unterschied im Alter", min_value=0, max_value=10, value=5, step=1)  # Integer slider
    penalty_mismatch_gender = st.slider("Strafgewicht für Geschlechterungleichgewicht", min_value=0, max_value=10, value=1, step=1)  # Integer slider
    penalty_mismatch_age = st.slider("Strafgewicht für Altersungleichgewicht", min_value=0, max_value=10, value=1, step=1)  # Integer slider

    # Save the updated optimization parameters in session state
    st.session_state.abs_diff_gender = abs_diff_gender
    st.session_state.abs_diff_age = abs_diff_age
    st.session_state.penalty_mismatch_gender = penalty_mismatch_gender
    st.session_state.penalty_mismatch_age = penalty_mismatch_age
