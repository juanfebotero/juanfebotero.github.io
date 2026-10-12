# Sitio web académico de Juan Felipe Botero

Sitio estático bilingüe (español e inglés) que se publica en GitHub Pages. Todo el contenido está en archivos de texto (YAML): se edita un archivo, se publica y el sitio se reconstruye solo en uno o dos minutos.

```
content/
  site.yml            usuario y repositorio de GitHub, dirección pública, dominio propio, fecha de actualización
  profile.yml         nombre, cargos, biografía, formación, reconocimientos, métricas, contacto y enlaces
  research.yml        líneas de investigación (alimentan el dibujo de red del inicio)
  publications.yml    publicaciones; verificadas con DBLP el 12-10-2026 (campo "verified")
  projects.yml        proyectos (actas del SIIU y CvLAC); los montos no se publican
  courses.yml         bloques y fichas breves de los cursos
  news.yml            novedades del inicio (3 a 5)
  service.yml         servicio editorial, organización de congresos, charlas y comités
  students.yml        tesis doctorales y posdoctorados dirigidos
static/               estilos, scripts, foto, CV en PDF y programas de curso en PDF
templates/            plantillas HTML (rara vez hay que tocarlas)
cv-latex/             fuente LaTeX del CV (compilar con XeLaTeX); el PDF va a static/cv/
notebooks/, tools/    cuadernos de Colab del borrador anterior; se conservan, pero el sitio no los muestra
build.py              convierte content/ en el sitio, dentro de _site/
publicar.sh           crea el repositorio y publica (primera vez) o publica los cambios (después)
```

## 1. Publicar en GitHub Pages

La carpeta del proyecto es `MyDigitalTwin/Projects/website` en Google Drive; en el portátil, `~/Desktop/GoogleDrive/MyDigitalTwin/Projects/website`.

Primera vez (unos 10 minutos):

```bash
sudo apt update && sudo apt install -y git gh python3-pip   # herramientas, solo la primera vez
cd ~/Desktop/GoogleDrive/MyDigitalTwin/Projects/website
pip install -r requirements.txt                             # opcional: vista previa local
python3 build.py --serve                                    # opcional: http://localhost:8000 (Ctrl+C para salir)
bash publicar.sh                                            # crea el repositorio y publica
```

`publicar.sh` abre el navegador para que usted inicie sesión en GitHub con la cuenta `juanfebotero` y autorice a GitHub CLI. Luego crea el repositorio público `juanfebotero.github.io`, sube los archivos y activa GitHub Pages con GitHub Actions. El sitio queda en `https://juanfebotero.github.io` cuando el flujo «Publicar sitio» aparece en verde en `https://github.com/juanfebotero/juanfebotero.github.io/actions` (uno o dos minutos).

Cambios posteriores: edite los archivos de `content/` y ejecute `bash publicar.sh "qué cambió"`.

Nota: `publicar.sh` crea una carpeta oculta `.git` dentro de esta carpeta, y Google Drive la sincroniza. Funciona bien si el sitio se publica siempre desde este mismo portátil. Si algún día publica desde otro equipo, clone el repositorio allí (`gh repo clone juanfebotero/juanfebotero.github.io`) en lugar de usar la copia de Drive.

### Dominio propio (opcional)

1. Compre el dominio en un registrador.
2. En `content/site.yml` ponga `url: "https://<dominio>"` y `domain: "<dominio>"`. `build.py` crea el archivo `CNAME` que necesita GitHub Pages.
3. En el DNS del registrador cree cuatro registros `A` para el dominio raíz, que apunten a `185.199.108.153`, `185.199.109.153`, `185.199.110.153` y `185.199.111.153`, y un registro `CNAME` de `www` hacia `juanfebotero.github.io`.
4. En el repositorio, en *Settings → Pages*, escriba el dominio y active *Enforce HTTPS* cuando GitHub emita el certificado.

## 2. Edición frecuente

| Quiero… | Archivo |
|---|---|
| Actualizar las métricas de Scholar | `metrics:` en `content/profile.yml` y `updated:` en `content/site.yml` |
| Agregar una publicación | copiar un bloque en `content/publications.yml`; `featured: true` la muestra en el inicio; `topics:` controla el filtro por tema |
| Agregar un proyecto | `content/projects.yml` (sin montos) |
| Activar un curso | en `content/courses.yml`: `status: active`, `classroom_url` y `classroom_code` |
| Publicar el programa de un curso | copiar el PDF a `static/syllabi/` y poner su ruta en `syllabus:` |
| Agregar una novedad | `content/news.yml` (la más reciente arriba) |
| Actualizar el CV | editar `cv-latex/JuanFelipeBotero-CV.tex`, compilar dos veces con `xelatex` y copiar el PDF a `static/cv/` |

Estados de un curso: `active` (muestra el botón de Classroom), `sabbatical` (no se ofrece durante el año sabático), `upcoming` (próximamente, 2027) e `inactive` (no se ofrece actualmente). Al volver del sabático, cambie `sabbatical` por `active` o `inactive`, y retire el aviso de `sabbatical:` en `content/profile.yml`.

Consejos de YAML: conserve la sangría con espacios, nunca con tabuladores, y ponga entre comillas los textos que contienen `:`.
