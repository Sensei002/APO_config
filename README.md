# SM7B-style podcast chain for the Fantech Leviosa

`mic_sm7b_podcast.txt` shapes your mic into the classic broadcast
"SM7B + LA-2A" sound: deep warm low end, no cardboard-box mud, forward
presence, and a crisp but never hissy top.

**Status: installed and live.** It is already written to
`C:\Program Files\EqualizerAPO\config\config.txt`.

---

## 0. What is where on this machine

| Thing | Value |
|---|---|
| Microphone Equalizer APO is attached to | **Fantech Leviosa** |
| APO slot | Capture device `{b3369c64-68d0-460d-9525-303a84b36f8b}`, SFX = `{EACD2258-…}` |
| Devices with no APO | `AB13X USB Audio` (a second, unused mic), all speakers/headphones |
| Plugins in the active chain | rnnoise + ReaComp (compressor) |
| Removed from the active chain | ReaEQ, ATKExpander |
| Backup of the previous config | `backup_config_original.txt` and `config.txt.bak` |

Because Equalizer APO is installed on the mic only, your speakers and
headphones were never affected. `Stage: capture` keeps it that way permanently.

> **Make sure Discord's input device is the Fantech Leviosa**, not `AB13X USB
> Audio`. If Discord listens to the other mic, none of this applies.

### If the change doesn't seem to have taken effect

Equalizer APO reloads `config.txt` automatically when the file changes. If your
voice still sounds flat, force it:

```
Restart-Service Audiosrv -Force
```

or re-open `Configurator.exe` and click OK. Worst case, reboot.

---

## 2. What each block does

| Block | What it does | Why it matters |
|---|---|---|
| `VSTPlugin: Library rnnoise_stereo.dll` | Noise suppression | Kept from your old config. **This is the #1 thing that makes a mic sound "processed" instead of natural.** If your room is quiet, comment it out. |
| Filters 1–3 | HPF 65 Hz, +3 dB @ 100 Hz, +1.5 dB shelf @ 250 Hz | The "deep bassy". Chest, body, weight. |
| Filter 4 | **−3 dB @ 330 Hz** | The mud cut. The single most important filter here — it's what separates "podcast" from "laptop mic". |
| Filters 5 | −1.5 dB @ 750 Hz | Kills the cheap-mic honk/nasal tone. |
| Filters 6–7 | +2.5 dB @ 3.2 kHz, +2 dB @ 6 kHz | Presence and definition. This is what makes words cut through Discord. |
| Filter 8 | −2 dB @ 7.8 kHz | Static de-esser. Tames the S/Z harshness that 6–7 would otherwise expose. |
| Filters 9–10 | +2 dB shelf @ 11 kHz, LPF 17 kHz | Air + smooth top. "Crispy" without hiss. |
| ReaComp | Compression, **4:1** | The other half of the podcast sound. Values measured against the real plugin — see §3. |

**Total peak boost is about +4 dB at 100 Hz**, which is why there's a
`Preamp: -5 dB` at the top. If you still clip, make it −6 or −7.

---

## 3. Compression — ON, and measured

The chain now ends in ReaComp set to **4:1 / 10 ms attack / 150 ms release /
6 dB soft knee / −20 dBFS threshold / auto make-up on / 100 Hz detector
high-pass**. Those numbers were not guessed — I loaded the actual plugin, read
its parameter scale, and ran audio through it to measure the result:

| Input | Output | Net gain |
|---|---|---|
| −3 dBFS | −6.0 dBFS | −3.0 dB |
| −12 dBFS | −8.4 dBFS | +3.6 dB |
| −24 dBFS | −16.5 dBFS | +7.5 dB |
| −40 dBFS | −32.5 dBFS | +7.5 dB |

27 dB of input range is squeezed into 16 dB of output range, and the output
never gets anywhere near clipping. Auto make-up gain measured at exactly
**+7.5 dB**.

For reference: your *previous* config had `Ratio 0`, which in ReaComp means
**1:1** — it was doing no compression at all.

### Adjusting it

| Symptom | Change |
|---|---|
| Too squashed, breathy, or you hear it working on every syllable | `Thresh 0.1` → `0.15` (that's −20 → −16.5 dBFS) |
| Not controlled enough | `Ratio 0.03` → `0.05` (4:1 → 6:1) |
| Pumping / level breathing | `Release 0.03` → `0.05` (150 → 250 ms) |
| Sounds dull / lifeless | `Attack 0.02` → `0.03` (10 → 15 ms) |
| Not loud enough overall | Raise the **mic level in Windows**, not the preamp |

### Why you can trust these numbers

The `tools/` folder contains the two scripts used to derive them:

- `vst_inspect_params.py` — loads a VST2 DLL and dumps every parameter's name
  plus the real-world value for a range of inputs. Run it against any plugin to
  learn its scale.
- `vst_measure_gain.py` — pushes audio through the plugin and reports output
  level, so you can check gain staging before it ever reaches your ears.

Both run on the bundled Python with no extra packages.

**Optional limiter:** if shouts and laughter still clip, add a second ReaComp
line at the very end of the chain with a high ratio (~20:1), ~1 ms attack,
~40 ms release and the threshold just under 0 dB. Not included by default.

---

## 4. About VST3

**Your Equalizer APO build is VST 2.4 only — it cannot load a `.vst3` file.**
I verified this against your actual install: the APO only exports
`VSTPluginLibrary` / `VSTPluginMain`, and there is no `VST3Plugin` command in
the official release. VST3 is a long-standing open feature request upstream.

Three ways forward:

1. **Install a VST3-capable fork** (unofficial) — e.g. *EqAPO64_with_VST3_support*
   or *EqualizerAPOVst3*. In those you add the plugin through the editor
   (`Add > VST plug-in`) and point it at the `.vst3` bundle. Fork syntax is not
   standardised, so let the editor write the line rather than hand-editing it.
2. **Wrap the VST3 in a VST2 shell** — DDMF MetaPlugin, Blue Cat's PatchWork, or
   Kushview Element. Load the wrapper as VST2.
3. **Just use VST2.** Everything in this config is VST2 and you lose nothing —
   ReaPlugs, TDR Nova, Klanghelm and Bertom all ship VST2 builds.

Good free VST2 additions if you want to go further:
- **TDR Nova** — dynamic EQ; its de-esser preset beats the static filter 8 here.
- **Klanghelm MJUC jr.** — vari-mu compression, extremely "radio".
- **Bertom Denoiser** — better-sounding than RNNoise if you need suppression.

---

## 5. Discord settings that matter

- **Turn off Discord's "Noise Suppression"** (Krisp) if you're using RNNoise —
  running both stacks two denoisers and sounds crunchy.
- **Turn off "Automatic Gain Control"** (or "Automatically determine input
  sensitivity"). We're doing proper compression now; Discord's AGC will fight it
  and pump.
- **Echo Cancellation off** unless you use speakers instead of headphones.
- Then set your input volume in Windows once and leave it alone.

---

## 6. Tuning it to *your* voice

This curve assumes a fairly typical mic. Adjust in this order:

- **Too boomy / too much bass?** Lower Filter 2 first (3.0 → 1.5 dB), then
  Filter 3. Don't touch the 65 Hz high-pass — that's just rumble removal.
- **Too thin / not deep enough?** Raise Filter 2 toward +4 dB and Filter 3 to
  +2.5 dB. Move closer to the mic (proximity effect adds real bass).
- **Still muddy?** Deepen Filter 4 toward −4 dB.
- **Harsh S sounds?** Deepen Filter 8 to −3 dB, or lower Filter 7 to +1 dB.
- **Not crisp enough?** Raise Filter 9 (air shelf) toward +3 dB.
- **Sounds hollow/phasey?** You've over-cut the mids — bring Filter 5 back
  toward 0 dB.
- **Dynamic mic that's already dark** (SM7B, SM58, PodMic)? Halve the presence
  boosts: Filter 6 to +1.5 dB, Filter 7 to +1 dB.
- **Bright USB condenser** (Yeti, Fifine, Blue, **Fantech Leviosa**)? The config
  as-is is already aimed at you.

**Your mic is a Fantech Leviosa** — a bright, thin, small-capsule USB condenser.
That is exactly the class this curve was designed for, so the defaults should
already sound right. If it comes out harsh rather than crisp, lower Filter 7
(6 kHz) from +2.0 to +1.0 dB — that's the most likely offender on this mic.

---

## 7. Troubleshooting

| Symptom | Cause |
|---|---|
| Nothing changes | APO not ticked on the *capture* device in Configurator, or no reboot. |
| Nothing changes in one app only | That app is using WASAPI Exclusive mode, or its own capture path. Switch it to shared/default. |
| APO Editor shows a red error on a VST line | Plugin path is wrong or it's a 32-bit plugin in a 64-bit APO. Must match. |
| Mic is suddenly very quiet | Lower `Preamp` less (−3 dB), or raise the mic level in Windows Sound settings. |
| Audio breaks entirely | Rename/delete `config.txt` — the APO falls back to a clean pass-through. |
| Crackling / dropouts | Too many plugins, or the plugin is crashing. Comment out the VST lines and test. |

If Equalizer APO's capture processing won't cooperate with Discord at all,
the fallback is **Voicemeeter Banana**, which does the same chain as a virtual
device — heavier, but bulletproof.

---

## 8. Files

| File | Purpose |
|---|---|
| `mic_sm7b_podcast.txt` | The config. Mirrors the live `config.txt`. |
| `README.md` | This file. |
| `FRESH_INSTALL.md` | Full step-by-step from a clean Equalizer APO install. |
| `backup_config_original.txt`, `config.txt.bak` | Your original config, before any of this. |
| `tools/vst_inspect_params.py` | Dump any VST2 plugin's parameter names and real values. |
| `tools/vst_measure_gain.py` | Measure a plugin's output level before trusting it. |
