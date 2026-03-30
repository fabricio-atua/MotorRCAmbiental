from datetime import datetime
import mysql.connector
from configLocal import db_user, db_password, db_name, db_host, db_port

def get_mysql_connection():
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port
    )

def gerar_nova_cotacao():
    conn = get_mysql_connection()
    conn.start_transaction()  # inicia transação
    cursor = conn.cursor()

    ano_atual = datetime.now().year
    cursor.execute(f"""
        SELECT numero_cotacao 
        FROM numero_cotacoes 
        WHERE numero_cotacao LIKE '{ano_atual}%'
        ORDER BY numero_cotacao DESC 
        LIMIT 1
        FOR UPDATE;
    """)
    row = cursor.fetchone()

    if row:
        ultima_seq = int(row[0][4:])  # pega parte numérica após o ano
        nova_seq = ultima_seq + 1
    else:
        nova_seq = 1

    numero_cotacao = f"{ano_atual}{str(nova_seq).zfill(4)}"
    versao = "01"

    cursor.execute("""
        INSERT INTO numero_cotacoes (numero_cotacao, versao)
        VALUES (%s, %s)
    """, (numero_cotacao, versao))

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "numero_cotacao": numero_cotacao,
        "versao": versao,
        "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
