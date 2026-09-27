# TCC — comparação A × B para detecção de Trypanosoma cruzi

> **B ativo substituído em 26/09/2026:** `experiments/runs/b_real_cpu_01/best.keras` agora contém o novo treino com união de regiões até 224 pixels. O modelo anterior foi removido a pedido do autor. Dados atuais: `data/processed/b_real_02_reduced/crops.csv` (3.129 treino, 778 validação); configuração: `configs/model_b_cpu_reduced.yaml`. Os resultados antigos de 98,70% e as instruções de transporte de `b_real_01` abaixo são históricos e não descrevem esse novo modelo. Conferência do novo checkpoint: `experiments/validation/b_replacement_20260926/verification.json`.

**Autores:** Victor Jacques e Caio Milão

**Orientador:** Prof. Rogério Mandelli

**Instituição:** UVA — Universidade Veiga de Almeida · Ciência da Computação

O estudo compara dois sistemas em imagens microscópicas inteiras: **A**, com inferência original e pesos congelados do Vision/FuzzyLab/FIOCRUZ; e **B**, a proposta com localização configurável e EfficientNet-B0. A melhoria de B é uma hipótese a testar.

## Por onde começar

1. [Preparar o computador](docs/ambiente.md): instalação Windows/CPU, limites da RX 6600 e transferência dos arquivos.
2. [Seguir o guia de treinamento](docs/guia_treinamento.md): preparar os dados, treinar B e comparar com A.
3. [Consultar o que falta](docs/status.md): prontidão e próximos passos.

O B atual completou 30 épocas; a época 23 foi selecionada pela menor perda de validação. São 674 imagens, divididas em 455 de treino, 114 de validação e 105 reservadas. O treino reduzido usa 3.129 recortes (3.053 positivos e 76 negativos); a validação usa 778 (740 positivos e 38 negativos). **Somente o ZIP público autorizado entra no treinamento.** A divisão é por imagem, sem independência entre animais comprovada. Os 98,70% pertenciam ao B anterior.

O modelo atual e seu histórico estão em `experiments/runs/b_real_cpu_01`. Consulte a [revisão geral](docs/revisao_geral.md) e os [próximos passos](docs/status.md). Há resultados pareados de 114 campos de validação e de 33 campos externos LABIMED, analisados separadamente. Faltam arquivos das galerias recentes nesta cópia local; sua recuperação está pendente. O painel `dashboard/` contém exemplos demonstrativos e não é fonte de resultados.

## Organização

| Pasta | Responsabilidade |
| --- | --- |
| `src/` | Regras de dados, localização, modelos, treino e avaliação |
| `scripts/` | Comandos para preparar, conferir e executar o experimento |
| `configs/` | Configurações dos dados, modelos e execuções |
| `models/model_a/` | Artefato original do A, congelado, e registro da cópia |
| `tests/` | Verificações automatizadas |
| `notebooks/` | Exploração e apresentação do fluxo |
| `data/` | Imagens, anotações, manifestos e recortes locais |
| `experiments/` | Resultados, checkpoints e registros de execução |
| `docs/` | Documentação vigente, organizada por finalidade |
| `tcc/` | Material de redação e figuras do trabalho acadêmico |
| `archive/` | Cópia compactada da documentação anterior, fora do fluxo de trabalho |

## Consultas específicas

| Assunto | Documento |
| --- | --- |
| Bases, anotações públicas e fontes de negativos | [Dados](docs/dados.md) |
| Revisão visual e formato das anotações | [Anotações](docs/anotacoes.md) |
| Regras e limitações do experimento | [Metodologia](docs/metodologia.md) |
| Objetivos e hipóteses do TCC | [Proposta](docs/proposta.md) |
| Bibliografia | [Referências](docs/referencias.md) |

## Conferir a instalação

No terminal da pasta que contém este README, após instalar o ambiente:

```powershell
.\.venv\Scripts\python.exe scripts/start_training.py --experiment configs/experiment_cpu.json --check-only
```

O comando informa as pendências sem iniciar treino. A configuração CPU é a opção preparada para o Windows com RX 6600. Dados, pesos e resultados não acompanham automaticamente o Git; use as instruções de transferência do ambiente.

## Modelos para a comparação

- **A:** `models/model_a/model_trained.keras`, caminho padrão de `scripts/run_model_a.py`; cópia idêntica ao original, sem novo treinamento.
- **B:** `experiments/runs/b_real_cpu_01/best.keras`; preserve também os arquivos de configuração, metadados e histórico nessa pasta.

Ambos estão dentro deste projeto. Para levar a comparação a outro computador, copie essas duas pastas além dos dados e do código. O ZIP inicial de entrega do treinamento não contém os modelos prontos.

Consulte [LICENSE](LICENSE) para o código. A origem e as condições de uso dos conjuntos de imagens ficam no documento de dados.
