"""Ponderação da perda sem duplicar ou eliminar recortes de treino."""
from collections import Counter
import math


def resolve_class_weights(labels, mode="auto", maximum=None):
    values = list(labels)
    if any(isinstance(v, bool) or v not in (0, 1) for v in values):
        raise ValueError("Balanceamento exige rótulos binários 0/1.")
    counts = Counter(int(v) for v in values)
    if set(counts) != {0, 1}:
        raise ValueError("Balanceamento exige ambas as classes no treino.")
    if maximum is not None and (isinstance(maximum, bool) or not math.isfinite(float(maximum)) or float(maximum) < 1):
        raise ValueError("Limite de peso deve ser finito e pelo menos 1.")
    if mode is None:
        return None
    if mode == "auto":
        weights = {k: len(values) / (2 * n) for k,n in counts.items()}
    elif isinstance(mode, dict) and {int(k) for k in mode} == {0,1}:
        weights = {int(k): float(v) for k,v in mode.items()}
        if any(not math.isfinite(v) or v <= 0 for v in weights.values()):
            raise ValueError("Pesos devem ser finitos e positivos.")
    else:
        raise ValueError("Pesos de classe devem ser auto, null ou mapa binário.")
    return {k: min(v, float(maximum)) if maximum is not None else v for k,v in weights.items()}
