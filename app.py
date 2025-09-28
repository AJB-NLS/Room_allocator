
import io
import pandas as pd
import streamlit as st
from allocator import (
    NAME_COL, GENDER_COL, CHOICE_COL,
    parse_choices, evaluate_status, seed_rooms_by_links,
    build_display_table, assign_names_by_capacity, split_capacities_auto
)

st.set_page_config(page_title="Room Allocator", layout="wide")

st.title("Residential Trip Room Allocator")
st.caption("Upload pupils + rooms, then click Allocate. Everyone gets at least one chosen friend; mutuals maximised.")

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

    try:
        pupils_df = pd.read_excel(pupils_file, sheet_name=sheet)
    except Exception as e:
        st.error(f"Could not read the pupils Excel: {e}")
        st.stop()
    try:
        rooms_df = pd.read_csv(rooms_file, header=None)
        all_rooms = [(str(r[0]).strip(), int(r[1])) for _, r in rooms_df.iterrows()]
    except Exception as e:
        st.error(f"Could not read the rooms CSV: {e}")
        st.stop()

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

    boys_rooms = seed_rooms_by_links(boys_choices, boys_caps)
    girls_rooms = seed_rooms_by_links(girls_choices, girls_caps)

    named_rooms = assign_names_by_capacity(all_rooms, boys_rooms, girls_rooms)
    display_df = build_display_table(named_rooms)

    st.subheader("Final Allocation")
    st.dataframe(display_df, use_container_width=True)

    boys_eval = evaluate_status(boys_choices, boys_rooms)
    girls_eval = evaluate_status(girls_choices, girls_rooms)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Boys — Mutual", int((boys_eval["status"]=="MUTUAL_OK").sum()))
        st.metric("Boys — One-way", int((boys_eval["status"]=="ONE_WAY_OK").sum()))
        st.metric("Boys — No match", int((boys_eval["status"]=="NO_MATCH").sum()))
    with c2:
        st.metric("Girls — Mutual", int((girls_eval["status"]=="MUTUAL_OK").sum()))
        st.metric("Girls — One-way", int((girls_eval["status"]=="ONE_WAY_OK").sum()))
        st.metric("Girls — No match", int((girls_eval["status"]=="NO_MATCH").sum()))

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        display_df.to_excel(writer, index=False, sheet_name="Allocation")
    st.download_button("Download Excel", data=output.getvalue(), file_name="room_allocation_output.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
