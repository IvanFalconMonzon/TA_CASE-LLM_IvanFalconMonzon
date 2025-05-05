import subprocess
import sys

# Verificar si las dependencias están instaladas
def install_requirements():
    try:
        # Intentar importar las librerías necesarias
        import flask
        import flask_cors
        import google.generativeai
    except ImportError:
        # Si alguna librería no está instalada, instalar las dependencias del archivo requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# Llamamos a la función para instalar las dependencias si no están presentes
install_requirements()

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import subprocess
import os
import google.generativeai as genai

# Creación de la aplicación Flask
app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'generated_files'
app.config['GENERATED_FOLDER'] = 'generated_files'

# Ruta para servir la página principal
@app.route('/')
def home():
    return render_template('UML.html')

# Procesar archivo XMI
@app.route('/generated_files', methods=['POST'])
@cross_origin()
def process_diagram():
    try:
        if 'xmi' in request.files:
            file = request.files['xmi']
            diagram_path = os.path.join(app.config['UPLOAD_FOLDER'], 'diagram.xmi')
            file.save(diagram_path)
            app.logger.info(f'Archivo guardado en: {diagram_path}')

        if not os.path.exists(diagram_path):
            return jsonify({'error': 'Archivo diagram.xmi no encontrado'}), 400

        return jsonify({'message': 'Archivo procesado correctamente'}), 200

    except Exception as e:
        return jsonify({'error': f'Error inesperado: {e}'}), 500

# Mostrar código generado por CLIPS
@app.route('/mostrar_clp', methods=['GET'])
@cross_origin()
def mostrar_clp():
    try:
        result = subprocess.run(['python', 'Traductor.py'], capture_output=True, text=True)
        if result.returncode != 0:
            app.logger.error(f'Error al ejecutar Traductor.py: {result.stderr}')
            return jsonify({'error': f'Error al ejecutar Traductor.py: {result.stderr}'}), 500

        return jsonify({'output': result.stdout}), 200

    except Exception as e:
        app.logger.error(f'Error al leer el archivo de código Java: {e}')
        return jsonify({'error': f'Error al leer el archivo de código Java: {e}'}), 500

# Descargar archivos generados
@app.route('/generated_files/<path:filename>')
@cross_origin()
def download_file(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

import google.generativeai as genai

# clave API
genai.configure(api_key="")

# Traducir Java a Python con Gemini
@app.route('/traducir_a_python', methods=['POST'])
@cross_origin()
def traducir_a_python():
    try:
        java_code = request.json.get('codigo_java', '')

        if not java_code.strip():
            return jsonify({'error': 'Código Java vacío'}), 400

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"Traduce este código Java a Python. Solo responde con el código Python, sin explicaciones ni comentarios:\n\n{java_code}"
        )

        # Limpiar respuesta de bloque markdown si es necesario
        codigo_python = response.text.strip()
        if codigo_python.startswith("```"):
            codigo_python = "\n".join(codigo_python.split("\n")[1:-1]).strip()

        return jsonify({'codigo_python': codigo_python})

    except Exception as e:
        return jsonify({'error': f'Error al traducir código: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
