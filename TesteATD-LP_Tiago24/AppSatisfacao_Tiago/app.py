from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import date, datetime
import sqlite3
import csv
import io
import os
from calendar import monthrange

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

DATABASE = "database.db"
ADMIN_URL = "/Admin_Registos2026"

# Dicionário de dias da semana em português
DIAS_SEMANA = {
    0: "Segunda",
    1: "Terça",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sábado",
    6: "Domingo"
}

def get_db():
    """Conectar à base de dados com row factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_dia_semana(data_str):
    """Obter nome do dia da semana"""
    data_obj = datetime.strptime(data_str, "%Y-%m-%d")
    return DIAS_SEMANA[data_obj.weekday()]

@app.route("/")
def index():
    """Página inicial para votação de satisfação"""
    return render_template("Index.html")

@app.route("/votar", methods=["POST"])
def votar():
    """Registar um voto de satisfação"""
    try:
        data = request.get_json()
        grau = data.get("grau")
        
        if grau not in ["Muito satisfeito", "Satisfeito", "Insatisfeito"]:
            return jsonify({"erro": "Grau inválido"}), 400
        
        hoje = date.today().strftime("%Y-%m-%d")
        dia_semana = get_dia_semana(hoje)
        agora = datetime.now().strftime("%H:%M:%S")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO satisfacao (grau, data, dia_semana, hora)
            VALUES (?, ?, ?, ?)
        """, (grau, hoje, dia_semana, agora))
        conn.commit()
        conn.close()
        
        return jsonify({"sucesso": True, "mensagem": "Voto registado com sucesso! Obrigado."})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route(ADMIN_URL, methods=["GET", "POST"])
def login_admin():
    """Login para administrador"""
    if request.method == "POST":
        senha = request.form.get("senha")
        # ATENÇÃO: Usar variável de ambiente em produção!
        if senha == "admin1711":
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("admin_login.html", erro="Senha incorreta")
    
    return render_template("admin_login.html")

@app.route(ADMIN_URL + "/logout")
def logout_admin():
    """Fazer logout do admin"""
    session.clear()
    return redirect(url_for("index"))

@app.route(ADMIN_URL + "/dashboard")
def dashboard():
    """Dashboard com estatísticas"""
    if not session.get("admin"):
        return redirect(url_for("login_admin"))

    conn = get_db()
    cursor = conn.cursor()
    
    # Data selecionada (padrão: hoje)
    data_selecionada = request.args.get("data", date.today().strftime("%Y-%m-%d"))
    dia_semana_sel = get_dia_semana(data_selecionada)
    
    # Estatísticas do dia selecionado
    cursor.execute("""
        SELECT grau, COUNT(*) as total
        FROM satisfacao
        WHERE data = ?
        GROUP BY grau
    """, (data_selecionada,))
    stats_raw = cursor.fetchall()
    stats = [[r['grau'], r['total']] for r in stats_raw]
    
    # Cálculo de total e percentagens
    total_dia = sum([r['total'] for r in stats_raw])
    percentagens = {}
    if total_dia > 0:
        for r in stats_raw:
            percentagens[r['grau']] = round((r['total'] / total_dia) * 100, 1)
    
    # Histórico do dia selecionado (com paginação)
    pagina = request.args.get("pagina", 1, type=int)
    registos_por_pagina = 20
    offset = (pagina - 1) * registos_por_pagina
    
    cursor.execute("""
        SELECT id, grau, data, dia_semana, hora
        FROM satisfacao
        WHERE data = ?
        ORDER BY hora DESC
        LIMIT ? OFFSET ?
    """, (data_selecionada, registos_por_pagina, offset))
    historico_raw = cursor.fetchall()
    historico = []
    for r in historico_raw:
        historico.append({
            "id": r['id'],
            "grau": r['grau'],
            "data": r['data'],
            "dia_semana": r['dia_semana'],
            "hora": r['hora']
        })
    
    # Total de registos do dia para paginação
    cursor.execute("SELECT COUNT(*) as total FROM satisfacao WHERE data = ?", (data_selecionada,))
    total_registos = cursor.fetchone()['total']
    total_paginas = (total_registos + registos_por_pagina - 1) // registos_por_pagina
    
    # Evolução últimos 7 dias
    cursor.execute("""
        SELECT data, COUNT(*) as total
        FROM satisfacao
        GROUP BY data
        ORDER BY data DESC
        LIMIT 7
    """)
    evolucao_raw = cursor.fetchall()
    evolucao = [[r['data'], r['total']] for r in evolucao_raw]
    evolucao.reverse()  # Ordenar do dia mais antigo para o mais recente
    
    # Estatísticas globais
    cursor.execute("""
        SELECT grau, COUNT(*) as total
        FROM satisfacao
        GROUP BY grau
    """)
    stats_globais_raw = cursor.fetchall()
    stats_globais = {}
    total_global = 0
    for r in stats_globais_raw:
        stats_globais[r['grau']] = r['total']
        total_global += r['total']
    
    # Calcular percentagens globais
    percentagens_globais = {}
    if total_global > 0:
        for grau in ["Muito satisfeito", "Satisfeito", "Insatisfeito"]:
            count = stats_globais.get(grau, 0)
            percentagens_globais[grau] = round((count / total_global) * 100, 1)

    conn.close()

    return render_template(
        "admin__dashboard.html",
        stats=stats,
        percentagens=percentagens,
        total_dia=total_dia,
        historico=historico,
        evolucao=evolucao,
        data_selecionada=data_selecionada,
        dia_semana_sel=dia_semana_sel,
        pagina=pagina,
        total_paginas=total_paginas,
        stats_globais=stats_globais,
        percentagens_globais=percentagens_globais,
        total_global=total_global
    )

@app.route(ADMIN_URL + "/export/csv")
def export_csv():
    """Exportar dados em CSV"""
    if not session.get("admin"):
        return redirect(url_for("login_admin"))
    
    data_filtro = request.args.get("data", None)
    
    conn = get_db()
    cursor = conn.cursor()
    
    if data_filtro:
        cursor.execute("""
            SELECT id, grau, data, dia_semana, hora 
            FROM satisfacao 
            WHERE data = ?
            ORDER BY hora DESC
        """, (data_filtro,))
    else:
        cursor.execute("""
            SELECT id, grau, data, dia_semana, hora 
            FROM satisfacao 
            ORDER BY data DESC, hora DESC
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Criar CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Grau de Satisfação", "Data", "Dia da Semana", "Hora"])
    for row in rows:
        writer.writerow([row['id'], row['grau'], row['data'], row['dia_semana'], row['hora']])
    
    # Preparar resposta
    output.seek(0)
    nome_ficheiro = f"satisfacao_{data_filtro or 'completo'}.csv"
    return output.getvalue(), 200, {
        'Content-Disposition': f'attachment; filename={nome_ficheiro}',
        'Content-type': 'text/csv; charset=utf-8'
    }

@app.route(ADMIN_URL + "/export/txt")
def export_txt():
    """Exportar dados em TXT"""
    if not session.get("admin"):
        return redirect(url_for("login_admin"))
    
    data_filtro = request.args.get("data", None)
    
    conn = get_db()
    cursor = conn.cursor()
    
    if data_filtro:
        cursor.execute("""
            SELECT id, grau, data, dia_semana, hora 
            FROM satisfacao 
            WHERE data = ?
            ORDER BY hora DESC
        """, (data_filtro,))
    else:
        cursor.execute("""
            SELECT id, grau, data, dia_semana, hora 
            FROM satisfacao 
            ORDER BY data DESC, hora DESC
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Criar TXT formatado
    output = "RELATÓRIO DE SATISFAÇÃO\n"
    output += "=" * 70 + "\n\n"
    
    if data_filtro:
        output += f"Data: {data_filtro}\n\n"
    
    output += f"Total de registos: {len(rows)}\n"
    output += "-" * 70 + "\n\n"
    
    for row in rows:
        output += f"ID: {row['id']:<5} | {row['grau']:<20} | {row['data']} ({row['dia_semana']:<8}) | {row['hora']}\n"
    
    output += "\n" + "=" * 70
    
    nome_ficheiro = f"satisfacao_{data_filtro or 'completo'}.txt"
    return output, 200, {
        'Content-Disposition': f'attachment; filename={nome_ficheiro}',
        'Content-type': 'text/plain; charset=utf-8'
    }

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
