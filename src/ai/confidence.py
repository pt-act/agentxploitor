"""
Confidence Calibration

Tracks historical accuracy and calibrates confidence scores
based on actual performance of predictions.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


@dataclass
class PredictionRecord:
    """Record of a prediction and its outcome."""
    id: str
    prediction_type: str
    predicted_confidence: float
    actual_outcome: Optional[bool] = None
    analyzer: Optional[str] = None
    severity: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'prediction_type': self.prediction_type,
            'predicted_confidence': self.predicted_confidence,
            'actual_outcome': self.actual_outcome,
            'analyzer': self.analyzer,
            'severity': self.severity,
            'timestamp': self.timestamp,
            'resolved_at': self.resolved_at,
        }


@dataclass
class CalibrationMetrics:
    """Calibration metrics for a prediction source."""
    source: str
    total_predictions: int = 0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    avg_predicted_confidence: float = 0.0
    avg_actual_accuracy: float = 0.0
    calibration_error: float = 0.0
    
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1_score(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def accuracy(self) -> float:
        if self.total_predictions == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / self.total_predictions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'total_predictions': self.total_predictions,
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'true_negatives': self.true_negatives,
            'false_negatives': self.false_negatives,
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
            'accuracy': round(self.accuracy, 4),
            'avg_predicted_confidence': round(self.avg_predicted_confidence, 4),
            'avg_actual_accuracy': round(self.avg_actual_accuracy, 4),
            'calibration_error': round(self.calibration_error, 4),
        }


class ConfidenceCalibrator:
    """
    Calibrates confidence scores based on historical accuracy.
    
    Tracks predictions and outcomes to adjust confidence
    to better reflect actual probability of correctness.
    """

    ANALYZER_ADJUSTMENTS: Dict[str, float] = {
        'slither': 0.95,
        'mythril': 0.92,
        'echidna': 0.88,
        'foundry': 0.90,
        'custom': 0.85,
        'llm': 0.75,
    }

    SEVERITY_ADJUSTMENTS: Dict[str, float] = {
        'CRITICAL': 0.85,
        'HIGH': 0.90,
        'MEDIUM': 0.95,
        'LOW': 1.0,
        'INFO': 1.0,
    }

    def __init__(self, history_size: int = 1000):
        self._history_size = history_size
        self._predictions: Dict[str, PredictionRecord] = {}
        self._metrics: Dict[str, CalibrationMetrics] = {}
        self._confidence_bins: Dict[str, List[float]] = defaultdict(list)

    def record_prediction(
        self,
        prediction_id: str,
        prediction_type: str,
        confidence: float,
        analyzer: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> PredictionRecord:
        """Record a new prediction."""
        record = PredictionRecord(
            id=prediction_id,
            prediction_type=prediction_type,
            predicted_confidence=confidence,
            analyzer=analyzer,
            severity=severity,
        )
        
        self._predictions[prediction_id] = record
        
        if len(self._predictions) > self._history_size:
            oldest = list(self._predictions.keys())[0]
            del self._predictions[oldest]
        
        return record

    def resolve_prediction(
        self,
        prediction_id: str,
        outcome: bool,
    ) -> Optional[PredictionRecord]:
        """Resolve a prediction with actual outcome."""
        record = self._predictions.get(prediction_id)
        
        if record is None:
            logger.warning(f"Prediction {prediction_id} not found")
            return None
        
        record.actual_outcome = outcome
        record.resolved_at = datetime.utcnow().isoformat()
        
        self._update_metrics(record)
        
        return record

    def calibrate_confidence(
        self,
        confidence: float,
        analyzer: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> float:
        """
        Calibrate a raw confidence score.
        
        Applies adjustments based on:
        - Historical accuracy of the analyzer
        - Severity-based adjustments
        - Calibration from historical data
        """
        calibrated = confidence
        
        if analyzer and analyzer in self.ANALYZER_ADJUSTMENTS:
            base_adj = self.ANALYZER_ADJUSTMENTS[analyzer]
            
            if analyzer in self._metrics:
                metrics = self._metrics[analyzer]
                if metrics.total_predictions >= 10:
                    actual_accuracy = metrics.accuracy
                    calibration = 0.5 * base_adj + 0.5 * actual_accuracy
                else:
                    calibration = base_adj
            else:
                calibration = base_adj
            
            calibrated = calibrated * calibration
        
        if severity and severity.upper() in self.SEVERITY_ADJUSTMENTS:
            sev_adj = self.SEVERITY_ADJUSTMENTS[severity.upper()]
            calibrated = calibrated * sev_adj
        
        calibrated = max(0.0, min(1.0, calibrated))
        
        return round(calibrated, 4)

    def get_confidence_interval(
        self,
        confidence: float,
        analyzer: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get confidence interval for a prediction."""
        margin = 0.1
        
        if analyzer and analyzer in self._metrics:
            metrics = self._metrics[analyzer]
            if metrics.total_predictions >= 20:
                error_rate = 1 - metrics.accuracy
                margin = error_rate / 2
        
        return {
            'point': confidence,
            'lower': max(0.0, confidence - margin),
            'upper': min(1.0, confidence + margin),
            'margin': margin,
        }

    def get_uncertainty(self, confidence: float) -> float:
        """
        Quantify uncertainty in a confidence score.
        
        Higher values = more uncertain.
        """
        entropy = -(
            confidence * math.log2(max(confidence, 0.001)) +
            (1 - confidence) * math.log2(max(1 - confidence, 0.001))
        )
        return entropy / math.log2(2)

    def should_auto_approve(
        self,
        confidence: float,
        threshold: float = 0.9,
        analyzer: Optional[str] = None,
    ) -> bool:
        """Determine if a prediction can be auto-approved."""
        calibrated = self.calibrate_confidence(confidence, analyzer)
        interval = self.get_confidence_interval(calibrated, analyzer)
        
        return interval['lower'] >= threshold

    def get_metrics(self, source: str) -> Optional[CalibrationMetrics]:
        """Get calibration metrics for a source."""
        return self._metrics.get(source)

    def get_all_metrics(self) -> Dict[str, CalibrationMetrics]:
        """Get all calibration metrics."""
        return self._metrics.copy()

    def _update_metrics(self, record: PredictionRecord) -> None:
        """Update metrics based on resolved prediction."""
        sources = []
        
        if record.analyzer:
            sources.append(record.analyzer)
        
        if record.severity:
            sources.append(f"severity_{record.severity.lower()}")
        
        sources.append('overall')
        
        for source in sources:
            if source not in self._metrics:
                self._metrics[source] = CalibrationMetrics(source=source)
            
            metrics = self._metrics[source]
            metrics.total_predictions += 1
            
            predicted_positive = record.predicted_confidence >= 0.5
            actual_positive = record.actual_outcome
            
            if predicted_positive and actual_positive:
                metrics.true_positives += 1
            elif predicted_positive and not actual_positive:
                metrics.false_positives += 1
            elif not predicted_positive and actual_positive:
                metrics.false_negatives += 1
            else:
                metrics.true_negatives += 1
            
            self._confidence_bins[source].append(record.predicted_confidence)
            metrics.avg_predicted_confidence = sum(self._confidence_bins[source]) / len(self._confidence_bins[source])
            metrics.avg_actual_accuracy = metrics.accuracy
            
            metrics.calibration_error = abs(
                metrics.avg_predicted_confidence - metrics.avg_actual_accuracy
            )

    def export_history(self) -> str:
        """Export prediction history as JSON."""
        data = {
            'predictions': [p.to_dict() for p in self._predictions.values()],
            'metrics': {k: v.to_dict() for k, v in self._metrics.items()},
        }
        return json.dumps(data, indent=2)

    def import_history(self, data: str) -> None:
        """Import prediction history from JSON."""
        parsed = json.loads(data)
        
        for p in parsed.get('predictions', []):
            record = PredictionRecord(
                id=p['id'],
                prediction_type=p['prediction_type'],
                predicted_confidence=p['predicted_confidence'],
                actual_outcome=p.get('actual_outcome'),
                analyzer=p.get('analyzer'),
                severity=p.get('severity'),
                timestamp=p['timestamp'],
                resolved_at=p.get('resolved_at'),
            )
            self._predictions[record.id] = record


_calibrator: Optional[ConfidenceCalibrator] = None


def get_calibrator() -> ConfidenceCalibrator:
    """Get global confidence calibrator."""
    global _calibrator
    if _calibrator is None:
        _calibrator = ConfidenceCalibrator()
    return _calibrator


def calibrate_confidence(
    confidence: float,
    analyzer: Optional[str] = None,
    severity: Optional[str] = None,
) -> float:
    """Convenience function to calibrate confidence."""
    return get_calibrator().calibrate_confidence(confidence, analyzer, severity)
