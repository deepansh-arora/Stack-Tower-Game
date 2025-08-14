import pygame
import sys
import os

pygame.init()
WIDTH, HEIGHT = 500, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stack Tower Game")
clock = pygame.time.Clock()

ODD_COLOR = (255, 100, 100)
EVEN_COLOR = (100, 100, 255)
TRIM_COLOR = (150, 150, 150)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)

try:
    BACKGROUND = pygame.image.load("city_blur.jpg").convert()
    BACKGROUND = pygame.transform.scale(BACKGROUND, (WIDTH, HEIGHT))
except:
    BACKGROUND = None

BLOCK_HEIGHT = 30
START_BLOCK_WIDTH = 200
INIT_SPEED = 3
SPEED_INCREMENT = 0.15
DROP_SPEED = 10
SCROLL_MARGIN = 0.4
HIGH_SCORE_FILE = "highscore.txt"
SMOOTH_SCROLL_FACTOR = 0.1
DIFFICULTY_STEP = 5
DIFFICULTY_INCREMENT = 0.5

def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_high_score(val):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(val))
    except:
        pass

high_score = load_high_score()

class Block:
    def __init__(self, x, y, width, direction, number):
        self.x = x
        self.y = y
        self.width = width
        self.height = BLOCK_HEIGHT
        self.direction = direction
        self.number = number
        self.falling_trim = None

    def move(self, speed):
        self.x += speed * self.direction
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x + self.width >= WIDTH:
            self.x = WIDTH - self.width
            self.direction = -1

    def draw(self, camera_y):
        color = ODD_COLOR if self.number % 2 == 1 else EVEN_COLOR
        pygame.draw.rect(screen, color, (self.x, self.y - camera_y, self.width, self.height))
        if self.falling_trim:
            pygame.draw.rect(screen, TRIM_COLOR,
                             (self.falling_trim.x, self.falling_trim.y - camera_y,
                              self.falling_trim.width, self.falling_trim.height))

    def drop_trim_piece(self, trim_x, trim_width):
        if trim_width > 0:
            self.falling_trim = pygame.Rect(trim_x, self.y, trim_width, self.height)

    def update_falling(self):
        if self.falling_trim:
            self.falling_trim.y += DROP_SPEED
            if self.falling_trim.y > HEIGHT + 50:
                self.falling_trim = None

def spawn_new_block(prev_block, block_number):
    direction = 1 if block_number % 2 == 1 else -1
    x = 0 if direction == 1 else WIDTH - prev_block.width
    y = prev_block.y - BLOCK_HEIGHT
    return Block(x, y, prev_block.width, direction, block_number)

def overlap_blocks(curr, last):
    left_overlap = max(curr.x, last.x)
    right_overlap = min(curr.x + curr.width, last.x + last.width)
    overlap_width = right_overlap - left_overlap
    if overlap_width <= 0:
        return None, None, None
    trim = None
    if curr.x < last.x:
        trim = (curr.x, last.x - curr.x)
    elif curr.x + curr.width > last.x + last.width:
        trim = (last.x + last.width, curr.x + curr.width - (last.x + last.width))
    return overlap_width, trim, left_overlap

def reset_game():
    global blocks, current_block, game_over, score, camera_y, speed
    base_block = Block(WIDTH//2 - START_BLOCK_WIDTH//2, HEIGHT - BLOCK_HEIGHT, START_BLOCK_WIDTH, 1, 0)
    blocks = [base_block]
    current_block = spawn_new_block(base_block, 1)
    game_over = False
    score = 0
    camera_y = 0
    speed = INIT_SPEED

def update_camera():
    global camera_y
    top_block_y = min(b.y for b in blocks)
    margin = HEIGHT * SCROLL_MARGIN
    free_space = top_block_y - camera_y
    if free_space < margin:
        camera_y -= (margin - free_space) * SMOOTH_SCROLL_FACTOR

def draw_hud():
    score_surf = font.render(f"Score: {score}", True, WHITE)
    high_surf = font.render(f"High: {high_score}", True, WHITE)
    screen.blit(score_surf, (10,10))
    screen.blit(high_surf, (WIDTH - high_surf.get_width() - 10,10))

def draw_game_over():
    over_surf = big_font.render("GAME OVER", True, WHITE)
    score_surf = font.render(f"Score: {score}", True, WHITE)
    high_surf = font.render(f"High Score: {high_score}", True, WHITE)
    restart_surf = font.render("Press R to Restart", True, WHITE)
    screen.blit(over_surf, (WIDTH//2 - over_surf.get_width()//2, HEIGHT//2 - 100))
    screen.blit(score_surf, (WIDTH//2 - score_surf.get_width()//2, HEIGHT//2 - 30))
    screen.blit(high_surf, (WIDTH//2 - high_surf.get_width()//2, HEIGHT//2 + 20))
    screen.blit(restart_surf, (WIDTH//2 - restart_surf.get_width()//2, HEIGHT//2 + 80))

reset_game()

while True:
    screen.fill(BLACK)
    if BACKGROUND:
        screen.blit(BACKGROUND, (0,0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_high_score(high_score)
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if not game_over and event.key == pygame.K_SPACE:
                last = blocks[-1]
                overlap_width, trim_piece, new_x = overlap_blocks(current_block, last)
                if overlap_width is None:
                    game_over = True
                    if score > high_score:
                        high_score = score
                        save_high_score(high_score)
                else:
                    if trim_piece:
                        current_block.drop_trim_piece(trim_piece[0], trim_piece[1])
                    current_block.width = overlap_width
                    current_block.x = new_x
                    blocks.append(current_block)
                    score += 1
                    speed += SPEED_INCREMENT
                    if score % DIFFICULTY_STEP == 0:
                        speed += DIFFICULTY_INCREMENT
                    current_block = spawn_new_block(current_block, score + 1)
            if game_over and event.key == pygame.K_r:
                reset_game()

    if not game_over:
        current_block.move(speed)
        update_camera()
        for b in blocks:
            b.update_falling()

    for b in blocks:
        b.draw(camera_y)
    if not game_over:
        current_block.draw(camera_y)

    draw_hud()
    if game_over:
        draw_game_over()

    pygame.display.flip()
    clock.tick(60)
