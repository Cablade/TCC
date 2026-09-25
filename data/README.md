# Dados locais

As fontes e seus limites estão em [dados](../docs/dados.md). O formato dos manifestos e da referência está em [anotações](../docs/anotacoes.md#formato). Para executar a preparação, siga o [guia de treinamento](../docs/guia_treinamento.md).

- `raw/`: originais ou metadados de aquisição;
- `protocol/`: inventários e auditorias;
- `annotations/`: referências publicadas e revisadas;
- `splits/`: atribuições de imagens/grupos;
- `processed/`: recortes;
- `external_candidates/`: fontes externas avaliadas separadamente.

Preserve somente a fonte ativa `trypoastigote_images.zip` e os artefatos derivados dela. Fontes externas avaliadas ficam fora do treino principal; o experimento utiliza apenas os caminhos definidos na configuração e nos manifestos atuais.
