from typing import Any
from fastmcp import Context, FastMCP
from pydantic_ai import Agent
from pydantic_ai.models.mcp_sampling import MCPSamplingModel
from pydantic import BaseModel, Field
import asyncio

mcp = FastMCP('CV Writer')
server_agent = Agent(instructions='Egy cv író asszisztens vagy. A feladatod, hogy megírd az egyes szekciókhoz a CV-be illő szöveget magyar nyelven a megadott adatok alapján.')
#You are a CV writer assistant. You will write the specific sections of a CV for a specific job.
USER_INFO = ""
PROJECT_SUMMARIES = ""
JOB_DATA = {}
def get_write_context():
    prompt = f"A felhasználó által megadott adatok: {USER_INFO}\n"
    prompt = prompt + f"A felhasználó projektjeinek összefoglalója: {PROJECT_SUMMARIES}\n"
    prompt = prompt + f"A megcélzott pozíció adatai: {JOB_DATA}\n"
    return prompt

@mcp.prompt()
def cv_structure_prompt():
    """Defines the structure of the CV."""

    return """
    A CV a következő szekciókat tartalmazza:
    0. SZEMÉLYES ADATOK ÉS TITULUS (az áletrajz címe)
    1. CÉLKITŰZÉS (SUMMARY / OBJECTIVE)
    2. FŐBB ERŐSSÉGEK (CORE COMPETENCES / SKILLS IN CONTEXT)
    3. SZAKMAI TAPASZTALAT (WORK EXPERIENCE)
    4. TANULMÁNYOK (EDUCATION)
    5. EGYÉB (LANGUAGES & MISC)
    """
    

class UserData(BaseModel):
    name: str = Field(description="The full name", default="[NAME]")
    email: str = Field(description="The email address", default="[EMAIL_ADDRESS]")
    mobile: str = Field(description="The mobile number", default="[MOBILE]")
    linkedin_url: str = Field(description="The LinkedIn URL", default="[URL]")

@mcp.tool()
async def write_personal_data_section(context: Context, relevant_info: str):
    """
    With this tool you can write the personal data and title section of a CV.
    """
    
    result = await context.elicit(message="Please provide the information below, which will be used to write the personal data and title section of a CV.\n ", response_type=UserData)
    if result.data is None or result.action != "accept":
        result.data = UserData()
        
    model = MCPSamplingModel(session=context.session)
    prompt = f"""
    - Magyarázat: A név és az elérhetőségek mellett kötelező megadni egy pontos, célzott szakmai titulust, amely azonnal pozicionálja a jelentkezőt a munkaerőpiacon. A pozícionálás az önéletrajz szemponjából meghatározó. Ez lesz az áletrajz címe, ennek a szekciónak külön cím nem kell.
    - Elvárt adatok: Teljes név, Szakmai titulus, E-mail, Telefonszám, LinkedIn URL (vagy GitHub/Portfólió).
    - Megadott adatok: {result.data}. Mindig ezeket használd fel.
    - Minta:
      László Áron – AI produktfejlesztő magabiztos python ismeretekkel
      Email: [EMAIL_ADDRESS] | Telefon: [MOBILE] | LinkedIn: [URL]
    - A felhasználó által megadott adatok: {relevant_info}
    """
    result = await server_agent.run(prompt, model=model)
    return result.output

@mcp.tool()
async def write_objective_section(context: Context):
    """
    With this tool you can write the objective section of a CV.
    CÉLKITŰZÉS (SUMMARY / OBJECTIVE)
    """
    model = MCPSamplingModel(session=context.session)
    prompt = """
    írd meg a következő szerkciót:Célkkitűzés 
     - Magyarázat: 2-3 mondatos, sűrített összefoglaló. Nem sablonos frázisokat kell írni, hanem azt, hogy a jelentkező milyen konkrét technológiák/területek elmélyítésére törekszik, és hogyan kíván értéket teremteni a leendő vállalatnak.
    - Minta:
      Célom, hogy elmélyítsem a tudásom mesterséges intelligencia alapú megoldások, különösen a GenAI, CV, ML és LLM tervezésében és implementálásában, és aktívan támogassam, illetve részt vegyek AI alapú termékek és szolgáltatások fejlesztésében.
    """
    prompt = prompt + get_write_context()
    result = await server_agent.run(prompt, model=model)
    return result.output
    
@mcp.tool()
async def write_competences_section(context: Context):
    """
    With this tool you can write the competences section of a CV.
    FŐBB ERŐSSÉGEK (CORE COMPETENCES / SKILLS IN CONTEXT)
    """
    model = MCPSamplingModel(session=context.session)
    prompt = """
    - Magyarázat: A kulcsszavakat és technológiákat nem száraz listaként kell felsorolni, hanem kontextusba helyezve (honnan származik a tudás, milyen projektben lett alkalmazva). Ez bizonyítja a kompetencia mélységét.
    - Felépítés: Technológiai fókuszpont -> Konkrét kontextus (egyetem/projekt/cég) -> Eszközök -> Eredmény/Tapasztalat.
    - Minta:
      * Ismeretek gépi tanulás, neurális hálózatok és adatfeldolgozás terén: Információs rendszerek specializációm révén alapos elméleti és gyakorlati tudást szereztem az ML modellek működéséről, a fejlett adatfeldolgozási technikákról és a Python könyvtárak (Tensorflow, Pandas, Scikit-learn) használatáról. Egy képosztályozó projektben CNN implementációt és metrika-kiértékelést végeztem.
      * AI-fejlesztői könyvtárak ismerete: Az Artillence Kft.-vel való együttműködés során LLM-ek használatában, az OpenAI API, a Hugging Face és a Pydantic AI könyvtárak alkalmazásában szereztem gyakorlatot.
      * Haladó AI tudás: A BME alapozó kurzusai mellett a Karlsruhe-i Erasmus félév során emelt szintű AI modulokat (autoenkóderek, diffúziós modellek, NLP, GAN-ok, multimodális rendszerek) teljesítettem.
    """
    prompt = prompt + get_write_context()
    result = await server_agent.run(prompt, model=model)
    return result.output

@mcp.tool()
async def write_work_experience_section(context: Context):
    """
    With this tool you can write the work experience section of a CV.
    SZAKMAI TAPASZTALAT (WORK EXPERIENCE)
    """
    model = MCPSamplingModel(session=context.session)
    prompt = """
    - Magyarázat: Fordított időrendi sorrendben (legfrissebb az első). Minden munkahelynél meg kell adni a pozíciót, a cégnevet, az időszakot (évszámokkal), egy rövid (1 mondatos) cégismertetőt a kontextus miatt, valamint a legfőbb feladatokat és eredményeket, igékkel indítva.
    - Minta:
      AI engineer | Artillence Kft. (6 fős AI szoftverfejlesztő cég) | 2024 - 2025
      Főbb feladatok: Nagy nyelvi modellek (LLM) integrációja API-n keresztül Python környezetben, dokumentumfeldolgozásra és információ-kinyerésre. Munkafolyamatok dokumentálása, prezentációk megtartása. Szakdolgozati keretek között mikroszolgáltatás-alapú AI webalkalmazás fejlesztése.
      Szoftverfejlesztő | Evosoft Kft. (2000 fős Siemens leányvállalat) | 2023
      Főbb feladatok: Multiplayer játék fejlesztése 11 fős csapatban. Játékmenet-logika, háttérstruktúra megtervezése, kliens-szerver kommunikáció megvalósítása. Aktív részvétel agilis (Scrum) munkafolyamatokban.
    """
    prompt = prompt + get_write_context()
    result = await server_agent.run(prompt, model=model)
    return result.output
    

@mcp.tool()
async def write_education_section(context: Context):
    """
    With this tool you can write the education section of a CV.
    TANULMÁNYOK (EDUCATION)
    """
    model = MCPSamplingModel(session=context.session)
    prompt = """
    - Magyarázat: Szintén fordított időrendben. Tartalmazza az intézmény nevét, a képzés szintjét (BSc, MSc), a szakot, az időintervallumot, és az esetleges releváns külföldi vagy speciális rész-tanulmányokat (pl. Erasmus).
    - Minta:
      * Budapesti Műszaki és Gazdaságtudományi Egyetem (2022 - 2026) – Villamosmérnöki és Informatikai Kar, Mérnökinformatikus BSc
      * Karlsruhe Institute of Technology (2025) – Erasmus félév (német nyelvű képzés keretében)
    """
    prompt = prompt + get_write_context()
    result = await server_agent.run(prompt, model=model)
    return result.output

@mcp.tool()
async def write_other_section(context: Context):
    """
    With this tool you can write the other section of a CV.
    """
    model = MCPSamplingModel(session=context.session)
    prompt = """
    - Magyarázat: Nyelvtudás pontos szintmegjelöléssel (nem csak felsorolva), valamint a pozíció szempontjából releváns egyéb készségek (pl. jogosítvány, ha szükséges a mobilitáshoz).
    - Minta:
      * Angol-német nyelvismeret: Aktív társalgási szint szóban és írásban
      * Vezetői engedély: B kategória
    """
    prompt = prompt + get_write_context()
    result = await server_agent.run(prompt, model=model)
    return result.output

@mcp.prompt()
def cv_generator_prompt(job:dict[str, Any],user_info:str, project_summaries:str):
    prompt=f"""
    A következő adatok alalpján készítsd el a CV-t.
    A pozíció neve: {job['title']}
    Cég: {job['company']}
    Pozíció leírása: {job['description']}
    A felhasználó által szolgáltatott információk: {user_info}
    A felhasználó által szolgáltatott projektek összefogalalója: {project_summaries}
    """
    global USER_INFO
    USER_INFO = user_info
    global PROJECT_SUMMARIES
    PROJECT_SUMMARIES = project_summaries
    global JOB_DATA
    JOB_DATA = {
        "title": job['title'],
        "company": job['company'],
        "description": job['description']
    }
    return prompt


@mcp.prompt()
def cv_check_critiera_prompt():
    """
    KRITÉRIUMRENDSZER (Ezek alapján vizsgáld a CV-t):

1. Személyes adatok és pozicionálás
- Van-e egyértelmű, célzott szakmai titulus a név mellett (pl. "AI produktfejlesztő német nyelvtudással")?
- Az elérhetőségek (e-mail, telefon, LinkedIn) hiánytalanul megvannak-e? Nincsenek-e felesleges adatok (pl. pontos lakcím, születési dátum, ha nem szükséges)?

2. Célkitűzés (Összefoglaló)
- Konkrét, sűrített és szakmai a megfogalmazás? 
- Kerüli a sablonos, üres frázisokat (pl. "kihívásokat keresek", "jó csapatjátékos")? 
- Világosan kiderül belőle, hogy a jelentkező milyen technológiákra fókuszál és milyen értéket hoz a cégnek?

3. Főbb erősségek és kompetenciák (Kontextusvizsgálat)
- A készségek és technológiák (pl. Python könyvtárak, AI modellek) kontextusba vannak helyezve? (Kritérium: Nem lehet száraz kulcsszólista! Minden technológiához kapcsolódnia kell egy egyetemi projektnek, munkahelynek vagy konkrét feladatnak, ami igazolja a tudást.)
- Relevánsak a felsorolt erősségek a megcélzott pozíció szempontjából?

4. Szakmai tapasztalat (Struktúra és tartalom)
- Fordított időrendben vannak a munkahelyek?
- Tartalmaz minden pont céget, pozíciót, évszámot?
- Van-e rövid (1 mondatos) kontextus a cégekről (pl. hány fős cég, mivel foglalkozik), hogy érthető legyen a lépték?
- A feladatok leírása cselekvő igékkel kezdődik? Elég specifikusak a feladatok, vagy túl általánosak?

5. Tanulmányok és nyelvtudás
- Fordított időrendben vannak az iskolák? Tartalmazza a szakot és a kar/intézmény nevét?
- A nyelvtudás szintje egyértelműen meg van határozva (pl. "aktív társalgási szint szóban és írásban") ahelyett, hogy csak fel lenne sorolva a nyelv neve?

6. Nyelvezet, formázás és logika
- Egységes és professzionális a hangnem?
- Nincsenek-e benne elgépelések, helyesírási vagy formázási hibák (pl. szétcsúszott tabulátorok, hiányzó szóközök)?
- Logikus az információk áramlása?
    """


if __name__ == "__main__":
    mcp.run(
        transport='sse',
        host='0.0.0.0',
        port=8002,
        json_response=True,
    )
