import json
import os
from functools import lru_cache

SCRYFALL_SETS_PATH = os.path.join(os.path.dirname(__file__), '..', 'scryfall_sets.json')

@lru_cache(maxsize=1)
def load_set_map():
    """Load Scryfall set data and return mappings for name->code and code->name."""
    with open(SCRYFALL_SETS_PATH, 'r') as f:
        data = json.load(f)
    name_to_code = {}
    code_to_name = {}
    for s in data['data']:
        name = s['name'].strip().lower()
        code = s['code'].strip().lower()
        name_to_code[name] = code
        code_to_name[code] = name
    return name_to_code, code_to_name

def get_set_codes_for_name(set_name):
    """Return all possible codes for a set name (case-insensitive)."""
    name_to_code, _ = load_set_map()
    set_name = set_name.strip().lower()
    codes = []
    if set_name in name_to_code:
        codes.append(name_to_code[set_name])
    # Also try partial matches (e.g., 'torment' in 'torment tokens')
    for name, code in name_to_code.items():
        if set_name in name and code not in codes:
            codes.append(code)
    return codes

def get_set_names_for_code(set_code):
    """Return all possible names for a set code (case-insensitive)."""
    _, code_to_name = load_set_map()
    set_code = set_code.strip().lower()
    names = []
    if set_code in code_to_name:
        names.append(code_to_name[set_code])
    # Also try partial matches
    for code, name in code_to_name.items():
        if set_code in code and name not in names:
            names.append(name)
    return names

def get_all_set_identifiers(set_name):
    """Return all identifiers (name, code, abbreviations) for a set name."""
    set_name = set_name.strip().lower()
    codes = get_set_codes_for_name(set_name)
    identifiers = set([set_name] + codes)
    # Add all names for these codes
    for code in codes:
        identifiers.update(get_set_names_for_code(code))
    return list(identifiers) 