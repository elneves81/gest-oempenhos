#!/usr/bin/env python3
"""
Teste direto da função de relatórios para identificar erro 500
"""

import importlib.util
import sys
import traceback

# Importar especificamente o arquivo app.py
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

from models import db, Empenho, Contrato, NotaFiscal, User

def test_relatorios_function():
    """Testar função de relatórios diretamente"""
    print("🔍 Testando função de relatórios...")
    
    with app_module.app.app_context():
        try:
            # Importar a função de relatórios
            from routes.relatorios import relatorios_bp
            
            print("✅ Import do blueprint de relatórios OK")
            
            # Testar conexão com banco
            total_empenhos = Empenho.query.count()
            total_contratos = Contrato.query.count()
            total_notas = NotaFiscal.query.count()
            
            print(f"✅ Dados no banco:")
            print(f"   - Empenhos: {total_empenhos}")
            print(f"   - Contratos: {total_contratos}")  
            print(f"   - Notas: {total_notas}")
            
            # Importar e testar função específica do dashboard
            from routes.relatorios import index
            
            print("✅ Import da função index OK")
            
            # Simular contexto de usuário logado
            user = User.query.first()
            if user:
                print(f"✅ Usuário encontrado: {user.username}")
                
                # Usar Flask test client para simular requisição
                with app_module.app.test_client() as client:
                    with client.session_transaction() as sess:
                        sess['user_id'] = user.id
                        sess['_user_id'] = str(user.id)
                        sess['logged_in'] = True
                    
                    print("🔄 Testando rota /relatorios/...")
                    response = client.get('/relatorios/')
                    
                    print(f"Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("✅ Rota de relatórios funcionando!")
                        print(f"Tamanho da resposta: {len(response.data)} bytes")
                        return True
                    elif response.status_code == 500:
                        print("❌ Erro 500 - Erro interno")
                        print(f"Dados: {response.data.decode('utf-8')[:500]}...")
                        return False
                    else:
                        print(f"⚠️  Status inesperado: {response.status_code}")
                        return False
            else:
                print("❌ Nenhum usuário encontrado no banco")
                return False
                
        except ImportError as e:
            print(f"❌ Erro de import: {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_relatorios_function()
    if success:
        print("\n✅ Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falhou!")
