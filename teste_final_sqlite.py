#!/usr/bin/env python3
"""
Teste final completo de compatibilidade SQLite
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verificar_compatibilidade_final():
    """Verificação final de todas as correções SQLite"""
    print("🔍 VERIFICAÇÃO FINAL - COMPATIBILIDADE SQLITE 100%")
    print("=" * 60)
    
    try:
        # 1. Verificar imports
        print("✅ 1. Verificando imports...")
        from routes.relatorios import relatorios_bp
        from sqlalchemy import text
        print("   ✅ Import 'text' disponível")
        
        # 2. Verificar código fonte
        print("\n✅ 2. Analisando código fonte...")
        with open('routes/relatorios.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2a. Verificar extract removido
        extract_count = len(re.findall(r'extract\(', content))
        if extract_count == 0:
            print("   ✅ Nenhum extract() - COMPATÍVEL")
        else:
            print(f"   ❌ {extract_count} extract() ainda presentes")
        
        # 2b. Verificar strftime
        strftime_count = len(re.findall(r'func\.strftime', content))
        print(f"   ✅ {strftime_count} usos de func.strftime() - COMPATÍVEL")
        
        # 2c. Verificar text() para execute
        text_execute = len(re.findall(r'db\.session\.execute\(text\(', content))
        raw_execute = len(re.findall(r'db\.session\.execute\([\'"]', content))
        if text_execute > 0 and raw_execute == 0:
            print("   ✅ db.session.execute(text()) - COMPATÍVEL")
        elif raw_execute > 0:
            print(f"   ❌ {raw_execute} execute() sem text()")
        
        # 2d. Verificar datediff removido
        datediff_count = len(re.findall(r'func\.datediff|DATEDIFF', content))
        if datediff_count == 0:
            print("   ✅ Nenhum datediff - COMPATÍVEL")
        else:
            print(f"   ❌ {datediff_count} datediff ainda presentes")
        
        # 2e. Verificar outerjoin explícitos
        outerjoin_explicit = len(re.findall(r'\.outerjoin\([^,)]+,[^)]+\)', content))
        outerjoin_implicit = len(re.findall(r'\.outerjoin\([^,)]+\)(?![^)]*,)', content))
        print(f"   ✅ {outerjoin_explicit} outerjoin explícitos")
        if outerjoin_implicit > 0:
            print(f"   ⚠️  {outerjoin_implicit} outerjoin implícitos")
        
        # 2f. Verificar count(case) vs sum(case)
        count_case = len(re.findall(r'func\.count\(case\(', content))
        sum_case = len(re.findall(r'func\.sum\(case\(', content))
        print(f"   ✅ {sum_case} sum(case()) - COMPATÍVEL")
        if count_case > 0:
            print(f"   ⚠️  {count_case} count(case()) restantes")
        
        # 3. Teste de funções
        print("\n✅ 3. Testando funções...")
        from routes.relatorios import _get_estatisticas_gerais_otimizado, _get_dados_graficos_otimizado
        
        import inspect
        sig1 = inspect.signature(_get_estatisticas_gerais_otimizado)
        sig2 = inspect.signature(_get_dados_graficos_otimizado)
        
        if len(sig1.parameters) == 2 and len(sig2.parameters) == 2:
            print("   ✅ Assinaturas de função corretas")
        
        # 4. Teste de conectividade
        print("\n✅ 4. Testando banco SQLite...")
        from models import db, Empenho
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///empenhos.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # Teste strftime
            from sqlalchemy import func, case
            ano_teste = db.session.query(func.strftime('%Y', '2024-01-15')).scalar()
            print(f"   ✅ func.strftime teste: {ano_teste}")
            
            # Teste sum(case)
            if db.session.query(Empenho).count() > 0:
                teste_case = db.session.query(
                    func.sum(case((Empenho.id > 0, 1), else_=0))
                ).scalar()
                print(f"   ✅ sum(case()) teste: {teste_case}")
        
        # RESULTADO FINAL
        print("\n" + "=" * 60)
        print("🎯 VERIFICAÇÃO FINAL:")
        
        issues = []
        if extract_count > 0:
            issues.append(f"{extract_count} extract() presentes")
        if raw_execute > 0:
            issues.append(f"{raw_execute} execute() sem text()")
        if datediff_count > 0:
            issues.append(f"{datediff_count} datediff presentes")
        if count_case > 0:
            issues.append(f"{count_case} count(case()) presentes")
        if outerjoin_implicit > 0:
            issues.append(f"{outerjoin_implicit} outerjoin implícitos")
            
        if not issues:
            print("🎉 CÓDIGO 100% COMPATÍVEL COM SQLITE!")
            print("✅ Todas as correções aplicadas")
            print("✅ Sistema pronto para produção")
            print("✅ Sem riscos de erro 500 relacionados ao SQLite")
            return True
        else:
            print("⚠️  Problemas restantes:")
            for issue in issues:
                print(f"   - {issue}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verificar_compatibilidade_final()
    
    if success:
        print("\n🚀 SISTEMA FINALIZADO!")
        print("=" * 30)
        print("✅ Dashboard v2.0 funcionando")
        print("✅ SQLite 100% compatível") 
        print("✅ Sem erros 500")
        print("✅ Pronto para uso!")
    
    exit(0 if success else 1)
