> DOCUMENTO HISTÓRICO — substituído em 2026-09-20 pelo protocolo A × B em ../metodologia.md. Preservado para rastreabilidade, incluindo alterações locais anteriores. Afirmações de execução, dados, autorização e conclusões abaixo são registros antigos; não constituem verificações desta revisão.

# Cronograma do TCC — Mai a Dez de 2026

> Plano de trabalho de Maio a Dezembro de 2026. Atualizar conforme necessário; manter histórico via commits.

## Premissas atuais

- **Estratégia experimental:** três modelos comparados (A1/A2/B) — ver `decisoes_tecnicas.md`
- **Fuzzylab/FIOCRUZ:** trabalhamos sob a premissa de que não haverá retorno a tempo. Caio é colaborador do projeto e tem acesso técnico legítimo
- **Hardware:** GPU local + Colab como backup para o K-fold

## Fases

| Fase | Período | Cor no Gantt |
|---|---|---|
| Preparação e dados | Mai 16 – Jul 31 | Cinza |
| Experimentos | Jul 15 – Out 15 | Teal |
| Escrita e defesa | Out 15 – Dez 20 | Roxo |

## Tarefas

| # | Tarefa | Início | Fim | Duração |
|---|---|---|---|---|
| 1 | Setup do repo + investigação inicial (concluído) | Mai 16 | Mai 16 | 1 dia |
| 2 | Proposta v3 + comunicação ao orientador | Mai 17 | Mai 24 | 1 semana |
| 3 | Download e exploração do dataset Zenodo | Mai 18 | Jun 15 | 4 semanas |
| 4 | Calibração do pipeline OpenCV + extração de ROIs | Jun 01 | Jul 15 | 6 semanas |
| 5 | Rotulagem das ROIs (estratégia a definir) | Jun 15 | Jul 31 | 6 semanas |
| 6 | Implementação e avaliação do Modelo A1 (entregue) | Jul 15 | Ago 05 | 3 semanas |
| 7 | Implementação e treino do Modelo A2 (RGB controle) | Jul 25 | Ago 25 | 4 semanas |
| 8 | Implementação e treino do Modelo B (proposta) | Ago 15 | Set 25 | 5 semanas |
| 9 | K-fold completo dos 3 modelos (5 sementes × 5 folds × 3 = 75 runs) | Set 10 | Out 10 | 4 semanas |
| 10 | Análise estatística + figuras | Out 01 | Out 31 | 4 semanas |
| 11 | Escrita do TCC | Out 15 | Nov 30 | 6 semanas |
| 12 | Revisão final + slides + defesa | Dez 01 | Dez 20 | 3 semanas |

## Marcos críticos (deadlines internas)

- **24 de Maio** — proposta v3 enviada ao orientador
- **30 de Junho** — dataset Zenodo organizado, pipeline calibrado
- **31 de Julho** — Modelo A1 reproduzido, baseline registrada
- **31 de Agosto** — A2 e B implementados e funcionando em escala pequena
- **10 de Outubro** — todas as 75 runs do K-fold concluídas, métricas salvas
- **31 de Outubro** — análise estatística pronta, figuras geradas
- **15 de Novembro** — draft completo do TCC para revisão do orientador
- **30 de Novembro** — versão final entregue
- **Dezembro** — apresentação e defesa

## Sobreposições intencionais

- Calibração do pipeline e rotulagem (Jun-Jul) rodam em paralelo: à medida que rotulamos um lote, já calibramos com ele
- Implementação de A2 começa antes de terminar A1 (reusam quase todo o código)
- Implementação de B começa enquanto A2 ainda treina
- K-fold completo só começa quando os três modelos estão funcionalmente prontos
- Escrita começa em meados de Outubro — esperar até Novembro é receita pra desespero

## Riscos identificados (em ordem de impacto)

1. **Rotulagem das ROIs** — maior risco escondido. Se cada imagem do Zenodo gerar 50-200 núcleos e for tudo manual, vira cratera de tempo. Mitigação: explorar se há rotulagem disponível no dataset Zenodo; se não, estratégia híbrida (rotular subset, treinar com poucos, auto-rotular o resto + revisão).

2. **Tempo de GPU para K-fold** — 75 treinos totais somando A1 + A2 + B (5 sementes × 5 folds × 3 modelos). Estimativa: 100-225h de GPU. Mitigação: planejar GPU própria em background; considerar Colab Pro+ em Setembro.

3. **Achado da divergência treino/inferência** — se Fuzzylab responder depois questionando, há plano definido (manter metodologia, ajustar discussão pontualmente).

4. **Imprevistos** (saúde, provas finais, problemas técnicos) — buffer mental de **2 semanas**. Bater no buffer é normal; passar dele é sinal de alerta.

## Histórico

- 2026-05-16 — Primeira versão (estratégia A vs B, 7 meses)
- 2026-05-16 — Revisão após achado e premissa de ausência da Fuzzylab: estratégia A1/A2/B, autorização removida como tarefa ativa

