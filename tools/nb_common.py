"""Helpers to write course notebooks programmatically (used once to create the starters).
You can edit the .ipynb files directly in Colab afterwards; this script is not needed for that."""
import json
from pathlib import Path

import nbformat as nbf

SITE = json.loads(json.dumps(__import__("yaml").safe_load(open(Path(__file__).parents[1] / "content/site.yml"))))

CHECK = '''# --- Autoevaluación: no modifique esta celda ---
import math
def verificar(nombre, valor, esperado, tol=1e-6):
    """Compara su respuesta con la esperada y muestra el resultado."""
    if valor is None:
        print(f"[ ] {nombre}: pendiente, complete la celda anterior.")
        return False
    try:
        ok = abs(float(valor) - float(esperado)) <= tol * max(1, abs(float(esperado)))
    except (TypeError, ValueError):
        ok = valor == esperado
    print(f"[{'✔' if ok else '✘'}] {nombre}: {'correcto' if ok else 'revise su respuesta (obtuvo ' + repr(valor) + ')'}")
    return ok
'''


def notebook(path, title, course, objectives, cells):
    nb = nbf.v4.new_notebook()
    colab = (f"https://colab.research.google.com/github/{SITE['github_user']}/{SITE['github_repo']}"
             f"/blob/{SITE['branch']}/notebooks/{path}")
    head = (f'<a href="{colab}" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Abrir en Colab"/></a>\n\n'
            f"# {title}\n\n**{course}** · Prof. Juan Felipe Botero · Universidad de Antioquia\n\n"
            "**Objetivos**\n\n" + "\n".join(f"- {o}" for o in objectives) +
            "\n\n> **Antes de empezar:** use *Archivo → Guardar una copia en Drive*. Si el cuaderno le llegó por Google Classroom, "
            "ya es su copia personal y el profesor verá su progreso.")
    nb.cells.append(nbf.v4.new_markdown_cell(head))
    for kind, src in cells:
        src = src.strip("\n")
        nb.cells.append(nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src))
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3"},
                   "language_info": {"name": "python"}, "colab": {"provenance": [], "toc_visible": True}}
    out = Path(__file__).parents[1] / "notebooks" / path
    out.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, out)
    return out
