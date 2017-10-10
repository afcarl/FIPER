import pygame

def convert():    
    pygame.init()
    pygame.display.set_mode()
    image = pygame.image.load("2.jpg").convert_alpha()
    for x in range(image.get_width()):
        for y in range(image.get_height()):
            if image.get_at((x, y)) == (255, 255, 255, 255):
                image.set_at((x, y), (255, 255, 255, 0))
    pygame.image.save(image, "2.png")

if __name__ == "__main__":
    convert()
