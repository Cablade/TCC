# TCC — comparação A × B para detecção de Trypanosoma cruzi

**Autores:** Victor Jacques e Caio Milão

**Orientador:** Prof. Rogério Mandelli

**Instituição:** UVA — Universidade Veiga de Almeida · Ciência da Computação

O estudo compara dois sistemas em imagens microscópicas inteiras: **A**, com inferência original e pesos congelados do Vision/FuzzyLab/FIOCRUZ; e **B**, a proposta com localização configurável e EfficientNet-B0. A melhoria de B é uma hipótese a testar.

## Por onde começar

1. [Preparar o computador](docs/ambiente.md): instalação Windows/CPU, limites da RX 6600 e transferência dos arquivos.
2. [Seguir o guia de treinamento](docs/guia_treinamento.md): preparar os dados, treinar B e comparar com A.
3. [Consultar o que falta](docs/status.md): prontidão e próximos passos.

As 674 imagens utilizáveis já têm 2.715 pontos positivos importados. Ainda faltam negativos adequados, partições e recortes para o treino real. Os negativos externos encontrados são campos de doadores positivos e não resolvem sozinhos a independência dos grupos.

## Organização

| Pasta | Responsabilidade |
| --- | --- |
| `src/` | Regras de dados, localização, modelos, treino e avaliação |
| `scripts/` | Comandos para preparar, conferir e executar o experimento |
| `configs/` | Configurações dos dados, modelos e execuções |
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

Consulte [LICENSE](LICENSE) para o código. A origem e as condições de uso dos conjuntos de imagens ficam no documento de dados.
