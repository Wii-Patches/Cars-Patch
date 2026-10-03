# Cars Trilogy Wii Patch: Technical Architecture & Implementation

This document describes the reverse engineering, hook placement, and controller synthesis implementation used in the Cars Wii Patch suite.

---

## 1. Engine & Subsystem Architecture

The three games in the Cars Wii trilogy share an engine foundation originated by Rainbow Studios and modified for Wii by Incinerator Studios:
- **Cars (2006)**: Early RVL_SDK integration (Wii launch window). Uses `WPADProbe`, `KPADRead`, and custom `WIIJoystickDevice` classes.
- **Cars: Mater-National Championship (2007)**: Expanded sandbox world, refined vehicle physics, and updated KPAD extensions.
- **Cars Race-O-Rama (2009)**: Modernized rendering pipeline, new drift mechanic, and expanded memory layouts.

---

## 2. Memory Layout & Trampoline Allocation

When patching a DOL statically without requiring dynamic code loaders (like Gecko OS), routines must reside in executable memory that does not conflict with the game's BSS, heap, or stack.

The Wii's low memory region `0x80001800 - 0x80003000` serves as a boot-time scratchpad that is entirely unused during standard game execution (the first 0x20 bytes are overwritten by OS boot). We partition this memory cave into deterministic windows:

| Address Range | Size | Allocation |
| :--- | :--- | :--- |
| `0x80001820 - 0x80002200` | `0x9E0` bytes | Classic Controller & FOV hook trampolines (`CC_BASE`) |
| `0x80002200 - 0x80002F00` | `0xD00` bytes | GameCube controller hook trampolines (`GC_BASE`) |
| `0x80002F00 - 0x80002F40` | `0x40` bytes | Per-channel state & button transition history (`DATA_BASE`) |

---

## 3. GameCube Controller Synthesis Pipeline

Rather than patching individual gameplay routines across hundreds of vehicle physics calls, the patch operates at the hardware polling boundary:

```
[Hardware: SI Inbuf] (0xCD006404)
        │
        ▼
[WPADProbe Hook] ────► If Wiimote disconnected & GC Pad present:
        │              Report ERR_NONE (0) and DevType = 2 (Classic Controller)
        ▼
[KPADRead Hook]  ────► Synthesize KPADStatus sample:
                       - Map GC buttons to CC bitfield
                       - Scale GC analog stick [-128..127] -> [-308..308]
                       - Map C-Stick / D-Pad Up to ZL / Shake (Jump)
                       - Compute trigger & release deltas
                       - Populate resting accelerometers
        │
        ▼
[Game Input Pipeline: WIIJoystickDevice]
Processes synthetic Classic Controller sample seamlessly.
```

### 3.1 SI Controller Registers
The Serial Interface (SI) coprocessor polls physical GameCube ports and mirrors results to hardware memory-mapped registers:
- `SICnINBUFH` (`0xCD006404 + 12 * n`):
  - Bit 31: Error flag (set if no controller connected).
  - Bit 23: Pad identification bit (always 1 for standard pads).
  - Bits [29:16]: Button bitfield (`A`, `B`, `X`, `Y`, `Start`, `Z`, `R`, `L`, `D-Pad`).
  - Bits [15:8]: Main Stick X (0..255).
- `SICnINBUFL` (`0xCD006408 + 12 * n`):
  - Bits [31:24]: Main Stick Y (0..255).
  - Bits [23:16]: C-Stick X (0..255).
  - Bits [15:8]: C-Stick Y (0..255).
  - Bits [7:0]: Analog triggers (L/R).

---

## 4. Skip Pitstop Motions & Widescreen FOV

### 4.1 Piston Cup Pitstop QTE Bypass
In the original Wii port of Cars 1, pitstops during Piston Cup races invoke motion-based QTE minigames requiring rapid Wii Remote gestures. The bypass patch replaces the timer check instruction in `PitstopMinigame::Update` (`0x80062CAC`):
```powerpc
b 0x80062CC8    # Force branch directly to successful completion
```

### 4.2 Widescreen Field of View (hor+)
Cars was originally rendered in 4:3 on sixth-gen consoles. In the Wii port, 16:9 widescreen was implemented by cropping the top and bottom of the 4:3 view (`vert-`).

The widescreen hook intercepts the viewport aspect calculation:
- Reads system aspect ratio flag (`0x800D99C8`).
- When 16:9 is active, multiplies the projection matrix horizontal field of view by `1.3333333f` (`4:3 -> 16:9`), maintaining vertical height while expanding the peripheral viewing field (`hor+`).
