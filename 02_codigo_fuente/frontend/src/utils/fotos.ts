// Reduce la fotografía en el navegador antes de subirla.
//
// Una foto de celular pesa 3-8 MB; reducida a 1600 px en WEBP queda en ~150-300 KB.
// Como la foto se guarda en la base de datos (remota), cada descarga es mucho más rápida
// y la base crece mucho menos. Además, al volver a dibujarla se descartan los metadatos
// EXIF (por ejemplo, la ubicación GPS del teléfono). El servidor sigue validando el tipo
// y el tamaño del archivo igual que antes.

// Lado mayor máximo: suficiente para ver al ejemplar y lesiones visibles en la ficha
const LADO_MAXIMO = 1600
const CALIDAD_WEBP = 0.82
const CALIDAD_JPEG = 0.85

function aBlob(canvas: HTMLCanvasElement, tipo: string, calidad: number) {
  return new Promise<Blob | null>((resolver) => canvas.toBlob(resolver, tipo, calidad))
}

/**
 * Devuelve la foto reducida (WEBP, o JPEG si el navegador no sabe generar WEBP).
 * Si algo falla, devuelve el archivo original para no impedir la subida.
 */
export async function optimizarFoto(archivo: File): Promise<File> {
  let imagen: ImageBitmap | null = null
  try {
    // Respeta la orientación con la que se tomó la foto (fotos verticales de celular)
    imagen = await createImageBitmap(archivo, { imageOrientation: 'from-image' })
    const escala = Math.min(1, LADO_MAXIMO / Math.max(imagen.width, imagen.height))
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(imagen.width * escala)
    canvas.height = Math.round(imagen.height * escala)
    const contexto = canvas.getContext('2d')
    if (!contexto) return archivo
    contexto.imageSmoothingQuality = 'high'
    contexto.drawImage(imagen, 0, 0, canvas.width, canvas.height)

    let blob = await aBlob(canvas, 'image/webp', CALIDAD_WEBP)
    // Algunos navegadores (Safari antiguo) devuelven PNG cuando no soportan WEBP
    if (!blob || blob.type !== 'image/webp') blob = await aBlob(canvas, 'image/jpeg', CALIDAD_JPEG)
    if (!blob) return archivo

    const extension = blob.type === 'image/webp' ? 'webp' : 'jpg'
    const nombre = `${archivo.name.replace(/\.[^.]+$/, '') || 'foto'}.${extension}`
    return new File([blob], nombre, { type: blob.type, lastModified: Date.now() })
  } catch {
    return archivo
  } finally {
    imagen?.close()
  }
}
