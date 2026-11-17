from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt

engine = create_engine("sqlite:///tarefas.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
password_hash = PasswordHash.recommended()
SECRET_KEY = "bfbf5979632bb1a24369c537ac614df9a49190d70272f606cf1a6747be2c4ada"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title="ToDoList debloatado",
    description="Uma API para criação e manipulação de tarefas, útil para um To Do List, por exemplo.",
    version="1.4",
)

class Tarefa(BaseModel):
    titulo: str
    desc: str
    concluida: bool = False

class Usuario(BaseModel):
    email: str
    senha: str

class TarefaSaida(Tarefa):
    id: int
    model_config = {"from_attributes": True}

class TarefaDB(Base):
    __tablename__ = "tarefas"

    id = Column(Integer, primary_key=True)
    titulo = Column(String)
    desc = Column(String)
    concluida = Column(Boolean, default=False)

class UsuarioDB(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    senha_hash = Column(String)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def criar_token(email: str):
    dados = {"sub": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)

def get_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    erro = HTTPException(status_code=401, detail="token inválido", headers={"WWW-Authenticate": "Bearer"})
    try:
        dados = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = dados.get("sub")
    except jwt.InvalidTokenError:
        raise erro
    usuario = db.query(UsuarioDB).filter(UsuarioDB.email == email).first()
    if usuario is None:
        raise erro
    return usuario

@app.post(
    "/token",
    tags=["Autenticação"],
    summary="Login",
    responses={401: {"description": "Email ou senha incorretos"}},          
)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Cria um token de autenticação para liberar as outras funções.
    Rota pública, não exige login.
    """
    usuario = db.query(UsuarioDB).filter(UsuarioDB.email == form.username).first()
    if usuario is None or not password_hash.verify(form.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="email ou senha incorretos")
    return {"access_token": criar_token(usuario.email), "token_type": "bearer"}

@app.get(
    "/tarefas",
    response_model=list[TarefaSaida],
    tags=["Tarefas"],
    summary="Listar as tarefas",        
)
async def listar_tarefas(db: Session = Depends(get_db)):
    """
    Lista as tarefas existentes no banco.
    Rota pública, não exige login.
    """
    return db.query(TarefaDB).all()

@app.post(
    "/tarefas",
    response_model=TarefaSaida,
    tags=["Tarefas"],
    summary="Criar uma tarefa",
    responses={401: {"description": "Você não está autenticado"}},
)
async def criar_tarefa(tarefa: Tarefa, db: Session = Depends(get_db), usuario: UsuarioDB = Depends(get_usuario_atual)):
    """
    Cria uma tarefa com título, descrição e com um parâmetro de concluída.
    Rota privada, exige login.
    """
    novo = TarefaDB(titulo=tarefa.titulo, desc=tarefa.desc, concluida=tarefa.concluida)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@app.post(
    "/usuarios",
    tags=["Autenticação"],
    summary="Criar um usuário",
    responses={400: {"description": "Email já cadastrado"}},
    )
async def criar_usuario(usuario: Usuario, db: Session = Depends(get_db)):
    """
    Cria um usuário para login, com email e senha.
    Rota pública, não exige login.
    """
    existe = db.query(UsuarioDB).filter(UsuarioDB.email == usuario.email).first()
    if existe is not None:
        raise HTTPException(status_code=400, detail="email já cadastrado")
    novo = UsuarioDB(email=usuario.email, senha_hash=password_hash.hash(usuario.senha))
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"id": novo.id, "email": novo.email}

@app.get(
    "/tarefas/{tarefa_id}",
    response_model=TarefaSaida,
    tags=["Tarefas"],
    summary="Buscar uma tarefa",
    responses={404: {"description": "Tarefa não encontrada"}},
    )
async def buscar_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    """
    Retorna uma tarefa específica pelo id.
    Rota pública, não exige login.
    """
    tarefa = db.get(TarefaDB, tarefa_id)
    if tarefa is None:
        raise HTTPException(status_code=404, detail="essa tarefa não existe")
    return tarefa

@app.put(
    "/tarefas/{tarefa_id}",
    response_model=TarefaSaida,
    tags=["Tarefas"],
    summary="Atualizar uma tarefa",
    responses={401: {"description": "Você não está autenticado"}, 404: {"description": "Essa tarefa não existe"}},
    )
async def atualizar_tarefa(tarefa_id: int, tarefa: Tarefa, db: Session = Depends(get_db), usuario: UsuarioDB = Depends(get_usuario_atual)):
    """
    Atualiza as informações de uma tarefa.
    Rota privada, exige login.
    """
    existente = db.get(TarefaDB, tarefa_id)
    if existente is None:
        raise HTTPException(status_code=404, detail="essa tarefa não existe")
    existente.titulo = tarefa.titulo
    existente.desc = tarefa.desc
    existente.concluida = tarefa.concluida
    db.commit()
    db.refresh(existente)
    return existente

@app.delete(
    "/tarefas/{tarefa_id}",
    tags=["Tarefas"],
    summary="Apagar uma tarefa",
    responses={401: {"description": "Você não está autenticado"}, 404: {"description": "Essa tarefa não existe"}},
    )
async def apagar_tarefa(tarefa_id: int, db: Session = Depends(get_db), usuario: UsuarioDB = Depends(get_usuario_atual)):
    """
    Apaga uma tarefa pelo id.
    Rota privada, exige login.
    """
    tarefa = db.get(TarefaDB, tarefa_id)
    if tarefa is None:
        raise HTTPException(status_code=404, detail="essa tarefa não existe")
    db.delete(tarefa)
    db.commit()
    return {"mensagem": "tarefa apagada"}

