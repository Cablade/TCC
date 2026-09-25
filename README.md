# TCC — comparação A × B para detecção de Trypanosoma cruzi

**Autores:** Victor Jacques e Caio Milão

**Orientador:** Prof. Rogério Mandelli

**Instituição:** UVA — Universidade Veiga de Almeida · Ciência da Computação

O estudo compara dois sistemas em imagens microscópicas inteiras: **A**, com inferência original e pesos congelados do Vision/FuzzyLab/FIOCRUZ; e **B**, a proposta com localização configurável e EfficientNet-B0. A melhoria de B é uma hipótese a testar.

## Por onde começar

1. [Preparar o computador](docs/ambiente.md): instalação Windows/CPU, limites da RX 6600 e transferência dos arquivos.
2. [Seguir o guia de treinamento](docs/guia_treinamento.md): preparar os dados, treinar B e comparar com A.
3. [Consultar o que falta](docs/status.md): prontidão e próximos passos.

O primeiro treino real está preparado: 674 imagens utilizáveis, divididas em 455 para treino, 114 para validação e 105 reservadas para teste; 7.019 recortes de treino/validação. A referência combina 2.715 pontos positivos publicados e 29 regiões negativas revisadas em oito imagens. **Somente o ZIP público autorizado entra no treinamento.** A divisão é por imagem, sem independência entre animais comprovada; os poucos negativos e a referência incompleta do teste limitam a avaliação científica.

Para enviar ao amigo, use `entrega_modelo_b_20260925.zip` junto do ZIP original de imagens. O [guia](docs/guia_treinamento.md) explica instalação, ajuste automático de caminhos e treinamento. Não copie o ambiente Python nem os históricos locais.

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
