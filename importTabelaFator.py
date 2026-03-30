# importTabelaFator.py
from flask import Blueprint, request, render_template 
from datetime import datetime
import pandas as pd
import mysql.connector
from configLocal import db_user, db_password, db_name, db_host, db_port

import_tabelas_bp = Blueprint("import_tabelas", __name__)


@import_tabelas_bp.route("/upload_tabelas", methods=["GET"])
def form_upload_tabelas():
    return render_template("upload_tabelas.html") # Renderiza o seu template


@import_tabelas_bp.route("/upload_tabelas", methods=["POST"])
def upload_tabelas():
    arquivos = request.files.getlist("files")
    mensagens = []

    def get_mysql_type(col_name, dtype, table_name):
        # Somente para FT_ISAGRUPCOBETURA os campos CD_LMI_INI e CD_LMI_FIM devem ser DECIMAL
        if table_name.upper() == "FT_ISAGRUPCOBETURA" and col_name in ["CD_LMI_INI", "CD_LMI_FIM"] : return "DECIMAL(18,2)"
        elif pd.api.types.is_integer_dtype(dtype): return "INT"
        elif pd.api.types.is_float_dtype(dtype): return "FLOAT"
        elif pd.api.types.is_bool_dtype(dtype): return "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(dtype): return "DATETIME"
        elif pd.api.types.is_string_dtype(dtype): return "VARCHAR(500)"
        else: return "TEXT"

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port
        )
        cursor = conn.cursor()

        for arquivo in arquivos:
            table_name = arquivo.filename.split('.')[0]
            try:
                df = pd.read_excel(arquivo)

                # Adiciona data de atualização
                df['data_hora_atualizacao'] = datetime.now()

                # Caso tabela comece com 'CA_': substitui a tabela inteira
                if table_name.startswith("CA_"):
                    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")

                    #columns_with_types = [f"`{col}` {get_mysql_type(dtype)}" for col, dtype in df.dtypes.items()]

                    columns_with_types = [f"`{col}` {get_mysql_type(col, dtype, table_name)}" for col, dtype in df.dtypes.items()]


                    create_query = f"CREATE TABLE `{table_name}` ({', '.join(columns_with_types)})"
                    cursor.execute(create_query)

                else:
                    # Caso seja 'FT_' ou 'PR_' → append
                    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                    table_exists = cursor.fetchone()

                    if table_exists:
                        # Define próximo NR_TARIFA
                        query = f"SELECT MAX(NR_TARIFA) FROM `{table_name}`"
                        cursor.execute(query)
                        result = cursor.fetchone()
                        next_nr_tarifa = int(result[0]) + 1 if result[0] is not None else 1000
                        df['NR_TARIFA'] = next_nr_tarifa
                    else:
                        df['NR_TARIFA'] = 1000
                        # Cria tabela se não existe
                        #columns_with_types = [f"`{col}` {get_mysql_type(dtype)}" for col, dtype in df.dtypes.items()]
                        columns_with_types = [f"`{col}` {get_mysql_type(col, dtype, table_name)}" for col, dtype in df.dtypes.items()]
                        create_query = f"CREATE TABLE `{table_name}` ({', '.join(columns_with_types)})"
                        cursor.execute(create_query)

                # Insere os dados
                for _, row in df.iterrows():
                    columns = ', '.join([f"`{col}`" for col in df.columns])
                    placeholders = ', '.join(['%s'] * len(row))
                    insert_query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
                    cursor.execute(insert_query, tuple(row))

                mensagens.append(f"Tabela '<strong>{table_name}</strong>' importada com sucesso.")

            except Exception as e:
                mensagens.append(f"<strong>Erro na tabela '{table_name}':</strong> {e}")

        conn.commit()

    except Exception as e:
        mensagens.append(f"<strong>Erro geral na conexão ou configuração:</strong> {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return "<br>".join(mensagens) + '<br><br><a href="/tabelas">← Voltar</a>'