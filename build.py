#!/usr/bin/env python3
"""
Static site generator for the academic website of Juan Felipe Botero.

    python build.py                    -> builds the site into _site/
    python build.py --serve            -> builds and serves it at http://localhost:8000
    python build.py --explicit-index   -> links point to index.html (offline preview)

Content lives in content/*.yml. Templates live in templates/, styles and scripts in static/.
You normally only edit the files in content/.
"""
import argparse
import datetime as dt
import http.server
import json
import os
import posixpath
import re
import shutil
import socketserver
import unicodedata
import urllib.parse
from pathlib import Path

import markdown as md
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "_site"
LANGS = ["es", "en"]

# Page routes for each language. Keys are page ids.
ROUTES = {
    "es": {"home": "", "research": "investigacion/", "publications": "publicaciones/",
           "projects": "proyectos/", "teaching": "docencia/", "students": "estudiantes/",
           "cv": "cv/", "contact": "contacto/"},
    "en": {"home": "en/", "research": "en/research/", "publications": "en/publications/",
           "projects": "en/projects/", "teaching": "en/teaching/", "students": "en/students/",
           "cv": "en/cv/", "contact": "en/contact/"},
}
NAV = ["home", "research", "publications", "projects", "teaching", "students", "cv", "contact"]

T = {  # interface strings
    "es": {
        "nav_home": "Inicio", "nav_research": "Investigación", "nav_publications": "Publicaciones",
        "nav_projects": "Proyectos", "nav_teaching": "Docencia", "nav_students": "Estudiantes",
        "nav_cv": "CV", "nav_contact": "Contacto", "menu": "Menú", "close": "Cerrar",
        "switch": "English", "switch_short": "EN", "theme": "Cambiar entre tema claro y oscuro",
        "skip": "Saltar al contenido", "photo_alt": "Fotografía de Juan Felipe Botero",
        "cv_pdf": "CV en PDF", "scholar": "Google Scholar", "email": "Correo", "copy_btn": "Copiar", "copied": "Copiado",
        "citations": "citas", "h_index": "índice h", "i10": "índice i10", "phd": "tesis doctorales dirigidas",
        "projects_n": "proyectos de investigación", "metrics_src": "Fuente: Google Scholar, {date}",
        "research_lines": "Líneas de investigación", "all_research": "Ver investigación",
        "topo_caption": "Una red programable y las cinco líneas que la estudian. Pase el cursor por una línea para resaltarla en la red.",
        "selected_pubs": "Publicaciones destacadas", "all_pubs": "Ver todas las publicaciones",
        "news": "Novedades", "sabbatical": "Año sabático",
        "doi": "DOI", "bibtex": "BibTeX", "copy_bibtex": "Copiar BibTeX",
        "journal": "Revista", "conference": "Congreso", "other": "Otro",
        "contact": "Contacto", "postal": "Dirección postal",
        "teaching_intro": "Cursos que dicto en la Universidad de Antioquia y en la University of Antwerp. El material de cada curso activo está en su aula de Google Classroom.",
        "status_active": "Activo", "status_sabbatical": "No se ofrece durante el año sabático", "status_upcoming": "Próximamente, 2027", "status_inactive": "No se ofrece actualmente",
        "institution": "Institución y programa", "level": "Nivel", "language": "Idioma", "semesters": "Semestres dictados", "editions": "Ediciones",
        "lang_es": "Español", "lang_en": "Inglés", "undergrad": "Pregrado", "grad": "Maestría y doctorado", "masters": "Maestría", "specialization": "Especialización",
        "syllabus": "Programa del curso (PDF)", "join_classroom": "Unirse en Google Classroom", "class_code": "Código de clase",
        "updated": "Actualizado el", "footer_note": "Sitio estático publicado en GitHub Pages, sin cookies ni rastreadores.",
        "soon": "Esta sección se completa en la siguiente fase.",
    },
    "en": {
        "nav_home": "Home", "nav_research": "Research", "nav_publications": "Publications",
        "nav_projects": "Projects", "nav_teaching": "Teaching", "nav_students": "Students",
        "nav_cv": "CV", "nav_contact": "Contact", "menu": "Menu", "close": "Close",
        "switch": "Español", "switch_short": "ES", "theme": "Switch between light and dark theme",
        "skip": "Skip to content", "photo_alt": "Photograph of Juan Felipe Botero",
        "cv_pdf": "CV (PDF)", "scholar": "Google Scholar", "email": "Email", "copy_btn": "Copy", "copied": "Copied",
        "citations": "citations", "h_index": "h-index", "i10": "i10-index", "phd": "doctoral theses supervised",
        "projects_n": "research projects", "metrics_src": "Source: Google Scholar, {date}",
        "research_lines": "Research lines", "all_research": "See research",
        "topo_caption": "A programmable network and the five lines of work that study it. Hover over a line to highlight it in the network.",
        "selected_pubs": "Selected publications", "all_pubs": "See all publications",
        "news": "News", "sabbatical": "Sabbatical",
        "doi": "DOI", "bibtex": "BibTeX", "copy_bibtex": "Copy BibTeX",
        "journal": "Journal", "conference": "Conference", "other": "Other",
        "contact": "Contact", "postal": "Postal address",
        "teaching_intro": "Courses I teach at Universidad de Antioquia and at the University of Antwerp. The material of each active course is in its Google Classroom.",
        "status_active": "Active", "status_sabbatical": "Not offered during the sabbatical", "status_upcoming": "Coming in 2027", "status_inactive": "Not currently offered",
        "institution": "Institution and program", "level": "Level", "language": "Language", "semesters": "Semesters taught", "editions": "Editions",
        "lang_es": "Spanish", "lang_en": "English", "undergrad": "Undergraduate", "grad": "Graduate", "masters": "Master's", "specialization": "Specialization",
        "syllabus": "Course syllabus (PDF)", "join_classroom": "Join on Google Classroom", "class_code": "Class code",
        "updated": "Updated", "footer_note": "Static site published on GitHub Pages, with no cookies or trackers.",
        "soon": "This section is completed in the next phase.",
    },
}

T["es"].update({
    "research_intro": "Trabajo en la gestión de redes programables con optimización matemática y aprendizaje automático. Estas son mis líneas de investigación y algunas publicaciones recientes de cada una.",
    "recent_in_line": "Publicaciones recientes", "group_title": "Grupo y colaboraciones",
    "group_text": "Investigo en el grupo GITA de la Universidad de Antioquia. Colaboro de forma continua con universidades de Europa y América Latina, con quienes compartimos proyectos, estancias de estudiantes y codirección de tesis.",
    "partners": "Socios principales",
    "pubs_intro": "Artículos en revistas, congresos y otros trabajos. Las referencias están verificadas con DBLP; las citas actualizadas están en",
    "search_pubs": "Buscar por título, autor o revista", "results": "resultados", "no_results": "Ninguna publicación coincide con los filtros.",
    "all_types": "Todos los tipos", "journals": "Revistas", "conferences": "Congresos", "others": "Otros",
    "all_topics": "Todos los temas", "all_years": "Todos los años", "topic": "Tema", "year": "Año", "type": "Tipo",
    "topic_security": "Ciberseguridad", "topic_virtualization": "Virtualización y asignación de recursos", "topic_programmable": "Redes programables",
    "topic_critical": "Infraestructura crítica y energía", "topic_education": "Educación", "topic_other": "Otros temas",
    "projects_intro": "Proyectos de investigación, desarrollo e innovación en los que he participado como investigador principal o coinvestigador. Los títulos aparecen en su idioma original.",
    "n_projects": "proyectos", "n_pi": "como investigador principal", "n_ongoing": "en curso",
    "role_pi": "Investigador principal", "role_co": "Coinvestigador", "role_na": "Participante", "role_all": "Todos los roles", "role": "Rol", "area": "Área",
    "funder": "Financiador", "partners_label": "Aliados", "pi_label": "Investigador principal", "status_ongoing": "En curso", "status_done": "Terminado",
    "area_all": "Todas las áreas", "area_security": "Ciberseguridad", "area_smartgrid": "Energía y redes eléctricas",
    "area_virtualization": "Virtualización e Internet del Futuro", "area_iot": "IoT y territorios inteligentes", "area_education": "Educación e internacionalización",
    "students_intro": "Estudiantes de doctorado y posdoctorado que he dirigido o dirijo.",
    "phd_students": "Tesis doctorales", "postdocs": "Posdoctorado", "masters_line": "He dirigido además unas {n} tesis de maestría, la mayoría en la Maestría en Ingeniería de Telecomunicaciones de la Universidad de Antioquia.",
    "ongoing_st": "En curso", "completed_st": "Terminada",
    "prospective": "Para estudiantes interesados",
    "prospective_text": "Recibo estudiantes de maestría y doctorado interesados en redes programables, optimización de redes y aprendizaje automático aplicado a la ciberseguridad. Si le interesa trabajar conmigo, escríbame por correo con su hoja de vida, un resumen de sus intereses de investigación y el programa al que piensa presentarse. Las posibilidades incluyen la Maestría en Ingeniería de Telecomunicaciones y el Doctorado en Ingeniería Electrónica y de Computación de la Universidad de Antioquia, y la codirección con universidades aliadas.",
    "cv_intro": "Resumen de mi trayectoria. La versión completa está en el CV en PDF (en inglés).",
    "download_cv": "Descargar el CV en PDF", "positions": "Cargos y estancias", "education": "Formación", "recognition": "Reconocimientos",
    "service": "Servicio académico", "editorial": "Servicio editorial", "chairs": "Organización de congresos", "talks": "Conferencias y tutoriales", "committees": "Comités y revisión", "languages": "Idiomas",
    "languages_text": "Español (lengua materna), inglés (dominio profesional completo) y catalán (lectura).",
    "contact_intro": "La forma más rápida de contactarme es por correo electrónico.",
    "profiles": "Perfiles académicos",
})
T["en"].update({
    "research_intro": "I work on the management of programmable networks with mathematical optimization and machine learning. These are my research lines and some recent publications in each.",
    "recent_in_line": "Recent publications", "group_title": "Group and collaborations",
    "group_text": "I am a member of the GITA research group at Universidad de Antioquia. I collaborate continuously with universities in Europe and Latin America, with whom we share projects, student exchanges and thesis co-supervision.",
    "partners": "Main partners",
    "pubs_intro": "Journal articles, conference papers and other work. References are checked against DBLP; up-to-date citations are on",
    "search_pubs": "Search by title, author or venue", "results": "results", "no_results": "No publication matches the filters.",
    "all_types": "All types", "journals": "Journals", "conferences": "Conferences", "others": "Other",
    "all_topics": "All topics", "all_years": "All years", "topic": "Topic", "year": "Year", "type": "Type",
    "topic_security": "Cybersecurity", "topic_virtualization": "Virtualization and resource allocation", "topic_programmable": "Programmable networks",
    "topic_critical": "Critical infrastructure and energy", "topic_education": "Education", "topic_other": "Other topics",
    "projects_intro": "Research, development and innovation projects in which I have taken part as principal investigator or co-investigator. Titles are shown in their original language.",
    "n_projects": "projects", "n_pi": "as principal investigator", "n_ongoing": "ongoing",
    "role_pi": "Principal investigator", "role_co": "Co-investigator", "role_na": "Participant", "role_all": "All roles", "role": "Role", "area": "Area",
    "funder": "Funder", "partners_label": "Partners", "pi_label": "Principal investigator", "status_ongoing": "Ongoing", "status_done": "Completed",
    "area_all": "All areas", "area_security": "Cybersecurity", "area_smartgrid": "Energy and power grids",
    "area_virtualization": "Virtualization and Future Internet", "area_iot": "IoT and smart territories", "area_education": "Education and internationalization",
    "students_intro": "Doctoral and postdoctoral researchers I have supervised or currently supervise.",
    "phd_students": "Doctoral theses", "postdocs": "Postdoctoral researchers", "masters_line": "I have also supervised about {n} master's theses, most of them in the M.Sc. in Telecommunications Engineering at Universidad de Antioquia.",
    "ongoing_st": "Ongoing", "completed_st": "Completed",
    "prospective": "Prospective students",
    "prospective_text": "I welcome master's and doctoral students interested in programmable networks, network optimization and machine learning applied to cybersecurity. If you would like to work with me, please email me your CV, a short summary of your research interests and the program you plan to apply to. Options include the M.Sc. in Telecommunications Engineering and the Ph.D. in Electronic and Computer Engineering at Universidad de Antioquia, and co-supervision with partner universities.",
    "cv_intro": "A summary of my career. The full version is in the PDF CV.",
    "download_cv": "Download the PDF CV", "positions": "Positions and research stays", "education": "Education", "recognition": "Recognition",
    "service": "Academic service", "editorial": "Editorial service", "chairs": "Conference organization", "talks": "Keynotes and tutorials", "committees": "Committees and reviewing", "languages": "Languages",
    "languages_text": "Spanish (native), English (full professional proficiency) and Catalan (reading).",
    "contact_intro": "Email is the fastest way to reach me.",
    "profiles": "Academic profiles",
})

MONTHS = {"es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}


def fmt_date(s, lang):
    """'2026-10-12' -> '12 de octubre de 2026' / 'October 12, 2026'; '2026-09' -> month and year."""
    parts = [int(x) for x in str(s).split("-")]
    if len(parts) == 1:
        return str(parts[0])
    m = MONTHS[lang][parts[1] - 1]
    if len(parts) == 2:
        return f"{m} de {parts[0]}" if lang == "es" else f"{m} {parts[0]}"
    return f"{parts[2]} de {m} de {parts[0]}" if lang == "es" else f"{m} {parts[2]}, {parts[0]}"


def load_yaml(p):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def bibtex(p):
    """BibTeX entry built from the YAML fields (no network access needed)."""
    first = re.split(r",", p["authors"])[0].strip()
    last = first.split()[-1] if first else "anon"
    words = [w for w in re.findall(r"[A-Za-z]+", p["title"]) if len(w) > 3]
    key = f"{slug(last)}{p['year']}{slug(words[0]) if words else ''}"
    kind = {"journal": "article", "conference": "inproceedings"}.get(p["type"], "misc")
    venue_field = {"article": "journal", "inproceedings": "booktitle"}.get(kind, "howpublished")
    authors = " and ".join(a.strip() for a in p["authors"].split(",") if a.strip() and a.strip() != "et al.")
    fields = [("title", "{" + p["title"] + "}"), ("author", authors), (venue_field, p["venue"]), ("year", str(p["year"]))]
    if p.get("doi"):
        fields.append(("doi", p["doi"]))
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields)
    return f"@{kind}{{{key},\n{body}\n}}"


def load_content():
    c = {}
    for name in ("site", "profile", "research", "news", "service", "students"):
        c[name] = load_yaml(CONTENT / f"{name}.yml")
    pubs = load_yaml(CONTENT / "publications.yml") or []
    for p in pubs:
        p.setdefault("type", "other")
        p["link"] = ("https://doi.org/" + p["doi"]) if p.get("doi") else (
            p.get("url") or "https://scholar.google.com/scholar?q=" + urllib.parse.quote('"' + p["title"] + '"'))
        p["bibtex"] = bibtex(p)
        p["key"] = "pub-" + slug(p["title"])[:40] + str(p["year"])
    pubs.sort(key=lambda p: (-int(p["year"]), p["title"].lower()))
    c["pubs"] = pubs
    courses = load_yaml(CONTENT / "courses.yml")
    c["blocks"] = courses["blocks"]
    c["courses"] = courses["courses"]
    projects = load_yaml(CONTENT / "projects.yml") or []
    today = dt.date.today().strftime("%Y-%m")
    for p in projects:
        p["ongoing"] = bool(p.get("end")) and p["end"] >= today
        p["years"] = p["start"][:4] + ("–" + p["end"][:4] if p.get("end") and p["end"][:4] != p["start"][:4] else "")
        for k in ("amount_usd", "amount_original", "rate_year"):   # amounts are never published
            p.pop(k, None)
    c["projects"] = projects
    return c


def person_jsonld(c, lang):
    pr = c["profile"]
    data = {
        "@context": "https://schema.org", "@type": "Person",
        "name": pr["full_name"], "alternateName": pr["name"],
        "jobTitle": pr["position"][lang], "email": "mailto:" + pr["contact"]["email"],
        "image": c["site"]["url"].rstrip("/") + "/static/img/profile-square.jpg",
        "url": c["site"]["url"],
        "affiliation": [{"@type": "CollegeOrUniversity", "name": "Universidad de Antioquia"},
                        {"@type": "CollegeOrUniversity", "name": "University of Antwerp"}],
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Universitat Politècnica de Catalunya"},
                     {"@type": "CollegeOrUniversity", "name": "Universidad de Antioquia"}],
        "knowsAbout": ["Software-defined networking", "Network function virtualization", "P4",
                       "Network optimization", "Machine learning for networking", "Network security"],
        "sameAs": [l["url"] for l in pr["links"]],
    }
    return Markup(json.dumps(data, ensure_ascii=False))


def highlight_me(authors):
    return Markup(re.sub(r"(J\. ?F\. Botero(?:[- ]Vega)?|J\. Botero|Juan F(?:elipe|\.)? Botero)",
                         r"<strong>\1</strong>", str(escape(authors))))


def build(explicit_index=False):
    c = load_content()
    site = c["site"]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    env.tests["contains"] = lambda seq, x: x in (seq or [])
    env.filters["md"] = lambda s: Markup(md.markdown(s or ""))
    env.filters["me"] = highlight_me
    env.filters["thousands"] = lambda v, lang="es": ("{:,}".format(v)).replace(",", " " if lang == "es" else ",")

    pages = []
    for lang in LANGS:
        for pid in NAV:
            pages.append((lang, pid, ROUTES[lang][pid], pid + ".html"))

    for lang, pid, path, tpl in pages:
        def url(target, lang_=lang, _from=path):
            """Relative URL from the current page to another page id (with optional #anchor) or a static path."""
            anchor = ""
            if "#" in target:
                target, anchor = target.split("#", 1)
                anchor = "#" + anchor
            dest = ROUTES[lang_][target] if target in ROUTES[lang_] else target
            rel = posixpath.relpath("/" + dest, "/" + _from) if dest else posixpath.relpath("/", "/" + _from)
            if dest.endswith("/") or dest == "":
                rel = (rel.rstrip("/") + "/") if rel != "." else "./"
                if explicit_index:
                    rel += "index.html"
            return rel + anchor

        other = "en" if lang == "es" else "es"
        ctx = dict(c, site=site, lang=lang, other=other, t=T[lang], page=pid, nav=NAV, url=url,
                   alt_url=url(pid, lang_=other), canonical=site["url"].rstrip("/") + "/" + path,
                   alt_canonical=site["url"].rstrip("/") + "/" + ROUTES[other][pid],
                   static=lambda p: url("static/" + p), fmt_date=lambda s: fmt_date(s, lang),
                   jsonld=person_jsonld(c, lang), build_date=site["updated"],
                   featured=[p for p in c["pubs"] if p.get("featured")],
                   years=sorted({p['year'] for p in c['pubs']}, reverse=True),
                   topics=['programmable', 'virtualization', 'security', 'critical', 'education', 'other'],
                   line_topic={'programmable': 'programmable', 'virtualization': 'virtualization', 'security': 'security', 'critical': 'critical', 'education': 'education'},
                   counts={k: sum(1 for p in c['pubs'] if p['type'] == k) for k in ('journal', 'conference', 'other')},
                   pstats={'n': len(c['projects']), 'pi': sum(1 for p in c['projects'] if p.get('role') == 'pi'), 'ongoing': sum(1 for p in c['projects'] if p['ongoing'])})
        html = env.get_template(tpl).render(**ctx)
        dest = OUT / path / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    home = (OUT / "index.html").read_text(encoding="utf-8")
    (OUT / "404.html").write_text(home.replace("<head>", f'<head>\n<base href="{site.get("base_path", "")}/">', 1), encoding="utf-8")
    urls = "\n".join(f"  <url><loc>{site['url'].rstrip('/')}/{p[2]}</loc></url>" for p in pages)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site['url'].rstrip('/')}/sitemap.xml\n")
    (OUT / ".nojekyll").write_text("")
    if site.get("domain"):
        (OUT / "CNAME").write_text(site["domain"] + "\n")
    print(f"Built {len(pages)} pages into {OUT}")


def serve(port=8000):
    os.chdir(OUT)
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"Serving at http://localhost:{port}  (Ctrl+C to stop)")
        httpd.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--explicit-index", action="store_true", help="link to index.html files (for offline preview)")
    a = ap.parse_args()
    build(explicit_index=a.explicit_index)
    if a.serve:
        serve()
