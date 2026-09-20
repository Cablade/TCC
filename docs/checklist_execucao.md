# Checklist de execução — A × B

> Atualizado em 20/09/2026. Evidências, comandos e artefatos no [relatório de execução](execucao_2026-09-20.md). Marcas concluídas indicam o nível de evidência descrito; testes sintéticos não demonstram qualidade real.

## Documentação e origem

- [x] Documentação ativa coerente com A original congelado e B proposto, avaliados em imagens inteiras.
- [x] Documentação anterior e edição local da proposta preservadas em `docs/historico`.
- [x] Metodologia central, critérios de correspondência e limitações registrados.
- [x] Commits do TCC e da referência local VisionCruzi, hash do A e mapeamento de classes registrados.
- [ ] Confirmar relação com `Cablade/Vision`, inacessível na consulta pública desta execução.
- [ ] Obter histórico do treino A e confirmar possível sobreposição com dados de avaliação.

## Dados e referência

- [x] Inventário dos quatro ZIPs: 188 JPGs, 106 conteúdos únicos; 82 cópias controladas por manifesto.
- [x] Lote 1: 59 arquivos, 58 únicos, uma duplicata por SHA-256; originais preservados.
- [x] Partição persistida do lote 1 somente em development; nenhuma proporção real inventada.
- [x] Validação de grupos, hashes e coordenadas implementada e testada sinteticamente.
- [x] Template 1 com rótulos desconhecidos, revisão pendente e dimensões verificadas.
- [ ] Confirmar animal/lâmina e relações entre originais, CZI, convertidos e filtrados.
- [ ] Anotações reais revisadas por pessoa qualificada, com positivos, negativos e cobertura.
- [ ] Definir divisão viável por grupos/classes e teste independente; preservar os 58 hashes já usados em desenvolvimento.
- [ ] Conversão/inspeção dos 48 CZI, se forem necessários ao experimento.

## Modelo A

- [x] Fluxo original instrumentado: HSV, morfologia, recorte mascarado, RGB, resize e preprocessamento ResNet50.
- [x] Artefato carregado com TensorFlow/Keras 2.15, sem retreinamento.
- [x] Cópia normalizada auditada: 329 tensores preservados, original intacto; 320 tensores de camadas carregados confrontados.
- [x] Dois casos sintéticos diferenciais com o código de referência; classificador real também executado com recorte sintético.
- [x] Inferência real em 58 imagens: zero pixels no primeiro HSV, zero regiões, zero classificações e nenhum erro.
- [x] Tabela, JSON, sobreposições e tempos; `sem_regioes` separado de classificação negativa.
- [ ] Verificar compatibilidade em Linux caso esse seja o ambiente do experimento; não testado nesta máquina Windows.

## Modelo B

- [x] Localização black-hat/Otsu executável e separada do A; parâmetros explicitamente provisórios.
- [x] Geometria/contexto/bordas iguais no treino e inferência; verificações sintéticas.
- [x] Candidatos desconhecidos não viram negativos; interseção de todo o crop com positivos verificada.
- [x] RGB float32 [0,255], sem divisão duplicada; aumento somente no treino.
- [x] Fine-tuning, caso zero camadas e Batch Normalization congelada verificados.
- [x] Seleção por val_loss e recarga do mesmo best.keras; config, seed, versões, hashes e histórico salvos.
- [x] Smoke de uma etapa, pesos aleatórios, salvamento, recarga e inferência; sem treino completo.
- [x] Diagnóstico real somente da localização: 9.603 candidatos, nenhum rótulo supervisionado criado.
- [ ] Calibrar localização usando apenas desenvolvimento/validação com referência revisada.
- [ ] Treinamento supervisionado real e avaliação do checkpoint real no teste reservado.

## Comparação e notebooks

- [x] Cinco notebooks reorganizados, executados de cima para baixo em modo sintético e entregues sem saídas antigas.
- [x] Comparação CLI sintética, associação um a um e FN por ausência de candidatos testados.
- [x] Mesmo universo de IDs; falhas/ausências mantidas, sem inventar decisão negativa.
- [x] Origem, partição, hash do manifesto e treino sintético verificados na CLI de comparação.
- [x] Métricas auxiliares de recortes separadas; AUC indisponível para classe única; nenhuma matriz de confusão sem referência.
- [x] Custos e ambiente de smoke/diagnóstico registrados; treino A indisponível.
- [x] 24 testes passaram; compilação e validação de notebooks registradas.
- [ ] Comparação real com referência revisada e parâmetros fixados antes do teste.
- [ ] Intervalos por grupos independentes somente se o planejamento e o número de grupos permitirem.

## Próximo passo

Revisar `data/annotations/Lote_1_pending.json` com alguém qualificado da equipe e confirmar os grupos de aquisição. As 58 imagens desse arquivo já pertencem ao desenvolvimento. Depois, justificar uma reserva independente considerando os 48 JPGs adicionais e suas possíveis relações com o material já inspecionado. Sem essas informações, treino real e conclusões de qualidade continuam pendentes.
