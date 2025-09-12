#!/usr/bin/env python3
"""
ZIP 파일 비교 스크립트
"""

import zipfile
import os
import json
from pathlib import Path

def extract_and_compare():
    # 경로 설정
    base_dir = Path('C:/Users/User/Documents/GitHub/labeling_qc/upload_compare')
    working_zip = base_dir / 'visualcontent-TLAW1202000221_TP_working.zip'
    notworking_zip = base_dir / 'visualcontent-TLAW1202000221_TP_notworking.zip'
    temp_dir = base_dir / 'temp_compare'
    
    # 기존 temp_compare 폴더 정리
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
    
    temp_dir.mkdir()
    (temp_dir / 'working').mkdir()
    (temp_dir / 'notworking').mkdir()

    # working ZIP 추출
    print("Working ZIP 추출 중...")
    with zipfile.ZipFile(working_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_dir / 'working')
        working_files = zip_ref.namelist()

    # notworking ZIP 추출  
    print("NotWorking ZIP 추출 중...")
    with zipfile.ZipFile(notworking_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_dir / 'notworking')
        notworking_files = zip_ref.namelist()

    print("\n=== ZIP 파일 내용 비교 ===")
    print(f"Working ZIP 파일 수: {len(working_files)}")
    print(f"NotWorking ZIP 파일 수: {len(notworking_files)}")
    
    print("\nWorking ZIP 파일 목록:")
    for f in sorted(working_files):
        print(f"  {f}")
    
    print("\nNotWorking ZIP 파일 목록:")
    for f in sorted(notworking_files):
        print(f"  {f}")
    
    # 파일 차이점 확인
    working_set = set(working_files)
    notworking_set = set(notworking_files)
    
    only_in_working = working_set - notworking_set
    only_in_notworking = notworking_set - working_set
    common_files = working_set & notworking_set
    
    if only_in_working:
        print(f"\nWorking에만 있는 파일 ({len(only_in_working)}개):")
        for f in sorted(only_in_working):
            print(f"  {f}")
    
    if only_in_notworking:
        print(f"\nNotWorking에만 있는 파일 ({len(only_in_notworking)}개):")
        for f in sorted(only_in_notworking):
            print(f"  {f}")
    
    print(f"\n공통 파일 ({len(common_files)}개):")
    for f in sorted(common_files):
        print(f"  {f}")
    
    # visualinfo.json 파일 비교
    working_json = None
    notworking_json = None
    
    for f in working_files:
        if 'visualinfo.json' in f:
            working_json_path = temp_dir / 'working' / f
            with open(working_json_path, 'r', encoding='utf-8') as file:
                working_json = json.load(file)
            break
    
    for f in notworking_files:
        if 'visualinfo.json' in f:
            notworking_json_path = temp_dir / 'notworking' / f
            with open(notworking_json_path, 'r', encoding='utf-8') as file:
                notworking_json = json.load(file)
            break
    
    if working_json and notworking_json:
        print("\n=== visualinfo.json 메타데이터 비교 ===")
        
        working_metadata = working_json.get('metadata', {})
        notworking_metadata = notworking_json.get('metadata', {})
        
        print(f"Working fileId: {working_metadata.get('fileId')}")
        print(f"NotWorking fileId: {notworking_metadata.get('fileId')}")
        
        print(f"Working fileName: {working_metadata.get('fileName')}")
        print(f"NotWorking fileName: {notworking_metadata.get('fileName')}")
        
        print(f"Working created: {working_metadata.get('created')}")
        print(f"NotWorking created: {notworking_metadata.get('created')}")
        
        working_elements = len(working_json.get('elements', []))
        notworking_elements = len(notworking_json.get('elements', []))
        
        print(f"Working elements 수: {working_elements}")
        print(f"NotWorking elements 수: {notworking_elements}")

if __name__ == "__main__":
    extract_and_compare()
