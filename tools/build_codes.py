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
    # Riivolution matches one game ID (+ disc version) per XML, so emit one
    # file per retail release; patches only contain that release's addresses.
    for f in os.listdir(RIIV_DIR):
        if f.endswith('.xml'):
            os.remove(os.path.join(RIIV_DIR, f))
    for gkey, ginfo in GAMES.items():
        for reg, rinfo in ginfo['regions'].items():
            feats = [k for k in ginfo['features'] if features.available(k, reg)]
            xml_path = os.path.join(RIIV_DIR, f"{reg}.xml")
            lines = [
                f'<!-- {rinfo["label"]}: patches by quatric -->',
                '<wiidisc version="1" root="/">',
                f'  <id game="{reg}" version="{rinfo["version"]}" />',
                '  <options>',
                f'    <section name="{rinfo["label"]}">',
            ]
            for fkey in feats:
                lines += [f'      <option name="{features.TITLES[fkey]}" default="1">',
                          f'        <choice name="Enabled"><patch id="{fkey}" /></choice>',
                          '      </option>']
            lines += ['    </section>', '  </options>']
            for fkey in feats:
                feat = features.load(fkey, reg)
                lines.append(f'  <patch id="{fkey}">')
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
