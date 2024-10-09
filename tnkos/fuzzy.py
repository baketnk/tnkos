import re
import unicodedata

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def normalize_rune(r):
    return unicodedata.normalize('NFKD', r)[0]

def char_class_of(char):
    if char.islower():
        return 'charLower'
    elif char.isupper():
        return 'charUpper'
    elif char.isdigit():
        return 'charNumber'
    elif char.isspace():
        return 'charWhite'
    elif char in '/,:;|':
        return 'charDelimiter'
    else:
        return 'charNonWord'

def bonus_for(prev_class, charclass):
    if charclass > 'charNonWord':
        if prev_class == 'charWhite':
            return 10
        elif prev_class == 'charDelimiter':
            return 9
        elif prev_class == 'charNonWord':
            return 8
    if (prev_class == 'charLower' and charclass == 'charUpper') or (prev_class != 'charNumber' and charclass == 'charNumber'):
        return 7
    if charclass in ['charNonWord', 'charDelimiter']:
        return 6
    elif charclass == 'charWhite':
        return 10
    return 0

def bonus_at(input, idx):
    if idx == 0:
        return 10
    return bonus_for(char_class_of(input[idx - 1]), char_class_of(input[idx]))

def ascii_fuzzy_index(input, pattern, case_sensitive):
    if not is_ascii(pattern):
        return -1, -1
    idx = 0
    first_idx = 0
    last_idx = 0
    for pidx, pchar in enumerate(pattern):
        if case_sensitive:
            idx = input.find(pchar, idx)
        else:
            idx = re.search(pchar, input[idx:], re.IGNORECASE)
            if idx:
                idx = idx.start() + idx.pos
            else:
                idx = -1
        if idx < 0:
            return -1, -1
        if pidx == 0 and idx > 0:
            first_idx = idx - 1
        last_idx = idx
        idx += 1
    return first_idx, last_idx + 1

def fuzzymatch_v2(case_sensitive, normalize, forward, input, pattern, with_pos):
    if len(pattern) == 0:
        return (0, 0, 0), None
    if len(input) < len(pattern):
        return (-1, -1, 0), None

    idx, _ = ascii_fuzzy_index(input, pattern, case_sensitive)
    if idx < 0:
        return (-1, -1, 0), None

    pidx = 0
    sidx = -1
    eidx = -1
    len_input = len(input)
    len_pattern = len(pattern)

    for index in range(len_input):
        index_ = index if forward else len_input - index - 1
        char = input[index_]
        if not case_sensitive:
            char = char.lower()
        if normalize:
            char = normalize_rune(char)
        pchar = pattern[pidx if forward else len_pattern - pidx - 1]
        if char == pchar:
            if sidx < 0:
                sidx = index
            if pidx + 1 == len_pattern:
                eidx = index + 1
                break
            pidx += 1
        else:
            index -= pidx
            pidx = 0

    if sidx >= 0 and eidx >= 0:
        pidx -= 1
        for index in range(eidx - 1, sidx - 1, -1):
            tidx = index if forward else len_input - index - 1
            char = input[tidx]
            if not case_sensitive:
                char = char.lower()
            pidx_ = pidx if forward else len_pattern - pidx - 1
            pchar = pattern[pidx_]
            if char == pchar:
                if pidx - 1 < 0:
                    sidx = index
                    break
                pidx -= 1

        if not forward:
            sidx, eidx = len_input - eidx, len_input - sidx
        return (sidx, eidx, 0), None

    return (-1, -1, 0), None

def fuzzymatch_v1(case_sensitive, normalize, forward, input, pattern, with_pos):
    if len(pattern) == 0:
        return (0, 0, 0), None

    idx, _ = ascii_fuzzy_index(input, pattern, case_sensitive)
    if idx < 0:
        return (-1, -1, 0), None

    pidx = 0
    sidx = -1
    eidx = -1

    len_input = len(input)
    len_pattern = len(pattern)

    for index in range(len_input):
        index_ = index if forward else len_input - index - 1
        char = input[index_]
        if not case_sensitive:
            char = char.lower()
        if normalize:
            char = normalize_rune(char)
        pchar = pattern[pidx if forward else len_pattern - pidx - 1]
        if char == pchar:
            if sidx < 0:
                sidx = index
            if pidx + 1 == len_pattern:
                eidx = index + 1
                break
            pidx += 1
        else:
            index -= pidx
            pidx = 0

    if sidx >= 0 and eidx >= 0:
        pidx -= 1
        for index in range(eidx - 1, sidx - 1, -1):
            tidx = index if forward else len_input - index - 1
            char = input[tidx]
            if not case_sensitive:
                char = char.lower()
            pidx_ = pidx if forward else len_pattern - pidx - 1
            pchar = pattern[pidx_]
            if char == pchar:
                if pidx - 1 < 0:
                    sidx = index
                    break
                pidx -= 1

        if not forward:
            sidx, eidx = len_input - eidx, len_input - sidx
        return (sidx, eidx, 0), None

    return (-1, -1, 0), None
