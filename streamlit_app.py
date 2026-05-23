import streamlit as st
import threading
import builtins
import io
import time
import asyncio
import os
import yaml
import sys

# Fájl útvonalak
USER_INPUT_PATH = "user_input.txt"
PROJECTS_YAML_PATH = "mcp/developer_stack_finder/local_projects.yaml"

st.set_page_config(page_title="Job Agent - Natív Web UI", layout="wide")

# Globális állapot a szálak közötti kommunikációhoz
class AppState:
    def __init__(self):
        self.prompt = None
        self.answer = None
        self.event = threading.Event()
        self.logs = ""
        self.is_running = False

# Állapot inicializálása (csak egyszer fut le)
if 'app_state' not in st.session_state:
    st.session_state.app_state = AppState()
if 'page' not in st.session_state:
    st.session_state.page = 'run'

# Eredeti függvények megőrzése (globális térben, hogy a háttérszál is elérje)
if not hasattr(builtins, "__original_input__"):
    builtins.__original_input__ = builtins.input
if not hasattr(builtins, "__original_print__"):
    builtins.__original_print__ = builtins.print

REAL_INPUT = builtins.__original_input__
REAL_PRINT = builtins.__original_print__

app_state = st.session_state.app_state

def custom_input(prompt=""):
    # Megjelenítjük a promptot a felületen ÉS beírjuk a logokba is, hogy látszódjon a "konzolban"
    app_state.logs += prompt
    app_state.prompt = prompt
    app_state.event.clear()
    
    # Blokkoljuk a szálat, amíg a felhasználó a felületen rá nem nyom a "Küldés" gombra
    app_state.event.wait()
    
    ans = app_state.answer
    # Visszaállítjuk az állapotot a következő inputig
    app_state.prompt = None
    app_state.answer = None
    return ans

def custom_print(*args, **kwargs):
    sio = io.StringIO()
    # Ha volt 'file' argumentum (pl sys.stderr), azt nem bántjuk
    if 'file' not in kwargs or kwargs['file'] in (sys.stdout, None):
        # 1. Elmentjük a memóriába
        kwargs_capture = kwargs.copy()
        kwargs_capture['file'] = sio
        REAL_PRINT(*args, **kwargs_capture)
        app_state.logs += sio.getvalue()
        
        # 2. Kiírjuk a valódi konzolra is (debug)
        kwargs_real = kwargs.copy()
        kwargs_real['file'] = sys.stdout
        REAL_PRINT(*args, **kwargs_real)
    else:
        REAL_PRINT(*args, **kwargs)

def run_background_task():
    # Eltérítjük a beépített függvényeket ezen a szálon (ami globálisan hat a Python futásra)
    builtins.input = custom_input
    builtins.print = custom_print
    app_state.is_running = True
    
    try:
        import main
        # Ha többször futtatjuk, a modul már be van töltve, így közvetlenül hívhatjuk
        asyncio.run(main.main())
    except Exception as e:
        app_state.logs += f"\n[Hiba]: {e}\n"
    finally:
        app_state.is_running = False
        app_state.prompt = None # Ha esetleg megszakadt egy input közben
        # Visszaállítjuk az eredeti függvényeket
        builtins.input = REAL_INPUT
        builtins.print = REAL_PRINT

def go_to_config():
    st.session_state.page = 'config'

def go_to_run():
    st.session_state.page = 'run'

# --- KONFIGURÁCIÓS OLDAL ---
if st.session_state.page == 'config':
    st.title("⚙️ Konfiguráció")
    st.button("⬅️ Vissza a futtatáshoz", on_click=go_to_run)
    
    if os.path.exists(USER_INPUT_PATH):
        with open(USER_INPUT_PATH, "r", encoding="utf-8") as f:
            current_user_input = f.read()
    else:
        current_user_input = ""

    current_projects = []
    if os.path.exists(PROJECTS_YAML_PATH):
        with open(PROJECTS_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "projects" in data:
                current_projects = data["projects"]
    projects_text = "\n".join(current_projects)

    col1, col2 = st.columns(2)

    with col1:
        st.header("👤 Felhasználói Profil")
        new_user_input = st.text_area("Profil leírása:", value=current_user_input, height=400)
        
        if st.button("💾 Profil Mentése", type="primary"):
            with open(USER_INPUT_PATH, "w", encoding="utf-8") as f:
                f.write(new_user_input)
            st.success("Sikeresen mentve!")

    with col2:
        st.header("📁 Lokális Projektek")
        new_projects_text = st.text_area("Projekt útvonalak:", value=projects_text, height=400)
        
        if st.button("💾 Projektek Mentése", type="primary"):
            lines = [line.strip() for line in new_projects_text.split('\n') if line.strip()]
            yaml_data = {"projects": lines}
            os.makedirs(os.path.dirname(PROJECTS_YAML_PATH), exist_ok=True)
            with open(PROJECTS_YAML_PATH, "w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
            st.success("Projektek sikeresen mentve!")

# --- FUTTATÁS OLDAL ---
elif st.session_state.page == 'run':
    st.title("🤖 Job Agent - Natív Web UI")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.button("⚙️ Konfiguráció megnyitása", on_click=go_to_config)
        st.write("---")
        
        if st.button("🚀 Agent Indítása", type="primary"):
            if not app_state.is_running:
                app_state.logs = ""
                # Daemon szálat indítunk, hogy ne tartsa életben a programot, ha leállítjuk
                t = threading.Thread(target=run_background_task)
                t.daemon = True
                t.start()
                st.rerun()
                
        if app_state.is_running:
            st.warning("⏳ Az ágens fut...")
            st.caption("A háttérben dolgoznak az LLM modellek és szerverek.")
        else:
            st.info("ℹ️ Az ágens jelenleg nem fut.")

    with col2:
        st.markdown("**Terminál Kimenet (Logok és Eredmények)**")
        # st.code használata st.text_area helyett, mert a text_area Streamlit alatt beragadhat, ha változik a tartalma
        st.code(app_state.logs if app_state.logs else "Várakozás az indításra...", language="markdown")
        
        # Ha a háttérszál vár egy inputra (akár MCP Elicit, akár main.py prompt)
        if app_state.prompt is not None:
            st.markdown(f"**Kérdés a rendszertől / ágenstől:**\n*{app_state.prompt}*")
            
            # Form használata, hogy az Enter megnyomására is elküldje és utána kiürüljön
            with st.form(key="input_form", clear_on_submit=True):
                user_response = st.text_input("Válaszod (pl. y/n, vagy a kért adat):")
                submit_button = st.form_submit_button(label="Küldés")
                
                if submit_button:
                    # Rögzítjük a választ a naplóban a jobb áttekinthetőségért
                    app_state.logs += f"\n> {user_response}\n\n"
                    # Átadjuk az értéket és felébresztjük a szálat
                    app_state.answer = user_response
                    app_state.event.set()
                    st.rerun()

    # Automatikus frissítés beállítása, ha fut az ágens és épp NEM vár inputra.
    # Ha vár inputra, MEGÁLLÍTJUK a frissítést, így a szövegmező sosem veszíti el a fókuszt gépelés közben!
    if app_state.is_running and app_state.prompt is None:
        time.sleep(1.0)
        st.rerun()
