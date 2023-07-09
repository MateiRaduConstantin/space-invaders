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

def main():
    # Initialize imported pygame modules
    pygame.init()

    score = 0
    enemies_passed = 0

    font = pygame.font.Font(None, 36)

    pygame.display.set_caption("Space invaders")

    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    background = pygame.Surface((WIDTH, HEIGHT))
    background = background.convert()
    background.fill(COLOR_WHITE)

    # Load ship
    ship_img = pygame.image.load("ship.png")
    ship_width = ship_img.get_width() // 2
    ship_height = ship_img.get_height() // 2
    ship_img = pygame.transform.scale(ship_img, (ship_width, ship_height))
    ship_img_rect = ship_img.get_rect()
    ship_img_rect.topleft = (WIDTH // 2, HEIGHT - ship_img_rect.height)

    # Load enemy
    enemy_img = pygame.image.load("enemy.png")
    enemy_img = pygame.transform.scale(enemy_img, (ENEMY_WIDTH, ENEMY_HEIGHT))

    enemy_img_rect = enemy_img.get_rect()

    # Bullets
    bullets = []

    # Enemies
    enemies = [([(pygame.Rect(random.randint(0, WIDTH - ENEMY_WIDTH), -i * ENEMY_HEIGHT, ENEMY_WIDTH, ENEMY_HEIGHT), enemy_img, 0) for i in range(1)], None, [0, WIDTH])]

    # Enemy bullets
    enemy_bullets = []

    # Enemies killed
    enemies_killed = 0

    # Last spawn time
    last_spawn_time = time.time()

    # Update hitbox
    ship_hitbox = ship_img_rect.copy()


    # Initialize shooting state and last shooting state change time
    shooting = True
    last_shooting_state_change = time.time()


    # Store the current occupied segments
    occupied_segments = [False] * SEGMENT_COUNT

    # Initial game parameters
    level = 1
    shooting_interval = 1
    shooting_chance = 0.01
    enemy_font_speed = 0.53

    # Shooting delay
    last_bullet_time = 0

    # Main loop
    while True:
        clock.tick(FPS)

        # Erase everything drawn at last step by filling the background
        # with color white
        background.fill(COLOR_WHITE)

        # Check for Quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Shooting bullets
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_SPACE] and pygame.time.get_ticks() - last_bullet_time >= BULLET_DELAY:
            bullet = pygame.Rect(ship_img_rect.centerx - BULLET_WIDTH // 2, ship_img_rect.y - BULLET_HEIGHT, BULLET_WIDTH // 2, BULLET_HEIGHT // 2)
            bullets.append(bullet)
            last_bullet_time = pygame.time.get_ticks()

        # Draw score
        score_text = font.render("Score: " + str(score), True, SCORE_COLOR)
        # Draw score in the top right corner
        background.blit(score_text, (WIDTH - score_text.get_width() - 10, 10))


        if level < 2 and enemies_killed >= 3:
            level = 2
            shooting_interval = 1.5
        if  level < 3 and enemies_killed >= 10:
            level = 3
            shooting_interval = 1
            shooting_chance = 0.04
            enemy_font_speed = 1

        # Draw level
        level_text = font.render("Level: " + str(level), True, LEVEL_COLOR)
        # Draw score in the top right corner
        background.blit(level_text, (10, 10))

        # Update bullets
        for bullet in bullets.copy():
            bullet.y -= 5
            if bullet.y < 0:
                bullets.remove(bullet)
            else:
                pygame.draw.rect(background, COLOR_GREEN, bullet)

        # Update ship
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            ship_img_rect.x = max(0, ship_img_rect.x - 5)
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            ship_img_rect.x = min(WIDTH - ship_img_rect.width, ship_img_rect.x + 5)
        ship_hitbox.x = ship_img_rect.x
        ship_hitbox.y = ship_img_rect.y

        # Restrict within screen
        ship_img_rect.x = max(0, min(ship_img_rect.x, WIDTH - ship_img_rect.width))

        # Draw ship
        background.blit(ship_img, ship_img_rect)

        # Spawn enemies
        if time.time() - last_spawn_time > ENEMY_SPAWN_INTERVAL:
            # Find an unoccupied segment
            available_segments = [i for i, occupied in enumerate(occupied_segments) if not occupied]
            if available_segments:
                total_enemies = sum(len(enemy_group) for enemy_group in enemies)
                if total_enemies < MAX_ENEMIES:
                      # If there are too many enemies, do not spawn more this frame

                    segment = random.choice(available_segments)  # Choose a random available segment
                    occupied_segments[segment] = True  # Mark the segment as occupied
                    segment_bounds = (segment * (WIDTH / SEGMENT_COUNT), (segment + 1) * (WIDTH / SEGMENT_COUNT) - ENEMY_WIDTH)

                    # Calculate the x-coordinate for the chosen segment
                    spawn_x = int(segment * (WIDTH / SEGMENT_COUNT) + (WIDTH / SEGMENT_COUNT) / 2 - ENEMY_WIDTH / 2)

                    if level > 1:
                        enemies.append(([(pygame.Rect(spawn_x, -(ENEMY_DELAY_HEIGHT * 2) - i * (ENEMY_DELAY_HEIGHT * 2), ENEMY_WIDTH, ENEMY_HEIGHT), enemy_img, time.time()) for i in range(4)], segment, segment_bounds))

                    else:
                        enemies.append(([(pygame.Rect(spawn_x, 0, ENEMY_WIDTH, ENEMY_HEIGHT), enemy_img, time.time())], segment, segment_bounds))

                    last_spawn_time = time.time()

        # Update enemies
        for index, enemy_data in enumerate(enemies.copy()):
            enemy_group, segment, segment_bounds = enemy_data
            if len(enemy_group) == 0:
                enemies.remove(enemy_data)
                # Check if the enemy group had a segment
                if segment is not None:
                    # Mark the segment as available
                    occupied_segments[segment] = False
                continue

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

            # Move the enemy towards the player's ship
            if HEIGHT - group_leader[0].y > 700:  # The distance at which the enemies stop advancing
                group_leader[0].x += ENEMY_SINE_SPEED * dx
                group_leader[0].y += enemy_font_speed * dy

            for i, enemy in enumerate(enemy_group):
                # For all enemies except the leader
                if i != 0:
                    # Update the enemy's x position to create a snake-like movement pattern
                    enemy[0].x = group_leader[0].x + i * ENEMY_DELAY_HEIGHT * math.sin(ENEMY_SINE_SPEED * (time_since_spawn + i/len(enemy_group)))
                    enemy[0].y = group_leader[0].y + enemy_font_speed + i * ENEMY_HEIGHT  # Update the enemy's y position

                enemy_rect = enemy[0]
                background.blit(enemy_img, enemy[0])

                # If the entire group is off the screen, mark its segment as available
                if all(enemy[0].y > HEIGHT for enemy in enemy_group):
                    enemy_group_x = enemy_group[0][0].x  # The x-coordinate of the group's spawn position
                    segment = int(enemy_group_x / segment_width)  # The segment the group was spawned in
                    occupied_segments[segment] = False  # Mark the segment as available


                # Remove enemy if it's out of screen
                if enemy_rect.y > HEIGHT:
                    enemy_group.remove(enemy)
                    enemies_passed += 1  # Increment enemies passed counter
                    continue

                # Check collision with ship's bullets
                for bullet in bullets.copy():
                    if enemy_rect.colliderect(bullet):
                        enemy_group.remove(enemy)
                        bullets.remove(bullet   )
                        enemies_killed += 1
                        score += 100  # Increment score
                        break

                # Enemy shooting
                if shooting and random.random() < shooting_chance:  # chance to shoot every frame
                    enemy_bullet = pygame.Rect(enemy[0].centerx - BULLET_WIDTH // 2, enemy[0].y + enemy[0].height, BULLET_WIDTH // 2, BULLET_HEIGHT // 2)
                    enemy_bullets.append(enemy_bullet)

        # Update enemy bullets
        for bullet in enemy_bullets.copy():
            bullet.y += 5
            if bullet.y > HEIGHT:
                enemy_bullets.remove(bullet)
            else:
                pygame.draw.rect(background, COLOR_RED, bullet)

                # Check collision with ship
                if bullet.colliderect(ship_hitbox):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

        # Check if it's time to change the shooting state
        if time.time() - last_shooting_state_change > shooting_interval:
            shooting = not shooting
            last_shooting_state_change = time.time()

        # Draw score
        score_text = font.render("Score: " + str(score), True, SCORE_COLOR)
        background.blit(score_text, (WIDTH - score_text.get_width() - 10, 10))  # Draw score in the top right corner

        # Render current game state
        pygame.display.flip()
        screen.blit(background, (0, 0))


if __name__ == '__main__':
    main()