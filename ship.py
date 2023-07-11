import config
import pygame

class Ship:
    def __init__(self):
        self.img = pygame.image.load("ship.png")
        self.width = self.img.get_width() // 2
        self.height = self.img.get_height() // 2
        self.img = pygame.transform.scale(self.img, (self.width, self.height))
        self.rect = self.img.get_rect()
        self.rect.topleft = (config.WIDTH // 2, config.HEIGHT - self.rect.height)
        self.speed = 5

    def update_position(self, keys_pressed):
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            self.rect.x = max(0, self.rect.x - self.speed)
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            self.rect.x = min(config.WIDTH - self.rect.width, self.rect.x + self.speed)
        return self.rect

    def draw(self, background):
        background.blit(self.img, self.rect)
