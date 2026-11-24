# SPU ADPCM (PS1 sound RAM format) encoder: 16-byte blocks of 28 samples, five prediction filters,
# shifts 0..12. Each block picks the filter/shift pair with the least squared error against the
# decoder's own history, so the encoder tracks exactly what the SPU will reconstruct.
import numpy as np

FILTERS = np.array([[0, 0], [60, 0], [115, -52], [98, -55], [122, -60]], dtype=np.int64)
SAMPLES = 28

# every (filter, shift) pair, tried side by side
_F = np.repeat(np.arange(5), 13)
_S = np.tile(np.arange(13), 5)


def encode(samples, flags=None):
    """samples: int16-range ints. flags: per-block flag byte (default 0, last block 0x01 = end + mute).
    Returns bytes, len(samples) padded up to a multiple of 28."""
    x = np.asarray(samples, dtype=np.int64)
    n = (len(x) + SAMPLES - 1) // SAMPLES
    x = np.concatenate([x, np.zeros(n * SAMPLES - len(x), dtype=np.int64)])
    if flags is None:
        flags = [0] * n
        flags[-1] = 0x01
    out = bytearray()
    h1 = h2 = 0
    f0 = FILTERS[_F, 0]
    f1 = FILTERS[_F, 1]
    for b in range(n):
        blk = x[b * SAMPLES:(b + 1) * SAMPLES]
        p1 = np.full(len(_F), h1, dtype=np.int64)
        p2 = np.full(len(_F), h2, dtype=np.int64)
        err = np.zeros(len(_F), dtype=np.int64)
        nib = np.zeros((len(_F), SAMPLES), dtype=np.int64)
        for i in range(SAMPLES):
            pred = (p1 * f0 + p2 * f1 + 32) >> 6
            # nibble that best reaches the target: residual scaled back by the shift
            r = blk[i] - pred
            q = np.round(r * (2.0 ** _S) / 4096.0).astype(np.int64)
            q = np.clip(q, -8, 7)
            d = ((q << 12) >> _S) + pred
            d = np.clip(d, -32768, 32767)
            err += (d - blk[i]) ** 2
            nib[:, i] = q
            p2, p1 = p1, d
        k = int(np.argmin(err))
        # replay the winner to carry its exact history into the next block
        f, s = int(_F[k]), int(_S[k])
        for i in range(SAMPLES):
            pred = (h1 * FILTERS[f, 0] + h2 * FILTERS[f, 1] + 32) >> 6
            d = max(-32768, min(32767, ((int(nib[k, i]) << 12) >> s) + pred))
            h2, h1 = h1, d
        out.append((f << 4) | s)
        out.append(flags[b])
        for i in range(0, SAMPLES, 2):
            out.append((int(nib[k, i]) & 0xF) | ((int(nib[k, i + 1]) & 0xF) << 4))
    return bytes(out)


def decode(data):
    """The reverse, for checking an encode: returns int16 samples."""
    out = []
    h1 = h2 = 0
    for b in range(0, len(data), 16):
        s = data[b] & 0xF
        f = min(data[b] >> 4, 4)
        for j in range(14):
            byte = data[b + 2 + j]
            for q in (byte & 0xF, byte >> 4):
                q = q - 16 if q >= 8 else q
                pred = (h1 * FILTERS[f, 0] + h2 * FILTERS[f, 1] + 32) >> 6
                d = max(-32768, min(32767, ((q << 12) >> s) + pred))
                h2, h1 = h1, d
                out.append(d)
    return np.array(out, dtype=np.int64)
