#!/usr/bin/env python3
import os
import json
import csv
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


def run_git(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(
        ['git', *args],
        cwd=str(cwd),
        stderr=subprocess.STDOUT,
    ).decode('utf-8', errors='replace')


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def text_stats(text: str) -> dict:
    words = [w for w in text.replace('\n', ' ').split() if w.strip()]
    headings = sum(1 for line in text.split('\n') if line.lstrip().startswith('#'))
    images = text.count('![')
    links = text.count('](')
    code_fences = text.count('```')
    return {
        'chars': len(text),
        'words': len(words),
        'headings': headings,
        'images': images,
        'links': links,
        'code_fences': code_fences,
    }


def is_text_file(path: Path, sample_size: int = 2048) -> bool:
    try:
        with path.open('rb') as f:
            data = f.read(sample_size)
        if b'\x00' in data:
            return False
        try:
            data.decode('utf-8')
            return True
        except Exception:
            return False
    except Exception:
        return False


def build_tree(root: Path, exclude_dirs: set[str] | None = None) -> str:
    exclude_dirs = exclude_dirs or set()
    lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in sorted(dirnames) if d not in exclude_dirs]
        rel = Path(dirpath).relative_to(root)
        indent = '  ' * (0 if rel == Path('.') else len(rel.parts))
        for d in dirnames:
            lines.append(f"{indent}{d}/")
        for f in sorted(filenames):
            if rel == Path('.') and f.startswith('.') and 'github' not in f:
                continue
            lines.append(f"{indent}{f}")
    return '\n'.join(lines)


def analyze_commits(root: Path) -> dict:
    try:
        count = int(run_git(['rev-list', '--count', 'HEAD'], cwd=root).strip())
    except Exception:
        count = 0

    try:
        log = run_git(['log', '--pretty=format:%h|%an|%ad|%s', '--date=iso'], cwd=root).strip().split('\n')
    except subprocess.CalledProcessError:
        return {'count': count, 'items': [], 'avg_msg_len': 0, 'quality': 0.0}

    commits = []
    quality_scores = []
    for line in log:
        if not line.strip():
            continue
        parts = line.split('|', 3)
        if len(parts) < 4:
            continue
        short, author, date, msg = parts
        msg_len = len(msg.strip())
        msg_lower = msg.strip().lower()
        generic = any(g in msg_lower for g in ['update', 'actualiza', 'fix', 'arreglo', 'cambios', 'misc', 'wip'])
        imperative = any(
            msg_lower.startswith(p)
            for p in ['add', 'create', 'anade', 'agrega', 'implement', 'refactor', 'remove', 'elimina', 'document', 'docs', 'feat', 'fix', 'chore']
        )
        score = 0
        if msg_len >= 12:
            score += 0.4
        if not generic:
            score += 0.3
        if imperative:
            score += 0.3
        quality_scores.append(score)
        commits.append({'short': short, 'author': author, 'date': date, 'message': msg, 'score': round(score, 2)})

    avg_len = sum(len(c['message']) for c in commits) / len(commits) if commits else 0
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    return {'count': max(count, len(commits)), 'items': commits, 'avg_msg_len': round(avg_len, 1), 'quality': round(avg_quality, 2)}


def analyze_branches(root: Path, default_branch: str | None = None) -> dict:
    expected_features = {'feature-mensaje-bienvenida', 'feature-licencia'}
    principal_candidates = set()
    if default_branch and default_branch.strip() and default_branch != '(unknown)':
        principal_candidates.add(default_branch.strip())
    principal_candidates.update({'main', 'master'})

    local_branches = set()
    remote_branches = set()
    remote_heads = set()

    try:
        out_local = run_git(['for-each-ref', '--format=%(refname:short)', 'refs/heads'], cwd=root)
        for line in out_local.splitlines():
            if line.strip():
                local_branches.add(line.strip())
    except Exception:
        pass

    try:
        out_remote = run_git(['for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin'], cwd=root)
        for line in out_remote.splitlines():
            b = line.strip()
            if not b:
                continue
            if b == 'origin/HEAD':
                continue
            if b.startswith('origin/'):
                b = b[len('origin/'):]
            remote_branches.add(b)
    except Exception:
        pass

    # En CI (actions/checkout), no siempre se descargan todas las refs remotas.
    # ls-remote consulta directamente los heads en origin.
    try:
        out_heads = run_git(['ls-remote', '--heads', 'origin'], cwd=root)
        for line in out_heads.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1].startswith('refs/heads/'):
                remote_heads.add(parts[1][len('refs/heads/'):])
    except Exception:
        pass

    try:
        out_all = run_git(['branch', '-a', '--format=%(refname:short)'], cwd=root)
        for line in out_all.splitlines():
            b = line.strip()
            if not b or b == 'origin/HEAD':
                continue
            if b.startswith('origin/'):
                b = b[len('origin/'):]
                remote_branches.add(b)
            else:
                local_branches.add(b)
    except Exception:
        pass

    all_set = local_branches.union(remote_branches).union(remote_heads)
    all_branches = sorted(all_set)
    found_features = sorted(expected_features.intersection(all_set))
    missing_features = sorted(expected_features.difference(all_set))
    main_or_default_detected = any(b in all_set for b in principal_candidates)

    expected = sorted(expected_features.union(principal_candidates))
    found_expected = sorted(set(found_features).union(principal_candidates.intersection(all_set)))
    missing_expected = sorted(set(expected).difference(set(found_expected)))

    return {
        'all': all_branches,
        'expected': expected,
        'found_expected': found_expected,
        'missing_expected': missing_expected,
        'expected_features': sorted(expected_features),
        'found_expected_features': found_features,
        'missing_expected_features': missing_features,
        'main_or_default_detected': main_or_default_detected,
        'principal_candidates': sorted(principal_candidates),
    }


def detect_features_from_evidence(root: Path) -> dict:
    expected_features = {'feature-mensaje-bienvenida', 'feature-licencia'}
    candidates = [
        root / 'cp1-ramas-iniciales.txt',
        root / 'cp2-feature-branch.txt',
        root / 'cp3-comparacion-ramas.md',
        root / 'cp4-multiples-ramas.txt',
    ]
    scanned_files = []
    found = set()

    for p in candidates:
        if not p.exists() or not p.is_file():
            continue
        scanned_files.append(str(p.relative_to(root)))
        txt = safe_read_text(p).lower()
        for b in expected_features:
            if b.lower() in txt:
                found.add(b)

    return {
        'found_features': sorted(found),
        'missing_features': sorted(expected_features.difference(found)),
        'scanned_files': scanned_files,
    }


def analyze_files(root: Path, exclude_dirs: set[str] | None = None) -> dict:
    exclude_dirs = exclude_dirs or set()
    large = []
    binaries = []
    total_files = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for f in filenames:
            p = Path(dirpath) / f
            rel = p.relative_to(root)
            total_files += 1
            try:
                size = p.stat().st_size
            except Exception:
                size = 0
            if size >= 10 * 1024 * 1024:
                large.append({'path': str(rel), 'size': size})
            if not is_text_file(p):
                binaries.append(str(rel))
    return {'total_files': total_files, 'large_files': large, 'binary_files': binaries}


def score_section(exists: bool, ok: bool) -> int:
    if not exists:
        return 0
    return 2 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--required', default='app.txt,LICENSE.txt,cp1-ramas-iniciales.txt,cp2-feature-branch.txt,cp3-comparacion-ramas.md,cp4-multiples-ramas.txt,reflexion-6-2.md')
    ap.add_argument('--min-commits', default='3')
    ap.add_argument('--outdir', default='reportes')
    args = ap.parse_args()

    root = Path(args.repo_root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    required = [x.strip() for x in args.required.split(',') if x.strip()]
    try:
        min_commits = int(str(args.min_commits))
    except Exception:
        min_commits = 3

    try:
        default_branch = run_git(['symbolic-ref', '--short', 'refs/remotes/origin/HEAD'], cwd=root).strip().split('/', 1)[-1]
    except Exception:
        try:
            default_branch = run_git(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=root).strip()
        except Exception:
            default_branch = '(unknown)'

    commits_info = analyze_commits(root)
    branches_info = analyze_branches(root, default_branch=default_branch)
    evidence_branch_info = detect_features_from_evidence(root)
    missing = [f for f in required if not (root / f).exists()]

    readme_path = root / 'README.md'
    readme_text = safe_read_text(readme_path) if readme_path.exists() else ''
    readme_stats = text_stats(readme_text) if readme_text else {'chars': 0, 'words': 0, 'headings': 0, 'images': 0, 'links': 0, 'code_fences': 0}
    readme_ok = bool(readme_text) and readme_stats['words'] >= 40 and readme_stats['headings'] >= 1

    reflex_path = root / 'reflexion-6-2.md'
    reflex_text = safe_read_text(reflex_path) if reflex_path.exists() else ''
    reflex_stats = text_stats(reflex_text) if reflex_text else {'words': 0}
    reflex_ok = bool(reflex_text) and reflex_stats['words'] >= 80

    evidencia_candidates = [
        'cp1', 'cp2', 'cp3', 'cp4',
        'app', 'license', 'ramas', 'feature', 'comparacion', 'reflexion',
    ]
    evidencias_presentes = []
    for cand in evidencia_candidates:
        for p in root.rglob(f'*{cand}*'):
            if outdir.name in p.parts or '.git' in p.parts:
                continue
            if p.is_file() and p.suffix.lower() in ('.md', '.png', '.jpg', '.jpeg', '.txt', ''):
                evidencias_presentes.append(str(p.relative_to(root)))
    evidencias_ok = len(set(evidencias_presentes)) >= 6

    excluded_dirs = {'.git', outdir.name}
    files_info = analyze_files(root, exclude_dirs=excluded_dirs)
    arbol = build_tree(root, exclude_dirs=excluded_dirs)
    (outdir / 'arbol.txt').write_text(arbol, encoding='utf-8')

    s_estructura = 2
    if files_info['large_files']:
        s_estructura = 1
    if missing:
        s_estructura = 0

    # Rúbrica oficial: 4 pts ramas + 3 pts evidencias + 3 pts reflexión = 10
    commits_ok = commits_info['count'] >= min_commits and commits_info['quality'] >= 0.6
    found_features_set = set(branches_info['found_expected_features']).union(set(evidence_branch_info['found_features']))
    missing_features_set = set(branches_info['expected_features']).difference(found_features_set)
    features_found = len(found_features_set)
    main_found = bool(branches_info['main_or_default_detected'])
    if commits_ok and features_found >= 2 and main_found:
        s_git_ramas = 4
    elif features_found >= 2:
        s_git_ramas = 3
    elif features_found == 1 and (commits_info['count'] > 0 or main_found):
        s_git_ramas = 2
    elif commits_info['count'] > 0 or main_found:
        s_git_ramas = 1
    else:
        s_git_ramas = 0

    if evidencias_ok:
        s_evid = 3
    elif len(set(evidencias_presentes)) >= 3:
        s_evid = 2
    elif evidencias_presentes:
        s_evid = 1
    else:
        s_evid = 0

    if reflex_ok:
        s_reflex = 3
    elif reflex_path.exists() and reflex_stats['words'] > 0:
        s_reflex = 1
    else:
        s_reflex = 0

    total = s_git_ramas + s_evid + s_reflex

    resumen = {
        'repo_default_branch': default_branch,
        'required_files': required,
        'missing_required': missing,
        'commits': commits_info,
        'branches': branches_info,
        'branch_evidence': {
            'found_expected_features': sorted(found_features_set),
            'missing_expected_features': sorted(missing_features_set),
            'scanned_files': evidence_branch_info['scanned_files'],
            'detected_only_in_evidence': sorted(set(evidence_branch_info['found_features']).difference(set(branches_info['found_expected_features']))),
        },
        'readme_stats': readme_stats,
        'reflexion_stats': reflex_stats,
        'evidencias_encontradas': sorted(set(evidencias_presentes)),
        'files_info': files_info,
        'checks_no_puntuables': {
            'estructura': {
                'score_referencia': s_estructura,
                'max_referencia': 2,
                'estado': 'ok' if s_estructura == 2 else ('parcial' if s_estructura == 1 else 'ko'),
            }
        },
        'scores': {
            'git_ramas (max_4)': s_git_ramas,
            'evidencias (max_3)': s_evid,
            'reflexion (max_3)': s_reflex,
            'total': total,
            'sobre': 10,
        },
    }

    with (outdir / 'informe.json').open('w', encoding='utf-8') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    with (outdir / 'metricas.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['criterio', 'puntuacion'])
        w.writerow(['git_ramas (max 4)', s_git_ramas])
        w.writerow(['evidencias (max 3)', s_evid])
        w.writerow(['reflexion (max 3)', s_reflex])
        w.writerow(['total', total])

    def badge(score: int) -> str:
        color = 'red'
        if score >= 9:
            color = 'brightgreen'
        elif score >= 7:
            color = 'green'
        elif score >= 5:
            color = 'yellow'
        elif score >= 3:
            color = 'orange'
        return f"![score](https://img.shields.io/badge/nota-{score}%2F10-{color})"

    md = []
    md.append(f"# Informe de evaluacion - {datetime.utcnow().isoformat(timespec='seconds')}Z")
    md.append(badge(total) + '')
    md.append(f"**Rama por defecto:** `{default_branch}`  ")
    md.append(f"**Minimo de commits esperado:** {min_commits}  ")
    md.append('')

    md.append('## Resultado por criterios')
    md.append('| Criterio | Puntuacion |')
    md.append('|---|---:|')
    md.append(f"| Uso de Git y ramas (`git branch`, `checkout`) | {s_git_ramas}/4 |")
    md.append(f"| Evidencias (checkpoints + archivos) | {s_evid}/3 |")
    md.append(f"| Reflexion 6.2 | {s_reflex}/3 |")
    md.append(f"| **Total** | **{total}/10** |")
    md.append('')

    md.append('## Validaciones adicionales (no puntuan)')
    if s_estructura == 2:
        md.append('- Estructura del repositorio: OK')
    elif s_estructura == 1:
        md.append('- Estructura del repositorio: Parcial (hay archivos grandes)')
    else:
        md.append('- Estructura del repositorio: KO (faltan archivos obligatorios)')
    md.append('')

    if missing:
        md.append('> WARNING: Faltan archivos obligatorios: ' + ', '.join(missing))
        md.append('')

    md.append('## Metricas del README')
    md.append(f"- Palabras: {readme_stats.get('words', 0)}  ")
    md.append(f"- Encabezados: {readme_stats.get('headings', 0)}  ")
    md.append(f"- Imagenes: {readme_stats.get('images', 0)}  ")
    md.append(f"- Enlaces: {readme_stats.get('links', 0)}  ")
    md.append('')

    md.append('## Archivos obligatorios')
    md.append(f"Requeridos: {', '.join(required)}  ")
    if missing:
        md.append(f"Faltantes: {', '.join(missing)}  ")
    else:
        md.append('Todos presentes.  ')
    md.append('')

    md.append('## Commits')
    md.append(f"- Numero de commits: **{commits_info['count']}**  ")
    md.append(f"- Calidad media de mensajes: **{commits_info['quality']}**  ")
    md.append(f"- Longitud media del mensaje: **{commits_info['avg_msg_len']}**  ")
    md.append('')
    md.append('<details><summary>Ver listado</summary>')
    md.append('')
    for c in commits_info['items'][:50]:
        md.append(f"- `{c['short']}` {c['date']} - {c['message']} (score {c['score']})")
    md.append('</details>')
    md.append('')

    md.append('## Ramas detectadas')
    if branches_info['all']:
        for b in branches_info['all']:
            md.append(f"- {b}")
    else:
        md.append('- No se detectaron ramas en refs locales/remotas.')
    if missing_features_set:
        md.append('')
        md.append('Features requeridas y no detectadas: ' + ', '.join(sorted(missing_features_set)))
    else:
        md.append('')
        md.append('Features requeridas detectadas: ' + ', '.join(sorted(found_features_set)))
    if evidence_branch_info['scanned_files']:
        md.append('')
        md.append('Evidencias revisadas para detectar ramas: ' + ', '.join(evidence_branch_info['scanned_files']))
    detected_only_in_evidence = set(evidence_branch_info['found_features']).difference(set(branches_info['found_expected_features']))
    if detected_only_in_evidence:
        md.append('')
        md.append('Features detectadas solo por evidencias (no como refs en repo): ' + ', '.join(sorted(detected_only_in_evidence)))
    md.append('')
    md.append('Rama principal detectada (main/master/default): ' + ('si' if branches_info['main_or_default_detected'] else 'no'))
    md.append('')

    md.append('## Evidencias detectadas (heuristica)')
    if evidencias_presentes:
        for e in sorted(set(evidencias_presentes))[:50]:
            md.append(f"- {e}")
    else:
        md.append('- No se detectaron evidencias con la convencion esperada.')
    md.append('')

    if files_info['large_files']:
        md.append('## Archivos grandes (>=10MB)')
        for lf in files_info['large_files']:
            md.append(f"- {lf['path']} - {lf['size']} bytes")
        md.append('')

    md.append('## Arbol del repositorio (resumen)')
    md.append('```')
    md.append(safe_read_text(outdir / 'arbol.txt')[:4000])
    md.append('```')

    (outdir / 'informe.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(f"Informe generado en: {outdir}/informe.md")


if __name__ == '__main__':
    main()
