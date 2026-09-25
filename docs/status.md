# Estado do experimento e próximos passos

Atualizado em 24/09/2026. Este é o único registro ativo de prontidão; resultados antigos não são tratados como resultados da base atual.

## Concluído

- Base principal: 675 JPGs únicos, 674 decodificáveis e uma exclusão documentada.
- Referência positiva: 2.715 pontos em 674 imagens; suplementos conferidos byte a byte.
- Fonte externa LABIMED: 36 campos auditados (13 negativos, 23 positivos), com 30 caixas; todos os negativos finos pertencem a um participante.
- Modelo A congelado: carregamento auditado e preservação de 329 tensores; mapeamento de classes registrado.
- Modelo B: extração, treino, salvamento/recarga e comparação implementados; verificações sintéticas concluídas.
- Ferramenta de revisão visual, transporte com SHA-256 e perfil CPU para Windows preparados.
- Em 24/09, 60 testes passaram. Os cinco notebooks foram executados sinteticamente na revisão anterior. O ambiente CPU local foi conferido; o PC do amigo ainda não foi testado.

## Para iniciar o treino real

1. Revisar negativos adequados na base principal, preservando os positivos públicos. A referência resultante deve ser `data/annotations/experimento_reference.json`; não partir do template vazio antigo. Consulte [anotações](anotacoes.md).
2. Confirmar grupos e definir partições antes dos recortes e ajustes. Persistir `data/splits/experimento/images.csv`. Não repartir o único participante negativo externo para fabricar independência.
3. Calibrar a localização somente em desenvolvimento/validação e gerar `data/processed/b_real_01/crops.csv`, com as duas classes em treino e validação.
4. Conferir o computador e executar o lançador conforme o [guia de treinamento](guia_treinamento.md).

Na última conferência, faltavam essas três entradas (partições, referência completada e recortes). **Nenhum treinamento supervisionado real nem comparação final foi concluído.** O número de testes aprovados não mede desempenho do modelo.

## Para concluir a avaliação e o texto

- Obter referência suficiente para a avaliação final e manter o teste reservado.
- Registrar a limitação de grupos por imagem quando não houver identificação biológica.
- Esclarecer histórico de treino do A e possível sobreposição com o teste; confirmar a relação entre os repositórios Vision e VisionCruzi.
- Executar A e B nos mesmos IDs, registrar falhas, custo e métricas previstas na [metodologia](metodologia.md).
- Conferir bibliografia e escrever resultados sem antecipar superioridade do B.

<a id="cronograma"></a>

## Cronograma

Metas indicativas herdadas do planejamento; confirmar prazos institucionais com o orientador.

| Etapa | Meta indicativa | Entrega e condição de conclusão |
| --- | --- | --- |
| Documentação e protocolo | Setembro/2026 | Proposta A × B, metodologia, checklist e separação entre relatos e testes atuais |
| Inventário e anotações | Setembro/2026 | Hashes, duplicatas, origens/grupos, referência revisada e estratégia viável de reserva |
| A original e infraestrutura B | Setembro–outubro/2026 | A instrumentado; B com localização e treino coerentes; verificações sintéticas e diagnóstico real |
| Treino real e comparação | Outubro/2026, condicionado aos dados | Referência qualificada, treino/validação separados, teste reservado; critérios congelados antes da avaliação |
| Análise e texto | Outubro–novembro/2026 | Resultados ou limitações documentados, figuras, discussão de falhas e custos |
| Revisão e apresentação | Novembro–dezembro/2026 | Texto revisto com orientador e apresentação conforme calendário institucional |
