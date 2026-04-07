"""
db.py — Camada de acesso ao banco de dados (MySQL)
"""

import os
from datetime import datetime, timedelta

import bcrypt
import mysql.connector
from mysql.connector import IntegrityError


# ─────────────────────────────────────────────
#  Conexão
# ─────────────────────────────────────────────

def _conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "vet_agendamento"),
        charset="utf8mb4",
        autocommit=False,
    )


def _executar(sql, params=(), fetchone=False, fetchall=False, lastrowid=False):
    conn = _conectar()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
        if lastrowid:
            conn.commit()
            return cur.lastrowid
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────
#  Usuários / Auth
# ─────────────────────────────────────────────

def criar_usuario(nome, email, senha, perfil, telefone=None):
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    try:
        return _executar(
            """INSERT INTO usuarios (nome, email, senha_hash, perfil, telefone)
               VALUES (%s, %s, %s, %s, %s)""",
            (nome, email, senha_hash, perfil, telefone),
            lastrowid=True,
        )
    except IntegrityError:
        return None


def autenticar(email, senha):
    usuario = _executar(
        "SELECT id, nome, email, senha_hash, perfil FROM usuarios WHERE email = %s",
        (email,),
        fetchone=True,
    )
    if not usuario:
        return None
    if not bcrypt.checkpw(senha.encode(), usuario["senha_hash"].encode()):
        return None
    return usuario


def listar_veterinarios():
    """Retorna todos os usuários com perfil veterinário."""
    return _executar(
        "SELECT id, nome, email, telefone FROM usuarios WHERE perfil = 'veterinario' ORDER BY nome",
        fetchall=True,
    )


# ─────────────────────────────────────────────
#  Pets
# ─────────────────────────────────────────────

def listar_pets(tutor_id):
    return _executar(
        "SELECT * FROM pets WHERE tutor_id = %s ORDER BY nome",
        (tutor_id,),
        fetchall=True,
    )


def listar_todos_pets():
    """Retorna todos os pets com nome do tutor — usado pelo veterinário."""
    return _executar(
        """SELECT p.id, p.nome, p.especie, p.raca, p.sexo,
                  t.id AS tutor_id, t.nome AS tutor_nome, t.email AS tutor_email
           FROM pets p
           JOIN usuarios t ON t.id = p.tutor_id
           ORDER BY p.nome""",
        fetchall=True,
    )


def criar_pet(tutor_id, dados):
    return _executar(
        """INSERT INTO pets (tutor_id, nome, especie, raca, data_nasc, sexo)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (
            tutor_id,
            dados["nome"],
            dados["especie"],
            dados.get("raca"),
            dados.get("data_nasc"),
            dados.get("sexo", "desconhecido"),
        ),
        lastrowid=True,
    )


def atualizar_pet(pet_id, tutor_id, dados):
    campos = []
    valores = []
    for col in ("nome", "especie", "raca", "data_nasc", "sexo"):
        if col in dados:
            campos.append(f"{col} = %s")
            valores.append(dados[col])
    if not campos:
        return False
    valores += [pet_id, tutor_id]
    rows = _executar(
        f"UPDATE pets SET {', '.join(campos)} WHERE id = %s AND tutor_id = %s",
        tuple(valores),
    )
    return rows > 0


def excluir_pet(pet_id, tutor_id):
    rows = _executar(
        "DELETE FROM pets WHERE id = %s AND tutor_id = %s",
        (pet_id, tutor_id),
    )
    return rows > 0


# ─────────────────────────────────────────────
#  Disponibilidade
# ─────────────────────────────────────────────

def horarios_disponiveis(vet_id, data_str):
    """
    Calcula os horários livres de um veterinário em uma data.
    Retorna lista de strings no formato HH:MM.
    """
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d")
    except ValueError:
        return []

    dia_semana = data.weekday()  # 0=Seg … 6=Dom (Python)
    # Converte para o padrão do banco: 0=Dom … 6=Sáb
    dia_banco = (dia_semana + 1) % 7

    horarios_padrao = _executar(
        """SELECT hora_inicio, hora_fim, duracao_consulta_min
           FROM horarios_padrao
           WHERE veterinario_id = %s AND dia_semana = %s""",
        (vet_id, dia_banco),
        fetchall=True,
    )

    if not horarios_padrao:
        return []

    # Agendamentos já existentes no dia
    agendamentos_dia = _executar(
        """SELECT data_hora, duracao_min FROM agendamentos
           WHERE veterinario_id = %s
             AND DATE(data_hora) = %s
             AND status NOT IN ('cancelado', 'remarcado')""",
        (vet_id, data_str),
        fetchall=True,
    )

    # Bloqueios no dia
    bloqueios = _executar(
        """SELECT data_inicio, data_fim FROM bloqueios_agenda
           WHERE veterinario_id = %s
             AND DATE(data_inicio) <= %s AND DATE(data_fim) >= %s""",
        (vet_id, data_str, data_str),
        fetchall=True,
    )

    slots_livres = []

    for hp in horarios_padrao:
        duracao = hp["duracao_consulta_min"]
        inicio = datetime.combine(data.date(), hp["hora_inicio"])
        fim = datetime.combine(data.date(), hp["hora_fim"])

        atual = inicio
        while atual + timedelta(minutes=duracao) <= fim:
            slot_fim = atual + timedelta(minutes=duracao)

            # Verifica conflito com agendamentos
            ocupado = False
            for ag in agendamentos_dia:
                ag_inicio = ag["data_hora"]
                ag_fim = ag_inicio + timedelta(minutes=ag["duracao_min"])
                if atual < ag_fim and slot_fim > ag_inicio:
                    ocupado = True
                    break

            # Verifica conflito com bloqueios
            if not ocupado:
                for bl in bloqueios:
                    if atual < bl["data_fim"] and slot_fim > bl["data_inicio"]:
                        ocupado = True
                        break

            if not ocupado:
                slots_livres.append(atual.strftime("%H:%M"))

            atual += timedelta(minutes=duracao)

    return slots_livres


# ─────────────────────────────────────────────
#  Agendamentos
# ─────────────────────────────────────────────

def _filtro_data(filtro):
    hoje_inicio = datetime.now().strftime("%Y-%m-%d 00:00:00")
    hoje_fim = datetime.now().strftime("%Y-%m-%d 23:59:59")

    if filtro == "passados":
        return f"AND a.data_hora < '{hoje_inicio}'"
    if filtro == "atuais":
        return f"AND a.data_hora BETWEEN '{hoje_inicio}' AND '{hoje_fim}'"
    if filtro == "futuros":
        return f"AND a.data_hora > '{hoje_fim}'"
    return ""


def agendamentos_tutor(tutor_id, filtro="todos"):
    where_data = _filtro_data(filtro)
    return _executar(
        f"""SELECT a.id, a.data_hora, a.duracao_min, a.status, a.motivo_consulta,
                   p.nome AS pet_nome, v.nome AS veterinario_nome
            FROM agendamentos a
            JOIN pets     p ON p.id = a.pet_id
            JOIN usuarios v ON v.id = a.veterinario_id
            WHERE a.tutor_id = %s {where_data}
            ORDER BY a.data_hora DESC""",
        (tutor_id,),
        fetchall=True,
    )


def agenda_veterinario(vet_id, filtro="todos"):
    where_data = _filtro_data(filtro)
    return _executar(
        f"""SELECT a.id, a.data_hora, a.duracao_min, a.status, a.motivo_consulta,
                   t.nome AS tutor_nome, p.nome AS pet_nome, p.especie
            FROM agendamentos a
            JOIN usuarios t ON t.id = a.tutor_id
            JOIN pets     p ON p.id = a.pet_id
            WHERE a.veterinario_id = %s {where_data}
            ORDER BY a.data_hora""",
        (vet_id,),
        fetchall=True,
    )


def _verificar_disponibilidade(vet_id, data_hora_str, duracao_min, excluir_id=None):
    dt = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M:%S")
    dt_fim = dt + timedelta(minutes=duracao_min)
    dt_fim_str = dt_fim.strftime("%Y-%m-%d %H:%M:%S")

    bloqueio = _executar(
        """SELECT id FROM bloqueios_agenda
           WHERE veterinario_id = %s
             AND data_inicio < %s AND data_fim > %s""",
        (vet_id, dt_fim_str, data_hora_str),
        fetchone=True,
    )
    if bloqueio:
        return False, "Horário bloqueado pelo veterinário"

    excluir_clause = f"AND id <> {int(excluir_id)}" if excluir_id else ""
    colisao = _executar(
        f"""SELECT id FROM agendamentos
            WHERE veterinario_id = %s
              AND status NOT IN ('cancelado','remarcado')
              AND data_hora < %s
              AND DATE_ADD(data_hora, INTERVAL duracao_min MINUTE) > %s
              {excluir_clause}""",
        (vet_id, dt_fim_str, data_hora_str),
        fetchone=True,
    )
    if colisao:
        return False, "Horário já ocupado"

    return True, None


def criar_agendamento(tutor_id, dados):
    vet_id = dados["veterinario_id"]
    duracao = dados.get("duracao_min", 30)
    data_hora = dados["data_hora"]

    ok, motivo = _verificar_disponibilidade(vet_id, data_hora, duracao)
    if not ok:
        return {"erro": motivo}

    ag_id = _executar(
        """INSERT INTO agendamentos
               (tutor_id, veterinario_id, pet_id, data_hora, duracao_min, motivo_consulta)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (tutor_id, vet_id, dados["pet_id"], data_hora, duracao, dados.get("motivo_consulta")),
        lastrowid=True,
    )
    return {"mensagem": "Agendamento criado", "id": ag_id}


def atualizar_status_agendamento(ag_id, novo_status, tutor_id=None, vet_id=None):
    if tutor_id:
        rows = _executar(
            "UPDATE agendamentos SET status = %s WHERE id = %s AND tutor_id = %s",
            (novo_status, ag_id, tutor_id),
        )
    else:
        rows = _executar(
            "UPDATE agendamentos SET status = %s WHERE id = %s AND veterinario_id = %s",
            (novo_status, ag_id, vet_id),
        )
    return rows > 0


def remarcar_agendamento(ag_id, tutor_id, nova_data_hora):
    ag = _executar(
        "SELECT veterinario_id, duracao_min FROM agendamentos WHERE id = %s AND tutor_id = %s",
        (ag_id, tutor_id),
        fetchone=True,
    )
    if not ag:
        return {"erro": "Agendamento não encontrado"}

    ok, motivo = _verificar_disponibilidade(
        ag["veterinario_id"], nova_data_hora, ag["duracao_min"], excluir_id=ag_id
    )
    if not ok:
        return {"erro": motivo}

    _executar(
        "UPDATE agendamentos SET data_hora = %s, status = 'remarcado' WHERE id = %s",
        (nova_data_hora, ag_id),
    )
    return {"mensagem": "Agendamento remarcado"}


# ─────────────────────────────────────────────
#  Pacientes / Histórico
# ─────────────────────────────────────────────

def pacientes_veterinario(vet_id):
    return _executar(
        """SELECT DISTINCT p.id, p.nome, p.especie, p.raca, t.nome AS tutor_nome, t.email
           FROM agendamentos a
           JOIN pets     p ON p.id = a.pet_id
           JOIN usuarios t ON t.id = a.tutor_id
           WHERE a.veterinario_id = %s
           ORDER BY p.nome""",
        (vet_id,),
        fetchall=True,
    )


def historico_atendimentos(pet_id):
    return _executar(
        """SELECT ha.*, a.data_hora, a.motivo_consulta, v.nome AS veterinario_nome
           FROM historico_atendimentos ha
           JOIN agendamentos a ON a.id = ha.agendamento_id
           JOIN usuarios     v ON v.id = a.veterinario_id
           WHERE a.pet_id = %s
           ORDER BY a.data_hora DESC""",
        (pet_id,),
        fetchall=True,
    )


def salvar_historico(ag_id, dados):
    try:
        _executar(
            """INSERT INTO historico_atendimentos
                   (agendamento_id, diagnostico, prescricao, observacoes, peso_kg)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                ag_id,
                dados.get("diagnostico"),
                dados.get("prescricao"),
                dados.get("observacoes"),
                dados.get("peso_kg"),
            ),
            lastrowid=True,
        )
        _executar(
            "UPDATE agendamentos SET status = 'concluido' WHERE id = %s",
            (ag_id,),
        )
        return True
    except IntegrityError:
        return False


# ─────────────────────────────────────────────
#  Horários e Bloqueios
# ─────────────────────────────────────────────

def horarios_padrao(vet_id):
    return _executar(
        "SELECT * FROM horarios_padrao WHERE veterinario_id = %s ORDER BY dia_semana, hora_inicio",
        (vet_id,),
        fetchall=True,
    )


def salvar_horario_padrao(vet_id, dados):
    return _executar(
        """INSERT INTO horarios_padrao
               (veterinario_id, dia_semana, hora_inicio, hora_fim, duracao_consulta_min)
           VALUES (%s, %s, %s, %s, %s)""",
        (
            vet_id,
            dados["dia_semana"],
            dados["hora_inicio"],
            dados["hora_fim"],
            dados.get("duracao_consulta_min", 30),
        ),
        lastrowid=True,
    )


def remover_horario_padrao(horario_id, vet_id):
    rows = _executar(
        "DELETE FROM horarios_padrao WHERE id = %s AND veterinario_id = %s",
        (horario_id, vet_id),
    )
    return rows > 0


def bloqueios_agenda(vet_id):
    return _executar(
        "SELECT * FROM bloqueios_agenda WHERE veterinario_id = %s ORDER BY data_inicio",
        (vet_id,),
        fetchall=True,
    )


def criar_bloqueio(vet_id, dados):
    return _executar(
        """INSERT INTO bloqueios_agenda (veterinario_id, data_inicio, data_fim, motivo)
           VALUES (%s, %s, %s, %s)""",
        (vet_id, dados["data_inicio"], dados["data_fim"], dados.get("motivo")),
        lastrowid=True,
    )


def remover_bloqueio(bloqueio_id, vet_id):
    rows = _executar(
        "DELETE FROM bloqueios_agenda WHERE id = %s AND veterinario_id = %s",
        (bloqueio_id, vet_id),
    )
    return rows > 0
