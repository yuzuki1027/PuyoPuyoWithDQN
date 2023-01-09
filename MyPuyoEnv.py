import gym
import math
import random
import sys
import urllib
from collections import defaultdict


class MyPuyoEnv(gym.Env):
    def __init__(self):
        self.colors = {-1: '', 0: '', 2: '\033[34m', 4: '\033[92m',
                       1: '\033[95m', 3: '\033[93m', 5: '\033[91m'}
        self.X = 6 + 2
        self.Y = 13 + 2
        self.xys = [(1 + (x % 6)) + (1 + (x//6)) * 8 for x in range(6*13)]

        self.rensa_bonus = [0, 8, 16, 32, 64, 96, 128, 160, 192,
                            224, 256, 288, 320, 352, 388, 416, 448, 480, 512]

        self.doujikesi_bonus = [0, 0, 0, 0, 0, 2, 3, 4, 5, 6, 7, 10] + [10]*100
        self.doujikesi_color_bonus = [0, 0, 3, 6, 12, 24]

    def reset():  # 環境のリセット　1エピソードの最初
        pass

    def step():  # 1ステップ進める
        pass

    def render():  # 描画
        pass

    def print_field(self, field, highlight_pos=None, next_puyos=None):
        if next_puyos:
            line = ""
            for ps in next_puyos:
                for p in ps:
                    line += self.colors.get(p) + "%2d" % p + '\033[0m'
                line += " -> "
            print(line)
        for y in range(self.Y):
            line = ""
            for x in range(self.X):
                p = field[x+y*8]
                if highlight_pos and any([pos == x+y*8 for pos in highlight_pos]):
                    line += "\033[40m"
                line += self.colors.get(p) + "%2d" % p + '\033[0m'
            print(line)

    def get_connections(self, field):
        visited = [0]*self.X*self.Y
        ret = []
        for x in self.xys:
            if field[x] <= 0 or visited[x]:
                continue
            connected = self.get_connected(field, x, visited)
            ret.append(connected)
        return ret

    def get_connected(self, field, x, visited=None):
        if visited == None:
            visited = []

        p = field[x]
        s = [x]
        # count = 0
        connected = []
        while s:
            x = s.pop()
            if visited[x]:
                continue
            visited[x] = True
            connected.append(x)
            for dx in (-1, 1, 8, -8):
                xx = dx + x
                if field[xx] == p and not visited[xx]:
                    s.append(xx)
        return connected

    def vanish(self, field, vanished):
        dys = [0]*self.X*self.Y
        for x in vanished:
            field[x] = 0
            for x in range(x-8, 0, -8):
                dys[x] += 1
        # self.print_field(self.field, vanished)
        # self.print_field(dys)
        for x in reversed(self.xys):
            dy = dys[x]
            if dy > 0:
                field[x+dy*8] = field[x]
        for x in range(self.X):
            for y in range(dys[x]):
                field[x+(y+1)*8] = 0

    def fire(self, field, fire_from=None, connections=None):
        n = 0
        total_score = 0
        if fire_from:
            # print("fire_from:", fire_from)
            self.vanish(field, fire_from)
            n += 1
        while True:
            score = self.rensa_bonus[n]
            if n != 0 or connections == None:
                connections = self.get_connections(field)
            vanished = []
            for c in connections:
                if len(c) >= 4:
                    score += self.doujikesi_bonus[len(c)]
                    vanished += c

            if not vanished:
                break
            colors = set()
            for x in vanished:
                colors.add(field[x])
            score += self.doujikesi_color_bonus[len(colors)]
            total_score += score * len(vanished) * 10
            self.vanish(field, vanished)

            n += 1
        return (n, total_score)

    def get_height(self, field):
        height = [100]
        for x in range(1, 7):
            for y in range(13, 0, -1):
                if field[x + y*8] <= 0:
                    height.append(y)
                    break
        height.append(100)
        return height

    def get_candidate_pos_internal(self, field, puyo):
        pos_list = []
        heights = self.get_height(field)
        for x in range(1, 7):
            if heights[x] > 2:
                pos_list.append((x + heights[x]*8, x + (heights[x]-1)*8))
            if heights[x] > 1 and heights[x+1] > 1 and x <= 5:
                pos_list.append((x + heights[x]*8, x + 1 + heights[x+1]*8))
        return pos_list

    def get_candidate_pos(self, field, puyo):
        pos_list = self.get_candidate_pos_internal(field, puyo)
        if puyo[0] != puyo[1]:
            pos_list += [(b, a) for (a, b) in pos_list]
        return pos_list

    def get_flatness(self, field):
        f = 0
        heights = self.get_height(field)[1:7]

        d0 = heights[1] - heights[0]

        if d0 < 0:
            f += d0 / 1.0
        d5 = heights[5] - heights[4]

        if d5 > 0:
            f -= d5 / 1.0
        d = max(1, (max(heights) - min(heights))) / 4.0
        f -= d
        dekoboko = 0

        for i in range(0, 5):
            dekoboko += abs(heights[i+1] - heights[i])
        f -= dekoboko / 10.0
        return f

    def put(self, field, pos, puyo):
        field[pos[0]] = puyo[0]
        field[pos[1]] = puyo[1]
        return field

    def take(self, field, pos, puyo):
        field[pos[0]] = 0
        field[pos[1]] = 0
        return field


data = ""

env = MyPuyoEnv()

flatness_table = [1.0, 1.0, 0.95, 0.9, 0.85,
                  0.7, 0.5, 0.3, 0.1, 0, 0, 0, 0, 0, 0]
connection_scores = [0.0, 0.0, 0.7, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5] + [0.5]*10


def eval(field, v=False):
    cs = env.get_connections(field)

    score = 0
    if not cs:
        return 0

    flatness = env.get_flatness(field)
    scores = []
    hakkaten = defaultdict(set)
    seen_hakka = set()

    for c in cs:
        for x in c:
            for dx in (-1, 1, -8):
                xx = x + dx
                if field[xx] == 0:
                    hakkaten[(xx, field[x])].update(c)

    deduped_hakkaten = {}
    seen_hakka = set()
    for h in hakkaten:
        c = tuple(hakkaten[h])
        if c not in seen_hakka:
            deduped_hakkaten[h] = c
            seen_hakka.add(c)
    
    for h in deduped_hakkaten:
        c = hakkaten[h]

        field_ = field[:]
        num_rensa_, score_ = env.fire(field_, fire_from=c)
        gomi = [True for x in env.xys if field_[x] != 0]

        score_ = math.log(max(score_, 1))
        penalized_rensa = num_rensa_
        if len(c) == 1:
            penalized_rensa *= 0.7
        elif(len(c)) == 2:
            penalized_rensa *= 0.9

        scores.append((num_rensa_, penalized_rensa, score_, len(gomi)))
    avg_connections = sum([connection_scores[len(deduped_hakkaten[h])]
                          for h in deduped_hakkaten]) / len(deduped_hakkaten)

    if v:
        print(deduped_hakkaten)
    sorted_rensas = sorted(scores, key=lambda x: x[1], reverse=True)
    topn = 4
    if len(sorted_rensas) == 1:
        topn_rensa = 0
    else:
        topn_rensa = float(
            sum([x[1] for x in sorted_rensas[1:topn]])) / len(sorted_rensas[1:topn])

    score = avg_connections * 2.0 + flatness * 2.0 + \
        topn_rensa / 2.0 + sorted_rensas[0][1]

    if v:
        print("scores: ", sorted_rensas)
        print("max_rensa: ", sorted_rensas[0][0])
        print("max_score: ", sorted_rensas[0][2])
        print("gomi: ", sorted_rensas[0][3])
        print("flatness: ", flatness)
        print("avg_connections: ", avg_connections)
        print("topn_rensa: ", topn_rensa)
        print("total score: ", score)
    
    return score

def ai(field, puyos, v=0):
    max_score = -100000
    max_pos = None

    for pos1 in env.get_candidate_pos(field, puyos[0]):
        field1 = env.put(field[:], pos1, puyos[0])
        (num_rensa, score) = env.fire(field1)
        if num_rensa > 0:
            continue

        if v > 1:
            print("score: %.2f rensa: %d " % (score, num_rensa))
            env.print_field(field1, pos1)
        score1 = eval(field1, v=v > 0)
        for pos2 in env.get_candidate_pos(field1, puyos[1]):
            
            field2 = env.put(field1[:], pos2, puyos[1])
            (num_rensa, score) = env.fire(field2)
            if num_rensa > 0:
                continue
            score = eval(field2)
            if v > 1:
                print("  score: %.2f rensa: %d" % (score, num_rensa))
            if num_rensa > 0:
                continue
            score += score1 * 0.0001
            if score > max_score:
                max_score = score
                max_pos = (pos1, pos2)
    return max_pos[0]


field = [-1]*8
field += [-1, 0, 0, 0, 0, 0, 0, -1]*13
field += [-1]*8

data = ""
V = 0
for a in sys.argv[1:]:
    try:
        V = int(a)
    except:
        pass

if len(sys.argv) > 1:
    url = sys.argv[1]
    if url.startswith("-1"):
        for line in url.split("\n"):
            if line:
                field.append([])
                for i in range(len(line)/2):
                    field[-1].append(int(line[i*2: i*2+2]))
    elif url.startswith("http"):
        if url.startswith("http://bit.ly"):
            url = urllib.urlopen(url).geturl()
        import re
        m = re.match('.*rensim/\?\?(\d+)', url)
        data = m.group(1)
        x, y = (6, 13)
        mapping = {'0': 0, '4': 1, '5': 2, '6': 3, '7': 4, '8': 5}
        for d in reversed(data):
            field[x+y*8] = mapping[d]
            x -= 1
            if x == 0:
                x = 6
                y -= 1

env.print_field(field)
num_rensa, score = env.fire(field)
eval(field, v=1)
#print(num_rensa)

if num_rensa > 0:
    print("%d rensa %d points" % (num_rensa, score))
    env.print_field(field)

random.seed(15)
puyos = []

for i in range(35):
    puyos.append((random.randint(1, 4), random.randint(1, 4)))

for i in range(len(puyos)-3):
    print(i)
    pos = ai(field, puyos[i:i+2], v = V)
    env.put(field, pos, puyos[i])
    env.print_field(field, highlight_pos=pos)
    eval(field, v=True)
    num_rensa, score = env.fire(field)
    if num_rensa > 0:
        print("%d rensa %d points" % (num_rensa, score))


            


    
        
