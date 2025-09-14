#!/usr/bin/env python3
"""
라벨링 품질 컨트롤러
전체적인 품질 검수 프로세스를 관리
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..models.quality_issue import QualityIssue
from .rule_validator import RuleValidator
from .rule_fixer import RuleBasedFixer


@dataclass
class QualityReport:
    """품질 검수 보고서"""
    total_files: int
    processed_files: int
    total_issues: int
    fixed_issues: int
    remaining_issues: int
    issue_types: Dict[str, int]
    processing_time: float


class QualityController:
    """메인 품질 검수 컨트롤러"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.validator = RuleValidator()
        self.fixer = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def validate_file(self, file_path: Path) -> List[QualityIssue]:
        """단일 파일 검증"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            issues = self.validator.validate_all_rules(data, str(file_path))
            
            self.logger.info(f"파일 검증 완료: {file_path} ({len(issues)}개 이슈)")
            return issues
            
        except Exception as e:
            self.logger.error(f"파일 검증 실패: {file_path} - {e}")
            return [QualityIssue(
                rule_id="SYSTEM_ERROR",
                severity="error",
                message=f"파일 로드 실패: {str(e)}",
                file_path=str(file_path)
            )]
    
    def validate_directory(self, dir_path: Path) -> Dict[str, List[QualityIssue]]:
        """디렉토리 내 모든 JSON 파일 검증"""
        results = {}
        json_files = list(dir_path.rglob("*.json"))
        
        self.logger.info(f"디렉토리 검증 시작: {dir_path} ({len(json_files)}개 파일)")
        
        for file_path in json_files:
            issues = self.validate_file(file_path)
            if issues:
                results[str(file_path)] = issues
        
        return results
    
    def auto_fix_file(self, file_path: Path) -> List[QualityIssue]:
        """단일 파일 자동 수정"""
        if not self.fixer:
            self.fixer = RuleBasedFixer(file_path.parent)
        
        try:
            # 수정 전 검증
            before_issues = self.validate_file(file_path)
            
            # 자동 수정 실행
            fixes = self.fixer.run_all_rule_fixes()
            
            # 수정 후 검증
            after_issues = self.validate_file(file_path)
            
            fixed_count = len(before_issues) - len(after_issues)
            self.logger.info(f"자동 수정 완료: {file_path} ({fixed_count}개 수정)")
            
            return after_issues
            
        except Exception as e:
            self.logger.error(f"자동 수정 실패: {file_path} - {e}")
            return []
    
    def generate_report(self, validation_results: Dict[str, List[QualityIssue]], 
                       processing_time: float) -> QualityReport:
        """품질 검수 보고서 생성"""
        total_files = len(validation_results)
        total_issues = sum(len(issues) for issues in validation_results.values())
        
        # 이슈 타입별 분류
        issue_types = {}
        for issues in validation_results.values():
            for issue in issues:
                issue_types[issue.rule_id] = issue_types.get(issue.rule_id, 0) + 1
        
        return QualityReport(
            total_files=total_files,
            processed_files=total_files,
            total_issues=total_issues,
            fixed_issues=0,  # 자동 수정 후 계산
            remaining_issues=total_issues,
            issue_types=issue_types,
            processing_time=processing_time
        )
    
    def export_report(self, report: QualityReport, output_path: Path):
        """보고서 파일로 내보내기"""
        report_data = {
            "summary": {
                "total_files": report.total_files,
                "processed_files": report.processed_files,
                "total_issues": report.total_issues,
                "fixed_issues": report.fixed_issues,
                "remaining_issues": report.remaining_issues,
                "processing_time": report.processing_time
            },
            "issue_breakdown": report.issue_types,
            "timestamp": str(Path().cwd())  # 현재 시간으로 대체 가능
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"보고서 저장 완료: {output_path}")


def main():
    """테스트용 메인 함수"""
    controller = QualityController()
    
    # 샘플 디렉토리 검증
    test_dir = Path("test_data")
    if test_dir.exists():
        results = controller.validate_directory(test_dir)
        
        if results:
            print(f"🔍 품질 검수 결과: {len(results)}개 파일에서 이슈 발견")
            for file_path, issues in results.items():
                print(f"📄 {file_path}: {len(issues)}개 이슈")
        else:
            print("✅ 모든 파일이 품질 기준을 만족합니다.")
    else:
        print("⚠️ 테스트 데이터 디렉토리를 찾을 수 없습니다.")


if __name__ == "__main__":
    main()
