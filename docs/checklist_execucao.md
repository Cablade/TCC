# Checklist de execução — A × B

> Atualizado em 22/09/2026. Fonte atual em [base ativa](dataset_atual.md); verificações técnicas anteriores no [histórico](historico/execucao_2026-09-20.md). Marcas concluídas indicam o nível de evidência descrito; testes sintéticos não demonstram qualidade real.

## Documentação e origem

- [x] Documentação ativa coerente com A original congelado e B proposto, avaliados em imagens inteiras.
- [x] Documentação anterior e edição local da proposta preservadas em `docs/historico`.
- [x] Metodologia central, critérios de correspondência e limitações registrados.
- [x] Commits do TCC e da referência local VisionCruzi, hash do A e mapeamento de classes registrados.
- [ ] Confirmar relação com `Cablade/Vision`, inacessível na consulta pública desta execução.
- [ ] Obter histórico do treino A e confirmar possível sobreposição com dados de avaliação.

## Dados e referência

- [x] Base local única: `trypoastigote_images.zip`; ZIPs e manifestos anteriores excluídos do experimento.
- [x] Origem Zenodo 5123062 confirmada pelo MD5 publicado; SHA-256 local registrado.
- [x] Inventário de 675 JPGs únicos; decodificação completa de 674, uma exclusão de integridade; original preservado.
- [x] Validação de grupos, hashes e coordenadas implementada e testada sinteticamente.
- [x] Template da base ativa com 674 registros, rótulos desconhecidos e revisão pendente.
- [x] Fontes públicas candidatas de negativos pesquisadas e limitações documentadas; nenhuma incorporada automaticamente.
- [ ] Conferir anotações públicas/suplementos e sua correspondência com as imagens originais.
- [ ] Confirmar animal/lâmina e independência dos campos do novo ZIP.
- [ ] Anotações reais revisadas por pessoa qualificada, com positivos, negativos e cobertura.
- [ ] Definir divisão viável por grupos/classes e teste independente; pastas originais `train/test` não bastam.
- [ ] Selecionar controles compatíveis, revisar o nível do rótulo e registrar licença/proveniência.

## Modelo A

- [x] Fluxo original instrumentado: HSV, morfologia, recorte mascarado, RGB, resize e preprocessamento ResNet50.
- [x] Artefato carregado com TensorFlow/Keras 2.15, sem retreinamento.
- [x] Cópia normalizada auditada: 329 tensores preservados, original intacto; 320 tensores de camadas carregados confrontados.
- [x] Dois casos sintéticos diferenciais com o código de referência; classificador real também executado com recorte sintético.
- [ ] Inferência real na base atual, após definir partições. Diagnósticos da base descartada não contam como resultados atuais.
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
- [ ] Diagnóstico da localização na parcela de desenvolvimento da base atual, sem examinar o teste para ajustar parâmetros.
- [ ] Calibrar localização usando apenas desenvolvimento/validação com referência revisada.
- [ ] Treinamento supervisionado real e avaliação do checkpoint real no teste reservado.

## Comparação e notebooks

- [x] Cinco notebooks reorganizados, executados de cima para baixo em modo sintético e entregues sem saídas antigas.
- [x] Comparação CLI sintética, associação um a um e FN por ausência de candidatos testados.
- [x] Mesmo universo de IDs; falhas/ausências mantidas, sem inventar decisão negativa.
- [x] Origem, partição, hash do manifesto e treino sintético verificados na CLI de comparação.
- [x] Métricas auxiliares de recortes separadas; AUC indisponível para classe única; nenhuma matriz de confusão sem referência.
- [x] Custos e ambiente de smoke/diagnóstico registrados; treino A indisponível.
- [x] Em 22/09: 25 testes passaram e cinco notebooks foram reexecutados em modo sintético; preparação do ZIP real auditada.
- [ ] Comparação real com referência revisada e parâmetros fixados antes do teste.
- [ ] Intervalos por grupos independentes somente se o planejamento e o número de grupos permitirem.

## Próximo passo

Conferir as anotações públicas e revisar `data/annotations/trypomastigote_pending.json` com alguém qualificado da equipe. Confirmar os grupos e selecionar controles compatíveis usando a [pesquisa de fontes](fontes_negativas.md). Depois, preparar as partições e seguir o [guia de treinamento](guia_treinamento.md). Sem referência revisada, treino real e conclusões de qualidade continuam pendentes.
