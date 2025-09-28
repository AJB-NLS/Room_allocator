
# Room Allocator V3

Current Version: V3

## What's New
- Enforces no singletons (no pupil left alone in a room)
- Stronger optimisation (tries many random restarts)
- Shows summary of results (mutual, one-way, no match, singletons)
- Spinner while optimising
- Warning banner if impossible
- Excel file exported as `room_allocation_output_V3.xlsx`

## How to Use
1. Prepare two files:
   - **Pupils Excel** (use the template `pupils_choices_template.xlsx`)
   - **Rooms CSV** (use the template `rooms_list_template.csv`)

2. Upload both files on the website.

3. Click **Allocate**.

4. Download the final Excel table of room allocations.

### Rules applied
- Boys and girls are placed in separate rooms.
- Every pupil will be placed with at least one of their chosen friends where possible.
- No one is left in a room alone.
- If it is not possible to satisfy all rules, the app will display a warning and ask you to adjust room capacities.
