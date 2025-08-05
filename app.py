
import streamlit as st
import fitz  # PyMuPDF
import re
import zipfile
from io import BytesIO

def extraer_datos(texto):
    mes_match = re.search(r'Mes:\s+(\w+)', texto)
    mes = mes_match.group(1).lower() if mes_match else "mes"

    rut_match = re.search(r'Rut:\s+([0-9\.]+-[0-9kK])', texto)
    rut = rut_match.group(1).replace('.', '') if rut_match else "RUT"

    lineas = texto.splitlines()
    nombre = "NOMBRE_COMPLETO"
    for idx, linea in enumerate(lineas):
        if "Mes:" in linea:
            for j in range(1, 4):
                if idx + j < len(lineas):
                    posible_nombre = lineas[idx + j].strip()
                    if posible_nombre and len(posible_nombre.split()) >= 2 and "rut" not in posible_nombre.lower():
                        nombre = posible_nombre
                        break
            break

    nombre_final = f"LIQUIDACIONES_{mes}_{rut}_{nombre.upper().replace(' ', '_')}.pdf"
    return nombre_final, lineas

def procesar_pdf(pdf_file, mostrar_texto=False):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    buffer_zip = BytesIO()
    textos_extraidos = []

    with zipfile.ZipFile(buffer_zip, "w") as zipf:
        for i, page in enumerate(doc, start=1):
            texto = page.get_text()
            nombre_archivo, lineas = extraer_datos(texto)
            nombre_ordenado = f"{i:02}_{nombre_archivo}"  # Mantiene orden original

            if mostrar_texto:
                texto_numerado = "\n".join([f"{idx+1:02}: {line}" for idx, line in enumerate(lineas)])
                textos_extraidos.append((nombre_ordenado, texto_numerado))

            pdf_individual = fitz.open()
            pdf_individual.insert_pdf(doc, from_page=i-1, to_page=i-1)
            pdf_bytes = pdf_individual.write()
            zipf.writestr(nombre_ordenado, pdf_bytes)

    buffer_zip.seek(0)
    return buffer_zip, textos_extraidos

st.set_page_config(page_title="Separador de Liquidaciones", page_icon="📄")
st.title("📄 Separador de Liquidaciones PDF")
st.write("Sube un archivo PDF con múltiples liquidaciones y obtén un ZIP con un PDF por trabajador.")

archivo = st.file_uploader("📤 Sube el archivo PDF", type=["pdf"])
mostrar_texto = st.checkbox("🔍 Mostrar texto extraído por página (con números de línea)")

if archivo:
    with st.spinner("🔍 Procesando archivo..."):
        zip_resultado, textos_extraidos = procesar_pdf(archivo, mostrar_texto=mostrar_texto)
        st.success("✅ ¡Proceso completo!")

        st.download_button(
            label="⬇️ Descargar ZIP con liquidaciones",
            data=zip_resultado,
            file_name="LIQUIDACIONES_SEPARADAS.zip",
            mime="application/zip"
        )

        if mostrar_texto:
            st.subheader("📝 Texto extraído por página")
            for i, (nombre_archivo, texto) in enumerate(textos_extraidos, start=1):
                st.markdown(f"**Página {i}: {nombre_archivo}**")
                st.text(texto)
