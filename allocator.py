
import pandas as pd
from collections import defaultdict

NAME_COL = "Select your name. MAKE SURE YOU CLICK YOU!"
GENDER_COL = "Gender"
CHOICE_COL = "Who would you like to share a room with. Choose up to 5. Boys can only choose boys & girls can only choose girls. "

def parse_choices(df_gender: pd.DataFrame):
    choices = {}
    for _, row in df_gender.iterrows():
        name = str(row[NAME_COL]).strip()
        raw = row.get(CHOICE_COL, "")
        lst = []
        if isinstance(raw, str) and raw.strip():
            lst = [x.strip() for x in raw.split(";") if x.strip()]
        choices[name] = lst
    return choices

def evaluate_status(choices, rooms):
    p2r = {}
    for i, r in enumerate(rooms):
        for m in r["members"]:
            p2r[m] = i
    rows = []
    for p, lst in choices.items():
        i = p2r.get(p, None)
        mates = set(rooms[i]["members"]) - {p} if i is not None else set()
        mutual = sum(1 for x in mates if (x in lst and p in choices.get(x, [])))
        one_way = sum(1 for x in mates if (x in lst and p not in choices.get(x, [])))
        status = "MUTUAL_OK" if mutual >= 1 else ("ONE_WAY_OK" if one_way >= 1 else "NO_MATCH")
        rows.append({"pupil": p, "room": i, "status": status})
    return pd.DataFrame(rows)

def seed_rooms_by_links(choices, capacities):
    unplaced = set(choices.keys())
    incoming = defaultdict(set)
    for a, lst in choices.items():
        for b in lst:
            if b in choices:
                incoming[b].add(a)
    rooms = [{"capacity": c, "members": []} for c in sorted(capacities, reverse=True)]
    order = sorted(unplaced, key=lambda p: (len(choices[p]) if choices[p] else 99, -len(incoming[p])))

    for p in order:
        if p not in unplaced:
            continue
        placed = False
        for r in rooms:
            if len(r["members"]) >= r["capacity"]:
                continue
            members = set(r["members"])
            if members & set(choices[p]) or members & incoming[p]:
                r["members"].append(p)
                unplaced.remove(p)
                for friend in choices[p]:
                    if friend in unplaced and len(r["members"]) < r["capacity"]:
                        r["members"].append(friend)
                        unplaced.remove(friend)
                placed = True
                break
        if not placed:
            for r in rooms:
                if len(r["members"]) == 0:
                    r["members"].append(p)
                    unplaced.remove(p)
                    for friend in choices[p]:
                        if friend in unplaced and len(r["members"]) < r["capacity"]:
                            r["members"].append(friend)
                            unplaced.remove(friend)
                    placed = True
                    break
        if not placed:
            for r in rooms:
                if len(r["members"]) < r["capacity"]:
                    r["members"].append(p)
                    unplaced.remove(p)
                    break
    for p in list(unplaced):
        for r in rooms:
            if len(r["members"]) < r["capacity"]:
                r["members"].append(p)
                unplaced.remove(p)
                break
    return rooms

def to_first_last(s: str) -> str:
    return f"{s.split(', ')[1]} {s.split(', ')[0]}" if ", " in s else s

def build_display_table(named_rooms):
    rows = []
    for r in named_rooms:
        mem = [to_first_last(x) for x in sorted(r["members"])]
        cap = r["Capacity"]
        while len(mem) < cap:
            mem.append("")
        rows.append({
            "Room Number": r["Room Number"],
            "Capacity": cap,
            "Gender": r["Gender"],
            "Pupil 1": mem[0] if cap>=1 else "",
            "Pupil 2": mem[1] if cap>=2 else "",
            "Pupil 3": mem[2] if cap>=3 else "",
            "Pupil 4": mem[3] if cap>=4 else "",
            "Filled": len(r["members"]),
            "Spare": cap - len(r["members"])
        })
    return pd.DataFrame(rows)

def assign_names_by_capacity(all_rooms, boys_alloc, girls_alloc):
    available = list(all_rooms)
    named = []
    for gender, alloc in (("Boys", boys_alloc), ("Girls", girls_alloc)):
        for r in alloc:
            cap = r["capacity"]
            idx = next(i for i,(nm,c) in enumerate(available) if c == cap)
            nm, c = available.pop(idx)
            named.append({"Room Number": nm, "Capacity": c, "Gender": gender, "members": r["members"]})
    return named

def split_capacities_auto(all_rooms, boys_n, girls_n):
    caps = sorted(all_rooms, key=lambda x: -x[1])
    boys_take, girls_take = [], []
    remaining_boys, remaining_girls = boys_n, girls_n
    for room, cap in caps:
        if remaining_boys >= remaining_girls:
            if remaining_boys > 0:
                boys_take.append((room, cap))
                remaining_boys -= cap
            else:
                girls_take.append((room, cap))
                remaining_girls -= cap
        else:
            if remaining_girls > 0:
                girls_take.append((room, cap))
                remaining_girls -= cap
            else:
                boys_take.append((room, cap))
                remaining_boys -= cap
    return boys_take, girls_take
