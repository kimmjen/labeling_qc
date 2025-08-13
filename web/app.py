#!/usr/bin/env python3
"""
웹 앱 - 품질 검수 웹 인터페이스
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.quality_controller import QualityController

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

controller = QualityController()


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """파일 업로드 및 검수"""
    if 'file' not in request.files:
        return jsonify({'error': '파일이 선택되지 않았습니다.'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다.'})
    
    if file and file.filename.endswith('.json'):
        # 파일 저장
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # 품질 검수 실행
        issues = controller.validate_file(Path(filepath))
        
        # 결과 반환
        return jsonify({
            'filename': file.filename,
            'issues_count': len(issues),
            'issues': [issue.to_dict() for issue in issues]
        })
    
    return jsonify({'error': '유효하지 않은 파일 형식입니다. JSON 파일만 지원됩니다.'})


@app.route('/results')
def results():
    """결과 페이지"""
    return render_template('results.html')


@app.route('/api/validate', methods=['POST'])
def api_validate():
    """API: 검증"""
    data = request.get_json()
    
    if not data or 'elements' not in data:
        return jsonify({'error': '유효하지 않은 데이터입니다.'})
    
    # 임시 파일로 저장 후 검증
    temp_file = Path('temp_validation.json')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    try:
        issues = controller.validate_file(temp_file)
        return jsonify({
            'issues_count': len(issues),
            'issues': [issue.to_dict() for issue in issues]
        })
    finally:
        # 임시 파일 삭제
        if temp_file.exists():
            temp_file.unlink()


@app.route('/api/fix', methods=['POST'])
def api_fix():
    """API: 자동 수정"""
    data = request.get_json()
    
    if not data or 'file_path' not in data:
        return jsonify({'error': '파일 경로가 필요합니다.'})
    
    file_path = Path(data['file_path'])
    
    if not file_path.exists():
        return jsonify({'error': '파일을 찾을 수 없습니다.'})
    
    try:
        # 수정 전 이슈 수
        before_issues = controller.validate_file(file_path)
        
        # 자동 수정
        after_issues = controller.auto_fix_file(file_path)
        
        fixed_count = len(before_issues) - len(after_issues)
        
        return jsonify({
            'success': True,
            'before_issues': len(before_issues),
            'after_issues': len(after_issues),
            'fixed_count': fixed_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
