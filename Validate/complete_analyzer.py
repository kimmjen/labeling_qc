#!/usr/bin/env python3
"""
전체 데이터 처리 및 더 나은 분석 결과 생성
"""

import csv
import json
import zipfile
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 기존 ResultFormatter 클래스를 개선
class AdvancedResultFormatter:
    """고급 결과 포맷터"""
    
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
                # 메모리에서 처리
                zip_data = main_zip.read(zip_filename)
                
                # 메모리상에서 내부 ZIP 처리
                from io import BytesIO
                with zipfile.ZipFile(BytesIO(zip_data), 'r') as inner_zip:
                    json_files = [f for f in inner_zip.namelist() 
                                if 'visualinfo' in f and f.endswith('.json')]
                    
                    if json_files:
                        json_file = json_files[0]
                        json_data = inner_zip.read(json_file)
                        return json.loads(json_data.decode('utf-8'))
                        
        except Exception as e:
            # 오류는 조용히 처리
            pass
            
        return None
    
    def _analyze_detailed_result(self, json_data: Dict, ids: List[int]) -> Dict:
        """상세한 결과 분석"""
        if not json_data or not ids:
            return {
                'total_ids': len(ids),
                'paratext_count': 0,
                'listtext_count': 0,
                'other_count': 0,
                'paratext_details': [],
                'listtext_details': [],
                'other_details': [],
                'summary': "No data" if not ids else "JSON load failed"
            }
        
        elements = json_data.get('elements', [])
        id_to_element = {e['id']: e for e in elements}
        
        paratext_details = []
        listtext_details = []
        other_details = []
        
        for element_id in ids:
            element = id_to_element.get(str(element_id))
            if element:
                label = element['category']['label']
                elem_type = element['category']['type']
                text = element.get('content', {}).get('text', '')[:50] if 'content' in element else ''
                
                detail = {
                    'id': element_id,
                    'label': label,
                    'type': elem_type,
                    'text': text
                }
                
                if label == 'ParaText':
                    paratext_details.append(detail)
                elif label == 'ListText':
                    listtext_details.append(detail)
                else:
                    other_details.append(detail)
            else:
                other_details.append({
                    'id': element_id,
                    'label': 'NotFound',
                    'type': 'NotFound',
                    'text': ''
                })
        
        return {
            'total_ids': len(ids),
            'paratext_count': len(paratext_details),
            'listtext_count': len(listtext_details),
            'other_count': len(other_details),
            'paratext_details': paratext_details,
            'listtext_details': listtext_details,
            'other_details': other_details,
            'summary': f"P:{len(paratext_details)}|L:{len(listtext_details)}|O:{len(other_details)}"
        }
    
    def process_all_records(self, max_records: int = None) -> List[Dict]:
        """모든 레코드 처리"""
        results = []
        total_records = len(self.csv_v2_data)
        
        if max_records:
            total_records = min(max_records, total_records)
        
        print(f"=== 총 {total_records}개 레코드 처리 중... ===")
        
        for i in range(total_records):
            if i % 10 == 0 or i == total_records - 1:
                print(f"진행률: {i+1}/{total_records} ({(i+1)/total_records*100:.1f}%)")
            
            v2_row = self.csv_v2_data[i]
            v3_row = self.csv_v3_data[i]
            
            source_file = v2_row['source_file']
            kinx_number = self._extract_kinx_number(source_file)
            
            # CSV에서 ID 추출
            v2_ids = self._extract_ids_from_output(v2_row['output_text'])
            v3_ids = self._extract_ids_from_output(v3_row['output_text'])
            
            # JSON 데이터 로드
            json_data = self._get_json_from_zip(kinx_number)
            
            # 상세 분석
            v2_analysis = self._analyze_detailed_result(json_data, v2_ids)
            v3_analysis = self._analyze_detailed_result(json_data, v3_ids)
            
            # 차이점 분석
            v2_set = set(v2_ids)
            v3_set = set(v3_ids)
            
            difference = {
                'has_difference': v2_set != v3_set,
                'v2_only': list(v2_set - v3_set),
                'v3_only': list(v3_set - v2_set),
                'common': list(v2_set & v3_set)
            }
            
            result = {
                'source_file': source_file,
                'kinx_number': kinx_number,
                'v2_output': str(v2_ids),
                'v2_result_summary': v2_analysis['summary'],
                'v2_paratext_count': v2_analysis['paratext_count'],
                'v2_listtext_count': v2_analysis['listtext_count'],
                'v2_other_count': v2_analysis['other_count'],
                'v3_output': str(v3_ids),
                'v3_result_summary': v3_analysis['summary'],
                'v3_paratext_count': v3_analysis['paratext_count'],
                'v3_listtext_count': v3_analysis['listtext_count'],
                'v3_other_count': v3_analysis['other_count'],
                'has_difference': difference['has_difference'],
                'v2_only_ids': str(difference['v2_only']),
                'v3_only_ids': str(difference['v3_only']),
                'json_loaded': json_data is not None,
                'total_v2_ids': len(v2_ids),
                'total_v3_ids': len(v3_ids)
            }
            
            results.append(result)
        
        print(f"✅ 완료: {total_records}개 레코드 처리됨")
        return results
    
    def save_to_csv(self, results: List[Dict], output_path: str = 'complete_validation_results.csv'):
        """결과를 CSV로 저장"""
        
        fieldnames = [
            'source_file',
            'kinx_number',
            'v2_output',
            'v2_result_summary',
            'v2_paratext_count',
            'v2_listtext_count', 
            'v2_other_count',
            'v3_output',
            'v3_result_summary',
            'v3_paratext_count',
            'v3_listtext_count',
            'v3_other_count',
            'has_difference',
            'v2_only_ids',
            'v3_only_ids',
            'total_v2_ids',
            'total_v3_ids',
            'json_loaded'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"📊 결과가 {output_path}에 저장되었습니다.")
    
    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """요약 리포트 생성"""
        total = len(results)
        successful_loads = sum(1 for r in results if r['json_loaded'])
        differences = sum(1 for r in results if r['has_difference'])
        
        # 타입별 통계
        v2_paratext_total = sum(r['v2_paratext_count'] for r in results)
        v2_listtext_total = sum(r['v2_listtext_count'] for r in results)
        v2_other_total = sum(r['v2_other_count'] for r in results)
        
        v3_paratext_total = sum(r['v3_paratext_count'] for r in results)
        v3_listtext_total = sum(r['v3_listtext_count'] for r in results)
        v3_other_total = sum(r['v3_other_count'] for r in results)
        
        # ID 개수 통계
        v2_total_ids = sum(r['total_v2_ids'] for r in results)
        v3_total_ids = sum(r['total_v3_ids'] for r in results)
        
        return {
            'total_records': total,
            'successful_loads': successful_loads,
            'load_success_rate': successful_loads / total * 100 if total > 0 else 0,
            'differences_count': differences,
            'difference_rate': differences / successful_loads * 100 if successful_loads > 0 else 0,
            'v2_stats': {
                'total_ids': v2_total_ids,
                'paratext': v2_paratext_total,
                'listtext': v2_listtext_total,
                'other': v2_other_total
            },
            'v3_stats': {
                'total_ids': v3_total_ids,
                'paratext': v3_paratext_total,
                'listtext': v3_listtext_total,
                'other': v3_other_total
            },
            'improvements': {
                'id_increase': v3_total_ids - v2_total_ids,
                'paratext_increase': v3_paratext_total - v2_paratext_total,
                'listtext_increase': v3_listtext_total - v2_listtext_total,
                'other_increase': v3_other_total - v2_other_total
            }
        }

def main():
    """메인 실행 함수"""
    
    print("🚀 고급 결과 분석 도구 시작")
    
    # 포맷터 초기화
    formatter = AdvancedResultFormatter(
        zip_path='filesforabstract.zip',
        csv_v2_path='responses_v2.csv', 
        csv_v3_path='responses_v3.csv'
    )
    
    # 전체 레코드 처리
    results = formatter.process_all_records()  # 전체 처리
    
    # CSV로 저장
    formatter.save_to_csv(results)
    
    # 요약 리포트 생성
    summary = formatter.generate_summary_report(results)
    
    print(f"\n{'='*60}")
    print("📊 최종 분석 결과")
    print(f"{'='*60}")
    print(f"총 레코드 수: {summary['total_records']}")
    print(f"성공적 JSON 로드: {summary['successful_loads']} ({summary['load_success_rate']:.1f}%)")
    print(f"V2-V3 차이 발생: {summary['differences_count']}건 ({summary['difference_rate']:.1f}%)")
    
    print(f"\n📈 V2 결과:")
    print(f"  - 총 ID 개수: {summary['v2_stats']['total_ids']}")
    print(f"  - ParaText: {summary['v2_stats']['paratext']}개")
    print(f"  - ListText: {summary['v2_stats']['listtext']}개")
    print(f"  - 기타: {summary['v2_stats']['other']}개")
    
    print(f"\n📈 V3 결과:")
    print(f"  - 총 ID 개수: {summary['v3_stats']['total_ids']}")
    print(f"  - ParaText: {summary['v3_stats']['paratext']}개")
    print(f"  - ListText: {summary['v3_stats']['listtext']}개")
    print(f"  - 기타: {summary['v3_stats']['other']}개")
    
    print(f"\n🔄 V2 → V3 개선사항:")
    print(f"  - 총 ID 증가: {summary['improvements']['id_increase']}개")
    print(f"  - ParaText 증가: {summary['improvements']['paratext_increase']}개")
    print(f"  - ListText 증가: {summary['improvements']['listtext_increase']}개")
    print(f"  - 기타 증가: {summary['improvements']['other_increase']}개")
    
    # 차이가 있는 케이스 몇 개 출력
    diff_cases = [r for r in results if r['has_difference']]
    if diff_cases:
        print(f"\n🔍 차이가 있는 케이스 예시 (총 {len(diff_cases)}개 중 처음 5개):")
        for i, case in enumerate(diff_cases[:5]):
            print(f"  {i+1}. {case['source_file']}")
            print(f"     V2: {case['v2_output']} -> {case['v2_result_summary']}")
            print(f"     V3: {case['v3_output']} -> {case['v3_result_summary']}")
            if case['v3_only_ids'] != '[]':
                print(f"     V3 추가: {case['v3_only_ids']}")

if __name__ == "__main__":
    main()