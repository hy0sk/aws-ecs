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

# API 1: 메인 화면 (뒤로가기 완벽 지원!)
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AWS 클라우드 갤러리</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 font-sans min-h-screen pb-12">
        <header class="bg-blue-700 text-white shadow-md py-4 mb-6">
            <div class="max-w-4xl mx-auto px-4 flex justify-between items-center">
                <a href="#" class="text-xl font-bold tracking-tight">☁️ Cloud Architecture Board</a>
                <span class="bg-blue-800 text-xs px-2 py-1 rounded text-blue-100">AWS 3-Tier</span>
            </div>
        </header>

        <main class="max-w-4xl mx-auto px-4">
            <div class="bg-white border border-slate-300 shadow-sm rounded-t-lg">
                
                <div class="flex justify-between items-center p-4 border-b border-slate-200 bg-slate-50 rounded-t-lg">
                    <h2 class="text-lg font-bold text-slate-800" id="boardTitle">전체 게시글</h2>
                    <button id="btnShowWrite" onclick="window.location.hash='#write'" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-sm font-medium transition">
                        ✏️ 글쓰기
                    </button>
                </div>

                <div id="listView" class="block">
                    <table class="w-full text-sm text-left text-slate-600">
                        <thead class="text-xs text-slate-500 bg-slate-100 border-b border-slate-200">
                            <tr>
                                <th class="px-4 py-2.5 w-16 text-center font-semibold">번호</th>
                                <th class="px-4 py-2.5 font-semibold">제목</th>
                            </tr>
                        </thead>
                        <tbody id="postsList" class="divide-y divide-slate-200"></tbody>
                    </table>
                </div>

                <div id="readView" class="hidden p-6">
                    <div class="border-b border-slate-200 pb-4 mb-4">
                        <h2 id="readTitle" class="text-xl font-bold text-slate-800 mb-3"></h2>
                        <div class="flex justify-between text-xs text-slate-500">
                            <span id="readId"></span>
                            <div class="relative">
                                <button onclick="toggleMenu()" class="text-slate-400 hover:text-slate-700 px-2">⋮</button>
                                <div id="readMenu" class="hidden absolute right-0 mt-1 w-24 bg-white border border-slate-200 shadow-lg rounded z-10">
                                    <button onclick="window.location.hash='#edit/' + currentEditId" class="block w-full text-left px-4 py-2 hover:bg-slate-50">수정</button>
                                    <button onclick="deletePost()" class="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50">삭제</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div id="readContent" class="text-slate-700 whitespace-pre-line min-h-[150px] text-sm"></div>
                    <div class="mt-8 border-t border-slate-200 pt-4 text-right">
                        <button onclick="window.location.hash=''" class="bg-slate-500 hover:bg-slate-600 text-white px-4 py-1.5 rounded text-sm font-medium transition">목록으로</button>
                    </div>
                </div>

                <div id="writeView" class="hidden p-6 bg-slate-50">
                    <form id="postForm" class="space-y-4">
                        <input type="text" id="title" required class="w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-blue-500 text-sm" placeholder="제목을 입력하세요">
                        <textarea id="content" rows="10" required class="w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-blue-500 text-sm resize-none" placeholder="내용을 입력하세요"></textarea>
                        <div class="flex justify-end gap-2 pt-2">
                            <button type="button" onclick="window.location.hash=''" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2 rounded text-sm font-medium transition">취소</button>
                            <button type="submit" id="submitBtn" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded text-sm font-medium transition">등록</button>
                        </div>
                    </form>
                </div>
                
            </div>
        </main>

        <script>
            let currentPosts = []; 
            let currentEditId = null;

            async function loadPosts() {
                try {
                    const response = await fetch('/posts/');
                    currentPosts = await response.json();
                    renderPosts();
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            function renderPosts() {
                const postsList = document.getElementById('postsList');
                if (currentPosts.length === 0) {
                    postsList.innerHTML = '<tr><td colspan="2" class="text-center py-8 text-slate-400">등록된 게시글이 없습니다.</td></tr>';
                    return;
                }
                
                // 🚀 리스트 클릭 시 주소를 #read/번호 로 바꿈
                postsList.innerHTML = currentPosts.slice().reverse().map(post => `
                    <tr class="hover:bg-slate-50 cursor-pointer transition" onclick="window.location.hash='#read/${post.id}'">
                        <td class="px-4 py-2.5 text-center text-slate-500 w-16">${post.id}</td>
                        <td class="px-4 py-2.5 text-slate-800 font-medium">${post.title}</td>
                    </tr>
                `).join('');
            }

            // ==========================================
            // 🌟 대망의 라우터 기능 (주소창 꼬리표 감지기) 🌟
            // ==========================================
            function router() {
                const hash = window.location.hash;

                // 1. 글쓰기 화면 (#write)
                if (hash === '#write') {
                    currentEditId = null;
                    document.getElementById('title').value = '';
                    document.getElementById('content').value = '';
                    document.getElementById('submitBtn').innerText = '등록';
                    
                    document.getElementById('listView').classList.add('hidden');
                    document.getElementById('readView').classList.add('hidden');
                    document.getElementById('btnShowWrite').classList.add('hidden');
                    document.getElementById('writeView').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '새 글 작성';
                } 
                
                // 2. 글읽기 화면 (#read/번호)
                else if (hash.startsWith('#read/')) {
                    const id = parseInt(hash.replace('#read/', ''));
                    const post = currentPosts.find(p => p.id === id);
                    if(!post) { window.location.hash = ''; return; }
                    
                    currentEditId = id;
                    document.getElementById('readTitle').innerText = post.title;
                    document.getElementById('readId').innerText = `글번호: ${post.id}`;
                    document.getElementById('readContent').innerText = post.content;
                    
                    document.getElementById('listView').classList.add('hidden');
                    document.getElementById('writeView').classList.add('hidden');
                    document.getElementById('btnShowWrite').classList.add('hidden');
                    document.getElementById('readView').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '게시글 읽기';
                    document.getElementById('readMenu').classList.add('hidden');
                } 
                
                // 3. 수정 화면 (#edit/번호)
                else if (hash.startsWith('#edit/')) {
                    const id = parseInt(hash.replace('#edit/', ''));
                    const post = currentPosts.find(p => p.id === id);
                    if(!post) { window.location.hash = ''; return; }

                    currentEditId = id;
                    document.getElementById('title').value = post.title;
                    document.getElementById('content').value = post.content;
                    document.getElementById('submitBtn').innerText = '수정 완료';

                    document.getElementById('readView').classList.add('hidden');
                    document.getElementById('writeView').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '글 수정하기';
                } 
                
                // 4. 기본 목록 화면 (꼬리표가 없거나 # 일 때)
                else {
                    document.getElementById('writeView').classList.add('hidden');
                    document.getElementById('readView').classList.add('hidden');
                    document.getElementById('listView').classList.remove('hidden');
                    document.getElementById('btnShowWrite').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '전체 게시글';
                    renderPosts(); // 목록 최신화
                }
            }

            // 주소창의 # 부분이 바뀔 때마다 router 함수 실행 (뒤로가기 핵심!)
            window.addEventListener('hashchange', router);

            // ==========================================

            function toggleMenu() {
                document.getElementById('readMenu').classList.toggle('hidden');
            }

            async function deletePost() {
                if(!confirm("정말 삭제하시겠습니까?")) return;
                try {
                    await fetch(`/posts/${currentEditId}`, { method: 'DELETE' });
                    await loadPosts();
                    window.location.hash = ''; // 삭제 완료 후 리스트로 이동
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            document.getElementById('postForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const title = document.getElementById('title').value;
                const content = document.getElementById('content').value;

                try {
                    if (currentEditId) {
                        await fetch(`/posts/${currentEditId}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ title, content })
                        });
                    } else {
                        await fetch('/posts/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ title, content })
                        });
                    }
                    await loadPosts();
                    window.location.hash = ''; // 등록/수정 완료 후 리스트로 이동
                } catch (error) {
                    console.error('Error:', error);
                }
            });

            window.onload = async () => {
                await loadPosts();
                router(); // 첫 로딩 시 현재 주소창에 맞게 화면 렌더링
            };
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/posts/")
def read_posts():
    db = SessionLocal()
    posts = db.query(Post).all()
    db.close()
    return posts

@app.post("/posts/")
def create_post(post: PostCreate):
    db = SessionLocal()
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    db.close()
    return {"message": "Success"}

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

@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    db = SessionLocal()
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
    db.close()
    return {"message": "Deleted"}