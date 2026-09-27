# Figuras e legendas — comparação exploratória A × B

Geradas de predições existentes, sem treino, nova inferência ou abertura de pixels do teste. Os CSVs e summary.json permitem conferir números e hashes.

## 01_composicao

Divisão por imagem original. Recortes não são unidades biológicas independentes. O teste aparece apenas como contagem do manifesto; seus pixels não foram abertos.

[PDF](01_composicao.pdf) · [PNG](01_composicao.png)

## 02_estados

Estados nas mesmas 114 imagens positivas de validação. Sinalizar um campo não comprova localizar seu parasita; não há especificidade estimável neste conjunto.

[PDF](02_estados.pdf) · [PNG](02_estados.png)

## 03_cobertura

Associação um a um de cardinalidade máxima; ponto contido na caixa com extremos direito/inferior exclusivos. Referência parcial: cobertura dos pontos disponíveis, não sensibilidade geral. Regiões sem associação não são automaticamente falsos positivos.

[PDF](03_cobertura.pdf) · [PNG](03_cobertura.png)

## 04_candidatos

Cada ponto é uma imagem de validação. Caixas mostram quartis e mediana; pontos incluem os extremos. O volume de regiões não equivale ao número de parasitas.

[PDF](04_candidatos.pdf) · [PNG](04_candidatos.png)

## 05_tempos

Tempos do algoritmo nas execuções registradas, sem exportação de imagens. Pareamento por image_id; inclui primeiras chamadas. Não é benchmark repetido com aquecimento. Etapas registradas podem não somar exatamente o total por haver overhead.

[PDF](05_tempos.pdf) · [PNG](05_tempos.png)

## 06_externos

Diagnóstico separado: 33 campos LABIMED humanos, 1 caso(s), 8 lâminas. Ausência de parasita visível relatada por Caio; registro reconstruído da conversa. Não são pacientes negativos independentes nem teste intocado. Não misturar à validação murina.

[PDF](06_externos.pdf) · [PNG](06_externos.png)

## 07_treinamento

Histórico exclusivo do B reduzido. Checkpoint escolhido pela menor val_loss, não pela maior acurácia. Há 740 recortes positivos e 38 negativos na validação; acurácia isolada é insuficiente. Não há histórico comparável de treinamento de A.

[PDF](07_treinamento.pdf) · [PNG](07_treinamento.png)

## 08_exemplo_01

A: suspeita sem ponto associado. Image ID: img_025f647cc85ef3c81fada042; caixa [3280, 2097, 3310, 2118]. Seleção pelo primeiro ID elegível ordenado (externo: FP001). Cruz indica ponto publicado quando disponível. Área amarela é de inspeção; no exemplo de ponto perdido, não é proposta do modelo. Sem associação não comprova falso positivo na referência parcial.

[PDF](08_exemplo_01.pdf) · [PNG](08_exemplo_01.png)

## 08_exemplo_02

B: suspeita associada a ponto. Image ID: img_00cd93a7e14b9dc222e2298a; caixa [1711, 1690, 1955, 1934]. Seleção pelo primeiro ID elegível ordenado (externo: FP001). Cruz indica ponto publicado quando disponível. Área amarela é de inspeção; no exemplo de ponto perdido, não é proposta do modelo. Sem associação não comprova falso positivo na referência parcial.

[PDF](08_exemplo_02.pdf) · [PNG](08_exemplo_02.png)

## 08_exemplo_03

B: ponto sem região positiva associada. Image ID: img_10cbbfcb271e6b8dd0547da7; caixa [1281, 2110, 1505, 2334]. Seleção pelo primeiro ID elegível ordenado (externo: FP001). Cruz indica ponto publicado quando disponível. Área amarela é de inspeção; no exemplo de ponto perdido, não é proposta do modelo. Sem associação não comprova falso positivo na referência parcial.

[PDF](08_exemplo_03.pdf) · [PNG](08_exemplo_03.png)

## 08_exemplo_04

B externo: sem parasita visível (Caio). Image ID: labimed_6b6b49b055396c8c09a92123; caixa [1720, 1870, 1920, 2054]. Seleção pelo primeiro ID elegível ordenado (externo: FP001). Cruz indica ponto publicado quando disponível. Área amarela é de inspeção; no exemplo de ponto perdido, não é proposta do modelo. Sem associação não comprova falso positivo na referência parcial.

[PDF](08_exemplo_04.pdf) · [PNG](08_exemplo_04.png)
