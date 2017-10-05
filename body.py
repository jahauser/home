# Class designed for moving objects in orbital simulator
# Keeps mass, position, velocity, radius, colour, name, tracing information
# Facilitates easy velocity and position changes
class Body:
    def __init__(self, mass, radius, position, velocity, colour, name):
        self.mass = mass
        self.rad = radius
        self.pos = position
        self.vel = velocity
        self.colour = colour
        self.name = name
        self.trace = []
    def getMass(self):
        return self.mass
    def getPos(self):
        return self.pos
    def getVel(self):
        return self.vel
    def getColour(self):
        return self.colour
    def getRad(self):
        return self.rad
    def getName(self):
        return self.name
    def move(self,dt):
        self.pos += dt*self.vel
    def boost(self, boost):
        self.vel += boost
    def shift(self, dpos):
        self.pos += dpos
    def addTrace(self, cap):
        if len(self.trace) >= cap:
            self.trace = self.trace[1:]
            self.trace.append((self.pos,0.001,self.colour))
        else:
            self.trace.append((self.pos,0.001,self.colour))
    def getTrace(self):
        return self.trace
    def clearTrace(self):
        self.trace = []
    def __str__(self):
        return self.name + "\nmass: " + str(self.mass) + " radius: " + str(self.rad) + " position: " + self.pos.__str__() + " velocity: " + self.vel.__str__() + "\n"