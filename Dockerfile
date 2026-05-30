# 1. 어떤 기본 이미지를 쓸 것인가? (가볍고 빠른 Nginx 웹 서버 사용)
FROM nginx:alpine

# 2. 로컬에 있는 index.html 파일을 컨테이너 내부의 Nginx 기본 경로로 복사
COPY index.html /usr/share/nginx/html/index.html

# 3. 80번 포트 개방
EXPOSE 80