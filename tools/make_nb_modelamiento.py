import networkx as nx, pulp
from nb_common import notebook, CHECK

# (u, v, delay ms, bandwidth Gbps, cost)
LINKS = [
    ("Medellín", "Bogotá", 6, 100, 4), ("Medellín", "Cali", 7, 40, 3), ("Medellín", "Pereira", 3, 40, 2),
    ("Medellín", "Cartagena", 8, 10, 5), ("Medellín", "Bucaramanga", 6, 10, 3), ("Bogotá", "Bucaramanga", 5, 40, 3),
    ("Bogotá", "Cali", 7, 100, 4), ("Bogotá", "Pereira", 4, 10, 2), ("Pereira", "Manizales", 1, 10, 1),
    ("Manizales", "Bogotá", 4, 10, 2), ("Pereira", "Cali", 3, 40, 2), ("Cartagena", "Barranquilla", 2, 100, 1),
    ("Bucaramanga", "Cúcuta", 3, 10, 2), ("Bucaramanga", "Barranquilla", 7, 40, 4), ("Bogotá", "Cúcuta", 7, 40, 5),
    ("Bogotá", "Barranquilla", 9, 100, 6),
]
G = nx.Graph()
for u, v, d, b, c in LINKS:
    G.add_edge(u, v, delay=d, bw=b, cost=c)

E1 = nx.shortest_path_length(G, "Medellín", "Barranquilla", weight="delay")

def widest(G, s, t):
    best = 0
    for p in nx.all_simple_paths(G, s, t):
        best = max(best, min(G[a][b]["bw"] for a, b in zip(p, p[1:])))
    return best
E2 = widest(G, "Cali", "Cúcuta")

def csp(G, s, t, D):
    best = None
    for p in nx.all_simple_paths(G, s, t):
        d = sum(G[a][b]["delay"] for a, b in zip(p, p[1:]))
        c = sum(G[a][b]["cost"] for a, b in zip(p, p[1:]))
        if d <= D and (best is None or c < best):
            best = c
    return best
E3 = csp(G, "Cali", "Barranquilla", 18)

TOPO = "enlaces = [\n" + "".join(f"    {l!r},\n" for l in LINKS) + "]"

notebook(
    "modelamiento-optimizacion-redes/01_grafos_enrutamiento_qos.ipynb",
    "Grafos y enrutamiento con restricciones de QoS",
    "Modelamiento y Optimización en Redes de Comunicaciones",
    ["Representar una red de transporte como un grafo con atributos.",
     "Calcular caminos más cortos (Dijkstra) según distintas métricas.",
     "Resolver el camino más ancho (*widest path*).",
     "Formular el camino más corto con restricción de retardo (CSP), un problema NP-difícil."],
    [
("code", "import networkx as nx, matplotlib.pyplot as plt, itertools"),
("md", "## 1. Una red troncal colombiana (ficticia)\nCada enlace tiene **retardo** (ms), **capacidad** (Gbps) y un **costo** administrativo."),
("code", TOPO + r"""
G = nx.Graph()
for u, v, d, b, c in enlaces:
    G.add_edge(u, v, delay=d, bw=b, cost=c)
pos = {"Barranquilla": (0.2, 3), "Cartagena": (-0.6, 2.7), "Cúcuta": (2.2, 1.8), "Bucaramanga": (1.5, 1.2),
       "Medellín": (-0.3, 0.6), "Bogotá": (1.1, -0.2), "Manizales": (0.1, -0.1), "Pereira": (-0.2, -0.5), "Cali": (-0.6, -1.4)}
plt.figure(figsize=(7, 6))
nx.draw(G, pos, with_labels=True, node_color="#dcefe4", node_size=1400, font_size=8,
        width=[G[u][v]["bw"]/25 for u, v in G.edges])
nx.draw_networkx_edge_labels(G, pos, {(u, v): f'{G[u][v]["delay"]}ms' for u, v in G.edges}, font_size=7)
plt.show()"""),
("md", "## 2. Dijkstra con distintas métricas\nEl camino «más corto» depende de la métrica: saltos, retardo o costo."),
("code", r"""for w in [None, "delay", "cost"]:
    p = nx.shortest_path(G, "Medellín", "Cúcuta", weight=w)
    print(f"{str(w):6s} -> {' → '.join(p)}")"""),
("md", "## 3. Camino más ancho\nPara una videoconferencia de alta resolución interesa maximizar la **capacidad cuello de botella**: $\\max_P \\min_{e\\in P} b_e$. Se resuelve con una variante de Dijkstra, pero aquí lo exploramos enumerando caminos simples (la red es pequeña)."),
("code", r"""def cuello(p):
    return min(G[a][b]["bw"] for a, b in zip(p, p[1:]))
caminos = list(nx.all_simple_paths(G, "Medellín", "Barranquilla"))
print(len(caminos), "caminos simples")
for p in sorted(caminos, key=cuello, reverse=True)[:3]:
    print(cuello(p), "Gbps :", " → ".join(p))"""),
("md", r"""## 4. Camino restringido (CSP)
Minimizar el costo sujeto a un retardo máximo $D$:
$$\min \sum_{e\in P} c_e \quad \text{s.a.} \quad \sum_{e\in P} d_e \le D$$
Este problema es NP-difícil en general. Pruebe cómo cambia la solución al variar $D$."""),
("code", r"""def csp(s, t, D):
    mejor = None
    for p in nx.all_simple_paths(G, s, t):
        d = sum(G[a][b]["delay"] for a, b in zip(p, p[1:]))
        c = sum(G[a][b]["cost"] for a, b in zip(p, p[1:]))
        if d <= D and (mejor is None or c < mejor[0]):
            mejor = (c, d, p)
    return mejor
for D in [10, 14, 20]:
    print(D, csp("Medellín", "Cúcuta", D))"""),
("md", "## 5. Ejercicios\n**Ejercicio 1.** Retardo mínimo (ms) de Medellín a Barranquilla → `resp_1`.\n\n**Ejercicio 2.** Capacidad cuello de botella del camino más ancho entre Cali y Cúcuta → `resp_2`.\n\n**Ejercicio 3.** Costo mínimo de Cali a Barranquilla con retardo ≤ 18 ms → `resp_3`."),
("code", "resp_1 = None\nresp_2 = None\nresp_3 = None"),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E1!r})\nverificar('Ejercicio 2', resp_2, {E2!r})\nverificar('Ejercicio 3', resp_3, {E3!r})"),
("md", "**Ejercicio 4 (reto).** Implemente el camino más ancho con una modificación de Dijkstra (cola de prioridad con máximos) y compruebe que coincide con la enumeración. ¿Cuál es su complejidad?"),
    ])

# ------------- Notebook 2: capacitated network design (multicommodity flow) -------------
NODES = ["A", "B", "C", "D", "E", "F"]
CAND = [("A", "B", 10, 1), ("A", "C", 12, 2), ("B", "C", 6, 1), ("B", "D", 14, 2), ("C", "E", 9, 1),
        ("D", "E", 7, 1), ("D", "F", 11, 2), ("E", "F", 8, 1), ("C", "D", 10, 1)]  # u, v, fixed cost, cost per Gbps
DEM = {("A", "F"): 8, ("B", "E"): 5, ("A", "D"): 4}
CAP = 12

def design(cap=CAP, single=False):
    m = pulp.LpProblem("diseno", pulp.LpMinimize)
    arcs = [(u, v) for u, v, _, _ in CAND] + [(v, u) for u, v, _, _ in CAND]
    fc = {(u, v): f for u, v, f, _ in CAND}; vc = {(u, v): c for u, v, _, c in CAND}
    y = {(u, v): pulp.LpVariable(f"y_{u}{v}", cat="Binary") for u, v, _, _ in CAND}
    if single:
        z = {(k, a): pulp.LpVariable(f"z_{k[0]}{k[1]}_{a[0]}{a[1]}", cat="Binary") for k in DEM for a in arcs}
        x = {(k, a): DEM[k] * z[k, a] for k in DEM for a in arcs}
    else:
        x = {(k, a): pulp.LpVariable(f"x_{k[0]}{k[1]}_{a[0]}{a[1]}", 0) for k in DEM for a in arcs}
    key = lambda a: a if a in y else (a[1], a[0])
    m += pulp.lpSum(fc[e] * y[e] for e in y) + pulp.lpSum(vc[key(a)] * x[k, a] for k in DEM for a in arcs)
    for k, d in DEM.items():
        s, t = k
        for n in NODES:
            out = pulp.lpSum(x[k, a] for a in arcs if a[0] == n); inn = pulp.lpSum(x[k, a] for a in arcs if a[1] == n)
            m += out - inn == (d if n == s else -d if n == t else 0)
    for e in y:
        m += pulp.lpSum(x[k, e] + x[k, (e[1], e[0])] for k in DEM) <= cap * y[e]
    m.solve(pulp.PULP_CBC_CMD(msg=0))
    return round(pulp.value(m.objective), 4)

E5 = design(); E6 = design(cap=10); E7 = design(single=True)

notebook(
    "modelamiento-optimizacion-redes/02_diseno_red_multiflujo.ipynb",
    "Diseño de red con flujo multiproducto (ILP)",
    "Modelamiento y Optimización en Redes de Comunicaciones",
    ["Formular el problema de diseño de red con costos fijos y variables.",
     "Escribir restricciones de conservación de flujo para varias demandas.",
     "Resolver con programación lineal entera mixta (PuLP + CBC).",
     "Comparar enrutamiento divisible y no divisible (un solo camino)."],
    [
("code", "!pip -q install pulp\nimport pulp, networkx as nx, matplotlib.pyplot as plt"),
("md", r"""## 1. Formulación
Se decide qué enlaces candidatos **instalar** ($y_e \in \{0,1\}$, costo fijo $f_e$) y cómo **enrutar** cada demanda $k$ ($x^k_{ij} \ge 0$, costo $c_e$ por Gbps):

$$\min \sum_e f_e y_e + \sum_k \sum_{(i,j)} c_{ij} x^k_{ij}$$

$$\sum_j x^k_{ij} - \sum_j x^k_{ji} = \begin{cases} d_k & i = s_k \\ -d_k & i = t_k \\ 0 & \text{otro caso}\end{cases} \qquad \forall k, i$$

$$\sum_k (x^k_{ij} + x^k_{ji}) \le C\, y_{ij} \qquad \forall e=(i,j)$$"""),
("code", f"nodos = {NODES!r}\n# (u, v, costo fijo, costo por Gbps)\ncandidatos = {CAND!r}\ndemandas = {DEM!r}  # Gbps\nC = {CAP}  # capacidad de cada enlace instalado (Gbps)"),
("code", r"""def disenar(C=C, un_camino=False, dibujar=True):
    m = pulp.LpProblem("diseno", pulp.LpMinimize)
    arcos = [(u, v) for u, v, _, _ in candidatos] + [(v, u) for u, v, _, _ in candidatos]
    f = {(u, v): fc for u, v, fc, _ in candidatos}
    c = {(u, v): vc for u, v, _, vc in candidatos}
    arista = lambda a: a if a in f else (a[1], a[0])
    y = {e: pulp.LpVariable(f"y_{e[0]}{e[1]}", cat="Binary") for e in f}
    if un_camino:
        z = {(k, a): pulp.LpVariable(f"z_{k[0]}{k[1]}_{a[0]}{a[1]}", cat="Binary") for k in demandas for a in arcos}
        x = {(k, a): demandas[k] * z[k, a] for k in demandas for a in arcos}
    else:
        x = {(k, a): pulp.LpVariable(f"x_{k[0]}{k[1]}_{a[0]}{a[1]}", lowBound=0) for k in demandas for a in arcos}
    m += pulp.lpSum(f[e]*y[e] for e in y) + pulp.lpSum(c[arista(a)]*x[k, a] for k in demandas for a in arcos)
    for k, d in demandas.items():
        s, t = k
        for n in nodos:
            sale = pulp.lpSum(x[k, a] for a in arcos if a[0] == n)
            entra = pulp.lpSum(x[k, a] for a in arcos if a[1] == n)
            m += sale - entra == (d if n == s else -d if n == t else 0)
    for e in y:
        m += pulp.lpSum(x[k, e] + x[k, (e[1], e[0])] for k in demandas) <= C * y[e]
    m.solve(pulp.PULP_CBC_CMD(msg=0))
    print("Estado:", pulp.LpStatus[m.status], "| costo total =", pulp.value(m.objective))
    if dibujar:
        H = nx.Graph([(u, v) for u, v, _, _ in candidatos])
        pos = nx.spring_layout(H, seed=4)
        on = [e for e in y if y[e].value() > 0.5]
        nx.draw(H, pos, with_labels=True, node_color="#dcefe4", edge_color="#ccc", style="dashed")
        nx.draw_networkx_edges(H, pos, edgelist=on, width=3, edge_color="#0b6b45")
        plt.title("Enlaces instalados"); plt.show()
    return pulp.value(m.objective)

disenar()"""),
("md", "## 2. Ejercicios\n**Ejercicio 1.** Costo óptimo del diseño base → `resp_1`.\n\n**Ejercicio 2.** Si los enlaces solo tienen **10 Gbps**, ¿cuál es el nuevo costo óptimo? → `resp_2`. ¿Qué enlaces adicionales se instalan?\n\n**Ejercicio 3.** Con $C=12$, exija que cada demanda use **un solo camino** (`un_camino=True`) → `resp_3`. ¿Por qué el costo no puede ser menor que el del ejercicio 1?"),
("code", "resp_1 = None\nresp_2 = None\nresp_3 = None"),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E5!r}, tol=1e-4)\nverificar('Ejercicio 2', resp_2, {E6!r}, tol=1e-4)\nverificar('Ejercicio 3', resp_3, {E7!r}, tol=1e-4)"),
("md", "**Ejercicio 4 (reto).** Agregue **protección 1+1**: cada demanda debe tener dos caminos disjuntos en enlaces. Modifique la formulación y discuta el aumento de costo.\n\n**Para ir más lejos:** descargue una instancia real de [SNDlib](https://sndlib.put.poznan.pl/) y adapte el código."),
    ])
print("ok modelamiento", E1, E2, E3, E5, E6, E7)
