"""Probe a VST2 plugin's parameters: names, and the display string for a
range of normalised values. Used to learn the real-world meaning of
ReaComp's internal parameter scale before writing an Equalizer APO config.
"""
import ctypes
from ctypes import (c_int32, c_int64, c_float, c_double, c_void_p,
                    POINTER, CFUNCTYPE, Structure, create_string_buffer)

DLL = r"C:\Program Files\VSTPlugins\ReaPlugs\reacomp-standalone.dll"

effOpen, effGetParamName, effGetParamDisplay = 0, 8, 7
effSetSampleRate, effSetBlockSize, effMainsChanged = 10, 11, 12


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
TIME.sampleRate, TIME.tempo = 48000.0, 120.0
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
        return 48000
    if opcode == 17:
        return 512
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


DISPATCH = CFUNCTYPE(c_int64, c_void_p, c_int32, c_int32, c_int64, c_void_p, c_float)
SETPARAM = CFUNCTYPE(None, c_void_p, c_int32, c_float)
GETPARAM = CFUNCTYPE(c_float, c_void_p, c_int32)

print("AEffect size =", ctypes.sizeof(AEffect), " numParams@", AEffect.numParams.offset)

lib = ctypes.CDLL(DLL)
entry = getattr(lib, "VSTPluginMain", None) or lib.main
entry.restype = c_void_p
entry.argtypes = [AUDIO_MASTER]

raw = entry(host)
if not raw:
    raise SystemExit("VSTPluginMain returned NULL")
print("AEffect ptr =", hex(raw), " magic =", hex(ctypes.cast(raw, POINTER(AEffect)).contents.magic))

e = ctypes.cast(raw, POINTER(AEffect)).contents
disp = DISPATCH(e.dispatcher)
setp = SETPARAM(e.setParameter)
getp = GETPARAM(e.getParameter)

disp(raw, effOpen, 0, 0, None, 0.0)
disp(raw, effSetSampleRate, 0, 0, None, 48000.0)
disp(raw, effSetBlockSize, 0, 512, None, 0.0)
disp(raw, effMainsChanged, 0, 1, None, 0.0)

n = e.numParams
print("numParams =", n, " inputs =", e.numInputs, " outputs =", e.numOutputs)
print()

SAMPLES = [0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]

for i in range(n):
    nbuf = create_string_buffer(256)
    disp(raw, effGetParamName, i, 0, nbuf, 0.0)
    name = nbuf.value.decode("latin-1")
    row = []
    for v in SAMPLES:
        setp(raw, i, v)
        dv = getp(raw, i)
        dbuf = create_string_buffer(256)
        disp(raw, effGetParamDisplay, i, 0, dbuf, 0.0)
        txt = dbuf.value.decode("latin-1")
        row.append("%.2f->%s(%.4g)" % (v, txt, dv))
    print("[%2d] %-10s %s" % (i, name, " | ".join(row)))
