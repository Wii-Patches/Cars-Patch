#!/usr/bin/env python3
"""Generate Gecko code lists (.txt and Dolphin .ini) and Riivolution XML files."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import features
from regions import ALL_REGIONS, GAMES

CODES_DIR = os.path.join(HERE, '..', 'codes')
RIIV_DIR = os.path.join(HERE, '..', 'riivolution')

os.makedirs(CODES_DIR, exist_ok=True)
os.makedirs(RIIV_DIR, exist_ok=True)

def generate_gecko_for_region(region_id):
    meta = ALL_REGIONS[region_id]
    game = meta['game']
    game_title = meta['game_title']
    valid_feats = meta.get('features', ())

    # 1. Plain text format
    txt_path = os.path.join(CODES_DIR, f"{region_id}.txt")
    lines = [
        f"{game_title} ({meta['short']}) [{region_id}]",
        "Classic Controller + GameCube Controller Code Suite",
        ""
    ]
    for feat_name in valid_feats:
        if features.available(feat_name, region_id):
            feat = features.load(feat_name, region_id)
            lines.append(f"{feat.title} [{region_id}]")
            for gl in feat.gecko_lines():
                lines.append(gl)
            lines.append("")

    with open(txt_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    # 2. Dolphin INI format
    ini_path = os.path.join(CODES_DIR, f"{region_id}.ini")
    ini_lines = [
        f"# {game_title} ({meta['short']}) - [{region_id}]",
        "[Gecko]",
    ]
    for feat_name in valid_feats:
        if features.available(feat_name, region_id):
            feat = features.load(feat_name, region_id)
            ini_lines.append(f"${feat.title}")
            for gl in feat.gecko_lines():
                if not gl.startswith('*'):
                    ini_lines.append(gl)
    ini_lines.append("")
    ini_lines.append("[Gecko_Enabled]")
    for feat_name in valid_feats:
        if feat_name in ('cc', 'gc') and features.available(feat_name, region_id):
            feat = features.load(feat_name, region_id)
            ini_lines.append(f"${feat.title}")

    with open(ini_path, 'w') as f:
        f.write('\n'.join(ini_lines) + '\n')

def generate_riivolution():
    # Generate unified Riivolution XML for each game in the trilogy
    for gkey, ginfo in GAMES.items():
        xml_path = os.path.join(RIIV_DIR, f"{gkey}.xml")
        lines = [
            '<wiidisc version="1">',
            f'  <id game="{gkey}">',
        ]
        for reg in ginfo['regions']:
            lines.append(f'    <region type="{reg[:3]}" />')
        lines.append('  </id>')
        lines.append(f'  <options>')
        lines.append(f'    <section name="{ginfo["title"]} Patch">')

        for fkey in ginfo['features']:
            lines.append(f'      <option name="{features.TITLES[fkey]}">')
            lines.append(f'        <choice name="Enabled">')
            lines.append(f'          <patch id="{fkey}" />')
            lines.append(f'        </choice>')
            lines.append(f'      </option>')

        lines.append('    </section>')
        lines.append('  </options>')

        for fkey in ginfo['features']:
            lines.append(f'  <patch id="{fkey}">')
            for reg in ginfo['regions']:
                if features.available(fkey, reg):
                    feat = features.load(fkey, reg)
                    lines.append(f'    <!-- {reg}: {feat.title} -->')
                    for el in feat.memory_elements():
                        lines.append(f'    {el}')
            lines.append('  </patch>')

        lines.append('</wiidisc>')
        with open(xml_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"Generated Riivolution XML: {os.path.basename(xml_path)}")

def main():
    for reg_id in ALL_REGIONS:
        generate_gecko_for_region(reg_id)
        print(f"Generated Gecko codes for {reg_id}")
    generate_riivolution()
    print("Done building codes and riivolution files!")

if __name__ == '__main__':
    main()
