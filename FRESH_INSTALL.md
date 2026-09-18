# Fresh install: Equalizer APO → SM7B-style podcast mic

Step-by-step reproduction of the setup running on this machine.
Verified against **Equalizer APO 1.4.2** (the version installed here).

**The 60-second version:** install Equalizer APO → reboot → tick your mic in the
Configurator → drop `rnnoise_stereo.dll` into `EqualizerAPO\VSTPlugins\` →
install ReaPlugs → copy `mic_sm7b_podcast.txt` over `config\config.txt` → reboot
→ point Discord at the mic and turn its own processing off.

---

## Step 0 — Before you start

Write down **which microphone you actually want processed**. On this machine
there are two active mics (`Fantech Leviosa` and `AB13X USB Audio`) and only one
of them is the one Discord listens to. Getting this wrong is the single most
common reason "Equalizer APO does nothing".

Also decide: are you installing on the **microphone** (capture) or the
**speakers** (render)? This guide is for the microphone.

---

## Step 1 — Install Equalizer APO

1. Download from **https://sourceforge.net/projects/equalizerapo/** (get 1.4.2
   or newer — you need 1.3+ for VST plugin support and `Stage:`).
2. Run the installer. Accept the default path
   `C:\Program Files\EqualizerAPO`.
3. At the end, the installer launches the **Configurator**.
4. **This is the step everyone skips.** In the Configurator:
   - Switch to the **Capture devices** tab.
   - Tick your **microphone**.
   - Leave the speakers unticked unless you want the EQ on playback too.
   - Click **OK**.
5. **Reboot.** Not optional — the APO is attached to the audio device at boot.

> If the Configurator doesn't appear, or the mic list is empty, run
> `C:\Program Files\EqualizerAPO\Configurator.exe` **as administrator**.

### Checkpoint

Open `C:\Program Files\EqualizerAPO\Editor.exe`. You should see a filter list
and a graph. If it opens, Equalizer APO is working.

---

## Step 2 — Install the two VST plugins

The config uses exactly two plugins. **Neither ships with Equalizer APO** — you
must add both by hand.

### 2a. rnnoise (noise suppression)

1. Download the Windows release from
   **https://github.com/werman/noise-suppression-for-voice/releases**
   (v1.10 is the current stable; v1.21 is a pre-release).
2. Extract it. Inside you'll find a **VST2 64-bit** build with
   `rnnoise_mono.dll` and `rnnoise_stereo.dll`.
3. Copy the DLL into:
   ```
   C:\Program Files\EqualizerAPO\VSTPlugins\
   ```
4. **Use `rnnoise_mono.dll` for a single microphone** — it costs half the CPU
   and a mic is mono anyway. If you use the mono file, change the line in the
   config to match:
   ```
   VSTPlugin: Library rnnoise_mono.dll
   ```

> This is exactly why the config says `rnnoise_stereo.dll` — that's the file
> that happens to be in the folder on this machine. The filename in the config
> must match the filename on disk, or the plugin silently fails to load.

### 2b. ReaPlugs (the compressor)

1. Download from **https://www.reaper.fm/reaplugs/**
2. Install it. It defaults to:
   ```
   C:\Program Files\VstPlugins\ReaPlugs\
   ```
3. Confirm `reacomp-standalone.dll` is in that folder.

> **The classic trap:** if you already own REAPER, do *not* point Equalizer APO
> at `ReaComp.dll` from inside the REAPER install. That's the DAW plugin and it
> will throw "Initialization failed". You need the **`-standalone`** build that
> ReaPlugs installs. This trips up a lot of people.

### Bit-depth rule

Equalizer APO 1.4.2 x64 can only load **64-bit** plugins. A 32-bit DLL will
either fail to load or crash the audio service. When in doubt, check the
download page for an x64 build.

---

## Step 3 — Put the config in place

1. **Back up the stock config first.** It's nearly empty, but do it anyway:
   ```
   copy "C:\Program Files\EqualizerAPO\config\config.txt" "%USERPROFILE%\Desktop\config-backup.txt"
   ```
2. Copy `mic_sm7b_podcast.txt` from this folder to
   ```
   C:\Program Files\EqualizerAPO\config\config.txt
   ```
   Writing into `Program Files` needs admin rights — use an **administrator**
   Notepad, or an admin PowerShell:
   ```
   Copy-Item .\mic_sm7b_podcast.txt "C:\Program Files\EqualizerAPO\config\config.txt" -Force
   ```
3. **The filename must be exactly `config.txt`.** With "hide known file
   extensions" on, Notepad will happily save `config.txt.txt` and nothing will
   work. Check in Explorer that it isn't showing a `.txt.txt`.
4. **If ReaPlugs installed somewhere else**, edit the path in the
   `VSTPlugin: Library "..."` line to match reality.

### Optional: verify the compressor values

The ReaComp line's numbers are not decibels or milliseconds — they're ReaComp's
internal scale. If you want to confirm them without trusting me:

```
C:\Users\Sensei\.workbuddy-ai\binaries\python\versions\3.13.12\python.exe tools\vst_inspect_params.py
```

That prints every ReaComp parameter and what it really means.

---

## Step 4 — Reload

Equalizer APO watches `config.txt` and reloads it automatically when the file
changes. If your voice sounds unchanged:

```
Restart-Service Audiosrv -Force
```

or reboot. Worst case, re-open `Configurator.exe` and click OK.

---

## Step 5 — Verify it's actually working

1. Open `Editor.exe`. You should see **14 active entries** and the response
   curve from the README.
2. No red error markers on either `VSTPlugin` line. A red line means the plugin
   path is wrong or the DLL is the wrong bit depth.
3. Talk into the mic and watch the **VST plugin's own window** — the ReaComp
   gain-reduction meter should move. If it never moves, audio isn't reaching it.
4. Record yourself in Windows **Voice Recorder** and listen. Compare with the
   config disabled (rename `config.txt` and reload).

---

## Step 6 — Discord

This matters as much as the config does.

| Setting | Set it to | Why |
|---|---|---|
| Input device | Your **Fantech Leviosa** | If Discord listens to the other mic, none of this applies |
| Input Volume | Leave at default, adjust the Windows mic level instead | Two gain stages fighting = pumping |
| **Automatic Gain Control** | **OFF** | We're doing real compression; AGC will fight it and pump |
| **Noise Suppression (Krisp)** | **OFF** | You're already running rnnoise. Two denoisers stacked sounds crunchy |
| Echo Cancellation | OFF (unless on speakers) | Same reason |
| Advanced Voice Activity | Optional | Fine to leave on |

Then in Windows: **Sound settings → your mic → Properties → Advanced**, and
untick **"Allow applications to take exclusive control of this device"**.
Exclusive mode bypasses audio processing objects entirely, so Equalizer APO
would be skipped.

---

## Step 7 — Confirm it applies everywhere you care about

Equalizer APO only affects apps that use the **shared** Windows audio engine.

| App | Works? |
|---|---|
| Discord, Teams, Zoom, OBS, browsers | Yes |
| Games in "exclusive mode" audio | No |
| Apps with their own ASIO driver | No |
| Voicemeeter / virtual audio devices | Only if the APO is on the right device in the chain |

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| Nothing changes at all | Mic not ticked in the Configurator, or no reboot |
| Works in one app, not another | That app uses exclusive mode or ASIO |
| Editor shows a red VST line | Wrong path, or 32-bit plugin in a 64-bit APO |
| "Initialization failed" on ReaComp | You pointed at REAPER's `ReaComp.dll` instead of ReaPlugs' `reacomp-standalone.dll` |
| Suddenly very quiet | Auto make-up gain is on and the threshold is low; raise the Windows mic level |
| Sudden loud distortion | Windows mic level too high — the compressor can't undo input clipping that already happened |
| Crackling / dropouts | Too many plugins, or a plugin is crashing. Comment out the VST lines and retest |
| Audio breaks entirely | Rename or delete `config.txt` — the APO falls back to clean pass-through |
| Broke after a Windows feature update | Re-run `Configurator.exe` as admin and re-tick the device; major updates sometimes drop APO registrations |
| Still stuck | **Voicemeeter Banana** does the same chain as a virtual device — heavier, but far more robust |

---

## What the finished state looks like

`C:\Program Files\EqualizerAPO\config\config.txt`:

```
Stage: capture
VSTPlugin: Library rnnoise_stereo.dll
Preamp: -5 dB
Filter 1: ON HPQ Fc 65 Hz Q 0.707
Filter 2: ON PK Fc 100 Hz Gain 3.0 dB Q 1.0
Filter 3: ON LS Fc 250 Hz Gain 1.5 dB
Filter 4: ON PK Fc 330 Hz Gain -3.0 dB Q 1.1
Filter 5: ON PK Fc 750 Hz Gain -1.5 dB Q 2.0
Filter 6: ON PK Fc 3200 Hz Gain 2.5 dB Q 1.2
Filter 7: ON PK Fc 6000 Hz Gain 2.0 dB Q 1.3
Filter 8: ON PK Fc 7800 Hz Gain -2.0 dB Q 1.8
Filter 9: ON HS Fc 11000 Hz Gain 2.0 dB
Filter 10: ON LP Fc 17000 Hz
VSTPlugin: Library "C:\Program Files\VSTPlugins\ReaPlugs\reacomp-standalone.dll" Hipass 0.005 Thresh 0.1 Ratio 0.03 Attack 0.02 Release 0.03 Pre-comp 0 resvd 0 Lowpass 1 SignIn 0 AudIn 0 Dry 0 Wet 1 AutoMkUp 1 PreviewF 0 "RMS size" 0.01 Knee 0.25 AutoRel 0 ClsAttk 1 AntiAls 0
```

14 active lines. Anything else in the file is a comment (`#`) and is ignored.

### Syntax rules worth remembering

- `#` at the start of a line = comment. Equalizer APO ignores it.
- **Never put a trailing `#` comment on a `Filter:` or `Preamp:` line.** Any
  line that doesn't match the expected format is silently dropped, so an inline
  comment can make the filter vanish without warning. Comments go on their own
  line.
- Relative plugin paths resolve against `C:\Program Files\EqualizerAPO\VSTPlugins\`.
- `Stage: capture` keeps this config off your speakers permanently.
