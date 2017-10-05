# Essentially implements vector datatype
# Conveniently inherits relevant Python operators
class Vec:
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def getX(self):
        return self.x
    def getY(self):
        return self.y
    def tuple(self):
        return (self.x,self.y)
    def __neg__(self):
        return Vec(-self.x,-self.y)
    def __add__(self, other):
        return Vec(self.x+other.getX(),self.y+other.getY())
    def __sub__(self, other):
        return Vec(self.x-other.getX(),self.y-other.getY())
    def __mul__(self, other):
        return self.x*other.getX()+self.y*other.getY()
    def __rmul__(self, other):
        return Vec(other*self.x,other*self.y)
    def __pow__(self, other):
        if other == 1:
            return self
        return self*(self**(other-1))
    def __truediv__(self, other):
        return Vec(self.x/other,self.y/other)
    def __str__(self):
        return "<" + str(self.x) + "," + str(self.y) + ">"