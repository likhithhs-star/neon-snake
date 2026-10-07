import pygame
import random
import math
import struct
import os
import sys

# ============================================================
# NEON SNAKE — ARCADE EDITION
# ============================================================

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

WIDTH = 900
HEIGHT = 800

HUD_HEIGHT = 86
FOOTER_HEIGHT = 42
CELL = 30

PLAY_HEIGHT = HEIGHT - HUD_HEIGHT - FOOTER_HEIGHT
COLS = WIDTH // CELL
ROWS = PLAY_HEIGHT // CELL

FPS = 120

START_SPEED = 4.5
SPEED_INCREASE = 0.55
FOOD_PER_SPEEDUP = 3
MAX_SPEED = 12

HIGH_SCORE_FILE = "highscore.txt"

# ============================================================
# COLORS
# ============================================================

BG = (5, 8, 15)
BG_2 = (8, 13, 23)
HUD = (14, 20, 34)
CARD = (20, 29, 48)

GRID = (14, 22, 36)
BORDER = (38, 54, 78)

WHITE = (242, 247, 255)
MUTED = (137, 151, 177)

GREEN = (42, 218, 119)
HEAD_GREEN = (112, 255, 174)
HEAD_DARK = (20, 110, 63)

RED = (255, 76, 101)
RED_LIGHT = (255, 145, 160)

YELLOW = (255, 211, 80)
BLUE = (90, 175, 255)

# ============================================================
# DISPLAY
# ============================================================

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON SNAKE")

clock = pygame.time.Clock()

# ============================================================
# FONTS
# ============================================================

title_font = pygame.font.Font(None, 42)
menu_title_font = pygame.font.Font(None, 92)
menu_subtitle_font = pygame.font.Font(None, 28)

hud_label_font = pygame.font.Font(None, 18)
hud_value_font = pygame.font.Font(None, 31)

small_font = pygame.font.Font(None, 22)
normal_font = pygame.font.Font(None, 30)
big_font = pygame.font.Font(None, 76)

button_font = pygame.font.Font(None, 34)

# ============================================================
# HIGH SCORE
# ============================================================

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as file:
            return int(file.read().strip())
    except:
        return 0


def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as file:
            file.write(str(score))
    except:
        pass


high_score = load_high_score()

# ============================================================
# SOUND
# ============================================================

def create_food_sound():
    sample_rate = 44100
    duration = 0.075
    samples = int(sample_rate * duration)

    data = bytearray()
    phase = 0.0

    for i in range(samples):
        progress = i / samples

        frequency = 880 if progress < 0.48 else 1175

        phase += 2 * math.pi * frequency / sample_rate

        wave = (
            math.sin(phase)
            + 0.30 * math.sin(phase * 2)
        )

        if progress < 0.08:
            envelope = progress / 0.08
        else:
            envelope = (1.0 - progress) / 0.92

        value = int(wave * envelope * 2600)

        data.extend(struct.pack("<h", value))

    return pygame.mixer.Sound(buffer=bytes(data))


def create_game_over_sound():
    sample_rate = 44100
    duration = 0.30
    samples = int(sample_rate * duration)

    data = bytearray()
    phase = 0.0

    for i in range(samples):
        progress = i / samples

        frequency = 620 - 360 * progress

        phase += 2 * math.pi * frequency / sample_rate

        envelope = max(0, 1 - progress)

        value = int(
            math.sin(phase)
            * envelope
            * 2200
        )

        data.extend(struct.pack("<h", value))

    return pygame.mixer.Sound(buffer=bytes(data))


food_sound = create_food_sound()
game_over_sound = create_game_over_sound()

# ============================================================
# PARTICLES
# ============================================================

particles = []


def spawn_particles(grid_position, color, amount=14):
    x, y = grid_position

    center_x = x * CELL + CELL // 2
    center_y = HUD_HEIGHT + y * CELL + CELL // 2

    for _ in range(amount):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(40, 130)

        particles.append({
            "x": center_x,
            "y": center_y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.uniform(0.35, 0.65),
            "max_life": 0.65,
            "size": random.randint(2, 5),
            "color": color,
        })


def update_particles(dt):
    seconds = dt / 1000

    for particle in particles[:]:

        particle["x"] += particle["vx"] * seconds
        particle["y"] += particle["vy"] * seconds

        particle["vy"] += 120 * seconds

        particle["life"] -= seconds

        if particle["life"] <= 0:
            particles.remove(particle)


def draw_particles():
    for particle in particles:

        life_ratio = max(
            0,
            particle["life"] / particle["max_life"]
        )

        size = max(
            1,
            int(particle["size"] * life_ratio)
        )

        pygame.draw.circle(
            screen,
            particle["color"],
            (
                int(particle["x"]),
                int(particle["y"])
            ),
            size
        )

# ============================================================
# FOOD
# ============================================================

def random_food(snake):
    while True:
        position = (
            random.randrange(COLS),
            random.randrange(ROWS)
        )

        if position not in snake:
            return position

# ============================================================
# GAME RESET
# ============================================================

def reset_game():
    particles.clear()
    score_popups.clear()

    center_x = COLS // 2
    center_y = ROWS // 2

    snake = [
        (center_x, center_y),
        (center_x - 1, center_y),
        (center_x - 2, center_y)
    ]

    direction = (1, 0)
    next_direction = (1, 0)

    food = random_food(snake)

    score = 0
    speed = START_SPEED

    game_over = False
    paused = False

    move_timer = 0

    return (
        snake,
        direction,
        next_direction,
        food,
        score,
        speed,
        game_over,
        paused,
        move_timer
    )

# ============================================================
# TEXT
# ============================================================

def draw_text(
    text,
    font,
    color,
    position,
    center=False
):

    surface = font.render(
        text,
        True,
        color
    )

    rect = surface.get_rect()

    if center:
        rect.center = position
    else:
        rect.topleft = position

    screen.blit(surface, rect)

# ============================================================
# BACKGROUND
# ============================================================

def draw_background(time):

    screen.fill(BG)

    # Subtle animated glow
    glow_x = int(
        WIDTH / 2
        + math.sin(time * 0.00035) * 180
    )

    glow_y = int(
        HEIGHT / 2
        + math.cos(time * 0.00028) * 130
    )

    glow = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    for radius in range(220, 30, -25):

        alpha = int(
            18 * (1 - radius / 220)
        )

        pygame.draw.circle(
            glow,
            (40, 110, 75, alpha),
            (glow_x, glow_y),
            radius
        )

    screen.blit(glow, (0, 0))

# ============================================================
# GRID
# ============================================================

def draw_grid():

    pygame.draw.rect(
        screen,
        BG_2,
        (
            0,
            HUD_HEIGHT,
            WIDTH,
            PLAY_HEIGHT
        )
    )

    for x in range(
        0,
        WIDTH + 1,
        CELL
    ):

        pygame.draw.line(
            screen,
            GRID,
            (
                x,
                HUD_HEIGHT
            ),
            (
                x,
                HUD_HEIGHT + PLAY_HEIGHT
            )
        )

    for y in range(
        HUD_HEIGHT,
        HUD_HEIGHT + PLAY_HEIGHT + 1,
        CELL
    ):

        pygame.draw.line(
            screen,
            GRID,
            (
                0,
                y
            ),
            (
                WIDTH,
                y
            )
        )

    pygame.draw.rect(
        screen,
        BORDER,
        (
            0,
            HUD_HEIGHT,
            WIDTH - 1,
            PLAY_HEIGHT
        ),
        2
    )

# ============================================================
# HUD
# ============================================================

def draw_hud(score, best, level, speed):

    pygame.draw.rect(
        screen,
        HUD,
        (0, 0, WIDTH, HUD_HEIGHT)
    )

    draw_text(
        "NEON SNAKE",
        title_font,
        WHITE,
        (22, 15)
    )

    draw_text(
        "ARCADE EDITION",
        hud_label_font,
        MUTED,
        (24, 49)
    )

    cards = [
        ("SCORE", score, WHITE),
        ("BEST", best, YELLOW),
        ("LEVEL", level, BLUE),
    ]

    x_positions = [265, 390, 515]

    for (label, value, color), x in zip(
        cards,
        x_positions
    ):

        pygame.draw.rect(
            screen,
            CARD,
            (
                x,
                13,
                112,
                59
            ),
            border_radius=10
        )

        draw_text(
            label,
            hud_label_font,
            MUTED,
            (
                x + 12,
                20
            )
        )

        draw_text(
            str(value),
            hud_value_font,
            color,
            (
                x + 12,
                39
            )
        )

    draw_text(
        f"{speed:.1f}x",
        hud_value_font,
        GREEN,
        (640, 29)
    )

# ============================================================
# FOOTER
# ============================================================

def draw_footer():

    pygame.draw.rect(
        screen,
        HUD,
        (
            0,
            HEIGHT - FOOTER_HEIGHT,
            WIDTH,
            FOOTER_HEIGHT
        )
    )

    draw_text(
        "WASD / ARROWS",
        small_font,
        MUTED,
        (18, HEIGHT - 31)
    )

    draw_text(
        "SPACE PAUSE",
        small_font,
        MUTED,
        (190, HEIGHT - 31)
    )

    draw_text(
        "R RESTART",
        small_font,
        MUTED,
        (370, HEIGHT - 31)
    )

    draw_text(
        "ESC QUIT",
        small_font,
        MUTED,
        (525, HEIGHT - 31)
    )

# ============================================================
# FOOD DRAW
# ============================================================

def draw_food(food, time):

    x, y = food

    center_x = x * CELL + CELL // 2
    center_y = (
        HUD_HEIGHT
        + y * CELL
        + CELL // 2
    )

    pulse = (
        math.sin(time * 0.006) + 1
    ) / 2

    bob = math.sin(time * 0.004) * 2

    center_y += bob

    glow_radius = int(
        15 + pulse * 9
    )

    glow = pygame.Surface(
        (50, 50),
        pygame.SRCALPHA
    )

    pygame.draw.circle(
        glow,
        (255, 60, 90, 35),
        (25, 25),
        glow_radius
    )

    screen.blit(
        glow,
        (
            center_x - 25,
            center_y - 25
        )
    )

    pygame.draw.circle(
        screen,
        (90, 25, 40),
        (center_x, center_y),
        14
    )

    pygame.draw.circle(
        screen,
        RED,
        (center_x, center_y),
        9
    )

    pygame.draw.circle(
        screen,
        RED_LIGHT,
        (
            center_x - 3,
            center_y - 3
        ),
        3
    )

    # animated shine
    shine_x = int(
        center_x - 7 + pulse * 14
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            shine_x,
            int(center_y - 7)
        ),
        2
    )

# ============================================================
# SNAKE
# ============================================================

def draw_snake(
    snake,
    direction,
    previous_snake,
    progress
):

    progress = max(
        0.0,
        min(1.0, progress)
    )

    rendered = []

    # ========================================================
    # SMOOTH POSITIONS
    # ========================================================

    for index, (x, y) in enumerate(snake):

        if index < len(previous_snake):
            old_x, old_y = previous_snake[index]
        else:
            old_x, old_y = x, y

        dx_wrap = x - old_x
        dy_wrap = y - old_y

        if abs(dx_wrap) > COLS / 2:
            if dx_wrap > 0:
                old_x += COLS
            else:
                old_x -= COLS

        if abs(dy_wrap) > ROWS / 2:
            if dy_wrap > 0:
                old_y += ROWS
            else:
                old_y -= ROWS

        render_x = old_x + (x - old_x) * progress
        render_y = old_y + (y - old_y) * progress

        render_x %= COLS
        render_y %= ROWS

        px = render_x * CELL + CELL / 2
        py = HUD_HEIGHT + render_y * CELL + CELL / 2

        rendered.append((px, py))

    # ========================================================
    # BODY CONNECTIONS
    #
    # IMPORTANT:
    # Never draw a connection across the entire screen.
    # For a wrap, only draw the small edge-to-edge portion.
    # ========================================================

    body_radius = CELL // 2 - 5
    connection_width = body_radius * 2

    board_top = HUD_HEIGHT
    board_bottom = HUD_HEIGHT + PLAY_HEIGHT

    for index in range(len(rendered) - 1):

        x1, y1 = rendered[index]
        x2, y2 = rendered[index + 1]

        factor = max(
            0.48,
            1 - index / max(len(snake), 1) * 0.42
        )

        body_color = (
            int(GREEN[0] * factor),
            int(GREEN[1] * factor),
            int(GREEN[2] * factor)
        )

        # ----------------------------------------------------
        # NORMAL ADJACENT SEGMENTS
        # ----------------------------------------------------

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        if dx <= CELL * 1.5 and dy <= CELL * 1.5:

            pygame.draw.line(
                screen,
                body_color,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                connection_width
            )

        # ----------------------------------------------------
        # HORIZONTAL WRAP
        # ----------------------------------------------------

        elif dx > WIDTH / 2:

            if x1 < WIDTH / 2:

                # Segment at LEFT edge.
                # Continue a tiny piece from the RIGHT edge.
                pygame.draw.line(
                    screen,
                    body_color,
                    (int(x1), int(y1)),
                    (0, int(y1)),
                    connection_width
                )

                pygame.draw.line(
                    screen,
                    body_color,
                    (WIDTH, int(y2)),
                    (int(x2), int(y2)),
                    connection_width
                )

            else:

                # Segment at RIGHT edge.
                # Continue a tiny piece from the LEFT edge.
                pygame.draw.line(
                    screen,
                    body_color,
                    (int(x1), int(y1)),
                    (WIDTH, int(y1)),
                    connection_width
                )

                pygame.draw.line(
                    screen,
                    body_color,
                    (0, int(y2)),
                    (int(x2), int(y2)),
                    connection_width
                )

        # ----------------------------------------------------
        # VERTICAL WRAP
        # ----------------------------------------------------

        elif dy > PLAY_HEIGHT / 2:

            if y1 < board_top + PLAY_HEIGHT / 2:

                pygame.draw.line(
                    screen,
                    body_color,
                    (int(x1), int(y1)),
                    (int(x1), int(board_top)),
                    connection_width
                )

                pygame.draw.line(
                    screen,
                    body_color,
                    (int(x2), int(board_bottom)),
                    (int(x2), int(y2)),
                    connection_width
                )

            else:

                pygame.draw.line(
                    screen,
                    body_color,
                    (int(x1), int(y1)),
                    (int(x1), int(board_bottom)),
                    connection_width
                )

                pygame.draw.line(
                    screen,
                    body_color,
                    (int(x2), int(board_top)),
                    (int(x2), int(y2)),
                    connection_width
                )

    # ========================================================
    # BODY SEGMENTS
    # ========================================================

    for index in range(len(rendered) - 1, 0, -1):

        px, py = rendered[index]

        factor = max(
            0.48,
            1 - index / max(len(snake), 1) * 0.42
        )

        body_color = (
            int(GREEN[0] * factor),
            int(GREEN[1] * factor),
            int(GREEN[2] * factor)
        )

        radius = body_radius

        # Soft glow.
        glow = pygame.Surface(
            (CELL * 2, CELL * 2),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow,
            (
                body_color[0],
                body_color[1],
                body_color[2],
                22
            ),
            (CELL, CELL),
            radius + 7
        )

        screen.blit(
            glow,
            (
                int(px - CELL),
                int(py - CELL)
            )
        )

        # Main body.
        pygame.draw.circle(
            screen,
            body_color,
            (int(px), int(py)),
            radius
        )

        # Small highlight.
        pygame.draw.circle(
            screen,
            (
                min(255, body_color[0] + 24),
                min(255, body_color[1] + 24),
                min(255, body_color[2] + 24)
            ),
            (
                int(px - 4),
                int(py - 4)
            ),
            2
        )

    # ========================================================
    # HEAD
    # ========================================================

    if rendered:

        head_x, head_y = rendered[0]

        head_radius = CELL // 2 - 2

        # Head glow.
        glow = pygame.Surface(
            (CELL * 2, CELL * 2),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow,
            (90, 255, 160, 38),
            (CELL, CELL),
            head_radius + 9
        )

        screen.blit(
            glow,
            (
                int(head_x - CELL),
                int(head_y - CELL)
            )
        )

        # Shadow.
        pygame.draw.circle(
            screen,
            HEAD_DARK,
            (
                int(head_x),
                int(head_y + 2)
            ),
            head_radius + 2
        )

        # Main head.
        pygame.draw.circle(
            screen,
            HEAD_GREEN,
            (
                int(head_x),
                int(head_y)
            ),
            head_radius
        )

        dx, dy = direction

        # ====================================================
        # EYES
        # ====================================================

        if dx == 1:

            eye_positions = [
                (head_x + 7, head_y - 6),
                (head_x + 7, head_y + 6)
            ]

        elif dx == -1:

            eye_positions = [
                (head_x - 7, head_y - 6),
                (head_x - 7, head_y + 6)
            ]

        elif dy == -1:

            eye_positions = [
                (head_x - 6, head_y - 7),
                (head_x + 6, head_y - 7)
            ]

        else:

            eye_positions = [
                (head_x - 6, head_y + 7),
                (head_x + 6, head_y + 7)
            ]

        for ex, ey in eye_positions:

            pygame.draw.circle(
                screen,
                (4, 12, 10),
                (
                    int(ex),
                    int(ey)
                ),
                4
            )

            pygame.draw.circle(
                screen,
                WHITE,
                (
                    int(ex - 1),
                    int(ey - 1)
                ),
                1
            )

        # ====================================================
        # TONGUE
        # ====================================================

        tongue_start = (
            head_x + dx * 10,
            head_y + dy * 10
        )

        tongue_end = (
            head_x + dx * 17,
            head_y + dy * 17
        )

        pygame.draw.line(
            screen,
            RED,
            (
                int(tongue_start[0]),
                int(tongue_start[1])
            ),
            (
                int(tongue_end[0]),
                int(tongue_end[1])
            ),
            2
        )

# ============================================================
# BUTTON
# ============================================================

def draw_button(
    rect,
    text,
    hovered=False
):

    if hovered:

        color = (
            40,
            185,
            105
        )

        border = HEAD_GREEN

    else:

        color = (
            27,
            42,
            60
        )

        border = BORDER

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        border,
        rect,
        2,
        border_radius=14
    )

    draw_text(
        text,
        button_font,
        WHITE,
        rect.center,
        True
    )

# ============================================================
# MAIN MENU
# ============================================================

def draw_menu(time, best):

    draw_background(time)

    # Dark overlay
    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (3, 6, 12, 80)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    draw_text(
        "NEON",
        menu_title_font,
        HEAD_GREEN,
        (WIDTH // 2, 180),
        True
    )

    draw_text(
        "SNAKE",
        menu_title_font,
        WHITE,
        (WIDTH // 2, 250),
        True
    )

    draw_text(
        "CLASSIC ARCADE  •  MODERN MOTION",
        menu_subtitle_font,
        MUTED,
        (WIDTH // 2, 305),
        True
    )

    mouse = pygame.mouse.get_pos()

    pulse = (
        math.sin(time * 0.005) + 1
    ) / 2

    button = pygame.Rect(
        WIDTH // 2 - 145,
        370,
        290,
        76
    )

    hovered = button.collidepoint(mouse)

    draw_button(
        button,
        "PLAY",
        hovered
    )

    draw_text(
        f"BEST SCORE  {best}",
        normal_font,
        YELLOW,
        (WIDTH // 2, 485),
        True
    )

    draw_text(
        "WASD / ARROWS TO MOVE",
        small_font,
        MUTED,
        (WIDTH // 2, 550),
        True
    )

    draw_text(
        "SPACE  PAUSE        ESC  QUIT",
        small_font,
        MUTED,
        (WIDTH // 2, 580),
        True
    )

    # Small animated indicator
    radius = int(
        4 + pulse * 3
    )

    pygame.draw.circle(
        screen,
        GREEN,
        (
            WIDTH // 2,
            625
        ),
        radius
    )

    draw_text(
        "ARCADE READY",
        hud_label_font,
        MUTED,
        (
            WIDTH // 2,
            650
        ),
        True
    )

    return button

# ============================================================
# GAME OVER OVERLAY
# ============================================================

def draw_game_over(
    score,
    best,
    time
):

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (3, 6, 12, 220)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    pulse = (
        math.sin(time * 0.006) + 1
    ) / 2

    draw_text(
        "GAME OVER",
        big_font,
        RED,
        (
            WIDTH // 2,
            HEIGHT // 2 - 90
        ),
        True
    )

    draw_text(
        f"SCORE  {score}",
        normal_font,
        WHITE,
        (
            WIDTH // 2,
            HEIGHT // 2 - 20
        ),
        True
    )

    draw_text(
        f"BEST  {best}",
        normal_font,
        YELLOW,
        (
            WIDTH // 2,
            HEIGHT // 2 + 20
        ),
        True
    )

    restart_rect = pygame.Rect(
        WIDTH // 2 - 145,
        HEIGHT // 2 + 65,
        290,
        68
    )

    mouse = pygame.mouse.get_pos()

    draw_button(
        restart_rect,
        "PLAY AGAIN",
        restart_rect.collidepoint(mouse)
    )

    draw_text(
        "Press R or click PLAY AGAIN",
        small_font,
        MUTED,
        (
            WIDTH // 2,
            HEIGHT // 2 + 150
        ),
        True
    )

    return restart_rect

# ============================================================
# PAUSE OVERLAY
# ============================================================

def draw_pause():

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (3, 6, 12, 190)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    draw_text(
        "PAUSED",
        big_font,
        WHITE,
        (
            WIDTH // 2,
            HEIGHT // 2 - 30
        ),
        True
    )

    draw_text(
        "Press SPACE to continue",
        normal_font,
        MUTED,
        (
            WIDTH // 2,
            HEIGHT // 2 + 45
        ),
        True
    )


# ============================================================
# FOOD PARTICLE EFFECTS
# ============================================================

particles = []
score_popups = []


def spawn_food_effect(food):
    """Create a small burst when food is collected."""

    x, y = food

    center_x = x * CELL + CELL // 2
    center_y = HUD_HEIGHT + y * CELL + CELL // 2

    # Particle burst
    for i in range(12):

        angle = (
            math.pi * 2 * i / 12
            + random.uniform(-0.18, 0.18)
        )

        speed_particle = random.uniform(45, 105)

        particles.append({
            "x": float(center_x),
            "y": float(center_y),
            "vx": math.cos(angle) * speed_particle,
            "vy": math.sin(angle) * speed_particle,
            "life": random.uniform(0.25, 0.45),
            "max_life": 0.45,
            "size": random.randint(2, 4),
        })

    # Floating score text
    score_popups.append({
        "x": float(center_x),
        "y": float(center_y),
        "life": 0.65,
        "max_life": 0.65,
    })


def update_effects(dt):
    """Update particles and floating score text."""

    seconds = dt / 1000.0

    # -------------------------
    # Particles
    # -------------------------

    for particle in particles[:]:

        particle["x"] += particle["vx"] * seconds
        particle["y"] += particle["vy"] * seconds

        particle["vx"] *= 0.94
        particle["vy"] *= 0.94

        particle["life"] -= seconds

        if particle["life"] <= 0:
            particles.remove(particle)

    # -------------------------
    # Score popups
    # -------------------------

    for popup in score_popups[:]:

        popup["y"] -= 42 * seconds
        popup["life"] -= seconds

        if popup["life"] <= 0:
            score_popups.remove(popup)


def draw_effects():
    """Render particles and score popups."""

    # -------------------------
    # Particles
    # -------------------------

    for particle in particles:

        alpha = int(
            255 *
            max(
                0.0,
                particle["life"] /
                particle["max_life"]
            )
        )

        size = max(
            1,
            int(
                particle["size"] *
                (
                    0.65 +
                    particle["life"] /
                    particle["max_life"] *
                    0.35
                )
            )
        )

        particle_surface = pygame.Surface(
            (size * 4, size * 4),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            particle_surface,
            (255, 95, 115, alpha),
            (size * 2, size * 2),
            size
        )

        screen.blit(
            particle_surface,
            (
                int(particle["x"] - size * 2),
                int(particle["y"] - size * 2)
            )
        )

    # -------------------------
    # +1 popup
    # -------------------------

    for popup in score_popups:

        alpha = int(
            255 *
            max(
                0.0,
                popup["life"] /
                popup["max_life"]
            )
        )

        popup_surface = small_font.render(
            "+1",
            True,
            YELLOW
        )

        popup_surface.set_alpha(alpha)

        rect = popup_surface.get_rect(
            center=(
                int(popup["x"]),
                int(popup["y"])
            )
        )

        screen.blit(
            popup_surface,
            rect
        )


# ============================================================
# GAME STATE
# ============================================================

(
    snake,
    direction,
    next_direction,
    food,
    score,
    speed,
    game_over,
    paused,
    move_timer
) = reset_game()

previous_snake = snake[:]

state = "MENU"

running = True

# ============================================================
# MAIN LOOP
# ============================================================

while running:

    dt = clock.tick(FPS)

    time_now = pygame.time.get_ticks()

    # ----------------------------------------
    # EVENTS
    # ----------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # Quit
            if event.key == pygame.K_ESCAPE:

                if state == "MENU":
                    running = False
                else:
                    state = "MENU"
                    paused = False

            # Start game
            elif (
                state == "MENU"
                and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                )
            ):

                (
                    snake,
                    direction,
                    next_direction,
                    food,
                    score,
                    speed,
                    game_over,
                    paused,
                    move_timer
                ) = reset_game()

                previous_snake = snake[:]

                state = "PLAYING"

            # Movement
            elif state == "PLAYING":

                if event.key in (
                    pygame.K_UP,
                    pygame.K_w
                ):

                    if direction != (0, 1):
                        next_direction = (0, -1)

                elif event.key in (
                    pygame.K_DOWN,
                    pygame.K_s
                ):

                    if direction != (0, -1):
                        next_direction = (0, 1)

                elif event.key in (
                    pygame.K_LEFT,
                    pygame.K_a
                ):

                    if direction != (1, 0):
                        next_direction = (-1, 0)

                elif event.key in (
                    pygame.K_RIGHT,
                    pygame.K_d
                ):

                    if direction != (-1, 0):
                        next_direction = (1, 0)

                elif event.key == pygame.K_SPACE:

                    if not game_over:
                        paused = not paused

                elif event.key == pygame.K_r:

                    (
                        snake,
                        direction,
                        next_direction,
                        food,
                        score,
                        speed,
                        game_over,
                        paused,
                        move_timer
                    ) = reset_game()

                    previous_snake = snake[:]

            # Restart after death
            elif state == "GAME_OVER":

                if event.key == pygame.K_r:

                    (
                        snake,
                        direction,
                        next_direction,
                        food,
                        score,
                        speed,
                        game_over,
                        paused,
                        move_timer
                    ) = reset_game()

                    previous_snake = snake[:]

                    state = "PLAYING"

    # ----------------------------------------
    # MOUSE
    # ----------------------------------------

    mouse_pressed = pygame.mouse.get_pressed()[0]

    if state == "MENU":

        mouse = pygame.mouse.get_pos()

        play_button = pygame.Rect(
            WIDTH // 2 - 145,
            370,
            290,
            76
        )

        if mouse_pressed and play_button.collidepoint(mouse):

            (
                snake,
                direction,
                next_direction,
                food,
                score,
                speed,
                game_over,
                paused,
                move_timer
            ) = reset_game()

            previous_snake = snake[:]

            state = "PLAYING"

    # ----------------------------------------
    # GAME LOGIC
    # ----------------------------------------

    if state == "PLAYING" and not paused:

        move_interval = (
            1000 / speed
        )

        move_timer += dt

        while move_timer >= move_interval:

            move_timer -= move_interval

            previous_snake = snake[:]

            direction = next_direction

            head_x, head_y = snake[0]

            new_head = (
                head_x + direction[0],
                head_y + direction[1]
            )

            # Edge wrapping
            new_head = (
                new_head[0] % COLS,
                new_head[1] % ROWS
            )

            # Self collision
            if new_head in snake:

                game_over = True
                state = "GAME_OVER"

                game_over_sound.play()

                spawn_particles(
                    snake[0],
                    RED,
                    28
                )

                break

            snake.insert(
                0,
                new_head
            )

            # Food
            if new_head == food:

                score += 1

                if score > high_score:

                    high_score = score
                    save_high_score(
                        high_score
                    )

                if (
                    score % FOOD_PER_SPEEDUP
                    == 0
                ):

                    speed = min(
                        MAX_SPEED,
                        speed + SPEED_INCREASE
                    )

                food_sound.play()

                spawn_particles(
                    food,
                    RED_LIGHT,
                    18
                )

                food = random_food(
                    snake
                )

            else:

                snake.pop()

    # ----------------------------------------
    # PARTICLES
    # ----------------------------------------

    update_particles(dt)

    # ----------------------------------------
    # DRAW
    # ----------------------------------------

    draw_background(
        time_now
    )

    if state == "MENU":

        draw_menu(
            time_now,
            high_score
        )

    else:

        draw_grid()

        level = (
            int(
                (speed - START_SPEED)
                / SPEED_INCREASE
            ) + 1
        )

        draw_hud(
            score,
            high_score,
            level,
            speed
        )

        draw_food(
            food,
            time_now
        )

        progress = (
            move_timer
            / (1000 / speed)
        )

        draw_snake(
            snake,
            direction,
            previous_snake,
            progress
        )

        draw_particles()

        draw_effects()

    draw_footer()

    if paused:

        draw_pause()

    if state == "GAME_OVER":

        restart_button = draw_game_over(
            score,
            high_score,
            time_now
        )

        mouse = pygame.mouse.get_pos()

        if (
            mouse_pressed
            and restart_button.collidepoint(
                mouse
            )
        ):

            (
                snake,
                direction,
                next_direction,
                food,
                score,
                speed,
                game_over,
                paused,
                move_timer
            ) = reset_game()

            previous_snake = snake[:]

            state = "PLAYING"

    pygame.display.flip()

pygame.quit()
sys.exit()
