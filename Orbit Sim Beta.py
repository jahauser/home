#############################################################################################
#################################### n-Body Orbit Simulator #################################
#############################################################################################

# Interactive n-body orbital simulator for varying systems and force laws
# Created by Jake Hauser

# Depends on body.py, vector.py, variables.py, custom, solar_system, inner_solar_system, and outer_solar_system;
# also uses courier.ttf, courier_bold.ttf, and Pygame; all of these should be included in this app.

# Changing settings in the variables file allows the user to:
#       1. Choose whether to randomly generate the system or use a particular preset
#       2. If randomizing, set the number of masses
#       3. If using a preset, select which preset
#       4. Alter the force law used
#       5. Toggle instructions

# Changing the values in the custom file allows the user to create their own system setups. Make sure to:
#       1. Keep the header line
#       2. Follow the existing format: "MASS COEFFICIENT;MASS POWER;POSITION;VELOCITY;COLOUR;NAME"
#       3. Use the units described in the header

########################################## IMPORTS ##########################################
# Standard python library imports
import math
import sys
import copy
import random
import os
from ast import literal_eval as tuple
from decimal import Decimal
import re

# Pygame import: used for graphics and mouse/keyboard detection
import pygame
from pygame.locals import *
from pygame import gfxdraw

# Homemade classes
from body import Body         # Class used for bodies in system
from vector import Vec # More convenient datatype for positions, velocities, etc.

##################################### USER INPUT IMPORT #####################################
# Parses user input from variables file
# Sets fullscreen status, body configuration, force law, and toggles main menu
regex = re.compile("<.*?>")

with open('variables', 'r') as var_file:
    vars = var_file.read().replace('\n', '')

vars = regex.split(vars)
del vars[0::2]
if vars[0] == "False":
    fullscreen = False
else:
    fullscreen = True

config = vars[1]
try:
    num_objects = int(config)
    randomize = True
except ValueError:
    doc = config
    randomize = False

force_power = float(vars[2])

if vars[3] == "False":
    main_menu = False
else:
    main_menu = True
######################################### FUNCTIONS #########################################
# Converts AU-coordinate positions to screen positions
def transform(pos):
    pos -= oldCentre.getPos()
    pos += shift
    pos = scale*pos
    pos += absolute_centre
    return pos

# Inverse of transform()
def detransform(pos):
    pos -= absolute_centre
    pos = pos/scale
    pos -= shift
    pos += oldCentre.getPos()
    return pos

# If radii were drawn to scale, many objects would be indistinguishable pixels
# This function scales radii along a log scale for visual convenience
def radScale(rad):
    return 2.5*(math.log(rad,10)/pow(10,2)-0.030)

# Converts AU coordinates and km radii to appropriate circle on screen
def drawCircle(pos, rad, colour):
    pos = transform(pos)
    rad = scale*rad
    if (pos.getX()+rad >= 0 and pos.getX()-rad <= dimensions[0] and pos.getY()+rad >= 0 and pos.getY()-rad <= dimensions[1]):
        pygame.gfxdraw.filled_circle(screen, round(pos.getX()), round(pos.getY()),round(rad), colour)
        if round(rad) > 1:
            pygame.gfxdraw.aacircle(screen, round(pos.getX()), round(pos.getY()), round(rad), colour) # Provides anti-aliasing

# Blits text onto screen
def drawText(pos, text, rad, colour, font):
    pos = transform(pos) + Vec(rad*scale+8,-4)
    label = font.render(text, 1, colour)
    screen.blit(label,pos.tuple())

# Detects collisions between two coordinate sets (with radii)
# Used between two bodies and between a body and the user's mouse
def collision(pos1,rad1,pos2,rad2):
    distance = math.sqrt((pos1-pos2)**2)
    if distance < (rad1+rad2+0.05): # larger collision resolution (0.05) accounts for passing bodies, but introduces error
        return True
    return False

# Calculates gravitational* force between two objects in AU*kg/day^2
# *also supports other force laws, which give other units
# Force on obj1 by obj2
def gravity(obj1, obj2):
    Gmm = G * obj1.getMass() * obj2.getMass()
    r = obj2.getPos() - obj1.getPos()
    if r*r != 0:
        force = Gmm*pow((r*r),force_power/2.0)
        return force*(r/math.sqrt(r*r))
    return Vec(0,0) # If the objects are overlapping, they should collide in the next frame so we call the force zero

# Calculates the potential at a point due to a body
# Uses same force law as gravity()
def potential(pos, obj):
    Gmm = G * obj.getMass()
    r = obj.getPos() - pos
    if r*r != 0:
        return Gmm*pow((r*r),(force_power+1.0)/2.0)
    return 0 # Sets potential to zero when overlapping the body in question

# Draws gravitational potential lines
# Very time consuming for large systems
# Step size = potential difference between lines
# Res = acceptable difference between potential step and point
def contourLines(xpoints,ypoints,step,res):
    points = []
    for x in range(0,xpoints):      # Iterates column by column for each x-point
        for y in range(0,ypoints):
            pot = 0.0
            for mass in system: # Potential is a scalar, so it sums for all masses
                pot += potential(detransform(Vec(x*dimensions[0]/xpoints,y*dimensions[1]/ypoints)), mass)
            if pot % step < res:
                points.append(detransform(Vec(x*dimensions[0]/xpoints,y*dimensions[1]/ypoints)))
    return points

# Converts text file information into system data
def parse(info):
    mass = float(info[0])*math.pow(10,int(info[1]))
    rad = float(info[2])
    (x,y) = (tuple(info[3]))
    (vx,vy) = (tuple(info[4]))
    colour = (tuple(info[5]))
    if info[6] == "": # Names unnamed bodies according to their mass
        name = "{:.2E}".format(Decimal(mass)) + "kg"
    else:
        name = info[6]
    return [mass,rad,Vec(x,y),Vec(vx,vy),colour,name]

# Calculates the average colour between two bodies
# Uses this for new colour after collision
def averageColour(c1,c2):
    return (int((c1[0]+c2[1])/2),int((c1[1]+c2[1])/2),int((c1[2]+c2[2])/2))

######################################## PYGAME INIT ########################################
# Initiates required Pygame graphics setup, including screen and fonts
pygame.init()
if fullscreen:
    dimensions = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    flags = FULLSCREEN | DOUBLEBUF
else:
    dimensions = (pygame.display.Info().current_w-50, pygame.display.Info().current_h-100)
    flags = DOUBLEBUF | RESIZABLE
screen = pygame.display.set_mode(dimensions,flags,0)
pygame.display.set_caption("Orbit Sim Beta")
screen.set_alpha(None)
if fullscreen:
    pygame.event.set_allowed([QUIT, KEYDOWN, MOUSEBUTTONDOWN, VIDEORESIZE])
else:
    pygame.event.set_allowed([QUIT, KEYDOWN, MOUSEBUTTONDOWN])
clock = pygame.time.Clock()

mass_font = pygame.font.Font("courier.ttf", 14)
button_font = pygame.font.Font("courier_bold.ttf", 48)
instruction_font = pygame.font.Font("courier.ttf", 36)

####################################### SYSTEM SETUP ########################################
scale = 24.0 # Zoom factor; starts at 24 pixels per AU
shift = Vec(0,0) # Shift factor, starts as the zero vector
absolute_centre = Vec(float(dimensions[0]/2),float(dimensions[1]/2)) # Used to shift (0,0) from the top left corner to
                                                                     # the middle of the screen
G = 1.4881314*math.pow(10,-34) # Gravitational constant in AU^3/day^2/kg
INF = sys.maxsize # Large number for initial click position (before click)

dt = 1 # Time interval in days
dt_step = 0.5 # Amount that dt changes each frame per user request
scale_step = 1.05 # Amount that scale changes each frame per user request
scroll_speed = 0.25 # Amount that shift changes each frame per user request

# These variables determine the number and size of gravitational potential lines
contour_step = 10*pow(10,-5)
contour_res = 2*pow(10,-5)

trace_cap = 1000 # Max number of trace points allowed, used to reduce strain on hardware

m0 = Body(0.0, 1.0, Vec(0, 0), Vec(0.0, 0.0), (0, 0, 0), "") # Initial system centre
system = [] # List containing all bodies
centre = m0 # Used for relative motion
oldCentre = m0 # Used for drawing purposes

contourPoints = [] # List of gravitational potential contour points
backup = [] # Backup system list to revert to

pause = True # Flag controlling whether simulation is paused or not
must_centre = False # Flag controlling whether the system is centring on a new body
tracing = False # Flag controlling whether system is actively tracing
trace_clear = False # Flag controlling commands to clear traces
trace_period = 4
trace_counter = 0

# Arrow key flags
up = False
down = False
left = False
right = False

# Build system list based either on random generations or input document
if randomize:
    for counter in range(num_objects):
        line = [str(float(random.randint(1,900))/100.0),str(random.randint(10, 16)+random.randint(10,16)),str(float(random.randint(1000,1000000))),
                str(((float(random.randint(-4000,4000))/100.0),float(random.randint(-3000,3000))/100.0)),str(((float(random.randint(-100,100))/10000.0,float(random.randint(-100,100))/10000.0))),
                str(((random.randint(25,255),random.randint(25,255),random.randint(25,255)))),""]
        info = parse(line)
        backup.append(Body(info[0], info[1], info[2], info[3], info[4], info[5]))
        system.append(Body(info[0], info[1], info[2], info[3], info[4], info[5]))
else:
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path,"docs/" + doc)
    input = open(path,'r')
    input.readline()
    for line in input:
        info = parse(line.split(";"))
        backup.append(Body(info[0], info[1], info[2], info[3], info[4], info[5]))
        system.append(Body(info[0], info[1], info[2], info[3], info[4], info[5]))

######################################### MAIN MENU #########################################
# Prints instructions onto screen until RETURN is pressed
# Can be toggled off in variables file
if main_menu:
    screen.fill((81,167,249))
    instructions = ["", "", "CLICK on a mass to make it the new reference frame", "", "ESC    = quit", "SPACE  = pause/unpause – note: game begins paused", "",
                    "+/-    = zoom in/out", "ARROWS = move view around", "]/[    = increase/decrease simulation speed", "",
                    "t      = toggle path tracing (slows simulation)", "r      = reset to original settings",
                    "c      = centre view around reference mass", "g      = draw gravitation equipotential lines (when paused)",
                    "", "press RETURN to start"]
    for i in range(len(instructions)):
        label = instruction_font.render(instructions[i], 1, (0, 0, 0))
        screen.blit(label, (100,60+35*i))
    pygame.display.flip()

while main_menu:
    ev = pygame.event.get()
    for event in ev:
        if event.type == VIDEORESIZE:
            dimensions = (event.w, event.h)
            screen = pygame.display.set_mode(dimensions, flags, 0)
            screen.set_alpha(None)
            screen.fill((0, 191, 255))
            for i in range(len(instructions)):
                label = instruction_font.render(instructions[i], 1, (0, 0, 0))
                screen.blit(label, (100, 60 + 25 * i))
            pygame.display.flip()
        if event.type == pygame.KEYDOWN:
            if event.key == K_RETURN:
                main_menu = False
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
######################################### GAME LOOP #########################################
# Main simulation loop running program
while not pygame.event.peek(QUIT):
    clock.tick(60) # Max FPS = 60

    screen.fill((0,0,0)) # Black background
    clickpos = Vec(INF, INF) # Reset mouse click position

    # Check currently pressed keys
    keys = pygame.key.get_pressed()
    if keys[K_LEFTBRACKET]:
        dt -= dt_step
    if keys[K_RIGHTBRACKET]:
        dt += dt_step
    if keys[K_EQUALS]:
        scale *= scale_step
        scroll_speed /= scale_step # Scroll speed decreases with zoom in to keep smooth controls
    if keys[K_MINUS]:
        scale /= scale_step
        scroll_speed *= scale_step # Scroll speed increases with zoom out to keep smooth controls
    if keys[K_UP]:
        up = True
    if keys[K_DOWN]:
        down = True
    if keys[K_LEFT]:
        left = True
    if keys[K_RIGHT]:
        right = True

    ev = pygame.event.get()
    for event in ev:
        # Handle window resizing events
        if event.type == VIDEORESIZE:
            dimensions = (event.w, event.h)
            screen = pygame.display.set_mode(dimensions, flags, 0)
            screen.set_alpha(None)
        # Handle clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            (x,y) = pygame.mouse.get_pos()
            clickpos = Vec(x,y)
        # Handle keystrokes
        if event.type == pygame.KEYDOWN:
            # Quit
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            # Pause
            if event.key == K_SPACE:
                pause = not pause
            # Centre selected body
            if event.key == K_c:
                oldCentre = centre
                trace_clear = True
            # Reset system
            if event.key == K_r:
                system = []
                for mass in backup:
                    system.append(copy.copy(mass))
                    mass.clearTrace()
                centre = m0
                oldCentre = centre
                contourPoints = []
            # Toggle tracing
            if event.key == K_t:
                tracing = not tracing
                trace_clear = True
            # If paused, generated gravitational potential lines
            if (event.key == K_g and pause):
                if contourPoints == []:
                    # 2 indicates potentials generated at every second point
                    contourPoints = contourLines(round(dimensions[0]/2),round(dimensions[1]/2),contour_step,contour_res)
                else:
                    contourPoints = []

    if not pause:
        delete = []
        for i in range(len(system)):
            for j in range(i+1, len(system)):
                force = gravity(system[i], system[j]) # force between the two objects
                try:
                    boost1 = dt/system[i].getMass() * force # acceleration on object 1
                    boost2 = -dt/system[j].getMass() * force # acceleration on object 2
                except ZeroDivisionError: # If force cannot be computed, implies impending collision, so set to zero
                    boost1 = Vec(0,0)
                    boost2 = Vec(0,0)
                # Change object speeds by boost amount
                system[i].boost(boost1)
                system[j].boost(boost2)
                # Detect and handle collisions
                if collision(system[i].getPos(), radScale(system[i].getRad()), system[j].getPos(), radScale(system[j].getRad())):
                    m1,m2 = system[i].getMass(),system[j].getMass()
                    r1,r2 = system[i].getRad(),system[j].getRad()
                    r = pow(r1**3+r2**3,1.0/3)
                    pos = system[i].getPos()
                    vel = (m1*system[i].getVel() + m2*system[j].getVel())/(m1+m2)
                    c = averageColour(system[i].getColour(),system[j].getColour())
                    n1,n2 = system[i].getName(),system[j].getName()
                    if n1[len(n1)-2:] == "kg":
                        name = "{:.2E}".format(Decimal(m1+m2)) + "kg"
                    else:
                        name = n1[:int(len(n1)/2)] + n2[int(len(n2)/2):]
                        name = n1
                    system = system[:i] + [Body(m1 + m2, r, pos, vel, c, name)] + system[i + 1:j] + \
                             [Body(0, 1, Vec(0, 0), Vec(0, 0), (0, 0, 0), "")] + system[j + 1:]
                    delete.append(j)
        # Delete second of collided objects
        # Complex arrangement dodges nasty problem of python not changing for loops after items are dleeted
        delete = list(set(delete))
        delete.sort()
        delete.reverse()
        for i in range(len(delete)):
            del system[delete[i]]
    if pause:
        for pos in contourPoints: # If contourPoints isn't empty, draw gravitational potential lines
            pos = transform(pos)
            pygame.draw.rect(screen, (255,255,255), pygame.Rect(round(pos.getX()-1),round(pos.getY()-1),2,2))

    # Move shift corresponding to arrow keys
    if up:
        shift += Vec(0,scroll_speed)
    if down:
        shift -= Vec(0, scroll_speed)
    if left:
        shift += Vec(scroll_speed,0)
    if right:
        shift -= Vec(scroll_speed,0)

    vshift = centre.getVel() # Velocity of reference frame
    for mass in system:
        if not pause:
            mass.boost(-vshift) # Shift all objects to proper reference frame.
            mass.move(dt) # Move objects
            if tracing:
                if trace_counter % trace_period == 0:
                    mass.addTrace(trace_cap) # Add new trace point
        if trace_clear:
            mass.clearTrace()
        if tracing:
            for dot in mass.getTrace():
                drawCircle(dot[0], dot[1], dot[2]) # Draw trace points
        drawCircle(mass.getPos(),radScale(mass.getRad()),mass.getColour()) # Draw body
        (x,y) = pygame.mouse.get_pos()
        if collision(mass.getPos(),radScale(mass.getRad()),detransform(Vec(x,y)),5/scale): # Check mouseover for names
            drawText(mass.getPos(),mass.getName(),radScale(mass.getRad()),mass.getColour(),mass_font)
        if collision(mass.getPos(),radScale(mass.getRad()),detransform(clickpos),5/scale): # Check click for new reference frame
            centre = mass

    trace_counter += 1

    # Reset flags
    up = False
    down = False
    left = False
    right = False
    trace_clear = False
    pygame.display.flip() # Update screen