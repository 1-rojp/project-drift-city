import pygame
import math
import sys

def show_main_menu(screen, WIDTH, HEIGHT):
    font = pygame.font.SysFont(None, 72)
    small_font = pygame.font.SysFont(None, 36)
    title_surf = font.render("Project Drift City", True, (255, 255, 0))
    prompt_surf = small_font.render("Press any key or click Start Game", True, (255, 255, 255))  # <-- Add this line
    button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 50)
    button_text = small_font.render("Start Game", True, (80, 80, 80))
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                # If mouse click, check if it's on the button
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(event.pos):
                        return  # Start the game
                else:
                    return  # Start the game on any key

        screen.fill((30, 30, 30))
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(prompt_surf, (WIDTH // 2 - prompt_surf.get_width() // 2, HEIGHT // 2 + 20))
        # Draw the Start Game button
        pygame.draw.rect(screen, (255, 220, 100), button_rect, border_radius=12)
        screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2, button_rect.centery - button_text.get_height() // 2))
        pygame.display.flip()
        clock.tick(60)

def tint_surface(surface, tint_color):
    """Return a tinted copy of the surface."""
    tinted = surface.copy()
    tinted.fill(tint_color + (0,), None, pygame.BLEND_RGBA_MULT)
    return tinted

def draw_pause_button(surface, rect, paused):
    color = (200, 200, 200) if not paused else (255, 220, 100)
    pygame.draw.rect(surface, color, rect, border_radius=8)
    if not paused:
        pygame.draw.rect(surface, (80, 80, 80), rect.inflate(-24, -8).move(6, 0))
        pygame.draw.rect(surface, (80, 80, 80), rect.inflate(-24, -8).move(-6, 0))
    else:
        points = [
            (rect.left + 12, rect.top + 8),
            (rect.left + 12, rect.bottom - 8),
            (rect.right - 8, rect.centery)
        ]
        pygame.draw.polygon(surface, (80, 80, 80), points)

def save_highscore(score, filename="highscore.txt"):
    try:
        with open(filename, "w") as f:
            f.write(str(score))
    except Exception as e:
        print("Error saving highscore:", e)

def load_highscore(filename="highscore.txt"):
    try:
        with open(filename, "r") as f:
            return int(f.read())
    except:
        return 0

def main():
    pygame.init()

    # Screen settings
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Project Drift City")

    clock = pygame.time.Clock()
    FPS = 60

    # Load map
    city_map = pygame.image.load("city_map.png")
    city_map = pygame.transform.scale(city_map, (1600, 1200))

    # Load car image
    car_image = pygame.image.load("car_sprite.png").convert_alpha()
    car_image = pygame.transform.scale(car_image, (35, 45))  # Shorter car

    # Car class
    class Car:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.angle = 0
            self.movement_angle = 0  # For drifting
            self.speed = 0
            self.velocity = pygame.math.Vector2(0.0, 0.0)
            self.max_speed = 5
            self.acceleration = 0.2
            self.friction = 0.05
            self.turn_speed = 3
            self.drift_factor = 0.15  # Lower = more drift
            self.score = 0  # Add this line

        def update(self, drive_vector):
            if drive_vector.length() > 0.2:
                self.speed += self.acceleration
                # Set angle to match joycon direction (up is 0 degrees)
                target_angle = -math.degrees(math.atan2(drive_vector.x, -drive_vector.y))
                # Smoothly rotate movement_angle toward target_angle for drift
                angle_diff = (target_angle - self.movement_angle + 180) % 360 - 180
                self.movement_angle += angle_diff * self.drift_factor
                self.angle = target_angle

                # --- Score for drifting ---
                drift_amount = abs((self.angle - self.movement_angle + 180) % 360 - 180)
                if drift_amount > 10 and self.speed > 1:  # Only score if drifting enough and moving
                    self.score += int(drift_amount * 0.1)  # Adjust multiplier as desired
            else:
                if self.speed > 0:
                    self.speed -= self.friction
                if self.speed < 0:
                    self.speed = 0

            self.speed = min(self.speed, self.max_speed)
            # Use movement_angle for velocity (drift effect)
            self.velocity.from_polar((self.speed, -self.movement_angle))
            self.x += self.velocity.x
            self.y += self.velocity.y

        def draw(self, surface, offset_x, offset_y):
            # Use self.angle for drawing (car faces where player steers)
            rotated = pygame.transform.rotate(car_image, self.angle - 90)
            rect = rotated.get_rect(center=(self.x - offset_x, self.y - offset_y))
            surface.blit(rotated, rect.topleft)

    # Joystick class
    class Joycon:
        def __init__(self, center):
            self.center = center
            self.drag_pos = None
            self.active = False
            self.radius = 40
            self.max_offset = 40

        def handle_event(self, event):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Vector2(event.pos).distance_to(self.center) < self.radius * 2:
                    self.active = True
                    self.drag_pos = pygame.Vector2(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.active = False
                self.drag_pos = None
            elif event.type == pygame.MOUSEMOTION and self.active:
                self.drag_pos = pygame.Vector2(event.pos)

        def get_vector(self):
            if not self.active or self.drag_pos is None:
                return pygame.Vector2(0, 0)
            vec = self.drag_pos - self.center
            if vec.length() > self.max_offset:
                vec.scale_to_length(self.max_offset)
            return vec / self.max_offset  # Normalize to -1..1

        def draw(self, surface):
            pygame.draw.circle(surface, (80, 80, 80), self.center, self.radius * 2, 3)
            if self.drag_pos:
                pygame.draw.circle(surface, (150, 150, 150), self.drag_pos, self.radius)

    # Setup
    player_car = Car(800, 600)
    joycon = Joycon(center=pygame.Vector2(WIDTH // 2, HEIGHT - 80))

    # Show main menu
    show_main_menu(screen, WIDTH, HEIGHT)

    # Example: List of house rectangles (x, y, width, height)
    houses = [
        pygame.Rect(300, 400, 80, 80),
        pygame.Rect(600, 700, 100, 60),
        pygame.Rect(1200, 900, 120, 100),
        # Add more as needed, coordinates are in map space
    ]

    pause_button_rect = pygame.Rect(10, 10, 40, 40)
    paused = False
    back_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 50)

    # Draw pause menu overlay if paused
    if paused:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont(None, 72)
        pause_text = font.render("Paused", True, (255, 255, 0))
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 60))
        small_font = pygame.font.SysFont(None, 36)
        info = small_font.render("Click pause button to resume", True, (255, 255, 255))
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 10))

        # Draw "Back to Main Menu" button
        pygame.draw.rect(screen, (255, 220, 100), back_button_rect, border_radius=12)
        btn_text = small_font.render("Back to Main Menu", True, (80, 80, 80))
        screen.blit(btn_text, (back_button_rect.centerx - btn_text.get_width() // 2, back_button_rect.centery - btn_text.get_height() // 2))

    # Load highscore
    highscore = load_highscore()

    # Game loop
    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in [pygame.MOUSEBUTTONDOWN]:
                if pause_button_rect.collidepoint(event.pos):
                    paused = not paused
                elif paused and back_button_rect.collidepoint(event.pos):
                    # Save highscore before returning to menu
                    if player_car.score > highscore:
                        save_highscore(player_car.score)
                        highscore = player_car.score
                    show_main_menu(screen, WIDTH, HEIGHT)
                    paused = False
                else:
                    if not paused:
                        joycon.handle_event(event)
            elif event.type in [pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                if not paused:
                    joycon.handle_event(event)

        if not paused:
            # Update car
            drive_vector = joycon.get_vector()
            player_car.update(drive_vector)

        # Camera offset (no clamping, allows infinite scrolling)
        offset_x = player_car.x - WIDTH // 2
        offset_y = player_car.y - HEIGHT // 2

        # Draw scene
        screen.fill((30, 30, 30))
        map_w, map_h = city_map.get_size()
        start_x = -int(offset_x) % map_w - map_w
        start_y = -int(offset_y) % map_h - map_h
        for x in range(start_x, WIDTH + map_w, map_w):
            for y in range(start_y, HEIGHT + map_h, map_h):
                screen.blit(city_map, (x, y))
        player_car.draw(screen, offset_x, offset_y)
        joycon.draw(screen)

        # --- Draw score and highscore ---
        font = pygame.font.SysFont(None, 36)
        score_surf = font.render(f"Score: {player_car.score}", True, (255, 255, 0))
        screen.blit(score_surf, (pause_button_rect.right + 10, pause_button_rect.top + (pause_button_rect.height - score_surf.get_height()) // 2))
        highscore_surf = font.render(f"High Score: {highscore}", True, (255, 255, 255))
        screen.blit(highscore_surf, (pause_button_rect.right + 10, pause_button_rect.bottom + 10))

        # Draw pause button
        draw_pause_button(screen, pause_button_rect, paused)

        # Draw pause menu overlay if paused
        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            font = pygame.font.SysFont(None, 72)
            pause_text = font.render("Paused", True, (255, 255, 0))
            screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 60))
            small_font = pygame.font.SysFont(None, 36)
            info = small_font.render("Click pause button to resume", True, (255, 255, 255))
            screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 10))

            # Draw "Back to Main Menu" button
            pygame.draw.rect(screen, (255, 220, 100), back_button_rect, border_radius=12)
            btn_text = small_font.render("Back to Main Menu", True, (80, 80, 80))
            screen.blit(btn_text, (back_button_rect.centerx - btn_text.get_width() // 2, back_button_rect.centery - btn_text.get_height() // 2))

        if player_car.score > highscore:
            save_highscore(player_car.score)
            highscore = player_car.score

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
