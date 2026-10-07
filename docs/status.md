# Estado atual — 06/10/2026

Novo treinamento, arquivamento do B anterior e nova comparação A/B concluídos. Somente A original e B atual participam do fluxo ativo.

## Modelos e treinamento

- A original preservado: `models/model_a/model_trained.keras`.
- B atual: `experiments/runs/b_val_01/best.keras`. EfficientNetB0, 17 épocas, melhor época 10 por `val_loss` (0,21533), aproximadamente 15,2 minutos em CPU.
- Treino: 4.381 recortes (3.053 positivos/1.328 negativos), incluindo 80 novos negativos de 20 originais Barcelona. Validação preservada: 1.070 recortes (740 positivos/330 negativos). Cada recorte uma vez por época, pesos por classe, sem oversampling ou undersampling.
- `data/processed/b_next/` é o conjunto efetivamente treinado. Ele compartilha os 5.371 recortes anteriores com `b_real_01`; preservar ambas as pastas.
- B anterior e seus 14 arquivos arquivados e conferidos em `archive/b_anterior_barcelona20_20261006/b_val_01/`. Protocolos e páginas antigas identificam esse checkpoint histórico.

O bloqueio de assinatura do Python pelo Windows foi resolvido com Python oficial 3.11.9 assinado, mantendo TensorFlow/Keras 2.15 e os pacotes instalados. Nenhuma política de segurança foi alterada. Registro em `data/protocol/retrain_b_barcelona20_20261006/environment_repair.json`.

## Nova comparação

Inferência refeita para ambos os modelos sobre os mesmos 367 IDs, sem reutilizar previsões antigas. Saída: `experiments/comparison/a_vs_b_barcelona20_20261006/`.

| Grupo | A original | B atual |
| --- | ---: | ---: |
| 114 positivas: imagens sinalizadas | 27 | 114 |
| 450 pontos positivos publicados: associados a regiões positivas | 0 | 424 |
| 253 negativas: imagens com falso alarme | 3 | 3 |
| 253 negativas: regiões positivas | 3 | 5 |

Nenhum erro de execução. Nos mesmos 180 negativos Barcelona, o B anterior sinalizou 24 imagens; o novo sinalizou 3 (redução observada de 87,5%), conservando a cobertura de 424/450 pontos. A referência positiva é parcial: regiões sem ponto associado não podem ser automaticamente declaradas falsos positivos.

Tempos medidos nesta execução: aproximadamente 28,35 segundos para A e 296,30 para B, em CPU, duas threads e sem exportação PNG durante a medição. Uma execução sequencial não constitui benchmark repetido.

[Gráficos e exemplos atuais](../tcc/figuras/a_vs_b_barcelona20_20261006/index.html), [texto dos resultados](../tcc/resultados_atuais.md) e [divisão visual 20/180](../data/protocol/barcelona_split_20261006/index.html).

## Escopo e conferência

As 20 Barcelona de treino foram escolhidas com semente 42 e balanceamento por tipo celular, sem consultar previsões; estão excluídas da comparação por IDs, grupos, bytes e pixels. A reserva foi feita após o diagnóstico inicial: as 180 restantes constituem desenvolvimento, não teste final independente. As 105 imagens do teste final continuam reservadas.

Negativos Kaggle/Barcelona são originais com ausência de parasita visível declarada por Caio. Isso não equivale a laudo clínico. Barcelona contém células individuais humanas/CellaVision, distintas dos campos positivos murinos; a independência entre lâminas/animais não foi demonstrada. A apresentação agora agrupa 114 imagens positivas e 253 negativas. Origens e diagnóstico por fonte permanecem nos registros técnicos, sem acurácia global ou conclusão clínica misturando aquisições.

132 testes passaram. Checkpoints, entradas do treinamento, recortes, pareamento e links das figuras conferidos em `experiments/validation/retrain_b_barcelona20_20261006/audit.json`.

O diagnóstico antigo das 200 Barcelona e as 561 variações de robustez pertencem ao B arquivado; não foram repetidos com o B atual. Consulte [histórico após o retreino](../archive/README.md). LABIMED e arquivos privados permanecem fora do fluxo ativo; históricos e limpezas anteriores estão em `archive/`.

Próximo: conferir os exemplos atuais com o orientador e congelar o protocolo antes de abrir o teste final.

Limpeza de 06/10/2026: quatro comparações do B anterior, relatórios e utilitários legados retirados da rotina e preservados em `archive/limpeza_pos_retreino_20261006.zip`. Fontes, revisões, partições, recortes compartilhados, modelos e comparação atual preservados. Conferência: `experiments/validation/cleanup_pos_retreino_20261006/audit.json`.
