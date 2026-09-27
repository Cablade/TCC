import json
from pathlib import Path
import sys

def update():
    root_dir = Path(__file__).resolve().parents[1]
    results_path = root_dir / "experiments" / "results" / "comparacao_a_b.csv"
    data_js_path = root_dir / "dashboard" / "js" / "data.js"

    if not results_path.exists():
        print(f"Erro: Arquivo {results_path} não encontrado. Rode o compare_systems.py primeiro.")
        sys.exit(1)

    print("Lendo resultados de", results_path)
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extrair metricas
    sys_a = data["systems"]["A"]
    sys_b = data["systems"]["B"]

    dashboard_payload = {
        "A": {
            "tp": sys_a["whole_image"]["tp"],
            "fn": sys_a["whole_image"]["fn"],
            "f1": round(sys_a["whole_image"]["f1"], 2) if sys_a["whole_image"]["f1"] is not None else 0.0,
            "time_seconds": round(sys_a["timing_seconds"]["total_seconds"]["total"]) if "timing_seconds" in sys_a else 0
        },
        "B": {
            "tp": sys_b["whole_image"]["tp"],
            "fn": sys_b["whole_image"]["fn"],
            "f1": round(sys_b["whole_image"]["f1"], 2) if sys_b["whole_image"]["f1"] is not None else 0.0,
            "time_seconds": round(sys_b["timing_seconds"]["total_seconds"]["total"]) if "timing_seconds" in sys_b else 0
        }
    }

    # Gerar conteudo do data.js
    js_content = f"""// Este arquivo é gerado automaticamente pelo script scripts/update_dashboard.py
const DASHBOARD_DATA = {json.dumps(dashboard_payload, indent=4)};
"""

    with open(data_js_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    
    print(f"Sucesso! {data_js_path} atualizado com os novos valores.")

if __name__ == "__main__":
    update()
