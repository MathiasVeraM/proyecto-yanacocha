"""Generación de códigos únicos de animal con formato YC-AAAA-NNNN."""
import re
import unicodedata


def iniciales(nombre_cientifico: str) -> str:
    # Se conserva para validar que el nombre científico tenga letras
    sin_tildes = unicodedata.normalize("NFKD", nombre_cientifico).encode("ascii", "ignore").decode()
    palabras = re.findall(r"[A-Za-z]+", sin_tildes)
    return "".join(palabra[0].upper() for palabra in palabras)

def siguiente_codigo(prefijo: str, codigos_existentes: list[str]) -> str:
    # Se parte del número más alto y no del total, para no reutilizar códigos faltantes
    numeros = [
        int(codigo.rsplit("-", 1)[1])
        for codigo in codigos_existentes
        if codigo.startswith(f"{prefijo}-") and codigo.rsplit("-", 1)[1].isdigit()
    ]
    return f"{prefijo}-{max(numeros, default=0) + 1:04d}"
