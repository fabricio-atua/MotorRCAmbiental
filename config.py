import mysql.connector
from mysql.connector import errorcode

from dotenv import load_dotenv
load_dotenv()

import os

db_user = os.getenv("MYSQLUSER")
db_password = os.getenv("MYSQLPASSWORD")
db_name = os.getenv("MYSQLDATABASE")
db_host = os.getenv("MYSQLHOST")
db_port = int(os.getenv("MYSQLPORT", 3306))


try:
    # Estabelecendo a conexão
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port
    )
    
    if connection.is_connected():
        print("Conexão ao banco de dados realizada com sucesso!")
        # Exibe informações da conexão
        db_info = connection.get_server_info()
        print(f"Versão do servidor MySQL: {db_info}")
    
except mysql.connector.Error as err:
    # Tratando possíveis erros de conexão
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Erro: Usuário ou senha incorretos")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Erro: Banco de dados não existe")
    else:
        print(f"Erro: {err}")
finally:
    if connection.is_connected():
        connection.close()
        print("Conexão ao banco de dados foi encerrada.")