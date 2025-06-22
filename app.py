from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
from scipy.stats import kstest, ttest_1samp
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
STANDARD_MEAN = 14.68785011  

@app.route('/')
def index():
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

        # Prueba de normalidad
        stat, p_normal = kstest(data, 'norm', args=(data.mean(), data.std()))

        # *************** MODIFICACIÓN AQUÍ ***************
        if p_normal < 0.05:
            resultado = {
                'normal': False,
                'p_t': None, # No se calculó la prueba t
                'hipotesis': "Los datos NO son normales, no se puede realizar la prueba T-student.",
                'pruebas utilizadas': f"Kolmogorov-Smirnov p={p_normal:.4f} (Datos no normales)",
                'detalle_hipotesis': "No aplica al no cumplir el supuesto de normalidad."
            }
            # Opcional: imprimir para depuración incluso si no es normal
            print(f"Datos de entrada (data.mean()): {data.mean()}")
            print(f"Standard Mean: {STANDARD_MEAN}")
            print(f"P-valor Kolmogorov-Smirnov (p_normal): {p_normal}")
            print("Los datos no son normales, se detiene el cálculo de la prueba T.")
            return jsonify(resultado)
        # *************** FIN MODIFICACIÓN ***************

        # Prueba t de una muestra, cola superior (solo si los datos son normales)
        t_stat, p_t = ttest_1samp(data, STANDARD_MEAN, alternative='greater')

        resultado = {
            'normal': True,
            'p_t': round(p_t, 4),
            'hipotesis': (
                "Existe diferencia significativa entre los solventes"
                if p_t < 0.05 else
                "No existe diferencia significativa entre los solventes"
            ),
            'pruebas utilizadas': f"Kolmogorov-Smirnov p={p_normal:.4f}, T-student para una muestra de una cola p={p_t:.4f}",
            'detalle_hipotesis': """H0: El promedio del nuevo solvente es menor o igual que el del estándar (Etanol 70)
        H1: El promedio del nuevo solvente es mayor que el del estándar (Etanol 70)"""
        }
        print(f"Datos de entrada (data.mean()): {data.mean()}")
        print(f"Standard Mean: {STANDARD_MEAN}")
        print(f"Estadístico t: {t_stat}")
        print(f"P-valor T-student (p_t): {p_t}")

        return jsonify(resultado)


    except Exception as e:
        # Asegúrate de que el frontend maneje este error adecuadamente
        print(f"Error en calcular: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)