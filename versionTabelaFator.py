# versionTabelaFator.py
from flask import Blueprint, render_template
import mysql.connector
from configLocal import db_user, db_password, db_name, db_host, db_port

version_bp = Blueprint("version", __name__)

@version_bp.route("/versao_tabelas")
def versao_tabelas():
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port
    )
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = '{db_name}'
    """)
    tables = cursor.fetchall()

    tabelas_info = []

    for (table_name,) in tables:
        try:
            cursor.execute(f"""
                SELECT NR_TARIFA, data_hora_atualizacao 
                FROM `{table_name}` 
                ORDER BY data_hora_atualizacao DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                tabelas_info.append({
                    "nome": table_name,
                    "nr_tarifa": row[0],
                    "data_atualizacao": row[1]
                })
        except:
            continue

    cursor.close()
    conn.close()

    return render_template("versao_tabelas.html", tabelas=tabelas_info)
