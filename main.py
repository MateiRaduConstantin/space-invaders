import sys
import random
import time
import math
import copy
import pygame

WIDTH = 1400
HEIGHT = 980

FPS = 60

COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
ENEMY_WIDTH, ENEMY_HEIGHT = 50, 50
ENEMY_SPACING = 20
ENEMY_DELAY_HEIGHT = (ENEMY_SPACING + ENEMY_HEIGHT)

BULLET_WIDTH, BULLET_HEIGHT = 5, 10

SEGMENT_COUNT = 5
MAX_ENEMIES = 12

ENEMY_SPAWN_INTERVAL = 5
ENEMY_SPEED = 1
ENEMY_SINE_SPEED = 1
BULLET_DELAY = 150
ENEMY_SPAWN_DELAY = 1000
SCORE_COLOR = (0, 0, 0)
LEVEL_COLOR = (0, 0, 0)

def initialize_game_parameters():
    enemy_img = pygame.image.load("enemy.png")
    enemy_img = pygame.transform.scale(enemy_img, (ENEMY_WIDTH, ENEMY_HEIGHT))
    game_params = {
        "background": pygame.Surface((WIDTH, HEIGHT)),
        "font": pygame.font.Font(None, 36),
        "score": 0,
        "score_text": None,
        "level": 1,
        "last_spawn_time": 0,
        "shooting": False,
        "shooting_interval": 1,
        "shooting_chance": 0.01,
        "enemy_font_speed": 0.53,
        "occupied_segments": [False] * SEGMENT_COUNT,
        "last_bullet_time": 0,
        "bullets": [],
        "enemy_bullets": [],
        "enemies": [([Enemy(enemy_img, random.randint(0, WIDTH - ENEMY_WIDTH), 0, ENEMY_WIDTH, ENEMY_HEIGHT, 0)], None, [0, WIDTH])],
        "enemy_img": enemy_img,
        "enemies_killed": 0,
    }
    return game_params

def update_bullets(game_params):
    for bullet in game_params["bullets"].copy():
        bullet.y -= 5
        if bullet.y < 0:
            game_params["bullets"].remove(bullet)
        else:
            pygame.draw.rect(game_params["background"], COLOR_GREEN, bullet)

def process_bullet_creation(game_params, ship_img_rect):
    keys_pressed = pygame.key.get_pressed()
    if keys_pressed[pygame.K_SPACE] and pygame.time.get_ticks() - game_params["last_bullet_time"] >= BULLET_DELAY:
        bullet = pygame.Rect(ship_img_rect.centerx - BULLET_WIDTH, ship_img_rect.y - BULLET_HEIGHT, BULLET_WIDTH, BULLET_HEIGHT)
        game_params["bullets"].append(bullet)
        game_params["last_bullet_time"] = pygame.time.get_ticks()

class Ship:
    def __init__(self):
        self.img = pygame.image.load("ship.png")
        self.width = self.img.get_width() // 2
        self.height = self.img.get_height() // 2
        self.img = pygame.transform.scale(self.img, (self.width, self.height))
        self.rect = self.img.get_rect()
        self.rect.topleft = (WIDTH // 2, HEIGHT - self.rect.height)
        self.speed = 5

    def update_position(self, keys_pressed):
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            self.rect.x = max(0, self.rect.x - self.speed)
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            self.rect.x = min(WIDTH - self.rect.width, self.rect.x + self.speed)
        return self.rect

    def draw(self, background):
        background.blit(self.img, self.rect)

def spawn_enemies(game_params):
    if time.time() - game_params["last_spawn_time"] > ENEMY_SPAWN_INTERVAL:
        available_segments = [i for i, occupied in enumerate(game_params["occupied_segments"]) if not occupied]
        if available_segments:
            total_enemies = sum(len(enemy_group) for enemy_group in game_params["enemies"])
            if total_enemies < MAX_ENEMIES:
                segment = random.choice(available_segments)
                game_params["occupied_segments"][segment] = True
                segment_bounds = (segment * (WIDTH / SEGMENT_COUNT), (segment + 1) * (WIDTH / SEGMENT_COUNT) - ENEMY_WIDTH)
                spawn_x = int(segment * (WIDTH / SEGMENT_COUNT) + (WIDTH / SEGMENT_COUNT) / 2 - ENEMY_WIDTH / 2)

                if game_params["level"] > 1:
                   enemies = []
                   for i in range(4):
                       y_position = -(ENEMY_DELAY_HEIGHT * 2) - i * (ENEMY_DELAY_HEIGHT * 2)
                       enemy = Enemy(game_params["enemy_img"], spawn_x, y_position, ENEMY_WIDTH, ENEMY_HEIGHT, time.time())
                       enemies.append(enemy)
                else:
                   single_enemy = Enemy(game_params["enemy_img"], spawn_x, 0, ENEMY_WIDTH, ENEMY_HEIGHT, time.time())
                   enemies = [single_enemy]

                game_params["enemies"].append((enemies, segment, segment_bounds))
                game_params["last_spawn_time"] = time.time()

def handle_bullet_enemy_collision(game_params, enemy, enemy_group):
    for bullet in game_params["bullets"].copy():
        if enemy.rect.colliderect(bullet):
            enemy_group.remove(enemy)
            game_params["bullets"].remove(bullet)
            game_params["enemies_killed"] += 1
            game_params["score"] += 100  # Increment score
            break

def update_enemy_bullets(game_params, ship_hitbox):
    for bullet in game_params["enemy_bullets"].copy():
        bullet.y += 5
        if bullet.y > HEIGHT:
            game_params["enemy_bullets"].remove(bullet)
        else:
            pygame.draw.rect(game_params["background"], COLOR_RED, bullet)

            if bullet.colliderect(ship_hitbox):
                pygame.event.post(pygame.event.Event(pygame.QUIT))

def update_enemy_group(game_params, enemy_data, ship_img_rect):
    enemy_group, segment, segment_bounds = enemy_data
    if len(enemy_group) == 0:
        game_params["enemies"].remove(enemy_data)
        if segment is not None:
            game_params["occupied_segments"][segment] = False
        return None

    group_leader = enemy_group[0]
    time_since_spawn = time.time() - group_leader.spawn_time
    group_leader.rect.x += ENEMY_SINE_SPEED * math.sin(time_since_spawn)
    group_leader.rect.x = max(segment_bounds[0], min(group_leader.rect.x, segment_bounds[1] - group_leader.width))

    dx = ship_img_rect.x - group_leader.rect.x
    dy = ship_img_rect.y - group_leader.rect.y
    dist = math.sqrt(dx**2 + dy**2)

    dx /= dist
    dy /= dist

    return dx, dy

def update_level(game_params):
    if game_params["level"] < 2 and game_params["enemies_killed"] >= 3:
        game_params["level"] = 2
        game_params["shooting_interval"] = 1.5
    if  game_params["level"] < 3 and game_params["enemies_killed"] >= 10:
        game_params["level"] = 3
        game_params["shooting_interval"] = 1
        game_params["shooting_chance"] = 0.04
        game_params["enemy_font_speed"] = 1
    return game_params

class Enemy:
    def __init__(self, img, x, y, width, height, spawn_time):
        self.width = width
        self.height = height
        self.img = img
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.spawn_time = spawn_time

    def draw(self, background):
        background.blit(self.img, self.rect)

    def update_enemy(self, group_leader, enemy_position, time_since_spawn, enemy_group, game_params):
        if enemy_position != 0:
            sine_factor = ENEMY_SINE_SPEED * (time_since_spawn + enemy_position/len(enemy_group))
            x_offset = enemy_position * ENEMY_DELAY_HEIGHT * math.sin(sine_factor)
            self.rect.x = group_leader.rect.x + x_offset

            y_offset = game_params["enemy_font_speed"] + enemy_position * ENEMY_HEIGHT
            self.rect.y = group_leader.rect.y + y_offset

        self.draw(game_params["background"])

        if game_params["shooting"] and random.random() < game_params["shooting_chance"]:
            bullet_x = self.rect.centerx - BULLET_WIDTH
            bullet_y = self.rect.y + self.height
            enemy_bullet = pygame.Rect(bullet_x, bullet_y, BULLET_WIDTH, BULLET_HEIGHT)

            game_params["enemy_bullets"].append(enemy_bullet)

    def remove_out_screen_enemy(self, enemy_group):
        enemies_passed = 0
        if self.rect.y > HEIGHT:
            enemy_group.remove(self)
            enemies_passed += 1
        return enemies_passed

def update_display(game_params, ship):
    game_params["background"].fill(COLOR_WHITE)

    game_params["score_text"] = game_params["font"].render("Score: " + str(game_params["score"]), True, SCORE_COLOR)
    game_params["background"].blit(game_params["score_text"], (WIDTH - game_params["score_text"].get_width() - 10, 10))

    level_text = game_params["font"].render("Level: " + str(game_params["level"]), True, LEVEL_COLOR)
    game_params["background"].blit(level_text, (10, 10))

    ship.draw(game_params["background"])

def main():
    pygame.init()
    game_params = initialize_game_parameters()
    enemies_passed = 0

    pygame.display.set_caption("Space invaders")
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    game_params["background"].fill(COLOR_WHITE)
    ship = Ship()
    game_params["last_spawn_time"] = time.time()
    last_shooting_state_change = time.time()

    while True:
        clock.tick(FPS)
        update_level(game_params)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        update_display(game_params, ship)

        process_bullet_creation(game_params, ship.rect)
        update_bullets(game_params)

        keys_pressed = pygame.key.get_pressed()
        ship.update_position(keys_pressed)

        spawn_enemies(game_params)

        for index, enemy_data in enumerate(game_params["enemies"].copy()):
            direction_vector = update_enemy_group(game_params, enemy_data, ship.rect)
            if direction_vector is None:
                continue
            else:
                dx, dy = direction_vector

            enemy_group, segment, segment_bounds = enemy_data
            group_leader = enemy_group[0]
            time_since_spawn = time.time() - group_leader.spawn_time

            if HEIGHT - group_leader.rect.y > 700:
                group_leader.rect.x += ENEMY_SINE_SPEED * dx
                group_leader.rect.y += game_params["enemy_font_speed"] * dy

            for i, enemy in enumerate(enemy_group):
                enemy.update_enemy(group_leader, i, time_since_spawn, enemy_group, game_params)
                enemies_passed = enemy.remove_out_screen_enemy(enemy_group)
                handle_bullet_enemy_collision(game_params, enemy, enemy_group)
        update_enemy_bullets(game_params, ship.rect)

        if time.time() - last_shooting_state_change > game_params["shooting_interval"]:
            game_params["shooting"] = not game_params["shooting"]
            last_shooting_state_change = time.time()

        pygame.display.flip()
        screen.blit(game_params["background"], (0, 0))

if __name__ == '__main__':
    main()