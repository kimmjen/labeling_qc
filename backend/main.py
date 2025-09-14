#!/usr/bin/env python3
"""
FastAPI 백엔드 서버 - 라벨링 품질 검수 API
CLI 도구의 기능을 웹 API로 제공
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import tempfile
import os
from pathlib import Path
import sys

# 백엔드 모듈들 임포트 (상대경로 사용)
from src.core import QualityController
from src.utils import AdvancedQualityAnalyzer
from src.core.rule_fixer import RuleBasedFixer

# FastAPI 앱 생성
app = FastAPI(
    title="라벨링 품질 검수 API",
    description="AI 기반 라벨링 품질 검수 및 자동 수정 API",
    version="2.0.0"
)

# CORS 설정 (React 프론트엔드와 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 인스턴스
controller = QualityController()
ai_analyzer = AdvancedQualityAnalyzer()

# Pydantic 모델들
class QualityIssueResponse(BaseModel):
    rule_id: str
    severity: str
    message: str
    file_path: str
    element_id: Optional[str] = None
    page_index: Optional[int] = None
    category: str
    suggested_fix: Optional[str] = None
    auto_fixable: bool

class AIAnalysisResponse(BaseModel):
    anomalies: List[Dict[str, Any]]
    optimizations: Dict[str, List[str]]
    quality_score: int

class ValidationResultResponse(BaseModel):
    filename: str
    issues_count: int
    issues: List[QualityIssueResponse]
    ai_analysis: AIAnalysisResponse

class LabelPredictionRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class LabelPredictionResponse(BaseModel):
    predicted_label: str
    confidence: float
    reason: str
    alternatives: List[Dict[str, Any]]

class TrendAnalysisRequest(BaseModel):
    history: List[Dict[str, Any]]

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "라벨링 품질 검수 API 서버",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "labeling-qc-api"}

@app.post("/upload", response_model=ValidationResultResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    파일 업로드 및 품질 검수
    CLI의 파일 검수 기능을 API로 제공
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="JSON 파일만 지원됩니다")

    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        try:
            # 1. 기본 품질 검수 실행
            issues = controller.validate_file(temp_path)

            # 2. JSON 데이터 로드
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 3. AI 분석 실행
            anomalies = ai_analyzer.detect_anomalies(data)
            optimizations = ai_analyzer.generate_optimization_suggestions(issues)

            # 4. 품질 점수 계산 (간단한 공식)
            quality_score = max(0, min(100, 100 - len(issues) * 2))

            # 5. 응답 데이터 구성
            issues_data = []
            for issue in issues:
                issues_data.append(QualityIssueResponse(
                    rule_id=issue.rule_id,
                    severity=issue.severity,
                    message=issue.message,
                    file_path=issue.file_path,
                    element_id=getattr(issue, 'element_id', None),
                    page_index=getattr(issue, 'page_index', None),
                    category=issue.category,
                    suggested_fix=getattr(issue, 'suggested_fix', None),
                    auto_fixable=issue.auto_fixable
                ))

            ai_analysis = AIAnalysisResponse(
                anomalies=anomalies,
                optimizations=optimizations,
                quality_score=quality_score
            )

            return ValidationResultResponse(
                filename=file.filename,
                issues_count=len(issues),
                issues=issues_data,
                ai_analysis=ai_analysis
            )

        finally:
            # 임시 파일 정리
            if temp_path.exists():
                os.unlink(temp_path)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="유효하지 않은 JSON 파일입니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류: {str(e)}")

@app.post("/api/predict_label", response_model=LabelPredictionResponse)
async def predict_label(request: LabelPredictionRequest):
    """
    AI 라벨 예측
    CLI의 AI 예측 기능을 API로 제공
    """
    try:
        label, confidence, reason = ai_analyzer.predict_optimal_label(
            request.text,
            request.context or {}
        )

        alternatives = ai_analyzer._get_alternative_predictions(request.text)

        return LabelPredictionResponse(
            predicted_label=label,
            confidence=confidence,
            reason=reason,
            alternatives=alternatives
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"라벨 예측 중 오류: {str(e)}")

@app.post("/api/analyze_trends")
async def analyze_trends(request: TrendAnalysisRequest):
    """
    품질 트렌드 분석
    CLI의 트렌드 분석 기능을 API로 제공
    """
    try:
        analysis = ai_analyzer.analyze_quality_trends(request.history)
        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"트렌드 분석 중 오류: {str(e)}")

@app.post("/api/auto_fix")
async def auto_fix_file(file: UploadFile = File(...)):
    """
    자동 수정 기능
    CLI의 자동 수정 기능을 API로 제공
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="JSON 파일만 지원됩니다")

    try:
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / file.filename

            # 파일 저장
            content = await file.read()
            with open(temp_path, 'wb') as f:
                f.write(content)

            # 수정 전 검증
            before_issues = controller.validate_file(temp_path)

            # 자동 수정 실행
            fixer = RuleBasedFixer(temp_path.parent)
            fixes = fixer.run_all_rule_fixes()

            if fixes:
                fixer.save_fixes()

            # 수정 후 검증
            after_issues = controller.validate_file(temp_path)

            # 수정된 파일 내용 읽기
            with open(temp_path, 'r', encoding='utf-8') as f:
                fixed_data = json.load(f)

            return {
                "success": True,
                "before_issues": len(before_issues),
                "after_issues": len(after_issues),
                "fixed_count": len(before_issues) - len(after_issues),
                "fixed_data": fixed_data,
                "fixes_applied": fixes
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자동 수정 중 오류: {str(e)}")

@app.get("/api/system_status")
async def system_status():
    """
    시스템 상태 확인
    CLI의 시스템 상태 확인 기능을 API로 제공
    """
    try:
        import psutil

        # 메모리 정보
        memory = psutil.virtual_memory()

        # CPU 정보
        cpu_percent = psutil.cpu_percent(interval=1)

        # 디스크 정보
        disk = psutil.disk_usage('/')

        return {
            "status": "healthy",
            "memory": {
                "total": f"{memory.total // (1024**3)}GB",
                "used": f"{memory.used // (1024**3)}GB",
                "percent": f"{memory.percent}%"
            },
            "cpu": {
                "percent": f"{cpu_percent}%"
            },
            "disk": {
                "total": f"{disk.total // (1024**3)}GB",
                "used": f"{disk.used // (1024**3)}GB",
                "percent": f"{(disk.used/disk.total)*100:.1f}%"
            },
            "modules": {
                "quality_controller": "loaded",
                "ai_analyzer": "loaded",
                "rule_fixer": "loaded"
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/rules")
async def get_validation_rules():
    """
    검증 규칙 목록 조회
    """
    try:
        rules = controller.validator.rules
        return {
            "rules": rules,
            "total_rules": len(rules)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"규칙 조회 중 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPI 서버 시작 중...")
    print("📡 URL: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("🔧 ReDoc: http://localhost:8000/redoc")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src/"]
    )
