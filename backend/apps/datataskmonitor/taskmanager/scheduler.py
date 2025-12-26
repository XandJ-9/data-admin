from __future__ import annotations

import threading
import time
from datetime import timedelta

from django.utils import timezone


def _parse_cron_atom(atom: str, min_v: int, max_v: int) -> set[int]:
    atom = (atom or '').strip()
    if not atom:
        raise ValueError('empty atom')
    if atom == '*':
        return set(range(min_v, max_v + 1))

    step = 1
    if '/' in atom:
        left, right = atom.split('/', 1)
        left = left.strip()
        step = int(right.strip())
        atom = left or '*'
        if step <= 0:
            raise ValueError('invalid step')

    if atom == '*':
        return set(range(min_v, max_v + 1, step))

    if '-' in atom:
        a, b = atom.split('-', 1)
        start = int(a.strip())
        end = int(b.strip())
        if start > end:
            raise ValueError('invalid range')
        if start < min_v or end > max_v:
            raise ValueError('out of range')
        return set(range(start, end + 1, step))

    value = int(atom)
    if value < min_v or value > max_v:
        raise ValueError('out of range')
    return {value}


def _parse_cron_field(field: str, min_v: int, max_v: int, *, dow: bool = False) -> set[int]:
    field = (field or '').strip()
    if not field:
        raise ValueError('empty field')
    values: set[int] = set()
    for part in field.split(','):
        part = part.strip()
        if not part:
            continue
        part_values = _parse_cron_atom(part, min_v, max_v)
        values |= part_values
    if dow and 7 in values:
        values.add(0)
        values.discard(7)
    if not values:
        raise ValueError('empty values')
    return values


def calc_next_cron_time(cron_expr: str, base_time=None):
    base_time = base_time or timezone.now()
    cron_expr = (cron_expr or '').strip()
    parts = cron_expr.split()
    if len(parts) != 5:
        return None

    try:
        minutes = _parse_cron_field(parts[0], 0, 59)
        hours = _parse_cron_field(parts[1], 0, 23)
        dom = _parse_cron_field(parts[2], 1, 31)
        months = _parse_cron_field(parts[3], 1, 12)
        dows = _parse_cron_field(parts[4], 0, 7, dow=True)
    except Exception:
        return None

    candidate = base_time.astimezone(timezone.get_current_timezone()).replace(second=0, microsecond=0) + timedelta(minutes=1)
    max_iter = 60 * 24 * 366
    for _ in range(max_iter):
        cron_dow = (candidate.weekday() + 1) % 7
        if (
            candidate.minute in minutes
            and candidate.hour in hours
            and candidate.day in dom
            and candidate.month in months
            and cron_dow in dows
        ):
            return candidate
        candidate += timedelta(minutes=1)
    return None


def calc_next_run_time(schedule_type: str, schedule_conf: str, base_time=None):
    base_time = base_time or timezone.now()
    schedule_type = (schedule_type or '').strip()
    schedule_conf = (schedule_conf or '').strip()

    if schedule_type == 'once':
        return None
    if schedule_type == 'interval':
        try:
            seconds = int(schedule_conf)
        except Exception:
            return None
        if seconds <= 0:
            return None
        return base_time + timedelta(seconds=seconds)
    if schedule_type == 'cron':
        return calc_next_cron_time(schedule_conf, base_time=base_time)
    return None


class TaskScheduler:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _run_loop(self):
        while self.running:
            time.sleep(60)


