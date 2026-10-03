"""The retail releases of the Disney-Pixar Cars trilogy on Wii.

Cars 1 (2006):
  - RCAE78: USA
  - RCAP78: Europe (UK / Australia / International)
  - RCAX78: Europe (En, Es, De, It)
  - RCAY78: Europe (Fr, Nl)
  - RCAJ78: Japan

Cars: Mater-National Championship (2007):
  - RC2E78: USA
  - RC2P78: Europe (UK / Australia / International)
  - RC2X78: Europe (En, Es, De, It)
  - RC2Y78: Europe (Fr, Nl)

Cars Race-O-Rama (2009):
  - R6OE78: USA
  - R6OP78: Europe (UK / Australia / International)
  - R6OX78: Europe (Fr, De, It, Es)
"""

GAMES = {
    'cars1': {
        'title': 'Disney-Pixar Cars',
        'year': 2006,
        'features': ('cc', 'gc', 'pitstop', 'fov'),
        'regions': {
            'RCAE78': dict(label='Cars (USA)', short='USA', version=0,
                           dol_md5='ea70e2a8f799cde13ea3b33cf95bf352', tab='USA'),
            'RCAP78': dict(label='Cars (Europe: UK, Australia)', short='EUR (En,Es)', version=0,
                           dol_md5=None, tab='EUR (En,Es) / EUR (De,It)'),
            'RCAX78': dict(label='Cars (Europe: De, It)', short='EUR (De,It)', version=0,
                           dol_md5=None, tab='EUR (En,Es) / EUR (De,It)'),
            'RCAY78': dict(label='Cars (Europe: Fr, Nl)', short='EUR (Fr,Nl)', version=0,
                           dol_md5=None, tab='EUR (Fr,Nl)'),
            'RCAJ78': dict(label='Cars (Japan)', short='JPN', version=0,
                           dol_md5=None, tab='JPN'),
        }
    },
    'cars2': {
        'title': 'Disney-Pixar Cars: Mater-National Championship',
        'year': 2007,
        'features': ('cc', 'gc'),
        'regions': {
            'RC2E78': dict(label='Cars: Mater-National (USA)', short='USA', version=0,
                           dol_md5='1a33e25bfc972e68531f070091a687c2', tab='USA'),
            'RC2P78': dict(label='Cars: Mater-National (Europe)', short='EUR', version=0,
                           dol_md5=None, tab='EUR'),
            'RC2X78': dict(label='Cars: Mater-National (Europe: X)', short='EUR', version=0,
                           dol_md5=None, tab='EUR'),
            'RC2Y78': dict(label='Cars: Mater-National (Europe: Y)', short='EUR', version=0,
                           dol_md5=None, tab='EUR'),
        }
    },
    'cars3': {
        'title': 'Disney-Pixar Cars Race-O-Rama',
        'year': 2009,
        'features': ('cc', 'gc'),
        'regions': {
            'R6OE78': dict(label='Cars Race-O-Rama (USA)', short='USA', version=0,
                           dol_md5='e391de5822b26976a8757c56314806cd', tab='USA'),
            'R6OP78': dict(label='Cars Race-O-Rama (Europe)', short='EUR', version=0,
                           dol_md5=None, tab='EUR'),
            'R6OX78': dict(label='Cars Race-O-Rama (Europe: X)', short='EUR', version=0,
                           dol_md5=None, tab='EUR'),
        }
    }
}

ALL_REGIONS = {}
for gkey, ginfo in GAMES.items():
    for rkey, rinfo in ginfo['regions'].items():
        entry = dict(rinfo)
        entry['game'] = gkey
        entry['game_title'] = ginfo['title']
        entry['features'] = ginfo['features']
        ALL_REGIONS[rkey] = entry

def game_for_region(region_id):
    return ALL_REGIONS.get(region_id, {}).get('game')

