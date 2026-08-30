
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# LÄS IN FIL, låt detta vara orört
# =========================

file = "Algebra_and_geometry_lab3_data.csv"
# file = "testsin.csv"

try:
    df = pd.read_csv(file, sep=";", header=None, encoding="utf-8")
except FileNotFoundError:
    raise SystemExit(f"Error: Data file '{file}' not found. Please check the file path.")

# hitta kolumn med "YYYY-MM"
ym = df[2]
T = df[3].astype(float).values

# =========================
# SKAPA TIDSVARIABEL
# =========================

year = ym.str[:4].astype(int)
month = ym.str[5:7].astype(int)
t = year + (month - 1)/12
t = t.values

T = .0007103 * t + 10

# =========================
# Skapa matrisen (ersätts i uppgiften)
# =========================

omega = 2 * np.pi # 1 år periodnp array

# X = np.ones((len(t), 4)) # dummy/start-matris, ersätts i uppgiften

A_matrix = np.column_stack([
    np.ones(len(t)),
    t,
    # np.sin(omega*t),
    # np.cos(omega*t)
])

# Commented out, may print for debugging uses
print("A_matrix =", A_matrix)
print("T =", T)

# =========================
# UPPGIFT
# =========================
# Implementera en minsta kvadrat-anpassning av modellen till data. T(t) = a + b*t + A*sin(\omega*t) + B*cos(\omega*t)

# Du ska alltså bestämma:
# - A_matrix (matrisen associerad till det överbestämda systemet)
# - beta (minsta kvadrat-lösningen till A * beta = T)
# - T_sin (modellens värden), alltså T_sin ska bli modellens prediktion av T
# - a, b, A, B (komponenterna i \beta)
# Använd matrismultiplikation för att lösa problemet.
# (A^T*A)*\beta = A^T*T, where 

left_matrix = A_matrix.T @ A_matrix
right_matrix = A_matrix.T @ T

beta = np.linalg.solve(left_matrix, right_matrix)
# a, b, A, B = beta
a, b = beta

'''
T_sin = a + b*t + A*np.sin(omega*t) + B*np.cos(omega*t)

# Gå tillbaka till c och t_s
c = np.sqrt(A**2 + B**2)
t_s = (1/omega) * np.arctan2(-B, A)

print("\nLinjär + sinus:")
print(f"a = {a:.3f}, b = {b:.5f}")
print(f"A = {A:.3f}, B = {B:.3f}")

print(f"Amplitud c = {c:.3f}")
print(f"Fas t_s = {t_s:.3f} år")

'''

T_sin = a + b*t

print("\nLinjär:")
print(f"a = {a:.3f}, b = {b:.5f}")

# =========================
# PLOT
# =========================

plt.figure(figsize=(10,6))

plt.plot(t, T, 'o', label="Data")
plt.plot(t, T_sin, label="Linjär + sinus")

plt.xlabel("Tid (år)")
plt.ylabel("Temperatur (°C)")
plt.title("Laboration 3")
plt.legend()
plt.grid()
plt.show()

