from sqlalchemy.orm import Session

from src.repositorios.listas_referencia_repo import ListasReferenciaRepository


class ReferenciasService:
    @staticmethod
    def planificacion(db: Session) -> dict:
        """Listas de referencia de Planificación: ejemplares, recintos y usuarios."""
        recintos: dict[int, dict] = {}
        animales_fila = []
        usuarios = []
        for fila in ListasReferenciaRepository.obtener_todas(db):
            if fila.tipo == "recinto":
                recintos[fila.id] = {
                    "id_recinto": fila.id,
                    "nombre_recinto": fila.t1,
                    "tipo": fila.t2,
                    "estado": fila.t3,
                    "capacidad": fila.n1,
                }
            elif fila.tipo == "animal":
                animales_fila.append(fila)
            else:
                usuarios.append(
                    {
                        "id_usuario": fila.id,
                        "nombre": fila.t1,
                        "apellido": fila.t2,
                        # NULL se trata como activo (el valor por defecto de la cuenta)
                        "activo": True if fila.n1 is None else bool(fila.n1),
                    }
                )

        animales = [
            {
                "id_animal": fila.id,
                "codigo_animal": fila.t1,
                "nombre": fila.t2,
                "estado_actual": fila.t3,
                "id_taxonomia": fila.n1,
                "id_recinto": fila.n2,
                "taxonomia": {
                    "id_taxonomia": fila.n1,
                    "nombre_comun": fila.t4,
                    "especie": fila.t5,
                    "clase": fila.t6,
                },
                "recinto": recintos[fila.n2],
            }
            # El recinto siempre existe (clave foránea); se omite cualquier dato huérfano
            for fila in animales_fila
            if fila.n2 in recintos
        ]
        # Mismo orden que los listados originales: ejemplares por código, recintos por nombre
        animales.sort(key=lambda animal: animal["codigo_animal"])
        usuarios.sort(key=lambda usuario: (usuario["apellido"].lower(), usuario["nombre"].lower()))
        return {
            "animales": animales,
            "recintos": sorted(recintos.values(), key=lambda recinto: recinto["nombre_recinto"]),
            "usuarios": usuarios,
        }
