import random
from .config import YinpaConfig as cfg

def num_limit_absolute(num, limit_min_value):
    is_positive = num > 0
    if abs(num) < limit_min_value:
        return limit_min_value if is_positive else -limit_min_value
    return num

def chest_size_to_cup(size: float):
    if size < 10:
        return "None"
    if size < 12:
        return "AA"
    ret_value = ord('A') + int((size - 10) / 2) - 1
    if ret_value > ord('Z'):
        return f"Z+{ret_value - ord('Z')}"
    return chr(ret_value)

def sensitive_to_volume(sensitive: int, use_time: float):
    if (sensitive <= 150) or (use_time <= cfg.min_persistance):
        return 0.0
    total_sensitive = int(sensitive)
    calc_sensitive = 0
    for_count = 1
    while True:
        for_count += 1
        if for_count <= 2:
            continue
        if total_sensitive >= cfg.sensitive_calc_demarcation:
            total_sensitive -= cfg.sensitive_calc_demarcation
            calc_sensitive += int(cfg.sensitive_calc_demarcation / for_count)
        else:
            calc_sensitive += int(total_sensitive / for_count)
            break
    base_value = (calc_sensitive + use_time / 16) / 16
    return random.randint(int(base_value / 2 * 100), int(base_value * 2 * 100)) / 100
