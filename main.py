from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# 1. 데이터베이스 연결 설정 (AWS ECS 환경변수에서 주소를 받아옵니다!)
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "password1234!")
# 여기서 DB_HOST가 나중에 테라폼 outputs.tf에서 튀어나올 'db_endpoint'로 교체됩니다.
DB_HOST = os.getenv("DB_HOST", "localhost") 
DB_NAME = os.getenv("DB_NAME", "community_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"

# DB 엔진 및 세션 생성
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. 데이터베이스 테이블 형태 정의 (게시글)
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    content = Column(String(255))

# 테이블 자동 생성 (서버 켜질 때 DB에 테이블이 없으면 알아서 만듦)
Base.metadata.create_all(bind=engine)

# 3. FastAPI 앱 실행
app = FastAPI()

# 사용자가 입력할 데이터 양식
class PostCreate(BaseModel):
    title: str
    content: str

# API 1: 메인 화면 (서버가 살아있는지 확인)
@app.get("/")
def read_root():
    return {"message": "🚀 형석님의 파이썬 서버가 AWS RDS와 성공적으로 연결되었습니다!"}

# API 2: 게시글 작성하기 (POST)
@app.post("/posts/")
def create_post(post: PostCreate):
    db = SessionLocal()
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    db.close()
    return {"message": "글이 성공적으로 작성되었습니다!", "post": db_post}

# API 3: 게시글 목록 보기 (GET)
@app.get("/posts/")
def read_posts():
    db = SessionLocal()
    posts = db.query(Post).all()
    db.close()
    return posts