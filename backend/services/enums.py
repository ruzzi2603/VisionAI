from django.db import models


class RiskLevel(models.TextChoices):
    LOW = "LOW", "Baixo"
    MEDIUM = "MEDIUM", "Medio"
    HIGH = "HIGH", "Alto"
    CRITICAL = "CRITICAL", "Critico"
