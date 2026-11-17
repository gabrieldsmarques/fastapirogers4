from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)
email = f"teste{uuid.uuid4()}@email.com"

def test_listar_tarefas_200():
    resposta = client.get("/tarefas")
    assert resposta.status_code == 200

def test_tarefa_404():
    resposta = client.get("/tarefas/999999")
    assert resposta.status_code == 404

def test_criar_usuario_400():
    client.post("/usuarios", json={"email": email, "senha": "123"})
    resposta = client.post("/usuarios", json={"email":email, "senha": "123"})
    assert resposta.status_code == 400

def test_criar_usuario_200():
    novo_email = f"teste{uuid.uuid4()}@email.com"
    resposta = client.post("/usuarios", json={"email": novo_email, "senha": "123"})
    assert resposta.status_code == 200

def test_login_errado_401():
    resposta = client.post("/token", data={"username": "testezao", "password": "123"})
    assert resposta.status_code == 401

def test_login_200():
    novo_email = f"teste{uuid.uuid4()}@email.com"
    client.post("/usuarios", json={"email": novo_email, "senha": "123"})
    resposta = client.post("/token", data={"username": novo_email, "password": "123"})
    assert resposta.status_code == 200
    assert "access_token" in resposta.json()

def test_token_invalido_401():
    headers = {"Authorization": "Bearer rx580 eu te amo"}
    resposta = client.post("/tarefas", json={"titulo": "x", "desc": "y"}, headers=headers)
    assert resposta.status_code == 401

def test_criar_tarefa_401():
    resposta = client.post("/tarefas", json={"titulo": "berimbas", "desc": "flombois"})
    assert resposta.status_code == 401

def test_criar_tarefa_com_token_200():
    novo_email = f"teste{uuid.uuid4()}@email.com"
    client.post("/usuarios", json={"email": novo_email, "senha": "123"})
    resposta_login = client.post("/token", data={"username": novo_email, "password": "123"})
    token = resposta_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resposta = client.post("/tarefas", json={"titulo": "testesbrabos", "desc": "seco seco seco"}, headers=headers)
    assert resposta.status_code == 200

def test_apagar_tarefa():
    novo_email = f"teste{uuid.uuid4()}@email.com"
    client.post("/usuarios", json={"email": novo_email, "senha": "123"})
    resposta_login = client.post("/token", data={"username": novo_email, "password": "123"})
    token = resposta_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    criada = client.post("/tarefas", json={"titulo": "x", "desc": "y"}, headers=headers)
    tarefa_id = criada.json()["id"]
    resposta = client.delete(f"/tarefas/{tarefa_id}", headers=headers)
    assert resposta.status_code == 200
    busca = client.get(f"/tarefas/{tarefa_id}")
    assert busca.status_code == 200