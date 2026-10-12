from nb_common import notebook, CHECK

LIB_OF = r'''
import ipaddress
from dataclasses import dataclass, field

CAMPOS = ["in_port", "eth_src", "eth_dst", "ip_src", "ip_dst", "ip_proto", "tp_dst"]

def coincide(regla, paquete):
    """Una regla coincide si todos sus campos (los ausentes son comodín) coinciden con el paquete."""
    for k, v in regla.items():
        p = paquete.get(k)
        if k in ("ip_src", "ip_dst") and p is not None:
            if ipaddress.ip_address(p) not in ipaddress.ip_network(v):
                return False
        elif p != v:
            return False
    return True

@dataclass
class Entrada:
    prioridad: int
    match: dict
    acciones: list          # p. ej. ["output:2"], ["drop"], ["controller"]
    paquetes: int = 0

@dataclass
class TablaFlujos:
    entradas: list = field(default_factory=list)
    def agregar(self, prioridad, match, acciones):
        self.entradas.append(Entrada(prioridad, match, acciones))
        self.entradas.sort(key=lambda e: -e.prioridad)
    def procesar(self, paquete):
        for e in self.entradas:
            if coincide(e.match, paquete):
                e.paquetes += 1
                return e.acciones
        return ["controller"]   # table-miss: se envía al controlador (Packet-In)
    def mostrar(self):
        for e in self.entradas:
            print(f"prio={e.prioridad:<5} match={e.match}  ->  {e.acciones}  [{e.paquetes} pkts]")
'''

TRACE = r'''
import random
random.seed(42)
hosts = {1: ("00:00:00:00:00:01", "10.0.0.1"), 2: ("00:00:00:00:00:02", "10.0.0.2"),
         3: ("00:00:00:00:00:03", "10.0.1.3"), 4: ("00:00:00:00:00:04", "192.168.5.4")}
def traza(n=200):
    pkts = []
    for _ in range(n):
        a, b = random.sample(list(hosts), 2)
        proto, puerto = random.choice([(6, 80), (6, 443), (6, 23), (17, 53), (1, None)])
        p = {"in_port": a, "eth_src": hosts[a][0], "eth_dst": hosts[b][0],
             "ip_src": hosts[a][1], "ip_dst": hosts[b][1], "ip_proto": proto}
        if puerto: p["tp_dst"] = puerto
        pkts.append(p)
    return pkts
paquetes = traza()
'''

LEARN = r'''
class SwitchAprendiz:
    """Controlador tipo L2 learning switch: aprende MAC -> puerto e instala reglas."""
    def __init__(self):
        self.tabla = TablaFlujos(); self.mac_a_puerto = {}; self.packet_in = 0
    def recibir(self, p):
        acc = self.tabla.procesar(p)
        if acc == ["controller"]:
            self.packet_in += 1
            self.mac_a_puerto[p["eth_src"]] = p["in_port"]
            destino = self.mac_a_puerto.get(p["eth_dst"])
            if destino is None:
                return ["flood"]
            self.tabla.agregar(10, {"eth_dst": p["eth_dst"]}, [f"output:{destino}"])
            return [f"output:{destino}"]
        return acc
'''

ns = {}
exec(LIB_OF + TRACE + LEARN, ns)
sw = ns["SwitchAprendiz"]()
for p in ns["paquetes"]:
    sw.recibir(p)
E1 = sw.packet_in
E2 = sum(1 for p in ns["paquetes"] if p.get("ip_proto") == 6 and p.get("tp_dst") == 23)
E3 = sum(1 for p in ns["paquetes"] if p["ip_src"].startswith("192.168.") and p["ip_dst"].startswith("10.0.0."))

notebook(
    "future-internet/01_openflow_match_action.ipynb",
    "Tablas de flujo OpenFlow: match-action en Python",
    "Internet del Futuro: Redes Programables",
    ["Entender el modelo *match-action* de una tabla de flujos OpenFlow.",
     "Simular prioridades, comodines, prefijos IP y el *table-miss*.",
     "Programar un controlador que aprende direcciones MAC.",
     "Escribir reglas de firewall y verificarlas contra una traza de tráfico."],
    [
("md", "## 1. La tabla de flujos\nEn SDN el conmutador no decide: consulta una tabla de reglas `(prioridad, match, acciones, contadores)` que el **controlador** instala. Si ninguna regla coincide ocurre un *table-miss* y el paquete sube al controlador (**Packet-In**)."),
("code", LIB_OF.strip()),
("code", r'''t = TablaFlujos()
t.agregar(100, {"ip_proto": 6, "tp_dst": 22}, ["drop"])          # bloquear SSH
t.agregar(50,  {"ip_dst": "10.0.0.0/24"}, ["output:2"])           # LAN interna
t.agregar(0,   {}, ["output:1"])                                  # regla por defecto
print(t.procesar({"ip_dst": "10.0.0.7", "ip_proto": 6, "tp_dst": 22}))
print(t.procesar({"ip_dst": "10.0.0.7", "ip_proto": 6, "tp_dst": 80}))
print(t.procesar({"ip_dst": "8.8.8.8", "ip_proto": 17}))
t.mostrar()'''),
("md", "**Pregunta:** ¿qué pasaría si la regla de SSH tuviera prioridad 10 en lugar de 100?"),
("md", "## 2. Una traza de tráfico\nCuatro hosts conectados a los puertos 1–4 del conmutador generan 200 paquetes aleatorios (HTTP, HTTPS, Telnet, DNS, ICMP)."),
("code", TRACE.strip() + "\nprint(paquetes[:3])"),
("md", "## 3. Controlador: switch con aprendizaje\nLa primera vez que ve una MAC de origen, el controlador aprende en qué puerto está. Si ya conoce el destino, **instala una regla** para que los siguientes paquetes no suban al controlador."),
("code", LEARN.strip() + r'''

sw = SwitchAprendiz()
for p in paquetes:
    sw.recibir(p)
print("Packet-In recibidos por el controlador:", sw.packet_in)
sw.tabla.mostrar()'''),
("md", "## 4. Ejercicios\n**Ejercicio 1.** ¿Cuántos Packet-In recibió el controlador en la simulación anterior? Guárdelo en `resp_1` leyendo el atributo correspondiente, y explique por qué es mucho menor que 200."),
("code", "resp_1 = None"),
("md", "**Ejercicio 2. Firewall.** Cree una `TablaFlujos` que **bloquee Telnet** (TCP, puerto 23) y reenvíe todo lo demás por el puerto 1. Procese la traza y guarde en `resp_2` el número de paquetes descartados (use los contadores de la regla)."),
("code", "fw = TablaFlujos()\n# agregue sus reglas aquí\n\nresp_2 = None"),
("md", "**Ejercicio 3.** Cree una nueva tabla con una regla de **mayor prioridad** que descarte todo el tráfico de `192.168.0.0/16` hacia `10.0.0.0/24`, más las reglas del ejercicio 2. Procese la traza y guarde en `resp_3` cuántos paquetes descartó esa nueva regla."),
("code", "resp_3 = None"),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E1!r})\nverificar('Ejercicio 2', resp_2, {E2!r})\nverificar('Ejercicio 3', resp_3, {E3!r})"),
("md", "## 5. Del simulador a la realidad\nEn el laboratorio 1 repetirá esto con **Mininet** y un controlador **Ryu** en su computador:\n```bash\nsudo mn --topo single,4 --controller remote\nryu-manager ryu.app.simple_switch_13\n```\nCompare los Packet-In que observa con los de este simulador."),
    ])

# ---------------- VNE ----------------
LIB_VNE = r'''
import random, networkx as nx

def red_sustrato(n=20, p=0.2, semilla=1):
    rng = random.Random(semilla)
    G = nx.connected_watts_strogatz_graph(n, 4, p, seed=semilla)
    for v in G.nodes: G.nodes[v]["cpu"] = rng.randint(50, 100)
    for u, v in G.edges: G[u][v]["bw"] = rng.randint(50, 100)
    return G

def solicitud(rng, nmin=2, nmax=5):
    n = rng.randint(nmin, nmax)
    R = nx.gnp_random_graph(n, 0.5, seed=rng.randint(0, 10**6))
    while not nx.is_connected(R):
        R = nx.gnp_random_graph(n, 0.5, seed=rng.randint(0, 10**6))
    for v in R.nodes: R.nodes[v]["cpu"] = rng.randint(5, 30)
    for u, w in R.edges: R[u][w]["bw"] = rng.randint(5, 30)
    return R

def mapear(G, R, rango=lambda G, v: G.nodes[v]["cpu"]):
    """Mapeo voraz en dos etapas. Devuelve (mapa_nodos, mapa_enlaces) o None si se rechaza."""
    libres = sorted(G.nodes, key=lambda v: rango(G, v), reverse=True)
    mn = {}
    for r in sorted(R.nodes, key=lambda r: R.nodes[r]["cpu"], reverse=True):
        cand = [v for v in libres if v not in mn.values() and G.nodes[v]["cpu"] >= R.nodes[r]["cpu"]]
        if not cand: return None
        mn[r] = cand[0]
    H = G.copy(); me = {}
    for a, b in R.edges:
        bw = R[a][b]["bw"]
        sub = nx.subgraph_view(H, filter_edge=lambda u, v: H[u][v]["bw"] >= bw)
        try: camino = nx.shortest_path(sub, mn[a], mn[b])
        except nx.NetworkXNoPath: return None
        for u, v in zip(camino, camino[1:]): H[u][v]["bw"] -= bw
        me[(a, b)] = camino
    for r, v in mn.items(): G.nodes[v]["cpu"] -= R.nodes[r]["cpu"]
    for (a, b), camino in me.items():
        for u, v in zip(camino, camino[1:]): G[u][v]["bw"] -= R[a][b]["bw"]
    return mn, me

def experimento(k=60, rango=lambda G, v: G.nodes[v]["cpu"], semilla=7):
    G = red_sustrato(); rng = random.Random(semilla); aceptadas = 0
    for _ in range(k):
        if mapear(G, solicitud(rng), rango) is not None: aceptadas += 1
    return aceptadas
'''
ns = {}
exec(LIB_VNE, ns)
E4 = ns["experimento"]()

notebook(
    "future-internet/02_virtual_network_embedding.ipynb",
    "Virtual Network Embedding: un algoritmo voraz paso a paso",
    "Internet del Futuro: Redes Programables",
    ["Entender el problema de *Virtual Network Embedding* (VNE) y por qué es NP-difícil.",
     "Implementar un mapeo en dos etapas: nodos y luego enlaces.",
     "Medir la tasa de aceptación de solicitudes.",
     "Diseñar una mejor función de ranking de nodos."],
    [
("md", r"""## 1. El problema
Un proveedor de infraestructura tiene una **red sustrato** $G_S$ con CPU en nodos y ancho de banda en enlaces. Llegan **solicitudes de red virtual** $G_V$. Hay que asignar cada nodo virtual a un nodo físico distinto con CPU suficiente, y cada enlace virtual a un camino físico con ancho de banda suficiente.

Referencia: A. Fischer, **J. F. Botero**, M. T. Beck, H. de Meer, X. Hesselbach. *Virtual Network Embedding: A Survey*. IEEE COMST, 2013."""),
("code", LIB_VNE.strip()),
("code", r'''import matplotlib.pyplot as plt
G = red_sustrato(); rng = random.Random(0); R = solicitud(rng)
res = mapear(G.copy(), R)
print("Mapa de nodos:", res[0]); print("Mapa de enlaces:", res[1])
pos = nx.spring_layout(G, seed=2)
usados = set(res[0].values())
nx.draw(G, pos, node_color=["#0b6b45" if v in usados else "#dcefe4" for v in G.nodes], with_labels=True, node_size=350, font_size=8)
plt.title("Nodos físicos que alojan la red virtual"); plt.show()'''),
("md", "## 2. Tasa de aceptación\nLlegan 60 solicitudes en secuencia (sin que expiren). ¿Cuántas acepta el algoritmo voraz?"),
("code", "print(experimento(), 'de 60 solicitudes aceptadas')"),
("md", "## 3. Ejercicios\n**Ejercicio 1.** Guarde en `resp_1` el número de solicitudes aceptadas por `experimento()` con el ranking por CPU."),
("code", "resp_1 = None"),
("md", r"""**Ejercicio 2.** El ranking por CPU ignora el ancho de banda. Pruebe el ranking de Zhu y Ammar: $H(v) = \text{CPU}(v)\cdot\sum_{e \ni v} \text{BW}(e)$. Escriba la función `rango_h(G, v)`, ejecute `experimento(rango=rango_h)` y compare. ¿Mejora la aceptación? ¿Por qué?"""),
("code", "def rango_h(G, v):\n    # complete aquí\n    return G.nodes[v]['cpu']\n\nprint(experimento(rango=rango_h))"),
("md", "**Ejercicio 3 (reto).** Haga que las solicitudes expiren después de 10 llegadas (libere sus recursos) y grafique la aceptación acumulada en el tiempo para ambos rankings."),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E4!r})"),
    ])
print("ok future", E1, E2, E3, E4)
