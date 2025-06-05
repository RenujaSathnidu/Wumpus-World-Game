import random
import pygame
from PIL import Image

class WumpusWorld:
    def __init__(self):
        self.grid_size = 4
        self.agent_pos = (0, 0)
        self.agent_dir = "right"
        self.has_gold = False
        self.has_arrow = True
        self.wumpus_alive = True
        self.steps = 0
        self.score = 0
        self.world = self.generate_world()
        self.percepts = {"stench": False, "breeze": False, "glitter": False, "bump": False, "scream": False}
        self.visited_cells = []

    def generate_world(self):
        def is_path_to_gold(world, start, gold_pos):
            visited = set()
            stack = [start]
            while stack:
                x, y = stack.pop()
                if (x, y) == gold_pos:
                    return True
                if (x, y) in visited:
                    continue
                visited.add((x, y))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                        if not world[nx][ny]["pit"] and not (world[nx][ny]["wumpus"] and self.wumpus_alive):
                            stack.append((nx, ny))
            return False

        world = [[{"pit": False, "wumpus": False, "gold": False} for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        while True:
            pit_positions = random.sample([(i, j) for i in range(self.grid_size) for j in range(self.grid_size) if (i, j) != (0, 0)], min(3, self.grid_size * self.grid_size - 1))
            for x, y in pit_positions:
                world[x][y]["pit"] = True
            wumpus_candidates = [(i, j) for i in range(self.grid_size) for j in range(self.grid_size) if (i, j) != (0, 0) and not world[i][j]["pit"]]
            if not wumpus_candidates:
                continue
            wumpus_pos = random.choice(wumpus_candidates)
            world[wumpus_pos[0]][wumpus_pos[1]]["wumpus"] = True
            gold_candidates = [(i, j) for i in range(self.grid_size) for j in range(self.grid_size) if (i, j) != (0, 0) and not world[i][j]["pit"] and (i, j) != wumpus_pos]
            if not gold_candidates:
                continue
            gold_pos = random.choice(gold_candidates)
            world[gold_pos[0]][gold_pos[1]]["gold"] = True
            if is_path_to_gold(world, (0, 0), gold_pos):
                break
        print(f"Gp: {gold_pos}, Wp: {wumpus_pos}, Pt: {pit_positions}")
        return world

    def get_percepts(self):
        x, y = self.agent_pos
        cell = self.world[x][y]
        percepts = {"stench": False, "breeze": False, "glitter": False, "bump": False, "scream": False}
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                if self.world[nx][ny]["wumpus"] and self.wumpus_alive:
                    percepts["stench"] = True
                if self.world[nx][ny]["pit"]:
                    percepts["breeze"] = True
        if cell["gold"]:
            percepts["glitter"] = True
        if self.percepts.get("bump", False):
            percepts["bump"] = True
        if self.percepts.get("scream", False):
            percepts["scream"] = True
        return percepts

    def move_forward(self):
        x, y = self.agent_pos
        new_x, new_y = x, y
        if self.agent_dir == "up":
            new_x -= 1
        elif self.agent_dir == "down":
            new_x += 1
        elif self.agent_dir == "left":
            new_y -= 1
        elif self.agent_dir == "right":
            new_y += 1
        if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
            self.agent_pos = (new_x, new_y)
            self.percepts = self.get_percepts()
            self.steps += 1
            self.score -= 1
            self.visited_cells.append((new_x, new_y))
            return True
        else:
            bump_sound.play()
            self.percepts["bump"] = True
            return False

    def turn_left(self):
        directions = ["up", "left", "down", "right"]
        current_index = directions.index(self.agent_dir)
        self.agent_dir = directions[(current_index + 1) % 4]
        self.percepts = self.get_percepts()

    def turn_right(self):
        directions = ["up", "right", "down", "left"]
        current_index = directions.index(self.agent_dir)
        self.agent_dir = directions[(current_index + 1) % 4]
        self.percepts = self.get_percepts()

    def shoot_arrow(self):
        if not self.has_arrow:
            return False
        self.has_arrow = False
        x, y = self.agent_pos
        wumpus_killed = False
        if self.agent_dir == "up":
            for i in range(x - 1, -1, -1):
                if self.world[i][y]["wumpus"]:
                    wumpus_killed = True
                    break
        elif self.agent_dir == "down":
            for i in range(x + 1, self.grid_size):
                if self.world[i][y]["wumpus"]:
                    wumpus_killed = True
                    break
        elif self.agent_dir == "left":
            for j in range(y - 1, -1, -1):
                if self.world[x][j]["wumpus"]:
                    wumpus_killed = True
                    break
        elif self.agent_dir == "right":
            for j in range(y + 1, self.grid_size):
                if self.world[x][j]["wumpus"]:
                    wumpus_killed = True
                    break
        if wumpus_killed:
            self.wumpus_alive = False
            self.percepts["scream"] = True
            self.score += 100
            scream_sound.play()
            return True
        self.score -= 10
        return False

    def grab_gold(self):
        x, y = self.agent_pos
        if self.world[x][y]["gold"]:
            self.has_gold = True
            self.world[x][y]["gold"] = False
            self.percepts["glitter"] = False
            self.score += 1000
            gold_sound.play()
            return True
        return False

    def climb_out(self):
        if self.agent_pos == (0, 0) and self.has_gold:
            self.score += 1000
            return "win"
        return "continue"

    def is_game_over(self):
        x, y = self.agent_pos
        cell = self.world[x][y]
        if cell["pit"] or (cell["wumpus"] and self.wumpus_alive):
            self.score -= 1000
            die_sound.play()
            return "lose"
        if self.has_gold and self.agent_pos == (0, 0):
            win_sound.play()
            return self.climb_out()
        return "continue"

def load_gif_frames(gif_path, cell_size):
    gif = Image.open(gif_path)
    frames = []
    try:
        while True:
            frame = gif.copy()
            frame = frame.resize((cell_size, cell_size))
            if frame.mode not in ("RGB", "RGBA"):
                frame = frame.convert("RGBA")
            mode = frame.mode if frame.mode in ("RGB", "RGBA") else "RGBA"
            frames.append(pygame.image.fromstring(frame.tobytes(), frame.size, mode))
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

pygame.init()
bump_sound = pygame.mixer.Sound("assets/sounds/bump.wav")
die_sound = pygame.mixer.Sound("assets/sounds/die.wav")
gold_sound = pygame.mixer.Sound("assets/sounds/gold.wav")
scream_sound = pygame.mixer.Sound("assets/sounds/scream.wav")
win_sound = pygame.mixer.Sound("assets/sounds/win.wav")

def visualize_world(env):
    screen = pygame.display.set_mode((600, 500))
    pygame.display.set_caption("Wumpus World")
    clock = pygame.time.Clock()
    cell_size = 75
    colors = {
        "background": (30, 30, 30),
        "grid": (60, 60, 60),
        "text": (200, 200, 200),
        "title": (255, 255, 255),
        "button_bg": (50, 50, 50),
        "button_text": (255, 255, 255),
        "button_hover": (100, 100, 100),
        "popup_bg": (0, 0, 0),
        "popup_text_win": (0, 255, 0),
        "popup_text_lose": (255, 0, 0),
        "popup_border_win": (0, 255, 0),
        "popup_border_lose": (255, 0, 0),
        "gold": (255, 215, 0),
        "agent": (0, 200, 0),
        "pit": (255, 0, 0),
        "wumpus": (128, 0, 128),
        "agent_frame": (245, 245, 245)
    }
    font = pygame.font.Font(None, 18)
    title_font = pygame.font.Font(None, 24)
    button_font = pygame.font.Font(None, 24)
    popup_font = pygame.font.Font(None, 36)
    wumpus_frames = load_gif_frames("assets/images/wumpus.gif", cell_size)
    frame_index = 0
    frame_delay = 10
    frame_timer = 0
    agent_image = pygame.image.load("assets/images/agent.png")
    agent_image = pygame.transform.scale(agent_image, (cell_size, cell_size))
    goldbar_image = pygame.image.load("assets/images/gold.png")
    goldbar_image = pygame.transform.scale(goldbar_image, (cell_size, cell_size))
    running = True
    game_over = False
    win = False
    auto_play = False

    def draw_button(x, y, width, height, text, hover=False):
        base_color = colors["button_bg"]
        hover_color = colors["button_hover"]
        shadow_color = (30, 30, 30)
        button_color = hover_color if hover else base_color
        pygame.draw.rect(screen, shadow_color, (x + 2, y + 2, width, height), border_radius=10)
        pygame.draw.rect(screen, button_color, (x, y, width, height), border_radius=10)
        text_surface = button_font.render(text, True, colors["button_text"])
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        screen.blit(text_surface, text_rect)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if 450 <= mouse_pos[0] <= 550 and 50 <= mouse_pos[1] <= 100:
                    running = False
                elif 450 <= mouse_pos[0] <= 550 and 110 <= mouse_pos[1] <= 160:
                    env = WumpusWorld()
                    game_over = False
                    win = False
                    auto_play = False
                elif 450 <= mouse_pos[0] <= 550 and 170 <= mouse_pos[1] <= 220:
                    auto_play = not auto_play
            if game_over or win:
                continue
            elif event.type == pygame.KEYDOWN and not game_over and not win:
                if event.key == pygame.K_UP:
                    env.agent_dir = "up"
                    env.move_forward()
                elif event.key == pygame.K_DOWN:
                    env.agent_dir = "down"
                    env.move_forward()
                elif event.key == pygame.K_LEFT:
                    env.agent_dir = "left"
                    env.move_forward()
                elif event.key == pygame.K_RIGHT:
                    env.agent_dir = "right"
                    env.move_forward()
                elif event.key == pygame.K_SPACE:
                    env.shoot_arrow()
                elif event.key == pygame.K_g:
                    env.grab_gold()
                elif event.key == pygame.K_LEFT and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    env.turn_left()
                elif event.key == pygame.K_RIGHT and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    env.turn_right()
                game_status = env.is_game_over()
                if game_status == "lose":
                    game_over = True
                elif game_status == "win":
                    win = True
        if auto_play and not game_over and not win:
            valid_moves = []
            for direction in ["up", "down", "left", "right"]:
                x, y = env.agent_pos
                new_x, new_y = x, y
                if direction == "up":
                    new_x -= 1
                elif direction == "down":
                    new_x += 1
                elif direction == "left":
                    new_y -= 1
                elif direction == "right":
                    new_y += 1
                if 0 <= new_x < env.grid_size and 0 <= new_y < env.grid_size:
                    valid_moves.append(direction)
            if valid_moves:
                env.agent_dir = random.choice(valid_moves)
                env.move_forward()
            game_status = env.is_game_over()
            if game_status == "lose":
                game_over = True
            elif game_status == "win":
                win = True
        screen.fill(colors["background"])
        for i in range(env.grid_size):
            for j in range(env.grid_size):
                cell = env.world[i][j]
                pygame.draw.rect(screen, colors["grid"], (j * cell_size, i * cell_size, cell_size, cell_size))
                pygame.draw.rect(screen, (0, 0, 0), (j * cell_size, i * cell_size, cell_size, cell_size), 1)
                if (i, j) in env.visited_cells or (i, j) == (0, 0):
                    pygame.draw.rect(screen, (173, 216, 230), (j * cell_size, i * cell_size, cell_size, cell_size))
                    pygame.draw.rect(screen, (0, 0, 0), (j * cell_size, i * cell_size, cell_size, cell_size), 2)
                if game_over or win:
                    if cell["pit"]:
                        pygame.draw.line(screen, colors["pit"], (j * cell_size, i * cell_size), ((j + 1) * cell_size, (i + 1) * cell_size), 3)
                        pygame.draw.line(screen, colors["pit"], ((j + 1) * cell_size, i * cell_size), (j * cell_size, (i + 1) * cell_size), 3)
                    elif cell["wumpus"] and env.wumpus_alive:
                        frame_timer += 1
                        if frame_timer >= frame_delay:
                            frame_timer = 0
                            frame_index = (frame_index + 1) % len(wumpus_frames)
                        screen.blit(wumpus_frames[frame_index], (j * cell_size, i * cell_size))
                    elif cell["gold"]:
                        screen.blit(goldbar_image, (j * cell_size, i * cell_size))
        agent_x, agent_y = env.agent_pos
        pygame.draw.rect(screen, colors["agent_frame"], (agent_y * cell_size, agent_x * cell_size, cell_size, cell_size), 3)
        screen.blit(agent_image, (agent_y * cell_size, agent_x * cell_size))
        pygame.draw.rect(screen, (50, 50, 50), (0, 300, 600, 200))
        status_title = title_font.render("Status", True, colors["title"])
        screen.blit(status_title, (10, 310))
        status_lines = [
            f"Score: {env.score}",
            f"Steps: {env.steps}",
            f"Gold: {'Yes' if env.has_gold else 'No'}",
            f"Arrow: {'Yes' if env.has_arrow else 'No'}",
            f"Wumpus: {'Alive' if env.wumpus_alive else 'Dead'}",
            f"Direction: {env.agent_dir.capitalize()}"
        ]
        for idx, line in enumerate(status_lines):
            text_surface = font.render(line, True, colors["text"])
            screen.blit(text_surface, (10, 340 + idx * 20))
        percepts_title = title_font.render("Percepts", True, colors["title"])
        screen.blit(percepts_title, (200, 310))
        percept_lines = [
            f"- Stench: {'Yes' if env.percepts['stench'] else 'No'}",
            f"- Breeze: {'Yes' if env.percepts['breeze'] else 'No'}",
            f"- Glitter: {'Yes' if env.percepts['glitter'] else 'No'}"
        ]
        for idx, line in enumerate(percept_lines):
            text_surface = font.render(line, True, colors["text"])
            screen.blit(text_surface, (200, 340 + idx * 20))
        controls_title = title_font.render("Controls", True, colors["title"])
        screen.blit(controls_title, (400, 310))
        controls_lines = ["Space Bar - Shoot arrow", "G - Grab the gold"]
        for idx, line in enumerate(controls_lines):
            text_surface = font.render(line, True, colors["text"])
            screen.blit(text_surface, (400, 340 + idx * 20))
        reasoning_title = title_font.render("Agent Reasoning", True, colors["title"])
        screen.blit(reasoning_title, (200, 400))
        if env.percepts.get("bump", False):
            reasoning_message = "Bump!!!"
        elif env.percepts.get("scream", False):
            reasoning_message = "Wumpus Killed"
        elif env.percepts.get("glitter", False) and env.has_gold:
            reasoning_message = "Gold Grabbed"
        elif game_over and env.world[env.agent_pos[0]][env.agent_pos[1]]["pit"]:
            reasoning_message = "Killed by a Pit"
        else:
            reasoning_message = "Moving"
        reasoning_surface = font.render(reasoning_message, True, colors["text"])
        screen.blit(reasoning_surface, (200, 430))
        draw_button(400, 50, 100, 50, "Stop", 450 <= mouse_pos[0] <= 550 and 50 <= mouse_pos[1] <= 100)
        draw_button(400, 110, 100, 50, "Restart", 450 <= mouse_pos[0] <= 550 and 110 <= mouse_pos[1] <= 160)
        draw_button(400, 170, 100, 50, f"Auto: {'On' if auto_play else 'Off'}", 450 <= mouse_pos[0] <= 550 and 170 <= mouse_pos[1] <= 220)
        if game_over or win:
            popup_color = colors["popup_bg"]
            border_color = colors["popup_border_lose"] if game_over else colors["popup_border_win"]
            text_color = colors["popup_text_lose"] if game_over else colors["popup_text_win"]
            play_again_hover = 150 <= mouse_pos[0] <= 250 and 250 <= mouse_pos[1] <= 290
            exit_hover = 350 <= mouse_pos[0] <= 450 and 250 <= mouse_pos[1] <= 290
            pygame.draw.rect(screen, border_color, (95, 145, 410, 210))
            pygame.draw.rect(screen, popup_color, (100, 150, 400, 200))
            popup_text = "GAME OVER" if game_over else "YOU WIN!"
            popup_surface = popup_font.render(popup_text, True, text_color)
            popup_rect = popup_surface.get_rect(center=(300, 180))
            screen.blit(popup_surface, popup_rect)
            score_text = f"Final Score: {env.score}"
            score_surface = font.render(score_text, True, text_color)
            score_rect = score_surface.get_rect(center=(300, 220))
            screen.blit(score_surface, score_rect)
            play_again_color = (0, 200, 0) if play_again_hover else (50, 150, 50)
            pygame.draw.rect(screen, play_again_color, (150, 250, 100, 40))
            play_again_text = button_font.render("Play Again", True, (255, 255, 255))
            play_again_text_rect = play_again_text.get_rect(center=(200, 270))
            screen.blit(play_again_text, play_again_text_rect)
            exit_color = (200, 0, 0) if exit_hover else (150, 50, 50)
            pygame.draw.rect(screen, exit_color, (350, 250, 100, 40))
            exit_text = button_font.render("Exit", True, (255, 255, 255))
            exit_text_rect = exit_text.get_rect(center=(400, 270))
            screen.blit(exit_text, exit_text_rect)
            if mouse_click[0]:
                if play_again_hover:
                    env = WumpusWorld()
                    game_over = False
                    win = False
                    auto_play = False
                    env.score = 0
                elif exit_hover:
                    running = False
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()

if __name__ == "__main__":
    env = WumpusWorld()
    visualize_world(env)
