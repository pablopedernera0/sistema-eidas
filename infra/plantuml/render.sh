#!/usr/bin/env bash
# Genera en SVG todos los .puml de un grupo (o de una carpeta cualquiera) con la CLI de
# PlantUML en Docker. No hace falta tener Java ni Graphviz instalados, ni que el repo sea
# público: lee los archivos locales.
#
# Uso:
#   ./render.sh <materia> <grupo-id>     ej: ./render.sh af-diseno-sistemas-web-32 portal-financiero
#   ./render.sh <carpeta>                 ej: ./render.sh ../../materias/af-diseno-sistemas-web-32/template/diagramas
#
# Los SVG quedan en /tmp/eidas-diagramas/..., FUERA del repo del grupo: si quedaran adentro,
# el clon tendría cambios sin commitear y `grupos.py publicar` se negaría a publicar.
set -e
cd "$(dirname "$0")"
RAIZ="$(cd ../.. && pwd)"

if [ $# -eq 2 ]; then
  ORIGEN="$RAIZ/materias/$1/grupos/$2/diagramas"
  DESTINO="/tmp/eidas-diagramas/$1/$2"
elif [ $# -eq 1 ]; then
  ORIGEN="$(cd "$1" && pwd)"
  DESTINO="/tmp/eidas-diagramas/$(basename "$ORIGEN")"
else
  sed -n '6,8p' "$0"
  exit 1
fi

if [ ! -d "$ORIGEN" ]; then
  echo "No existe $ORIGEN"
  exit 1
fi

# La carpeta se crea antes: si la crea Docker, queda a nombre de root y la CLI no puede escribir
mkdir -p "$DESTINO"
# -u: que los SVG queden a nombre del usuario y no de root.
# PlantUML sale con 200 si algún diagrama tiene errores, pero igual genera todos (los rotos
# como una imagen con el error): no cortamos acá, listamos primero y avisamos después.
set +e
SALIDA=$(docker run --rm -u "$(id -u):$(id -g)" \
  -v "$ORIGEN":/entrada:ro \
  -v "$DESTINO":/salida \
  plantuml/plantuml -tsvg -o /salida "/entrada/**.puml" 2>&1)
CODIGO=$?
set -e

echo "Diagramas generados en $DESTINO:"
ls -1 "$DESTINO"

if [ $CODIGO -ne 0 ]; then
  echo ""
  echo "ATENCIÓN: hay diagramas con errores de sintaxis (su SVG muestra el error en vez del diagrama):"
  echo "$SALIDA" | grep "^Error line" | sed "s|/entrada/|$ORIGEN/|" | sed 's/^/  /'
  exit 1
fi
