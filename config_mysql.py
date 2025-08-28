# Configuração MySQL para XAMPP
# Substitua as configurações do SQLite por MySQL

# 1. Instalar dependências MySQL
# pip install mysql-connector-python
# pip install PyMySQL

# 2. Configurações de conexão
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # Deixe vazio se não tem senha no XAMPP
    'database': 'chat_empenhos',
    'charset': 'utf8mb4'
}

# 3. String de conexão para SQLAlchemy
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}?charset={MYSQL_CONFIG['charset']}"

# 4. Configurações alternativas
MYSQL_CONFIGS = {
    # Configuração padrão XAMPP
    'xampp': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'chat_empenhos'
    },
    
    # Configuração com senha
    'xampp_com_senha': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'sua_senha_aqui',
        'database': 'chat_empenhos'
    },
    
    # Configuração para outro usuário
    'custom': {
        'host': 'localhost',
        'port': 3306,
        'user': 'chat_user',
        'password': 'chat_password',
        'database': 'chat_empenhos'
    }
}
