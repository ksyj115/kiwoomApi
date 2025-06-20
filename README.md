# 키움증권 API 자동매매 프로그램

키움증권 Open API+를 이용한 자동매매 프로그램입니다.

## 설치 및 설정

1. 키움증권 Open API+ 설치
   - 키움증권 홈페이지에서 Open API+ 다운로드 및 설치
   - 모의투자 신청 (실제 거래 전 테스트 필요)

2. Python 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```

3. 환경 설정
   - `.env` 파일에 계정 정보 설정
   - `config.py`에서 거래 설정 조정

## 사용법

```bash
python main.py
```

## 주의사항

- 모의투자 환경에서 충분히 테스트 후 실제 거래 사용
- 키움증권 API는 Windows 환경에서만 동작
- 실제 거래 시 책임은 사용자에게 있음 