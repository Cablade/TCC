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

- [Base ativa e auditoria do ZIP](docs/dataset_atual.md): única fonte local selecionada, integridade e pendências.
- [Fontes candidatas de imagens negativas](docs/fontes_negativas.md): links, diferenças entre bases e critérios de uso.
- [Guia prático de treinamento](docs/guia_treinamento.md): do primeiro teste rápido à preparação, treino real e comparação A × B.
- [Proposta atual](docs/proposta_v3.md): problema, objetivos e hipóteses A × B; nome do arquivo mantido para preservar os links.
- [Metodologia](docs/metodologia.md): protocolo central, regras de avaliação e limitações.
- [Dados e anotações](data/README.md): inventário, partições e referência supervisionada.
- [Checklist de execução](docs/checklist_execucao.md): entregas e dependências.
- [Execução histórica de 20/09/2026](docs/historico/execucao_2026-09-20.md): verificações técnicas; a base de dados daquela execução foi descartada.
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

Os comandos atuais estão no [guia de treinamento](docs/guia_treinamento.md). A preparação do novo ZIP está documentada em [base ativa](docs/dataset_atual.md). O [checklist](docs/checklist_execucao.md) separa o trabalho concluído das dependências humanas.

## Estado e limites

Esta revisão começou pela atualização efetiva da documentação. A base inspecionada do TCC é o commit `e056cd60739d2f4d6f74b329a24beb81b6ae916b`, com alterações locais preservadas. Código existente não equivale a teste concluído. O checklist distingue implementação, execução sintética, execução real e pendências.

Desde 22/09/2026, a única base local ativa é `trypoastigote_images.zip`: 675 JPGs únicos, dos quais 674 passaram pela decodificação completa e um foi excluído por erro de leitura. Os dados anteriores não entram no experimento. Anotações revisadas e partições finais ainda estão pendentes; as pastas `train/test` da fonte não foram adotadas automaticamente.

Permanecem as verificações técnicas anteriores do carregamento do A (329 tensores preservados), do treino sintético com salvamento/recarga de B e dos cinco notebooks em modo sintético. Diagnósticos reais feitos na base descartada não são resultados desta base. Sem anotações revisadas, não há métricas supervisionadas reais nem superioridade demonstrada do B.

Dados, pesos e resultados volumosos permanecem fora do Git conforme a política do projeto. Consulte [LICENSE](LICENSE) para o código; registre a licença e a autorização de uso de cada fonte de dados sem deduzi-las apenas da disponibilidade local.
