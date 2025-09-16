#!/usr/bin/env python3
"""
CSV-ZIP-JSON 연결 관계 검증 및 요약 여부 자동 판단 도구
"""

import csv
import json
import zipfile
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class AbstractValidationTool:
    """추상화 검증 도구"""
    
    def __init__(self, zip_path: str, csv_v2_path: str, csv_v3_path: str):
        self.zip_path = zip_path
        self.csv_v2_path = csv_v2_path
        self.csv_v3_path = csv_v3_path
        
        # 데이터 로드
        self.csv_v2_data = self._load_csv(csv_v2_path)
        self.csv_v3_data = self._load_csv(csv_v3_path)
        
    def _load_csv(self, csv_path: str) -> List[Dict]:
        """CSV 파일 로드"""
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))
    
    def _extract_ids_from_output(self, output_text: str) -> List[int]:
        """output_text에서 ID 추출"""
        ids = re.findall(r'\d+', output_text)
        return [int(id_str) for id_str in ids if id_str.isdigit()]
    
    def _extract_kinx_number(self, source_file: str) -> str:
        """source_file에서 KINX 번호 추출"""
        match = re.search(r'KINX(\d+)', source_file)
        return match.group(1) if match else ""
    
    def _get_json_from_zip(self, kinx_number: str) -> Optional[Dict]:
        """ZIP 파일에서 해당 KINX 번호의 JSON 추출"""
        zip_filename = f'visualcontent-KINX{kinx_number}.zip'
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as main_zip:
                # 임시 디렉토리 생성
                temp_dir = f'temp_{kinx_number}'
                os.makedirs(temp_dir, exist_ok=True)
                
                # 대상 ZIP 추출
                main_zip.extract(zip_filename, temp_dir)
                
                # 내부 ZIP에서 JSON 추출
                inner_zip_path = os.path.join(temp_dir, zip_filename)
                with zipfile.ZipFile(inner_zip_path, 'r') as inner_zip:
                    json_files = [f for f in inner_zip.namelist() 
                                if 'visualinfo' in f and f.endswith('.json')]
                    
                    if json_files:
                        json_file = json_files[0]
                        inner_zip.extract(json_file, temp_dir)
                        
                        # JSON 로드
                        json_path = os.path.join(temp_dir, json_file)
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # 임시 파일 정리
                        os.remove(json_path)
                        os.remove(inner_zip_path)
                        os.rmdir(temp_dir)
                        
                        return data
                    
        except Exception as e:
            print(f"오류 발생 (KINX{kinx_number}): {e}")
            # 정리 시도
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except:
                pass
            
        return None
    
    def analyze_element_by_id(self, json_data: Dict, element_id: int) -> Dict:
        """특정 ID의 요소 분석"""
        elements = json_data.get('elements', [])
        element = next((e for e in elements if e['id'] == str(element_id)), None)
        
        if not element:
            return {
                'found': False,
                'element_id': element_id,
                'error': 'Element not found'
            }
        
        label = element['category']['label']
        element_type = element['category']['type']
        text = element.get('content', {}).get('text', '') if 'content' in element else ''
        confidence = element.get('confidence', 0.0)
        
        # 요약 대상 여부 판단
        is_abstract_target = (label == 'ParaText' and element_type == 'PARAGRAPH')
        
        return {
            'found': True,
            'element_id': element_id,
            'label': label,
            'type': element_type,
            'text': text[:100] + '...' if len(text) > 100 else text,
            'confidence': confidence,
            'is_abstract_target': is_abstract_target,
            'summary': f"{label} ({element_type})"
        }
    
    def validate_single_record(self, index: int) -> Dict:
        """단일 레코드 검증"""
        v2_row = self.csv_v2_data[index]
        v3_row = self.csv_v3_data[index]
        
        source_file = v2_row['source_file']
        kinx_number = self._extract_kinx_number(source_file)
        
        # CSV에서 ID 추출
        v2_ids = self._extract_ids_from_output(v2_row['output_text'])
        v3_ids = self._extract_ids_from_output(v3_row['output_text'])
        
        # JSON 데이터 로드
        json_data = self._get_json_from_zip(kinx_number)
        
        result = {
            'index': index,
            'source_file': source_file,
            'kinx_number': kinx_number,
            'v2_ids': v2_ids,
            'v3_ids': v3_ids,
            'json_loaded': json_data is not None,
            'elements_analysis': {},
            'v2_abstract_count': 0,
            'v3_abstract_count': 0,
            'differences': []
        }
        
        if json_data:
            # 모든 ID 분석
            all_ids = set(v2_ids + v3_ids)
            
            for element_id in all_ids:
                analysis = self.analyze_element_by_id(json_data, element_id)
                result['elements_analysis'][element_id] = analysis
                
                # 요약 대상 카운트
                if analysis.get('is_abstract_target', False):
                    if element_id in v2_ids:
                        result['v2_abstract_count'] += 1
                    if element_id in v3_ids:
                        result['v3_abstract_count'] += 1
            
            # V2와 V3 차이점 분석
            v2_set = set(v2_ids)
            v3_set = set(v3_ids)
            
            if v2_set != v3_set:
                result['differences'] = {
                    'v2_only': list(v2_set - v3_set),
                    'v3_only': list(v3_set - v2_set),
                    'common': list(v2_set & v3_set)
                }
        
        return result
    
    def validate_all(self, max_samples: int = 10) -> List[Dict]:
        """전체 검증 (샘플 제한)"""
        results = []
        
        print(f"=== 전체 검증 (최대 {max_samples}개 샘플) ===")
        
        for i in range(min(max_samples, len(self.csv_v2_data))):
            print(f"\n--- 샘플 {i+1}/{max_samples} ---")
            result = self.validate_single_record(i)
            results.append(result)
            
            # 결과 출력
            self._print_validation_result(result)
        
        return results
    
    def _print_validation_result(self, result: Dict):
        """검증 결과 출력"""
        print(f"파일: {result['source_file']}")
        print(f"KINX: {result['kinx_number']}")
        print(f"JSON 로드: {'✅' if result['json_loaded'] else '❌'}")
        
        if result['json_loaded']:
            print(f"V2 IDs: {result['v2_ids']} (요약대상: {result['v2_abstract_count']}개)")
            print(f"V3 IDs: {result['v3_ids']} (요약대상: {result['v3_abstract_count']}개)")
            
            # 요소별 분석 출력
            for element_id, analysis in result['elements_analysis'].items():
                if analysis['found']:
                    status = "🎯 요약대상" if analysis['is_abstract_target'] else "📝 일반텍스트"
                    print(f"  ID {element_id}: {analysis['summary']} - {analysis['text']} [{status}]")
                else:
                    print(f"  ID {element_id}: ❌ 찾을 수 없음")
            
            # 차이점 출력
            if result['differences']:
                diff = result['differences']
                if diff['v2_only']:
                    print(f"  🔴 V2에만 있음: {diff['v2_only']}")
                if diff['v3_only']:
                    print(f"  🟢 V3에만 있음: {diff['v3_only']}")
        else:
            print("  ❌ JSON 파일을 로드할 수 없습니다.")
    
    def get_summary_statistics(self, results: List[Dict]) -> Dict:
        """요약 통계"""
        total_samples = len(results)
        successful_loads = sum(1 for r in results if r['json_loaded'])
        
        total_v2_abstracts = sum(r['v2_abstract_count'] for r in results)
        total_v3_abstracts = sum(r['v3_abstract_count'] for r in results)
        
        differences_count = sum(1 for r in results if r['differences'])
        
        return {
            'total_samples': total_samples,
            'successful_loads': successful_loads,
            'load_success_rate': successful_loads / total_samples * 100,
            'total_v2_abstracts': total_v2_abstracts,
            'total_v3_abstracts': total_v3_abstracts,
            'differences_count': differences_count,
            'difference_rate': differences_count / successful_loads * 100 if successful_loads > 0 else 0
        }

def main():
    """메인 실행 함수"""
    
    # 도구 초기화
    tool = AbstractValidationTool(
        zip_path='filesforabstract.zip',
        csv_v2_path='responses_v2.csv',
        csv_v3_path='responses_v3.csv'
    )
    
    # 전체 검증 실행
    results = tool.validate_all(max_samples=5)  # 처음 5개만
    
    # 통계 출력
    print(f"\n{'='*50}")
    print("=== 검증 통계 ===")
    stats = tool.get_summary_statistics(results)
    
    print(f"총 샘플 수: {stats['total_samples']}")
    print(f"성공적 로드: {stats['successful_loads']} ({stats['load_success_rate']:.1f}%)")
    print(f"V2 요약 대상 총 개수: {stats['total_v2_abstracts']}")
    print(f"V3 요약 대상 총 개수: {stats['total_v3_abstracts']}")
    print(f"V2-V3 차이 발생: {stats['differences_count']}건 ({stats['difference_rate']:.1f}%)")

if __name__ == "__main__":
    main()