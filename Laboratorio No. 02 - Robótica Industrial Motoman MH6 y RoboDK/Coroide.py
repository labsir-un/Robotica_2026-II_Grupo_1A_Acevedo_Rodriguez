from robodk.robolink import *
from robodk.robomath import *
import math
from matplotlib.textpath import TextPath
from matplotlib.path import Path

#------------------------------------------------
# 1) Conexión e inicialización
#------------------------------------------------
RDK = Robolink()

robot = RDK.ItemUserPick("Selecciona un robot", ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise Exception("No se ha seleccionado un robot válido.")

frame_name = "Frame_from_Target1"
frame = RDK.Item(frame_name, ITEM_TYPE_FRAME)
if not frame.Valid():
    raise Exception(f'No se encontró el Frame "{frame_name}" en la estación.')

target_name = "Target_Home"
target = RDK.Item(target_name, ITEM_TYPE_TARGET)
if not target.Valid():
    raise Exception(f"El target '{target_name}' no existe en la estación.")

### Conectar al robot físico
##if not robot.Connect():
##    raise Exception("No se pudo conectar al robot. Verifica que esté en modo remoto y que la configuración sea correcta.")
##
### Confirmar conexión
##if not robot.ConnectedState():
##    raise Exception("El robot no está conectado correctamente. Revisa la conexión.")
##
##print("Robot conectado correctamente.")

robot.setPoseFrame(frame)
robot.setPoseTool(robot.PoseTool())
robot.setSpeed(300)
robot.setRounding(5)  # blending (radio de curvatura)

#------------------------------------------------
# 2) Parámetros
#------------------------------------------------
num_points = 50
a = 45
b = 90
z_surface = 0
z_safe = 50
z_up = z_surface - z_safe   # altura con el lápiz levantado (misma convención que tu código)
x_off = 150                 # desplazamiento de los nombres en X del frame

#------------------------------------------------
# 3) Función de trazo: sube -> se posiciona -> baja -> dibuja -> sube
#------------------------------------------------
def draw_stroke(pts):
    """pts: lista de (x, y) en el plano del frame."""
    x0, y0 = pts[0]

    # Posicionarse arriba del inicio y bajar (sin blending para no recortar esquinas)
    robot.setRounding(0)
    robot.MoveL(transl(x0, y0, z_up))
    robot.MoveL(transl(x0, y0, z_surface))

    # Trazo continuo
    robot.setRounding(5)
    for x, y in pts[1:-1]:
        robot.MoveL(transl(x, y, z_surface))

    # Último punto y subida vertical
    xf, yf = pts[-1]
    robot.setRounding(0)
    robot.MoveL(transl(xf, yf, z_surface))
    robot.MoveL(transl(xf, yf, z_up))

#------------------------------------------------
# 4) Puntos de la coroide: r = a - b*cos(theta)
#------------------------------------------------
coroide = []
for i in range(num_points + 1):
    theta = 2 * math.pi * i / num_points
    r = a - b * math.cos(theta)
    coroide.append((r * math.cos(theta), r * math.sin(theta)))

#------------------------------------------------
# 5) Puntos de los nombres (curvas aplanadas, sin CLOSEPOLY basura)
#------------------------------------------------
path_jose = TextPath((0, 0), "Jose", size=75)
path_leonardo = TextPath((0, -50), "Leonardo", size=75)
text_path = Path.make_compound_path(path_jose, path_leonardo)

letras = []
for poly in text_path.to_polygons(closed_only=False):
    # mismo cambio de ejes que tenías: x = pt[1], y = pt[0]
    pts = [(p[1] + x_off, p[0]) for p in poly]
    if pts[0] != pts[-1]:
        pts.append(pts[0])      # cerrar el contorno de la letra
    if len(pts) > 1:
        letras.append(pts)

#------------------------------------------------
# 6) Ejecución
#------------------------------------------------
robot.MoveJ(target)
x0, y0 = coroide[0]
robot.MoveJ(transl(x0, y0, z_up))     # primera aproximación desde home, en el aire

draw_stroke(coroide)
for stroke in letras:
    draw_stroke(stroke)

robot.setRounding(0)
robot.MoveJ(target)
print(f"¡Coroide y nombres completados en el frame '{frame_name}'!")
