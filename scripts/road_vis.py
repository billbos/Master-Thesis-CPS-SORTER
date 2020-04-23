import sys
import matplotlib.pyplot as plt
import json

class Point:
    def __init__(self,x_init,y_init):
        self.x = x_init
        self.y = y_init

    def shift(self, x, y):
        self.x += x
        self.y += y

    def __repr__(self):
        return "".join(["Point(", str(self.x), ",", str(self.y), ")"])
    
    def __eq__(self, other):
        if (self.x == other.x) and (self.y == other.y):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

class Curve:
    def __init__(self, start, end, turning_point, type):
        self.start = start
        self.end = end
        self.turning_points = turning_point
        self.type = type

def find_turning_points(gradients):
    turning_points = []
    for i in range(0, len(gradients) -1):
        if gradients[i] > 0 and gradients[i+1] < 0:
            turning_points.append(i)
            # print(gradients[i], gradients[i+1])
        elif gradients[i] < 0 and gradients[i+1] > 0:
            turning_points.append(i)
            # print(gradients[i], gradients[i+1])
    return turning_points

def find_curves(steering):
    curves = {
        'right': 0,
        'left': 0,
        'straight': 0
    }
    indexes = []
    straight = 0
    right = -1
    left = 1
    old_state = straight
    for i in range(0, len(steering)-1):
        if steering[i] == 0 and steering[i+1] == 0:
            current_state = straight
        if steering[i] > 0 and steering[i+1] > 0:
            current_state = left
        if steering[i] < 0 and steering[i+1] < 0:
            current_state = right
        if old_state != current_state:
            old_state = current_state
            indexes.append(i)
            if old_state == straight:
                curves['straight'] += 1
                print('Straight!')
            if old_state == right:
                curves['right'] += 1
                print('right!')
            if old_state == left:
                curves['left'] += 1
                print('left!')
    return curves, indexes

            

def remove_duplicates(points):
    return  [points[i] for i in range(0, len(points)-1) if points[i] != points[i+1]]

def get_gradients(points):
    gradients = []
    for i in range(0, len(points)-1):
        gradients.append(grad(points[i], points[i+1]))
    return gradients

def main(file):
    try:
        with open(file) as json_file:
            data = json.load(json_file)
            points = []
            steering = []
            for state in data['states']:
                points.append(Point(state['pos_x'],state['pos_y']))
                steering.append(state['steering'])
            # points = remove_duplicates(points)
            gradients = get_gradients(points)
            turning_points = find_turning_points(gradients)

            plt.plot([point.x for point in points],[point.y for point in points])
            curves, indexes = find_curves(steering)
            turning_points = [plt.plot(points[index].x, points[index].y, 'g*') for index in indexes]
            print(curves)
            plt.show()
            return curves
    except Exception as e:
        print(e)
        # pass

def grad(a:Point, b:Point) -> float:
    try:
        grad = (b.y - a.y) / (b.x - a.x)
    except Exception:
        # print(a,b)
        return (b.y - a.y)
    return grad
if __name__ == '__main__':
    main(sys.argv[1])