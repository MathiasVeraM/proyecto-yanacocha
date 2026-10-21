"""Generación del código único del animal a partir de su nombre científico (ej. Canis lupus familiaris -> CLF-001)."""
import re
import unicodedata

def iniciales(nombre_cientifico: str) -> str:
    # Se quitan tildes y signos para que el código solo tenga letras A-Z
    sin_tildes = unicodedata.normalize("NFKD", nombre_cientifico).encode("ascii", "ignore").decode()
    palabras = re.findall(r"[A-Za-z]+", sin_tildes)
    return "".join(palabra[0].upper() for palabra in palabras)

def siguiente_codigo(prefijo: str, codigos_existentes: list[str]) -> str:
    # Se parte del número más alto y no del total, para no repetir un código aunque falte alguno
    numeros = [
        int(codigo.split("-", 1)[1])
        for codigo in codigos_existentes
        if codigo.startswith(f"{prefijo}-") and codigo.split("-", 1)[1].isdigit()
    ]
    return f"{prefijo}-{max(numeros, default=0) + 1:03d}"
