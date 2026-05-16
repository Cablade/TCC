"""
Código modular do TCC — Detecção de Doença de Chagas via classificação
de núcleos celulares em esfregaços sanguíneos.

Módulos:
    data_pipeline: carregamento e tf.data
    segmentation:  pipeline OpenCV (replica do Modelo A)
    augmentation:  transforms do Modelo B
    model_a:       ResNet-50 igual ao Modelo A da Fuzzylab/FIOCRUZ
    model_b:       EfficientNet-B0 com técnicas modernas
    train:         loop de treino genérico
    evaluate:      cálculo de métricas
    stats:         testes estatísticos (Wilcoxon, etc.)
"""

__version__ = "0.1.0"
