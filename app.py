"""
Sistema de Agendamento Veterinário — Backend
Python + Flask + mysql-connector-python
"""

import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

import db

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", "troque-essa-chave")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

jwt = JWTManager(app)


# ─────────────────────────────────────────────
#  CORS — permite o frontend React acessar a API
# ─────────────────────────────────────────────

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    return jsonify({}), 200


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def perfil_requerido(*perfis):
    from functools import wraps
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            perfil = get_jwt().get("perfil")
            if perfil not in perfis:
                return jsonify(erro="Acesso negado"), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

@app.post("/auth/cadastro")
def cadastro():
    dados = request.get_json()
    campos = ("nome", "email", "senha", "perfil")
    if not all(dados.get(c) for c in campos):
        return jsonify(erro="Campos obrigatórios: nome, email, senha, perfil"), 400

    if dados["perfil"] not in ("tutor", "veterinario"):
        return jsonify(erro="perfil deve ser 'tutor' ou 'veterinario'"), 400

    usuario_id = db.criar_usuario(
        nome=dados["nome"],
        email=dados["email"],
        senha=dados["senha"],
        perfil=dados["perfil"],
        telefone=dados.get("telefone"),
    )
    if usuario_id is None:
        return jsonify(erro="E-mail já cadastrado"), 409

    return jsonify(mensagem="Usuário criado", id=usuario_id), 201


@app.post("/auth/login")
def login():
    dados = request.get_json()
    usuario = db.autenticar(dados.get("email"), dados.get("senha"))
    if not usuario:
        return jsonify(erro="Credenciais inválidas"), 401

    token = create_access_token(
        identity=str(usuario["id"]),
        additional_claims={"perfil": usuario["perfil"]}
    )
    return jsonify(access_token=token, perfil=usuario["perfil"], nome=usuario["nome"])


# ─────────────────────────────────────────────
#  ENDPOINTS COMPARTILHADOS (usados pelo frontend do tutor)
# ─────────────────────────────────────────────

@app.get("/veterinarios")
@jwt_required()
def listar_veterinarios():
    """Lista todos os veterinários cadastrados — usado pelo tutor ao agendar."""
    return jsonify(db.listar_veterinarios())


@app.get("/veterinarios/<int:vet_id>/disponibilidade")
@jwt_required()
def disponibilidade_veterinario(vet_id):
    """
    Retorna horários livres de um veterinário em uma data específica.
    Query param: ?data=YYYY-MM-DD
    """
    data = request.args.get("data")
    if not data:
        return jsonify(erro="Parâmetro 'data' é obrigatório"), 400

    horarios = db.horarios_disponiveis(vet_id, data)
    return jsonify(horarios)


# ─────────────────────────────────────────────
#  TUTOR — Pets
# ─────────────────────────────────────────────

@app.get("/tutor/pets")
@perfil_requerido("tutor")
def listar_pets():
    tutor_id = int(get_jwt_identity())
    return jsonify(db.listar_pets(tutor_id))


@app.post("/tutor/pets")
@perfil_requerido("tutor")
def criar_pet():
    tutor_id = int(get_jwt_identity())
    dados = request.get_json()
    if not dados.get("nome") or not dados.get("especie"):
        return jsonify(erro="nome e especie são obrigatórios"), 400

    pet_id = db.criar_pet(tutor_id, dados)
    return jsonify(mensagem="Pet criado", id=pet_id), 201


@app.put("/tutor/pets/<int:pet_id>")
@perfil_requerido("tutor")
def atualizar_pet(pet_id):
    tutor_id = int(get_jwt_identity())
    dados = request.get_json()
    ok = db.atualizar_pet(pet_id, tutor_id, dados)
    if not ok:
        return jsonify(erro="Pet não encontrado"), 404
    return jsonify(mensagem="Pet atualizado")


@app.delete("/tutor/pets/<int:pet_id>")
@perfil_requerido("tutor")
def excluir_pet(pet_id):
    tutor_id = int(get_jwt_identity())
    ok = db.excluir_pet(pet_id, tutor_id)
    if not ok:
        return jsonify(erro="Pet não encontrado"), 404
    return jsonify(mensagem="Pet removido")


# ─────────────────────────────────────────────
#  TUTOR — Agendamentos
# ─────────────────────────────────────────────

@app.get("/tutor/agendamentos")
@perfil_requerido("tutor")
def meus_agendamentos():
    tutor_id = int(get_jwt_identity())
    filtro = request.args.get("filtro", "todos")
    return jsonify(db.agendamentos_tutor(tutor_id, filtro))


@app.post("/tutor/agendamentos")
@perfil_requerido("tutor")
def novo_agendamento():
    tutor_id = int(get_jwt_identity())
    dados = request.get_json()
    campos = ("veterinario_id", "pet_id", "data_hora")
    if not all(dados.get(c) for c in campos):
        return jsonify(erro=f"Campos obrigatórios: {', '.join(campos)}"), 400

    resultado = db.criar_agendamento(tutor_id, dados)
    if "erro" in resultado:
        return jsonify(resultado), 409

    return jsonify(resultado), 201


@app.put("/tutor/agendamentos/<int:ag_id>/cancelar")
@perfil_requerido("tutor")
def cancelar_agendamento(ag_id):
    tutor_id = int(get_jwt_identity())
    ok = db.atualizar_status_agendamento(ag_id, "cancelado", tutor_id=tutor_id)
    if not ok:
        return jsonify(erro="Agendamento não encontrado"), 404
    return jsonify(mensagem="Agendamento cancelado")


@app.put("/tutor/agendamentos/<int:ag_id>/remarcar")
@perfil_requerido("tutor")
def remarcar_agendamento(ag_id):
    tutor_id = int(get_jwt_identity())
    dados = request.get_json()
    if not dados.get("nova_data_hora"):
        return jsonify(erro="nova_data_hora é obrigatório"), 400

    resultado = db.remarcar_agendamento(ag_id, tutor_id, dados["nova_data_hora"])
    if "erro" in resultado:
        return jsonify(resultado), 409
    return jsonify(resultado)


# ─────────────────────────────────────────────
#  VETERINÁRIO — Agenda
# ─────────────────────────────────────────────

@app.get("/vet/agenda")
@perfil_requerido("veterinario")
def agenda_completa():
    vet_id = int(get_jwt_identity())
    filtro = request.args.get("filtro", "todos")
    return jsonify(db.agenda_veterinario(vet_id, filtro))


@app.post("/vet/agendamentos")
@perfil_requerido("veterinario")
def vet_criar_agendamento():
    vet_id = int(get_jwt_identity())
    dados = request.get_json()
    dados["veterinario_id"] = vet_id
    campos = ("tutor_id", "pet_id", "data_hora")
    if not all(dados.get(c) for c in campos):
        return jsonify(erro=f"Campos obrigatórios: {', '.join(campos)}"), 400

    resultado = db.criar_agendamento(dados["tutor_id"], dados)
    if "erro" in resultado:
        return jsonify(resultado), 409
    return jsonify(resultado), 201


@app.get("/vet/todos-pets")
@perfil_requerido("veterinario")
def todos_pets_para_vet():
    """
    Lista todos os pets de todos os tutores.
    Usado pelo veterinário ao criar um agendamento manualmente.
    """
    return jsonify(db.listar_todos_pets())


@app.get("/vet/disponibilidade")
@perfil_requerido("veterinario")
def minha_disponibilidade():
    """
    Retorna os horários livres do próprio veterinário em uma data.
    Query param: ?data=YYYY-MM-DD
    """
    vet_id = int(get_jwt_identity())
    data = request.args.get("data")
    if not data:
        return jsonify(erro="Parâmetro 'data' é obrigatório"), 400

    horarios = db.horarios_disponiveis(vet_id, data)
    return jsonify(horarios)


# ─────────────────────────────────────────────
#  VETERINÁRIO — Pacientes / Histórico
# ─────────────────────────────────────────────

@app.get("/vet/pacientes")
@perfil_requerido("veterinario")
def gestao_pacientes():
    vet_id = int(get_jwt_identity())
    return jsonify(db.pacientes_veterinario(vet_id))


@app.get("/vet/pacientes/<int:pet_id>/historico")
@perfil_requerido("veterinario")
def historico_pet(pet_id):
    return jsonify(db.historico_atendimentos(pet_id))


@app.post("/vet/agendamentos/<int:ag_id>/historico")
@perfil_requerido("veterinario")
def registrar_historico(ag_id):
    dados = request.get_json()
    ok = db.salvar_historico(ag_id, dados)
    if not ok:
        return jsonify(erro="Agendamento não encontrado ou já possui histórico"), 409
    return jsonify(mensagem="Histórico registrado"), 201


# ─────────────────────────────────────────────
#  VETERINÁRIO — Configurações de Agenda
# ─────────────────────────────────────────────

@app.get("/vet/horarios")
@perfil_requerido("veterinario")
def listar_horarios():
    vet_id = int(get_jwt_identity())
    return jsonify(db.horarios_padrao(vet_id))


@app.post("/vet/horarios")
@perfil_requerido("veterinario")
def definir_horario():
    vet_id = int(get_jwt_identity())
    dados = request.get_json()
    campos = ("dia_semana", "hora_inicio", "hora_fim")
    if not all(dados.get(c) is not None for c in campos):
        return jsonify(erro=f"Campos obrigatórios: {', '.join(campos)}"), 400

    horario_id = db.salvar_horario_padrao(vet_id, dados)
    return jsonify(mensagem="Horário definido", id=horario_id), 201


@app.delete("/vet/horarios/<int:horario_id>")
@perfil_requerido("veterinario")
def remover_horario(horario_id):
    vet_id = int(get_jwt_identity())
    ok = db.remover_horario_padrao(horario_id, vet_id)
    if not ok:
        return jsonify(erro="Horário não encontrado"), 404
    return jsonify(mensagem="Horário removido")


@app.get("/vet/bloqueios")
@perfil_requerido("veterinario")
def listar_bloqueios():
    vet_id = int(get_jwt_identity())
    return jsonify(db.bloqueios_agenda(vet_id))


@app.post("/vet/bloqueios")
@perfil_requerido("veterinario")
def criar_bloqueio():
    vet_id = int(get_jwt_identity())
    dados = request.get_json()
    if not dados.get("data_inicio") or not dados.get("data_fim"):
        return jsonify(erro="data_inicio e data_fim são obrigatórios"), 400

    bloqueio_id = db.criar_bloqueio(vet_id, dados)
    return jsonify(mensagem="Bloqueio criado", id=bloqueio_id), 201


@app.delete("/vet/bloqueios/<int:bloqueio_id>")
@perfil_requerido("veterinario")
def remover_bloqueio(bloqueio_id):
    vet_id = int(get_jwt_identity())
    ok = db.remover_bloqueio(bloqueio_id, vet_id)
    if not ok:
        return jsonify(erro="Bloqueio não encontrado"), 404
    return jsonify(mensagem="Bloqueio removido")


# ─────────────────────────────────────────────
#  Ponto de entrada
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
