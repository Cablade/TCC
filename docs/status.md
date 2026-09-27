# Estado do experimento — 27/09/2026

Veja a [revisão geral](revisao_geral.md) para achados, gráficos possíveis e limpeza. A documentação anterior está preservada em `archive/documentacao_pre_revisao_20260927.zip`, com hashes conferidos.

## Versão vigente

- A original: `models/model_a/model_trained.keras`, sem retreinamento.
- B reduzido: `experiments/runs/b_real_cpu_01/best.keras`; hash `5ff1aba014490a5ca8fbc6435e764b417e3e6af687a61245ae8d5337a150ed1a`.
- Configuração: `configs/model_b_cpu_reduced.yaml`; 30 épocas realizadas, melhor época 23; 1.063,54 segundos de treino registrados.
- Treino: 455 imagens, 3.129 recortes (3.053 positivos / 76 negativos).
- Validação: 114 imagens, 778 recortes (740 positivos / 38 negativos).
- Teste reservado: 105 imagens; não executar para escolher parâmetros.
- Referência: `data/annotations/experimento_reference_v2.json`; independência por animal/lâmina e referência exaustiva não demonstradas.

Os 25.695 candidatos são a saída de inferência do B nas 114 imagens inteiras, não o tamanho do treino. Os números de 7.019 recortes, 98,70% e época 19 pertencem à versão anterior.

## Resultados disponíveis

| Medida | A | B |
| --- | ---: | ---: |
| Validação: imagens sinalizadas / 114 | 27 | 114 |
| Validação: regiões positivas | 42 | 7.758 |
| Validação: tempo do algoritmo | 32,37 s | 281,87 s |
| Externas LABIMED: imagens sinalizadas / 33 | 20 | 33 |
| Externas LABIMED: regiões positivas | 140 | 5.277 |

Fontes: `experiments/results/comparacao_val_reduced_01.json` e `experiments/runs/{a,b}_labimed_neg_20260927/predictions.json`. O diagnóstico pontual anterior registra 0/450 pontos associados às regiões positivas de A e 424/450 de B. Referência parcial impede chamar todas as regiões sem associação de falsos positivos. A auditoria das 42 regiões do A reproduziu as coordenadas dentro dos arquivos, incluindo bordas escuras do campo circular.

Os 33 campos externos são desenvolvimento, não teste independente. Caio declarou na conversa ausência de parasita visível nos campos e nos 99 recortes selecionados. As galerias foram reconstruídas. O vínculo dos 99 recortes foi conferido pixel a pixel contra as imagens originais e suas caixas. Os arquivos `review_reconstructed.json` registram a declaração da conversa; não são os JSONs originais perdidos nem uma nova revisão especializada. Registro técnico: `experiments/validation/consolidacao_20260927/recovery.json`.

## Verificação atual

Os 92 testes da suíte passaram após a consolidação. A auditoria conferiu os quatro hashes de entrada do relatório, o checkpoint B e o pareamento dos 114 e dos 33 IDs. A cobertura pontual foi recalculada: 425 propostas e 424 regiões positivas associadas para B; zero para A. O gerador separa os estados de execução, usa associação um a um e exporta sem depender de janela Tcl/Tk. Os registros atuais estão em `experiments/validation/consolidacao_20260927/`.

## Próximos passos e cronograma

Sequência por entregas, sem datas presumidas:

1. Concluído: três galerias reconstruídas (33 campos externos, 99 regiões B e 456 recortes comuns), com hashes/pixels conferidos.
2. Concluído: 11 figuras em PDF/PNG, CSVs, legendas e índice em `tcc/figuras/consolidado_20260927`; texto em `tcc/resultados_preliminares.md`. Painel demonstrativo e atualizador arquivados em ZIP verificado.
3. Fechar com o orientador o nível da referência e os limites de generalização. O TCC não depende de B vencer A.
4. Se necessário, planejar outra versão de B com negativos de desenvolvimento. Campos usados para corrigir B não servirão de teste independente dessa versão.
5. Congelar o protocolo e completar a referência antes da avaliação final; redigir resultados e limitações.
