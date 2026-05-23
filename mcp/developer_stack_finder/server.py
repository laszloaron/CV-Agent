import os
import yaml
import ast
import re
import json
from fastmcp import FastMCP
import asyncio

mcp = FastMCP("Developer Stack Finder Server")

YAML_PATH = os.environ.get("YAML_PATH", "/app/local_projects.yaml")

def load_projects():
    try:
        if not os.path.exists(YAML_PATH):
            print(f"Warning: {YAML_PATH} does not exist.")
            return []
        with open(YAML_PATH, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('projects', []) if data else []
    except Exception as e:
        print(f"Error loading YAML: {e}")
        return []

def extract_imports_from_file(filepath):
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        # Silently pass file parsing errors to avoid spamming the logs
        pass
    return list(imports)

def extract_js_ts_imports(filepath):
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import_regex = re.compile(r"(?:import|export)\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]")
        require_regex = re.compile(r"(?:require|import)\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")
        
        for match in import_regex.findall(content) + require_regex.findall(content):
            # Csak a külső csomagokat tartjuk meg, a relatív importokat kihagyjuk
            if not match.startswith('.') and not match.startswith('/'):
                imports.add(match)
    except Exception:
        pass
    return list(imports)

def extract_java_imports(filepath):
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        java_import_regex = re.compile(r"import\s+(?:static\s+)?([\w\.]+);")
        for match in java_import_regex.findall(content):
            imports.add(match)
    except Exception:
        pass
    return list(imports)

@mcp.resource(
    uri="resource://projects",
    description="A konfigurált (elérhető) projektek neveinek listáját",
    mime_type="application/json"
)   
def get_available_projects() -> str:
    return json.dumps({
        "projects": [path.replace('\\', '/').rstrip('/').split('/')[-1] for path in load_projects()]
    })

@mcp.tool()
def get_developer_stack(project_name: str) -> list[str] | str:
    """
    Elemzi a megadott lokális projektet és visszaadja a használt importokat, amiből a fejlesztő szaktudására lehet következtetni.
    Támogatott nyelvek: Python (.py), JavaScript/TypeScript (.js, .jsx, .ts, .tsx), és Java (.java).
    """
    projects = load_projects()
    project_map = {path.replace('\\', '/').rstrip('/').split('/')[-1]: path for path in projects}
    
    if project_name not in project_map:
        return f"Hiba: A megadott projekt név '{project_name}' nem szerepel a konfigurált projektek között. Elérhető projektek: {list(project_map.keys())}"
        
    project_path = project_map[project_name]
    if not os.path.exists(project_path):
        return f"Hiba: A megadott projekt '{project_name}' útvonala ({project_path}) nem található a fájlrendszeren."
            
    project_imports = set()
    for root, dirs, files in os.walk(project_path):
        # Skip hidden directories like .git, .venv, node_modules etc. to speed up and avoid noise
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'venv', 'env', 'node_modules', 'target', 'build', 'dist', 'out')]
        
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.py'):
                file_imports = extract_imports_from_file(filepath)
                project_imports.update(file_imports)
            elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                file_imports = extract_js_ts_imports(filepath)
                project_imports.update(file_imports)
            elif file.endswith('.java'):
                file_imports = extract_java_imports(filepath)
                project_imports.update(file_imports)
    
    return sorted(list(project_imports))

@mcp.tool()
def get_file_extensions(project_name: str) -> list[str] | str:
    """
    Visszaadja a projektben található összes file kiterjesztést (az első pont utáni részt). Ha nincs pont a fájlban akkor az egész fájlnevet berakja.
    """
    projects = load_projects()
    project_map = {path.replace('\\', '/').rstrip('/').split('/')[-1]: path for path in projects}
    
    if project_name not in project_map:
        return f"Hiba: A megadott projekt név '{project_name}' nem szerepel a konfigurált projektek között. Elérhető projektek: {list(project_map.keys())}"
        
    project_path = project_map[project_name]
    if not os.path.exists(project_path):
        return f"Hiba: A megadott projekt '{project_name}' útvonala ({project_path}) nem található a fájlrendszeren."
            
    extensions = set()
    for root, dirs, files in os.walk(project_path):
        # Skip hidden directories like .git, .venv, etc. to speed up and avoid noise
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'venv', 'env')]
        
        for file in files:
            # Az első pont utáni rész, ha nincs pont a fájlban akkor az egész fájlnevet berakja
            if '.' in file:
                ext = file.split('.', 1)[1]
            else:
                ext = file
                
            if ext:
                extensions.add(ext)
                    
    return sorted(list(extensions))

if __name__ == "__main__":
    asyncio.run(mcp.run_http_async(transport='streamable-http', host='0.0.0.0', port=8001, json_response=True, stateless_http=True))
