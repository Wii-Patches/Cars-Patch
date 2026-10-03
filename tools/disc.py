"""Patch a whole Cars trilogy disc image: extract with wit, patch sys/main.dol, rebuild.

The rebuilt image replaces the original in place, keeping its filename and
folder (USB loaders key off the `/wbfs/<Title> [ID6]/` layout); the untouched
original is kept next to it as `<name>.bak`.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import features
import patcher
from dol import Dol
from regions import ALL_REGIONS, GAMES


def find_wit():
    """Locate wiimms ISO Tool (wit). Bundled binary wins over PATH."""
    name = 'wit.exe' if os.name == 'nt' else 'wit'
    if getattr(sys, 'frozen', False):
        for base in (getattr(sys, '_MEIPASS', None), os.path.dirname(sys.executable)):
            if base:
                bundled = os.path.join(base, name)
                if os.path.isfile(bundled):
                    return bundled
    return shutil.which('wit')


def find_file(root, name):
    for r, _, files in os.walk(root):
        if name in files:
            return os.path.join(r, name)
    return None


def read_disc_id(fst):
    boot = find_file(fst, 'boot.bin')
    if not boot:
        return None
    with open(boot, 'rb') as f:
        header = f.read(8)
    return header[0:6].decode('ascii', 'replace'), header[7]


def run_patch(image_path, log, done, which=('cc', 'gc', 'pitstop', 'fov'), ios=None, dest=None):
    """Patch `image_path` in place or to `dest`."""
    try:
        wit = find_wit()
        if wit is None:
            raise RuntimeError('wit (Wiimms ISO Tool) not found: not bundled with this build and not on PATH')

        fmt = '--iso' if (dest or image_path).lower().endswith('.iso') else '--wbfs'

        with tempfile.TemporaryDirectory(prefix='cars_patch_') as tmp:
            fst = os.path.join(tmp, 'fst')
            log('extracting %s...' % os.path.basename(image_path))
            r = subprocess.run([wit, 'extract', image_path, '--dest', fst, '--psel', 'data',
                                '--overwrite', '-q'], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError('extract failed:\n' + (r.stderr or r.stdout))

            got = read_disc_id(fst)
            if not got:
                raise RuntimeError('could not read sys/boot.bin from the extracted disc')
            disc_id, disc_ver = got
            if disc_id not in ALL_REGIONS:
                raise RuntimeError('%s is not a recognized Cars trilogy release.\n\n'
                                   'Supported:\n%s' % (disc_id, '\n'.join(
                                       '  %s: %s' % (k, v['label']) for k, v in ALL_REGIONS.items())))

            region = disc_id
            reg_info = ALL_REGIONS[region]
            log('disc: %s (%s)' % (region, reg_info['label']))

            dol_path = find_file(fst, 'main.dol')
            if not dol_path or os.path.basename(os.path.dirname(dol_path)) != 'sys':
                raise RuntimeError('could not find sys/main.dol in the extracted disc')
            dol = Dol(dol_path)

            have = patcher.status(dol, region)
            valid_feats = reg_info.get('features', patcher.ORDER)
            selected = [w for w in valid_feats if w in which]
            if not selected:
                raise RuntimeError('no applicable patches selected for this title')

            todo = []
            for name in selected:
                st = have.get(name)
                if st == 'patched':
                    log('  %s is already applied in this disc' % features.TITLES[name])
                elif st == 'clean':
                    todo.append(name)
                else:
                    raise RuntimeError('main.dol does not match clean retail %s (%s): already modified '
                                       'or bad dump. Refusing to patch.'
                                       % (reg_info['label'], features.TITLES[name]))

            want_ios = ios is not None and ios != _disc_ios(wit, image_path)
            if not todo and not want_ios:
                raise RuntimeError('nothing left to add: selected patches are already in this disc.')

            if todo:
                applied = patcher.patch(dol, region, todo)
                for t in applied:
                    log('  added %s' % t)
                dol.save(dol_path)
                log('  saved patched main.dol')

            staged = os.path.join(tmp, 'patched.img')
            log('rebuilding disc image...')
            cmd = [wit, 'copy', fst, '--dest', staged, fmt, '--overwrite', '-q']
            if ios is not None:
                cmd += ['--ios', str(ios)]
                log('  setting disc IOS to %d' % ios)
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError('rebuild failed:\n' + (r.stderr or r.stdout))

            if dest:
                shutil.move(staged, dest)
                log('done: wrote %s' % dest)
                done(True, dest)
                return

            backup = image_path + '.bak'
            if os.path.exists(backup):
                log('  backup already exists, keeping it: %s' % os.path.basename(backup))
            else:
                shutil.copyfile(image_path, backup)
                log('  backed up original -> %s' % os.path.basename(backup))
            shutil.move(staged, image_path)
            log('done: patched in place, %s' % os.path.basename(image_path))
            done(True, image_path)
    except Exception as e:
        log('ERROR: %s' % e)
        done(False, str(e))


def _disc_ios(wit, image_path):
    try:
        out = subprocess.run([wit, 'dump', image_path], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if 'System version:' in line and 'IOS' in line:
                return int(line.rsplit('IOS', 1)[1].split()[0], 0)
    except Exception:
        pass
    return None

