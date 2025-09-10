# Proyecto: GitHub Gist Manager

## Objetivo
Crear un módulo Python instalable que permita gestionar GitHub Gists desde la línea de comandos, compatible con Claude Code.

## Estructura del proyecto
```
gist-manager/
├── gist_manager/
│   ├── __init__.py
│   ├── core.py
│   ├── cli.py
│   └── config.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

## Especificaciones técnicas

### 1. Dependencias (requirements.txt)
```
requests>=2.31.0
click>=8.1.0
```

### 2. Configuración del paquete (setup.py)
```python
from setuptools import setup, find_packages

setup(
    name="gist-manager",
    version="1.0.0",
    description="CLI tool for managing GitHub Gists",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "click>=8.1.0"
    ],
    entry_points={
        'console_scripts': [
            'gist=gist_manager.cli:main',
            'quick-gist=gist_manager.cli:quick_command',
        ],
    },
    python_requires=">=3.7",
)
```

### 3. Funcionalidades core (gist_manager/core.py)

**Clase principal: GistManager**
- Constructor que busca token automáticamente
- Método `create_gist()` con soporte para archivos múltiples
- Método `create_from_directory()` con patrones de archivos
- Método `_read_files_from_paths()` para leer archivos locales
- Manejo robusto de errores HTTP

**Gestión de configuración:**
- Variable de entorno: `GITHUB_TOKEN`
- Archivos de config: `~/.gist-manager/config.json`, `./config.json`
- Formato config: `{"github_token": "ghp_xxxxx"}`

**Función de conveniencia:**
```python
def quick_gist(content: str, filename: str = "snippet.txt") -> str
```

### 4. CLI con Click (gist_manager/cli.py)

**Comandos principales:**

1. **`gist create [FILES...] [OPTIONS]`**
   - `--description, -d`: Descripción del gist
   - `--public, -p`: Hacer público (por defecto: privado)
   - `--output, -o`: Formato de salida (text/json)

2. **`gist from-dir [DIRECTORY] [OPTIONS]`**
   - `--patterns`: Patrones de archivos (ej: "*.py" "*.md")
   - `--description, -d`: Descripción
   - `--public, -p`: Hacer público

3. **`quick-gist [OPTIONS]`** (comando separado)
   - Lee desde stdin
   - `--filename, -f`: Nombre del archivo (default: "snippet.txt")
   - `--description, -d`: Descripción

**Ejemplos de uso esperados:**
```bash
# Crear gist con archivos específicos
gist create main.py utils.py -d "Mi proyecto Python" --public

# Crear gist desde directorio
gist from-dir ./src --patterns "*.py" "*.js" -d "Código fuente"

# Gist rápido desde stdin
echo "print('hello world')" | quick-gist -f "hello.py"

# Gist rápido desde archivo
cat script.py | quick-gist -f "script.py" -d "Script útil"
```

### 5. Configuración automática (gist_manager/config.py)

**Función `get_github_token()`:**
1. Buscar en `os.environ["GITHUB_TOKEN"]`
2. Buscar en `~/.gist-manager/config.json`
3. Buscar en `./config.json`
4. Lanzar error explicativo si no encuentra

**Función `setup_config(token: str)`:**
- Crear directorio `~/.gist-manager/`
- Guardar config.json con el token

### 6. Inicialización del paquete (gist_manager/__init__.py)
```python
from .core import GistManager, quick_gist
from .config import get_github_token, setup_config

__version__ = "1.0.0"
__all__ = ["GistManager", "quick_gist", "get_github_token", "setup_config"]
```

### 7. Archivos de soporte

**README.md debe incluir:**
- Instrucciones de instalación (`pip install -e .`)
- Configuración del token de GitHub
- Ejemplos de uso de cada comando
- Integración con Claude Code

**.env.example:**
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**.gitignore:**
```
__pycache__/
*.pyc
*.pyo
*.pyd
.env
config.json
build/
dist/
*.egg-info/
```

### 8. Características especiales

**Manejo de errores:**
- Mensajes claros para errores de autenticación
- Validación de archivos antes de enviar
- Rate limiting awareness

**Compatibilidad Claude Code:**
- Comandos simples y directos
- Salida estructurada (JSON opcional)
- Exit codes apropiados (0 = éxito, 1 = error)

**Auto-detección de contenido:**
- Descripción automática basada en tipos de archivo
- Encoding automático (UTF-8 con fallback)
- Soporte para archivos binarios (base64)

### 9. Instalación y uso

**Instalación en modo desarrollo:**
```bash
cd gist-manager
pip install -e .
```

**Configuración inicial:**
```bash
export GITHUB_TOKEN="ghp_tu_token_aqui"
# O crear config.json manualmente
```

**Uso desde Claude Code:**
Una vez instalado, Claude Code puede ejecutar comandos como:
```bash
gist create *.py -d "Generated Python code" --public
gist from-dir . --patterns "*.md" -d "Documentation"
```

### 10. Testing (TDD obligatorio)

Seguir metodología TDD (Test-Driven Development):

**Estructura de tests:**
```
tests/
├── __init__.py
├── conftest.py           # Fixtures compartidas
├── test_core.py          # Tests para funcionalidad principal
├── test_cli.py           # Tests para comandos CLI
├── test_config.py        # Tests para gestión de configuración
└── fixtures/
    ├── sample_files/     # Archivos de ejemplo para testing
    └── mock_responses/   # Respuestas mock de GitHub API
```

**Dependencias de desarrollo (requirements-dev.txt):**
```
pytest>=7.0.0
pytest-cov>=4.0.0
responses>=0.23.0
```

**Tests esenciales:**
- **test_config.py**: Discovery de token, manejo de archivos config
- **test_core.py**: GistManager, integración con API (mocked), manejo de errores
- **test_cli.py**: Comandos CLI usando Click testing utilities
- **Fixtures**: Tokens mock, directorios temporales, archivos de prueba, respuestas API

**Comandos de testing:**
```bash
python -m pytest                    # Ejecutar todos los tests
python -m pytest --cov=gist_manager # Con coverage
python -m pytest -v                 # Modo verbose
python -m pytest -x                 # Parar en primer fallo
```

---

## Tareas para Claude Code (Metodología TDD)

**Orden de desarrollo siguiendo TDD:**

1. **Configurar entorno de desarrollo**
   - Crear estructura de directorios base
   - Configurar entorno virtual (`python3.13 -m venv venv`)
   - Crear requirements.txt y requirements-dev.txt

2. **Setup de testing infrastructure**
   - Crear estructura `tests/` con conftest.py
   - Configurar pytest y fixtures básicas
   - Crear archivos de prueba en `tests/fixtures/`

3. **TDD para gist_manager/config.py**
   - Escribir tests para discovery de tokens
   - Escribir tests para manejo de archivos config
   - Implementar funcionalidad para pasar tests

4. **TDD para gist_manager/core.py**
   - Escribir tests para GistManager class
   - Crear mocks para GitHub API responses
   - Implementar integración con GitHub API

5. **TDD para gist_manager/cli.py**
   - Escribir tests para comandos CLI usando Click testing
   - Tests para parsing de argumentos y validación
   - Implementar interfaz CLI

6. **Configuración del paquete**
   - Crear setup.py y pyproject.toml
   - Crear archivos de soporte (.gitignore, .env.example)

7. **Documentación y validación final**
   - Crear README.md completo
   - Instalación de prueba (`pip install -e .`)
   - Tests de integración completos

**Prioridad: Tests primero, luego implementación. Ciclo Red-Green-Refactor.**
