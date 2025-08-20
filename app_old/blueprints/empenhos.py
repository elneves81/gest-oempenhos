from flask import Blueprint, render_template
from flask_login import login_required

# Importar modelos - ajuste conforme sua estrutura
try:
    from models import Empenho
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from models import Empenho

bp = Blueprint("empenhos", __name__, url_prefix="/empenhos")

@bp.route("/", methods=["GET"], endpoint="index")
@login_required
def lista():
    """Lista todos os empenhos"""
    try:
        # Buscar empenhos - ajuste conforme necessário
        empenhos = Empenho.query.order_by(Empenho.data_empenho.desc()).all()
        
        # Calcular estatísticas se necessário
        total_empenhos = len(empenhos)
        valor_total = sum(empenho.valor_empenhado or 0 for empenho in empenhos)
        
        return render_template(
            "empenhos/index.html",  # ou "empenhos/lista.html"
            empenhos=empenhos,
            total_empenhos=total_empenhos,
            valor_total=valor_total
        )
    except Exception as e:
        # Se houver erro, renderizar template vazio
        return render_template(
            "empenhos/index.html",
            empenhos=[],
            total_empenhos=0,
            valor_total=0,
            erro=str(e)
        )
