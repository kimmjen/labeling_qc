#!/usr/bin/env python3
"""
라벨링 품질 검증 규칙
각종 검증 규칙을 정의하고 실행
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models.quality_issue import QualityIssue, create_label_issue, create_content_issue, create_structure_issue


class RuleValidator:
    """품질 검증 규칙 실행기"""
    
    def __init__(self):
        self.rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """검증 규칙 로드"""
        return {
            "R001": {
                "name": "빈 텍스트 검증",
                "description": "텍스트가 비어있거나 공백만 있는 요소 검출",
                "severity": "error",
                "auto_fixable": True
            },
            "R002": {
                "name": "라벨 타입 일관성",
                "description": "유사한 텍스트는 동일한 라벨 타입 사용",
                "severity": "warning",
                "auto_fixable": True
            },
            "R003": {
                "name": "제목 패턴 검증",
                "description": "제목 형태의 텍스트에 적절한 라벨 적용",
                "severity": "warning",
                "auto_fixable": True
            },
            "R004": {
                "name": "날짜 형식 검증",
                "description": "날짜 패턴에 Date 라벨 적용",
                "severity": "warning",
                "auto_fixable": True
            },
            "R005": {
                "name": "테이블 구조 검증",
                "description": "테이블 요소의 구조적 정합성 검증",
                "severity": "error",
                "auto_fixable": False
            },
            "R006": {
                "name": "순서 일관성 검증",
                "description": "요소들의 순서가 읽기 순서와 일치하는지 검증",
                "severity": "warning",
                "auto_fixable": True
            },
            "R007": {
                "name": "중복 요소 검증",
                "description": "중복된 텍스트나 영역 검출",
                "severity": "warning",
                "auto_fixable": True
            },
            "R008": {
                "name": "금지된 라벨 검증",
                "description": "사용하지 말아야 할 라벨 타입 검출",
                "severity": "error",
                "auto_fixable": True
            },
            "R009": {
                "name": "특정 텍스트 라벨 검증",
                "description": "'원문', '번역문', '본문'은 ParaText 라벨 사용",
                "severity": "warning",
                "auto_fixable": True
            },
            "R010": {
                "name": "날짜 패턴 라벨 검증",
                "description": "날짜 패턴은 Date 라벨 사용",
                "severity": "warning",
                "auto_fixable": True
            }
        }
    
    def validate_all_rules(self, data: Dict[str, Any], file_path: str) -> List[QualityIssue]:
        """모든 규칙 검증"""
        issues = []
        
        elements = data.get('elements', [])
        if not elements:
            issues.append(create_structure_issue("STRUCTURE_001", "요소가 없습니다", file_path))
            return issues
        
        # 각 규칙 실행
        issues.extend(self._validate_r001_empty_text(elements, file_path))
        issues.extend(self._validate_r002_label_consistency(elements, file_path))
        issues.extend(self._validate_r003_title_patterns(elements, file_path))
        issues.extend(self._validate_r004_date_format(elements, file_path))
        issues.extend(self._validate_r005_table_structure(elements, file_path))
        issues.extend(self._validate_r006_order_consistency(elements, file_path))
        issues.extend(self._validate_r007_duplicate_elements(elements, file_path))
        issues.extend(self._validate_r008_forbidden_labels(elements, file_path))
        issues.extend(self._validate_r009_specific_text_labels(elements, file_path))
        issues.extend(self._validate_r010_date_pattern_labels(elements, file_path))
        
        return issues
    
    def _validate_r001_empty_text(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R001: 빈 텍스트 검증"""
        issues = []
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            element_id = element.get('id', 'unknown')
            page_index = element.get('pageIndex', 0)
            
            if not text:
                issues.append(QualityIssue(
                    rule_id="R001",
                    severity="error",
                    message="빈 텍스트 요소",
                    file_path=file_path,
                    element_id=element_id,
                    page_index=page_index,
                    category="label_content",
                    suggested_fix="요소 제거 또는 텍스트 추가",
                    auto_fixable=True
                ))
        
        return issues
    
    def _validate_r002_label_consistency(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R002: 라벨 타입 일관성 검증"""
        issues = []
        
        # 유사한 텍스트 패턴 그룹화
        text_patterns = {}
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            label = element.get('category', {}).get('label', '')
            element_id = element.get('id', 'unknown')
            
            if not text or not label:
                continue
            
            # 텍스트 패턴 생성 (숫자, 특수문자 제거)
            pattern = re.sub(r'[0-9\W]+', '', text.lower())
            
            if len(pattern) < 3:  # 너무 짧은 패턴은 제외
                continue
            
            if pattern not in text_patterns:
                text_patterns[pattern] = []
            
            text_patterns[pattern].append({
                'element_id': element_id,
                'text': text,
                'label': label,
                'element': element
            })
        
        # 패턴별 라벨 일관성 검사
        for pattern, items in text_patterns.items():
            if len(items) < 2:
                continue
            
            labels = set(item['label'] for item in items)
            if len(labels) > 1:
                # 가장 많이 사용된 라벨을 권장 라벨로 선택
                label_counts = {}
                for item in items:
                    label_counts[item['label']] = label_counts.get(item['label'], 0) + 1
                
                recommended_label = max(label_counts, key=label_counts.get)
                
                for item in items:
                    if item['label'] != recommended_label:
                        issues.append(create_label_issue(
                            "R002",
                            item['element_id'],
                            item['label'],
                            recommended_label,
                            file_path,
                            item['element'].get('pageIndex', 0)
                        ))
        
        return issues
    
    def _validate_r003_title_patterns(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R003: 제목 패턴 검증"""
        issues = []
        
        title_patterns = [
            r'^[IVX]+\.\s+',           # "I. ", "II. " 등
            r'^\d+\.\s+[가-힣]+',      # "1. 개요", "2. 현황" 등  
            r'^[가나다라마바사]\.\s+', # "가. ", "나. " 등
            r'^제\d+[장절조]\s+',      # "제1장 ", "제2절 " 등
        ]
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            current_label = element.get('category', {}).get('label', '')
            element_id = element.get('id', 'unknown')
            page_index = element.get('pageIndex', 0)
            
            if not text:
                continue
            
            # 제목 패턴 확인
            is_title_pattern = any(re.search(pattern, text) for pattern in title_patterns)
            
            if is_title_pattern and current_label not in ['ParaTitle', 'DocTitle']:
                issues.append(create_label_issue(
                    "R003",
                    element_id,
                    current_label,
                    "ParaTitle",
                    file_path,
                    page_index
                ))
        
        return issues
    
    def _validate_r004_date_format(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R004: 날짜 형식 검증"""
        issues = []
        
        date_patterns = [
            r'^\d{4}년\s*\d{1,2}월\s*\d{1,2}일',      # "2021년 2월 3일"
            r'^\d{4}\.\s*\d{1,2}\.\s*\d{1,2}$',        # "2021. 2. 3"
            r'^\d{4}-\d{1,2}-\d{1,2}$',                # "2021-02-03"
            r'^\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\s*작성',  # "2021. 2. 3 작성"
        ]
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            current_label = element.get('category', {}).get('label', '')
            element_id = element.get('id', 'unknown')
            page_index = element.get('pageIndex', 0)
            
            if not text:
                continue
            
            # 날짜 패턴 확인
            is_date_pattern = any(re.search(pattern, text) for pattern in date_patterns)
            
            if is_date_pattern and current_label != 'Date':
                issues.append(create_label_issue(
                    "R004",
                    element_id,
                    current_label,
                    "Date",
                    file_path,
                    page_index
                ))
        
        return issues
    
    def _validate_r005_table_structure(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R005: 테이블 구조 검증"""
        issues = []
        
        table_elements = [e for e in elements if e.get('category', {}).get('type') == 'TABLE']
        
        for table in table_elements:
            element_id = table.get('id', 'unknown')
            table_data = table.get('table', {})
            cells = table_data.get('cells', [])
            
            if not cells:
                issues.append(QualityIssue(
                    rule_id="R005",
                    severity="error",
                    message="테이블에 셀이 없습니다",
                    file_path=file_path,
                    element_id=element_id,
                    category="structure",
                    auto_fixable=False
                ))
        
        return issues
    
    def _validate_r006_order_consistency(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R006: 순서 일관성 검증"""
        issues = []
        
        # 페이지별로 그룹화
        page_groups = {}
        for element in elements:
            page_idx = element.get('pageIndex', 0)
            if page_idx not in page_groups:
                page_groups[page_idx] = []
            page_groups[page_idx].append(element)
        
        for page_idx, page_elements in page_groups.items():
            # Y좌표 순서와 실제 순서 비교
            sorted_by_position = sorted(page_elements, key=lambda e: e.get('bbox', {}).get('top', 0))
            
            for i, element in enumerate(page_elements):
                expected_position = sorted_by_position.index(element)
                if i != expected_position:
                    issues.append(QualityIssue(
                        rule_id="R006",
                        severity="warning",
                        message=f"요소 순서가 읽기 순서와 다릅니다 (현재: {i}, 예상: {expected_position})",
                        file_path=file_path,
                        element_id=element.get('id', 'unknown'),
                        page_index=page_idx,
                        category="structure",
                        auto_fixable=True
                    ))
        
        return issues
    
    def _validate_r007_duplicate_elements(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R007: 중복 요소 검증"""
        issues = []
        
        seen_texts = {}
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            element_id = element.get('id', 'unknown')
            
            if not text or len(text) < 5:  # 너무 짧은 텍스트는 제외
                continue
            
            if text in seen_texts:
                issues.append(QualityIssue(
                    rule_id="R007",
                    severity="warning",
                    message=f"중복된 텍스트: {text[:50]}...",
                    file_path=file_path,
                    element_id=element_id,
                    category="consistency",
                    suggested_fix="중복 요소 제거 또는 병합",
                    auto_fixable=True,
                    metadata={
                        "duplicate_of": seen_texts[text],
                        "text": text
                    }
                ))
            else:
                seen_texts[text] = element_id
        
        return issues
    
    def _validate_r008_forbidden_labels(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R008: 금지된 라벨 검증"""
        issues = []
        
        forbidden_labels = ['연결', '국가명', '정책명', '법률명', '요약']
        
        for element in elements:
            current_label = element.get('category', {}).get('label', '')
            element_id = element.get('id', 'unknown')
            
            if current_label in forbidden_labels:
                issues.append(QualityIssue(
                    rule_id="R008",
                    severity="error",
                    message=f"금지된 라벨 사용: {current_label}",
                    file_path=file_path,
                    element_id=element_id,
                    category="label_type",
                    suggested_fix="적절한 라벨로 변경",
                    auto_fixable=True
                ))
        
        return issues
    
    def _validate_r009_specific_text_labels(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R009: 특정 텍스트 라벨 검증 ('원문', '번역문', '본문' → ParaText)"""
        issues = []
        
        target_texts = {"원문", "번역문", "본문"}
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            current_label = element.get('category', {}).get('label', '')
            element_id = element.get('id', 'unknown')
            page_index = element.get('pageIndex', 0)
            
            if text in target_texts and current_label != 'ParaText':
                issues.append(create_label_issue(
                    "R009",
                    element_id,
                    current_label,
                    "ParaText",
                    file_path,
                    page_index
                ))
        
        return issues
    
    def _validate_r010_date_pattern_labels(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R010: 날짜 패턴 라벨 검증"""
        issues = []
        
        date_patterns = [
            r'^\d{4}년\s*\d{1,2}월\s*\d{1,2}일',      # "2021년 2월 3일"
            r'^\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\s*작성',  # "2021. 2. 3 작성"
            r'^\d{4}\.\s*\d{1,2}\.\s*\d{1,2}$',        # "2021. 2. 3"
            r'^\d{4}-\d{1,2}-\d{1,2}$',                # "2021-02-03"
        ]
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            current_label = element.get('category', {}).get('label', '')
            element_id = element.get('id', 'unknown')
            page_index = element.get('pageIndex', 0)
            
            if not text:
                continue
            
            # 날짜 패턴 확인
            is_date_pattern = any(re.search(pattern, text) for pattern in date_patterns)
            
            if is_date_pattern and current_label != 'Date':
                issues.append(create_label_issue(
                    "R010",
                    element_id,
                    current_label,
                    "Date",
                    file_path,
                    page_index
                ))
        
        return issues


def main():
    """테스트용 메인 함수"""
    validator = RuleValidator()
    
    # 샘플 데이터로 테스트
    sample_data = {
        "elements": [
            {
                "id": "test1",
                "content": {"text": "원문"},
                "category": {"label": "ListText"},
                "pageIndex": 0
            },
            {
                "id": "test2", 
                "content": {"text": "2021. 2. 3 작성"},
                "category": {"label": "ParaText"},
                "pageIndex": 0
            }
        ]
    }
    
    issues = validator.validate_all_rules(sample_data, "test.json")
    
    print(f"🔍 검증 결과: {len(issues)}개 이슈 발견")
    for issue in issues:
        print(f"  {issue}")


if __name__ == "__main__":
    main()
