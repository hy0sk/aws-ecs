from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional

# 1. 데이터베이스 연결 설정
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "password1234!")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "community_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

SECRET_KEY = "aws_cloud_architecture_super_secret_key"
ALGORITHM = "HS256"


# 2. 데이터베이스 테이블 정의
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    content = Column(String(255))
    author = Column(String(50), default="익명")
    post_password = Column(String(255), nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255))


Base.metadata.create_all(bind=engine)

# 4. 보안 헬퍼 함수
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

# 테이블 생성 직후에 아래 코드를 추가해 주세요!
Base.metadata.create_all(bind=engine)

# 🚀 서버가 켜질 때 hy0sk 관리자 계정이 없으면 자동 생성하는 코드
with SessionLocal() as init_db:
    admin_user = (
        init_db.query(User).filter(User.username == "hy0sk").first()
    )
    if not admin_user:
        hashed_admin_pw = hash_password(
            "qlalfqjsgh0!"
        )  # 사용할 비밀번호 입력!
        db_admin = User(username="hy0sk", password=hashed_admin_pw)
        init_db.add(db_admin)
        init_db.commit()

with engine.connect() as conn:
    try:
        conn.execute(
            text(
                "ALTER TABLE posts ADD COLUMN author VARCHAR(50) DEFAULT '익명';"
            )
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            text(
                "ALTER TABLE posts ADD COLUMN post_password VARCHAR(255) NULL;"
            )
        )
        conn.commit()
    except Exception:
        pass

app = FastAPI()


# 3. 데이터 검증 모델
class PostCreate(BaseModel):
    title: str
    content: str
    author: str = "익명"
    post_password: Optional[str] = None


class PostAction(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    post_password: Optional[str] = None
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str



def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_jwt_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ==========================================
# 🌟 프론트엔드 UI (hy0sk 웹페이지 & 비번 필수 검사)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>hy0sk 웹페이지</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 font-sans min-h-screen pb-12">
        <header class="bg-blue-700 text-white shadow-md py-4 mb-6">
            <div class="max-w-4xl mx-auto px-4 flex justify-between items-center">
                <a href="#" class="text-xl font-bold tracking-tight">☁️ hy0sk 웹페이지</a>
                <div id="authSection" class="flex items-center gap-3 text-sm"></div>
            </div>
        </header>

        <main class="max-w-4xl mx-auto px-4">
            <div class="bg-white border border-slate-300 shadow-sm rounded-t-lg">
                <div class="flex justify-between items-center p-4 border-b border-slate-200 bg-slate-50 rounded-t-lg">
                    <h2 class="text-lg font-bold text-slate-800" id="boardTitle">전체 게시글</h2>
                    <button id="btnShowWrite" onclick="window.location.hash='#write'" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-sm font-medium transition">✏️ 글쓰기</button>
                </div>

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

                <div id="writeView" class="hidden p-6 bg-slate-50">
                    <form id="postForm" class="space-y-4">
                        <div class="flex justify-between items-center text-xs text-slate-500 mb-1">
                            <span>✍️ 작성자: <strong id="currentAuthorDisplay" class="text-blue-600">익명</strong></span>
                            <!-- 🚀 기본값 1234 완전 삭제! 필수 입력 안내로 변경 -->
                            <div id="postPwContainer" class="flex items-center gap-2">
                                <label class="text-slate-600 font-bold">🔑 게시글 비번:</label>
                                <input type="password" id="postPw" class="px-2 py-1 border border-slate-300 rounded text-xs w-32 focus:outline-none focus:border-blue-500" placeholder="비밀번호(필수)">
                            </div>
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

        <div id="authModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4">
            <div class="bg-white rounded-lg shadow-xl max-w-sm w-full p-6 relative animate-fade-in">
                <button onclick="closeModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600">✕</button>
                <h3 id="modalTitle" class="text-lg font-bold text-slate-800 mb-4">🔑 로그인</h3>
                <form id="authForm" class="space-y-3">
                    <input type="text" id="authUser" required class="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none" placeholder="아이디">
                    <input type="password" id="authPass" required class="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none" placeholder="비밀번호">
                    <button type="submit" id="authSubmitBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded text-sm transition mt-2">로그인</button>
                </form>
            </div>
        </div>

        <script>
            let currentPosts = []; let currentEditId = null; let authMode = 'login';

            function updateAuthUI() {
                const username = localStorage.getItem('username');
                const authSection = document.getElementById('authSection');
                const authorDisplay = document.getElementById('currentAuthorDisplay');
                const pwContainer = document.getElementById('postPwContainer');
                
                if (username) {
                    const badge = (username === 'hy0sk') ? '👑 관리자 hy0sk님' : `👑 ${username}님`;
                    authSection.innerHTML = `<span class="bg-blue-800 text-blue-100 px-2.5 py-1 rounded text-xs font-semibold">${badge}</span><button onclick="logout()" class="text-blue-200 hover:text-white text-xs underline">로그아웃</button>`;
                    if(authorDisplay) authorDisplay.innerText = username;
                    if(pwContainer) pwContainer.classList.add('hidden');
                } else {
                    authSection.innerHTML = `<button onclick="openModal('login')" class="bg-blue-800 hover:bg-blue-900 px-3 py-1.5 rounded transition text-xs font-medium">🔑 로그인</button><button onclick="openModal('signup')" class="bg-white text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded transition text-xs font-bold">✨ 회원가입</button>`;
                    if(authorDisplay) authorDisplay.innerText = '익명';
                    if(pwContainer) pwContainer.classList.remove('hidden');
                }
            }

            function openModal(mode) {
                authMode = mode;
                document.getElementById('modalTitle').innerText = mode === 'login' ? '🔑 로그인' : '✨ 새 계정 만들기';
                document.getElementById('authSubmitBtn').innerText = mode === 'login' ? '로그인' : '회원가입 완료';
                document.getElementById('authModal').classList.remove('hidden');
            }
            function closeModal() { document.getElementById('authModal').classList.add('hidden'); document.getElementById('authUser').value = ''; document.getElementById('authPass').value = ''; }

            document.getElementById('authForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('authUser').value; const password = document.getElementById('authPass').value;
                try {
                    const res = await fetch(authMode === 'login' ? '/login' : '/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
                    const data = await res.json();
                    if (!res.ok) { alert(data.detail || "오류가 발생했습니다."); return; }
                    if (authMode === 'signup') { alert("🎉 회원가입 성공! 이제 로그인해주세요."); openModal('login'); } 
                    else { localStorage.setItem('token', data.token); localStorage.setItem('username', data.username); alert(`👑 환영합니다, ${data.username}님!`); closeModal(); updateAuthUI(); }
                } catch (e) { console.error('Error:', e); }
            });

            function logout() { localStorage.removeItem('token'); localStorage.removeItem('username'); alert("로그아웃 되었습니다."); updateAuthUI(); }
            async function loadPosts() { try { const res = await fetch('/posts/'); currentPosts = await res.json(); renderPosts(); } catch (e) { console.error('Error:', e); } }

            function renderPosts() {
                const list = document.getElementById('postsList');
                if (currentPosts.length === 0) { list.innerHTML = '<tr><td colspan="3" class="text-center py-8 text-slate-400">등록된 게시글이 없습니다.</td></tr>'; return; }
                list.innerHTML = currentPosts.slice().reverse().map(p => `
                    <tr class="hover:bg-slate-50 cursor-pointer transition" onclick="window.location.hash='#read/${p.id}'">
                        <td class="px-4 py-2.5 text-center text-slate-500 w-16">${p.id}</td><td class="px-4 py-2.5 text-slate-800 font-medium">${p.title}</td>
                        <td class="px-4 py-2.5 text-center text-slate-500 w-28 text-xs"><span class="bg-slate-100 px-2 py-1 rounded">${p.author || '익명'}</span></td>
                    </tr>`).join('');
            }

            function router() {
                const hash = window.location.hash;
                if (hash === '#write') {
                    currentEditId = null; document.getElementById('title').value = ''; document.getElementById('content').value = '';
                    if(document.getElementById('postPw')) document.getElementById('postPw').value = '';
                    document.getElementById('submitBtn').innerText = '등록';
                    document.getElementById('listView').classList.add('hidden'); document.getElementById('readView').classList.add('hidden');
                    document.getElementById('btnShowWrite').classList.add('hidden'); document.getElementById('writeView').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '새 글 작성'; updateAuthUI();
                } else if (hash.startsWith('#read/')) {
                    const id = parseInt(hash.replace('#read/', '')); const post = currentPosts.find(p => p.id === id);
                    if(!post) { window.location.hash = ''; return; }
                    currentEditId = id; document.getElementById('readTitle').innerText = post.title;
                    document.getElementById('readId').innerText = `글번호: ${post.id}`; document.getElementById('readAuthor').innerText = `👤 작성자: ${post.author || '익명'}`;
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
                    document.getElementById('boardTitle').innerText = '글 수정하기'; updateAuthUI();
                } else {
                    document.getElementById('writeView').classList.add('hidden'); document.getElementById('readView').classList.add('hidden');
                    document.getElementById('listView').classList.remove('hidden'); document.getElementById('btnShowWrite').classList.remove('hidden');
                    document.getElementById('boardTitle').innerText = '전체 게시글'; renderPosts();
                }
            }
            window.addEventListener('hashchange', router);
            function toggleMenu() { document.getElementById('readMenu').classList.toggle('hidden'); }
            
            async function deletePost() {
                const post = currentPosts.find(p => p.id === currentEditId);
                const currentUsername = localStorage.getItem('username');
                let postPassword = null;

                // 👑 hy0sk 관리자는 비번 없이 프리패스!
                if (currentUsername !== 'hy0sk') {
                    if (post.author === '익명' || post.author !== currentUsername) {
                        postPassword = prompt("🚨 익명 글(또는 타인 글)을 삭제하려면 게시글 비밀번호를 입력하세요:", "");
                        if (postPassword === null) return; 
                    }
                }

                if (!confirm("정말 이 게시글을 삭제하시겠습니까?")) return;

                try {
                    const res = await fetch(`/posts/${currentEditId}`, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ post_password: postPassword, username: currentUsername })
                    });
                    const data = await res.json();
                    if (!res.ok) { alert("⛔ " + (data.detail || "권한이 없습니다!")); return; }
                    alert("🗑️ 게시글이 삭제되었습니다.");
                    await loadPosts(); window.location.hash = '';
                } catch (e) { console.error('Error:', e); }
            }

            document.getElementById('postForm').addEventListener('submit', async (e) => {
                e.preventDefault(); 
                const title = document.getElementById('title').value; 
                const content = document.getElementById('content').value;
                const author = localStorage.getItem('username') || '익명';
                
                let rawPw = (author === '익명' && document.getElementById('postPw')) ? document.getElementById('postPw').value : null;
                const post_password = (rawPw && rawPw.trim() !== "") ? rawPw.trim() : null;

                // 🚀 [핵심 수정!] 익명으로 글 작성/수정할 때 비밀번호를 비워두면 경고 띄우고 차단!
                if (author === '익명' && !post_password && !currentEditId) {
                    alert("⚠️ 익명 게시글 작성 시 비밀번호를 꼭 입력해야 합니다!");
                    document.getElementById('postPw').focus();
                    return;
                }

                try {
                    if (currentEditId) {
                        const post = currentPosts.find(p => p.id === currentEditId);
                        let editPw = post_password;
                        
                        if (author !== 'hy0sk') {
                            if (post.author === '익명' || post.author !== author) {
                                editPw = prompt("🚨 게시글 수정 비밀번호를 입력하세요:", "");
                                if (editPw === null) return;
                                if (!editPw || editPw.trim() === "") {
                                    alert("⚠️ 비밀번호를 입력해야 수정할 수 있습니다!");
                                    return;
                                }
                            }
                        }
                        const res = await fetch(`/posts/${currentEditId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, content, post_password: editPw, username: author }) });
                        if (!res.ok) { const d = await res.json(); alert("⛔ " + (d.detail || "수정 권한이 없습니다!")); return; }
                    } else { 
                        const res = await fetch('/posts/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, content, author, post_password }) }); 
                        if (!res.ok) { 
                            const d = await res.json();
                            alert("⛔ " + (d.detail || "게시글 등록에 실패했습니다.")); 
                            return; 
                        }
                    }
                    await loadPosts(); 
                    window.location.hash = '';
                } catch (e) { 
                    console.error('Error:', e); 
                    alert("서버와 통신 중 오류가 발생했습니다.");
                }
            });

            window.onload = async () => { updateAuthUI(); await loadPosts(); router(); };
        </script>
    </body>
    </html>
    """
    return html_content


# ==========================================
# 🌟 백엔드 API (👑 hy0sk 관리자 & 비번 필수 검증)
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
    # 🚀 백엔드에서도 익명 글인데 비밀번호가 없으면 에러 뱉고 거절!
    if post.author == "익명" and not post.post_password:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="익명 게시글 작성 시 비밀번호를 꼭 입력해야 합니다!",
        )

    hashed_pw = (
        hash_password(post.post_password)
        if (post.post_password and post.author == "익명")
        else None
    )
    db_post = Post(
        title=post.title,
        content=post.content,
        author=post.author,
        post_password=hashed_pw,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    db.close()
    return {"message": "Success"}


@app.put("/posts/{post_id}")
def update_post(post_id: int, action: PostAction):
    db = SessionLocal()
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        db.close()
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")

    is_admin = action.username == "hy0sk"

    if not is_admin:
        if db_post.author != "익명":
            if db_post.author != action.username:
                db.close()
                raise HTTPException(
                    status_code=403,
                    detail="다른 사람의 글은 수정할 수 없습니다!",
                )
        else:
            if not action.post_password or not verify_password(
                action.post_password, db_post.post_password
            ):
                db.close()
                raise HTTPException(
                    status_code=403, detail="게시글 비밀번호가 틀렸습니다!"
                )

    if action.title:
        db_post.title = action.title
    if action.content:
        db_post.content = action.content
    db.commit()
    db.close()
    return {"message": "Updated"}


@app.delete("/posts/{post_id}")
def delete_post(post_id: int, action: PostAction):
    db = SessionLocal()
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        db.close()
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")

    is_admin = action.username == "hy0sk"

    if not is_admin:
        if db_post.author != "익명":
            if db_post.author != action.username:
                db.close()
                raise HTTPException(
                    status_code=403,
                    detail="회원이 작성한 글은 본인만 삭제할 수 있습니다!",
                )
        else:
            if not action.post_password or not verify_password(
                action.post_password, db_post.post_password
            ):
                db.close()
                raise HTTPException(
                    status_code=403,
                    detail="게시글 비밀번호가 일치하지 않습니다!",
                )

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


@app.post("/login")
def login(user: UserCreate):
    db = SessionLocal()
    db_user = db.query(User).filter(User.username == user.username).first()
    db.close()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=401, detail="아이디 또는 비밀번호가 일치하지 않습니다."
        )
    token = create_jwt_token(db_user.username)
    return {
        "message": "로그인 성공!",
        "token": token,
        "username": db_user.username,
    }