#!/usr/bin/env python3
"""
품질 이슈 모델
라벨링 검수 중 발견되는 문제들을 정의
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class IssueSeverity(Enum):
    """이슈 심각도"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(Enum):
    """이슈 카테고리"""
    LABEL_TYPE = "label_type"
    LABEL_CONTENT = "label_content"
    STRUCTURE = "structure"
    FORMAT = "format"
    CONSISTENCY = "consistency"


@dataclass
class QualityIssue:
    """품질 이슈 데이터 클래스"""
    rule_id: str
    severity: str
    message: str
    file_path: str
    element_id: Optional[str] = None
    page_index: Optional[int] = None
    category: Optional[str] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """초기화 후 처리"""
        if self.metadata is None:
            self.metadata = {}
            
        # 라벨 변경 정보가 있으면 metadata에 저장
        if hasattr(self, 'old_label'):
            self.metadata['old_label'] = self.old_label
        if hasattr(self, 'new_label'):
            self.metadata['new_label'] = self.new_label
    
    @property
    def severity_level(self) -> int:
        """심각도 레벨 (숫자)"""
        severity_map = {
            "error": 3,
            "warning": 2,
            "info": 1
        }
        return severity_map.get(self.severity, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "element_id": self.element_id,
            "page_index": self.page_index,
            "category": self.category,
            "suggested_fix": self.suggested_fix,
            "auto_fixable": self.auto_fixable,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityIssue":
        """딕셔너리에서 생성"""
        return cls(**data)
    
    def __str__(self) -> str:
        """문자열 표현"""
        location = ""
        if self.element_id:
            location += f" (요소: {self.element_id})"
        if self.page_index is not None:
            location += f" (페이지: {self.page_index + 1})"
        
        return f"[{self.severity.upper()}] {self.rule_id}: {self.message}{location}"


@dataclass
class FixResult:
    """수정 결과 데이터 클래스"""
    success: bool
    description: str
    before_value: Optional[Any] = None
    after_value: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """초기화 후 처리"""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "success": self.success,
            "description": self.description,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "error_message": self.error_message,
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        status = "✅" if self.success else "❌"
        return f"{status} {self.description}"


# 공통으로 사용되는 이슈 생성 함수들
def create_label_issue(rule_id: str, message: str, element_id: str, file_path: str,
                      old_label: str = None, new_label: str = None,
                      page_index: int = None) -> QualityIssue:
    """라벨 관련 이슈 생성"""
    metadata = {}
    if old_label:
        metadata['old_label'] = old_label
    if new_label:
        metadata['new_label'] = new_label
        
    return QualityIssue(
        rule_id=rule_id,
        severity="warning",
        message=message,
        file_path=file_path,
        element_id=element_id,
        page_index=page_index,
        category="label_type",
        suggested_fix=f"라벨을 '{new_label}'로 변경" if new_label else None,
        auto_fixable=True,
        metadata=metadata
    )


def create_content_issue(rule_id: str, element_id: str, content: str, 
                        issue_description: str, file_path: str, page_index: int = None) -> QualityIssue:
    """콘텐츠 관련 이슈 생성"""
    return QualityIssue(
        rule_id=rule_id,
        severity="error",
        message=f"콘텐츠 문제: {issue_description}",
        file_path=file_path,
        element_id=element_id,
        page_index=page_index,
        category="label_content",
        auto_fixable=False,
        metadata={
            "content": content[:100] + "..." if len(content) > 100 else content
        }
    )


def create_structure_issue(rule_id: str, issue_description: str, file_path: str) -> QualityIssue:
    """구조 관련 이슈 생성"""
    return QualityIssue(
        rule_id=rule_id,
        severity="error",
        message=f"구조 문제: {issue_description}",
        file_path=file_path,
        category="structure",
        auto_fixable=False
    )
