"""Reject ambiguous/missing local times instead of silently inventing UTC."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def parse_local(value, zone):
    try:
        naive = datetime.strptime(value, '%Y-%m-%dT%H:%M')
        tz = ZoneInfo(zone)
    except (ValueError, TypeError, ZoneInfoNotFoundError) as exc:
        raise ValueError('Enter a valid date, time, and IANA time zone.') from exc
    possibilities = set()
    for fold in (0, 1):
        aware = naive.replace(tzinfo=tz, fold=fold)
        utc = aware.astimezone(timezone.utc)
        if utc.astimezone(tz).replace(tzinfo=None) == naive:
            possibilities.add(int(utc.timestamp()))
    if len(possibilities) != 1:
        raise ValueError('This time is missing or repeated during a daylight-saving change. Choose an unambiguous time.')
    return possibilities.pop()

def display_time(timestamp, zone, lang='en'):
    dt = datetime.fromtimestamp(timestamp, ZoneInfo(zone))
    if lang in ('zh', 'ja'):
        return dt.strftime('%Y年%m月%d日 %H:%M') + ' (' + zone + ')'
    # ISO date order is unambiguous internationally.
    return dt.strftime('%Y-%m-%d %H:%M') + ' (' + zone + ')'
