#!/usr/bin/env python3
"""Build and export production @Previews offscreen, with an explicit legacy Studio backend."""
import argparse
import getpass
import hashlib
import json
from pathlib import Path
import re
import shutil
import signal
import os
import subprocess
import tempfile
import time


def png_size(path):
    from PIL import Image
    with Image.open(path) as image:
        if image.format != 'PNG':
            raise ValueError('Renderer did not produce a PNG')
        image.verify()
    with Image.open(path) as image:
        image.load()  # Decode pixel data, not just chunks/checksums.
        if image.width <= 0 or image.height <= 0:
            raise ValueError('Empty PNG')
        return image.size


def acquire_lock(path):
    handle = path.open('a+b')
    try:
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return handle
    except Exception:
        handle.close()
        raise RuntimeError('Another Preview exporter owns the Studio lock; wait for it to finish')


def exact_ready(output, project):
    # CLI columns: READY <display name> <absolute project path>. Match the full
    # trailing path with a preceding column boundary, not a path substring.
    expected = str(project)
    return any(re.match(r'^\s*READY\s+', line) and
               re.search(r'\s+' + re.escape(expected) + r'\s*$', line)
               for line in output.splitlines())


def input_snapshot(roots, output):
    result = {}
    excluded = {'.git', '.gradle', '.idea', '.kotlin', '.cxx', '__pycache__', 'node_modules', '.venv'}
    for root in roots:
        for directory, dirs, files in os.walk(root):
            here = Path(directory)
            dirs[:] = [name for name in dirs if name not in excluded
                       and not (name == 'build' and 'src' not in here.relative_to(root).parts)
                       and not (here/name).resolve().is_relative_to(output)]
            for name in files:
                path = here/name
                if path.resolve().is_relative_to(output):
                    continue
                result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def run_logged(command, log_path, timeout, cwd=None):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, cwd=cwd, start_new_session=os.name != 'nt')
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # The headless CLI can launch builds/renderers. Stop our own process
        # group on POSIX, rather than leaving a build running after timeout.
        if os.name != 'nt':
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name != 'nt':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            stdout, stderr = process.communicate()
        log_path.write_text(stdout + stderr)
        raise RuntimeError('Command timed out; partial output saved in ' + log_path.name)
    log_path.write_text(stdout + stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def headless_output(stdout):
    # CLI progress can precede the structured result. Accept only a final object
    # with the documented result envelope, never an arbitrary success log line.
    decoder = json.JSONDecoder()
    for match in re.finditer(r"(?m)^\s*\{", stdout):
        try:
            value, end = decoder.raw_decode(stdout, match.end() - 1)
        except ValueError:
            continue
        if not stdout[end:].strip() and isinstance(value, dict) and isinstance(value.get('results'), list) and 'success' in value:
            return value
    raise RuntimeError('No structured Preview result; inspect renderer.txt')


def render_headless(args, cli, project, out, record):
    help_result = run_logged([cli, 'preview', 'render', '--help'], out/'capability.txt', 30, project)
    if help_result.returncode or '--fqn' not in help_result.stdout or '--format' not in help_result.stdout:
        raise RuntimeError('This Android CLI lacks headless preview render. Update the full CLI runtime and verify preview render --help; replacing only its launcher can retain an old cached runtime. No GUI fallback was attempted.')
    reference = args.reference or ('gradle://' + str(project) + '?' + args.module)
    record.update(backend='headless', ide_required=False, build_reference=reference,
                  build_arguments=args.build_arg, method_fqn=args.fqn)
    cmd = [cli] + (['--sdk=' + str(args.sdk.resolve())] if args.sdk else [])
    cmd += ['preview', 'render', reference, '--fqn=' + args.fqn,
            '--format=json', '--output=' + str(out/'images')]
    if args.component_tree:
        cmd.append('--component-tree')
    if args.build_arg:
        cmd += ['--'] + args.build_arg
    record['command'] = cmd
    run = run_logged(cmd, out/'renderer.txt', args.timeout, project)
    record['exit_code'] = run.returncode
    result = headless_output(run.stdout)
    (out/'renderer-result.json').write_text(json.dumps(result, indent=2)+'\n')
    if run.returncode or result['success'] is not True or result.get('globalError') or not result['results']:
        raise RuntimeError('Headless build/render failed or selected no Previews; inspect renderer-result.json and renderer.txt')
    images = []
    for item in result['results']:
        if item.get('error') or item.get('methodFqn') != args.fqn:
            raise RuntimeError('Preview failed or returned a different method; inspect renderer-result.json')
        image = Path(item.get('imagePath') or '').resolve()
        if not image.is_file() or not image.is_relative_to(out/'images'):
            raise RuntimeError('Renderer image is missing or outside this fresh attempt directory')
        entry = {'preview_id':item.get('previewId'), 'method_fqn':item['methodFqn'],
                 'image':str(image), 'pixels':png_size(image),
                 'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest()}
        if item.get('componentTreePath'):
            tree = Path(item['componentTreePath']).resolve()
            if not tree.is_file() or not tree.is_relative_to(out/'images'):
                raise RuntimeError('Component tree is missing or outside this attempt directory')
            json.loads(tree.read_text())
            entry['component_tree'] = str(tree)
        images.append(entry)
    record['images'] = images
    if len(images) == 1:
        record.update({k: images[0][k] for k in ['image', 'pixels', 'image_sha256']})


def render_studio(args, cli, project, source, out, record):
    record.update(backend='studio', ide_required=True)
    ready = run_logged([cli,'studio','check'], out/'studio-check.txt', 30, project)
    if ready.returncode or not exact_ready(ready.stdout, project):
        raise RuntimeError('Exact project is not READY in Android Studio; use the headless backend or resolve import/sync separately')
    image = out/'preview.png'
    cmd=[cli,'studio','render-compose-preview','--project='+str(project),
         '--output-image-file='+str(image),str(source),args.composable]
    record['command']=cmd
    run=run_logged(cmd, out/'renderer.txt', args.timeout, project)
    record['exit_code']=run.returncode
    if run.returncode or re.search(r'^\s*Error\s*:',run.stdout+run.stderr,re.MULTILINE|re.IGNORECASE):
        raise RuntimeError('Studio renderer reported failure. Compile changed sources/dependencies using the project build workflow, then retry once in a new attempt. Do not require an unlocked screen or click Build & Refresh as an automatic fallback.')
    if not image.is_file():
        raise RuntimeError('No image exported; command success is insufficient')
    record.update(image=str(image),pixels=png_size(image),image_sha256=hashlib.sha256(image.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--backend', choices=['headless', 'studio'], default='headless')
    parser.add_argument('--fqn', help='exact JVM method FQN from android preview list; required for headless')
    parser.add_argument('--composable', help='simple Preview function name; required for studio')
    parser.add_argument('--module', default=':app', help='Gradle target used with the explicit project path')
    parser.add_argument('--reference', help='explicit CLI build reference for another build system/target')
    parser.add_argument('--sdk', type=Path, help='Android SDK path passed to the CLI')
    parser.add_argument('--build-arg', action='append', default=[], help='argument passed verbatim to the build system; use --build-arg=VALUE')
    parser.add_argument('--component-tree', action='store_true')
    parser.add_argument('--source-root', action='append', type=Path, default=[], help='additional actual production/build input root')
    parser.add_argument('--variant', help='caller-declared variant; does not select or verify the build target')
    parser.add_argument('--output', required=True, type=Path, help='new attempt directory')
    parser.add_argument('--android', default='android', help='Android CLI executable')
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if args.backend == 'headless' and not args.fqn:
        parser.error('headless requires --fqn from android preview list; use --backend studio explicitly for the old --composable interface')
    if args.backend == 'studio' and not args.composable:
        parser.error('studio requires --composable')
    project = args.project.resolve()
    source = args.file.resolve() if args.file.is_absolute() else (project/args.file).resolve()
    roots = list(dict.fromkeys([project] + [x.resolve() for x in args.source_root]))
    if not all(x.is_dir() for x in roots) or not source.is_file() or not any(source.is_relative_to(x) for x in roots):
        parser.error('source must exist within the project or an explicitly supplied source root')
    cli = shutil.which(args.android)
    if not cli:
        parser.error('Android CLI unavailable; install official CLI, no device fallback')
    if args.timeout <= 0:
        parser.error('timeout must be positive')
    try:
        from PIL import Image
    except ImportError:
        parser.error('Pillow is required to decode exported PNGs; install Pillow in this Python environment')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lock = Path(tempfile.gettempdir())/('composer-preview-'+hashlib.sha256(getpass.getuser().encode()).hexdigest()[:16]+'.lockfile')
    record = {'project':str(project),'source':str(source),'composable':args.fqn or args.composable,
              'backend':args.backend, 'ide_required':args.backend == 'studio',
              'started_at':time.time(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'status':'blocked','device_used':False,'visual_review':'not performed by exporter',
              'variant_declared':args.variant, 'variant_verified_by_exporter':False,
              'freshness_scope':'unchanged source/build inputs during command; headless builds its selected target; this is not a visual correctness claim',
              'input_roots':[str(x) for x in roots]}
    lock_handle = None
    try:
        if args.backend == 'studio':
            lock_handle = acquire_lock(lock)
        record['owner_pid'] = os.getpid()
        version = run_logged([cli, '--version'], out/'cli-version.txt', 30, project)
        record['cli_version'] = version.stdout.strip()
        if version.returncode:
            raise RuntimeError('Unable to determine Android CLI version')
        before = input_snapshot(roots, out)
        (out/'inputs-before.json').write_text(json.dumps(before,indent=2))
        if args.backend == 'headless':
            render_headless(args, cli, project, out, record)
        else:
            render_studio(args, cli, project, source, out, record)
        after = input_snapshot(roots, out)
        (out/'inputs-after.json').write_text(json.dumps(after,indent=2))
        if before != after:
            record['changed_inputs'] = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
            raise RuntimeError('Production/build inputs changed during rendering; do not use this image as current-source evidence')
        record['inputs_sha256'] = hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
        record['status'] = 'rendered'
    except Exception as exc:
        record['error']=str(exc)
    finally:
        record['finished_at']=time.time()
        (out/'render.json').write_text(json.dumps(record,indent=2)+'\n')
        if lock_handle is not None:
            lock_handle.close()  # OS releases ownership on close or process death. Keep inode stable.
    print(json.dumps(record,indent=2))
    return 0 if record['status']=='rendered' else 1


if __name__=='__main__':
    raise SystemExit(main())
