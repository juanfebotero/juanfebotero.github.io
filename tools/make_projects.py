"""Builds content/projects.yml from the project actas (Drive) and CvLAC.
# OBSOLETO desde el 12-10-2026: content/projects.yml se edita a mano (sin montos y con proyectos nuevos como QC3AI-LA). No ejecute este script: sobrescribiría ese archivo.
Amounts are converted to USD at the average exchange rate of the project's start year.
Re-run after editing the RAW list:  python tools/make_projects.py"""
from pathlib import Path
import yaml

# Average annual TRM (COP per USD), Superfinanciera series as published by dolar.wilkinsonpc.com.co
COP_PER_USD = {2018: 2956.43, 2019: 3281.09, 2021: 3743.09, 2022: 4255.44, 2023: 4325.05, 2024: 4071.35, 2025: 4052.71}
# ECB reference rate, annual average (USD per EUR)
USD_PER_EUR = {2019: 1.1195, 2021: 1.1827}

UDEA = "Universidad de Antioquia"

RAW = [
  # ---------- from the SIIU "Acta de registro y de propiedad intelectual" ----------
  dict(code="2025-83171", title="SUCCESS", start="2025-04", end="2028-04", role="co", funder="Erasmus+ (Unión Europea) · CODI 928 de 2025",
       partners=["Mälardalen University (Suecia)"], amount=978_944_400, cur="COP", rate_year=2025, pi="Natalia Gaviria Gómez", area="education"),
  dict(code="2025-79210", title="Sistema para la detección de ataques mediante la creación de datos abiertos e Inteligencia Artificial en aplicaciones de ciberseguridad",
       start="2024-12", end="2025-12", role="pi", funder="LACNIC · CODI 917 de 2025",
       partners=["LACNIC", "Tecnológico de Monterrey (México)"], amount=126_000_000, cur="COP", rate_year=2024, area="security"),
  dict(code="2025-79272", title="TinyML para la detección de anomalías mediante planos de datos programables en la arquitectura de Redes Definidas por Software",
       start="2024-12", end="2025-12", role="co", funder="LACNIC · CODI 918 de 2025",
       partners=["LACNIC", "Universidad de Costa Rica"], amount=114_076_000, cur="COP", rate_year=2024, pi="Adrián Lara Petitdemange (UCR)", area="security"),
  dict(code="FUA 002-2024", title="LatinAware: un motor predictivo basado en Inteligencia Artificial para detectar ciberataques dirigidos a la industria latinoamericana",
       start="2024-10", end="2026-03", role="pi", funder="Fundación Universidad de Antioquia · Convocatoria FUA 002-2024",
       partners=["Aligo S.A.S."], amount=612_316_000, cur="COP", rate_year=2024, area="security"),
  dict(code="2023-66093", title="Diseño e implementación de una red inteligente para la gestión óptima de las fuentes de energía renovable no convencional",
       start="2023-11", end="2026-11", role="co", funder="Ministerio de Ciencia, Tecnología e Innovación (Minciencias)",
       partners=["Institución Universitaria Pascual Bravo", "Promigas S.A. E.S.P.", "Celsia Colombia S.A. E.S.P.", "Potencia y Tecnologías Incorporadas S.A."],
       amount=5_230_511_802, cur="COP", rate_year=2023, pi="Nicolás Muñoz Galeano", area="smartgrid"),
  dict(code="2023-58130", title="Desarrollo de una plataforma de agricultura inteligente y autónoma energéticamente para el monitoreo continuo de variables relevantes orientada a mejorar la productividad y mitigar el impacto ambiental en cultivos hortofrutícolas de Antioquia, Quindío",
       start="2022-11", end="2026-11", role="co", funder="Sistema General de Regalías (SGR)",
       partners=["Universidad del Quindío", "Gobernación del Quindío", "Gobernación de Antioquia"], amount=10_908_048_566, cur="COP", rate_year=2022, pi="Franklin Jaramillo Isaza", area="iot"),
  dict(code="2022-53069", title="Desarrollo de una estrategia de innovación didáctica con enfoque adaptativo soportada en técnicas de Inteligencia Artificial que promueva la preparación para la vida universitaria de estudiantes de educación media del Departamento de Antioquia",
       start="2022-09", end="2025-09", role="co", funder="Sistema General de Regalías (SGR)",
       partners=["Gobernación de Antioquia"], amount=1_856_492_558, cur="COP", rate_year=2022, pi="Luis Alejandro Fletscher Bocanegra", area="education"),
  dict(code="2022-47430", title="Identificación y mitigación de ataques de denegación de servicios (DDoS) en Redes Definidas por Software",
       start="2021-10", end="2022-10", role="co", funder="LACNIC · CODI 843 de 2022",
       partners=["LACNIC", "Tecnológico de Monterrey (México)"], amount=50_000, cur="USD", pi="Jesús Arturo Pérez Díaz (Tec de Monterrey)", area="security"),
  dict(code="2021-43810", title="Fortalecimiento de las capacidades de investigación y desarrollo en gestión de riesgos cibernéticos en la infraestructura crítica del sector eléctrico desde las instituciones de educación superior públicas de Medellín",
       start="2021-09", end="2024-09", role="pi", funder="Sistema General de Regalías (SGR) · OCAD 100",
       partners=["Universidad Nacional de Colombia"], amount=2_281_443_893, cur="COP", rate_year=2021, area="smartgrid"),
  dict(code="2021-44071", title="Administración inteligente de problemas de seguridad ciudadana a través de modelos y herramientas generadas a partir de plataformas para territorios inteligentes apoyadas por estrategias de participación ciudadana en la ciudad de Medellín",
       start="2021-09", end="2024-09", role="co", funder="Sistema General de Regalías (SGR) · OCAD 97",
       partners=["Universidad Nacional de Colombia"], amount=2_634_302_085, cur="COP", rate_year=2021, pi="José Edinson Aedo Cobo", area="iot"),
  dict(code="2021-41470", title="Comprehensive Internationalization through digitalization, innovation and global regional coproduction",
       start="2021-04", end="2023-04", role="co", funder="STINT – Swedish Foundation for International Cooperation in Research and Higher Education · CODI 830 de 2021",
       partners=["Mälardalen University (Suecia)"], amount=604_642, cur="EUR", rate_year=2021, pi="Natalia Gaviria Gómez", area="education"),
  dict(code="2020-31555", title="Plataforma tecnológica para resolver la problemática de comunicaciones planteada por la resolución CREG 038 de 2014 (código de medida) y el acuerdo 1043 de 2018 (requerimientos de seguridad de comunicaciones) para el mercado no regulado de energía",
       start="2019-10", end="2021-02", role="pi", funder="Minciencias (Colciencias) · Contrato 295-2019",
       partners=["Kinnesis Solutions S.A.S."], amount=240_000_000, cur="COP", rate_year=2019, area="smartgrid"),
  dict(code="2019-25931", title="Formación en redes de datos y sistemas de cómputo de nueva generación mediada por una plataforma MOOC con un enfoque pedagógico y didáctico altamente cualificado",
       start="2019-06", end="2020-09", role="co", funder="Colciencias · Convocatoria 609-2019",
       partners=["Kinetics Systems S.A.S."], amount=1_012_455_174, cur="COP", rate_year=2019, pi="Luis Alejandro Fletscher Bocanegra", area="education"),
  dict(code="2019-25170", title="Seguridad en redes de comunicación de nueva generación basadas en SDN y NFV (Red Temática CYTED)",
       start="2019-01", end="2023-01", role="pi", funder="CYTED – Programa Iberoamericano de Ciencia y Tecnología para el Desarrollo",
       partners=["Universidad del País Vasco (España)", "Universidad Galileo (Guatemala)", "Universidade Federal do Rio Grande do Sul (Brasil)", "Universidad de Costa Rica"],
       amount=154_000, cur="EUR", rate_year=2019, area="security"),
  dict(code="2017-16826", title="Desarrollo de un sistema de gestión de red como habilitador de tecnologías de Redes Inteligentes para el sector energía basado en Redes Definidas por Software (SDN)",
       start="2018-02", end="2018-10", role="pi", funder="Ruta N · Convocatoria 0249C-2017",
       partners=["Kinnesis Solutions S.A.S."], amount=353_575_000, cur="COP", rate_year=2018, area="smartgrid"),
  # ---------- from CvLAC only (no acta available: no amount / role shown) ----------
  dict(title="Desarrollo de una solución de software que automatiza las redes informáticas basado en tecnologías de redes definidas por software", start="2018-09", end="2019-07", area="smartgrid"),
  dict(title="Integración y gestión inteligente de las fuentes de energía renovable para propiciar la sostenibilidad energética", start="2019-07", area="smartgrid"),
  dict(title="Ruta N-023C: Red informática auto-configurable para las empresas eléctricas a través de un software", start="2016-10", end="2017-09", funder="Ruta N", area="smartgrid"),
  dict(title="Tormenta: gestión inteligente de servicios eléctricos en la nube (PRG-2015-7793)", start="2016-08", area="smartgrid"),
  dict(title="Redes definidas por software (SDN) como habilitador de tecnologías de redes inteligentes para el sector energía eléctrica", start="2015-05", end="2015-12", funder="Colciencias", area="smartgrid"),
  dict(title="Asignación eficiente de recursos en una arquitectura de Internet del Futuro", start="2014-10", end="2016-10", area="virtualization"),
  dict(title="Plataforma tecnológica para los servicios de teleasistencia, emergencias médicas, seguimiento y monitoreo permanente a los pacientes y apoyo a los programas de promoción y prevención", start="2013-12", end="2016-01", area="iot"),
  dict(title="All4Green", start="2011-11", end="2014-05", funder="Unión Europea · 7.º Programa Marco (FP7)", area="virtualization"),
  dict(title="Mantychore: IP Networks as a Service", start="2011-11", end="2013-03", funder="Unión Europea · 7.º Programa Marco (FP7)", partners=["i2CAT", "HEAnet", "NORDUnet"], area="virtualization"),
  dict(title="VNREAL: Virtual Network Resource Embedding Algorithms", start="2010-06", end="2011-06", funder="Euro-NF (Red de Excelencia europea)", partners=["Universitat Politècnica de Catalunya", "University of Passau", "University of Würzburg"], area="virtualization"),
  dict(title="Euro-NF: Network of the Future (Network of Excellence)", start="2008-03", end="2012-03", funder="Unión Europea · 7.º Programa Marco (FP7)", area="virtualization"),
  dict(title="Manticore II", start="2009-01", end="2010-10", partners=["Cisco", "Telefónica I+D", "HEAnet", "NORDUnet", "RedIRIS", "Juniper", "University of Essex"], area="virtualization"),
  dict(title="MANTICORE: Making APN Network Topologies on Internet COREs", start="2007-06", end="2008-06", partners=["Cisco", "Telefónica I+D", "HEAnet", "NORDUnet", "RedIRIS", "Juniper", "University of Essex"], area="virtualization"),
  dict(title="Acompañante Móvil Digital", start="2005-01", end="2007-01", area="iot"),
]


def usd(p):
    a, c = p.get("amount"), p.get("cur")
    if a is None:
        return None
    if c == "USD":
        v = a
    elif c == "EUR":
        v = a * USD_PER_EUR[p["rate_year"]]
    else:
        v = a / COP_PER_USD[p["rate_year"]]
    return int(round(v, -3))  # nearest thousand


out = []
for p in RAW:
    q = {k: p[k] for k in ("code", "title", "start", "end", "role", "funder", "pi", "area") if p.get(k)}
    q["partners"] = p.get("partners", [])
    if p.get("amount") is not None:
        q["amount_usd"] = usd(p)
        q["amount_original"] = f"{p['cur']} {p['amount']:,}".replace(",", ".") if p["cur"] == "COP" else f"{p['cur']} {p['amount']:,}"
        q["rate_year"] = p.get("rate_year")
    q["source"] = "acta" if p.get("code") else "cvlac"
    out.append(q)
out.sort(key=lambda q: q["start"], reverse=True)

header = """# ------------------------------------------------------------
# Research projects. Generated by tools/make_projects.py from the SIIU actas
# ("Acta de registro y de propiedad intelectual") and CvLAC. You may edit this file directly.
# role: pi (investigador principal) | co (coinvestigador)
# amount_usd: total project value in USD, converted at the average exchange rate
#             of the start year (TRM for COP, ECB reference rate for EUR), rounded to the nearest thousand.
# area: security | smartgrid | virtualization | iot | education  (used for filtering)
# ------------------------------------------------------------
"""
Path(__file__).parents[1].joinpath("content/projects.yml").write_text(
    header + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
for q in out:
    print(q["start"], q.get("role", "-"), q.get("amount_usd"), q.get("amount_original"), q["title"][:60])
print("total USD (actas):", sum(q.get("amount_usd") or 0 for q in out))
