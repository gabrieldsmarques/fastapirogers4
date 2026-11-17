# Trabalho: To do list com fastapi
# Nome: Gabriel da Silva Marques

para rodar (precisa de uv instalado): 

uv sync

uv run alembic upgrade head

uv run fastapi dev

depois só acessar o localhost:8000/docs

para criar um usuário, você precisa ir no localhost:8000/docs e ir no POST /usuarios, lá você precisa preencher só o email e senha da conta, feito isso é só executar.

agora pra testar o login, ainda no docs é só clicar no Authorize (botão com cadeado verde escrito authorize, canto superior direito) e preencher o username e password no formulário (username é o email mesmo). Feito isso é só clicar no authorize dentro do formulário e você vai estar logado.

Estando logado você pode executar alterações, como criar e deletar tarefas, se não estiver logado você ainda pode executar leituras


## Testes

os testes ficam no arquivo test_main.py. Pra rodar:

uv run pytest

eles verificam se o listar tarefas funciona, se buscar uma tarefa inexistente retorna 404 e se CRUD nas tarefas sem autenticação é bloqueado