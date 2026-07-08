from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import bcrypt
import jwt
from datetime import datetime, timedelta

# 1. 데이터베이스 연결 설정
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "password1234!")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "community_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. JWT 토큰 설정 (암호화 열쇠)
SECRET_KEY = "aws_cloud_architecture_super_secret_key"
ALGORITHM = "HS256"

# 3. 데이터베이스 테이블 정의
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    content = Column(String(255))
    author = Column(String(50), default="익명")  # 🚀 작성자 컬럼 추가!

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255))

Base.metadata.create_all(bind=engine)

# 🚀 기존 DB 테이블에 author 컬럼이 없으면 자동 추가하는 마이그레이션 로직
try:
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE posts ADD COLUMN author VARCHAR(50) DEFAULT '익명';"
            )
        )
        conn.commit()
except Exception:
    pass  # 이미 컬럼이 존재하면 패스!

app = FastAPI()

# 4. 데이터 검증 모델
class PostCreate(BaseModel):
    title: str
    content: str
    author: str = "익명"

class UserCreate(BaseModel):
    username: str
    password: str

# 5. 보안 헬퍼 함수
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )

def create_jwt_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=24),  # 24시간 동안 유효
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ==========================================
# 🌟 프론트엔드 UI (로그인 모달 & 작성자 연동) 🌟
# ==========================================
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
        <!-- 상단 헤더 & 로그인 상태바 -->
        <header class="bg-blue-700 text-white shadow-md py-4 mb-6">
            <div class="max-w-4xl mx-auto px-4 flex justify-between items-center">
                <a href="#" class="text-xl font-bold tracking-tight">☁️ Cloud Architecture Board</a>
                
                <!-- 우측 상단 유저 컨트롤 -->
                <div id="authSection" class="flex items-center gap-3 text-sm">
                    <button onclick="openModal('login')" class="bg-blue-800 hover:bg-blue-900 px-3 py-1.5 rounded transition text-xs font-medium">🔑 로그인</button>
                    <button onclick="openModal('signup')" class="bg-white text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded transition text-xs font-bold">✨ 회원가입</button>
                </div>
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

                <!-- 1. 리스트 뷰 -->
                <div id="listView" class="block">
                    <table class="w-full text-sm text-left text-slate-600">
                        <thead class="text-xs text-slate-500 bg-slate-100 border-b border-slate-200">
                            <tr>
                                <th class="px-4 py-2.5 w-16 text-center font-semibold">번호</th>
                                <th class="px-4 py-2.5 font-semibold">제목</th>
                                <th class="px-4 py-2.5 w-28 text-center font-semibold">작성자</th>
                            </tr>
                        </thead>
                        <tbody id="postsList" class="divide-y divide-slate-200"></tbody>
                    </table>
                </div>

                <!-- 2. 읽기 뷰 -->
                <div id="readView" class="hidden p-6">
                    <div class="border-b border-slate-200 pb-4 mb-4">
                        <h2 id="readTitle" class="text-xl font-bold text-slate-800 mb-2"></h2>
                        <div class="flex justify-between items-center text-xs text-slate-500">
                            <div>
                                <span id="readId" class="mr-3"></span>
                                <span id="readAuthor" class="font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded"></span>
                            </div>
                            <div class="relative">
                                <button onclick="toggleMenu()" class="text-slate-400 hover:text-slate-700 px-2 text-base">⋮</button>
                                <div id="readMenu" class="hidden absolute right-0 mt-1 w-24 bg-white border border-slate-200 shadow-lg rounded z-10">
                                    <button onclick="window.location.hash='#edit/' + currentEditId" class="block w-full text-left px-4 py-2 hover:bg-slate-50 text-xs">수정</button>
                                    <button onclick="deletePost()" class="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 text-xs">삭제</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div id="readContent" class="text-slate-700 whitespace-pre-line min-h-[150px] text-sm"></div>
                    <div class="mt-8 border-t border-slate-200 pt-4 text-right">
                        <button onclick="window.location.hash=''" class="bg-slate-500 hover:bg-slate-600 text-white px-4 py-1.5 rounded text-sm font-medium transition">목록으로</button>
                    </div>
                </div>

                <!-- 3. 쓰기/수정 뷰 -->
                <div id="writeView" class="hidden p-6 bg-slate-50">
                    <form id="postForm" class="space-y-4">
                        <div class="flex justify-between items-center text-xs text-slate-500 mb-1">
                            <span>✍️ 작성자: <strong id="currentAuthorDisplay" class="text-blue-600">익명</strong></span>
                        </div>
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

        <!-- 🚀 로그인 & 회원가입 모달 창 -->
        <div id="authModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4">
            <div class="bg-white rounded-lg shadow-xl max-w-sm w-full p-6 relative animate-fade-in">
                <button onclick="closeModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600">✕</button>
                <h3 id="modalTitle" class="text-lg font-bold text-slate-800 mb-4">🔑 로그인</h3>
                <form id="authForm" class="space-y-3">
                    <input type="text" id="authUser" required class="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-blue-500" placeholder="아이디 (username)">
                    <input type="password" id="authPass" required class="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-blue-500" placeholder="비밀번호">
                    <button type="submit" id="authSubmitBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded text-sm transition mt-2">로그인</button>
                </form>
            </div>
        </div>

        <script>
            let currentPosts = []; let currentEditId = null;
            let authMode = 'login'; // 'login' or 'signup'

            // 🟢 UI 업데이트 (로그인 상태에 따라 상단 버튼 변경)
            function updateAuthUI() {
                const username = localStorage.getItem('username');
                const authSection = document.getElementById('authSection');
                const authorDisplay = document.getElementById('currentAuthorDisplay');
                
                if (username) {
                    authSection.innerHTML = `
                        <span class="bg-blue-800 text-blue-100 px-2.5 py-1 rounded text-xs font-semibold">👑 ${username}님</span>
                        <button onclick="logout()" class="text-blue-200 hover:text-white text-xs underline">로그아웃</button>
                    `;
                    if(authorDisplay) authorDisplay.innerText = username;
                } else {
                    authSection.innerHTML = `
                        <button onclick="openModal('login')" class="bg-blue-800 hover:bg-blue-900 px-3 py-1.5 rounded transition text-xs font-medium">🔑 로그인</button>
                        <button onclick="openModal('signup')" class="bg-white text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded transition text-xs font-bold">✨ 회원가입</button>
                    `;
                    if(authorDisplay) authorDisplay.innerText = '익명';
                }
            }

            // 모달 열기/닫기
            function openModal(mode) {
                authMode = mode;
                document.getElementById('modalTitle').innerText = mode === 'login' ? '🔑 로그인' : '✨ 새 계정 만들기';
                document.getElementById('authSubmitBtn').innerText = mode === 'login' ? '로그인' : '회원가입 완료';
                document.getElementById('authModal').classList.remove('hidden');
            }
            function closeModal() {
                document.getElementById('authModal').classList.add('hidden');
                document.getElementById('authUser').value = '';
                document.getElementById('authPass').value = '';
            }

            // 🔐 로그인 & 회원가입 폼 제출 처리
            document.getElementById('authForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('authUser').value;
                const password = document.getElementById('authPass').value;
                const endpoint = authMode === 'login' ? '/login' : '/signup';

                try {
                    const res = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const data = await res.json();

                    if (!res.ok) {
                        alert(data.detail || "오류가 발생했습니다.");
                        return;
                    }

                    if (authMode === 'signup') {
                        alert("🎉 회원가입 성공! 이제 로그인해주세요.");
                        openModal('login'); // 가입 성공 시 로그인 창으로 전환
                    } else {
                        // 로그인 성공 시 발급받은 출입증(토큰)과 유저명 저장!
                        localStorage.setItem('token', data.token);
                        localStorage.setItem('username', data.username);
                        alert(`👑 환영합니다, ${data.username}님!`);
                        closeModal();
                        updateAuthUI();
                    }
                } catch (e) { console.error('Error:', e); }
            });

            function logout() {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                alert("로그아웃 되었습니다.");
                updateAuthUI();
            }

            // 게시글 목록 불러오기
            async function loadPosts() {
                try { const res = await fetch('/posts/'); currentPosts = await res.json(); renderPosts(); } 
                catch (e) { console.error('Error:', e); }
            }

            function renderPosts() {
                const list = document.getElementById('postsList');
                if (currentPosts.length === 0) { list.innerHTML = '<tr><td colspan="3" class="text-center py-8 text-slate-400">등록된 게시글이 없습니다.</td></tr>'; return; }
                
                list.innerHTML = currentPosts.slice().reverse().map(p => `
                    <tr class="hover:bg-slate-50 cursor-pointer transition" onclick="window.location.hash='#read/${p.id}'">
                        <td class="px-4 py-2.5 text-center text-slate-500 w-16">${p.id}</td>
                        <td class="px-4 py-2.5 text-slate-800 font-medium">${p.title}</td>
                        <td class="px-4 py-2.5 text-center text-slate-500 w-28 text-xs"><span class="bg-slate-100 px-2 py-1 rounded">${p.author || '익명'}</span></td>
                    </tr>
                `).join('');
            }

            function router() {
                const hash = window.location.hash;
                if (hash === '#write') {
                    currentEditId = null; document.getElementById('title').value = ''; document.getElementById('content').value = '';
                    document.getElementById('submitBtn').innerText = '등록';
                    document.getElementById('listView').classList.add('hidden'); document.getElementById('readView').classList.add('hidden');
                    document.getElementById('btnShowWrite').classList.add('hidden'); document.getElementById('writeView').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '새 글 작성';
                    updateAuthUI();
                } else if (hash.startsWith('#read/')) {
                    const id = parseInt(hash.replace('#read/', '')); const post = currentPosts.find(p => p.id === id);
                    if(!post) { window.location.hash = ''; return; }
                    currentEditId = id; document.getElementById('readTitle').innerText = post.title;
                    document.getElementById('readId').innerText = `글번호: ${post.id}`; 
                    document.getElementById('readAuthor').innerText = `👤 작성자: ${post.author || '익명'}`;
                    document.getElementById('readContent').innerText = post.content;
                    document.getElementById('listView').classList.add('hidden'); document.getElementById('writeView').classList.add('hidden');
                    document.getElementById('btnShowWrite').classList.add('hidden'); document.getElementById('readView').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '게시글 읽기'; document.getElementById('readMenu').classList.add('hidden');
                } else if (hash.startsWith('#edit/')) {
                    const id = parseInt(hash.replace('#edit/', '')); const post = currentPosts.find(p => p.id === id);
                    if(!post) { window.location.hash = ''; return; }
                    currentEditId = id; document.getElementById('title').value = post.title; document.getElementById('content').value = post.content;
                    document.getElementById('submitBtn').innerText = '수정 완료';
                    document.getElementById('readView').classList.add('hidden'); document.getElementById('writeView').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '글 수정하기';
                } else {
                    document.getElementById('writeView').classList.add('hidden'); document.getElementById('readView').classList.add('hidden');
                    document.getElementById('listView').classList.remove('hidden'); document.getElementById('btnShowWrite').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '전체 게시글'; renderPosts();
                }
            }
            window.addEventListener('hashchange', router);
            function toggleMenu() { document.getElementById('readMenu').classList.toggle('hidden'); }
            
            async function deletePost() {
                if(!confirm("정말 삭제하시겠습니까?")) return;
                try { await fetch(`/posts/${currentEditId}`, { method: 'DELETE' }); await loadPosts(); window.location.hash = ''; } 
                catch (e) { console.error('Error:', e); }
            }

            // 🚀 게시글 등록 시 현재 로그인한 유저명(author)을 함께 전송!
            document.getElementById('postForm').addEventListener('submit', async (e) => {
                e.preventDefault(); 
                const title = document.getElementById('title').value; 
                const content = document.getElementById('content').value;
                const author = localStorage.getItem('username') || '익명';

                try {
                    if (currentEditId) { 
                        await fetch(`/posts/${currentEditId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, content, author }) }); 
                    } else { 
                        await fetch('/posts/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, content, author }) }); 
                    }
                    await loadPosts(); window.location.hash = '';
                } catch (e) { console.error('Error:', e); }
            });

            window.onload = async () => { updateAuthUI(); await loadPosts(); router(); };
        </script>
    </body>
    </html>
    """
    return html_content

# ==========================================
# 🌟 백엔드 API (게시판 CRUD + 인증) 🌟
# ==========================================
@app.get("/posts/")
def read_posts():
    db = SessionLocal()
    posts = db.query(Post).all()
    db.close()
    return posts

@app.post("/posts/")
def create_post(post: PostCreate):
    db = SessionLocal()
    db_post = Post(title=post.title, content=post.content, author=post.author)
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
        db_post.author = post.author
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

@app.post("/signup")
def signup(user: UserCreate):
    db = SessionLocal()
    existing_user = (
        db.query(User).filter(User.username == user.username).first()
    )
    if existing_user:
        db.close()
        raise HTTPException(
            status_code=400, detail="이미 존재하는 아이디입니다."
        )

    hashed_pw = hash_password(user.password)
    db_user = User(username=user.username, password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return {"message": "회원가입 성공!", "username": db_user.username}

# 🚀 [신규] 로그인 & JWT 토큰 발급 API!
@app.post("/login")
def login(user: UserCreate):
    db = SessionLocal()
    db_user = db.query(User).filter(User.username == user.username).first()
    db.close()

    # 아이디가 없거나, 비밀번호 해시 검증에 실패한 경우
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=401, detail="아이디 또는 비밀번호가 일치하지 않습니다."
        )

    # 검증 성공 시 디지털 출입증(JWT Access Token) 발급
    token = create_jwt_token(db_user.username)
    return {
        "message": "로그인 성공!",
        "token": token,
        "username": db_user.username,
    }