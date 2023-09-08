from datetime import datetime, timedelta

def _set_dt_start_end(_start: datetime, duration_in_seconds: int, update_per_minute: bool, s: int, calculate_end: bool) -> tuple[datetime, datetime]:
    _dt_start: datetime
    _dt_end: datetime
    if not calculate_end:
        _dt_start = _start +timedelta(hours=s - _start.hour)
        if not update_per_minute:
            _dt_start = _dt_start.replace(minute=0)
        _dt_end = _dt_start + timedelta(seconds=duration_in_seconds)
    else:
        _dt_end = (_start +timedelta(hours=s - _start.hour) + timedelta(seconds=duration_in_seconds)).replace(minute=_start.minute * int(update_per_minute))
        _dt_start = _dt_end - timedelta(seconds=duration_in_seconds)
    return (_dt_start.strftime("%d %H:%M"), _dt_end.strftime("%d %H:%M"))



dur = 3900
start = datetime.now().replace(minute=10, second=0, microsecond=0)

print(f"start: {start.strftime('%d %H:%M')}")
for s in range(datetime.now().hour,23):
    print(f"upd_min, calc_end: {_set_dt_start_end(_start=start, duration_in_seconds=dur, update_per_minute=True, s=s, calculate_end=True)}")
    print(f"upd_min, calc_start: {_set_dt_start_end(_start=start, duration_in_seconds=dur, update_per_minute=True, s=s, calculate_end=False)}")
    print(f"upd_hour, calc_end: {_set_dt_start_end(_start=start, duration_in_seconds=dur, update_per_minute=False, s=s, calculate_end=True)}")
    print(f"upd_hour, calc_start: {_set_dt_start_end(_start=start, duration_in_seconds=dur, update_per_minute=False, s=s, calculate_end=False)}")
    print("")