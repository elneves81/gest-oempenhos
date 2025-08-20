#!/usr/bin/env python3
"""
Script para remover campo data_fim_original dos templates
"""
import os
import re
from pathlib import Path

def remover_campo_data_fim_original(arquivo_path):
    """Remove o campo data_fim_original de um template HTML"""
    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        conteudo_original = conteudo
        
        # Padrão para remover o grupo completo do campo data_fim_original
        # Inclui a div col-md-6, label, input e div de fechamento
        padrao_campo = r'<div class="col-md-6">\s*<label for="data_fim_original".*?</div>\s*</div>'
        conteudo = re.sub(padrao_campo, '', conteudo, flags=re.DOTALL)
        
        # Padrão alternativo mais específico
        padrao_label = r'<label for="data_fim_original"[^>]*>.*?</label>'
        conteudo = re.sub(padrao_label, '', conteudo, flags=re.DOTALL)
        
        padrao_input = r'<input[^>]*id="data_fim_original"[^>]*>'
        conteudo = re.sub(padrao_input, '', conteudo, flags=re.DOTALL)
        
        # Remover divs vazias que podem ter sobrado
        conteudo = re.sub(r'<div class="col-md-6">\s*</div>', '', conteudo)
        
        # Remover referências no template de detalhes
        padrao_detalhes = r'\{% if contrato\.data_fim_original %\}.*?\{% endif %\}'
        conteudo = re.sub(padrao_detalhes, '', conteudo, flags=re.DOTALL)
        
        if conteudo != conteudo_original:
            with open(arquivo_path, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            print(f"✅ Removido campo de: {arquivo_path}")
            return True
        else:
            print(f"⚪ Nenhuma alteração necessária: {arquivo_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar {arquivo_path}: {e}")
        return False

def main():
    """Processa todos os templates de contratos"""
    print("🔧 Removendo campo data_fim_original dos templates...")
    
    # Lista de templates para processar
    templates = [
        "templates/contratos/form_novo.html",
        "templates/contratos/form_new.html", 
        "templates/contratos/form.html",
        "templates/contratos/form_backup.html",
        "templates/contratos/detalhes.html"
    ]
    
    alteracoes = 0
    for template in templates:
        if os.path.exists(template):
            if remover_campo_data_fim_original(template):
                alteracoes += 1
        else:
            print(f"⚠️ Arquivo não encontrado: {template}")
    
    print(f"\n📊 Resultado: {alteracoes} arquivo(s) alterado(s)")
    print("✅ Remoção do campo data_fim_original concluída!")

if __name__ == "__main__":
    main()
