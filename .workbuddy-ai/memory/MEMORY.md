# APO_config — project notes

## Purpose
Maintain a Shure SM7B-style "podcast voice" processing chain for the user's
microphone, applied system-wide through Equalizer APO.

## Hardware / environment (stable facts)
- **Equalizer APO version: 1.4.2** (binaries dated 2025-03-21). Installed
  2026-09-19 at 00:23.
- **Microphone: Fantech Leviosa** — bright, thin, small-capsule USB condenser.
  EQ curves for this project should assume that mic, not a neutral one.
- A second, unused active mic is present: **AB13X USB Audio**. Discord must be
  pointed at the Leviosa or nothing here applies.
- Equalizer APO lives at `C:\Program Files\EqualizerAPO`. Live config is
  `config\config.txt`; bundled VST folder is `VSTPlugins`.
- Equalizer APO is installed on the **microphone only** — no render device has
  it, so playback is never affected.
- **The installed build is VST 2.4 only.** It cannot load `.vst3` files; there
  is no `VST3Plugin` command upstream. VST3 needs a fork or a VST2 wrapper.

## Plugins: what ships with what

**Nothing usable ships with Equalizer APO.** Both plugins are added by hand:

- `rnnoise_stereo.dll` in `EqualizerAPO\VSTPlugins\` comes from
  **werman/noise-suppression-for-voice** (Xiph RNNoise), latest stable v1.10.
  It is NOT bundled by the installer — do not assume a fresh install has it.
  Ships `rnnoise_mono.dll` and `rnnoise_stereo.dll` (VST2 x64); **mono is the
  right pick for a single mic** (half the CPU). The filename in the config must
  match the file on disk.
- `C:\Program Files\VstPlugins\ReaPlugs\` — ReaPlugs, from reaper.fm/reaplugs
  (default install path). Contains reacomp, reaeq, reaxcomp, reagate, readelay,
  reafir, reajs, all `*-standalone.dll`.
- **Use `reacomp-standalone.dll`, never REAPER's `ReaComp.dll`** — the DAW
  plugin fails with "Initialization failed" in Equalizer APO.
- Equalizer APO 1.4.2 x64 can only load **64-bit** plugins.

## Conventions
- Keep `Stage: capture` at the top of the config so the chain can never reach
  speakers/headphones.
- Comments go on their own line. Never add a trailing `#` comment to a
  `Filter:` / `Preamp:` line — Equalizer APO silently drops lines it cannot
  parse, so the filter would vanish.
- Keep exactly one backup of the previous live config before overwriting.
- Prefer native APO `Filter:` commands for tone shaping; only reach for a VST
  when the effect genuinely cannot be done natively (compression, denoise).
- ReaComp parameter values are in ReaComp's own internal scale and are not
  reliably hand-writable — set them in the plugin GUI and let APO rewrite the
  line.

## ReaComp parameter scale (measured, authoritative)

ReaComp's config values are **not** real-world units. Verified by loading the
DLL in a hand-written ctypes VST2 host:

| Param | Scale | Notes |
|---|---|---|
| Thresh | linear amplitude, shows as `20*log10(v)` | `0.1` = −20 dBFS |
| Ratio | `ratio = v*100 + 1` | `0.03` = 4:1, `0.05` = 6:1, **`0` = 1:1** |
| Attack | `ms = v*500` | |
| Release | `ms = v*5000` | |
| Pre-comp | `ms = v*250` | |
| Lowpass / Hipass | `Hz = v*20000` | |
| Dry / Wet | linear gain shown in dB | `0` = −inf, `1` = 0 dB |
| RMS size | `ms = v*1000` | |
| Knee | `dB = v*24` | |
| AutoMkUp / AutoRel / ClsAttk / PreviewF | toggles, ≥0.5 = on | |
| AntiAls | stepped 0–13 | |
| SignIn / AudIn | 0–1084 | |

Shipped vocal setting: `Thresh 0.1 Ratio 0.03 Attack 0.02 Release 0.03 Knee 0.25
RMS 0.01 Hipass 0.005 Dry 0 Wet 1 AutoMkUp 1 ClsAttk 1`. Measured: auto make-up
is a fixed **+7.5 dB**, output peaks ≈ −6 dBFS, no clipping.

## Technique: interrogating an opaque VST2 plugin

`tools/vst_inspect_params.py` and `tools/vst_measure_gain.py` load a VST2 DLL
with `ctypes` and either dump each parameter's real value or push audio through
it and measure the output level. Use these instead of guessing whenever a
plugin's config values are opaque. Essentials: `ctypes.CDLL` (VSTCALLBACK is
`__cdecl`), `AEffect` is 192 bytes on x64, and the `audioMaster` callback must
be stubbed (version→2400, getTime→valid `VstTimeInfo`, sample rate, block size).

## Files
- `mic_sm7b_podcast.txt` — the config (mirrors the live file).
- `backup_config_original.txt` / `config.txt.bak` — pre-change backups.
- `README.md` — install, tuning and troubleshooting guide.
- `tools/` — the two VST interrogation scripts.
