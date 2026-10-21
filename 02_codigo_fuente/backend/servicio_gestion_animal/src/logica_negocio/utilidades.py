def datos_a_actualizar(esquema, campos_obligatorios: set) -> dict:
    """Campos enviados por el cliente; los obligatorios no aceptan null."""
    datos = esquema.model_dump(exclude_unset=True)
    return {k: v for k, v in datos.items() if v is not None or k not in campos_obligatorios}
