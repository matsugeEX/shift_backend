def time_to_minutes(time_str):
    h, m = map(int, time_str.split(":"))
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

    # 11:00-11:30
    if 11 * 60 <= slot < 11 * 60 + 30:
        return 2

    # 11:30-17:00
    if 11 * 60 + 30 <= slot < 17 * 60:
        return 3

    # 17:00-19:30
    if 17 * 60 <= slot < 19 * 60 + 30:
        return 2

    return 0


def required_leader_count(slot):

    if 11 * 60 <= slot < 21 * 60:
        return 1

    return 0


def is_working(worker, slot):

    start = time_to_minutes(worker["start"])
    end = time_to_minutes(worker["end"])

    return start <= slot < end


def is_on_break(name, slot, worker_breaks):

    return slot in worker_breaks[name]


def select_leader(
    workers,
    slot,
    leader_total_minutes,
    worker_breaks,
):

    candidates = []

    for worker in workers:

        if not worker["leader"]:
            continue

        if not is_working(worker, slot):
            continue

        if is_on_break(
            worker["name"],
            slot,
            worker_breaks,
        ):
            continue

        candidates.append(worker["name"])

    if not candidates:
        return None

    candidates.sort(
        key=lambda name: leader_total_minutes[name]
    )

    return candidates[0]

def can_take_break(
    worker,
    break_start,
    break_minutes,
    workers,
    worker_breaks,
    break_usage,
):

    current = break_start

    while current < break_start + break_minutes:

        #
        # 第一段階
        # 同時休憩人数制限
        #
        if break_usage.get(current, 0) >= 4:
            return False

        #
        # 第二段階
        # 必要人数確保
        #
        working_count = 0

        for w in workers:

            if not is_working(w, current):
                continue

            if current in worker_breaks.get(
                w["name"],
                []
            ):
                continue

            working_count += 1

        required_count = (
            required_register_count(current)
            + required_leader_count(current)
        )

        #
        # 今からこの人を休憩に入れる
        #
        if working_count - 1 < required_count:
            return False

        #
        # 第三段階
        # 責任者候補確保
        #
        leader_available = False

        for w in workers:

            if not w["leader"]:
                continue

            if w["name"] == worker["name"]:
                continue

            if not is_working(w, current):
                continue

            if current in worker_breaks.get(
                w["name"],
                []
            ):
                continue

            leader_available = True
            break

        if not leader_available:
            return False

        current += 15

    return True

def reserve_break(
    break_start,
    break_minutes,
    break_usage,
):

    current = break_start

    while current < break_start + break_minutes:

        break_usage[current] = (
            break_usage.get(current, 0)
            + 1
        )

        current += 15

def allocate(workers):

    slots = generate_slots()

    #
    # 休憩
    #
    worker_breaks = {}

    break_usage = {}

    for worker in workers:

        start = time_to_minutes(worker["start"])
        end = time_to_minutes(worker["end"])

        work_minutes = end - start

        break_minutes = get_break_minutes(
            work_minutes
        )

        if break_minutes == 0:

            worker_breaks[
                worker["name"]
            ] = []

            continue

        preferred_start = (
            start + int(work_minutes * 0.6)
        )

        preferred_start = (
            preferred_start // 15
        ) * 15

        #
        # 休憩開始可能範囲
        #
        earliest_break = start + 180

        latest_return = 18 * 60 + 30

        latest_break = min(
            end - break_minutes,
            latest_return - break_minutes,
        )

        #
        # 希望位置が範囲外なら補正
        #
        preferred_start = min(
            preferred_start,
            latest_break,
        )

        preferred_start = max(
            preferred_start,
            earliest_break,
        )

        break_start = None

        candidate = preferred_start

        while candidate >= earliest_break:

            if can_take_break(
                worker,
                candidate,
                break_minutes,
                workers,
                worker_breaks,
                break_usage,
            ):

                break_start = candidate
                break

            candidate -= 15

        #
        # 見つからない場合
        #
        if break_start is None:

            worker_breaks[
                worker["name"]
            ] = []

            continue

        break_slots = []

        current = break_start

        while current < break_start + break_minutes:

            break_slots.append(current)

            current += 15

        worker_breaks[
            worker["name"]
        ] = break_slots

        reserve_break(
            break_start,
            break_minutes,
            break_usage,
        )

    #
    # レジ管理
    #
    register_minutes = {
        worker["name"]: 0
        for worker in workers
    }

    total_register_minutes = {
        worker["name"]: 0
        for worker in workers
    }

    #
    # 責任者管理
    #
    leader_total_minutes = {
        worker["name"]: 0
        for worker in workers
        if worker["leader"]
    }

    current_leader = None
    next_leader_change = 11 * 60

    result = {}

    for slot in slots:

        result[slot] = {
            "leader": [],
            "register": [],
            "break": [],
        }

        #
        # 休憩者
        #
        for worker in workers:

            if is_on_break(
                worker["name"],
                slot,
                worker_breaks,
            ):
                result[slot]["break"].append(
                    worker["name"]
                )

        #
        # 責任者
        #
        if required_leader_count(slot):

            if slot >= next_leader_change:

                current_leader = select_leader(
                    workers,
                    slot,
                    leader_total_minutes,
                    worker_breaks,
                )

                next_leader_change = (
                    slot + 180
                )

            if current_leader:

                result[slot]["leader"] = [
                    current_leader
                ]

                leader_total_minutes[
                    current_leader
                ] += 15

        #
        # レジ
        #
        register_needed = (
            required_register_count(
                slot
            )
        )

        register_candidates = []

        for worker in workers:

            name = worker["name"]

            if not is_working(
                worker,
                slot,
            ):
                continue

            if is_on_break(
                name,
                slot,
                worker_breaks,
            ):
                continue

            if (
                name
                in result[slot]["leader"]
            ):
                continue

            if (
                register_minutes[name]
                < 90
            ):
                register_candidates.append(
                    name
                )

        #
        # 人数不足時は90分制限解除
        #
        if (
            len(register_candidates)
            < register_needed
        ):

            for worker in workers:

                name = worker["name"]

                if not is_working(
                    worker,
                    slot,
                ):
                    continue

                if is_on_break(
                    name,
                    slot,
                    worker_breaks,
                ):
                    continue

                if (
                    name
                    in result[slot]["leader"]
                ):
                    continue

                if (
                    name
                    not in register_candidates
                ):
                    register_candidates.append(
                        name
                    )

        #
        # 公平性
        #
        register_candidates.sort(
            key=lambda name: (
                register_minutes[name],
                total_register_minutes[name],
            )
        )

        selected_register = (
            register_candidates[
                :register_needed
            ]
        )

        result[slot]["register"] = (
            selected_register
        )

        #
        # レジ時間更新
        #
        for worker in workers:

            name = worker["name"]

            if (
                name
                in selected_register
            ):

                register_minutes[
                    name
                ] += 15

                total_register_minutes[
                    name
                ] += 15

            else:

                register_minutes[
                    name
                ] = 0

    return (
        result,
        total_register_minutes,
        leader_total_minutes,
        worker_breaks,
    )

def reserve_break(
    break_start,
    break_minutes,
    break_usage,
):

    current = break_start

    while current < break_start + break_minutes:

        break_usage[current] = (
            break_usage.get(current, 0)
            + 1
        )

        current += 15


def print_schedule(result):

    for slot, info in result.items():

        hour = slot // 60
        minute = slot % 60

        print(
            f"{hour:02}:{minute:02}",
            f"Leader={info['leader']}",
            f"Register={info['register']}",
            f"Break={info['break']}",
        )


def build_worker_schedule(
    workers,
    result,
):

    worker_schedule = {
        worker["name"]: []
        for worker in workers
    }

    for slot in sorted(result.keys()):

        info = result[slot]

        for worker in workers:

            name = worker["name"]

            symbol = "."

            if name in info["break"]:
                symbol = "#"

            elif name in info["leader"]:
                symbol = "L"

            elif name in info["register"]:

                index = (
                    info["register"].index(name)
                    + 1
                )

                symbol = str(index)

            worker_schedule[name].append(
                symbol
            )

    return worker_schedule


def print_worker_schedule(worker_schedule, result):

    slots = sorted(result.keys())

    print()

    print("       ", end="")
    for slot in slots:
        if slot % 60 == 0:
            print(f"{slot//60:02}", end="")
        else:
            print("  ", end="")
    print()

    print("       ", end="")
    for slot in slots:
        if slot % 60 == 0:
            print("00", end="")
        else:
            print("  ", end="")
    print()

    for name, schedule in worker_schedule.items():

        line = ""

        for symbol in schedule:
            line += symbol + " "

        print(f"{name:6} {line}")

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

result, register_stats, leader_stats, worker_breaks = allocate(workers)

worker_schedule = build_worker_schedule(
    workers,
    result,
)
for slot, info in result.items():

    if info["break"]:

        h = slot // 60
        m = slot % 60

        print(
            f"{h:02}:{m:02}",
            info["break"]
        )

def print_worker_schedule_compact(
    worker_schedule
):

    print()

    for name, schedule in (
        worker_schedule.items()
    ):

        print(
            f"{name} [{','.join(schedule)}]"
        )
print_worker_schedule_compact(worker_schedule)
for name, breaks in worker_breaks.items():
    print(name, len(breaks))