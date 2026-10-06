# TCC — comparação A × B para detecção de Trypanosoma cruzi

**Autores:** Victor Jacques e Caio Milão · **Orientador:** Prof. Rogério Mandelli · **Instituição:** UVA — Ciência da Computação.

O estudo compara dois sistemas completos nas mesmas imagens microscópicas: **A original**, congelado, e **B atual**, com localização configurável e EfficientNetB0. A melhoria é uma hipótese a medir.

## Comece aqui

- [Guia atual](docs/guia_treinamento.md): modelos, dados e comparação.
- [Estado do trabalho](docs/status.md): o que terminou e o que falta.
- [Dados e revisão](docs/dados.md): fontes autorizadas e limitações.
- [Ambiente](docs/ambiente.md): instalação e transporte.
- [Mapa dos comandos](scripts/README.md): finalidade dos scripts.

## Dois modelos em uso

| Modelo | Arquivo |
| --- | --- |
| A original | `models/model_a/model_trained.keras` |
| B atual | `experiments/runs/b_val_01/best.keras` |

Apesar do nome `b_val_01`, essa pasta contém o **Treinamento atual**: 17 épocas, melhor época 10, cerca de 15,2 minutos em CPU. Preserve configuração, histórico e metadados. O B anterior está em `archive/b_anterior_barcelona20_20261006/b_val_01/`. Não há terceiro modelo ativo na comparação.

[Gráficos e exemplos atuais](tcc/figuras/a_vs_b_barcelona20_20261006/index.html) · [Texto dos resultados](tcc/resultados_atuais.md).

Dados usados pelo B atual: `data/processed/b_next/`, com 4.381 recortes de treino (3.053 positivos/1.328 negativos), incluindo 80 negativos de 20 originais Barcelona, e 1.070 de validação. Cada recorte uma vez por época, sem oversampling/undersampling. `b_real_01` permanece como origem dos recortes compartilhados e registro dos dados anteriores. As 105 imagens do teste principal continuam reservadas.

## Organização

| Pasta | Responsabilidade |
| --- | --- |
| `src/`, `scripts/`, `configs/` | Regras, comandos e configurações vigentes |
| `models/model_a/`, `experiments/runs/b_val_01/` | Os dois modelos e seus registros |
| `experiments/comparison/` | Comparação A × B atual |
| `data/` | Fontes, revisões, partições e recortes necessários |
| `docs/`, `tcc/` | Documentação, texto e figuras acadêmicas |
| `tests/`, `notebooks/` | Verificação e exploração |
| `archive/` | Histórico compactado, fora da rotina atual |

A `.venv` e o Python em `.cache/python` são necessários neste PC. Dados e modelos grandes são locais e não acompanham automaticamente o Git. Consulte [LICENSE](LICENSE) e [fontes](docs/dados.md) antes de redistribuir.

[Todas as figuras e comparações](tcc/figuras/index.html). Nova comparação após o treino: **114 positivas + 73 negativas Kaggle + 180 negativas Barcelona**, mesmos 367 IDs para A original/B atual. As 20 Barcelona usadas no treino ficam fora. Previsões executadas novamente, sem reutilização das do B anterior. O diagnóstico anterior das 200 e a robustez sobre os 187 originais permanecem identificados como histórico do B arquivado.
