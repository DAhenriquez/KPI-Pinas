from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
from scipy.stats import kstest, ttest_1samp
import os

# Inicializa la aplicación Flask, indicándole que busque las plantillas
# en el directorio actual (donde se encuentra app.py).
app = Flask(__name__, template_folder='.') # <-- CAMBIO AQUÍ
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
STANDARD_MEAN = 14.68785011

@app.route('/')
def index():
    # Flask ahora buscará 'index.html' en el mismo directorio que app.py
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    if 'file' not in request.files:
        return jsonify({'error': 'Archivo no enviado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, sheet_name=0)

        data = df.iloc[:, 0].dropna().astype(float)

        # Prueba de normalidad (Kolmogorov-Smirnov)
        stat, p_normal = kstest(data, 'norm', args=(data.mean(), data.std()))

        if p_normal < 0.05:
            resultado = {
                'normal': False,
                'p_t': None,
                'hipotesis': "Los datos NO son normales, no se puede realizar la prueba T-student.",
                'pruebas_utilizadas': f"Kolmogorov-Smirnov p={p_normal:.4f} (Datos no normales)",
                'detalle_hipotesis': "No aplica al no cumplir el supuesto de normalidad."
            }
            print(f"Datos de entrada (data.mean()): {data.mean()}")
            print(f"Standard Mean: {STANDARD_MEAN}")
            print(f"P-valor Kolmogorov-Smirnov (p_normal): {p_normal}")
            print("Los datos no son normales, se detiene el cálculo de la prueba T.")
            return jsonify(resultado)

        # Prueba t de una muestra, cola superior (solo si los datos son normales)
        t_stat, p_t = ttest_1samp(data, STANDARD_MEAN, alternative='greater')

        resultado = {
            'normal': True,
            'p_t': round(p_t, 4),
            'hipotesis': (
                "Se rechaza H0"
                if p_t < 0.05 else
                "Se acepta H0"
            ),
            'pruebas_utilizadas': f"Kolmogorov-Smirnov p={p_normal:.4f}, T-student para una muestra de una cola p={p_t:.4f}",
            'detalle_hipotesis': """H0: El promedio del nuevo solvente es menor o igual que el del estándar (Etanol 70)
        H1: El promedio del nuevo solvente es mayor que el del estándar (Etanol 70)"""
        }
        print(f"Datos de entrada (data.mean()): {data.mean()}")
        print(f"Standard Mean: {STANDARD_MEAN}")
        print(f"Estadístico t: {t_stat}")
        print(f"P-valor T-student (p_t): {p_t}")

        return jsonify(resultado)

    except Exception as e:
        import traceback
        print(f"Error en calcular: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
if __name__ == '__main__':
    # Para despliegue en Render, Gunicorn gestiona el puerto.
    # En desarrollo local, puedes usar un puerto fijo o de entorno.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
