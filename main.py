import flet as ft
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

def procesar_terremoto_con_buscador(url, termino, chrome_options, callback_progreso):
    """Procesamiento especial para la primera página usando su propio buscador interno"""
    resultados_sitio = []
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(4) # Espera a que cargue la página inicial
        
        callback_progreso(0.2, "Utilizando el buscador interno de Terremoto Venezuela...")
        
        # Localizamos el cuadro de búsqueda de la página web usando XPATHs comunes para inputs de búsqueda
        buscador_web = None
        selectores_busqueda = [
            "//input[@type='search']",
            "//input[contains(@placeholder, 'buscar') or contains(@placeholder, 'Buscar') or contains(@placeholder, 'search')]",
            "//input[@id='search' or @name='search']"
        ]
        
        for selector in selectores_busqueda:
            try:
                buscador_web = driver.find_element(By.XPATH, selector)
                if buscador_web:
                    break
            except:
                continue
                
        if buscador_web:
            # Limpiamos el campo, escribimos el nombre y ejecutamos la búsqueda
            buscador_web.clear()
            buscador_web.send_keys(termino)
            buscador_web.send_keys(Keys.ENTER)
            time.sleep(3.5) # Esperamos a que la tabla se actualice con el filtro
            
            callback_progreso(0.4, "Analizando los resultados filtrados...")
            
            # Capturamos el HTML filtrado y extraemos la información
            html_filtrado = driver.page_source
            soup = BeautifulSoup(html_filtrado, "html.parser")
            
            # Buscamos en las filas de la tabla (td) o contenedores de texto
            for tag in soup.find_all(['td', 'h3', 'h4', 'div', 'p', 'span', 'li']):
                texto = tag.get_text().strip()
                if termino in texto.lower() and 3 < len(texto) < 250:
                    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
                    texto_limpio = " | ".join(lineas)
                    
                    fmt_resultado = f"[Terremoto Venezuela] {texto_limpio}"
                    if fmt_resultado not in resultados_sitio:
                        resultados_sitio.append(fmt_resultado)
        else:
            print("No se localizó el cuadro de búsqueda en la página, se intentará lectura directa.")
            
    except Exception as e:
        print(f"Error en Terremoto Venezuela: {e}")
    finally:
        if driver:
            driver.quit()
            
    return resultados_sitio

def procesar_venezuela_te_busca(url, termino, chrome_options, callback_progreso, porcentaje_base):
    """Mantiene el método de expansión por botón para la segunda página"""
    resultados_sitio = []
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(4)
        
        max_clics = 12 
        for intento in range(max_clics):
            callback_progreso(
                porcentaje_base + (intento / max_clics) * 0.4, 
                f"Desplegando registros ocultos en Venezuela Te Busca (Paso {intento+1}/{max_clics})..."
            )
            try:
                botones = driver.find_elements(
                    By.XPATH, 
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'cargar') or contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'ver') or contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'more')] | "
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'cargar') or contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'ver')]"
                )
                if botones:
                    driver.execute_script("arguments[0].click();", botones[0])
                    time.sleep(2.5)
                else:
                    break
            except:
                break
        
        callback_progreso(porcentaje_base + 0.4, "Analizando la lista completa de Venezuela Te Busca...")
        html_expandido = driver.page_source
        soup = BeautifulSoup(html_expandido, "html.parser")
        
        for tag in soup.find_all(['h3', 'h4', 'div', 'p', 'span', 'td', 'li', 'a']):
            texto = tag.get_text().strip()
            if termino in texto.lower() and 3 < len(texto) < 250:
                lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
                texto_limpio = " | ".join(lineas)
                
                fmt_resultado = f"[Venezuela Te Busca] {texto_limpio}"
                if fmt_resultado not in resultados_sitio:
                    resultados_sitio.append(fmt_resultado)
                    
    except Exception as e:
        print(f"Error en Venezuela Te Busca: {e}")
    finally:
        if driver:
            driver.quit()
            
    return resultados_sitio

def buscar_en_paginas(termino_busqueda, callback_progreso):
    termino = termino_busqueda.lower().strip()
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # --- PASO 1: PRIORIDAD CON EL BUSCADOR INTERNO ---
    callback_progreso(0.0, "Conectando a Terremoto Venezuela...")
    resultados = procesar_terremoto_con_buscador(
        url="https://desaparecidosterremotovenezuela.com/",
        termino=termino,
        chrome_options=chrome_options,
        callback_progreso=callback_progreso
    )
    
    # --- PASO 2: CONDICIONAL SINO CONSIGUE ALLÍ ---
    if resultados:
        callback_progreso(1.0, "Coincidencia encontrada en el portal prioritario.")
        return resultados
        
    # Si no encontró nada, salta a la segunda página usando clics automáticos
    callback_progreso(0.5, "No se hallaron registros en el primer portal. Conectando a Venezuela Te Busca...")
    resultados = procesar_venezuela_te_busca(
        url="https://venezuelatebusca.com/",
        termino=termino,
        chrome_options=chrome_options,
        callback_progreso=callback_progreso,
        porcentaje_base=0.5
    )
    
    callback_progreso(1.0, "Búsqueda secuencial finalizada.")
    return resultados

def main(page: ft.Page):
    page.title = "Búsqueda Integral de Desaparecidos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    txt_busqueda = ft.TextField(
        label="Nombre, Apellido o Cédula", 
        width=350,
        hint_text="Ej. Andreina"
    )
    
    lv_resultados = ft.ListView(
        expand=True, 
        spacing=10, 
        padding=20, 
        auto_scroll=False
    )
    
    pb_progreso = ft.ProgressBar(width=350, value=0, visible=False, color=ft.Colors.BLUE)
    txt_estado = ft.Text("", size=12, italic=True, color=ft.Colors.GREY_600, visible=False)

    def callback_progreso(valor, texto):
        pb_progreso.value = valor
        txt_estado.value = texto
        page.update()

    def hilo_busqueda(termino):
        coincidencias = buscar_en_paginas(termino, callback_progreso)
        
        pb_progreso.visible = False
        txt_estado.visible = False
        btn_buscar.disabled = False
        
        if coincidencias:
            for item in coincidencias:
                lv_resultados.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Text(item, size=14),
                            padding=15
                        )
                    )
                )
        else:
            lv_resultados.controls.append(
                ft.Text("No se encontraron coincidencias en ninguna plataforma.", color=ft.Colors.RED, size=16)
            )
        page.update()

    def realizar_busqueda(e):
        if not txt_busqueda.value.strip():
            txt_busqueda.error_text = "Por favor ingresa un término"
            page.update()
            return
        
        txt_busqueda.error_text = None
        lv_resultados.controls.clear()
        
        pb_progreso.visible = True
        txt_estado.visible = True
        pb_progreso.value = 0
        txt_estado.value = "Iniciando motores de búsqueda secuencial..."
        btn_buscar.disabled = True 
        page.update()

        t = threading.Thread(target=hilo_busqueda, args=(txt_busqueda.value,))
        t.start()

    btn_buscar = ft.FilledButton("Buscar en Sitios", on_click=realizar_busqueda, width=200)

    page.add(
        ft.Image(
            src="bandera.png",
            width=120,
            height=80,
            fit="contain",
        ),
        ft.Text("Búsqueda Integral de Desaparecidos", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        ft.Container(
            content=ft.Text(
                'Mateo 7:7 "Pedid, y se os dará; buscad, y hallaréis; llamad, y se os abrirá."',
                size=13,
                italic=True,
                color=ft.Colors.GREY_700,
                text_align=ft.TextAlign.CENTER
            ),
            padding=15 
        ),
        ft.Divider(),
        txt_busqueda,
        btn_buscar,
        ft.Container(content=pb_progreso, padding=10),
        ft.Container(content=txt_estado, padding=5),
        ft.Text("Resultados:", size=16, weight=ft.FontWeight.W_500),
        ft.Container(
            content=lv_resultados, 
            height=350, 
            width=380, 
            border=ft.Border.all(1, ft.Colors.BLACK_12), 
            border_radius=8
        ),
        ft.Divider(),
        ft.Container(
            content=ft.Text(
                'Salmo 46:1 "Dios es nuestro amparo y fortaleza, nuestro pronto auxilio en las tribulaciones."',
                size=13,
                italic=True,
                color=ft.Colors.GREY_700,
                text_align=ft.TextAlign.CENTER
            ),
            padding=15
        ),
        ft.Container(
            content=ft.Text(
                "Version 1.0 - Desarrollado por @bastidaslucio sin fines de lucro",
                size=10,
                color=ft.Colors.GREY_500,
                text_align=ft.TextAlign.RIGHT
            ),
            alignment=ft.Alignment(1.0, 1.0),
            width=380,
            padding=10
        )
    )

ft.run(main)