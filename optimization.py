import streamlit as st
from optimize import optimize_group_assignment, calculate_age
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

def plot_group_distribution(group_name, df, new_members_df, col):
    """Plot an improved age and gender distribution of members in a given group using Plotly."""

    # Separate new and existing members
    existing_members = df[(df['Gruppe'] == group_name) & (df['Gruppe'].notnull())]
    new_members = new_members_df[(new_members_df['Gruppe'] == group_name) & (df['Gruppe'].isnull())]

    # Filter existing and new members by gender
    existing_male = existing_members[existing_members['Geschlecht'] == 'männlich']
    existing_female = existing_members[existing_members['Geschlecht'] == 'weiblich']
    new_male = new_members[new_members['Geschlecht'] == 'männlich']
    new_female = new_members[new_members['Geschlecht'] == 'weiblich']

    # Count members by age
    existing_male_counts = existing_male['Age'].value_counts().sort_index()
    existing_female_counts = existing_female['Age'].value_counts().sort_index()
    new_male_counts = new_male['Age'].value_counts().sort_index()
    new_female_counts = new_female['Age'].value_counts().sort_index()

    # Collect unique ages for y-axis labels
    all_ages = sorted(set(existing_male_counts.index)
                      .union(existing_female_counts.index)
                      .union(new_male_counts.index)
                      .union(new_female_counts.index))

    # Initialize Plotly figure
    fig = go.Figure()

    # Add bar for existing males (negative values)
    fig.add_trace(go.Bar(
        y=existing_male_counts.index, 
        x=-existing_male_counts.values, 
        orientation='h',
        name='Bestehende Männer',
        marker=dict(color='steelblue'),
        hoverinfo='x+y'
    ))

    # Add bar for new males (negative values stacked on existing males)
    fig.add_trace(go.Bar(
        y=new_male_counts.index, 
        x=-new_male_counts.values, 
        orientation='h',
        name='Neue Männer',
        marker=dict(color='lightblue'),
        hoverinfo='x+y'
    ))

    # Add bar for existing females (positive values)
    fig.add_trace(go.Bar(
        y=existing_female_counts.index, 
        x=existing_female_counts.values, 
        orientation='h',
        name='Bestehende Frauen',
        marker=dict(color='orange'),
        hoverinfo='x+y'
    ))

    # Add bar for new females (positive values stacked on existing females)
    fig.add_trace(go.Bar(
        y=new_female_counts.index, 
        x=new_female_counts.values, 
        orientation='h',
        name='Neue Frauen',
        marker=dict(color='peachpuff'),
        hoverinfo='x+y'
    ))

    # Customize layout to only show y-axis labels for ages with members
    fig.update_layout(
        title=f'Alters- und Geschlechterverteilung in der Gruppe: {group_name}',
        xaxis=dict(
            title='Anzahl der Mitglieder',
            showgrid=False,
            zeroline=True,
            tickformat=',d',  # Ensure integers
        ),
        yaxis=dict(
            title='Alter',
            showgrid=False,
            zeroline=False,
            tickvals=all_ages,  # Only show ages where members exist
            ticktext=[str(age) for age in all_ages]  # Convert ages to strings for labeling
        ),
        barmode='relative',  # Stacks the bars for new and existing members
        bargap=0.2,
        bargroupgap=0.1,
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)'  # Transparent background
    )

    # Show the figure in the Streamlit app
    col.plotly_chart(fig, use_container_width=True)


# Function to create a downloadable Excel file
def to_excel(df):
    """Convert a DataFrame to an Excel file and return it as a downloadable byte stream."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Optimierungsergebnisse')
    return output.getvalue()

def optimization_page():
    """Main optimization page for file upload, optimization configuration, and result display."""
    st.title("Optimierung der Platzvergabe")

    # File upload for optimization input (Excel format)
    uploaded_file = st.file_uploader("Laden Sie Ihre Excel-Datei hoch", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        # Calculate age if the 'Geburtsdatum' column exists
        if 'Geburtsdatum' in df.columns:
            df['Age'] = df['Geburtsdatum'].apply(calculate_age)

        st.write("Datenvorschau der hochgeladenen Daten:")
        st.write(df.head())

        st.subheader("Ergebnisse der Optimierung")

        # Retrieve groups and capacities from session state (set in the Einstellungen page)
        if 'group_ages' not in st.session_state:
            st.error("Keine Gruppen gefunden. Bitte fügen Sie Gruppen auf der Seite 'Einstellungen' hinzu.")
            return

        group_ages = st.session_state.group_ages
        groups = dict(zip(group_ages['Group'], group_ages['Capacity']))

        # Split the screen into two parts for pre-optimization slider settings
        col1, col2 = st.columns(2)

        # Left side sliders for optimization
        with col1:
            point_weight_left = st.slider("Gewichtung für Punkte-Optimierung (Links)", min_value=0, max_value=10, value=1)
            age_dist_weight_left = st.slider("Gewichtung für Altersverteilung (Links)", min_value=0, max_value=10, value=0)
            gender_dist_weight_left = st.slider("Gewichtung für Geschlechterverteilung (Links)", min_value=0, max_value=10, value=0)
            age_consistency_weight_left = st.slider("Gewichtung für Alterskonsistenz zwischen den Gruppen (Links)", min_value=0, max_value=10, value=0)

        # Right side sliders for optimization
        with col2:
            point_weight_right = st.slider("Gewichtung für Punkte-Optimierung (Rechts)", min_value=0, max_value=10, value=5)
            age_dist_weight_right = st.slider("Gewichtung für Altersverteilung (Rechts)", min_value=0, max_value=10, value=5)
            gender_dist_weight_right = st.slider("Gewichtung für Geschlechterverteilung (Rechts)", min_value=0, max_value=10, value=5)
            age_consistency_weight_right = st.slider("Gewichtung für Alterskonsistenz zwischen den Gruppen (Rechts)", min_value=0, max_value=10, value=5)

        # Left optimization results
        col1.subheader("Linke Optimierungsergebnisse")
        display_optimization_results(df, groups, point_weight_left, age_dist_weight_left, gender_dist_weight_left, age_consistency_weight_left, col1, "links")

        # Right optimization results
        col2.subheader("Rechte Optimierungsergebnisse")
        display_optimization_results(df, groups, point_weight_right, age_dist_weight_right, gender_dist_weight_right, age_consistency_weight_right, col2, "rechts")


def display_optimization_results(df, groups, points_weight, age_dist_weight, gender_dist_weight, age_consistency_weight, col, key_prefix):
    """
    Perform optimization based on the provided parameters and display results in a specified column, 
    including download links and plots.
    """
    optimized_df = optimize_group_assignment(
        df, groups, points_weight, age_dist_weight, gender_dist_weight, age_consistency_weight
    )
    total_points = optimized_df["Gesamtpunkte"].sum()

    # Display total points in bold green
    col.markdown(f"### Gesamtpunktzahl für alle ausgewählten Bewerber: **<span style='color:green;'>{total_points}</span>**", unsafe_allow_html=True)

    # Filter and display relevant columns
    df_filtered = optimized_df[["Vorname", "Nachname", "Age", "Gesamtpunkte", "Gruppe", "Geschlecht"]]
    col.write(df_filtered)

    # Provide download button for optimization results with unique keys
    df_xlsx = to_excel(df_filtered)
    col.download_button(label=f'📥 Download Optimierte Daten ({key_prefix})', data=df_xlsx, file_name=f'{key_prefix}_optimierte_daten.xlsx', key=f'download_{key_prefix}')

    # Plot graphs for each group
    if not df_filtered.empty:
        for group in sorted(df_filtered['Gruppe'].unique()):
            col.markdown(f"#### Gruppe: {group}")
            plot_group_distribution(group, df, df_filtered, col)
    else:
        col.write("Keine Daten für die Optimierung nach der Filterung verfügbar.")
