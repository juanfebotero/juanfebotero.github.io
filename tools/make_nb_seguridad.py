from nb_common import notebook, CHECK

PLANO = "la seguridad de una red depende tanto de la criptografia como de las personas que la administran"
def cesar(t, k):
    return "".join(chr((ord(c) - 97 + k) % 26 + 97) if c.isalpha() else c for c in t)
CIFRADO = cesar(PLANO, 7)

notebook(
    "seguridad-informacion/01_criptografia_practica.ipynb",
    "Criptografía práctica: de César a AES-GCM y RSA",
    "Seguridad de la Información",
    ["Romper un cifrado clásico por fuerza bruta y por análisis de frecuencias.",
     "Observar el efecto avalancha de una función hash.",
     "Cifrar y autenticar con AES-GCM y detectar manipulaciones.",
     "Construir RSA con números pequeños para entender sus fundamentos."],
    [
("code", "!pip -q install cryptography\nimport hashlib, os, collections, string\nimport matplotlib.pyplot as plt"),
("md", "## 1. Cifrado César\nCada letra se desplaza $k$ posiciones: $E_k(x) = (x + k) \\bmod 26$."),
("code", r'''def cesar(texto, k):
    return "".join(chr((ord(c) - 97 + k) % 26 + 97) if c.isalpha() else c for c in texto.lower())
m = "ataque al amanecer"
c = cesar(m, 3); print(c, "->", cesar(c, -3))'''),
("md", "## 2. Criptoanálisis\nSolo hay 26 claves: la fuerza bruta es inmediata. El **análisis de frecuencias** es más elegante: en español la letra más frecuente suele ser la *e* (o la *a*)."),
("code", f"cifrado = {CIFRADO!r}\n" + r'''
frec = collections.Counter(ch for ch in cifrado if ch.isalpha())
letras = string.ascii_lowercase
plt.bar(list(letras), [frec.get(l, 0) for l in letras]); plt.title("Frecuencias en el texto cifrado"); plt.show()
print("Más frecuentes:", frec.most_common(3))'''),
("md", "**Ejercicio 1.** Encuentre la clave $k$ con la que se cifró `cifrado` y guárdela en `resp_1` (un entero entre 0 y 25). Muestre el texto descifrado."),
("code", "resp_1 = None"),
("md", "## 3. Funciones hash y efecto avalancha\nUn cambio mínimo en la entrada cambia aproximadamente la mitad de los bits de la salida."),
("code", r'''def bits_distintos(a, b):
    ha, hb = hashlib.sha256(a.encode()).digest(), hashlib.sha256(b.encode()).digest()
    return sum(bin(x ^ y).count("1") for x, y in zip(ha, hb))
print(hashlib.sha256(b"Transferir 100 COP").hexdigest())
print(hashlib.sha256(b"Transferir 900 COP").hexdigest())
print("Bits distintos:", bits_distintos("Transferir 100 COP", "Transferir 900 COP"), "de 256")'''),
("md", "## 4. AES-GCM: confidencialidad + integridad\nGCM es un modo de cifrado **autenticado**: si alguien altera un solo byte del texto cifrado, el descifrado falla."),
("code", r'''from cryptography.hazmat.primitives.ciphers.aead import AESGCM
clave = AESGCM.generate_key(bit_length=256)
aes = AESGCM(clave); nonce = os.urandom(12)
ct = aes.encrypt(nonce, b"Lectura del medidor: 1532 kWh", b"subestacion-7")
print(ct.hex())
print(aes.decrypt(nonce, ct, b"subestacion-7"))'''),
("md", "**Ejercicio 2.** Modifique un byte de `ct` (por ejemplo con `bytearray`) e intente descifrar dentro de un `try/except`. Guarde en `resp_2` `True` si el descifrado **falló** como se esperaba."),
("code", "resp_2 = None"),
("md", r"""## 5. RSA de juguete
1. Elegir primos $p, q$; $n = pq$, $\varphi(n) = (p-1)(q-1)$.
2. Elegir $e$ coprimo con $\varphi(n)$.
3. $d = e^{-1} \bmod \varphi(n)$.
4. Cifrar: $c = m^e \bmod n$. Descifrar: $m = c^d \bmod n$."""),
("code", r'''p, q, e = 61, 53, 17
n, phi = p*q, (p-1)*(q-1)
# Ejercicio 3: calcule d (pista: pow(e, -1, phi))
d = None
resp_3 = d
if d:
    m = 65; c = pow(m, e, n); print("cifrado:", c, "descifrado:", pow(c, d, n))'''),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, 7)\nverificar('Ejercicio 2', resp_2, True)\nverificar('Ejercicio 3', resp_3, 2753)"),
("md", "## Para discutir\n- ¿Por qué nunca se debe reutilizar un *nonce* con la misma clave en AES-GCM?\n- ¿Por qué RSA con primos de 2 dígitos es inseguro? Intente factorizar $n$ por fuerza bruta.\n- Abra un sitio web en su navegador y revise su certificado TLS: ¿qué algoritmos usa?"),
    ])

# ---------------- IDS ----------------
LIB = r'''
import numpy as np, pandas as pd
rng = np.random.default_rng(2026)

def generar_flujos(n_normal=3000, n_ddos=800, n_scan=400):
    """Flujos sintéticos inspirados en conjuntos como LATAM-DDoS-IoT o SDNFlow."""
    def bloque(n, dur, pk, by_pk, puertos, syn, etiqueta):
        d = pd.DataFrame({
            "duracion_s": rng.gamma(*dur, n),
            "paquetes": rng.poisson(pk, n) + 1,
            "bytes_por_paquete": rng.normal(*by_pk, n).clip(40, 1500),
            "puertos_destino": rng.poisson(puertos, n) + 1,
            "fraccion_syn": rng.beta(*syn, n),
        })
        d["tasa_pps"] = d["paquetes"] / (d["duracion_s"] + 1e-3)
        d["etiqueta"] = etiqueta
        return d
    return pd.concat([
        bloque(n_normal, (2, 3), 40, (700, 250), 0.3, (1, 12), "normal"),
        bloque(n_ddos, (1, 0.3), 400, (60, 10), 0.2, (12, 2), "ddos"),
        bloque(n_scan, (1, 1), 6, (60, 5), 25, (8, 3), "escaneo"),
    ]).sample(frac=1, random_state=1).reset_index(drop=True)

flujos = generar_flujos()
'''
MODEL = r'''
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
X = flujos.drop(columns="etiqueta"); y = flujos["etiqueta"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)
rf = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_tr, y_tr)
'''
ns = {}
exec(LIB + MODEL, ns)
imp = sorted(zip(ns["rf"].feature_importances_, ns["X"].columns), reverse=True)
E_top = imp[0][1]
E_n = len(ns["flujos"])

notebook(
    "seguridad-informacion/02_deteccion_intrusiones_ml.ipynb",
    "Detección de intrusiones con aprendizaje automático",
    "Seguridad de la Información",
    ["Describir un flujo de red con características estadísticas.",
     "Entrenar un clasificador supervisado (bosque aleatorio) para detectar DDoS y escaneos.",
     "Evaluar con matriz de confusión, precisión y exhaustividad.",
     "Contrastar con detección de anomalías no supervisada (una sola clase)."],
    [
("code", "import matplotlib.pyplot as plt\nfrom sklearn.metrics import classification_report, ConfusionMatrixDisplay"),
("md", "## 1. Datos\nUn IDS basado en flujos no inspecciona el contenido: resume cada conversación en estadísticas. Generamos datos sintéticos con tres clases: tráfico **normal**, **DDoS** (inundación SYN) y **escaneo** de puertos."),
("code", LIB.strip() + "\nflujos.head()"),
("code", "flujos.groupby('etiqueta').median(numeric_only=True).round(2)"),
("md", "**Ejercicio 1.** ¿Cuántos flujos hay en total? → `resp_1`"),
("code", "resp_1 = None"),
("md", "## 2. Clasificador supervisado"),
("code", MODEL.strip() + r'''
pred = rf.predict(X_te)
print(classification_report(y_te, pred, digits=3))
ConfusionMatrixDisplay.from_predictions(y_te, pred); plt.show()'''),
("md", "**Ejercicio 2.** Use `rf.feature_importances_` para identificar la característica **más importante** y guarde su nombre (texto) en `resp_2`. ¿Tiene sentido desde el punto de vista de un ataque DDoS?"),
("code", "resp_2 = None"),
("md", "## 3. Detección de anomalías (una sola clase)\nEn la práctica rara vez tenemos ejemplos etiquetados de todos los ataques. Un detector de **una sola clase** aprende solo el tráfico normal y marca lo que se desvía. Ver: P. Arregocés, J. Vergara, S. A. Gutiérrez, J. F. Botero, *Network-based intrusion detection: A one-class classification approach*, NOMS 2022."),
("code", r'''from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.05, random_state=0).fit(X_tr[y_tr == "normal"])
anom = iso.predict(X_te) == -1
print(pd.crosstab(y_te, anom, colnames=["marcado como anómalo"]))'''),
("md", "**Ejercicio 3.** Varíe `contamination` entre 0.01 y 0.2. Grafique la tasa de detección de ataques y la tasa de falsos positivos del tráfico normal. ¿Qué valor escogería para un centro de operaciones con pocos analistas?"),
("code", "# Experimento del ejercicio 3\n"),
("code", CHECK + f"\nverificar('Ejercicio 1', resp_1, {E_n!r})\nverificar('Ejercicio 2', resp_2, {E_top!r})"),
("md", "## Para ir más lejos\nRepita el análisis con un conjunto real como **LATAM-DDoS-IoT** (IEEE DataPort) o **SDNFlow** (IEEE Access, 2024), ambos desarrollados con participación del grupo GITA."),
    ])
print("ok seguridad", E_n, E_top)
