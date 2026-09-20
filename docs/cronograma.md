# Cronograma do TCC — plano A × B

> Revisado em 2026-09-20. O cronograma antigo foi [arquivado](historico/cronograma_anterior.md). As datas abaixo são metas de trabalho, não declarações de conclusão. Confirmar os prazos institucionais com o orientador.

| Etapa | Meta indicativa | Entrega e condição de conclusão |
| --- | --- | --- |
| Documentação e protocolo | Setembro/2026 | Proposta A × B, metodologia, checklist e separação entre relatos e testes atuais |
| Inventário e anotações | Setembro/2026 | Hashes, duplicatas, origens/grupos, referência revisada e estratégia viável de reserva |
| A original e infraestrutura B | Setembro–outubro/2026 | A instrumentado; B com localização e treino coerentes; verificações sintéticas e diagnóstico real |
| Treino real e comparação | Outubro/2026, condicionado aos dados | Referência qualificada, treino/validação separados, teste reservado; critérios congelados antes da avaliação |
| Análise e texto | Outubro–novembro/2026 | Resultados ou limitações documentados, figuras, discussão de falhas e custos |
| Revisão e apresentação | Novembro–dezembro/2026 | Texto revisto com orientador e apresentação conforme calendário institucional |

## Ordem e dependências

1. Atualizar documentação primeiro; depois implementar infraestrutura, dados e avaliação.
2. Inventariar grupos e classes antes de determinar divisões. A ausência de reserva viável precisa constar no texto.
3. Localizar/revisar anotações em paralelo à execução instrumentada do A e às verificações sintéticas do B.
4. Ajustar B apenas no desenvolvimento e selecionar checkpoints na validação.
5. Executar comparação final somente após fixar os critérios e reservar os mesmos IDs para os dois sistemas.
6. Escrever metodologia e limitações desde já; acrescentar resultados reais somente quando existirem.

## Riscos e resposta

| Dependência | Efeito | Trabalho que pode continuar |
| --- | --- | --- |
| Anotações ausentes ou sem revisão | Impede treino supervisionado real e métricas finais válidas | Inventário, execução técnica, instrumentação, testes sintéticos e metodologia |
| Poucas lâminas/animais independentes | Pode impedir teste reservado ou intervalos confiáveis | Quantificar limitação e planejar coleta, sem fabricar independência de recortes |
| Histórico de treino do A incompleto | Impede afirmar igualdade de treino e independência em relação a seu treino | Reproduzir pesos e inferência disponíveis, registrar limitação |
| Diferenças de aquisição/resolução | Pode reduzir cobertura e desempenho | Diagnóstico no desenvolvimento e documentação do domínio |
| Dependências computacionais | Pode impedir execução local de modelos | Validar componentes leves e preparar ambiente compatível |

Não há obrigação de um número fixo de folds, sementes ou treinos extensos. Repetições do B são condicionadas à viabilidade e não criam novas abordagens. A disponibilidade técnica dos arquivos não comprova autorização documental; a situação deve ser registrada com as evidências fornecidas pela equipe, sem pressupor resposta ou silêncio institucional.
