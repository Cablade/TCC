"""Inventário, exclusões, divisão por grupo e referência revisada (A × B)."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import data_protocol as dp  # noqa: E402 - raiz deve preceder import local


def save_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2,
                    ensure_ascii=False), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inv = commands.add_parser('inventory')
    inv.add_argument('--input', action='append', nargs='+', required=True,
                     help='Uma ou mais pastas/arquivos; pode repetir --input.')
    inv.add_argument('--metadata')
    inv.add_argument('--output-dir', required=True)
    split = commands.add_parser('split')
    split.add_argument('--inventory', required=True)
    choice = split.add_mutually_exclusive_group(required=True)
    choice.add_argument('--assignments')
    choice.add_argument('--counts', nargs='+',
                        help='Contagens explícitas por grupo: train=10 val=3 test=3')
    split.add_argument('--seed', type=int, default=42)
    split.add_argument('--output-dir', required=True)
    ann = commands.add_parser('annotation-template')
    ann.add_argument('--inventory', required=True)
    ann.add_argument('--output', required=True)
    valid = commands.add_parser('validate')
    valid.add_argument('--splits', required=True)
    valid.add_argument('--annotations')
    args = parser.parse_args()
    if args.command == 'inventory':
        inputs = [path for group in args.input for path in group]
        result = dp.build_inventory(inputs, dp.read_manifest(
            args.metadata) if args.metadata else [])
        output = Path(args.output_dir)
        if (output / 'inventory.csv').exists():
            raise FileExistsError('Inventário existente; use outro destino.')
        dp.write_manifest(result['images'], output/'inventory.csv')
        dp.write_manifest(result['exclusions'], output /
                          'exclusions.csv', [*dp.INVENTORY_FIELDS, 'reason'])
        save_json(output/'inventory_report.json',
                  {k: v for k, v in result.items() if k not in ('images', 'exclusions')})
        print(json.dumps(result['summary'], ensure_ascii=False))
        return int(bool(result['errors']))
    if args.command == 'split':
        rows = dp.read_manifest(args.inventory)
        assignments, counts = None, None
        if args.assignments:
            entries = dp.read_manifest(args.assignments)
            assignments = {row['group_id']: row['split'] for row in entries}
            if len(assignments) != len(entries):
                raise ValueError('Atribuições repetidas para um grupo')
        else:
            pairs = [entry.split('=', 1) for entry in args.counts]
            counts = {name: int(value) for name, value in pairs}
            if len(counts) != len(pairs):
                raise ValueError('Partições repetidas em --counts')
        partitions = dp.assign_splits(
            rows, assignments=assignments, counts=counts, seed=args.seed)
        output = Path(args.output_dir)
        if output.exists():
            raise FileExistsError('Partições existentes; use outro destino para preservar a divisão.')
        from src.dataset_policy import validate_active_images
        validate_active_images(partitions)
        dp.write_manifest(partitions, output/'images.csv')
        for name in dp.SPLITS:
            dp.write_manifest([row for row in partitions if row['split'] == name],
                              output/(name+'.csv'), [*dp.INVENTORY_FIELDS, 'split'])
        save_json(output/'split_report.json', {'seed': args.seed, 'assignments': assignments, 'counts': counts,
                                               'inventory_sha256': hashlib.sha256(Path(args.inventory).read_bytes()).hexdigest(),
                                               'partitions': {name: dp.inventory_summary([row for row in partitions if row['split'] == name]) for name in dp.SPLITS}})
        print(f'{len(partitions)} imagens únicas; manifesto: {output / "images.csv"}')
    elif args.command == 'annotation-template':
        if Path(args.output).exists():
            raise FileExistsError(
                'Template não sobrescreve anotações existentes')
        save_json(args.output, dp.annotation_template(
            dp.read_manifest(args.inventory)))
        print('Template pendente de revisão; nenhum rótulo real foi fabricado.')
    else:
        rows = dp.read_manifest(args.splits)
        dp.validate_partitions(rows)
        if args.annotations:
            annotations = dp.load_annotations(args.annotations, rows)
            print(
                f'{len(annotations)} registros de anotação estruturalmente válidos; revisão humana continua necessária.')
        print('Partições válidas: nenhum grupo ou conteúdo duplicado entre partições.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
