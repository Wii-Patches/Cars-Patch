#!/usr/bin/env python3
"""Generate all prebuilt feature definitions in tools/prebuilt/*.json."""
import json
import os
import sys
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

from dol import Dol
from ops import Patch, Hook, Blob, Feature
from layout import CC_BASE, GC_BASE, DATA_BASE
import gecko
import asm
from regions import GAMES, ALL_REGIONS
from features import PREBUILT, dump

# Load raw codes
raw_path = os.path.join(HERE, '..', 'work', 'raw_vague_codes.json')
with open(raw_path) as f:
    db = json.load(f)

# DOL paths for reference
REF_DOLS = {
    'RCAE78': os.path.join(HERE, '..', 'work', 'extracted_RCAE78', 'DATA', 'sys', 'main.dol'),
    'RC2E78': os.path.join(HERE, '..', 'work', 'extracted_RC2E78', 'DATA', 'sys', 'main.dol'),
    'R6OE78': os.path.join(HERE, '..', 'work', 'extracted_R6OE78', 'DATA', 'sys', 'main.dol'),
}

def build_cars1_for_region(region_id, tab_name):
    # Determine reference DOL
    ref_dol_path = REF_DOLS.get(region_id, REF_DOLS['RCAE78'])
    dol = Dol(ref_dol_path)

    tab_data = db['cars1'][tab_name]
    cc_text = tab_data['cc']
    fov_text = tab_data['fov']
    ps_text = db['cars1_pitstop']

    # 1. Classic Controller
    cc_parsed = gecko.parse(cc_text)
    cc_ops = []
    tramp = CC_BASE
    for kind, addr, val in cc_parsed:
        if kind == '04':
            cur = dol.read(addr, 4)
            new = struct.pack('>I', val[0])
            cc_ops.append(Patch(addr, new, cur, 'Classic Controller 04 patch'))
        elif kind == '06':
            cur = dol.read(addr, len(val))
            cc_ops.append(Patch(addr, val, cur, 'Classic Controller 06 patch'))
        elif kind == 'C2':
            cur = struct.unpack('>I', dol.read(addr, 4))[0]
            cc_ops.append(Hook(addr, cur, val + [0], tramp, 'Classic Controller hook'))
            tramp += (len(val) + 1) * 4
            if tramp % 8 != 0:
                tramp += 4
    feat_cc = Feature('cc', 'Classic Controller Support', region_id, cc_ops)

    # 2. Skip Pitstop Motions
    ps_parsed = gecko.parse(ps_text)
    ps_addr = ps_parsed[0][1]
    ps_val = ps_parsed[0][2][0]
    ps_cur = dol.read(ps_addr, 4)
    ps_new = struct.pack('>I', ps_val)
    feat_ps = Feature('pitstop', 'Skip Pitstop Motions', region_id, [Patch(ps_addr, ps_new, ps_cur, 'Skip Pitstop Motions')])

    # 3. Fix Widescreen FOV
    fov_parsed = gecko.parse(fov_text)
    fov_ops = []
    for kind, addr, val in fov_parsed:
        cur = struct.unpack('>I', dol.read(addr, 4))[0]
        fov_ops.append(Hook(addr, cur, val + [0], tramp, 'Widescreen FOV hook'))
        tramp += (len(val) + 1) * 4
        if tramp % 8 != 0:
            tramp += 4
    feat_fov = Feature('fov', 'Fix Widescreen FOV', region_id, fov_ops)

    # 4. GameCube Controller Support (Standalone)
    # GC Probe Hook (WPADProbe: cmpwi r30, 0)
    gc_probe_site = 0x803131ec
    if region_id == 'RCAP78' or region_id == 'RCAX78':
        gc_probe_site = 0x80313240
    elif region_id == 'RCAY78':
        gc_probe_site = 0x80313244
    elif region_id == 'RCAJ78':
        gc_probe_site = 0x80313938

    gc_probe_src = """
        lwz     0, 2044(31)
        cmpwi   0, 0
        beq     1f

        lis     5, 0xCD00
        lwz     6, 0x6404(5)
        cmpwi   6, 0
        blt     1f
        andis.  7, 6, 0x0080
        beq     1f

        li      0, 0
        stw     0, 2044(31)
        li      0, 2
        stb     0, 2049(31)
    1:
        cmpwi   30, 0
    """
    probe_words = asm.words(asm.assemble(gc_probe_src, GC_BASE)) + [0]
    probe_cur = struct.unpack('>I', dol.read(gc_probe_site, 4))[0]
    gc_tramp = GC_BASE
    hook_probe = Hook(gc_probe_site, probe_cur, probe_words, gc_tramp, 'GC Controller probe hook')
    gc_tramp += len(probe_words) * 4
    if gc_tramp % 8 != 0:
        gc_tramp += 4

    # GC Sample Hook (KPADRead epilogue: mr r3, r23)
    gc_sample_site = 0x802F8954
    if region_id == 'RCAP78' or region_id == 'RCAX78':
        gc_sample_site = 0x802F89C4
    elif region_id == 'RCAY78':
        gc_sample_site = 0x802F89C4
    elif region_id == 'RCAJ78':
        gc_sample_site = 0x802F9054

    gc_sample_src = f"""
    .macro MAP src, dst
        andi.   11, 9, \\src
        beq     1f
        ori     10, 10, \\dst
    1:
    .endm

        cmpwi   23, 0
        bgt     orig_done

        mulli   4, 22, 12
        lis     5, 0xCD00
        add     5, 5, 4
        lwz     8, 0x6404(5)
        cmpwi   8, 0
        blt     orig_done
        andis.  9, 8, 0x0080
        beq     orig_done

        li      0, 0
        stb     0, 0x85(26)
        stb     0, 0x85(29)

        li      0, 2
        stw     0, 0x5C(26)
        stw     0, 0x5C(29)

        srwi    9, 8, 16
        li      10, 0

        MAP     0x0100, 0x0010
        MAP     0x0200, 0x0040
        MAP     0x0400, 0x0008
        MAP     0x0800, 0x0020
        MAP     0x1000, 0x0400
        MAP     0x0010, 0x0004
        MAP     0x0020, 0x0200
        MAP     0x0040, 0x2000
        MAP     0x0008, 0x0081
        MAP     0x0004, 0x4000
        MAP     0x0001, 0x0002
        MAP     0x0002, 0x8000

        lwz     12, 0x6408(5)

        rlwinm  4, 12, 16, 24, 31
        addi    4, 4, -128
        srawi   6, 4, 31
        xor     4, 4, 6
        subf    4, 6, 4
        cmpwi   4, 35
        bgt     do_jump

        rlwinm  4, 12, 24, 24, 31
        addi    4, 4, -128
        srawi   6, 4, 31
        xor     4, 4, 6
        subf    4, 6, 4
        cmpwi   4, 35
        ble     skip_jump

    do_jump:
        ori     10, 10, 0x0080

    skip_jump:
        stw     10, 0x60(26)
        stw     10, 0x60(29)

        slwi    7, 22, 2
        lis     6, 0x{DATA_BASE >> 16:04X}
        ori     6, 6, 0x{DATA_BASE & 0xFFFF:04X}
        lwzx    4, 6, 7
        andc    5, 10, 4
        stw     5, 0x64(26)
        stw     5, 0x64(29)
        andc    5, 4, 10
        stw     5, 0x68(26)
        stw     5, 0x68(29)
        stwx    10, 6, 7

        rlwinm  4, 8, 24, 24, 31
        addi    4, 4, -128
        mulli   4, 4, 3
        sth     4, 0x6C(26)
        sth     4, 0x6C(29)

        rlwinm  4, 12, 8, 24, 31
        addi    4, 4, -128
        mulli   4, 4, 3
        sth     4, 0x6E(26)
        sth     4, 0x6E(29)

        li      0, 0
        stw     0, 0x14(26)
        stw     0, 0x14(29)
        lis     0, 0x3F80
        stw     0, 0x18(26)
        stw     0, 0x18(29)
        li      0, 0
        stw     0, 0x1C(26)
        stw     0, 0x1C(29)

        li      23, 1

    orig_done:
        mr      3, 23
    """
    sample_words = asm.words(asm.assemble(gc_sample_src, gc_tramp)) + [0]
    sample_cur = struct.unpack('>I', dol.read(gc_sample_site, 4))[0]
    hook_sample = Hook(gc_sample_site, sample_cur, sample_words, gc_tramp, 'GC Controller sample hook')
    blob_data = Blob(DATA_BASE, bytes(32), 'GC per-channel state')
    feat_gc = Feature('gc', 'GameCube Controller Support (Standalone)', region_id, [hook_probe, hook_sample, blob_data])

    return [feat_cc, feat_ps, feat_fov, feat_gc]

def build_cars2_for_region(region_id, tab_name):
    ref_dol_path = REF_DOLS.get(region_id, REF_DOLS['RC2E78'])
    dol = Dol(ref_dol_path)

    tab_data = db['cars2'][tab_name]
    cc_text = tab_data['cc']

    cc_parsed = gecko.parse(cc_text)
    cc_ops = []
    tramp = CC_BASE
    for kind, addr, val in cc_parsed:
        if kind == '04':
            cur = dol.read(addr, 4)
            new = struct.pack('>I', val[0])
            cc_ops.append(Patch(addr, new, cur, 'Classic Controller 04 patch'))
        elif kind == '06':
            cur = dol.read(addr, len(val))
            cc_ops.append(Patch(addr, val, cur, 'Classic Controller 06 patch'))
        elif kind == 'C2':
            cur = struct.unpack('>I', dol.read(addr, 4))[0]
            cc_ops.append(Hook(addr, cur, val + [0], tramp, 'Classic Controller hook'))
            tramp += (len(val) + 1) * 4
            if tramp % 8 != 0:
                tramp += 4
    feat_cc = Feature('cc', 'Classic Controller Support', region_id, cc_ops)

    # GC Controller for Cars 2
    gc_probe_site = 0x80340A00 if region_id != 'RC2E78' else 0x8033F53C
    # In RC2E78, WPADProbe is at 0x8033F510, type cmpwi r30, 0 is at 0x8033F53C
    gc_probe_src = """
        lwz     0, 2044(31)
        cmpwi   0, 0
        beq     1f

        lis     5, 0xCD00
        lwz     6, 0x6404(5)
        cmpwi   6, 0
        blt     1f
        andis.  7, 6, 0x0080
        beq     1f

        li      0, 0
        stw     0, 2044(31)
        li      0, 2
        stb     0, 2049(31)
    1:
        cmpwi   30, 0
    """
    probe_words = asm.words(asm.assemble(gc_probe_src, GC_BASE)) + [0]
    probe_cur = struct.unpack('>I', dol.read(gc_probe_site, 4))[0]
    gc_tramp = GC_BASE
    hook_probe = Hook(gc_probe_site, probe_cur, probe_words, gc_tramp, 'GC Controller probe hook')
    gc_tramp += len(probe_words) * 4
    if gc_tramp % 8 != 0:
        gc_tramp += 4

    gc_sample_site = 0x80324888 if region_id != 'RC2E78' else 0x803233C4
    gc_sample_src = f"""
    .macro MAP src, dst
        andi.   11, 9, \\src
        beq     1f
        ori     10, 10, \\dst
    1:
    .endm

        cmpwi   23, 0
        bgt     orig_done

        mulli   4, 22, 12
        lis     5, 0xCD00
        add     5, 5, 4
        lwz     8, 0x6404(5)
        cmpwi   8, 0
        blt     orig_done
        andis.  9, 8, 0x0080
        beq     orig_done

        li      0, 0
        stb     0, 0x85(26)
        stb     0, 0x85(29)

        li      0, 2
        stw     0, 0x5C(26)
        stw     0, 0x5C(29)

        srwi    9, 8, 16
        li      10, 0

        MAP     0x0100, 0x0010
        MAP     0x0200, 0x0040
        MAP     0x0400, 0x0008
        MAP     0x0800, 0x0020
        MAP     0x1000, 0x0400
        MAP     0x0010, 0x0004
        MAP     0x0020, 0x0200
        MAP     0x0040, 0x2000
        MAP     0x0008, 0x0081
        MAP     0x0004, 0x4000
        MAP     0x0001, 0x0002
        MAP     0x0002, 0x8000

        lwz     12, 0x6408(5)

        rlwinm  4, 12, 16, 24, 31
        addi    4, 4, -128
        srawi   6, 4, 31
        xor     4, 4, 6
        subf    4, 6, 4
        cmpwi   4, 35
        bgt     do_jump

        rlwinm  4, 12, 24, 24, 31
        addi    4, 4, -128
        srawi   6, 4, 31
        xor     4, 4, 6
        subf    4, 6, 4
        cmpwi   4, 35
        ble     skip_jump

    do_jump:
        ori     10, 10, 0x0080

    skip_jump:
        stw     10, 0x60(26)
        stw     10, 0x60(29)

        slwi    7, 22, 2
        lis     6, 0x{DATA_BASE >> 16:04X}
        ori     6, 6, 0x{DATA_BASE & 0xFFFF:04X}
        lwzx    4, 6, 7
        andc    5, 10, 4
        stw     5, 0x64(26)
        stw     5, 0x64(29)
        andc    5, 4, 10
        stw     5, 0x68(26)
        stw     5, 0x68(29)
        stwx    10, 6, 7

        rlwinm  4, 8, 24, 24, 31
        addi    4, 4, -128
        mulli   4, 4, 3
        sth     4, 0x6C(26)
        sth     4, 0x6C(29)

        rlwinm  4, 12, 8, 24, 31
        addi    4, 4, -128
        mulli   4, 4, 3
        sth     4, 0x6E(26)
        sth     4, 0x6E(29)

        li      0, 0
        stw     0, 0x14(26)
        stw     0, 0x14(29)
        lis     0, 0x3F80
        stw     0, 0x18(26)
        stw     0, 0x18(29)
        li      0, 0
        stw     0, 0x1C(26)
        stw     0, 0x1C(29)

        li      23, 1

    orig_done:
        mr      3, 23
    """
    sample_words = asm.words(asm.assemble(gc_sample_src, gc_tramp)) + [0]
    sample_cur = struct.unpack('>I', dol.read(gc_sample_site, 4))[0]
    hook_sample = Hook(gc_sample_site, sample_cur, sample_words, gc_tramp, 'GC Controller sample hook')
    blob_data = Blob(DATA_BASE, bytes(32), 'GC per-channel state')
    feat_gc = Feature('gc', 'GameCube Controller Support (Standalone)', region_id, [hook_probe, hook_sample, blob_data])

    return [feat_cc, feat_gc]

def build_cars3_for_region(region_id, tab_name):
    ref_dol_path = REF_DOLS.get(region_id, REF_DOLS['R6OE78'])
    dol = Dol(ref_dol_path)

    tab_data = db['cars3'][tab_name]
    cc_text = tab_data['cc']

    cc_parsed = gecko.parse(cc_text)
    cc_ops = []
    tramp = CC_BASE
    for kind, addr, val in cc_parsed:
        if kind == '04':
            cur = dol.read(addr, 4)
            new = struct.pack('>I', val[0])
            cc_ops.append(Patch(addr, new, cur, 'Classic Controller 04 patch'))
        elif kind == '06':
            cur = dol.read(addr, len(val))
            cc_ops.append(Patch(addr, val, cur, 'Classic Controller 06 patch'))
        elif kind == 'C2':
            cur = struct.unpack('>I', dol.read(addr, 4))[0]
            cc_ops.append(Hook(addr, cur, val + [0], tramp, 'Classic Controller hook'))
            tramp += (len(val) + 1) * 4
            if tramp % 8 != 0:
                tramp += 4
    feat_cc = Feature('cc', 'Classic Controller Support', region_id, cc_ops)

    # GC Controller for Cars 3
    gc_probe_site = 0x803C5C70 if region_id != 'R6OE78' else 0x803C4B30
    gc_probe_src = """
        lwz     0, 2044(31)
        cmpwi   0, 0
        beq     1f

        lis     5, 0xCD00
        lwz     6, 0x6404(5)
        cmpwi   6, 0
        blt     1f
        andis.  7, 6, 0x0080
        beq     1f

        li      0, 0
        stw     0, 2044(31)
        li      0, 2
        stb     0, 2049(31)
    1:
        cmpwi   30, 0
    """
    probe_words = asm.words(asm.assemble(gc_probe_src, GC_BASE)) + [0]
    probe_cur = struct.unpack('>I', dol.read(gc_probe_site, 4))[0]
    gc_tramp = GC_BASE
    hook_probe = Hook(gc_probe_site, probe_cur, probe_words, gc_tramp, 'GC Controller probe hook')
    gc_tramp += len(probe_words) * 4
    if gc_tramp % 8 != 0:
        gc_tramp += 4

    gc_sample_site = 0x80381664 if region_id != 'R6OE78' else 0x80380524
    gc_sample_src = f"""
    .macro MAP src, dst
        andi.   11, 9, \\src
        beq     1f
        ori     10, 10, \\dst
    1:
    .endm

        cmpwi   23, 0
        bgt     orig_done

        mulli   4, 22, 12
        lis     5, 0xCD00
        add     5, 5, 4
        lwz     8, 0x6404(5)
        cmpwi   8, 0
        blt     orig_done
        andis.  9, 8, 0x0080
        beq     orig_done

        li      0, 0
        stb     0, 0x85(26)
        stb     0, 0x85(29)

        li      0, 2
        stw     0, 0x5C(26)
        stw     0, 0x5C(29)

        srwi    9, 8, 16
        li      10, 0

        MAP     0x0100, 0x0010
        MAP     0x0200, 0x0040
        MAP     0x0400, 0x0008
        MAP     0x0800, 0x0020
        MAP     0x1000, 0x0400
        MAP     0x0010, 0x0004
        MAP     0x0020, 0x0200
        MAP     0x0040, 0x2000
        MAP     0x0008, 0x0081
        MAP     0x0004, 0x4000
        MAP     0x0001, 0x0002
        MAP     0x0002, 0x8000

        lwz     12, 0x6408(5)

        rlwinm  4, 12, 16, 24, 31
        addi    4, 4, -128
        srawi   6, 4, 31
        xor     4, 4, 6
        subf    4, 6, 4
        cmpwi   4, 35
        bgt     do_jump

        rlwinm  4, 12, 24, 24, 31
        addi    4, 4, -128
        srawi   6, 4, 31
        xor     4, 4, 6
        subf    4, 6, 4
        cmpwi   4, 35
        ble     skip_jump

    do_jump:
        ori     10, 10, 0x0080

    skip_jump:
        stw     10, 0x60(26)
        stw     10, 0x60(29)

        slwi    7, 22, 2
        lis     6, 0x{DATA_BASE >> 16:04X}
        ori     6, 6, 0x{DATA_BASE & 0xFFFF:04X}
        lwzx    4, 6, 7
        andc    5, 10, 4
        stw     5, 0x64(26)
        stw     5, 0x64(29)
        andc    5, 4, 10
        stw     5, 0x68(26)
        stw     5, 0x68(29)
        stwx    10, 6, 7

        rlwinm  4, 8, 24, 24, 31
        addi    4, 4, -128
        mulli   4, 4, 3
        sth     4, 0x6C(26)
        sth     4, 0x6C(29)

        rlwinm  4, 12, 8, 24, 31
        addi    4, 4, -128
        mulli   4, 4, 3
        sth     4, 0x6E(26)
        sth     4, 0x6E(29)

        li      0, 0
        stw     0, 0x14(26)
        stw     0, 0x14(29)
        lis     0, 0x3F80
        stw     0, 0x18(26)
        stw     0, 0x18(29)
        li      0, 0
        stw     0, 0x1C(26)
        stw     0, 0x1C(29)

        li      23, 1

    orig_done:
        mr      3, 23
    """
    sample_words = asm.words(asm.assemble(gc_sample_src, gc_tramp)) + [0]
    sample_cur = struct.unpack('>I', dol.read(gc_sample_site, 4))[0]
    hook_sample = Hook(gc_sample_site, sample_cur, sample_words, gc_tramp, 'GC Controller sample hook')
    blob_data = Blob(DATA_BASE, bytes(32), 'GC per-channel state')
    feat_gc = Feature('gc', 'GameCube Controller Support (Standalone)', region_id, [hook_probe, hook_sample, blob_data])

    return [feat_cc, feat_gc]

def main():
    os.makedirs(PREBUILT, exist_ok=True)
    count = 0
    for reg_id, meta in ALL_REGIONS.items():
        game = meta['game']
        tab = meta['tab']
        if game == 'cars1':
            feats = build_cars1_for_region(reg_id, tab)
        elif game == 'cars2':
            feats = build_cars2_for_region(reg_id, tab)
        elif game == 'cars3':
            feats = build_cars3_for_region(reg_id, tab)

        for feat in feats:
            out_file = os.path.join(PREBUILT, f"{feat.name}_{reg_id}.json")
            with open(out_file, 'w') as fh:
                json.dump(dump(feat), fh, indent=2)
                fh.write('\n')
            count += 1
            print(f"Generated {feat.name:8s} {reg_id}: {len(feat.ops):2d} ops -> {os.path.basename(out_file)}")

    print(f"\nGenerated total of {count} prebuilt JSON definition files!")

if __name__ == '__main__':
    main()
