#!/usr/bin/env python3
"""
새로운 ZIP 파일 비교 스크립트 - TLAW1202000305_TP.zip
"""

import zipfile
import os
import json
from pathlib import Path

def compare_new_zips():
    # 경로 설정
    base_dir = Path('C:/Users/User/Documents/GitHub/labeling_qc/upload_compare')
    working_zip = base_dir / 'working' / 'visualcontent-TLAW1202000305_TP.zip'
    notworking_zip = base_dir / 'notworking' / 'visualcontent-TLAW1202000305_TP.zip'
    temp_dir = base_dir / 'temp_compare_new'
    
    # 기존 temp_compare_new 폴더 정리
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
    
    temp_dir.mkdir()
    (temp_dir / 'working').mkdir()
    (temp_dir / 'notworking').mkdir()

    # working ZIP 추출
    print("Working ZIP (TLAW1202000305_TP) 추출 중...")
    with zipfile.ZipFile(working_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_dir / 'working')
        working_files = zip_ref.namelist()

    # notworking ZIP 추출  
    print("NotWorking ZIP (TLAW1202000305_TP) 추출 중...")
    with zipfile.ZipFile(notworking_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_dir / 'notworking')
        notworking_files = zip_ref.namelist()

    print("\n=== ZIP 파일 내용 비교 (TLAW1202000305_TP) ===")
    print(f"Working ZIP 파일 수: {len(working_files)}")
    print(f"NotWorking ZIP 파일 수: {len(notworking_files)}")
    
    print(f"\nWorking ZIP 파일 목록 ({len(working_files)}개):")
    for f in sorted(working_files):
        file_path = temp_dir / 'working' / f
        if file_path.is_file():
            size = file_path.stat().st_size
            print(f"  {f} ({size:,} bytes)")
        else:
            print(f"  {f} (폴더)")
    
    print(f"\nNotWorking ZIP 파일 목록 ({len(notworking_files)}개):")
    for f in sorted(notworking_files):
        file_path = temp_dir / 'notworking' / f
        if file_path.is_file():
            size = file_path.stat().st_size
            print(f"  {f} ({size:,} bytes)")
        else:
            print(f"  {f} (폴더)")
    
    # 파일 차이점 확인
    working_set = set(working_files)
    notworking_set = set(notworking_files)
    
    only_in_working = working_set - notworking_set
    only_in_notworking = notworking_set - working_set
    common_files = working_set & notworking_set
    
    if only_in_working:
        print(f"\n✅ Working에만 있는 파일 ({len(only_in_working)}개):")
        for f in sorted(only_in_working):
            print(f"  {f}")
    
    if only_in_notworking:
        print(f"\n❌ NotWorking에만 있는 파일 ({len(only_in_notworking)}개):")
        for f in sorted(only_in_notworking):
            print(f"  {f}")
    
    print(f"\n📄 공통 파일 ({len(common_files)}개):")
    for f in sorted(common_files):
        print(f"  {f}")
    
    # 이미지 파일 수 확인
    working_images = [f for f in working_files if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.jpeg')]
    notworking_images = [f for f in notworking_files if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.jpeg')]
    
    print(f"\n🖼️ 이미지 파일 수:")
    print(f"  Working: {len(working_images)}개")
    print(f"  NotWorking: {len(notworking_images)}개")
    
    if working_images:
        print(f"\n✅ Working 이미지 파일들:")
        for img in working_images:
            file_path = temp_dir / 'working' / img
            size = file_path.stat().st_size
            print(f"  {img} ({size:,} bytes)")
    
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
        
        working_elements = len(working_json.get('elements', []))
        notworking_elements = len(notworking_json.get('elements', []))
        
        print(f"Working elements 수: {working_elements}")
        print(f"NotWorking elements 수: {notworking_elements}")
        
        # 이미지 관련 elements 찾기
        working_image_elements = []
        notworking_image_elements = []
        
        for element in working_json.get('elements', []):
            if 'content' in element and 'imagePath' in element.get('content', {}):
                working_image_elements.append(element['content']['imagePath'])
        
        for element in notworking_json.get('elements', []):
            if 'content' in element and 'imagePath' in element.get('content', {}):
                notworking_image_elements.append(element['content']['imagePath'])
        
        print(f"\n🖼️ JSON에서 참조하는 이미지 경로 수:")
        print(f"  Working: {len(working_image_elements)}개")
        print(f"  NotWorking: {len(notworking_image_elements)}개")
        
        if working_image_elements:
            print(f"\n✅ Working JSON의 이미지 경로들 (처음 5개):")
            for i, path in enumerate(working_image_elements[:5]):
                print(f"  {i+1}. {path}")
        
        if notworking_image_elements:
            print(f"\n❌ NotWorking JSON의 이미지 경로들 (처음 5개):")
            for i, path in enumerate(notworking_image_elements[:5]):
                print(f"  {i+1}. {path}")

if __name__ == "__main__":
    compare_new_zips()
