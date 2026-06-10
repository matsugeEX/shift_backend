from ortools.sat.python import cp_model

# =========================
# モデル
# =========================

model = cp_model.CpModel()


# =========================
# 共通関数
# =========================

def time_to_minutes(time_str):

    h, m = map(int,time_str.split(":"))

    return h * 60 + m


def get_break_minutes(work_minutes):

    if work_minutes < 240:
        return 0

    if work_minutes < 300:
        return 15

    if work_minutes < 390:
        return 30

    if work_minutes < 525:
        return 45

    if work_minutes < 660:
        return 60

    return 75


def generate_slots():

    slots = []

    current = 10 * 60
    end = 21 * 60

    while current < end:

        slots.append(current)

        current += 15

    return slots


def required_register_count(slot):

    if 11 * 60 <= slot < 11 * 60 + 30:
        return 2

    if 11 * 60 + 30 <= slot < 17 * 60:
        return 3

    if 17 * 60 <= slot < 19 * 60 + 30:
        return 2

    return 0


def required_leader_count(slot):

    if 11 * 60 <= slot < 21 * 60:
        return 1

    return 0


# =========================
# 従業員
# =========================

workers = [
    {"name": "田中", "start": "10:00", "end": "21:00", "leader": True},
    {"name": "佐藤", "start": "10:00", "end": "21:00", "leader": True},
    {"name": "鈴木", "start": "10:00", "end": "19:00", "leader": False},
    {"name": "高橋", "start": "10:00", "end": "18:00", "leader": False},
    {"name": "伊藤", "start": "11:00", "end": "20:00", "leader": False},
    {"name": "渡辺", "start": "11:00", "end": "21:00", "leader": False},
    {"name": "山本", "start": "12:00", "end": "21:00", "leader": False},
    {"name": "中村", "start": "12:00", "end": "18:00", "leader": False},
    {"name": "小林", "start": "13:00", "end": "21:00", "leader": False},
    {"name": "加藤", "start": "13:00", "end": "20:00", "leader": False},
    {"name": "吉田", "start": "14:00", "end": "21:00", "leader": False},
    {"name": "松本", "start": "15:00", "end": "21:00", "leader": False},
]


# =========================
# スロット
# =========================

slots = generate_slots()


# =========================
# タスク
# =========================

tasks = [
    "leader",
    "register",
    "break",
    "other",
]


# =========================
# 変数
# =========================

x = {}
break_start = {}


# =========================
# break開始位置
# =========================

for worker in workers:

    name = worker["name"]

    for slot in slots:

        break_start[name, slot] = (
            model.NewBoolVar(
                f"break_start_{name}_{slot}"
            )
        )


# =========================
# 勤務内容
# =========================

for worker in workers:

    name = worker["name"]

    for slot in slots:

        for task in tasks:

            x[name, slot, task] = (
                model.NewBoolVar(
                    f"{name}_{slot}_{task}"
                )
            )


# =========================
# 勤務時間制約
# =========================

for worker in workers:

    name = worker["name"]

    start = time_to_minutes(
        worker["start"]
    )

    end = time_to_minutes(
        worker["end"]
    )

    for slot in slots:

        if start <= slot < end:

            model.Add(

                sum(
                    x[name, slot, task]
                    for task in tasks
                )

                == 1
            )

        else:

            for task in tasks:

                model.Add(
                    x[name, slot, task]
                    == 0
                )


# =========================
# リーダー資格制約
# =========================

for worker in workers:

    if not worker["leader"]:

        name = worker["name"]

        for slot in slots:

            model.Add(
                x[name, slot, "leader"]
                == 0
            )


# =========================
# リーダー人数
# =========================

for slot in slots:

    if required_leader_count(slot):

        model.Add(

            sum(

                x[
                    worker["name"],
                    slot,
                    "leader"
                ]

                for worker in workers
                if worker["leader"]

            )

            == 1
        )


# =========================
# レジ人数
# =========================

for slot in slots:

    required = required_register_count(slot)

    model.Add(
        sum(
            x[
                worker["name"],
                slot,
                "register"
            ]
            for worker in workers
        )
        == required
    )

is_register = {}

for worker in workers:

    name = worker["name"]

    for slot in slots:

        is_register[name, slot] = (
            model.NewBoolVar(
                f"is_register_{name}_{slot}"
            )
        )

        model.Add(
            is_register[name, slot]
            ==
            x[name, slot, "register"]
        )

register_start = {}

for worker in workers:

    name = worker["name"]

    for slot in slots:

        register_start[name, slot] = model.NewBoolVar(
            f"register_start_{name}_{slot}"
        )

for worker in workers:

    name = worker["name"]

    first_slot = slots[0]

    model.Add(
        register_start[name, first_slot]
        ==
        is_register[name, first_slot]
    )

    for i in range(1, len(slots)):

        current = slots[i]
        prev = slots[i - 1]

        model.Add(
            register_start[name, current]
            >=
            is_register[name, current] - is_register[name, prev]
        )

        model.Add(
            register_start[name, current]
            <=
            is_register[name, current]
        )

        model.Add(
            register_start[name, current]
            <=
            1 - is_register[name, prev]
        )

for worker in workers:

    name = worker["name"]

    for i in range(len(slots) - 3):

        start_slot = slots[i]

        model.Add(
            sum(
                is_register[name, slots[j]]
                for j in range(i, i + 4)
            )
            >=
            4 * register_start[name, start_slot]
        )

register_end = {}

for worker in workers:

    name = worker["name"]

    for slot in slots:

        register_end[name, slot] = model.NewBoolVar(
            f"register_end_{name}_{slot}"
        )

for worker in workers:

    name = worker["name"]

    last_slot = slots[-1]

    model.Add(
        register_end[name, last_slot]
        ==
        is_register[name, last_slot]
    )

    for i in range(len(slots) - 1):

        current = slots[i]
        next_slot = slots[i + 1]

        model.Add(
            register_end[name, current]
            >=
            is_register[name, current] - is_register[name, next_slot]
        )

        model.Add(
            register_end[name, current]
            <=
            is_register[name, current]
        )

        model.Add(
            register_end[name, current]
            <=
            1 - is_register[name, next_slot]
        )

for worker in workers:

    name = worker["name"]

    for i in range(len(slots) - 4):

        end_slot = slots[i]

        for j in range(i + 1, i + 5):

            model.Add(
                is_register[name, slots[j]]
                <=
                1 - register_end[name, end_slot]
            )
# =========================
# 休憩制約
# =========================

for worker in workers:

    name = worker["name"]

    start_time = time_to_minutes(
        worker["start"]
    )

    end_time = time_to_minutes(
        worker["end"]
    )

    work_minutes = (
        end_time
        - start_time
    )

    break_slots_needed = (
        get_break_minutes(
            work_minutes
        )
        // 15
    )

    if break_slots_needed == 0:

        for slot in slots:

            model.Add(
                x[name, slot, "break"]
                == 0
            )

            model.Add(
                break_start[name, slot]
                == 0
            )

        continue

    valid_starts = []

    for slot in slots:

        end_of_break = (
            slot
            + break_slots_needed * 15
        )

        if slot < start_time + 120:
            continue

        if slot > end_time - 120:
            continue

        if end_of_break > 18 * 60 + 30:
            continue

        valid_starts.append(slot)

    model.Add(

        sum(
            break_start[name, slot]
            for slot in valid_starts
        )

        == 1
    )

    for slot in slots:

        covering_starts = []

        for start_slot in valid_starts:

            if (
                start_slot
                <= slot
                <
                start_slot
                + break_slots_needed * 15
            ):

                covering_starts.append(
                    break_start[
                        name,
                        start_slot
                    ]
                )

        if covering_starts:

            model.Add(

                x[
                    name,
                    slot,
                    "break"
                ]

                == sum(
                    covering_starts
                )
            )

        else:

            model.Add(
                x[
                    name,
                    slot,
                    "break"
                ]
                == 0
            )


# =========================
# 18:30以降休憩禁止
# =========================

for worker in workers:

    name = worker["name"]

    for slot in slots:

        if slot >= 18 * 60 + 30:

            model.Add(
                x[
                    name,
                    slot,
                    "break"
                ]
                == 0
            )

# =========================
# レジ連続90分制限
# =========================

for worker in workers:

    name = worker["name"]

    for i in range(len(slots) - 6):

        seven_slots = slots[i:i+7]

        model.Add(
            sum(
                x[name, slot, "register"]
                for slot in seven_slots
            )
            <= 6
        )

is_leader = {}

for worker in workers:

    name = worker["name"]

    for slot in slots:

        is_leader[name, slot] = (
            model.NewBoolVar(
                f"is_leader_{name}_{slot}"
            )
        )

        model.Add(
            is_leader[name, slot]
            ==
            x[name, slot, "leader"]
        )

leader_start = {}

for worker in workers:

    if not worker["leader"]:
        continue

    name = worker["name"]

    for slot in slots:

        leader_start[name, slot] = (
            model.NewBoolVar(
                f"leader_start_{name}_{slot}"
            )
        )

for worker in workers:

    if not worker["leader"]:
        continue

    name = worker["name"]

    first_slot = slots[0]

    model.Add(
        leader_start[name, first_slot]
        ==
        is_leader[name, first_slot]
    )

    for i in range(1, len(slots)):

        current = slots[i]
        prev = slots[i - 1]

        model.Add(
            leader_start[name, current]
            >=
            is_leader[name, current]
            - is_leader[name, prev]
        )

        model.Add(
            leader_start[name, current]
            <=
            is_leader[name, current]
        )

        model.Add(
            leader_start[name, current]
            <=
            1 - is_leader[name, prev]
        )

for worker in workers:

    if not worker["leader"]:
        continue

    name = worker["name"]

    for i in range(len(slots) - 3):

        start_slot = slots[i]

        model.Add(

            sum(
                is_leader[name, slots[j]]
                for j in range(i, i + 4)
            )

            >=

            4 * leader_start[name, start_slot]

        )

for worker in workers:

    if not worker["leader"]:
        continue

    name = worker["name"]

    for i in range(len(slots)-3, len(slots)):

        model.Add(
            leader_start[name, slots[i]]
            == 0
        )

# =========================
# リーダー連続3時間制限
# =========================

for worker in workers:

    if not worker["leader"]:
        continue

    name = worker["name"]

    for i in range(len(slots) - 12):

        thirteen_slots = slots[i:i+13]

        model.Add(

            sum(

                is_leader[
                    name,
                    slot
                ]

                for slot in thirteen_slots

            )

            <= 12

        )

leader_minutes = {}

for worker in workers:

    if worker["leader"]:

        name = worker["name"]

        leader_minutes[name] = model.NewIntVar(
            0,
            len(slots) * 15,
            f"leader_minutes_{name}"
        )

        model.Add(

            leader_minutes[name]

            ==

            sum(
                x[name, slot, "leader"]
                for slot in slots
            ) * 15
        )

leader_max = model.NewIntVar(
    0,
    len(slots) * 15,
    "leader_max"
)

leader_min = model.NewIntVar(
    0,
    len(slots) * 15,
    "leader_min"
)

model.AddMaxEquality(
    leader_max,
    list(leader_minutes.values())
)

model.AddMinEquality(
    leader_min,
    list(leader_minutes.values())
)

leader_gap = model.NewIntVar(
    0,
    len(slots) * 15,
    "leader_gap"
)

model.Add(
    leader_gap
    ==
    leader_max - leader_min
)

# =========================
# 仮目的関数
# =========================

model.Minimize(
    leader_gap
)


# =========================
# 求解
# =========================

solver = cp_model.CpSolver()

status = solver.Solve(model)

print(
    "status =",
    solver.StatusName(status)
)

def print_worker_schedule():

    for worker in workers:

        name = worker["name"]

        schedule = []

        for slot in slots:

            symbol = "-"

            if solver.Value(
                x[name, slot, "leader"]
            ):
                symbol = "L"

            elif solver.Value(
                x[name, slot, "register"]
            ):
                symbol = "R"

            elif solver.Value(
                x[name, slot, "break"]
            ):
                symbol = "#"

            elif solver.Value(
                x[name, slot, "other"]
            ):
                symbol = "o"

            schedule.append(symbol)

        print(
            f"{name} [{','.join(schedule)}]"
        )

if status == cp_model.OPTIMAL:

    print_worker_schedule()