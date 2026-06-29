# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# 1. 데이터베이스 연결 설정
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "password1234!")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "community_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. 데이터베이스 테이블 정의
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    content = Column(String(255))

Base.metadata.create_all(bind=engine)

app = FastAPI()

class PostCreate(BaseModel):
    title: str
    content: str

# API 1: 🌟 메인 화면을 예쁜 HTML/CSS 게시판으로 교체!
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AWS 3-Tier 클라우드 게시판</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 font-sans min-h-screen">
        <header class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-md py-6 px-4 mb-8">
            <div class="max-w-4xl mx-auto flex justify-between items-center">
                <h1 class="text-2xl font-bold tracking-wide">🚀 Cloud Architecture Board</h1>
                <span class="bg-blue-500 text-xs px-3 py-1 rounded-full font-semibold">AWS 3-Tier 완성이틀차</span>
            </div>
        </header>

        <main class="max-w-4xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="md:col-span-1 bg-white p-6 rounded-xl shadow-sm h-fit border border-slate-100">
                <h2 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                    ✍️ 새 글 작성하기
                </h2>
                <form id="postForm" class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">제목</label>
                        <input type="text" id="title" required class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" placeholder="제목을 입력하세요">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">내용</label>
                        <textarea id="content" rows="4" required class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" placeholder="내용을 입력하세요"></textarea>
                    </div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-sm shadow-sm">
                        등록하기
                    </button>
                </form>
            </div>

            <div class="md:col-span-2">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-slate-800">📋 전체 게시글</h2>
                    <button onclick="loadPosts()" class="text-xs text-blue-600 hover:underline">🔄 새로고침</button>
                </div>
                <div id="postsList" class="space-y-4">
                    <div class="text-center py-8 text-slate-400 text-sm">게시글을 불러오는 중...</div>
                </div>
            </div>
        </main>

        <script>
            // 1. 서버에서 게시글 목록 받아와서 화면에 뿌리기 (GET)
            async function loadPosts() {
                try {
                    const response = await fetch('/posts/');
                    const posts = await response.json();
                    const postsList = document.getElementById('postsList');
                    
                    if (posts.length === 0) {
                        postsList.innerHTML = '<div class="text-center py-12 bg-white rounded-xl border border-dashed text-slate-400 text-sm">아직 등록된 게시글이 없습니다. 첫 글을 남겨보세요!</div>';
                        return;
                    }

                    postsList.innerHTML = posts.map(post => `
                        <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-100 transition hover:shadow-md">
                            <h3 class="font-bold text-slate-800 text-base mb-2">${post.title}</h3>
                            <p class="text-slate-600 text-sm whitespace-pre-line">${post.content}</p>
                            <div class="mt-3 pt-3 border-t border-slate-50 flex justify-between items-center text-xs text-slate-400">
                                <span>📌 번호: ${post.id}</span>
                                <span class="text-emerald-500 font-medium">● AWS RDS Storage</span>
                            </div>
                        </div>
                    `).reverse().join(''); // 최신글이 맨 위로 오도록 반전
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            // 2. 폼 제출 시 서버로 데이터 보내기 (POST)
            document.getElementById('postForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const title = document.getElementById('title').value;
                const content = document.getElementById('content').value;

                try {
                    const response = await fetch('/posts/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, content })
                    });

                    if (response.ok) {
                        document.getElementById('title').value = '';
                        document.getElementById('content').value = '';
                        loadPosts(); // 등록 후 목록 새로고침
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            });

            // 페이지 로드 시 자동으로 글 목록 불러오기
            window.onload = loadPosts;
        </script>
    </body>
    </html>
    """
    return html_content

# API 2: 게시글 작성하기 (POST)
@app.get("/posts/")
def read_posts():
    db = SessionLocal()
    posts = db.query(Post).all()
    db.close()
    return posts

# API 3: 게시글 목록 보기 (GET)
@app.post("/posts/")
def create_post(post: PostCreate):
    db = SessionLocal()
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    db.close()
    return {"message": "Success", "post": db_post}