import math
from nb_common import notebook, CHECK

LIB_R = r'''
import heapq
red = {  # enlaces bidireccionales con costo
    ("A", "B"): 2, ("A", "C"): 5, ("B", "C"): 1, ("B", "D"): 4,
    ("C", "D"): 1, ("C", "E"): 6, ("D", "E"): 2, ("D", "F"): 7, ("E", "F"): 1,
}
def vecinos(red):
    v = {}
    for (a, b), c in red.items():
        v.setdefault(a, {})[b] = c; v.setdefault(b, {})[a] = c
    return v

def dijkstra(red, origen):
    V = vecinos(red); dist = {n: math.inf for n in V}; prev = {}
    dist[origen] = 0; cola = [(0, origen)]
    while cola:
        d, u = heapq.heappop(cola)
        if d > dist[u]: continue
        for w, c in V[u].items():
            if d + c < dist[w]:
                dist[w] = d + c; prev[w] = u; heapq.heappush(cola, (dist[w], w))
    return dist, prev

def vector_distancia(red, max_rondas=50, tablas=None, verbose=False):
    """Bellman-Ford distribuido síncrono: en cada ronda cada router envía su vector a sus vecinos."""
    V = vecinos(red); nodos = sorted(V)
    if tablas is None:
        tablas = {n: {m: (0 if m == n else math.inf) for m in nodos} for n in nodos}
    for ronda in range(1, max_rondas + 1):
        nuevas = {}
        for n in nodos:
            nuevas[n] = {m: (0 if m == n else min([V[n][w] + tablas[w][m] for w in V[n]], default=math.inf)) for m in nodos}
        if nuevas == tablas:
            return tablas, ronda - 1
        tablas = nuevas
        if verbose: print(f"ronda {ronda}: A ->", tablas["A"])
    return tablas, max_rondas
'''
import math as _m
ns = {"math": _m}
exec(LIB_R, ns)
E1 = ns["dijkstra"](ns["red"], "A")[0]["F"]
E2 = ns["vector_distancia"](ns["red"])[1]

notebook(
    "redes-computadores-3/01_enrutamiento_ls_dv.ipynb",
    "Estado de enlace vs. vector distancia: Dijkstra y Bellman-Ford",
    "Redes de Computadores III",
    ["Implementar Dijkstra (base de OSPF) y construir la tabla de reenvío.",
     "Simular vector distancia (base de RIP) ronda a ronda.",
     "Observar la convergencia y el problema de la cuenta al infinito."],
    [
("code", "import math\nimport networkx as nx, matplotlib.pyplot as plt"),
("code", LIB_R.strip() + r'''

G = nx.Graph(); [G.add_edge(a, b, weight=c) for (a, b), c in red.items()]
pos = nx.spring_layout(G, seed=3)
nx.draw(G, pos, with_labels=True, node_color="#dcefe4", node_size=700)
nx.draw_networkx_edge_labels(G, pos, nx.get_edge_attributes(G, "weight")); plt.show()'''),
("md", "## 1. Estado de enlace (OSPF)\nCada router conoce **toda** la topología (inundación de LSAs) y ejecuta Dijkstra localmente."),
("code", r'''dist, prev = dijkstra(red, "A")
def siguiente_salto(prev, origen, destino):
    while prev.get(destino) != origen: destino = prev[destino]
    return destino
print("Destino  Costo  Siguiente salto")
for n in sorted(dist):
    if n != "A": print(f"{n:8s} {dist[n]:5}  {siguiente_salto(prev, 'A', n)}")'''),
("md", "## 2. Vector distancia (RIP)\nCada router solo conoce a sus vecinos e intercambia su vector de distancias: $D_x(y) = \\min_v \\{c(x,v) + D_v(y)\\}$."),
("code", "tablas, rondas = vector_distancia(red, verbose=True)\nprint('Convergió en', rondas, 'rondas')"),
("md", "**Ejercicio 1.** Costo del camino más corto de A a F → `resp_1`.\n\n**Ejercicio 2.** Número de rondas que tarda vector distancia en converger (valor que devuelve la función) → `resp_2`."),
("code", "resp_1 = None\nresp_2 = None"),
("md", "## 3. Cuenta al infinito\nPartiendo de las tablas convergidas, el enlace **E–F** se cae. Observe cómo las distancias hacia F crecen lentamente."),
("code", r'''red_caida = {k: v for k, v in red.items() if k != ("E", "F")}
_, r = vector_distancia(red_caida, tablas=tablas, verbose=True)
print("Rondas hasta reconverger:", r)'''),
("md", "**Ejercicio 3.** Ahora elimine también el enlace **D–F** (F queda aislado). ¿Qué ocurre? Use `max_rondas=30`. Explique cómo *split horizon* y *poison reverse* mitigan el problema, e implemente *split horizon*."),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E1!r})\nverificar('Ejercicio 2', resp_2, {E2!r})"),
    ])

# ---------------- TCP ----------------
LIB_T = r'''
def reno(rtts=60, ssthresh=32, perdidas=(18, 35, 48), timeouts=()):
    """cwnd (en MSS) por RTT para TCP Reno. perdidas: RTTs con 3 ACK duplicados; timeouts: RTTs con RTO."""
    cwnd, hist = 1.0, []
    for t in range(rtts):
        hist.append(cwnd)
        if t in timeouts:
            ssthresh = max(cwnd / 2, 2); cwnd = 1.0
        elif t in perdidas:
            ssthresh = max(cwnd / 2, 2); cwnd = ssthresh          # recuperación rápida
        elif cwnd < ssthresh:
            cwnd = min(cwnd * 2, ssthresh)                         # arranque lento
        else:
            cwnd += 1                                              # evitación de congestión (AIMD)
    return hist
'''
ns = {}
exec(LIB_T, ns)
E3 = ns["reno"]()[30]
E4 = round(math.sqrt(1.5) * 1460 * 8 / (0.1 * math.sqrt(0.01)) / 1e6, 3)

notebook(
    "redes-computadores-3/02_control_congestion_tcp.ipynb",
    "Control de congestión TCP: simulación AIMD interactiva",
    "Redes de Computadores III",
    ["Distinguir arranque lento, evitación de congestión y recuperación rápida.",
     "Simular la ventana de congestión de TCP Reno.",
     "Explorar interactivamente el efecto de las pérdidas.",
     "Estimar el throughput con la fórmula de Mathis."],
    [
("code", "import math, numpy as np, matplotlib.pyplot as plt"),
("md", "## 1. TCP Reno ronda a ronda\n- **Arranque lento:** `cwnd` se duplica cada RTT hasta `ssthresh`.\n- **Evitación de congestión:** +1 MSS por RTT (*additive increase*).\n- **3 ACK duplicados:** `ssthresh = cwnd/2`, `cwnd = ssthresh` (*multiplicative decrease*).\n- **Timeout:** `cwnd = 1`."),
("code", LIB_T.strip() + r'''

h = reno()
plt.figure(figsize=(8, 3.5)); plt.step(range(len(h)), h, where="post")
plt.xlabel("RTT"); plt.ylabel("cwnd (MSS)"); plt.title("TCP Reno: diente de sierra AIMD"); plt.grid(alpha=.3); plt.show()'''),
("md", "## 2. Explore\nMueva los controles: tasa de pérdidas aleatorias y `ssthresh` inicial."),
("code", r'''from ipywidgets import interact, FloatSlider, IntSlider
def explorar(p_perdida=0.03, ssthresh=32, semilla=1):
    rng = np.random.default_rng(semilla)
    perd = tuple(t for t in range(100) if rng.random() < p_perdida)
    h = reno(100, ssthresh, perd)
    plt.figure(figsize=(8, 3)); plt.step(range(100), h, where="post")
    plt.title(f"cwnd media = {np.mean(h):.1f} MSS"); plt.ylim(0, 70); plt.show()
interact(explorar, p_perdida=FloatSlider(min=0, max=0.2, step=0.01, value=0.03),
         ssthresh=IntSlider(min=4, max=64, value=32), semilla=IntSlider(min=1, max=20, value=1));'''),
("md", "**Ejercicio 1.** Con los parámetros por defecto de `reno()`, ¿cuál es `cwnd` en el RTT número 30 (índice 30 de la lista)? → `resp_1`"),
("code", "resp_1 = None"),
("md", r"""## 3. Fórmula de Mathis
Para pérdidas aleatorias con probabilidad $p$:
$$\text{Throughput} \approx \frac{MSS}{RTT}\cdot\frac{C}{\sqrt{p}}, \qquad C = \sqrt{3/2}$$

**Ejercicio 2.** Calcule el throughput en **Mbps** para MSS = 1460 bytes, RTT = 100 ms y $p = 0.01$. Redondee a 3 decimales → `resp_2`. ¿Cuánto cambia si el RTT baja a 10 ms (un servidor en Medellín en lugar de EE. UU.)?"""),
("code", "resp_2 = None"),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E3!r})\nverificar('Ejercicio 2', resp_2, {E4!r}, tol=1e-3)"),
("md", "**Ejercicio 3 (reto).** Implemente TCP **CUBIC** ($W(t) = C(t-K)^3 + W_{max}$) y compárelo con Reno en un enlace de alto producto ancho de banda × retardo."),
    ])
print("ok redes3", E1, E2, E3, E4)
