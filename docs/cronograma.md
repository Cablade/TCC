# Cronograma do TCC — Mai a Dez de 2026

> Plano de trabalho semanal de Maio a Dezembro de 2026. Atualizar conforme necessário; manter o histórico das versões via commits.

## Fases

| Fase | Período | Cor no Gantt |
|---|---|---|
| Preparação e dados | Mai 16 – Jul 31 | Cinza |
| Experimentos | Jul 15 – Out 31 | Teal |
| Escrita e defesa | Out 15 – Dez 20 | Roxo |

## Tarefas

| # | Tarefa | Início | Fim | Duração |
|---|---|---|---|---|
| 1 | Autorização formal Fuzzylab/FIOCRUZ | Mai 16 | Jun 30 | ~6 semanas (background) |
| 2 | Setup do repo + investigação da divergência treino/inferência | Mai 16 | Jun 15 | 4 semanas |
| 3 | Download e exploração do dataset Zenodo | Jun 01 | Jun 30 | 4 semanas |
| 4 | Calibração do pipeline OpenCV + rotulagem das ROIs | Jun 15 | Jul 31 | 6 semanas |
| 5 | Replicação e avaliação do Modelo A no Zenodo | Jul 15 | Ago 15 | 4 semanas |
| 6 | Implementação do Modelo B (EfficientNet-B0 + técnicas) | Ago 01 | Set 05 | 5 semanas |
| 7 | Treino K-fold (5 sementes × 5 folds = 25 runs) | Set 05 | Set 30 | 4 semanas |
| 8 | Análise estatística (Wilcoxon, métricas, figuras) | Out 01 | Out 31 | 4 semanas |
| 9 | Escrita do TCC | Out 15 | Nov 30 | 6 semanas |
| 10 | Revisão final + slides + defesa | Dez 01 | Dez 20 | 3 semanas |

## Marcos críticos (deadlines internas)

- **30 de Junho** — dataset organizado, pipeline calibrado
- **31 de Julho** — Modelo A reproduzido, baseline registrada
- **30 de Setembro** — 25 runs do K-fold concluídas, métricas salvas
- **31 de Outubro** — análise estatística pronta, figuras geradas
- **15 de Novembro** — draft completo do TCC para revisão do orientador
- **30 de Novembro** — versão final entregue
- **Dezembro** — apresentação e defesa

## Sobreposições intencionais

- A formalização da autorização roda em background e não bloqueia nada
- Replicação do Modelo A (Jul-Ago) sobrepõe com o final da rotulagem
- Implementação do Modelo B (Ago) começa antes de terminar a replicação do A (sanity tests em paralelo)
- Escrita começa em meados de Outubro (não em Novembro) — esperar até Novembro é receita pra desespero

## Riscos identificados (em ordem de impacto)

1. **Rotulagem das ROIs** — maior risco escondido. Se cada imagem do Zenodo gerar 50-200 núcleos e for tudo manual, vira cratera de tempo. Mitigação: alinhar com a Fuzzylab/FIOCRUZ se já existe rotulagem disponível ou se há estratégia semi-automática.

2. **Tempo de GPU para K-fold** — 25 treinos do B (+25 do A, se re-treinar) podem somar 50-150h de GPU. Mitigação: planejar uso da GPU própria em background, considerar Colab Pro+ para Setembro.

3. **Divergência treino/inferência no Modelo A** — se confirmada, muda parte da análise. Mitigação: investigar na primeira semana e documentar no `docs/decisoes_tecnicas.md`.

4. **Imprevistos** (saúde, provas finais, problemas técnicos) — reservar **2 semanas de buffer mental**. Bater no buffer é normal; passar dele é sinal de alerta.

## Histórico

- 2026-05-16 — Primeira versão do cronograma.
