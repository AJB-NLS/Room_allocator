
import io
import pandas as pd
import streamlit as st
from allocator import (
    NAME_COL, GENDER_COL, CHOICE_COL,
    parse_choices, evaluate_status, strict_allocation, fallback_allocation,
    build_display_table, assign_names_by_capacity, split_capacities_auto
)

st.set_page_config(page_title="Room Allocator", layout="wide")

st.title("Residential Trip Room Allocator")
st.caption("Upload pupils + rooms, then click Allocate. Tries strict rules first; falls back with a warning if not possible.")

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

    # Try strict boys/girls allocation
    boys_rooms, boys_eval = strict_allocation(boys_choices, boys_caps)
    girls_rooms, girls_eval = strict_allocation(girls_choices, girls_caps)

    warning = False
    if boys_rooms is None:
        boys_rooms, boys_eval = fallback_allocation(boys_choices, boys_caps)
        warning = True
    if girls_rooms is None:
        girls_rooms, girls_eval = fallback_allocation(girls_choices, girls_caps)
        warning = True

    named_rooms = assign_names_by_capacity(all_rooms, boys_rooms, girls_rooms)
    display_df = build_display_table(named_rooms)

    if warning:
        st.warning("⚠️ It was not possible to satisfy every pupil’s choices. Below is the closest match, minimising pupils without a friend.")

    st.subheader("Final Allocation")
    st.dataframe(display_df, use_container_width=True)

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
