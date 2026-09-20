# TCC — comparação dos sistemas A e B para localizar e classificar regiões suspeitas de *Trypanosoma cruzi*

**Autores:** Victor Jacques e Caio Milão

**Orientador:** Prof. Rogério Mandelli

**Instituição:** UVA — Universidade Veiga de Almeida · Ciência da Computação

O estudo compara **dois sistemas completos**, recebendo as mesmas imagens microscópicas inteiras. O **Modelo A** reproduz a inferência do Vision/FuzzyLab/FIOCRUZ com os pesos entregues e fixos. O **Modelo B** é a proposta do TCC, com localização configurável e classificador EfficientNet-B0. Sua eventual melhoria será testada; ainda não é uma conclusão.

O arquivo `.keras` do A representa somente o classificador. Segmentação, recortes, ordem dos canais, pré-processamento e decisão original também integram o sistema de referência. O A não será retreinado. O B pode modificar localização e classificação; um resultado diferente não poderá ser atribuído a uma técnica isolada.

## Protocolo atual

- Avaliação principal em **imagem inteira**, com os mesmos IDs reservados para A e B.
- Separação por animal/lâmina confiável ou, quando indisponível, por imagem original, antes de recortes e aumentos de dados.
- Duplicatas identificadas por conteúdo e excluídas por manifesto, mantendo os originais.
- Ausência de anotação não significa imagem ou região negativa. Treino e métricas reais exigem referência revisada por alguém qualificado.
- Histórico e quantidade de dados de treino do A desconhecidos: não se presume igualdade de treinamento nem ausência de sobreposição com o teste.
- Métricas de recortes são auxiliares; cobertura da localização, detecção final e decisão por imagem são medidas distintas.

## Documentação

- [Proposta atual](docs/proposta_v3.md): problema, objetivos e hipóteses A × B; nome do arquivo mantido para preservar os links.
- [Metodologia](docs/metodologia.md): protocolo central, regras de avaliação e limitações.
- [Dados e anotações](data/README.md): inventário, partições e referência supervisionada.
- [Checklist de execução](docs/checklist_execucao.md): entregas e dependências.
- [Execução de 20/09/2026](docs/execucao_2026-09-20.md): comandos, testes novos, diagnóstico real e arquivos gerados.
- [Decisões técnicas](docs/decisoes_tecnicas.md): escolhas atuais e sua justificativa.
- [Cronograma](docs/cronograma.md): etapas condicionadas aos dados disponíveis.
- [Referências](docs/referencias.md): bibliografia a conferir para o texto final.
- [Histórico substituído](docs/historico/README.md): documentos antigos preservados, sem validar suas alegações.

## Execução

Use **Python 3.10 ou 3.11** com as versões de [requirements.txt](requirements.txt); TensorFlow 2.15 não atende Python 3.12+. Nesta máquina já existe `.venv` com Python 3.11.15 e TensorFlow/Keras 2.15. Os notebooks usam fixtures sintéticas por padrão; variáveis `TCC_*` permitem configurar caminhos reais.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyter notebook
```

Verificações sem treino completo nem download de pesos:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/train_model_b.py --smoke
.\.venv\Scripts\python.exe scripts/validate_notebooks.py
```

Fluxo de trabalho, reutilizando os nomes existentes:

1. [01_exploracao_dataset.ipynb](notebooks/01_exploracao_dataset.ipynb) — inventário, origens, duplicatas e grupos.
2. [02_pipeline_segmentacao.ipynb](notebooks/02_pipeline_segmentacao.ipynb) — dados, anotações, partições e localização.
3. [03_modelo_a_baseline.ipynb](notebooks/03_modelo_a_baseline.ipynb) — A original com instrumentação.
4. [04_modelo_b_treino.ipynb](notebooks/04_modelo_b_treino.ipynb) — B, verificação curta e treinamento condicionado aos dados.
5. [05_analise_estatistica.ipynb](notebooks/05_analise_estatistica.ipynb) — comparação dos sistemas em imagens inteiras.

Os comandos experimentais exatos e artefatos estão no [relatório de execução](docs/execucao_2026-09-20.md). O [checklist](docs/checklist_execucao.md) separa o trabalho concluído das dependências humanas.

## Estado e limites

Esta revisão começou pela atualização efetiva da documentação. A base inspecionada do TCC é o commit `e056cd60739d2f4d6f74b329a24beb81b6ae916b`, com alterações locais preservadas. Código existente não equivale a teste concluído. O checklist distingue implementação, execução sintética, execução real e pendências.

Nesta execução foram reconfirmados o carregamento do A, a preservação de 329 tensores na cópia normalizada e a ausência de regiões nas 58 imagens únicas do lote Luiz. O B passou por uma etapa sintética de treino, salvamento e recarga. Os cinco notebooks executaram em modo sintético. Esses testes novos estão separados dos relatos antigos no relatório. Sem anotações revisadas, não há métricas supervisionadas reais nem superioridade demonstrada do B.

Dados, pesos e resultados volumosos permanecem fora do Git conforme a política do projeto. Consulte [LICENSE](LICENSE) para o código; registre a licença e a autorização de uso de cada fonte de dados sem deduzi-las apenas da disponibilidade local.
