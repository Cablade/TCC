# Registro de Decisões Técnicas

> **Como usar:** toda vez que tomarmos uma decisão técnica relevante, anote aqui com data, contexto e justificativa. Vai facilitar muito a escrita da metodologia em novembro.

---

## 2026-05-16 — Escolha da arquitetura do Modelo B: EfficientNet-B0

**Contexto:** precisávamos de uma arquitetura moderna comparável à ResNet-50 do Modelo A.

**Decisão:** EfficientNet-B0.

**Justificativa:**
- ~5M parâmetros (vs ~25M da ResNet-50) → menor uso de memória, treino mais rápido em Colab
- Eficiência superior em ImageNet (top-1 accuracy)
- Mesma família de redes convolucionais → comparação direta
- Pré-treinada no ImageNet, disponível nativamente em `keras.applications`

**Alternativas consideradas:**
- ConvNeXt-Tiny: mais moderna, mas curva de aprendizado mais íngreme
- ViT pequeno: requer mais dados para fine-tuning eficaz, arriscado com nosso dataset
- ResNet-50 com técnicas modernas: opção mais segura, mas reduz o diferencial frente ao Modelo A

---

## 2026-05-16 — Manter pipeline OpenCV do Modelo A para Modelo B

**Contexto:** o Modelo A usa segmentação clássica (HSV + morfologia) antes da classificação por CNN. O Modelo B poderia substituir todo o pipeline por uma rede end-to-end (YOLO, U-Net).

**Decisão:** manter o pipeline OpenCV para ambos os modelos.

**Justificativa:**
- Isola a variável sob análise: apenas a etapa de classificação muda
- Comparação metodologicamente mais limpa
- Treinos end-to-end exigem rotulação por bounding box ou máscara, que não temos prontamente
- Reduz escopo do TCC ao viável em 7 meses

**Riscos assumidos:**
- O pipeline OpenCV pode ser um gargalo de performance que ambos os modelos herdam
- Se as ROIs forem ruins, nenhum classificador vai funcionar bem

---

## 2026-05-16 — Dataset: Zenodo 5123062

**Contexto:** não temos acesso ao dataset original da Fuzzylab/FIOCRUZ por questões éticas.

**Decisão:** usar o dataset público "Image dataset from Automatic analysis of Trypanosoma cruzi" (Morais et al., 2021) — DOI 10.5281/zenodo.5123062.

**Justificativa:**
- Licença CC-BY 4.0 (uso livre com atribuição)
- 1,3 GB de imagens, suficiente para treino com augmentation
- Mesmo tipo de preparo (esfregaço fino, Giemsa) que o Modelo A foi treinado
- Provavelmente o dataset original do paper que originou o modelo da Fuzzylab/FIOCRUZ → compatibilidade metodológica

---

<!--
## YYYY-MM-DD — Título curto da decisão

**Contexto:**

**Decisão:**

**Justificativa:**

**Alternativas consideradas:**

**Riscos assumidos:**
-->
