import mysql.connector
from werkzeug.security import generate_password_hash
from config import db_user, db_password, db_name, db_host, db_port

#########################################################################################################
# Criação da Tabela "usuarios_consulta" e adição da coluna "perfil"
def create_users_table():
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port
    )
    
    cursor = conn.cursor()
    
    try:
        # Script SQL para criar a tabela, caso não exista
        create_table_query = """
        CREATE TABLE IF NOT EXISTS usuarios_consulta (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            nome_completo VARCHAR(100),
            ativo BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_login TIMESTAMP NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        print("Tabela 'usuarios_consulta' criada com sucesso!")
        
        # Verifica se a tabela foi criada corretamente
        cursor.execute("SHOW TABLES LIKE 'usuarios_consulta'")
        result = cursor.fetchone()
        if result:
            print("Verificação: Tabela existe no banco de dados.")
        else:
            print("Aviso: Tabela não foi criada corretamente.")
        
        # Adiciona a coluna 'perfil' se não existir
        cursor.execute("SHOW COLUMNS FROM usuarios_consulta LIKE 'perfil'")
        column_exists = cursor.fetchone()
        if not column_exists:
            add_column_query = "ALTER TABLE usuarios_consulta ADD COLUMN perfil VARCHAR(50) DEFAULT 'user';"
            cursor.execute(add_column_query)
            conn.commit()
            print("Coluna 'perfil' adicionada com sucesso!")
            
    except mysql.connector.Error as err:
        print(f"Erro ao criar tabela ou adicionar coluna: {err}")
        
    finally:
        cursor.close()
        conn.close()

#########################################################################################################
# Criação de usuários com perfis diferentes
def create_users():
    try:
        # Estabelece conexão com o banco
        with mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port
        ) as conn:
            with conn.cursor() as cursor:
                
                # Lista de usuários com diferentes perfis
                users_data = [
                    {'username': 'admin', 'password_hash': generate_password_hash('stang2025segurad@ra'), 'nome_completo': 'Fabricio Lopes', 'perfil': 'admin'},
                    {'username': 'Jardel Monti', 'password_hash': generate_password_hash('stang2025segurad@ra'), 'nome_completo': 'Jardel Monti', 'perfil': 'admin'},
                    {'username': 'Gean Eduardo', 'password_hash': generate_password_hash('stang2025segurad@ra'), 'nome_completo': 'Gean Eduardo', 'perfil': 'user'},
                    {'username': 'csPrime', 'password_hash': generate_password_hash('stg2025segurad@ra'), 'nome_completo': 'csPrime', 'perfil': 'admin'},
                ]

                # Verifica se a tabela existe
                cursor.execute("SHOW TABLES LIKE 'usuarios_consulta'")
                if not cursor.fetchone():
                    print("Erro: Tabela 'usuarios_consulta' não existe!")
                    return False

                # Insere ou atualiza os usuários
                for user_data in users_data:
                    cursor.execute("""
                        INSERT INTO usuarios_consulta 
                        (username, password_hash, nome_completo, perfil)
                        VALUES (%(username)s, %(password_hash)s, %(nome_completo)s, %(perfil)s)
                        ON DUPLICATE KEY UPDATE
                            password_hash = VALUES(password_hash),
                            nome_completo = VALUES(nome_completo),
                            perfil = VALUES(perfil)
                    """, user_data)
                    print(f"✅ Usuário '{user_data['username']}' criado ou atualizado com sucesso.")

                conn.commit()
                return True
        
    except mysql.connector.Error as err:
        print(f"⛔ Erro de banco de dados: {err}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando criação da tabela de usuários e usuários...")
    create_users_table()  # Criação da tabela e coluna 'perfil' se não existir
    success = create_users()  # Criação dos usuários
    
    if success:
        print("✔️ Processo concluído com sucesso!")
    else:
        print("✖️ Falha ao criar usuários. Verifique os logs acima.")