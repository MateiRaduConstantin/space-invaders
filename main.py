import sys
import random
import time
import math
import copy
import pygame
import config
from enemy import Enemy
from ship import Ship

def initialize_game_parameters():
    enemy_img = pygame.image.load("enemy.png")
    enemy_img = pygame.transform.scale(enemy_img, (config.ENEMY_WIDTH, config.ENEMY_HEIGHT))
    width = config.WIDTH
    height = config.HEIGHT
    enemy_width = config.ENEMY_WIDTH
    enemy_height = config.ENEMY_HEIGHT
    enemy_spawn = [Enemy(enemy_img, random.randint(0, width - enemy_width), 0, enemy_width, enemy_height, 0)]
    boundaries = [0, width]
    game_params = {
        "background": pygame.Surface((config.WIDTH, config.HEIGHT)),
        "font": pygame.font.Font(None, 36),
        "score": 0,
        "score_text": None,
        "level": 1,
        "last_spawn_time": 0,
        "shooting": False,
        "shooting_interval": 1,
        "shooting_chance": 0.01,
        "enemy_font_speed": 0.53,
        "occupied_segments": [False] * config.SEGMENT_COUNT,
        "last_bullet_time": 0,
        "bullets": [],
        "enemy_bullets": [],
        "enemies": [(enemy_spawn, None, boundaries)],
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
            pygame.draw.rect(game_params["background"], config.COLOR_GREEN, bullet)

def process_bullet_creation(game_params, ship_img_rect):
    keys_pressed = pygame.key.get_pressed()
    if keys_pressed[pygame.K_SPACE] and pygame.time.get_ticks() - game_params["last_bullet_time"] >= config.BULLET_DELAY:
        bullet = pygame.Rect(ship_img_rect.centerx - config.BULLET_WIDTH, ship_img_rect.y - config.BULLET_HEIGHT, config.BULLET_WIDTH, config.BULLET_HEIGHT)
        game_params["bullets"].append(bullet)
        game_params["last_bullet_time"] = pygame.time.get_ticks()

def spawn_enemies(game_params):
    if time.time() - game_params["last_spawn_time"] > config.ENEMY_SPAWN_INTERVAL:
        available_segments = [i for i, occupied in enumerate(game_params["occupied_segments"]) if not occupied]
        if available_segments:
            total_enemies = sum(len(enemy_group) for enemy_group in game_params["enemies"])
            if total_enemies < config.MAX_ENEMIES:
                segment = random.choice(available_segments)
                game_params["occupied_segments"][segment] = True
                segment_width = config.WIDTH / config.SEGMENT_COUNT
                segment_start = segment * segment_width
                segment_end = (segment + 1) * segment_width - config.ENEMY_WIDTH

                segment_bounds = (segment_start, segment_end)
                spawn_x = int(segment_start + segment_width / 2 - config.ENEMY_WIDTH / 2)

                image = game_params["enemy_img"]
                width, height = config.ENEMY_WIDTH, config.ENEMY_HEIGHT
                spawn_time = time.time()

                if game_params["level"] > 1:
                    enemies = []
                    for i in range(4):
                        y_position = -(config.ENEMY_DELAY_HEIGHT * 2) - i * (config.ENEMY_DELAY_HEIGHT * 2)
                        enemies.append(Enemy(image, spawn_x, y_position, width, height, spawn_time))
                else:
                    enemies = [Enemy(image, spawn_x, 0, width, height, spawn_time)]

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
        if bullet.y > config.HEIGHT:
            game_params["enemy_bullets"].remove(bullet)
        else:
            pygame.draw.rect(game_params["background"], config.COLOR_RED, bullet)

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
    group_leader.rect.x += config.ENEMY_SINE_SPEED * math.sin(time_since_spawn)
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

    def remove_out_screen_enemy(self, enemy_group):
        enemies_passed = 0
        if self.rect.y > config.HEIGHT:
            enemy_group.remove(self)
            enemies_passed += 1
        return enemies_passed

def update_display(game_params, ship):
    game_params["background"].fill(config.COLOR_WHITE)

    game_params["score_text"] = game_params["font"].render("Score: " + str(game_params["score"]), True, config.SCORE_COLOR)
    game_params["background"].blit(game_params["score_text"], (config.WIDTH - game_params["score_text"].get_width() - 10, 10))

    level_text = game_params["font"].render("Level: " + str(game_params["level"]), True, config.LEVEL_COLOR)
    game_params["background"].blit(level_text, (10, 10))

    ship.draw(game_params["background"])

def main():
    pygame.init()
    game_params = initialize_game_parameters()
    enemies_passed = 0

    pygame.display.set_caption("Space invaders")
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))

    game_params["background"].fill(config.COLOR_WHITE)
    ship = Ship()
    game_params["last_spawn_time"] = time.time()
    last_shooting_state_change = time.time()

    while True:
        clock.tick(config.FPS)
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

            if config.HEIGHT - group_leader.rect.y > 700:
                group_leader.rect.x += config.ENEMY_SINE_SPEED * dx
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