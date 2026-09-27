"""Exporta PNGs sem marcações e CSVs de uma inferência A/B já concluída."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from src.data_protocol import read_manifest
    from src.prediction_exports import export_saved_predictions
    from src.model_a import file_sha256
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output-dir', required=True, help='Pasta nova para preservar os resultados anteriores.')
    args = parser.parse_args()
    payload = json.loads(Path(args.predictions).read_text(encoding='utf-8'))
    expected = payload.get('manifest_sha256') or payload['artifact'].get('manifest_sha256')
    if not expected or file_sha256(args.manifest) != expected:
        raise ValueError('Manifesto difere do usado na inferência.')
    exports = export_saved_predictions(payload, read_manifest(args.manifest), args.output_dir)
    errors = sum(bool(entry['export_error']) for entry in exports.values())
    report = {'predictions_sha256': file_sha256(args.predictions), 'manifest_sha256': expected,
              'images': len(exports), 'export_errors': errors, 'image_mode': 'original',
              'inference_repeated': False, 'source_predictions': str(Path(args.predictions).resolve())}
    (Path(args.output_dir) / 'export.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    return int(errors > 0)


if __name__ == '__main__':
    raise SystemExit(main())
