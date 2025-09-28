
import io
import pandas as pd
import streamlit as st
from allocator import (
    NAME_COL, GENDER_COL, CHOICE_COL,
    parse_choices, optimise_allocation,
    build_display_table, assign_names_by_capacity, split_capacities_auto, evaluate_status
)

st.set_page_config(page_title="Room Allocator V3", layout="wide")

st.title("Residential Trip Room Allocator — V3")
st.caption("Optimised version: no singletons, stronger optimisation, summary included.")

col1, col2 = st.columns(2)
with col1:
    pupils_file = st.file_uploader("Upload pupils Excel (.xlsx)", type=["xlsx"])
    sheet = st.text_input("Sheet name", value="Sheet1")
with col2:
    rooms_file = st.file_uploader("Upload rooms CSV", type=["csv"])
    auto_split = st.checkbox("Auto-split room capacities between boys/girls", value=True)

manual_cols = st.columns(2)
with manual_cols[0]:
    boys_manual = st.text_input("Manual boys room sizes (comma-separated, optional)", value="")
with manual_cols[1]:
    girls_manual = st.text_input("Manual girls room sizes (comma-separated, optional)", value="")

run = st.button("Allocate")

if run:
    if pupils_file is None or rooms_file is None:
        st.error("Please upload both pupils Excel and rooms CSV.")
        st.stop()

    pupils_df = pd.read_excel(pupils_file, sheet_name=sheet)
    rooms_df = pd.read_csv(rooms_file, header=None)
    all_rooms = [(str(r[0]).strip(), int(r[1])) for _, r in rooms_df.iterrows()]

    boys_df = pupils_df[pupils_df[GENDER_COL] == "M"].copy()
    girls_df = pupils_df[pupils_df[GENDER_COL] == "F"].copy()
    boys_n, girls_n = len(boys_df), len(girls_df)
    boys_choices = parse_choices(boys_df)
    girls_choices = parse_choices(girls_df)

    if auto_split:
        boys_named_caps, girls_named_caps = split_capacities_auto(all_rooms, boys_n, girls_n)
        boys_caps = [cap for _, cap in boys_named_caps]
        girls_caps = [cap for _, cap in girls_named_caps]
    else:
        boys_caps = [int(x.strip()) for x in boys_manual.split(",") if x.strip()]
        girls_caps = [int(x.strip()) for x in girls_manual.split(",") if x.strip()]

    with st.spinner("Optimising allocation... please wait"):
        boys_rooms, boys_eval = optimise_allocation(boys_choices, boys_caps, n_iter=2000)
        girls_rooms, girls_eval = optimise_allocation(girls_choices, girls_caps, n_iter=2000)

    if boys_rooms is None or girls_rooms is None:
        st.error("⚠️ Allocation failed: A pupil would be left alone. Please adjust room capacities.")
        st.stop()

    named_rooms = assign_names_by_capacity(all_rooms, boys_rooms, girls_rooms)
    display_df = build_display_table(named_rooms)

    st.subheader("Final Allocation")
    st.dataframe(display_df, use_container_width=True)

    # Summary section
    st.subheader("Summary of Optimisation Results")
    pupils_total = len(pupils_df)
    singletons_boys = sum(1 for r in boys_rooms if len(r["members"])==1)
    singletons_girls = sum(1 for r in girls_rooms if len(r["members"])==1)
    no_match_boys = (boys_eval["status"]=="NO_MATCH").sum()
    no_match_girls = (girls_eval["status"]=="NO_MATCH").sum()
    mutual_total = (boys_eval["status"]=="MUTUAL_OK").sum() + (girls_eval["status"]=="MUTUAL_OK").sum()
    one_way_total = (boys_eval["status"]=="ONE_WAY_OK").sum() + (girls_eval["status"]=="ONE_WAY_OK").sum()
    no_match_total = no_match_boys + no_match_girls

    st.write(f"**Pupils:** {pupils_total}")
    st.write(f"**Singletons:** {singletons_boys + singletons_girls}")
    st.write(f"**Mutual matches:** {mutual_total}")
    st.write(f"**One-way matches:** {one_way_total}")
    st.write(f"**No matches:** {no_match_total}")

    # Download file with V3 in the name
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        display_df.to_excel(writer, index=False, sheet_name="Allocation")
    st.download_button("Download Excel (V3)", data=output.getvalue(), file_name="room_allocation_output_V3.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
