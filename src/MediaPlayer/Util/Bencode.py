class BTFailure(Exception):
    pass


def decode_int(x, f):
    f += 1
    new_f = x.index(b'e', f)
    n = int(x[f:new_f])
    if x[f] == ord('-'):
        if x[f + 1] == ord('0'):
            raise ValueError()
    elif x[f] == ord('0') and new_f != f + 1:
        raise ValueError()
    return n, new_f + 1


def decode_string(x, f):
    colon = x.index(b':', f)
    n = int(x[f:colon])
    if x[f] == ord('0') and colon != f + 1:
        raise ValueError()
    colon += 1
    return x[colon:colon + n], colon + n


def decode_list(x, f):
    r, f = [], f + 1
    while x[f] != ord('e'):
        v, f = decode_func[x[f]](x, f)
        r.append(v)
    return r, f + 1


def decode_dict(x, f):
    r, f = {}, f + 1
    while x[f] != ord('e'):
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f]](x, f)
    return r, f + 1


decode_func = {
    ord('l'): decode_list,
    ord('d'): decode_dict,
    ord('i'): decode_int,
    ord('1'): decode_string,
    ord('2'): decode_string,
    ord('0'): decode_string,
    ord('3'): decode_string,
    ord('4'): decode_string,
    ord('5'): decode_string,
    ord('6'): decode_string,
    ord('7'): decode_string,
    ord('8'): decode_string,
    ord('9'): decode_string,
}


def bdecode(x):
    try:
        r, l = decode_func[x[0]](x, 0)
    except (IndexError, KeyError, ValueError):
        raise BTFailure("not a valid bencoded string")
    if l != len(x):
        pass
        # raise BTFailure("invalid bencoded value (data after valid prefix)")
    return r


def encode_int(x, r):
    r.extend((b'i', str(x).encode(), b'e'))


def encode_bool(x, r):
    if x:
        encode_int(1, r)
    else:
        encode_int(0, r)


def encode_string(x, r):
    r.extend((str(len(x)).encode(), b':', x))


def encode_list(x, r):
    r.append(b'l')
    for i in x:
        encode_func[type(i)](i, r)
    r.append(b'e')


def encode_dict(x, r):
    r.append(b'd')
    item_list = list(x.items())
    item_list.sort()
    for k, v in item_list:
        r.extend((str(len(k)).encode(), b':', k))
        encode_func[type(v)](v, r)
    r.append(b'e')


encode_func = {
    int: encode_int,
    bytes: encode_string,
    list: encode_list,
    tuple: encode_list,
    dict: encode_dict,
    bool: encode_bool,
}


def bencode(x):
    r = []
    encode_func[type(x)](x, r)
    return b''.join(r)