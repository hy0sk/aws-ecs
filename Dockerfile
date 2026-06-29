# 1. 파이썬이 설치된 가벼운 리눅스 환경 가져오기
FROM python:3.9-slim

# 2. 작업할 폴더 지정
WORKDIR /app

# 3. 필요한 라이브러리 목록 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 내 파이썬 코드(main.py)를 도커 안으로 복사
COPY . .

# 5. 서버 실행! (포트는 ALB와 맞추기 위해 80번 사용)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]