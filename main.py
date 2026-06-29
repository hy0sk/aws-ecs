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

# API 1: 메인 화면 (UI & 프론트엔드 로직)
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
            <div class="md:col-span-1 bg-white p-6 rounded-xl shadow-sm h-fit border border-slate-100 sticky top-8">
                <h2 id="formTitle" class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
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
                    <button id="submitBtn" type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-sm shadow-sm">
                        등록하기
                    </button>
                    <button id="cancelBtn" type="button" onclick="cancelEdit()" class="hidden w-full bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium py-2 rounded-lg transition text-sm shadow-sm mt-2">
                        수정 취소
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
            let editingId = null; // 수정 중인 글의 ID를 기억하는 공간

            // 게시글 불러오기
            async function loadPosts() {
                try {
                    const response = await fetch('/posts/');
                    const posts = await response.json();
                    const postsList = document.getElementById('postsList');
                    
                    if (posts.length === 0) {
                        postsList.innerHTML = '<div class="text-center py-12 bg-white rounded-xl border border-dashed text-slate-400 text-sm">등록된 게시글이 없습니다.</div>';
                        return;
                    }

                    postsList.innerHTML = posts.map(post => `
                        <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-100 transition hover:shadow-md relative group">
                            
                            <div class="absolute top-4 right-3">
                                <button onclick="toggleMenu(${post.id})" class="text-slate-400 hover:text-slate-600 focus:outline-none p-1">
                                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path></svg>
                                </button>
                                <div id="menu-${post.id}" class="hidden absolute right-0 mt-1 w-20 bg-white rounded-md shadow-lg border border-slate-100 z-10 overflow-hidden">
                                    <button onclick="startEdit(${post.id})" class="block w-full text-left px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 border-b border-slate-50">수정</button>
                                    <button onclick="deletePost(${post.id})" class="block w-full text-left px-4 py-2 text-xs font-medium text-red-600 hover:bg-red-50">삭제</button>
                                </div>
                            </div>

                            <h3 id="post-title-${post.id}" class="font-bold text-slate-800 text-base mb-2 pr-8">${post.title}</h3>
                            <p id="post-content-${post.id}" class="text-slate-600 text-sm whitespace-pre-line">${post.content}</p>
                            
                            <div class="mt-3 pt-3 border-t border-slate-50 flex justify-between items-center text-xs text-slate-400">
                                <span>📌 번호: ${post.id}</span>
                                <span class="text-emerald-500 font-medium">● AWS RDS Storage</span>
                            </div>
                        </div>
                    `).reverse().join('');
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            // 점 3개 메뉴 열기/닫기
            function toggleMenu(id) {
                document.querySelectorAll('[id^="menu-"]').forEach(el => {
                    if (el.id !== `menu-${id}`) el.classList.add('hidden');
                });
                document.getElementById(`menu-${id}`).classList.toggle('hidden');
            }

            // 바탕화면 클릭 시 열려있는 메뉴 닫기
            document.addEventListener('click', function(event) {
                if (!event.target.closest('.relative')) {
                    document.querySelectorAll('[id^="menu-"]').forEach(el => el.classList.add('hidden'));
                }
            });

            // 🟢 게시글 삭제 (DELETE)
            async function deletePost(id) {
                if(!confirm("이 게시글을 정말 삭제하시겠습니까?")) return;
                
                try {
                    await fetch(`/posts/${id}`, { method: 'DELETE' });
                    loadPosts(); // 삭제 후 새로고침
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            // 🟠 게시글 수정 모드 켜기
            function startEdit(id) {
                const title = document.getElementById(`post-title-${id}`).innerText;
                const content = document.getElementById(`post-content-${id}`).innerText;

                document.getElementById('title').value = title;
                document.getElementById('content').value = content;
                editingId = id; // 수정할 ID 기억

                // 폼 디자인을 '수정 모드'로 변경
                document.getElementById('formTitle').innerHTML = '📝 글 수정하기';
                const submitBtn = document.getElementById('submitBtn');
                submitBtn.innerText = '수정 완료';
                submitBtn.classList.replace('bg-blue-600', 'bg-emerald-600');
                submitBtn.classList.replace('hover:bg-blue-700', 'hover:bg-emerald-700');
                
                document.getElementById('cancelBtn').classList.remove('hidden');
                document.getElementById(`menu-${id}`).classList.add('hidden'); // 메뉴 닫기
                window.scrollTo({ top: 0, behavior: 'smooth' }); // 위로 부드럽게 스크롤
            }

            // 🔘 수정 취소 (원래대로)
            function cancelEdit() {
                editingId = null;
                document.getElementById('title').value = '';
                document.getElementById('content').value = '';
                
                document.getElementById('formTitle').innerHTML = '✍️ 새 글 작성하기';
                const submitBtn = document.getElementById('submitBtn');
                submitBtn.innerText = '등록하기';
                submitBtn.classList.replace('bg-emerald-600', 'bg-blue-600');
                submitBtn.classList.replace('hover:bg-emerald-700', 'hover:bg-blue-700');
                
                document.getElementById('cancelBtn').classList.add('hidden');
            }

            // 🔵 폼 제출 (POST:등록 / PUT:수정)
            document.getElementById('postForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const title = document.getElementById('title').value;
                const content = document.getElementById('content').value;

                try {
                    if (editingId) {
                        // 수정 중일 때
                        await fetch(`/posts/${editingId}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ title, content })
                        });
                        cancelEdit(); // 폼 초기화
                    } else {
                        // 새 글일 때
                        await fetch('/posts/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ title, content })
                        });
                        document.getElementById('title').value = '';
                        document.getElementById('content').value = '';
                    }
                    loadPosts(); // 목록 새로고침
                } catch (error) {
                    console.error('Error:', error);
                }
            });

            window.onload = loadPosts;
        </script>
    </body>
    </html>
    """
    return html_content

# API 2: 리스트 불러오기 (GET)
@app.get("/posts/")
def read_posts():
    db = SessionLocal()
    posts = db.query(Post).all()
    db.close()
    return posts

# API 3: 게시글 등록 (POST)
@app.post("/posts/")
def create_post(post: PostCreate):
    db = SessionLocal()
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    db.close()
    return {"message": "Success"}

# 🚀 API 4: 게시글 수정 (PUT) 추가
@app.put("/posts/{post_id}")
def update_post(post_id: int, post: PostCreate):
    db = SessionLocal()
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post:
        db_post.title = post.title
        db_post.content = post.content
        db.commit()
    db.close()
    return {"message": "Updated"}

# 🚀 API 5: 게시글 삭제 (DELETE) 추가
@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    db = SessionLocal()
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
    db.close()
    return {"message": "Deleted"}