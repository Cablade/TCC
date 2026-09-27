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

Os 33 campos externos são desenvolvimento, não teste independente. Caio declarou na conversa ausência de parasita visível nos campos e nos 99 recortes selecionados. Os JSONs e HTMLs dessa revisão estão ausentes nesta cópia local: recuperar o vínculo individual antes de publicar a análise reproduzível dos 99 recortes.

## Verificação atual

86 testes existentes e 3 testes adicionais do gráfico passaram. A auditoria conferiu os quatro hashes de entrada do relatório, o checkpoint B e o pareamento dos 114 e dos 33 IDs. Registro: `experiments/validation/revisao_geral_20260927/audit.json`. O gerador separa erros, ausência de regiões e regiões sem suspeita e exporta sem depender de janela Tcl/Tk. Os testes adicionais estão em `tests/test_tcc_figures.py`.

## Próximos passos e cronograma

Sequência por entregas, sem datas presumidas:

1. Recuperar os registros individuais e os geradores das galerias ausentes; conferir contra as predições preservadas.
2. Consolidar gráficos descritivos e discutir os alarmes externos separadamente da cobertura dos pontos de validação.
3. Fechar com o orientador o nível da referência e os limites de generalização. O TCC não depende de B vencer A.
4. Se necessário, planejar outra versão de B com negativos de desenvolvimento. Campos usados para corrigir B não servirão de teste independente dessa versão.
5. Congelar o protocolo e completar a referência antes da avaliação final; redigir resultados e limitações.
