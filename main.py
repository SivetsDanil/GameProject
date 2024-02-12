import pygame
import copy
import time
import sys
import os


def terminate():
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


FPS = 50
pygame.init()
size = width, height = 500, 500
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
tile_images = {
    'wall': load_image('box.png'),
    'empty': load_image('grass.png')
}
hunter_image = pygame.transform.scale(load_image('bomb2.png'), (50, 50))
player_image = load_image('mario.png')
hunter = None
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
hunter_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
box_group = pygame.sprite.Group()
tile_width = tile_height = 50


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def clear():
    for item in all_sprites:
        item.kill()
    for item in tiles_group:
        item.kill()
    for item in hunter_group:
        item.kill()
    for item in box_group:
        item.kill()


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        board = []
        self.p_cord = [3, 3]
        for i in load_level('map.txt'):
            board.append(list(map(int, i.replace('.', '0,').replace('#', '1,').replace('@', '2,').split(',')[:-1])))
        self.level = board
        self.left = 0
        self.top = 0
        self.cell_size = 2
        self.last = []

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def render(self):
        new_hunter, x, y = None, None, None
        clear()
        for y in range(len(self.level)):
            for x in range(len(self.level[y])):
                if self.level[y][x] == 0:
                    Tile('empty', x, y)
                elif self.level[y][x] == 1:
                    Tile('wall', x, y)
                elif self.level[y][x] == 2:
                    Tile('empty', x, y)
                    new_hunter = Hunter(self, x, y)
                    self.flag = 1
                    self.cords = (x, y)
        new_player = Player(self)
        all_sprites.draw(screen)
        return new_hunter, new_player

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        x = (x - self.left) // self.cell_size
        y = (y - self.top) // self.cell_size
        if x < self.width and y < self.height:
            return x, y


class Hunter(pygame.sprite.Sprite):
    def __init__(self, board, pos_x, pos_y):
        super().__init__(hunter_group, all_sprites)
        self.image = hunter_image
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)
        self.board = board

    def has_path(self, x1, y1, x2, y2):
        self.table = copy.deepcopy(self.board.level)
        for i in range(len(self.table)):
            for j in range(len(self.table)):
                if self.table[i][j] == 1:
                    self.table[i][j] = -1
        self.table[y2][x2] = -2
        self.rec([(x2, y2)], x1, y1)
        if self.table[y1][x1] != 0:
            return True

    def get_click(self, mouse_pos):
        cell = self.board.get_cell(mouse_pos)
        self.go_to(cell)

    def go_to(self, cell):
        if self.board.flag != 0 and self.board.level[cell[1]][cell[0]] == 0:
            if self.has_path(cell[0], cell[1], self.board.cords[0], self.board.cords[1]):
                self.save = [cell[0], cell[1]]
                self.board.flag = 0
                self.i_cord = cell
                self.show_path()

    def rec(self, points, x, y):
        p = []
        c = 0
        for (x0, y0) in points:
            for a in range(-1, 2):
                for b in range(-1, 2):
                    try:
                        if x0 + a == -1 or y0 + b == -1 or abs(a) == abs(b):
                            continue
                        if x0 + a == x and y0 + b == y:
                            self.table[y0 + b][x0 + a] = self.table[y0][x0] + 1 + 2 * bool(self.table[y0][x0] == -2)
                            return
                        if self.table[y0 + b][x0 + a] == 0:
                            c = 1
                            self.table[y0 + b][x0 + a] = self.table[y0][x0] + 1 + 2 * bool(self.table[y0][x0] == -2)
                            p.append((x0 + a, y0 + b))
                    except IndexError:
                        pass
        if c == 0:
            return
        self.rec(p, x, y)

    def show_path(self):
        self.actions = []
        while self.board.cords != self.i_cord:
            x0, y0 = self.i_cord
            x1, y1 = 0, 0
            self.board.level[y0][x0] = 0
            for a in range(-1, 2):
                for b in range(-1, 2):
                    try:
                        if x0 + a == -1 or y0 + b == -1 or abs(a) == abs(b):
                            continue
                        if self.table[y0 + b][x0 + a] == -2:
                            x1 = -1
                            break
                        if (self.table[y0 + b][x0 + a] < self.table[y0][x0] and self.table[y0 + b][x0 + a] != -1
                                and self.table[y0 + b][x0 + a] != 0):
                            x1 = x0 + a
                            y1 = y0 + b
                            break
                    except IndexError:
                        pass
                if x1 != 0 or y1 != 0:
                    break
            if x1 == -1:
                x1, y1 = self.board.cords
            self.actions.append((x0, y0, x1, y1))
            self.i_cord = (x1, y1)

    def update(self):
        try:
            if self.actions:
                x1, y1, x0, y0 = self.actions[::-1][0]
                self.board.level[y1][x1] = 2
                self.board.level[y0][x0] = 0
                self.board.render()
                pygame.display.flip()
                self.actions = self.actions[:-1]
            else:
                self.board.flag = 1
                self.board.cords = (self.actions[0][0], self.actions[0][1])
        except Exception:
            pass


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        if tile_type == 'wall':
            super().__init__(tiles_group, box_group, all_sprites)
        else:
            super().__init__(tiles_group, all_sprites)
        self.image = pygame.transform.scale(tile_images[tile_type], (50, 50))
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Player(pygame.sprite.Sprite):
    def __init__(self, board):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.board = board
        self.rect = self.image.get_rect().move(tile_width * board.p_cord[0] + 15, tile_height * board.p_cord[1] + 5)

    def go(self, event):
        if event.dict['key'] == 1073741904:
            player.rect.x -= 50
            board.p_cord[0] -= 1
            if pygame.sprite.spritecollideany(self, box_group):
                board.p_cord[0] += 1
                player.rect.x += 50
        if event.dict['key'] == 1073741903:
            board.p_cord[0] += 1
            player.rect.x += 50
            if pygame.sprite.spritecollideany(self, box_group):
                player.rect.x -= 50
                board.p_cord[0] -= 1
        if event.dict['key'] == 1073741906:
            player.rect.y -= 50
            board.p_cord[1] -= 1
            if pygame.sprite.spritecollideany(self, box_group):
                player.rect.y += 50
                board.p_cord[1] += 1
        if event.dict['key'] == 1073741905:
            player.rect.y += 50
            board.p_cord[1] += 1
            if pygame.sprite.spritecollideany(self, box_group):
                player.rect.y -= 50
                board.p_cord[1] -= 1
        board.render()


def start_screen():
    intro_text = ["ЗАСТАВКА", "",
                  "Правила игры",
                  "Если в правилах несколько строк,",
                  "приходится выводить их построчно"]

    fon = pygame.transform.scale(load_image('fon.jpg'), screen.get_size())
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


def end_screen():
    time.sleep(0.50)
    cur = Gameover()
    MYEVENTTYPE = pygame.USEREVENT + 1
    pygame.time.set_timer(MYEVENTTYPE, 2)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and cur.flag == 1:
                terminate()
            if event.type == MYEVENTTYPE:
                cur.update()
                screen.blit(cur.image, (cur.x, cur.y))
        pygame.display.flip()
    terminate()


class Gameover(pygame.sprite.Sprite):
    image = load_image("gameover.png")

    def __init__(self, *group):
        super().__init__(*group)
        self.image = Gameover.image
        self.rect = self.image.get_rect()
        self.x = -600
        self.y = 0
        self.f = 0
        self.flag = 0

    def update(self):
        if self.x != 0:
            self.x += 1
        else:
            self.flag = 1


if __name__ == '__main__':
    level_x, level_y = len(load_level('map.txt')[0]), len(load_level('map.txt'))
    board = Board(level_x, level_y)
    board.set_view(0, 0, 50)
    running = True
    pygame.init()
    pygame.display.set_mode((level_x * 50, level_y * 50))
    pygame.display.set_caption('test')
    MYEVENTTYPE = pygame.USEREVENT + 1
    timer = 200
    start_screen()
    pygame.time.set_timer(MYEVENTTYPE, timer)
    screen.fill((0, 0, 0))
    hunter, player = board.render()
    pygame.display.flip()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == MYEVENTTYPE:
                hunter.update()
                pygame.display.flip()
            if event.type == pygame.KEYDOWN:
                player.go(event)
                hunter.go_to(board.p_cord)
            if pygame.sprite.spritecollideany(player, hunter_group):
                end_screen()