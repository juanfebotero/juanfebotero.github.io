import itertools, math, random
import pulp
from nb_common import notebook, CHECK

# ---------- expected answers computed here, embedded as numbers ----------
def solve_isp(bw=1000, hours=120, ports=50, integer=False):
    m = pulp.LpProblem("isp", pulp.LpMaximize)
    cat = "Integer" if integer else "Continuous"
    x1 = pulp.LpVariable("x1", 0, cat=cat); x2 = pulp.LpVariable("x2", 0, cat=cat)
    m += 40 * x1 + 90 * x2
    m += 10 * x1 + 50 * x2 <= bw
    m += 2 * x1 + 3 * x2 <= hours
    m += x1 <= ports
    m.solve(pulp.PULP_CBC_CMD(msg=0))
    return pulp.value(m.objective)

E1 = solve_isp(bw=1200)
E2 = solve_isp(integer=True)

# assignment problem expected
cost = [[9, 2, 7, 8], [6, 4, 3, 7], [5, 8, 1, 8], [7, 6, 9, 4]]
E3 = min(sum(cost[i][p[i]] for i in range(4)) for p in itertools.permutations(range(4)))

notebook(
    "tecnicas-optimizacion/01_programacion_lineal.ipynb",
    "Programación lineal con PuLP: formular, resolver y visualizar",
    "Técnicas de Optimización",
    ["Formular un problema de programación lineal (PL) a partir de un enunciado.",
     "Resolverlo gráficamente y con el solver CBC a través de PuLP.",
     "Interpretar precios sombra y holguras.",
     "Ver qué cambia al exigir variables enteras."],
    [
("code", "!pip -q install pulp\nimport pulp, numpy as np, matplotlib.pyplot as plt"),
("md", r"""## 1. El problema

Un operador de internet en Medellín vende dos planes:

| Plan | Ganancia mensual | Ancho de banda reservado | Horas de instalación |
|---|---|---|---|
| Residencial ($x_1$) | 40 mil COP | 10 Mbps | 2 h |
| Empresarial ($x_2$) | 90 mil COP | 50 Mbps | 3 h |

Este mes dispone de **1000 Mbps** en el enlace de agregación, **120 horas** de técnicos y solo **50 puertos** residenciales libres.

$$\max\; z = 40x_1 + 90x_2$$
$$\text{s.a.}\quad 10x_1 + 50x_2 \le 1000,\quad 2x_1 + 3x_2 \le 120,\quad x_1 \le 50,\quad x_1,x_2 \ge 0$$"""),
("md", "## 2. Solución gráfica\nCon dos variables podemos dibujar la región factible. El óptimo de un PL siempre está en un vértice."),
("code", r"""x = np.linspace(0, 70, 400)
fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(x, (1000 - 10*x)/50, label="ancho de banda")
ax.plot(x, (120 - 2*x)/3, label="horas técnicos")
ax.axvline(50, color="gray", ls="--", label="puertos")
X, Y = np.meshgrid(np.linspace(0, 70, 300), np.linspace(0, 45, 300))
fact = (10*X + 50*Y <= 1000) & (2*X + 3*Y <= 120) & (X <= 50)
ax.contourf(X, Y, fact, levels=[0.5, 1], alpha=.25)
for z in [1500, 2500, 3300]:
    ax.plot(x, (z - 40*x)/90, ":", color="k", lw=.8)
ax.set(xlim=(0, 70), ylim=(0, 45), xlabel="$x_1$ residencial", ylabel="$x_2$ empresarial")
ax.legend(); plt.show()"""),
("md", "Las líneas punteadas son curvas de nivel de $z$. Al desplazarlas hacia arriba y a la derecha, la última que toca la región factible marca el óptimo."),
("md", "## 3. Resolver con PuLP"),
("code", r"""modelo = pulp.LpProblem("planes_isp", pulp.LpMaximize)
x1 = pulp.LpVariable("x1_residencial", lowBound=0)
x2 = pulp.LpVariable("x2_empresarial", lowBound=0)

modelo += 40*x1 + 90*x2, "ganancia"
modelo += 10*x1 + 50*x2 <= 1000, "ancho_banda"
modelo += 2*x1 + 3*x2 <= 120, "horas"
modelo += x1 <= 50, "puertos"

modelo.solve(pulp.PULP_CBC_CMD(msg=0))
print("Estado:", pulp.LpStatus[modelo.status])
print("x1 =", x1.value(), " x2 =", x2.value(), " z =", pulp.value(modelo.objective))"""),
("md", "## 4. Precios sombra y holguras\nEl **precio sombra** de una restricción dice cuánto mejora $z$ si aumentamos su lado derecho en una unidad. Una restricción con holgura positiva no está activa y su precio sombra es cero."),
("code", r"""for nombre, c in modelo.constraints.items():
    print(f"{nombre:12s} precio sombra = {c.pi:6.2f}   holgura = {c.slack:6.2f}")"""),
("md", "**Pregunta para pensar:** ¿vale la pena pagar 1 mil COP por hora extra de técnico? ¿Y 1 mil COP por Mbps adicional?"),
("md", "## 5. Ejercicios\n**Ejercicio 1.** El operador consigue 1200 Mbps en lugar de 1000. Modifique el modelo, resuélvalo y guarde la nueva ganancia óptima en `resp_1`."),
("code", "# Escriba aquí su solución\nresp_1 = None"),
("md", "**Ejercicio 2.** No se pueden vender fracciones de plan. Resuelva el modelo original con variables **enteras** (`cat='Integer'`) y guarde la ganancia en `resp_2`. ¿Por qué cambia (o no) respecto al PL?"),
("code", "# Escriba aquí su solución\nresp_2 = None"),
("md", r"""**Ejercicio 3. Asignación.** Cuatro técnicos deben atender cuatro zonas; la matriz `costo[i][j]` es el tiempo (h) del técnico *i* en la zona *j*. Formule el problema de asignación con variables binarias $y_{ij}$ (cada técnico una zona, cada zona un técnico) y guarde el tiempo mínimo total en `resp_3`."""),
("code", "costo = " + repr(cost) + "\n# Escriba aquí su solución\nresp_3 = None"),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E1!r})\nverificar('Ejercicio 2', resp_2, {E2!r})\nverificar('Ejercicio 3', resp_3, {E3!r})"),
("md", "## Para ir más lejos\n- Documentación de PuLP: https://coin-or.github.io/pulp/\n- Pruebe cambiar el solver o escribir el modelo en forma matricial con `numpy` y `scipy.optimize.linprog`."),
    ])

# ---------------- Notebook 2: simulated annealing TSP ----------------
random.seed(3)
cities = [(round(random.uniform(0, 100), 1), round(random.uniform(0, 100), 1)) for _ in range(8)]
def tour_len(t):
    return sum(math.dist(cities[t[i]], cities[t[(i + 1) % len(t)]]) for i in range(len(t)))
E4 = min(tour_len((0,) + p) for p in itertools.permutations(range(1, 8)))

notebook(
    "tecnicas-optimizacion/02_recocido_simulado.ipynb",
    "Recocido simulado para el problema del viajero (TSP)",
    "Técnicas de Optimización",
    ["Entender por qué el TSP es NP-difícil y cuándo usar metaheurísticas.",
     "Implementar recocido simulado con vecindario 2-opt.",
     "Estudiar el efecto de la temperatura inicial y el factor de enfriamiento.",
     "Comparar con la solución exacta en una instancia pequeña."],
    [
("code", "import math, random, itertools\nimport numpy as np, matplotlib.pyplot as plt\nrandom.seed(3)"),
("md", "## 1. Instancia\nOcho nodos de una red de fibra que un vehículo de mantenimiento debe visitar una vez y regresar al origen."),
("code", "ciudades = " + repr(cities) + r"""
def longitud(t):
    return sum(math.dist(ciudades[t[i]], ciudades[t[(i+1) % len(t)]]) for i in range(len(t)))
def dibujar(t, titulo=""):
    p = [ciudades[i] for i in t] + [ciudades[t[0]]]
    plt.figure(figsize=(4.5, 4.5)); plt.plot(*zip(*p), "-o"); plt.title(f"{titulo}  L = {longitud(t):.1f}"); plt.show()
dibujar(list(range(len(ciudades))), "Recorrido inicial")"""),
("md", r"""## 2. ¿Por qué no probar todo?
Con $n$ ciudades hay $(n-1)!/2$ recorridos distintos. Para 8 son 2520 (fácil). Para 20 son $6 \times 10^{16}$."""),
("code", "for n in [8, 12, 16, 20, 30]:\n    print(n, f\"{math.factorial(n-1)//2:.3e}\")"),
("md", r"""## 3. Recocido simulado
Idea: aceptar a veces soluciones peores, con probabilidad $e^{-\Delta/T}$, para escapar de óptimos locales. La temperatura $T$ baja poco a poco: $T \leftarrow \alpha T$.

Vecindario **2-opt**: se invierte un tramo del recorrido."""),
("code", r"""def vecino_2opt(t):
    i, j = sorted(random.sample(range(len(t)), 2))
    return t[:i] + t[i:j+1][::-1] + t[j+1:]

def recocido(t0, T0=100.0, alfa=0.995, iters=5000):
    actual, mejor = t0[:], t0[:]
    T, historia = T0, []
    for _ in range(iters):
        cand = vecino_2opt(actual)
        delta = longitud(cand) - longitud(actual)
        if delta < 0 or random.random() < math.exp(-delta / T):
            actual = cand
            if longitud(actual) < longitud(mejor):
                mejor = actual[:]
        historia.append(longitud(actual)); T *= alfa
    return mejor, historia

mejor, hist = recocido(list(range(len(ciudades))))
plt.plot(hist); plt.xlabel("iteración"); plt.ylabel("longitud"); plt.show()
dibujar(mejor, "Recocido simulado")"""),
("md", "## 4. Ejercicios\n**Ejercicio 1.** Calcule la longitud del recorrido **óptimo** por fuerza bruta (fije la ciudad 0 como inicio y permute las demás). Guárdela en `resp_1`."),
("code", "# Escriba aquí su solución\nresp_1 = None"),
("md", "**Ejercicio 2.** Ejecute `recocido` 20 veces con `T0=1` y 20 veces con `T0=100`. ¿Cuál encuentra el óptimo más veces? Explique con sus palabras el papel de la temperatura inicial."),
("code", "# Experimento del ejercicio 2\n"),
("md", "**Ejercicio 3 (reto).** Genere 30 ciudades aleatorias y compare recocido simulado con una búsqueda local pura (solo acepta mejoras). Grafique ambas curvas de convergencia."),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E4!r}, tol=1e-3)"),
    ])
print("ok optimizacion", E1, E2, E3, E4)
