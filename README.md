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

Apesar do nome `b_val_01`, essa pasta contém o **treinamento atual**: 16 épocas, melhor época 9, com negativos originais revisados. Preserve configuração, histórico e metadados. Não há terceiro modelo na comparação.

[Gráficos e exemplos atuais](tcc/figuras/a_vs_b_barcelona/index.html) · [Texto dos resultados](tcc/resultados_atuais.md).

Dados usados pelo B atual: `data/processed/b_real_01/`, com 4.301 recortes de treino e 1.070 de validação, preservados. Próximo treino **somente preparado**, em `data/processed/b_next/`: 4.381 recortes de treino, incluindo 80 negativos extraídos de 20 originais Barcelona; validação mantém 1.070 recortes. Nenhum novo treino foi iniciado. As 105 imagens do teste principal continuam reservadas.

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

[Todas as figuras e comparações](tcc/figuras/index.html). Comparação atual: **114 positivas + 73 negativas Kaggle + 180 negativas Barcelona**, mesmos 367 IDs para A/B. As 20 Barcelona do próximo treino ficam fora. A sinalizou 3/180 e B 24/180 nas Barcelona restantes, reutilizando previsões anteriores; não são resultados de um B retreinado. O diagnóstico anterior das 200 e a robustez sobre os 187 originais continuam como histórico.
