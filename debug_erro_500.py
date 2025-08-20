#!/usr/bin/env python3
"""
Script para debugar erro 500 na rota /relatorios/
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar diretamente do arquivo app.py
import importlib.util
spec = importlib.util.spec_from_file_location("main_app", "app.py")
main_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_app)
app = main_app.app

import traceback

def debug_relatorios_error():
    """Debug detalhado do erro 500 em /relatorios/"""
    print("🔍 DEBUG DETALHADO - ERRO 500 em /relatorios/")
    print("=" * 60)
    
    try:
        with app.app_context():
            print("✅ Contexto da aplicação criado")
            
            with app.test_client() as client:
                # Simular login admin
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                    sess['user_role'] = 'admin'
                    sess['logged_in'] = True
                
                print("✅ Sessão de admin configurada")
                
                # Testar rota de relatórios
                print("🧪 Testando GET /relatorios/...")
                response = client.get('/relatorios/')
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 500:
                    print("❌ ERRO 500 DETECTADO!")
                    
                    # Tentar capturar detalhes do erro
                    content = response.get_data(as_text=True)
                    print("📄 Conteúdo da resposta:")
                    print(content[:1000])
                    
                    # Tentar executar a função diretamente para capturar o stack trace
                    print("\n🔬 TESTE DIRETO DA FUNÇÃO index()...")
                    from routes.relatorios import index
                    
                    # Simular request
                    with app.test_request_context('/relatorios/'):
                        try:
                            result = index()
                            print("✅ Função executou sem erro")
                        except Exception as e:
                            print(f"❌ ERRO NA FUNÇÃO: {str(e)}")
                            print("📋 STACK TRACE COMPLETO:")
                            traceback.print_exc()
                            
                elif response.status_code == 200:
                    print("✅ SUCESSO: Relatórios carregaram corretamente!")
                    content = response.get_data(as_text=True)
                    if 'Dashboard' in content:
                        print("✅ Dashboard presente")
                    
                else:
                    print(f"⚠️  Status inesperado: {response.status_code}")
                    content = response.get_data(as_text=True)
                    print(f"Conteúdo: {content[:500]}...")
                    
    except Exception as e:
        print(f"❌ ERRO GERAL: {str(e)}")
        print("📋 STACK TRACE:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_relatorios_error()
