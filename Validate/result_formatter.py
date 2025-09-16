#!/usr/bin/env python3
"""
CSV 결과를 원하는 형태로 변환
sourcefile, v2_output, v2_output_result, v3_output, v3_output_result
"""

import csv
import json
import zipfile
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class ResultFormatter:
    """결과를 원하는 형태로 포맷팅"""
    
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
        """ZIP 파일에서 해당 KINX 번호의 JSON 추출 (간소화)"""
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
            print(f"오류 발생 (KINX{kinx_number}): {e}")
            
        return None
    
    def _analyze_output_result(self, json_data: Dict, ids: List[int]) -> Dict:
        """output 결과 분석"""
        if not json_data or not ids:
            return {
                'total_ids': len(ids),
                'paratext_count': 0,
                'listtext_count': 0,
                'other_count': 0,
                'paratext_ids': [],
                'listtext_ids': [],
                'other_ids': [],
                'summary': "No data"
            }
        
        elements = json_data.get('elements', [])
        id_to_element = {e['id']: e for e in elements}
        
        paratext_ids = []
        listtext_ids = []
        other_ids = []
        
        for element_id in ids:
            element = id_to_element.get(str(element_id))
            if element:
                label = element['category']['label']
                if label == 'ParaText':
                    paratext_ids.append(element_id)
                elif label == 'ListText':
                    listtext_ids.append(element_id)
                else:
                    other_ids.append(element_id)
            else:
                other_ids.append(element_id)  # 찾을 수 없는 ID
        
        return {
            'total_ids': len(ids),
            'paratext_count': len(paratext_ids),
            'listtext_count': len(listtext_ids),
            'other_count': len(other_ids),
            'paratext_ids': paratext_ids,
            'listtext_ids': listtext_ids,
            'other_ids': other_ids,
            'summary': f"ParaText:{len(paratext_ids)}, ListText:{len(listtext_ids)}, Other:{len(other_ids)}"
        }
    
    def process_all_records(self, max_records: int = None) -> List[Dict]:
        """모든 레코드 처리"""
        results = []
        total_records = len(self.csv_v2_data)
        
        if max_records:
            total_records = min(max_records, total_records)
        
        print(f"=== 총 {total_records}개 레코드 처리 ===")
        
        for i in range(total_records):
            if i % 10 == 0:
                print(f"진행률: {i}/{total_records} ({i/total_records*100:.1f}%)")
            
            v2_row = self.csv_v2_data[i]
            v3_row = self.csv_v3_data[i]
            
            source_file = v2_row['source_file']
            kinx_number = self._extract_kinx_number(source_file)
            
            # CSV에서 ID 추출
            v2_ids = self._extract_ids_from_output(v2_row['output_text'])
            v3_ids = self._extract_ids_from_output(v3_row['output_text'])
            
            # JSON 데이터 로드
            json_data = self._get_json_from_zip(kinx_number)
            
            # 결과 분석
            v2_result = self._analyze_output_result(json_data, v2_ids)
            v3_result = self._analyze_output_result(json_data, v3_ids)
            
            result = {
                'source_file': source_file,
                'v2_output': str(v2_ids),
                'v2_output_result': v2_result['summary'],
                'v2_paratext_ids': str(v2_result['paratext_ids']),
                'v2_listtext_ids': str(v2_result['listtext_ids']),
                'v3_output': str(v3_ids),
                'v3_output_result': v3_result['summary'],
                'v3_paratext_ids': str(v3_result['paratext_ids']),
                'v3_listtext_ids': str(v3_result['listtext_ids']),
                'json_loaded': json_data is not None
            }
            
            results.append(result)
        
        print(f"완료: {total_records}개 레코드 처리됨")
        return results
    
    def save_to_csv(self, results: List[Dict], output_path: str = 'validation_results.csv'):
        """결과를 CSV로 저장"""
        
        fieldnames = [
            'source_file',
            'v2_output',
            'v2_output_result',
            'v2_paratext_ids',
            'v2_listtext_ids',
            'v3_output', 
            'v3_output_result',
            'v3_paratext_ids',
            'v3_listtext_ids',
            'json_loaded'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"결과가 {output_path}에 저장되었습니다.")
    
    def print_summary_statistics(self, results: List[Dict]):
        """요약 통계 출력"""
        total = len(results)
        successful_loads = sum(1 for r in results if r['json_loaded'])
        
        # ParaText vs ListText 통계
        v2_paratext_total = 0
        v2_listtext_total = 0
        v3_paratext_total = 0
        v3_listtext_total = 0
        
        for result in results:
            if result['json_loaded']:
                # 간단히 개수 계산 (문자열에서 숫자 개수)
                v2_para_count = len(eval(result['v2_paratext_ids'])) if result['v2_paratext_ids'] != '[]' else 0
                v2_list_count = len(eval(result['v2_listtext_ids'])) if result['v2_listtext_ids'] != '[]' else 0
                v3_para_count = len(eval(result['v3_paratext_ids'])) if result['v3_paratext_ids'] != '[]' else 0
                v3_list_count = len(eval(result['v3_listtext_ids'])) if result['v3_listtext_ids'] != '[]' else 0
                
                v2_paratext_total += v2_para_count
                v2_listtext_total += v2_list_count
                v3_paratext_total += v3_para_count
                v3_listtext_total += v3_list_count
        
        print(f"\n=== 요약 통계 ===")
        print(f"총 레코드 수: {total}")
        print(f"성공적 JSON 로드: {successful_loads} ({successful_loads/total*100:.1f}%)")
        print(f"\nV2 결과:")
        print(f"  - ParaText 총 개수: {v2_paratext_total}")
        print(f"  - ListText 총 개수: {v2_listtext_total}")
        print(f"\nV3 결과:")
        print(f"  - ParaText 총 개수: {v3_paratext_total}")
        print(f"  - ListText 총 개수: {v3_listtext_total}")
        
        print(f"\n차이:")
        print(f"  - ParaText 증가: {v3_paratext_total - v2_paratext_total}")
        print(f"  - ListText 증가: {v3_listtext_total - v2_listtext_total}")

def main():
    """메인 실행 함수"""
    
    # 포맷터 초기화
    formatter = ResultFormatter(
        zip_path='filesforabstract.zip',
        csv_v2_path='responses_v2.csv',
        csv_v3_path='responses_v3.csv'
    )
    
    # 전체 레코드 처리 
    results = formatter.process_all_records()  # 전체 데이터 처리
    
    # CSV로 저장
    formatter.save_to_csv(results)
    
    # 통계 출력
    formatter.print_summary_statistics(results)
    
    # 처음 5개 결과 미리보기
    print(f"\n=== 처음 5개 결과 미리보기 ===")
    for i, result in enumerate(results[:5]):
        print(f"\n{i+1}. {result['source_file']}")
        print(f"   V2: {result['v2_output']} -> {result['v2_output_result']}")
        print(f"   V3: {result['v3_output']} -> {result['v3_output_result']}")

if __name__ == "__main__":
    main()