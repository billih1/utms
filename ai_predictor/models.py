from django.db import models


class Prediction(models.Model):
    """
    FR-22 / UC-21: Machine Learning prediction records predicting likelihood of default.
    """
    class RiskLevel(models.TextChoices):
        HIGH = 'High', 'High'
        MEDIUM = 'Medium', 'Medium'
        LOW = 'Low', 'Low'

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    target_month = models.CharField(max_length=20)
    risk_score = models.FloatField(help_text="Probability 0.0 to 1.0 (default probability)")
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices)
    features_json = models.JSONField(default=dict, help_text="Features passed to prediction pipeline")
    reason = models.TextField(blank=True, default='', help_text="Transparent explanation for staff")
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-risk_score']
        unique_together = ['student', 'target_month']

    def __str__(self):
        return f"{self.student.admission_number} - {self.target_month} ({self.risk_level}: {self.risk_score:.0%})"
