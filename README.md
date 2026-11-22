# TCC — comparação A × B para detecção de Trypanosoma cruzi

**Autores:** Victor Jacques e Caio Milão · **Orientador:** Prof. Rogério Mandelli · **Instituição:** UVA — Ciência da Computação.

O estudo compara dois sistemas completos nas mesmas imagens microscópicas: **A**, o modelo Fuzzylab/FIOCRUZ avaliado como foi entregue, e **B**, proposto pelo TCC, com localização por black-hat e Otsu e classificação com EfficientNet-B0. O teste final de 105 imagens foi aberto uma única vez, em 14/10/2026, depois do congelamento do protocolo.

## Comece aqui

- [Estado do trabalho](docs/status.md): o que terminou e o que falta.
- [Guia da rotina](docs/guia_treinamento.md): modelos, dados, teste final e figuras.
- [Metodologia](docs/metodologia.md) e [plano estatístico](docs/plano_estatistico.md): congelados no protocolo.
- [Dados e revisão](docs/dados.md): fontes autorizadas e limitações.
- [Ambiente](docs/ambiente.md): instalação, testes e transporte.
- [Mapa dos comandos](scripts/README.md): finalidade dos scripts.

## Dois modelos

| Modelo | Arquivo |
| --- | --- |
| A, como entregue | `models/model_a/model_trained.keras` |
| B avaliado (`b_hardneg_s42`) | `experiments/runs/b_atual/best.keras` |

`experiments/runs/b_atual/` é o lugar fixo do B em uso; `metadata.json` → `run_name` identifica o treino. O B foi treinado com `data/processed/b_hardneg/`: 4.898 recortes de treino (3.053 positivos/1.845 negativos, dos quais 517 negativos difíceis murinos revisados) e 1.070 de validação. As outras quatro sementes estão em `experiments/runs/b_hardneg_s*` e servem para a estabilidade entre treinos.

## Resultado do teste final

105 imagens murinas de teste (441 pontos publicados) e 253 negativos humanos de outra aquisição como resultado auxiliar. IC 95% por bootstrap pareado de imagens.

| Desfecho | A | B |
| --- | ---: | ---: |
| Cobertura dos pontos publicados | 0,0% | 91,6% [88,9%; 94,2%] |
| Precisão revisada por região | 0,0% (0/23) | 53,3% [44,9%; 62,5%] |
| Imagens positivas sinalizadas | 17,1% | 100,0% |
| Negativos sem alarme (auxiliar) | 98,8% | 100,0% |

McNemar nas positivas: só B acerta 87, só A acerta 0 (p Holm = 2,6e-26). Concordância entre dois avaliadores em 50 regiões: kappa 0,73 (três categorias) e 0,90 (binário, sem incertas).

[Texto dos resultados](tcc/resultados_atuais.md) · [Figuras do teste final](tcc/figuras/teste_final_20261014/LEIA-ME.md) · [Estatística completa](experiments/final_test_20261014/stats.md).

## Organização

| Pasta | Responsabilidade |
| --- | --- |
| `src/`, `scripts/`, `configs/` | Regras, comandos e configurações |
| `models/model_a/`, `experiments/runs/` | Os modelos e seus registros de treino |
| `experiments/comparison/` | Comparações de desenvolvimento (antes e depois da correção do viés) |
| `experiments/final_test_20261014/` | Previsões e estatística do teste final |
| `data/` | Fontes, revisões, partições, recortes e registros do protocolo |
| `docs/`, `tcc/` | Documentação, texto e figuras acadêmicas |
| `tests/`, `notebooks/` | Verificação e exploração |
| `archive/` | Histórico compactado, fora da rotina |

A `.venv` e o Python em `.cache/python` são necessários neste PC. Dados e modelos grandes são locais e não acompanham o Git. Consulte [LICENSE](LICENSE) e [fontes](docs/dados.md) antes de redistribuir.
