#!/usr/bin/env python3
"""
라벨링 품질 검증 규칙
각종 검증 규칙을 정의하고 실행
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.quality_issue import QualityIssue, create_label_issue, create_content_issue, create_structure_issue


class RuleValidator:
    """품질 검증 규칙 실행기"""
    
    def __init__(self):
        self.rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """검증 규칙 로드"""
        return {
            "R001": {
                "name": "ListText → ParaText 변경",
                "description": "원문/번역문이 ListText인 경우 ParaText로 변경",
                "severity": "warning",
                "auto_fixable": True
            },
            "R002": {
                "name": "RegionTitle → ParaTitle 변경",
                "description": "숫자나 '□' 없는 텍스트가 RegionTitle인 경우 ParaTitle로 변경",
                "severity": "warning",
                "auto_fixable": True
            },
            "R003": {
                "name": "법령 구조 라벨링",
                "description": "법령 문서의 계층 구조에 따른 라벨 적용",
                "severity": "warning",
                "auto_fixable": True
            },
            "R004": {
                "name": "한글 인코딩 오류 검출",
                "description": "한글이 깨지거나 잘못된 영어로 인식된 텍스트 검출",
                "severity": "error",
                "auto_fixable": False
            }
        }
    
    def validate_all_rules(self, data: Dict[str, Any], file_path: str) -> List[QualityIssue]:
        """모든 규칙 검증"""
        issues = []
        
        elements = data.get('elements', [])
        if not elements:
            issues.append(create_structure_issue("STRUCTURE_001", "요소가 없습니다", file_path))
            return issues
        
        # 규칙 1 실행
        list_to_para_issues, found_elements = self._validate_r001_listtext_to_paratext(elements, file_path)
        issues.extend(list_to_para_issues)
        
        # 규칙 2는 규칙 1에서 찾은 요소들의 이전 요소만 검사
        if found_elements:
            region_to_para_issues = self._validate_r002_regiontitle_to_paratitle(elements, file_path, found_elements)
            issues.extend(region_to_para_issues)
        
        # 규칙 3: 법령 구조 라벨링
        law_structure_issues = self._validate_r003_law_structure(elements, file_path)
        issues.extend(law_structure_issues)
        
        # 규칙 4: 한글 인코딩 오류 검출
        encoding_issues = self._validate_r004_korean_encoding(elements, file_path)
        issues.extend(encoding_issues)
        
        return issues
    
    def _validate_r001_listtext_to_paratext(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R001: ListText → ParaText 변경 검증"""
        issues = []
        found_elements = []  # 원문/번역문 요소 저장
        
        for element in elements:
            label = element.get('category', {}).get('label', '')
            text = element.get('content', {}).get('text', '').strip()
            element_id = element.get('id', 'unknown')
            
            # ListText인 원문/번역문 찾기
            if label == "ListText" and ("원문" in text or "번역문" in text):
                message = f"[ListText → ParaText 필요] '{text[:30]}...'"
                issue = create_label_issue("R001", message, element_id, file_path, 
                                        old_label="ListText", new_label="ParaText")
                issues.append(issue)
                found_elements.append({
                    'element_id': element_id,
                    'text': text,
                    'index': elements.index(element)
                })
        
        return issues, found_elements
    
    def _validate_r002_regiontitle_to_paratitle(self, elements: List[Dict], file_path: str, found_elements: List[Dict]) -> List[QualityIssue]:
        """R002: RegionTitle → ParaTitle 변경 검증"""
        issues = []
        
        for found in found_elements:
            # 원문/번역문 요소의 이전 요소 찾기
            found_index = found['index']
            if found_index > 0:  # 이전 요소가 있는 경우만
                prev_element = elements[found_index - 1]
                label = prev_element.get('category', {}).get('label', '')
                text = prev_element.get('content', {}).get('text', '').strip()
                element_id = prev_element.get('id', 'unknown')
                
                # RegionTitle인 경우 체크
                if label == "RegionTitle":
                    # 숫자나 □ 기호가 있는지 체크
                    has_number = bool(re.search(r'\d', text))
                    has_square = "□" in text
                    
                    # 숫자나 □ 기호가 있는 경우에는 RegionTitle 유지
                    # 없는 경우에만 ParaTitle로 변경
                    if not (has_number or has_square):
                        message = f"[RegionTitle → ParaTitle 필요] '{text[:50]}'"
                        issue = create_label_issue("R002", message, element_id, file_path,
                                              old_label="RegionTitle", new_label="ParaTitle")
                        issues.append(issue)
        
        return issues
    
    def _validate_r003_law_structure(self, elements: List[Dict], file_path: str) -> List[QualityIssue]:
        """R003: 법령 구조 라벨링 검증"""
        issues = []
        
        for i, element in enumerate(elements):
            text = element.get('content', {}).get('text', '').strip()
            current_label = element.get('category', {}).get('label', '')
            current_type = element.get('category', {}).get('type', '')
            element_id = element.get('id', 'unknown')
            page_index = element.get('pageIndex', 0)
            
            if not text:
                continue
            
            # ParaTitle로 변경해야 할 패턴들
            should_be_paratitle = False
            
            # 1. ~법 (예: "헌법신체운동법")
            if re.search(r'[가-힣]+법$', text):
                should_be_paratitle = True
            
            # 2. 제~편 (예: "제52편 총칙과 선거")
            elif re.search(r'^제\s*\d+\s*편', text):
                should_be_paratitle = True
            
            # 3. 제~장 (예: "제301장 헌법선거운동")
            elif re.search(r'^제\s*\d+\s*장', text):
                should_be_paratitle = True
            
            # 4. 제~절 (예: "제1절 선발선수운동과의 공지")
            elif re.search(r'^제\s*\d+\s*절', text):
                should_be_paratitle = True
            
            # 5. 제~조 (예: "제3010조")
            elif re.search(r'^제\s*\d+\s*조', text):
                should_be_paratitle = True
            
            # ParaTitle로 변경이 필요한 경우
            if should_be_paratitle and current_label != 'ParaTitle':
                message = f"[법령 구조] ParaTitle 필요: '{text[:50]}...'"
                issue = create_label_issue("R003", message, element_id, file_path,
                                        old_label=current_label, new_label="ParaTitle")
                issue.metadata['target_type'] = 'HEADING'  # type도 함께 변경
                issues.append(issue)
            
            # ListText로 변경해야 할 패턴들 (조문의 하위 내용)
            should_be_listtext = False
            
            # 6. 항 또는 제~조 아래의 내용 (번호나 기호로 시작하는 하위 항목들)
            if re.search(r'^\s*\(\d+\)', text) or re.search(r'^\s*\d+\.', text) or re.search(r'^\s*[가-힣]\.', text):
                # 이전 요소가 제~조인지 확인
                if i > 0:
                    prev_text = elements[i-1].get('content', {}).get('text', '').strip()
                    if re.search(r'^제\s*\d+\s*조', prev_text):
                        should_be_listtext = True
                # 또는 현재 요소가 조문 구조의 하위 항목인 경우
                elif re.search(r'^\s*\(\d+\)', text):  # (1), (2) 형태
                    should_be_listtext = True
            
            # "항"이 포함된 내용
            elif '항' in text and current_label != 'ListText':
                should_be_listtext = True
            
            # ListText로 변경이 필요한 경우
            if should_be_listtext and current_label != 'ListText':
                message = f"[법령 구조] ListText 필요: '{text[:50]}...'"
                issue = create_label_issue("R003", message, element_id, file_path,
                                        old_label=current_label, new_label="ListText")
                issue.metadata['target_type'] = 'LIST'  # type도 함께 변경
                issues.append(issue)
        
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
        
        target_texts = {"원문", "번역문"}
        
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


def main():
    """테스트용 메인 함수"""
    print("🔍 RuleValidator 테스트 시작")
    
    validator = RuleValidator()
    
    # 테스트 데이터
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
        """R004: 한글 인코딩 오류 검출"""
        issues = []
        
        # 한글 깨짐 패턴들
        corrupted_patterns = [
            r'[A-Z]{4,}[0-9]*',  # GOEECCD0 같은 대문자+숫자 조합
            r'[A-Z]+CD[0-9]*',   # ~CD0 패턴
            r'[A-Z]+EE[A-Z]*',   # ~EE~ 패턴
            r'\b[A-Z]{6,}\b',    # 6글자 이상 연속 대문자
        ]
        
        # 잘못된 영어 인식 패턴 (한국어 문서에서 나타나는 의심스러운 영어)
        suspicious_english_patterns = [
            r'\b[a-z]+[A-Z][a-z]+\b',  # camelCase 패턴 (한글이 잘못 인식될 때)
            r'\b[bcdfghjklmnpqrstvwxyz]{3,}\b',  # 자음이 많은 단어
            r'\b[A-Z][a-z]*[A-Z][a-z]*\b',  # PascalCase 패턴
        ]
        
        # 잘못된 특수문자 조합
        invalid_char_patterns = [
            r'[^\w\s가-힣\[\]().,!?;:\'"<>{}|\\/@#$%^&*+=~`-]',  # 예상치 못한 특수문자
            r'[\x00-\x1f\x7f-\x9f]',  # 제어문자
        ]
        
        for i, element in enumerate(elements):
            content = element.get('content', {})
            text = content.get('text', '')
            
            if not text:
                continue
            
            # 한글 깨짐 검사
            for pattern in corrupted_patterns:
                if re.search(pattern, text):
                    issues.append(create_content_issue(
                        "R004_CORRUPTED",
                        f"한글 깨짐 의심 텍스트: '{text[:50]}...' (패턴: {pattern})",
                        file_path,
                        element_id=element.get('id', f'element_{i}'),
                        current_value=text[:100],
                        suggested_action="텍스트 인코딩 확인 필요"
                    ))
                    break
            
            # 잘못된 영어 인식 검사 (한국어 문서 맥락에서)
            if self._is_korean_document_context(elements) and len(text) > 3:
                for pattern in suspicious_english_patterns:
                    matches = re.findall(pattern, text)
                    if matches and len(matches) > len(text.split()) * 0.3:  # 30% 이상이 의심스러운 패턴
                        issues.append(create_content_issue(
                            "R004_WRONG_ENGLISH",
                            f"잘못된 영어 인식 의심: '{text[:50]}...'",
                            file_path,
                            element_id=element.get('id', f'element_{i}'),
                            current_value=text[:100],
                            suggested_action="OCR 결과 재검토 필요"
                        ))
                        break
            
            # 잘못된 특수문자 검사
            for pattern in invalid_char_patterns:
                if re.search(pattern, text):
                    issues.append(create_content_issue(
                        "R004_INVALID_CHARS",
                        f"잘못된 문자 포함: '{text[:50]}...'",
                        file_path,
                        element_id=element.get('id', f'element_{i}'),
                        current_value=text[:100],
                        suggested_action="문자 인코딩 수정 필요"
                    ))
                    break
        
        return issues
    
    def _is_korean_document_context(self, elements: List[Dict]) -> bool:
        """문서가 한국어 문서인지 판단"""
        korean_count = 0
        total_text_elements = 0
        
        for element in elements:
            content = element.get('content', {})
            text = content.get('text', '')
            
            if text and len(text.strip()) > 0:
                total_text_elements += 1
                if re.search(r'[가-힣]', text):
                    korean_count += 1
        
        # 50% 이상이 한글을 포함하면 한국어 문서로 판단
        return total_text_elements > 0 and korean_count / total_text_elements >= 0.5


if __name__ == "__main__":
    main()
