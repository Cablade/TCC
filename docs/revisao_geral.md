# Revisão geral do TCC — 27/09/2026

## Parecer de escopo

O estudo permanece no escopo ao comparar os sistemas completos A original e B proposto nas mesmas imagens, medindo localização, decisões, erros e custo. Negativos externos e inspeção de artefatos são análises complementares úteis. Os resultados não sustentam antecipar vitória de B, ganho clínico ou que A era a melhor tecnologia de 2024. Também não isolam ResNet versus EfficientNet: localização, dados e pré-processamento diferem.

Priorizar consolidação e redação. Novas arquiteturas, aplicativo de diagnóstico e sucessivos ajustes sem hipótese definida aumentariam o escopo sem resolver a referência incompleta. A proposta preexistente em `docs/proposta.md` foi preservada.

## Achados e correções

| Prioridade | Achado | Encaminhamento |
| --- | --- | --- |
| Alta | README/status/guia misturavam B antigo e atual | Documentação atualizada; versões anteriores preservadas com hashes em ZIP. |
| Alta | Painel tinha números de exemplo e dizia “105 amostras clínicas” | Arquivado com seu atualizador em ZIP conferido e removido do fluxo ativo. |
| Alta | Faltavam HTMLs, JSONs de revisão e geradores descritos na conversa | Três galerias reconstruídas; registros da declaração de Caio identificados como reconstrução da conversa. Os JSONs originais não foram recuperados. |
| Alta | B treinado com 3.053 positivos / 76 negativos; validação 740 / 38 | Não avaliar apenas acurácia. Classificar todos os recortes de validação como positivos daria 740/778 ≈ 95,12%. Isso é cálculo de referência, não nova execução. |
| Média | Gráfico chamava todo resultado não positivo de “sem regiões” | Corrigido: quatro estados separados, total dinâmico e teste de regressão. |
| Média | Atualizador do painel buscava arquivo inexistente e transformava métrica indisponível em zero | Arquivado junto do protótipo, fora do fluxo científico. |
| Média | Comparação de classificadores usa recortes propostos por B e brutos para A | Análise auxiliar; não isola arquiteturas nem reproduz A completo. |

Os quatro arquivos usados pelo relatório de validação coincidem com seus hashes. O checkpoint B coincide com os metadados. IDs únicos pareados: 114 na validação e 33 nos externos. Esses checks não são auditoria de todos os pixels nem confirmação biológica dos rótulos. Evidência: `experiments/validation/revisao_geral_20260927/audit.json`.

## Interpretação dos resultados

Na validação positiva, A sinalizou 27/114 imagens e B 114/114; produziram 42 e 7.758 regiões positivas. Tempos do algoritmo: 32,37 e 281,87 segundos. O diagnóstico anterior registra 0/450 pontos associados às regiões positivas de A e 424/450 de B. A auditoria de A reproduziu as 42 caixas dentro dos arquivos: uma região na borda escura pode estar fora do campo circular e ainda dentro da imagem.

Cobertura de pontos publicados não equivale a detecção completa. Referência parcial impede chamar todas as regiões sem associação de falsos positivos. Todas as 114 imagens são positivas e participaram do desenvolvimento de B; não permitem medir rejeição de negativos ou avaliação final independente.

Nos externos, A sinalizou 20/33 campos e B 33/33, com 140 e 5.277 regiões positivas. Caio declarou na conversa ausência de parasita visível nos campos e nos 99 recortes selecionados. Os registros `review_reconstructed.json` identificam a reconstrução dessa declaração. Os 99 recortes coincidem pixel a pixel com as caixas das predições nas imagens originais. As 99 regiões, selecionadas por escores altos (três por campo), não são amostra aleatória para estimar precisão global. Células, bordas e artefatos são achados gerais, sem contagem por categoria.

Os externos LABIMED são campos humanos e diferem da base murina principal. Campos sem parasita visível não equivalem a pacientes sem Chagas nem a 33 unidades biológicas independentes. Manter como diagnóstico de desenvolvimento separado.

## Plano de figuras

| Figura | Dados/unidade | Limite da interpretação |
| --- | --- | --- |
| Fluxo e composição dos dados | 455/114/105 imagens e 3.129/778 recortes; classes separadas | Recortes não são animais independentes. |
| Estados A × B | Mesmos 114 IDs; suspeita, sem regiões, regiões sem suspeita, erro | Sinalização não prova localização correta. |
| Cobertura dos pontos | Propostas e regiões positivas, associação um a um | Denominador 450; referência parcial, não sensibilidade geral. |
| Candidatos e suspeitas por imagem | Distribuições pareadas, mediana e dispersão | Regiões desconhecidas não viram negativas. |
| Tempo A × B | Por imagem, total e dispersão; algoritmo separado de leitura/exportação | B foi ≈ 8,71 vezes mais lento nesta execução; falta benchmark repetido com aquecimento. |
| Alarmes externos | 20/33 A e 33/33 B, painel separado | Origem e revisão explícitas; não juntar com murinos numa acurácia global. |
| Treinamento de B | Acurácia e perda de treino/validação; época 23 selecionada | Auxiliar; histórico de A é desconhecido. |
| Exemplos qualitativos | Campo, recorte, previsão e referência separados | Recuperar vínculo da revisão; incluir falhas e acertos com critério explícito. |

O modo `--complete` de `scripts/generate_tcc_figures.py` agora produz as análises da tabela: sete figuras quantitativas e quatro exemplos qualitativos, todos em PDF/PNG, com duas tabelas CSV, legendas, hashes e índice em [consolidado_20260927](../tcc/figuras/consolidado_20260927/index.html). Os exemplos são escolhidos por regra determinística documentada. A figura de composição quantifica as partições; o fluxo experimental está descrito no texto. O modo resumido de quatro painéis permanece disponível. O [texto de resultados e discussão](../tcc/resultados_preliminares.md) acompanha a entrega.

Evitar por enquanto: ROC/AUC de campos sem duas classes revisadas no mesmo protocolo; precisão/F1 de detecção com referência parcial; intervalos tratando recortes como animais; conclusões causais sobre arquitetura sem experimento específico.

## Limpeza e arquitetura

`src/` concentra regras e `scripts/` contém comandos. A separação é adequada ao TCC; novas camadas não resolveriam os principais problemas. Organizar o fluxo e retirar instruções contraditórias tem prioridade. O inventário automatizado registra tamanho e referências textuais por script; ausência de referências não comprova desuso de um comando manual.

| Grupo | Decisão |
| --- | --- |
| Preparação, revisão, treino, inferência, comparação e exportação | Manter; mapa em `scripts/README.md`. |
| `tune_region_merging.py` | Manter para reproduzir a escolha do B reduzido; fora da rotina diária. |
| `validate_notebooks.py`, `audit_model_a.py`, `notebook_support.py` | Manter para verificações; suporte é importado por cinco notebooks. |
| `relocate_experiment.py` | Manter; dependência de transporte e testes. |
| `update_dashboard.py` e `dashboard/` | Arquivados e removidos do fluxo ativo após conferência dos bytes; `archive/dashboard_demonstrativo_20260927.zip`. |
| Configurações locais/pacotes antigos | Conferir usos antes de remover; podem ser necessários para transporte ou histórico. |
| Caches e imagens derivadas | Regeneráveis somente quando o gerador existe; não apagar galerias com geradores ausentes. |

O atualizador obsoleto e quatro arquivos do painel foram retirados após arquivamento e conferência SHA-256. O ZIP permite recuperação. Os demais scripts foram mantidos por suas funções de reprodução, revisão ou suporte. README, status e guia foram atualizados, com versões anteriores em `archive/documentacao_pre_revisao_20260927.zip`. Dados, pesos, predições e recortes foram preservados.

## Ordem recomendada

1. Concluído: reconstrução de três galerias e de dois registros baseados na declaração da conversa, com hashes/pixels conferidos. Gerador atual: `scripts/recover_reviews.py`.
2. Concluído: 11 figuras, tabelas, legendas e texto preliminar. Validação, externos e recortes estão separados.
3. Confirmar com orientador se a entrega será estudo exploratório reproduzível ou avaliação final com referência completa. Não é necessário forçar vitória de B.
4. Se houver novo treino, definir hipótese, negativos de desenvolvimento e nova versão antes de executar. Campos que orientaram ajuste não podem avaliar independentemente essa versão.
5. Congelar regras antes de abrir o teste reservado. Limitar conclusões à referência e independência disponíveis.
