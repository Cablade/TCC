# Estado atual — 14/10/2026

A parte experimental terminou. O viés de origem do B foi corrigido, o protocolo foi congelado e o teste final de 105 imagens foi aberto uma única vez. Falta escrever a monografia.

## O que foi feito depois da revisão de 13/10/2026

1. **Negativos difíceis murinos.** O B anterior rodou nas 455 imagens de treino de camundongo; 600 regiões positivas foram revisadas por Caio (517 negativas, 46 parasitas, 37 incertas). Só as 517 negativas entraram no treino, em `data/processed/b_hardneg/`. Registro: `data/annotations/hard_negatives_20261013/` e `data/processed/b_hardneg/assembly.json`.
2. **Retreino com cinco sementes.** `b_hardneg_s42` (avaliado, em `experiments/runs/b_atual/`) e as sementes 123, 456, 789 e 1024 (`experiments/runs/b_hardneg_s*`), todas declaradas antes do treino.
3. **Desenvolvimento.** Nas mesmas 367 imagens de 06/10, o B passou de 12.296 para 3.232 regiões positivas nos campos murinos, manteve a cobertura (423/450 pontos) e zerou os alarmes em negativos humanos (de 3 para 0 imagens). Saída: `experiments/comparison/a_vs_b_hardneg_20261013/`. Precisão revisada numa amostra aleatória de 200 regiões: `data/annotations/precision_B_val_20261013/precision.json`.
4. **A no domínio original.** Rodado nas lâminas da FIOCRUZ, só em pasta temporária e sem guardar imagens: gera regiões nas versões já processadas (24 de 48 convertidas no Fiji; 14 de 22 filtradas por distância) e nenhuma nas fotos originais (0 de 59 do aparelho; 0 de 59 de 2023). Sem referência anotada, isso mostra só que o fluxo funciona com o pré-processamento para o qual foi feito. Números agregados em `experiments/validation/model_a_original_domain_20261013/summary.json`.
5. **Congelamento.** `data/protocol/protocolo_congelado.json` registra os SHA-256 de 21 arquivos (código de avaliação, metodologia, plano estatístico, modelos, configuração, dados de treino, precisão de desenvolvimento e partição de teste). Alterar qualquer um deles é desvio de protocolo.
6. **Teste final.** Aberto em 14/10/2026 (`data/protocol/teste_aberto.json`). Saída: `experiments/final_test_20261014/`. Precisão revisada às cegas em `data/annotations/precision_teste_final_20261014/`, com segundo avaliador (Victor) em 50 regiões.

## Resultado do teste final

| Desfecho | A | B | B − A (IC 95%) |
| --- | ---: | ---: | ---: |
| Cobertura dos 441 pontos | 0,0% | 91,6% | 91,6% [88,9%; 94,2%] |
| Imagens positivas sinalizadas (105) | 17,1% | 100,0% | 82,9% [75,2%; 89,5%] |
| Negativos sem alarme (253, auxiliar) | 98,8% | 100,0% | 1,2% [0,0%; 2,8%] |
| Precisão revisada por região | 0% (0/23) | 53,3% [44,9%; 62,5%] | — |

McNemar exato nas positivas: 87 × 0 (p Holm = 2,6e-26); nas negativas: 3 × 0 (p = 0,25). Kappa de Cohen entre avaliadores: 0,73 em três categorias, 0,90 no binário sem incertas.

A referência positiva é parcial: regiões sem ponto publicado não são automaticamente falsos positivos, e a precisão vem da revisão humana. Os negativos são humanos (Kaggle/Barcelona), de outra aquisição; servem como resultado auxiliar, não como teste do mesmo domínio.

Figuras e legendas: [tcc/figuras/teste_final_20261014](../tcc/figuras/teste_final_20261014/LEIA-ME.md). Texto: [resultados](../tcc/resultados_atuais.md).

## O que falta

_ FINALIZADO

## Registros

- Histórico das limpezas: [archive/README.md](../archive/README.md). A limpeza de 14/10/2026 está em `archive/limpeza_pos_teste_final_20261014.zip`.
- O caminho de cada etapa da correção está em [roteiro_correcao_vies.md](roteiro_correcao_vies.md).
