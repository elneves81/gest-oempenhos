from app import app

# Não criar tabelas automaticamente para evitar conflito
if __name__ == '__main__':
    print("✅ Servidor iniciando sem criar tabelas...")
    app.run(host='0.0.0.0', port=5000, debug=True)
