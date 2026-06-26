import flet as ft
import time
import threading
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# --- FUNCIONES DE SCRAPING (MANTENIDAS) ---
def procesar_terremoto_con_buscador(url, termino, chrome_options, callback_progreso):
    resultados_sitio = []
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(4)
        callback_progreso(0.2, "Utilizando buscador interno...")
        
        buscador_web = None
        selectores_busqueda = ["//input[@type='search']", "//input[contains(@placeholder, 'buscar')]", "//input[@id='search']"]
        
        for selector in selectores_busqueda:
            try:
                buscador_web = driver.find_element(By.XPATH, selector)
                if buscador_web: break
            except: continue
                
        if buscador_web:
            buscador_web.clear()
            buscador_web.send_keys(termino)
            buscador_web.send_keys(Keys.ENTER)
            time.sleep(3.5)
            callback_progreso(0.4, "Analizando resultados...")
            html_filtrado = driver.page_source
            soup = BeautifulSoup(html_filtrado, "html.parser")
            for tag in soup.find_all(['td', 'h3', 'div', 'p', 'span']):
                texto = tag.get_text().strip()
                if termino in texto.lower() and 3 < len(texto) < 250:
                    fmt_resultado = f"[Terremoto] {texto}"
                    if fmt_resultado not in resultados_sitio: resultados_sitio.append(fmt_resultado)
    except Exception as e: print(f"Error: {e}")
    finally:
        if driver: driver.quit()
    return resultados_sitio

def procesar_venezuela_te_busca(url, termino, chrome_options, callback_progreso, porcentaje_base):
    resultados_sitio = []
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(4)
        max_clics = 5 # Reducido para evitar timeout en servidores gratuitos
        for intento in range(max_clics):
            callback_progreso(porcentaje_base + (intento / max_clics) * 0.4, "Desplegando registros...")
            try:
                botones = driver.find_elements(By.XPATH, "//button[contains(text(), 'cargar')]")
                if botones:
                    driver.execute_script("arguments[0].click();", botones[0])
                    time.sleep(2)
                else: break
            except: break
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(['div', 'p', 'span', 'li']):
            texto = tag.get_text().strip()
            if termino in texto.lower() and 3 < len(texto) < 250:
                fmt_resultado = f"[VzlaTeBusca] {texto}"
                if fmt_resultado not in resultados_sitio: resultados_sitio.append(fmt_resultado)
    finally:
        if driver: driver.quit()
    return resultados_sitio

def buscar_en_paginas(termino_busqueda, callback_progreso):
    termino = termino_busqueda.lower().strip()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    resultados = procesar_terremoto_con_buscador("https://desaparecidosterremotovenezuela.com/", termino, chrome_options, callback_progreso)
    if not resultados:
        resultados = procesar_venezuela_te_busca("https://venezuelatebusca.com/", termino, chrome_options, callback_progreso, 0.5)
    return resultados

# --- INTERFAZ (MANTENIDA Y ADAPTADA) ---
def main(page: ft.Page):
    page.title = "Búsqueda Integral"
    page.scroll = ft.ScrollMode.AUTO
    
    txt_busqueda = ft.TextField(label="Nombre o Cédula", width=350)
    lv_resultados = ft.ListView(expand=True, spacing=10)
    pb_progreso = ft.ProgressBar(width=350, visible=False)
    txt_estado = ft.Text("", visible=False)

    def callback_progreso(valor, texto):
        pb_progreso.value = valor
        txt_estado.value = texto
        page.update()

    def realizar_busqueda(e):
        pb_progreso.visible = True
        txt_estado.visible = True
        btn_buscar.disabled = True
        lv_resultados.controls.clear()
        
        def hilo_busqueda():
            coincidencias = buscar_en_paginas(txt_busqueda.value, callback_progreso)
            pb_progreso.visible = False
            txt_estado.visible = False
            btn_buscar.disabled = False
            for item in coincidencias:
                lv_resultados.controls.append(ft.Card(content=ft.Container(content=ft.Text(item), padding=10)))
            page.update()
            
        threading.Thread(target=hilo_busqueda).start()

    btn_buscar = ft.FilledButton("Buscar", on_click=realizar_busqueda)
    page.add(ft.Text("Búsqueda de Desaparecidos", size=20), txt_busqueda, btn_buscar, pb_progreso, txt_estado, lv_resultados)

# --- LANZAMIENTO PARA NUBE (CRÍTICO) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, port=port, view=ft.AppView.WEB_BROWSER)
