# 🌿 Actividad 6.2 – Introducción a ramas con `git branch`

> En la Actividad 6.1 has practicado el flujo básico de Git (working directory → staging → commits).
> Ahora vas a aprender a trabajar con **ramas**, que son líneas de tiempo alternativas de tu proyecto.

---

## 🎯 Objetivos de la actividad

Al finalizar esta actividad serás capaz de:

- Explicar qué es una **rama** en Git y para qué se usa.
- Crear nuevas ramas con `git branch` / `git checkout -b`.
- Cambiar entre ramas y observar cómo cambia el contenido del directorio de trabajo.
- Listar ramas y reconocer en cuál estás trabajando.

---

## 🧠 Conceptos clave: ¿Qué es una rama?

Una **rama** en Git es como una **línea de tiempo alternativa** de tu proyecto: te permite desarrollar nuevas ideas sin romper la rama principal (`main`).

- Cada rama apunta a una **serie de commits** (un historial).
- La rama `main` suele representar la versión estable del proyecto.
- Crear una rama nueva es como decir: “a partir de este punto, voy a probar cosas nuevas aquí, sin tocar `main`”.

---

## 🧩 Parte 1 – Preparar el repositorio

### Reto 1.1 – Crear el repositorio base

1. Crea una carpeta para esta actividad:
   ```bash
   mkdir actividad-6-2-ramas-git
   cd actividad-6-2-ramas-git
   ```
2. Inicializa un repositorio:
   ```bash
   git init
   ```
3. Crea un archivo inicial `app.txt` con este contenido:

   ```text
   Versión inicial de la aplicación
   ```

4. Añade y haz commit:
   ```bash
   git add app.txt
   git commit -m "Versión inicial de la aplicación"
   ```

5. Lista las ramas:
   ```bash
   git branch
   ```

Deberías ver solo la rama `main`.

### Checkpoint 1 – Evidencia

- Crea el archivo `cp1-ramas-iniciales.txt` y pega la salida de:
  - `git branch`
  - `git log --oneline`

---

## 🧩 Parte 2 – Crear una rama de característica

### Reto 2.1 – Crear y cambiar a una nueva rama

Vas a crear una rama para una nueva “característica” (feature).

1. Crea una rama llamada `feature-mensaje-bienvenida` y cámbiate a ella:

   ```bash
   git checkout -b feature-mensaje-bienvenida
   ```

   Este comando:
   - Crea la rama.
   - Te cambia a esa rama en un solo paso.

2. Comprueba en qué rama estás:
   ```bash
   git branch
   ```

La rama actual debería aparecer marcada con un `*`.

### Reto 2.2 – Modificar el archivo en la nueva rama

1. Edita `app.txt` y déjalo así:

   ```text
   Versión inicial de la aplicación
   Mensaje de bienvenida: ¡Hola desde la rama feature!
   ```

2. Añade y haz commit:
   ```bash
   git add app.txt
   git commit -m "Añade mensaje de bienvenida en rama feature"
   ```

3. Muestra el historial:
   ```bash
   git log --oneline
   ```

### Checkpoint 2 – Evidencia

- Crea el archivo `cp2-feature-branch.txt` con:
  - La salida de `git branch`.
  - La salida de `git log --oneline`.
- Añade debajo una breve explicación (2–3 líneas) de qué has hecho en la rama `feature-mensaje-bienvenida`.

---

## 🧩 Parte 3 – Comparar ramas: `main` vs rama feature

### Reto 3.1 – Volver a `main` y comparar

1. Cambia de nuevo a la rama `main`:

   ```bash
   git checkout main
   ```

2. Abre el archivo `app.txt` y observa su contenido.
   Debería **NO** incluir el mensaje de bienvenida, porque ese cambio solo se hizo en la rama `feature-mensaje-bienvenida`.

3. Vuelve a la rama `feature-mensaje-bienvenida` y revisa el archivo otra vez:

   ```bash
   git checkout feature-mensaje-bienvenida
   ```
   Abre `app.txt` y comprueba que sí contiene el mensaje.

### Checkpoint 3 – Evidencia

- Crea el archivo `cp3-comparacion-ramas.md` con:
  - Una breve explicación de qué diferencias ves en `app.txt` entre `main` y `feature-mensaje-bienvenida`.
  - Una frase que resuma con tus palabras qué hace `git checkout` al cambiar de rama.

---

## 🧩 Parte 4 – Crear otra rama independiente

### Reto 4.1 – Rama para otra funcionalidad

Vas a practicar la idea de **múltiples líneas de trabajo**.

1. Sitúate en `main`:
   ```bash
   git checkout main
   ```

2. Crea y cambia a una rama llamada `feature-licencia`:

   ```bash
   git checkout -b feature-licencia
   ```

3. Crea un archivo nuevo `LICENSE.txt` con algún texto breve, por ejemplo:

   ```text
   Licencia de uso:
   - Solo para actividades didácticas.
   ```

4. Añade y haz commit:
   ```bash
   git add LICENSE.txt
   git commit -m "Añade archivo de licencia en rama feature-licencia"
   ```

5. Lista las ramas:
   ```bash
   git branch
   ```

### Checkpoint 4 – Evidencia

- Crea `cp4-multiples-ramas.txt` con:
  - La salida de `git branch`.
  - La salida de `git log --oneline` estando en `feature-licencia`.
- Indica cuántas ramas tienes y para qué sirve cada una (`main`, `feature-mensaje-bienvenida`, `feature-licencia`).

---

## 🧩 Parte 5 – Pequeña reflexión sobre ramas

### Reto 5.1 – Reflexión guiada

Crea un archivo `reflexion-6-2.md` y responde brevemente:

1. Explica con tus palabras qué es una rama y por qué es útil.
2. ¿Qué ventaja tiene trabajar una nueva funcionalidad en su propia rama, en lugar de hacerlo directamente en `main`?
3. ¿Qué podría ocurrir si todos los miembros de un equipo trabajan siempre sobre `main` sin usar ramas?

---

## 📦 Entrega esperada en el repositorio

Al finalizar, tu repositorio de la Actividad 6.2 debe incluir al menos:

- `app.txt`
- `LICENSE.txt` (creado en la rama correspondiente)
- `cp1-ramas-iniciales.txt`
- `cp2-feature-branch.txt`
- `cp3-comparacion-ramas.md`
- `cp4-multiples-ramas.txt`
- `reflexion-6-2.md`

> Nota: Es suficiente con que estos archivos estén presentes en la **rama que el profesorado indique para la entrega** (por defecto, suele ser `main` o una rama específica).

---

## 🏁 Evaluación sugerida

- 4 pts – Uso correcto de comandos de ramas (`git branch`, `git checkout`, `git checkout -b`).
- 3 pts – Evidencias claras en los archivos de checkpoints (contenidos según rama, salidas de comandos).
- 3 pts – Claridad y profundidad en `reflexion-6-2.md`.

**Puntuación máxima: 10 puntos.**

---

## 🤖 Evaluación automática y redacción de informe

Esta actividad incluye una evaluación automática similar a la de la Actividad 6.1, adaptada a ramas:

- Workflow: `.github/workflows/evaluacion.yml`
- Script de evaluación: `tools/evaluar_repo.py`
- Script de redacción IA: `tools/ai_redactor.py`

### ¿Qué genera?

Al ejecutarse en GitHub Actions, se generan los siguientes archivos en `reportes/`:

- `informe.md` (resumen técnico de evaluación)
- `informe.json` (métricas en formato estructurado)
- `metricas.csv` (puntuaciones por criterio)
- `arbol.txt` (resumen del árbol del repositorio)

Si hay credenciales de IA configuradas en Secrets/Variables, también se generan:

- `retro.md` (retroalimentación redactada por IA)
- `retro.docx` (versión formal en Word)

### Parámetros del workflow (`workflow_dispatch`)

- `min_commits` (por defecto: `3`)
- `required_files` (por defecto: `README.md,reflexion-6-2.md`)

---