"""
Modelo A2 — ResNet-50 re-treinada em ROIs RGB coerentes.

Mesma arquitetura e configuração de treino do Modelo A1, mas treinada
em ROIs coloridas (extraídas pelo pipeline OpenCV aplicado ao Zenodo),
não em máscaras binárias.

Serve como controle isolado: permite atribuir ganhos especificamente
à correção da divergência treino/inferência, separadamente dos ganhos
das técnicas modernas do Modelo B.

Como reusa toda a lógica do model_a, este módulo é essencialmente
um alias semântico para deixar claro que é um modelo diferente do A1
no contexto experimental.
"""

from __future__ import annotations

from tensorflow.keras.models import Model

from src.model_a import build_model_a


def build_model_a2(
    num_classes: int = 2,
    input_shape: tuple[int, int, int] = (224, 224, 3),
    dropout_rate: float = 0.3,
    freeze_base: bool = True,
) -> Model:
    """
    Constrói o Modelo A2.

    Idêntico em arquitetura ao Modelo A1 (build_model_a). A diferença
    experimental está no que será passado como entrada durante o treino:
    ROIs RGB do Zenodo, em vez das máscaras binárias originais.
    """
    return build_model_a(
        num_classes=num_classes,
        input_shape=input_shape,
        dropout_rate=dropout_rate,
        freeze_base=freeze_base,
    )
