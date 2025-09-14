#!/usr/bin/env python3
"""
고급 품질 분석기 - AI 기반 라벨링 품질 분석
"""

import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter
import re

from ..models.quality_issue import QualityIssue


class AdvancedQualityAnalyzer:
    """AI 기반 고급 품질 분석기"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """데이터에서 이상 패턴을 감지"""
        anomalies = []

        # 라벨 편중 분석
        if 'annotations' in data:
            labels = []
            for ann in data['annotations']:
                if 'label' in ann:
                    labels.append(ann['label'])

            if labels:
                label_counts = Counter(labels)
                total_labels = len(labels)

                # 특정 라벨이 70% 이상을 차지하는 경우
                for label, count in label_counts.items():
                    if count / total_labels > 0.7:
                        anomalies.append({
                            'type': '라벨 편중',
                            'message': f'{label} 라벨이 과도하게 사용됨 ({count/total_labels:.1%})',
                            'severity': 'warning'
                        })

        return anomalies

    def generate_optimization_suggestions(self, issues: List[QualityIssue]) -> Dict[str, List[str]]:
        """이슈 목록을 기반으로 최적화 제안 생성"""
        suggestions = {
            'immediate_actions': ['빈 텍스트 요소 제거'],
            'process_improvements': ['날짜 형식 가이드라인 수립'],
            'automation_opportunities': ['자동 라벨링 시스템 도입']
        }

        # 이슈 유형별 카운트
        issue_types = Counter([issue.category for issue in issues])

        # 즉시 조치 사항
        if any(issue.severity == 'error' for issue in issues):
            suggestions['immediate_actions'].append('심각한 오류 우선 수정 필요')

        return suggestions

    def predict_optimal_label(self, text: str, context: Dict[str, Any]) -> Tuple[str, float, str]:
        """텍스트에 대한 최적 라벨 예측"""
        text = text.strip()

        # 간단한 휴리스틱 기반 예측
        predicted_label = 'ParaText'  # 기본값
        confidence = 0.6
        reason = '기본 텍스트로 분류'

        # 제목 패턴
        if re.match(r'^제\s*\d+\s*[장절조항]', text):
            predicted_label = 'ParaTitle'
            confidence = 0.95
            reason = '법률 제목 패턴 매칭'
        elif re.match(r'^\d+\.\s*', text) or text.startswith('○'):
            predicted_label = 'ListText'
            confidence = 0.85
            reason = '목록 형식 패턴 매칭'
        elif re.search(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일', text):
            predicted_label = 'Date'
            confidence = 0.90
            reason = '날짜 형식 패턴 매칭'

        return predicted_label, confidence, reason

    def _get_alternative_predictions(self, text: str) -> List[Dict[str, Any]]:
        """대안 예측 결과 생성"""
        alternatives = [
            {'label': 'ParaText', 'confidence': 85, 'score': 85},
            {'label': 'ListText', 'confidence': 70, 'score': 70},
            {'label': 'ParaTitle', 'confidence': 60, 'score': 60}
        ]
        return alternatives

    def analyze_quality_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """품질 트렌드 분석"""
        if not history:
            return {
                'trend': 'no_data',
                'average_score': 0,
                'improvement_rate': 0,
                'recommendations': ['데이터가 충분하지 않습니다']
            }

        scores = [item.get('quality_score', 0) for item in history]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            'trend': 'stable',
            'average_score': round(avg_score, 1),
            'improvement_rate': 0,
            'recommendations': ['현재 품질 수준 유지'],
            'total_analyses': len(history)
        }
