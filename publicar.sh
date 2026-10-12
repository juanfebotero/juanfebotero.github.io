#!/usr/bin/env bash
# ------------------------------------------------------------
# Publica este sitio en GitHub Pages desde su computador.
#   Primera vez:   bash publicar.sh
#   Actualizar:    bash publicar.sh "mensaje opcional"
# Requiere git y GitHub CLI (gh). El inicio de sesión lo hace usted en el navegador.
# ------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v gh >/dev/null 2>&1; then
  echo "Falta GitHub CLI. Instálela con:  sudo apt install gh   (o  sudo snap install gh)"; exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "Inicie sesión en GitHub (se abrirá el navegador; use la cuenta juanxfelipe@gmail.com)."
  gh auth login --hostname github.com --git-protocol https --web --scopes workflow
fi
# subir archivos de .github/workflows requiere el permiso "workflow"
gh auth status 2>&1 | grep -q "workflow" || gh auth refresh --hostname github.com --scopes workflow
gh auth setup-git >/dev/null

# El flujo de publicación (GitHub Actions) vive en setup/deploy.yml; se copia a su lugar
mkdir -p .github/workflows
[ -f .github/workflows/deploy.yml ] || cp setup/deploy.yml .github/workflows/deploy.yml

USER_GH=$(gh api user -q .login)
REPO="${USER_GH}.github.io"
echo "Cuenta de GitHub: ${USER_GH}  ->  repositorio ${REPO}"

# Ajusta usuario, repositorio y URL en content/site.yml y el enlace de GitHub del perfil
sed -i -E "s|^github_user: .*|github_user: \"${USER_GH}\"|; s|^github_repo: .*|github_repo: \"${REPO}\"|; s|^url: .*|url: \"https://${REPO}\"|" content/site.yml
sed -i -E "s|https://github.com/[A-Za-z0-9-]+\"|https://github.com/${USER_GH}\"|" content/profile.yml
# Los cuadernos llevan el enlace de Colab dentro; se corrige el usuario también ahí
grep -rl "colab.research.google.com/github/" notebooks | xargs -r sed -i -E "s|colab.research.google.com/github/[A-Za-z0-9-]+/[A-Za-z0-9.-]+/|colab.research.google.com/github/${USER_GH}/${REPO}/|g"

if [ ! -d .git ]; then
  git init -q -b main
  git add -A
  git -c user.name="Juan Felipe Botero" -c user.email="${USER_GH}@users.noreply.github.com" commit -q -m "Sitio web inicial"
  if gh repo view "${USER_GH}/${REPO}" >/dev/null 2>&1; then
    git remote add origin "https://github.com/${USER_GH}/${REPO}.git"
    git push -u origin main
  else
    gh repo create "${REPO}" --public --source=. --remote=origin --push \
      --description "Sitio web académico de Juan Felipe Botero (Universidad de Antioquia)"
  fi
  # Activa GitHub Pages con GitHub Actions como fuente
  gh api -X POST "repos/${USER_GH}/${REPO}/pages" -f build_type=workflow >/dev/null 2>&1 || \
  gh api -X PUT  "repos/${USER_GH}/${REPO}/pages" -f build_type=workflow >/dev/null 2>&1 || true
else
  git add -A
  git -c user.name="Juan Felipe Botero" -c user.email="${USER_GH}@users.noreply.github.com" commit -q -m "${1:-Actualización del sitio}" || echo "No hay cambios nuevos."
  git push
fi

echo
echo "Listo. En uno o dos minutos el sitio estará en: https://${REPO}"
echo "Progreso de la publicación: https://github.com/${USER_GH}/${REPO}/actions"
