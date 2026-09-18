"""Measure ReaComp's real output level for a range of input levels, so we
know whether auto make-up gain will push the mic into clipping.
"""
import ctypes, math
from ctypes import (c_int32, c_int64, c_float, c_double, c_void_p,
                    POINTER, CFUNCTYPE, Structure, create_string_buffer)

DLL = r"C:\Program Files\VSTPlugins\ReaPlugs\reacomp-standalone.dll"
SR, N = 48000.0, 512
SETTINGS = [("Hipass", 7, 0.005), ("Thresh", 0, 0.1), ("Ratio", 1, 0.03),
            ("Attack", 2, 0.02), ("Release", 3, 0.03), ("Lowpass", 6, 1.0),
            ("Dry", 10, 0.0), ("Wet", 11, 1.0), ("RMS size", 13, 0.01),
            ("Knee", 14, 0.25), ("AutoMkUp", 15, 1.0), ("ClsAttk", 17, 1.0)]


class VstTimeInfo(Structure):
    _fields_ = [("samplePos", c_double), ("sampleRate", c_double),
                ("nanoSeconds", c_double), ("ppqPos", c_double),
                ("tempo", c_double), ("barStartPos", c_double),
                ("cycleStartPos", c_double), ("cycleEndPos", c_double),
                ("timeSigNumerator", c_int32), ("timeSigDenominator", c_int32),
                ("smpteOffset", c_int32), ("smpteFrameRate", c_int32),
                ("samplesToNextClock", c_int32), ("flags", c_int32)]


class AEffect(Structure):
    _fields_ = [("magic", c_int32), ("dispatcher", c_void_p),
                ("process", c_void_p), ("setParameter", c_void_p),
                ("getParameter", c_void_p), ("numPrograms", c_int32),
                ("numParams", c_int32), ("numInputs", c_int32),
                ("numOutputs", c_int32), ("flags", c_int32),
                ("reserved1", c_void_p), ("reserved2", c_void_p),
                ("initialDelay", c_int32), ("realQualities", c_int32),
                ("offQualities", c_int32), ("ioRatio", c_float),
                ("object", c_void_p), ("user", c_void_p),
                ("uniqueID", c_int32), ("version", c_int32),
                ("processReplacing", c_void_p), ("processDoubleReplacing", c_void_p),
                ("future", ctypes.c_char * 56)]


TIME = VstTimeInfo()
TIME.sampleRate, TIME.tempo = SR, 120.0
TIME.timeSigNumerator, TIME.timeSigDenominator = 4, 4
TIME.flags = 0x2 | 0x10 | 0x400 | 0x800
AUDIO_MASTER = CFUNCTYPE(c_int64, c_void_p, c_int32, c_int32, c_int64, c_void_p, c_float)


@AUDIO_MASTER
def host(effect, opcode, index, value, ptr, opt):
    if opcode == 1:
        return 2400
    if opcode == 7:
        return ctypes.addressof(TIME)
    if opcode == 16:
        return SR
    if opcode == 17:
        return N
    if opcode == 21:
        return 1
    if opcode == 23:
        return 2
    if opcode in (32, 33):
        ctypes.memmove(ptr, b"Probe", 6)
        return 1
    if opcode == 34:
        return 1000
    if opcode == 39:
        return 1
    return 0


lib = ctypes.CDLL(DLL)
entry = getattr(lib, "VSTPluginMain", None) or lib.main
entry.restype = c_void_p
entry.argtypes = [AUDIO_MASTER]
raw = entry(host)
e = ctypes.cast(raw, POINTER(AEffect)).contents

DISPATCH = CFUNCTYPE(c_int64, c_void_p, c_int32, c_int32, c_int64, c_void_p, c_float)
SETPARAM = CFUNCTYPE(None, c_void_p, c_int32, c_float)
PROC = CFUNCTYPE(None, c_void_p, POINTER(POINTER(c_float)), POINTER(POINTER(c_float)), c_int32)

disp = DISPATCH(e.dispatcher)
setp = SETPARAM(e.setParameter)
proc = PROC(e.processReplacing)

disp(raw, 0, 0, 0, None, 0.0)
disp(raw, 10, 0, 0, None, SR)
disp(raw, 11, 0, N, None, 0.0)
disp(raw, 12, 0, 1, None, 0.0)
for _, idx, val in SETTINGS:
    setp(raw, idx, val)

print("plugin reports: numInputs=%d numOutputs=%d  processReplacing=%s"
      % (e.numInputs, e.numOutputs, "yes" if e.processReplacing else "NO"))

nch_in, nch_out = max(e.numInputs, 1), max(e.numOutputs, 1)
inbufs = [(c_float * N)() for _ in range(nch_in)]
outbufs = [(c_float * N)() for _ in range(nch_out)]
in_ptrs = (POINTER(c_float) * nch_in)()
out_ptrs = (POINTER(c_float) * nch_out)()
for i in range(nch_in):
    in_ptrs[i] = ctypes.cast(inbufs[i], POINTER(c_float))
for i in range(nch_out):
    out_ptrs[i] = ctypes.cast(outbufs[i], POINTER(c_float))


def dbfs(x):
    return 20.0 * math.log10(x) if x > 1e-12 else float("-inf")


print()
print("%-12s %-12s %-12s %s" % ("INPUT", "OUTPUT", "NET GAIN", "VERDICT"))
print("-" * 62)
for amp_db in (-3.0, -6.0, -12.0, -18.0, -24.0, -30.0, -40.0):
    amp = 10 ** (amp_db / 20.0)
    for blk in range(80):
        for i in range(N):
            v = amp * math.sin(2 * math.pi * 1000.0 * i / SR)
            for ch in range(nch_in):
                inbufs[ch][i] = v
        proc(raw, in_ptrs, out_ptrs, N)
    peak = max(abs(outbufs[0][i]) for i in range(N))
    gain = dbfs(peak) - amp_db
    verdict = "OK"
    if dbfs(peak) > -0.5:
        verdict = "CLIPPING RISK"
    elif gain < -12:
        verdict = "very quiet"
    print("%-12s %-12s %-12s %s" % ("%.1f dBFS" % amp_db, "%.1f dBFS" % dbfs(peak),
                                    "%+.1f dB" % gain, verdict))
