from flask import Blueprint, render_template
from flask_login import login_required

# Importar modelos - ajuste conforme sua estrutura
try:
    from models import NotaFiscal
    NOTAS_DISPONIVEL = True
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from models import NotaFiscal
        NOTAS_DISPONIVEL = True
    except ImportError:
        NOTAS_DISPONIVEL = False

bp = Blueprint("notas", __name__, url_prefix="/notas")

@bp.route("/", methods=["GET"], endpoint="index")
@login_required
def lista():
    """Lista todas as notas fiscais"""
    try:
        if NOTAS_DISPONIVEL:
            # Buscar notas fiscais
            notas = NotaFiscal.query.order_by(NotaFiscal.data_emissao.desc()).all()
            total_notas = len(notas)
            valor_total = sum(nota.valor_total or 0 for nota in notas)
        else:
            notas = []
            total_notas = 0
            valor_total = 0
        
        return render_template(
            "notas/index.html",  # ou "notas/lista.html"
            notas=notas,
            total_notas=total_notas,
            valor_total=valor_total,
            notas_disponivel=NOTAS_DISPONIVEL
        )
    except Exception as e:
        # Se houver erro, renderizar template vazio
        return render_template(
            "notas/index.html",
            notas=[],
            total_notas=0,
            valor_total=0,
            notas_disponivel=False,
            erro=str(e)
        )
