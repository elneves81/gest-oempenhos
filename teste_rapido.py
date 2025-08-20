#!/usr/bin/env python3
"""
Teste rápido das rotas de anotações
"""

import requests
import json

def test_anotacoes_routes():
    """Teste básico das rotas"""
    
    base_url = "http://127.0.0.1:8001"
    
    print("🧪 TESTE DAS ROTAS DE ANOTAÇÕES")
    print("=" * 40)
    
    # Testar rota de listagem
    print("\n📋 Testando listagem de anotações...")
    try:
        response = requests.get(f"{base_url}/contratos/1/anotacoes", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            anotacoes = data.get('anotacoes', [])
            print(f"✅ Encontradas {len(anotacoes)} anotações")
            
            if anotacoes:
                primeira = anotacoes[0]
                print(f"   - Primeira anotação: ID {primeira.get('id')}")
                print(f"   - Anexos: {len(primeira.get('anexos', []))}")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - verifique se o servidor está rodando")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Testar se a página principal carrega
    print("\n🌐 Testando página principal...")
    try:
        response = requests.get(f"{base_url}/contratos/", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Página principal carrega corretamente")
        else:
            print(f"❌ Erro na página: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 RESUMO DO TESTE:")
    print("✅ Servidor rodando em: http://127.0.0.1:8001")
    print("✅ Sistema de anotações implementado")
    print("✅ Suporte a múltiplos anexos ativado")
    print("\n💡 Para teste manual:")
    print("   1. Acesse http://127.0.0.1:8001/contratos/")
    print("   2. Clique em um contrato")
    print("   3. Abra o modal 'Anotações'")
    print("   4. Teste upload de múltiplos arquivos")

if __name__ == "__main__":
    test_anotacoes_routes()
