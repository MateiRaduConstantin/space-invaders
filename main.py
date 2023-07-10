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

BULLET_WIDTH, BULLET_HEIGHT = 10, 20

SEGMENT_COUNT = 5
MAX_ENEMIES = 12

ENEMY_SPAWN_INTERVAL = 5
ENEMY_SPEED = 1
ENEMY_SINE_SPEED = 1
BULLET_DELAY = 150
SCORE_COLOR = (0, 0, 0)
LEVEL_COLOR = (0, 0, 0)

def initialize_game_parameters():
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
        "enemies": [],
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
        bullet = pygame.Rect(ship_img_rect.centerx - BULLET_WIDTH // 2, ship_img_rect.y - BULLET_HEIGHT, BULLET_WIDTH // 2, BULLET_HEIGHT // 2)
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

def spawn_enemies(game_params, enemy_img):
    if time.time() - game_params["last_spawn_time"] > ENEMY_SPAWN_INTERVAL:
        available_segments = [i for i, occupied in enumerate(game_params["occupied_segments"]) if not occupied]
        if available_segments:
            total_enemies = sum(len(enemy_group) for enemy_group in game_params["enemies"])
            if total_enemies < MAX_ENEMIES:
                segment = random.choice(available_segments)  # Choose a random available segment
                game_params["occupied_segments"][segment] = True  # Mark the segment as occupied
                segment_bounds = (segment * (WIDTH / SEGMENT_COUNT), (segment + 1) * (WIDTH / SEGMENT_COUNT) - ENEMY_WIDTH)

                # Calculate the x-coordinate for the chosen segment
                spawn_x = int(segment * (WIDTH / SEGMENT_COUNT) + (WIDTH / SEGMENT_COUNT) / 2 - ENEMY_WIDTH / 2)

                if game_params["level"] > 1:
                    game_params["enemies"].append(([(pygame.Rect(spawn_x, -(ENEMY_DELAY_HEIGHT * 2) - i * (ENEMY_DELAY_HEIGHT * 2), ENEMY_WIDTH, ENEMY_HEIGHT), enemy_img, time.time()) for i in range(4)], segment, segment_bounds))

                else:
                    game_params["enemies"].append(([(pygame.Rect(spawn_x, 0, ENEMY_WIDTH, ENEMY_HEIGHT), enemy_img, time.time())], segment, segment_bounds))
                game_params["last_spawn_time"] = time.time()

def handle_bullet_enemy_collision(game_params, enemy, enemy_group, enemy_rect):
    for bullet in game_params["bullets"].copy():
        if enemy_rect.colliderect(bullet):
            enemy_group.remove(enemy)
            game_params["bullets"].remove(bullet)
            game_params["enemies_killed"] += 1
            game_params["score"] += 100  # Increment score
            break

def update_enemy_position(enemy, group_leader, i, time_since_spawn, enemy_group, game_params, enemy_img):
    if i != 0:
        # Update the enemy's x position to create a snake-like movement pattern
        enemy[0].x = group_leader[0].x + i * ENEMY_DELAY_HEIGHT * math.sin(ENEMY_SINE_SPEED * (time_since_spawn + i/len(enemy_group)))
        enemy[0].y = group_leader[0].y + game_params["enemy_font_speed"] + i * ENEMY_HEIGHT  # Update the enemy's y position
    enemy_rect = enemy[0]
    game_params["background"].blit(enemy_img, enemy[0])
    return enemy_rect

def remove_out_screen_enemy(enemy, enemy_group, enemy_rect):
    # Remove enemy if it's out of screen
    enemies_passed = 0
    if enemy_rect.y > HEIGHT:
        enemy_group.remove(enemy)
        enemies_passed += 1  # Increment enemies passed counter
    return enemies_passed

def update_enemy_bullets(game_params, ship_hitbox):
    for bullet in game_params["enemy_bullets"].copy():
        bullet.y += 5
        if bullet.y > HEIGHT:
            game_params["enemy_bullets"].remove(bullet)
        else:
            pygame.draw.rect(game_params["background"], COLOR_RED, bullet)

            # Check collision with ship
            if bullet.colliderect(ship_hitbox):
                pygame.event.post(pygame.event.Event(pygame.QUIT))

def update_enemy_group(game_params, enemy_data, ship_img_rect):
    enemy_group, segment, segment_bounds = enemy_data
    if len(enemy_group) == 0:
        game_params["enemies"].remove(enemy_data)
        # Check if the enemy group had a segment
        if segment is not None:
            # Mark the segment as available
            game_params["occupied_segments"][segment] = False
        return None

    # The first enemy in the group is the leader
    group_leader = enemy_group[0]
    time_since_spawn = time.time() - group_leader[2]
    group_leader[0].x += ENEMY_SINE_SPEED * math.sin(time_since_spawn)
    group_leader[0].x = max(segment_bounds[0], min(group_leader[0].x, segment_bounds[1] - group_leader[0].width))  # Restrict within screen

    dx = ship_img_rect.x - group_leader[0].x
    dy = ship_img_rect.y - group_leader[0].y
    dist = math.sqrt(dx**2 + dy**2)

    # Normalize the direction vector
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

def main():
    pygame.init()
    game_params = initialize_game_parameters()
    enemies_passed = 0

    pygame.display.set_caption("Space invaders")

    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    game_params["background"].fill(COLOR_WHITE)

    ship = Ship()

    enemy_img = pygame.image.load("enemy.png")
    enemy_img = pygame.transform.scale(enemy_img, (ENEMY_WIDTH, ENEMY_HEIGHT))

    enemy_img_rect = enemy_img.get_rect()

    game_params["enemies"] = [([(pygame.Rect(random.randint(0, WIDTH - ENEMY_WIDTH), -i * ENEMY_HEIGHT, ENEMY_WIDTH, ENEMY_HEIGHT), enemy_img, 0) for i in range(1)], None, [0, WIDTH])]

    game_params["last_spawn_time"] = time.time()

    last_shooting_state_change = time.time()

    while True:
        clock.tick(FPS)
        game_params["background"].fill(COLOR_WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        process_bullet_creation(game_params, ship.rect)

        game_params["score_text"] = game_params["font"].render("Score: " + str(game_params["score"]), True, SCORE_COLOR)
        game_params["background"].blit(game_params["score_text"], (WIDTH - game_params["score_text"].get_width() - 10, 10))

        game_params = update_level(game_params)

        level_text = game_params["font"].render("Level: " + str(game_params["level"]), True, LEVEL_COLOR)
        game_params["background"].blit(level_text, (10, 10))

        update_bullets(game_params)

        keys_pressed = pygame.key.get_pressed()
        ship.update_position(keys_pressed)

        ship.draw(game_params["background"])
        spawn_enemies(game_params, enemy_img)

        for index, enemy_data in enumerate(game_params["enemies"].copy()):
            direction_vector = update_enemy_group(game_params, enemy_data, ship.rect)
            if direction_vector is None:
                continue
            else:
                dx, dy = direction_vector

            enemy_group, segment, segment_bounds = enemy_data
            group_leader = enemy_group[0]
            time_since_spawn = time.time() - group_leader[2]

            if HEIGHT - group_leader[0].y > 700:
                group_leader[0].x += ENEMY_SINE_SPEED * dx
                group_leader[0].y += game_params["enemy_font_speed"] * dy

            for i, enemy in enumerate(enemy_group):
                enemy_rect = update_enemy_position(enemy, group_leader, i, time_since_spawn, enemy_group, game_params, enemy_img)
                enemies_passed = remove_out_screen_enemy(enemy, enemy_group, enemy_rect)
                handle_bullet_enemy_collision(game_params, enemy, enemy_group, enemy_rect)

                if game_params["shooting"] and random.random() < game_params["shooting_chance"]:
                    enemy_bullet = pygame.Rect(enemy[0].centerx - BULLET_WIDTH // 2, enemy[0].y + enemy[0].height, BULLET_WIDTH // 2, BULLET_HEIGHT // 2)
                    game_params["enemy_bullets"].append(enemy_bullet)

        update_enemy_bullets(game_params, ship.rect)

        if time.time() - last_shooting_state_change > game_params["shooting_interval"]:
            game_params["shooting"] = not game_params["shooting"]
            last_shooting_state_change = time.time()

        game_params["score_text"] = game_params["font"].render("Score: " + str(game_params["score"]), True, SCORE_COLOR)
        game_params["background"].blit(game_params["score_text"], (WIDTH - game_params["score_text"].get_width() - 10, 10))

        pygame.display.flip()
        screen.blit(game_params["background"], (0, 0))

if __name__ == '__main__':
    main()