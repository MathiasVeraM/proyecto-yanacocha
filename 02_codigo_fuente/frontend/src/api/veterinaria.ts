import { request } from './http'
import type {
  Diagnostico,
  DiagnosticoCreate,
  DiagnosticoUpdate,
  SignosVitalesHistorial,
  Tratamiento,
  TratamientoCreate,
  TratamientoUpdate,
} from '@/types/veterinaria'

const URL = '/api/animales'

export const veterinariaApi = {
  listarDiagnosticos: (idAnimal: number) =>
    request<Diagnostico[]>('GET', `${URL}/${idAnimal}/diagnosticos`),

  listarSignosVitales: (idAnimal: number) =>
    request<SignosVitalesHistorial[]>('GET', `${URL}/${idAnimal}/signos-vitales`),

  crearDiagnostico: (idAnimal: number, datos: DiagnosticoCreate) =>
    request<Diagnostico>('POST', `${URL}/${idAnimal}/diagnosticos`, datos),

  actualizarDiagnostico: (id: number, datos: DiagnosticoUpdate) =>
    request<Diagnostico>('PUT', `${URL}/diagnosticos/${id}`, datos),

  listarTratamientos: (idDiagnostico: number) =>
    request<Tratamiento[]>('GET', `${URL}/diagnosticos/${idDiagnostico}/tratamientos`),

  crearTratamiento: (idDiagnostico: number, datos: TratamientoCreate) =>
    request<Tratamiento>('POST', `${URL}/diagnosticos/${idDiagnostico}/tratamientos`, datos),

  actualizarTratamiento: (id: number, datos: TratamientoUpdate) =>
    request<Tratamiento>('PUT', `${URL}/tratamientos/${id}`, datos),
}
