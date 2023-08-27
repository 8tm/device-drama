def simplify_size_string(size_str):
    parts = size_str.split(' ')
    value = float(parts[0])
    formatted_value = str(int(value)) if value == int(value) else f"{value:.2f}"
    return f"{formatted_value} {parts[1]}"


def format_size(size_bytes):
    b_size = 1024
    units = ('B', 'KB', 'MB', 'GB', 'TB')
    for unit in units:
        if size_bytes < b_size:
            raw_str = f"{size_bytes:.2f} {unit}"
            return simplify_size_string(raw_str)
        size_bytes /= b_size
