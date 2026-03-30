#Codigo para Criação de tabelas no mysql
import mysql.connector

from configLocal import db_user, db_password, db_name, db_host, db_port

def get_mysql_connection():
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port,
        autocommit=True
    )

###########################################################################################################################################
# Abre a parte abaixo caso o banco na nuvem não tenha a tabela numero_cotacoes. 
# O código abaixo é para criar a tabela, caso ainda não exista.
def criar_tabela_numero_cotacoes(cursor):
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS numero_cotacoes (
                numero_cotacao VARCHAR(30) PRIMARY KEY,
                versao VARCHAR(5),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Tabela 'numero_cotacoes' verificada/criada com sucesso.")
    except mysql.connector.Error as err:
        print(f"❌ Erro ao criar tabela 'numero_cotacoes': {err}")
        raise  # repropaga o erro para quem chamou

###########################################################################################################################################
#CRIA A TABELA cotacoes_armazenadas 
# Cria a tabela cotacoes_armazenadas, caso não exista
def criar_tabela_cotacoes_armazenadas(cursor):
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotacoes_armazenadas (
                numero_cotacao VARCHAR(30),
                versao_cotacao VARCHAR(5),
                premio_total DECIMAL(15,2),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dados_json JSON,
                PRIMARY KEY (numero_cotacao, versao_cotacao)
            );
        """)
        print("✅ Tabela 'cotacoes_armazenadas' verificada/criada com sucesso.")
    except mysql.connector.Error as err:
        print(f"❌ Erro ao criar tabela 'cotacoes_armazenadas': {err}")
        raise

###########################################################################################################################################
#CRIA A TABELA DEPURADOR 
def criar_tabela_depurador(cursor):
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS depurador (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numero_cotacao VARCHAR(20),
                versao_cotacao VARCHAR(10),
                data_criacao DATETIME,
                detalhes_depurador JSON,
                premio_total DECIMAL(18,4),
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Tabela 'depurador' verificada/criada com sucesso.")
    except mysql.connector.Error as err:
        print(f"❌ Erro ao criar tabela 'depurador': {err}")
        raise


###########################################################################################################################################
# CRIA A TABELA DEPURADOR (SOBREPÕE A EXISTENTE)
#def criar_tabela_depurador(cursor):
#    try:
#        cursor.execute("DROP TABLE IF EXISTS depurador;")
#        cursor.execute("""
#            CREATE TABLE depurador (
#                id INT AUTO_INCREMENT PRIMARY KEY,
#                numero_cotacao VARCHAR(20),
#                versao_cotacao VARCHAR(10),
#                data_criacao DATETIME,
#                detalhes_depurador JSON,
#                premio_total DECIMAL(18,4),
#                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#            );
#        """)
#        print("✅ Tabela 'depurador' foi recriada com sucesso.")
#    except mysql.connector.Error as err:
#        print(f"❌ Erro ao recriar tabela 'depurador': {err}")
#        raise

###########################################################################################################################################
# Execução principal 
if __name__ == "__main__":
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        criar_tabela_numero_cotacoes(cursor)
        criar_tabela_cotacoes_armazenadas(cursor)
        criar_tabela_depurador(cursor)

    finally:
        cursor.close()
        conn.close()
        print("🔒 Conexão encerrada.")