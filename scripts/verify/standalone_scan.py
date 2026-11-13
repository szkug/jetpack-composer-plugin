"""Run native analyzer CLIs against an explicit compilation context; never run a build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from ensure_analyzers import ensure, lock_data, rule_path, ROOT
from incremental_lint import git, changed_lines, snapshot, write_json
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'score'))
from rule_policy import POLICY as RULE_POLICY, policy_digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(path):
    path = Path(path)
    if path.is_file():return sha(path)
    if not path.is_dir():raise ValueError('Missing analysis input: ' + str(path))
    digest = hashlib.sha256()
    for p in sorted(p for p in path.rglob('*') if p.is_file()):
        digest.update(p.relative_to(path).as_posix().encode() + b'\0' + bytes.fromhex(sha(p)))
    return digest.hexdigest()


def load_context(filename):
    filename = Path(filename).resolve()
    data = json.loads(filename.read_text())
    if data.get('schema_version') != 1 or not data.get('provenance'):
        raise ValueError('Context schema_version=1 and a compilation metadata provenance are required')
    allowed = {'schema_version','project','module','module_dir','variant','source_roots','generated_sources','classpath','jvm_target','language_version','api_version','jdk_home','provenance','android','lint_rule_jars','lint_config'}
    if set(data) - allowed:raise ValueError('Unsupported context fields (not silently ignored): ' + ', '.join(sorted(set(data) - allowed)))
    project = (filename.parent / data['project']).resolve()
    if not project.is_dir():raise ValueError('Context project is missing')
    def path(value):
        p = (project / value).resolve()
        if not p.exists():raise ValueError('Missing context input: ' + str(p))
        if os.pathsep in str(p):raise ValueError('Analyzer path-list separator in an input path is unsupported: ' + str(p))
        return str(p)
    data['project'] = str(project)
    data['module_dir'] = path(data.get('module_dir', '.'))
    for key in ['module', 'variant', 'jvm_target', 'language_version']:
        if not isinstance(data.get(key), str) or not data[key].strip():raise ValueError('Missing context field: ' + key)
    for key in ['source_roots', 'classpath']:
        if not isinstance(data.get(key), list) or not data[key]:raise ValueError('Full analysis requires nonempty ' + key)
        data[key] = [path(v) for v in data[key]]
    for key in ['generated_sources', 'lint_rule_jars']:
        data[key] = [path(v) for v in data.get(key, [])]
    # Android library extraction places lint.jar beside its own classes.jar.
    # Follow only declared library artifacts; never search arbitrary dependency caches.
    companions = sorted({str(Path(v).parent / 'lint.jar') for v in data['classpath']
                         if Path(v).name == 'classes.jar' and (Path(v).parent / 'lint.jar').is_file()})
    data['lint_rule_jars'] = sorted(set(data['lint_rule_jars'] + companions))
    if any(Path(v).suffix == '.aar' for v in data['classpath']):
        raise ValueError('Classpath must contain resolved classes directories/JARs, not AAR archives')
    android = data.get('android')
    if android:
        for key in ['sdk', 'manifest']:android[key] = path(android[key])
        android['resources'] = [path(v) for v in android.get('resources', [])]
        android['android_jar'] = path(str(Path(android['sdk']) / 'platforms' / ('android-' + str(android['compile_sdk'])) / 'android.jar'))
        if android['android_jar'] not in data['classpath']:data['classpath'].append(android['android_jar'])
    if data.get('lint_config'):data['lint_config'] = path(data['lint_config'])
    if data.get('jdk_home'):data['jdk_home'] = path(data['jdk_home'])
    sources = sorted({str(p) for root in data['source_roots'] + data['generated_sources']
                      for p in ([Path(root)] if Path(root).is_file() else Path(root).rglob('*'))
                      if p.is_file() and p.suffix in ('.kt', '.java')})
    if not sources:raise ValueError('No Kotlin/Java inputs; an empty scan is not a pass')
    data['source_files'] = sources
    data['context_file'] = str(filename)
    return data


def lint_descriptor(context, out, rules):
    android = context.get('android')
    if not android:raise ValueError('Android lint requires android SDK/manifest/compile_sdk context')
    xml = ET.Element('project')
    ET.SubElement(xml, 'root', dir=context['module_dir'])
    ET.SubElement(xml, 'sdk', dir=android['sdk'])
    for jar in map(str, rules):
        ET.SubElement(xml, 'lint-checks', file=jar)
    cache = out / 'lint-cache';cache.mkdir()
    ET.SubElement(xml, 'cache', dir=str(cache))
    module = ET.SubElement(xml, 'module', name=context['module'], android='true',
                           library=str(bool(android.get('library', False))).lower(),
                           **{'compile-sdk-version': str(android['compile_sdk'])})
    for path in context['source_files']:ET.SubElement(module, 'src', file=path)
    for path in context['classpath']:ET.SubElement(module, 'classpath', file=path)
    ET.SubElement(module, 'manifest', file=android['manifest'])
    for root in android['resources']:
        for p in ([Path(root)] if Path(root).is_file() else Path(root).rglob('*')):
            if p.is_file():ET.SubElement(module, 'resource', file=str(p))
    target = out / 'project.xml';ET.ElementTree(xml).write(target, encoding='utf-8', xml_declaration=True)
    return target


def prepare(args, analyzer):
    context = load_context(args.context)
    if analyzer == 'lint' and context.get('lint_config'):
        raise ValueError('Full-registry Lint assessment uses a generated override; remove lint_config from the context')
    project = Path(context['project'])
    root = Path(git(project, 'rev-parse', '--show-toplevel').decode().strip())
    base = git(root, 'rev-parse', '--verify', args.base + '^{commit}').decode().strip()
    if args.merge_base:base = git(root, 'merge-base', base, 'HEAD').decode().strip()
    before = snapshot(root, base)
    changes = changed_lines(root, base)
    # Native tools are installed only when this authorized scan needs them.
    native = ensure(analyzer)
    out = Path(args.out).resolve() if args.out else Path(tempfile.mkdtemp(prefix='compose-' + analyzer + '-'))
    if out == root or root in out.parents:raise ValueError('Evidence output must be outside the Git worktree')
    if args.out:out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'context.json', context)
    lock, lock_sha = lock_data(ROOT)
    rules = ([rule_path(ROOT, lock, name) for name in ['detekt-0.6.8.jar', 'common-detekt-0.6.8.jar', 'composer-quality-rules.jar']]
             if analyzer == 'detekt' else [rule_path(ROOT, lock, 'compose-lint-checks-1.6.1.jar'), *map(Path, context['lint_rule_jars'])])
    config = ROOT / 'scripts/verify/rules/detekt.yml'
    common = [native['executable']]
    if analyzer == 'detekt':
        shutil.copyfile(config, out / 'detekt.yml')
        command = common + ['--analysis-mode', 'full', '--input', os.pathsep.join(context['source_files']),
            '--classpath', os.pathsep.join(context['classpath']), '--jvm-target', context['jvm_target'],
            '--language-version', context['language_version'], '--base-path', str(root),
            '--plugins', os.pathsep.join(map(str, rules)), '--config', str(out / 'detekt.yml'),
            '--fail-on-severity', 'Never', '--report', 'sarif:' + str(out / 'detekt.sarif')]
        if context.get('api_version'):command += ['--api-version', context['api_version']]
        if context.get('jdk_home'):command += ['--jdk-home', str(Path(context['jdk_home']).resolve())]
    else:
        from lint_inventory import collect
        lint_inventory = collect(native, rules, out)
        descriptor = lint_descriptor(context, out, rules)
        (out / 'empty-baseline.xml').write_text('<issues format="6" />\n')
        command = common + ['--project', str(descriptor), '--lint-rule-jars', os.pathsep.join(map(str, rules)),
            '--xml', str(out / 'lint.xml'), '--quiet', '--baseline', str(out / 'empty-baseline.xml'),
            '--java-language-level', context['jvm_target'], '--kotlin-language-level', context['language_version']]
        # A scoring run enables every registered ID, including default-disabled rules.
        # The generated override prevents local lint.xml from overriding built-in activation or severity.
        command += ['--check', ','.join(lint_inventory['rules']),
                    '--override-config', str(out / 'all-rules-lint.xml')]
    frozen_paths = set(context['source_roots'] + context['generated_sources'] + context['classpath'] +
                       context['lint_rule_jars'] + [context['context_file'], str(config), *map(str, rules)])
    # Also freeze inherited lint policy and Android resources/manifest used by this invocation.
    for parent in [Path(context['module_dir']), *Path(context['module_dir']).parents]:
        if (parent / 'lint.xml').is_file():frozen_paths.add(str(parent / 'lint.xml'))
    if context.get('lint_config'):frozen_paths.add(context['lint_config'])
    if context.get('android'):
        a = context['android'];frozen_paths.update(a['resources'] + [a['manifest'], a['android_jar']])
    if native.get('runtime_manifest'):
        runtime = Path(native['runtime_manifest']);record = json.loads(runtime.read_text())
        frozen_paths.add(str(runtime));frozen_paths.update(str(runtime.parent / name) for name in record['files'])
    frozen_paths.add(native['executable'])
    frozen_paths.add(str(ROOT / 'scripts/verify/runtime/analyzers.lock.json'))
    frozen_paths.add(str(RULE_POLICY))
    def item(path):return {'path': str(path), 'name': Path(path).name, 'sha256': fingerprint(path)}
    receipt = {'rulePolicySha256': policy_digest(), 'integration': 'standalone-cli', 'analyzer': analyzer, 'mode': 'full',
        'version': lock['tools'][analyzer]['version'], 'cliVersion': native['version'],
        'module': context['module'], 'variant': context['variant'], 'projectDir': context['module_dir'],
        'originalProjectEvaluated': False, 'contextProvenance': context['provenance'],
        'contextFile': item(context['context_file']), 'contextVerified': True,
        'sourceFiles': context['source_files'], 'sourceInputs': [item(p) for p in context['source_files']],
        'classpath': [item(p) for p in context['classpath']], 'jvmTarget': context['jvm_target'],
        'languageVersion': context['language_version'], 'autoCorrect': False, 'baseline': None,
        'buildUponDefaultConfig': False, 'pluginClasspath': [item(p) for p in rules],
        'configFiles': [item(out / 'detekt.yml')] if analyzer == 'detekt' else [],
        'composeRulesVersion': '0.6.8', 'composerRulesVersion': '1.4.1', 'slackVersion': '1.6.1',
        'analyzerLockSha256': lock_sha, 'native': native, 'command': command,
        'coverageBoundary': 'Full analysis of declared compilation context. Context provenance/completeness must be reviewed; no Gradle evaluation or build is implied.'}
    if analyzer == 'lint':
        receipt['ruleInventory'] = lint_inventory
        receipt['configFiles'] = [item(out / 'all-rules-lint.xml')]
    write_json(out / 'receipt.json', receipt)
    write_json(out / 'command.json', {'argv': command, 'cwd': str(project)})
    manifest = {'analyzer': analyzer, 'project': str(project), 'root': str(root), 'base': base,
        'head': git(root, 'rev-parse', 'HEAD').decode().strip(), 'source_digest': before,
        'changes': changes, 'module': context['module'], 'variant': context['variant'],
        'fail_level': args.fail_level, 'profile': 'composer-static-v7', 'analysis_mode': 'full',
        'coverage_note': receipt['coverageBoundary'], 'cli_argv': command,
        'analysis_environment': {k: os.environ.get(k) for k in ['JAVA_HOME','JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS']},
        'original_inputs': {p: fingerprint(p) for p in sorted(frozen_paths)},
        'inputs': {p.relative_to(out).as_posix(): sha(p) for p in out.rglob('*') if p.is_file()}}
    if snapshot(root, base) != before:raise ValueError('Source changed during preparation')
    write_json(out / 'manifest.json', manifest)
    print(json.dumps({'run_dir': str(out), 'cwd': str(project), 'command_file': str(out / 'command.json'), 'executable': native['executable']}))
    return out, manifest


def validate_run(out, exit_code):
    manifest = json.loads((out / 'manifest.json').read_text())
    errors = []
    if manifest.get('analysis_environment') != {k: os.environ.get(k) for k in ['JAVA_HOME','JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS']}:
        errors.append('Java execution environment changed during scan')
    if exit_code != 0:errors.append('Native CLI execution failed: ' + str(exit_code))
    if snapshot(Path(manifest['root']), manifest['base']) != manifest['source_digest']:
        errors.append('Source changed during scan')
    for p, expected in manifest['original_inputs'].items():
        if not Path(p).exists() or fingerprint(p) != expected:errors.append('Analysis input changed: ' + p)
    for p, expected in manifest['inputs'].items():
        if not (out / p).is_file() or sha(out / p) != expected:errors.append('Prepared input changed: ' + p)
    receipt = json.loads((out / 'receipt.json').read_text())
    if receipt.get('integration') != 'standalone-cli' or receipt.get('mode') != 'full' or not receipt.get('contextVerified'):
        errors.append('Invalid standalone analysis receipt')
    if receipt.get('rulePolicySha256') != policy_digest():
        errors.append('Shared verification/scoring rule policy changed')
    if manifest.get('fail_level') != 'warning':
        errors.append('Built-in policy requires warnings and errors to block delivery')
    report = out / ('detekt.sarif' if manifest['analyzer'] == 'detekt' else 'lint.xml')
    if not report.is_file():errors.append('Fresh native analyzer report missing')
    return manifest, receipt, errors


def main(analyzer):
    parser = argparse.ArgumentParser(description='Native ' + analyzer + ' CLI, bundled rules and Git changed-line gate; no Gradle execution.')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['run', 'prepare']:
        p = commands.add_parser(name)
        p.add_argument('--context', required=True, help='Explicit compilation-context JSON; see CLI.md. No guessed classpath or syntax fallback.')
        p.add_argument('--base', default='HEAD')
        p.add_argument('--merge-base', action='store_true')
        p.add_argument('--out')
        p.add_argument('--fail-level', choices=['warning'], default='warning')
    p = commands.add_parser('check');p.add_argument('--run-dir', required=True);p.add_argument('--exit-code', required=True, type=int)
    args = parser.parse_args()
    from incremental_detekt import check as detekt_check
    from incremental_lint import check as lint_check
    check = detekt_check if analyzer == 'detekt' else lint_check
    if args.command == 'check':return check(Path(args.run_dir).resolve(), args.exit_code)
    out, manifest = prepare(args, analyzer)
    if args.command == 'prepare':return 0
    env = dict(os.environ)
    # Extra ambient lint plugins are not part of the declared profile.
    env.pop('ANDROID_LINT_JARS', None);env.pop('LINT_JARS', None)
    with (out / 'analyzer.log').open('w') as log:
        result = subprocess.run(manifest['cli_argv'], cwd=manifest['project'], env=env, stdout=log, stderr=subprocess.STDOUT)
    write_json(out / 'execution.json', {'command': manifest['cli_argv'], 'exit_code': result.returncode})
    return check(out, result.returncode)
