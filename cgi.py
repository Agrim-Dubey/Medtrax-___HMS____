def parse_header(line):
    """A minimal compatible replacement for cgi.parse_header"""
    parts = line.split(";")
    key = parts[0].strip().lower()
    pdict = {}
    for item in parts[1:]:
        if "=" in item:
            name, value = item.strip().split("=", 1)
            pdict[name.lower()] = value.strip('"')
    return key, pdict