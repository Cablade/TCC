# Revisão e organização atual

A rotina foi consolidada em **A original × B atual**. A melhoria é uma hipótese a testar sobre as mesmas imagens; os sistemas diferem em localização, dados e pré-processamento, portanto a comparação não isola apenas ResNet versus EfficientNet.

Concluído: B com negativos originais revisados, histórico do treino preservado, documentação central atualizada, scripts/configurações obsoletos e resultados históricos retirados do fluxo ativo. Arquivo conferido: `archive/limpeza_fluxo_atual_20261005.zip`; decisões e alvos: `archive/limpeza_fluxo_atual_20261005.json`.

Manter `src` para regras e `scripts` para comandos. Não criar camadas apenas para aumentar a estrutura. `notebooks` serve para exploração; comandos de revisão, transporte e verificação não são inúteis por serem ocasionais.

A `.venv` depende do Python em `.cache/python`; essa pasta não é cache descartável. Fontes, modelos, rótulos e evidências do treino também não são descartáveis. As figuras atuais sairão da comparação em `experiments/comparison/a_vs_b/`.

Limites científicos: referência positiva parcial, grupos sem independência biológica comprovada, negativos externos de aquisição diferente e revisão visual declarada pelo autor. Separar fontes; não usar recortes como animais independentes, não chamar ausência de parasita visível de ausência clínica de Chagas e não presumir vitória de B.

Próximo: cobertura dos pontos publicados, falsos alarmes nos negativos, tempo e exemplos; revisar com o orientador e congelar o protocolo antes do teste final. A revisão detalhada anterior e suas figuras permanecem no ZIP histórico.
