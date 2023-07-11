import pygame
import math
import random
import config

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
            sine_factor = config.ENEMY_SINE_SPEED * (time_since_spawn + enemy_position/len(enemy_group))
            x_offset = enemy_position * config.ENEMY_DELAY_HEIGHT * math.sin(sine_factor)
            self.rect.x = group_leader.rect.x + x_offset

            y_offset = game_params["enemy_font_speed"] + enemy_position * config.ENEMY_HEIGHT
            self.rect.y = group_leader.rect.y + y_offset

        self.draw(game_params["background"])

        if game_params["shooting"] and random.random() < game_params["shooting_chance"]:
            bullet_x = self.rect.centerx - config.BULLET_WIDTH
            bullet_y = self.rect.y + self.height
            enemy_bullet = pygame.Rect(bullet_x, bullet_y, config.BULLET_WIDTH, config.BULLET_HEIGHT)

            game_params["enemy_bullets"].append(enemy_bullet)

    def remove_out_screen_enemy(self, enemy_group):
        enemies_passed = 0
        if self.rect.y > config.HEIGHT:
            enemy_group.remove(self)
            enemies_passed += 1
        return enemies_passed