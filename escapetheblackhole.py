#importing all needed modules
import os, sys
sys.path.append(os.getcwd() + "\modules")
from math import cos, sin, atan2, pi
from itertools import combinations
import random
import time
#renaming module for faster typing
import pygame as pyg
from pygame.locals import *

 
#gravitational constant
G = 6.67 * 10**-11
#window resolution, can be made larger, text may not fit for some resolutions
Screen_Width = 1200
Screen_Height = 600
#dictionary for ship path prediction dots
Dots = {}
#list for storage of asteroid data values
Asteroid_Stats_List = []

#time between recalculating coordinates of sprites
dt = 1/30
#rate of rotation of the ship
Rate_Of_Rotation = 10

#setting default gamemode to easy and setting gameplay variables for easy gameplay
Black_Hole_Mass = 10**32
Max_Ammunition = 9999999
Max_Fuel = 9*10**99
Asteroid_Rate = 50

Mode_Selected = "EASY"


#colour variables
Grey = (165,165,165)
White = (255,255,255)
Navy_Blue = (8,8,36)
Black = (0,0,0)
Orange = (255,128,0)
Green = (0,255,0)
Red = (153,0,0)
#list of colours asteroids can be, various grey, brown and red colours
Asteroid_Colours = [(100,0,0),(32,32,32),(64,64,64),(96,96,96),(128,128,128),(160,160,160),(51,25,0)]

#ends program if true
End_Program = False
#variables used to navigate menu and game states
Game_Over = False
How_To_Menu = False
Settings_Menu = False
Start_Game = False
Escaped_Black_Hole = False


#trys to load image from file when called
#return image and image rectangle
def load_image(name):
    fullname = os.path.join(name)
    try:
        image = pyg.image.load(fullname)
    except pyg.error:
        print("Cannot load image:", name)
        raise SystemExit
    #image = image.convert()
    return image, image.get_rect()

#returns polar coordinates of a sprite for given cartesian coordinates of sprite and origin
#boolean parameter use to reduce variable use and processing power needed when only distance of separation needed
def polar_coordinates(x1, y1, x0, y0, theta = True):
    Delta_y = y0-y1
    Delta_x = x1-x0
    r = ((Delta_y**2)+(Delta_x**2))**(1/2)
    if theta == True:
        theta = 90 - (180*atan2(Delta_y, Delta_x)/pi)
        return r, theta
    else:
        return r

#returns cartesian coordinates for given polar coordinates and origin
def cartesian_coordinates(r, theta, x0, y0):
    return r*sin(pi*theta/180)+x0, y0-r*cos(pi*theta/180)

#calculates acceleration due to gravity object a feels in the direction of object b, and the direction to object b from object a
def gravity(Object_A, Object_B):
    Distance_Of_Separation, Bearing_To_Object_B = polar_coordinates(Object_B.Position_x, Object_B.Position_y, Object_A.Position_x, Object_A.Position_y)
    #distance of separation increased to model interstellar distances
    Acceleration_Due_To_Gravity = G*Object_B.Mass/(Distance_Of_Separation*1000000)**2
    return Acceleration_Due_To_Gravity, Bearing_To_Object_B

#separate function for ship needed for ship path prediction, dt can be changed to allow variable precision of prediction
def new_ship_velocity(Main_Object, dt = dt):
    Tethered_Velocity_x = Main_Object.Velocity_x
    Tethered_Velocity_y = Main_Object.Velocity_y
    #calculates added velocity due to tethered objects
    if len(Tethered) != 0:
        for Object in Tethered:
            Accel_Due_To_Grav, Bearing_Of_Grav = gravity(Main_Object, Object)
            Tethered_Velocity_x += (Accel_Due_To_Grav*sin(pi*Bearing_Of_Grav/180)*dt)
            Tethered_Velocity_y += (Accel_Due_To_Grav*cos(pi*Bearing_Of_Grav/180)*dt)
    Accel_Due_To_Grav, Bearing_Of_Grav = gravity(Main_Object, Black_Hole)
    return Tethered_Velocity_x + ((Main_Object.Acceleration*sin(pi*Main_Object.Bearing/180)+ Accel_Due_To_Grav*sin(pi*Bearing_Of_Grav/180))*dt), Tethered_Velocity_y + ((Main_Object.Acceleration*cos(pi*Main_Object.Bearing/180)+ Accel_Due_To_Grav*cos(pi*Bearing_Of_Grav/180))*dt)
    

#calculates new position for many objects, taking into account starting velocity, acceleration due to gravity, and position relative to ship
def new_position(Main_Object, dt = dt):
    if Main_Object != (Black_Hole or Bomb):
        #calculating new gravitational acceleration for asteroids
        Accel_Due_To_Grav, Bearing_Of_Grav = gravity(Main_Object, Black_Hole)
        Main_Object.Velocity_x += Accel_Due_To_Grav*sin(pi*Bearing_Of_Grav/180)*dt
        Main_Object.Velocity_y += Accel_Due_To_Grav*cos(pi*Bearing_Of_Grav/180)*dt
    if Main_Object == Ship:
        Ship.Velocity_x, Ship.Velocity_y = new_ship_velocity(Ship)
    else:
        #moving all objects in accordance with their velocity and the velocity of the ship
        Main_Object.Position_x += dt*(Main_Object.Velocity_x - Ship.Velocity_x)/40
        Main_Object.Position_y += -dt*(Main_Object.Velocity_y - Ship.Velocity_y)/40

#calculates predicted path of ship, number of dots calculated and how far ahead in time path predicts can cause lag for high values, so kept low
def predicted_path(Dots_Left):
    if Dots_Left != 0:
        if Dots_Left == 50:
            #setting variables to global as I was recieving variable referenced before assignment errors
            global Dot_Position_x
            global Dot_Position_y
            Dot_Position_x = Screen_Width/2
            Dot_Position_y = Screen_Height/2
            #if first dot predicting velocities with reference to current ship velocity
            New_Velocity_x, New_Velocity_y = new_ship_velocity(Ship, 20*dt)
        else:
            #if not first dot calculating new velocities with reference to last dot calculated
            New_Velocity_x, New_Velocity_y = new_ship_velocity(Dots[Dots_Left+1], 20*dt)
        #assigning new dot position based on new velocities
        Dot_Position_x += 20*dt*New_Velocity_x/40
        Dot_Position_y += -20*dt*New_Velocity_y/40
        #using try except clause as sometimes if new velocity calculated when last dot very near center of black hole or asteroid,
        #ship would be predicted to accelerate to ridiculous speed, and a invalid rect assignment error would be thrown,
        #as the new ship coordinates would be too large
        try:
            #assigning new dot a key in the dictionary
            Dots[Dots_Left] = Ship_Path_Objects(Dot_Position_x, Dot_Position_y, New_Velocity_x, New_Velocity_y)
            Dots_Left -= 1
            predicted_path(Dots_Left)
        except TypeError:
            global Dots_Calculated
            Dots_Calculated = 50 - Dots_Left
    else:
        Dots_Calculated = 50

#creates a text image for given text, size, position, and colour, and can either return surface and rectangle or blit the image        
def text(text, size, position, display, colour=Green):
    #using default pygame font
    Font = pyg.font.Font(None, size)
    Text_Surface = Font.render(text, 1, colour)
    Text_Surface_Rect = Text_Surface.get_rect()
    Text_Surface_Rect.topleft = (position)
    if display == True:
        Main_Window.blit(Text_Surface, Text_Surface_Rect)
    else:
        return Text_Surface, Text_Surface_Rect

#displays flame of ship, always pointing away from ship and glued to back of ship
def display_flame():
    Ship_Flame_Active = pyg.transform.rotate(Ship_Flame, -Ship.Bearing)
    Ship_Flame_Active_Rect = Ship_Flame_Active.get_rect(center = (cartesian_coordinates(15, Ship.Bearing+180, Ship.rect.centerx, Ship.rect.centery)))
    Main_Window.blit(Ship_Flame_Active, Ship_Flame_Active_Rect)



#class used to create spaceship, defaults to standard ship stats, functionality for different ship scenarios
class Ship_Objects(pyg.sprite.Sprite):
    def __init__(self, Acceleration = 0,Ship_Acceleration = 10000, Velocity_x = 0, Velocity_y = 0, Position_x = Screen_Width/2, Position_y = Screen_Height/2, Bearing = 0, Rotation = 0, Mass = 50000):
        pyg.sprite.Sprite.__init__(self)
        self.image = pyg.Surface((20,30))
        self.image.fill(White)
        self.image.set_colorkey(White)
        pyg.draw.polygon(self.image, Grey, ((10,0),(0,30),(20,30)))
        self.rect = self.image.get_rect()
        self.radius = 5
        #current acceleration of ship
        self.Acceleration = Acceleration
        #maximum acceleration of ship
        self.Ship_Acceleration = Ship_Acceleration
        self.Velocity_x = Velocity_x
        self.Velocity_y = Velocity_y
        self.Position_x = Position_x
        self.Position_y = Position_y
        #current heading ship is pointing to
        self.Bearing = Bearing
        #sets rate of ship rotation
        self.Rotation = Rotation
        self.Mass = Mass
        self.rect.center = (self.Position_x, self.Position_y)
        #active ship sprite which is displayed, used so that original ship image doesn't reduce in quality as it is rotated
        self.Active_Sprite = pyg.transform.rotate(self.image, -self.Bearing)
        #used to ensure ship rotates about center point
        self.Active_Sprite_Rect = self.Active_Sprite.get_rect(center = self.rect.center)
        
    def update(self):
        self.Bearing += self.Rotation
        self.rect.center = (self.Position_x, self.Position_y)
        new_position(self)
        self.Active_Sprite = pyg.transform.rotate(self.image, -self.Bearing)
        self.Active_Sprite_Rect = self.Active_Sprite.get_rect(center = self.rect.center)

    def display(self):
        Main_Window.blit(self.Active_Sprite, self.Active_Sprite_Rect)

        #method used to reset ship attributes when new game started
    def reset(self):
        self.Acceleration = 0
        self.Ship_Acceleration = 10000
        self.Velocity_x = 0
        self.Velocity_y = 0
        self.Position_x = Screen_Width/2
        self.Position_y = Screen_Height/2
        self.Bearing = 0
        self.Rotation = 0
        self.Active_Sprite = pyg.transform.rotate(self.image, -self.Bearing)
        self.Active_Sprite_Rect = self.Active_Sprite.get_rect(center = self.rect.center)
    

#class used to draw small green ship path prediction dots, has some unnecessary variables so that it can be passed through the ship velocity function
class Ship_Path_Objects(pyg.sprite.Sprite):
    def __init__(self, Position_x, Position_y, Velocity_x, Velocity_y):
        pyg.sprite.Sprite.__init__(self)
        self.image = pyg.Surface((4,4))
        self.image.fill(White)
        self.image.set_colorkey(White)
        pyg.draw.circle(self.image, Green, (2,2), 2)
        self.rect = self.image.get_rect()
        self.Position_x = Position_x
        self.Position_y = Position_y
        self.Velocity_x = Velocity_x
        self.Velocity_y = Velocity_y
        self.rect.center = (self.Position_x, self.Position_y)   
        self.Acceleration = 0
        self.Bearing = 0

    def display(self):
        Main_Window.blit(self.image, self.rect)
        

#class used to control asteroids
#takes a list of randomly generated attribute when initialised, only some variables are randomly assigned at creation by necessity to reduce processing power needed 
class Asteroid_Objects(pyg.sprite.Sprite):
    def __init__(self, Stats):
        pyg.sprite.Sprite.__init__(self)
        self.image = pyg.Surface((Stats[0], Stats[1]))
        self.image.fill(White)
        self.image.set_colorkey(White)
        pyg.draw.ellipse(self.image, Stats[2], (0, 0, Stats[0], Stats[1]))
        self.rect = self.image.get_rect()
        self.radius = Stats[0]/2
        self.Acceleration = Stats[3]
        self.Velocity_x = Stats[4]
        self.Velocity_y = Stats[5]
        self.Angle = 0
        self.Rotation = Stats[6]
        self.Mass = Stats[7]
        self.radius = Stats[0]
        self.Position_x, self.Position_y = cartesian_coordinates(max(Screen_Width, Screen_Height)+100, Bearing_To_Black_Hole + 180 + random.randint(-45, 45), Screen_Width/2, Screen_Height/2)
        self.Bearing = Bearing_To_Black_Hole + random.randint(-10, 10)
        self.rect.center = ((self.Position_x, self.Position_y))
        self.Active_Sprite = pyg.transform.rotate(self.image, -self.Bearing)
        self.Active_Sprite_Rect = self.Active_Sprite.get_rect(center = self.rect.center)

    def update(self):
        self.Angle += self.Rotation
        new_position(self)
        self.rect.center = ((self.Position_x, self.Position_y))
        self.Active_Sprite = pyg.transform.rotate(self.image, -self.Angle)
        self.Active_Sprite_Rect = self.Active_Sprite.get_rect(center = self.rect.center)
        
    def display(self):
        Main_Window.blit(self.Active_Sprite, self.Active_Sprite_Rect)


#class used to create and control black hole
#only takes mass as parameter for changes in gamemode
class Black_Hole_Object(pyg.sprite.Sprite):
    def __init__(self, Black_Hole_Mass):
        pyg.sprite.Sprite.__init__(self)
        self.image = pyg.Surface((5000,5000))
        self.image.fill(White)
        self.image.set_colorkey(White)
        pyg.draw.circle(self.image, Black, (2500,2500), 2500)
        self.rect = self.image.get_rect()
        self.radius = 2300
        self.Acceleration = 0
        self.Bearing = 0
        self.Velocity_x = 0
        self.Velocity_y = 0
        self.Position_x = Screen_Width/2
        self.Position_y = Screen_Height + 2400
        self.Display_x = self.Position_x
        self.Display_y = self.Position_y
        self.Mass = Black_Hole_Mass
        self.rect.center = ((self.Position_x, self.Position_y))
        self.Active_Sprite = self.image
        self.Active_Sprite_Rect = self.Active_Sprite.get_rect(center = self.rect.center)

    def update(self):
        new_position(self)
        self.rect.center = ((self.Position_x, self.Position_y))

    def display(self):
        Main_Window.blit(self.image, self.rect)
        

    def reset(self, New_Mass):
        self.Acceleration = 0
        self.Bearing = 0
        self.Velocity_x = 0
        self.Velocity_y = 0
        self.Position_x = Screen_Width/2
        self.Position_y = Screen_Height + 2400
        self.Display_x = self.Position_x
        self.Display_y = self.Position_y
        self.Mass = New_Mass
        

#class used to control projectiles
#again has some unnecessary variables so it can be passed through new_position function
class Projectiles(pyg.sprite.Sprite):
    def __init__(self):
        pyg.sprite.Sprite.__init__(self)
        self.image = pyg.Surface((4,4))
        self.image.fill(White)
        self.image.set_colorkey(White)
        pyg.draw.circle(self.image, Red, (2,2), 2)
        self.rect = self.image.get_rect()
        self.radius = 2
        self.Range = 0
        self.Velocity = 600
        self.Velocity_x = 0
        self.Velocity_y = 0
        self.Bearing = Ship.Bearing
        self.Position_x = Ship.Position_x
        self.Position_y = Ship.Position_y
        self.rect.center = (cartesian_coordinates(self.Range, self.Bearing, self.Position_x, self.Position_y))
        Main_Window.blit(self.image, self.rect)

    def update(self):
        new_position(self)
        self.Range += self.Velocity*dt
        self.rect.center = (cartesian_coordinates(self.Range, self.Bearing, self.Position_x, self.Position_y))

    def display(self):
        Main_Window.blit(self.image, self.rect)

#class used to create background stars, randomly generated every time game launched
class Star_Objects(pyg.sprite.Sprite):
    def __init__(self):
        pyg.sprite.Sprite.__init__(self)
        self.image = pyg.Surface((2,2))
        self.image.fill(Black)
        self.image.set_colorkey(Black)
        pyg.draw.line(self.image, White, (1,0), (1,2))
        self.rect = self.image.get_rect()
        self.Position_x = random.randint(0, Screen_Width)
        self.Position_y = random.randint(0, Screen_Height)
        self.rect.center = (self.Position_x, self.Position_y)

    def display(self):
        Main_Window.blit(self.image, self.rect)
        
 
        
#initialises pygame modules
pyg.init()
#creates main window
Main_Window = pyg.display.set_mode([Screen_Width, Screen_Height])
#filling window with navy blue space colour
Main_Window.fill(Navy_Blue)
#gives the window a title
pyg.display.set_caption("Escape the Black Hole")



#initialises sprites groups 
All_Sprites_List = pyg.sprite.Group()
All_Asteroids_List = pyg.sprite.Group()
All_Except_Ship = pyg.sprite.Group()
All_Projectiles = pyg.sprite.Group()
All_Stars = pyg.sprite.Group()
Tethered = pyg.sprite.Group()

#initialising ship and black hole objects
Ship = Ship_Objects()
Black_Hole = Black_Hole_Object(Black_Hole_Mass)

#creating and drawing ship flame surface
Ship_Flame = pyg.Surface((20,30))
Ship_Flame.fill(White)
Ship_Flame.set_colorkey(White)
pyg.draw.polygon(Ship_Flame, Orange, ((3,15),(10,30),(17,15)))
Ship_Flame_Rect = Ship_Flame.get_rect()

#adding ship to group
All_Sprites_List.add(Ship)


#randomly generating 50 asteroid stats to be used later when generating asteroids
for n in range(51):
    #variable size of asteroid using beta distribution, also ensuring asteroid is never of size 0 as this throws an error
    A_x_Width = 200*random.betavariate(10,25) + 10
    A_y_Width = A_x_Width + random.randint(-10,10)
    #randomly choosing colour for asteroid
    A_Colour = random.choice(Asteroid_Colours)
    A_Accel = 0
    A_Velo_x = random.randint(-1000,1000)
    A_Velo_y = random.randint(-1000,1000)
    #random rate of rotation for asteroids
    A_Rotation = random.randint(-5,5)
    A_Mass = 500000*random.betavariate(10,25)
    #creating a list of lists of asteroid stats
    Asteroid_Stats_List.append([A_x_Width, A_y_Width, A_Colour, A_Accel, A_Velo_x, A_Velo_y, A_Rotation, A_Mass])

#creating 1000 stars
for n in range(1001):
    Star = Star_Objects()
    All_Stars.add(Star)
    
    
    
#initialises clock
Clock = pyg.time.Clock()


#################
#   MAIN LOOP   #
#################


while not End_Program:
    #setting frame rate
    Clock.tick(1/dt)
    #exits game if exit button or esc button pressed
    for event in pyg.event.get():
        if event.type == pyg.QUIT:
            End_Program = True
        elif event.type == MOUSEBUTTONDOWN:
            if Start_Text_Rect.collidepoint(event.pos):
                Start_Game = True
            elif How_To_Text_Rect.collidepoint(event.pos):
                How_To_Menu = True
            elif Settings_Rect.collidepoint(event.pos):
                Settings_Menu = True
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                End_Program = True
    #refilling display with navy blue every time screen refreshs
    Main_Window.fill(Navy_Blue)
    #drawing stars
    for Star in All_Stars:
        Star_Objects.display(Star)
    #displaying text, retrieving text rects so text can be clicked on
    text("ESCAPE THE BLACK HOLE", 100, (100,100), True)
    Start_Text, Start_Text_Rect = text("Start The Game", 60, (300,300), False)
    How_To_Text, How_To_Text_Rect = text("How To Play", 60, (300, 400), False)
    Settings_Text, Settings_Rect = text("Gameplay Settings", 60, (300,500), False)
    Main_Window.blit(Start_Text, Start_Text_Rect)
    Main_Window.blit(How_To_Text, How_To_Text_Rect)
    Main_Window.blit(Settings_Text, Settings_Rect)
    #updating display
    pyg.display.flip()

    if How_To_Menu == True:
        #how to play menu
        while (How_To_Menu == True) and (End_Program == False):
            for event in pyg.event.get():
                if event.type == pyg.QUIT:
                    End_Program = True
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        End_Program = True
                    if event.key == K_BACKSPACE:
                        How_To_Menu = False

            Main_Window.fill(Navy_Blue)

            for Star in All_Stars:
                Star_Objects.display(Star)
            
            text("How To Play", 80, (50, 50), True)
            text("In this game you must escape from the Black Hole while dodging incoming asteroids", 30, (100, 150), True)
            text("You control the ship by pressing W to accelerate forwards and A and D to turn", 30, (100, 190), True)
            text("However keep in mind that accelerating will use up precious fuel", 30, (100, 230), True)
            text("You have a few abilities at your disposal", 30, (100, 270), True)
            text("You can launch antimatter bombs at the asteroids to remove them, however ammunition is limited", 30, (100, 310), True)
            text("Press space to launch bombs", 30, (100, 350), True)
            text("You can also tether yourself to asteroids which will increase their effective mass", 30, (100, 390), True)
            text("This is helpful when fuel runs low, but watch out you don't crash into the asteroid", 30, (100, 430), True)
            text("Click and hold on an asteroid to use this ability", 30, (100, 470), True)
            text("Press backspace to go back to main menu", 30, (100, 510), True)
            
            pyg.display.flip()
    elif Settings_Menu == True:
        #settings menu
        while (Settings_Menu == True) and (End_Program == False):
            for event in pyg.event.get():
                if event.type == pyg.QUIT:
                    End_Program = True
                elif event.type == MOUSEBUTTONDOWN:
                    #setting gameplay parameters when different modes of play selected
                    if Easy_Rect.collidepoint(event.pos):
                        Mode_Selected = "EASY"
                        Black_Hole_Mass = 10**32
                        Max_Ammunition = 999999999
                        Max_Fuel = 9*10**99
                        Asteroid_Rate = 50
                    elif Medium_Rect.collidepoint(event.pos):
                        Mode_Selected = "MEDIUM"
                        Black_Hole_Mass = 2*(10**32)
                        Max_Ammunition = 20
                        Max_Fuel = 500
                        Asteroid_Rate = 25
                    elif Hard_Rect.collidepoint(event.pos):
                        Mode_Selected = "HARD"
                        Black_Hole_Mass = 3*(10**32)
                        Max_Ammunition = 5
                        Max_Fuel = 100
                        Asteroid_Rate = 10
                    elif Insane_Rect.collidepoint(event.pos):
                        Mode_Selected = "INSANE"
                        Black_Hole_Mass = 4*(10**32)
                        Max_Ammunition = 999999999
                        Max_Fuel = 99999999
                        Asteroid_Rate = 3
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        End_Program = True
                    if event.key == K_BACKSPACE:
                        Settings_Menu = False

            Main_Window.fill(Navy_Blue)

            for Star in All_Stars:
                Star_Objects.display(Star)

            text("Gameplay Settings", 100, (50, 50), True)
            text("Mode Selected: " + Mode_Selected, 40, (700, 150), True)
            text("Press backspace to go back to main menu", 30, (100, 160), True)
            Easy_Text, Easy_Rect = text("EASY", 50, (100, 200), False)
            text("(Weak Black Hole, Unlimited Bombs, Unlimited Fuel, Fewer Asteroids)", 20, (100,250), True)
            Medium_Text, Medium_Rect = text("MEDIUM", 50, (100, 300), False)
            text("(Average Black Hole, 20 Bombs, 500 Units of Fuel, Normal Asteroid Rate)", 20, (100,350), True)
            Hard_Text, Hard_Rect = text("HARD", 50, (100, 400), False)
            text("(Powerful Black Hole, 5 Bombs, 100 Units of Fuel, Lots of Asteroids)", 20, (100,450), True)
            Insane_Text, Insane_Rect = text("INSANE MODE", 50, (100, 500), False)
            text("(Ridiculous Black Hole, Unlimited Bombs, Unlimited Fuel, Screen Full of Asteroids)", 20, (100,550), True)
            Main_Window.blit(Easy_Text, Easy_Rect)
            Main_Window.blit(Medium_Text, Medium_Rect)
            Main_Window.blit(Hard_Text, Hard_Rect)
            Main_Window.blit(Insane_Text, Insane_Rect)

            pyg.display.flip()
    elif Start_Game == True:
        #actual game loop
        #making sure all gameplay booleans set correctly
        Start_Game = False
        Game_Over = False
        #updating black hole mass and resetting position
        Black_Hole_Object.reset(Black_Hole, Black_Hole_Mass)
        #resetting ship parameters
        Ship_Objects.reset(Ship)
        All_Sprites_List.add(Black_Hole)
        All_Except_Ship.add(Black_Hole)
        All_Sprites_List.add(Ship)
        #setting gameplay parameters according to difficulty level
        Ammunition = Max_Ammunition
        Fuel = Max_Fuel
        while not (End_Program or Game_Over or Escaped_Black_Hole):
            Game_Over = False
            #sets frame rate
            Clock.tick(1/dt)
             
            #checks for events
            for event in pyg.event.get():
                if event.type == pyg.QUIT:
                    End_Program = True
                elif event.type == MOUSEBUTTONDOWN:
                    #checks if any asteroids have been tethered
                    for Asteroid in All_Asteroids_List:
                        if Asteroid.Active_Sprite_Rect.collidepoint(event.pos):
                            Tethered.add(Asteroid)
                            #increasing effective mass of asteroid
                            Asteroid.Mass *= 10**25
                elif event.type == MOUSEBUTTONUP:
                    for Asteroid in Tethered:
                        #returning effective mass of asteroid to normal
                        Asteroid.Mass *= 10**-25
                    Tethered.empty()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        End_Program = True
                    elif event.key == K_w:
                        if Fuel != 0:
                            Ship.Acceleration = Ship.Ship_Acceleration
                    elif event.key == K_a:
                        Ship.Rotation = -Rate_Of_Rotation
                    elif event.key == K_d:
                        Ship.Rotation = Rate_Of_Rotation
                    elif event.key == K_SPACE:
                        #firing bomb if possible
                        if Ammunition != 0:
                            Bomb = Projectiles()
                            All_Projectiles.add(Bomb)
                            Ammunition -= 1
                elif event.type == KEYUP:
                    if event.key == K_w:
                        Ship.Acceleration = 0
                    elif event.key == K_a:
                        Ship.Rotation  = 0
                    elif event.key == K_d:
                        Ship.Rotation = 0

            #these variables are used by a few functions, so they are recalulated every frame
            Distance_To_Black_Hole, Bearing_To_Black_Hole = polar_coordinates(Black_Hole.Position_x, Black_Hole.Position_y, Screen_Width/2, Screen_Height/2)

            #adds asteroids, lower asteroid_rate means more asteroids
            if random.randint(1,Asteroid_Rate) == 1:
                i = random.randint(0,50)
                #giving asteroid random attributes
                Asteroid = Asteroid_Objects(Asteroid_Stats_List[i])
                All_Sprites_List.add(Asteroid)
                All_Asteroids_List.add(Asteroid)
                All_Except_Ship.add(Asteroid)
                
            #updating ship sprite
            Ship_Objects.update(Ship)

            #predicting new ship path after ship variables updated
            predicted_path(50)
            #updating black hole
            Black_Hole_Object.update(Black_Hole)
            #updating bombs
            for Bomb in All_Projectiles:
                Projectiles.update(Bomb)

            #updating all asteroids
            for Asteroid in All_Asteroids_List:
                Asteroid_Objects.update(Asteroid)
                #testing if antimatter bombs collide with an asteroid, and annhilating asteroid if so 
                for Bomb in All_Projectiles:
                    if pyg.sprite.collide_circle(Bomb, Asteroid):
                        All_Sprites_List.remove(Asteroid)
                        All_Asteroids_List.remove(Asteroid)
                        All_Except_Ship.remove(Asteroid)
                        All_Projectiles.remove(Bomb)
                #testing if asteroid has been sucked into the black hole
                if pyg.sprite.collide_circle(Asteroid, Black_Hole):
                    All_Sprites_List.remove(Asteroid)
                    All_Asteroids_List.remove(Asteroid)
                    All_Except_Ship.remove(Asteroid)
                #using more accurate hit detection between ship and asteroid to make it more fair for the user
                collide_r = polar_coordinates(Asteroid.Position_x, Asteroid.Position_y, Screen_Width/2, Screen_Height/2, False)
                if collide_r < (Asteroid.radius/2) + 5:
                    Game_Over = True
                    
            
            #using itertools module function to test all asteroid combinations for collisions
            for Asteroid_A, Asteroid_B in combinations(All_Asteroids_List, 2):
                collide_r = polar_coordinates(Asteroid_A.Position_x, Asteroid_A.Position_y, Asteroid_B.Position_x, Asteroid_B.Position_y, False)
                if collide_r < Asteroid_A.radius+Asteroid_B.radius:
                    #crude method for asteroid collision modelling, swaps velocitys between asteroids
                    Asteroid_A.Velocity_x, Asteroid_B.Velocity_x = Asteroid_B.Velocity_x, Asteroid_A.Velocity_x
                    Asteroid_A.Velocity_y, Asteroid_B.Velocity_y = Asteroid_B.Velocity_y, Asteroid_A.Velocity_y
            
            #testing if ship been pulled into black hole
            #can go quite deep into black hole before game over, means small slip ups not punished to badly
            collide_r = polar_coordinates(Black_Hole.Position_x, Black_Hole.Position_y, Screen_Width/2, Screen_Height/2, False)
            if collide_r < Black_Hole.radius:
                Game_Over = True
            #testing if ship has gotten sufficiently far enough from the black hole yet for game win state
            if int(Distance_To_Black_Hole/200) > 100:
                Escaped_Black_Hole = True
            #refilling window with space colour
            Main_Window.fill(Navy_Blue)
            #displaying stars
            for Star in All_Stars:
                Star_Objects.display(Star)
            #displaying black hole
            Black_Hole_Object.display(Black_Hole)
            #displaying ship
            Ship_Objects.display(Ship)
            #displaying asteroids
            for Asteroid in All_Asteroids_List:
                Asteroid_Objects.display(Asteroid)
            #displaying ship path prediction if ship not using engines
            #draws all dots that have been calculated
            if Ship.Acceleration == 0:
                for i in range(50, 50-Dots_Calculated, -1):
                    Ship_Path_Objects.display(Dots[i])
            else:
                #displaying ship engine flame if ship using engines
                display_flame()
                #reducing fuel while engines burning
                if Fuel != 0:
                    Fuel -= 1
                #ensuring ship engines cut out if no fuel
                else:
                    Ship.Acceleration = 0
            #dispaying bombs
            for Bomb in All_Projectiles:
                Projectiles.display(Bomb)
            #displaying text
            text("Percentage of way to Safe Zone", 18, (Screen_Width-250,10), True)
            text(str(int(Distance_To_Black_Hole/200))+"%", 48, (Screen_Width-70,10), True)
            if Mode_Selected != ("EASY" or "INSANE"):
                #displaying ammunition and fuel count if relevant to game mode
                text("Ammunition Remaining", 18, (Screen_Width-250,60), True)
                text("Percentage of Fuel Remaining", 18, (Screen_Width-250,110), True)
                text(str(Ammunition), 48, (Screen_Width-70,60), True)
                text(str(int(100*Fuel/Max_Fuel))+"%", 48, (Screen_Width-70,110), True)
            
            
            #displaying all drawn objects on the display
            pyg.display.flip()
        else:
            #if loop not ending due to the game being closed, displays relevant message
            if End_Program != True:
                if Game_Over == True:
                    Game_Over = False
                    text("GAME OVER", 200, (200, 300), True)
                elif Escaped_Black_Hole == True:
                    Escaped_Black_Hole = False
                    text("YOU ESCAPED THE BLACK HOLE!", 80, (100, 300), True)
                pyg.display.flip()
                #emptying all groups as part of reset
                All_Asteroids_List.empty()
                All_Projectiles.empty()
                All_Sprites_List.empty()
                time.sleep(2)
            
        
if End_Program == True:
    #quiting pygame if game closed
    pyg.quit()
    sys.exit()
