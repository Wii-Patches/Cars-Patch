# Cars Trilogy Wii Patch: technical notes

How each patch is built, where it hooks, and what has been checked.

## Releases

| Game | IDs | KPAD offset from USA |
| :--- | :--- | :--- |
| Cars (2006) | `RCAE78` USA, `RCAP78` En/Es, `RCAX78` Fr/Nl, `RCAY78` De/It, `RCAJ78` Japan | 0, +0x70 (all PAL), +0x760 |
| Mater-National (2007) | `RC2E78`, `RC2P78`, `RC2X78`, `RC2Y78` | 0, +0x130 (all PAL) |
| Race-O-Rama (2009) | `R6OE78`, `R6OP78`, `R6OX78` | 0, +0x50 (all PAL) |

All are disc version 0. The Redump names map to IDs as follows: "Europe (De,It)"
is `xxxY78` and "Europe (Fr,Nl)" is `xxxX78`, read from the discs themselves.
Earlier versions of this repo had those two swapped, labels and Classic
Controller codes both.

`tools/verify.py` checks the patch data against the retail `main.dol` of all
twelve releases (`CARS_DOLS=<dir with <ID>.dol>`).

## Memory layout

Hook bodies live in a section the patcher adds to `main.dol` at low memory, which
the games never touch after boot (`tools/layout.py`):

| Range | Use |
| :--- | :--- |
| `0x80001820-0x80002000` | Classic Controller hooks |
| `0x80002000-0x80002200` | Widescreen fix hooks (Cars) |
| `0x80002200-0x80002FC0` | GameCube controller hooks |
| `0x80002FC0-0x80002FD4` | SI poller state (probe time stamps, NOREP counters) |

A loader's own Gecko code handler also lives in this area, so the Gecko codes
should not be combined with a loader's cheat engine on a real Wii; the patched
disc and Riivolution are fine.

## Classic Controller, pitstop skip, widescreen fix

These are Vague Rant's Gecko codes (`src/cc/<ID>.txt`, `src/fov/<ID>.txt`, and
the one-line pitstop skip in `src/gen_pitstop.py`), turned into patch
operations so the same data can become a patched DOL, a Gecko list or a
Riivolution patch.

Fixes against the codes as posted:

- The Japanese Cars code's first button hook was `C22F6498`, the European
  address. On `RCAJ78` that is the middle of an unrelated store run; the
  instruction it means (`lhz r0,0(r4)` in `read_kpad_button`) is at
  `0x802F6B88`, the USA site plus Japan's `+0x760`.
- The `RCAX78` / `RCAY78` codes were swapped (see Releases).

The pitstop skip (`0x80062CAC`: `bne` → `b`) and both widescreen hook sites are
the same instruction in every Cars release; the widescreen code's two function
pointers are checked to be the same functions as USA's.

## GameCube controller

### Reading the pad

The SI hardware mirrors each port's answer into `SICnINBUFH/L`
(`0xCD006404/0xCD006408 + 12·n`): bit 31 error, bit 23 set in a pad's answer,
bits 29–16 the PAD buttons, then the stick bytes.

None of the three games links the SDK's `PAD` library. `SIInit` probes the four
ports once at boot and nothing ever enables auto-polling. Dolphin refreshes the
result registers anyway, a real Wii does not. So `src/gc_poll.s` hooks the
entry of `KPADRead` (called once per channel per frame) and does what
`PADRead` / `SIEnablePolling` would, following the console-tested Barrel Blast
poller:

- re-probes a port whose cached type (`Si+0x18+4n`) is not a confirmed
  standard pad with `SIGetType`, at most every 0.25 s per port;
- turns a NOREP that persists for ~10 frames into cached type 8, the only value
  that makes `SIGetType` probe again, so a re-plugged pad is found;
- writes the poll command `0x00400300` to every `SICnOUTBUF`, then `SISR` = WR |
  the error nibbles to latch it;
- sets the enable + copy-on-vblank bits in `SIPOLL` for confirmed pads only,
  and the same byte in si's shadow copy (`Si+4`), which the VI retrace writes
  back to `SIPOLL`.

The si state block `Si` and `SIGetType` are read from each DOL
(`gen_gc._si`): `SISetXY` is the only `stw rX,0x6430(rY)`, and `SIInit` calls
`SIGetType` four times in a row.

| | `Si` (USA) | `SIGetType` (USA) | `KPADRead` (USA) |
| :--- | :--- | :--- | :--- |
| Cars | `0x8049DFA0` | `0x8030A4EC` | `0x802F8568` |
| Mater-National | `0x80508B08` | `0x80306244` | `0x802F3868` |
| Race-O-Rama | `0x804E1CE0` | `0x80318120` | `0x803671D0` |

Every hook only uses a port that si's type cache marks as a confirmed standard
pad, whose answer has bit 31 clear and bit 23 set (`PADREAD` in
`src/gc_macros.s`). An unplugged port stops being polled, so its registers keep
the last answer; the type check keeps that from reading as a held pad.

Checked in Dolphin (Cars USA, pad in port 1, no Wii Remote): after boot si's
shadow holds `0x00F60288` (port 1 enabled with copy-on-vblank), port 1 is cached
as `0x09000000` and the empty ports as 8.

### Feeding the game

Port N feeds KPAD channel N. The pad makes the channel look like a Wii Remote
with a Classic Controller, so Vague Rant's Classic Controller code does the rest:

- **Cars, Mater-National:** in the KPAD read loop, around the call that turns a
  sample into acceleration data, the channel's extension type is set to 2 while
  a pad answers and the remote has no extension of its own; the sticks are
  written where a Classic Controller's go; the real type is put back before the
  call returns (`*_acc.s`, `*_restore.s`). The buttons are ORed in at the
  merge point of `read_kpad_button` (`*_buttons.s`).
- **Race-O-Rama:** the same, at both read loops, plus the game's own
  controller-type table: a bare remote with a pad is recorded as a Classic
  Controller (`ror_type.s`).

### Known limitation: a Wii Remote is still needed

KPAD only produces samples for a channel whose remote is connected
(`KPADRead` returns early for device type 253 / a negative channel state), and
Cars stops at "Press the + Button" with only a pad. Playing without any remote
would need WPAD-level faking (`WPADProbe`, the WPAD sample ring KPAD copies
from) for three KPAD versions plus each game's own connection checks.
