import pygame
import sys
import math
import random
import asyncio

# Constants for screen dimensions and frame rate
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Constants for tile properties
TILE_SIZE = 80
TILE_SPACING = 20
TILE_Y_CENTER = SCREEN_HEIGHT // 2

# Constants for EEG wave display
EEG_WAVE_Y = 100
EEG_WAVE_HEIGHT = 100
EEG_WAVE_CENTER_Y = EEG_WAVE_Y + EEG_WAVE_HEIGHT // 2

# Constants for title display
TITLE_Y = 50

# Color definitions
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)

# Tile class to represent each flashing tile
class Tile:
    def __init__(self, x, y, frequency):
        # Initialize tile position and size using a Pygame Rect
        self.rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        self.rect.center = (x, y)
        self.frequency = frequency  # Flashing frequency in Hz
        self.state = 0  # 0 for black, 1 for white
        # Font for frequency label (simulated, as Pyodide doesn't load files)
        self.font = pygame.font.SysFont(None, 24)  # Fallback font
        self.label = self.font.render(f"{frequency} Hz", True, WHITE)

    def update(self, current_time):
        # Update flashing state based on current time
        # Phase oscillates between 0 and 1 per cycle; < 0.5 is state 0, >= 0.5 is state 1
        phase = (current_time * self.frequency) % 1
        self.state = 0 if phase < 0.5 else 1

    def draw(self, screen):
        # Draw the tile with color based on state
        color = BLACK if self.state == 0 else WHITE
        pygame.draw.rect(screen, color, self.rect)
        # Draw frequency label (inverted color for visibility)
        label_color = WHITE if self.state == 0 else BLACK
        self.label = self.font.render(f"{self.frequency} Hz", True, label_color)
        label_pos = (self.rect.centerx - self.label.get_width() // 2,
                     self.rect.centery - self.label.get_height() // 2)
        screen.blit(self.label, label_pos)

    def is_mouse_over(self, pos):
        # Check if the mouse position is over the tile
        return self.rect.collidepoint(pos)

    def set_position(self, x, y):
        # Set the tile's center position (for dragging)
        self.rect.center = (x, y)

# EEGWave class to simulate a moving EEG wave
class EEGWave:
    def __init__(self):
        # Initialize wave points across screen width
        self.wave_points = [0] * SCREEN_WIDTH
        # Parameters for a complex wave: multiple sine components
        self.amplitudes = [20, 10, 5]  # Amplitudes of sine waves
        self.frequencies = [0.5, 1.0, 2.0]  # Frequencies of sine waves in Hz
        self.noise_level = 5  # Noise amplitude

    def update(self, current_time):
        # Calculate new y-value using multiple sine waves plus noise
        new_y = sum([a * math.sin(2 * math.pi * f * current_time)
                    for a, f in zip(self.amplitudes, self.frequencies)]) + \
                random.gauss(0, self.noise_level)
        # Shift wave left and add new point
        self.wave_points.pop(0)
        self.wave_points.append(new_y)

    def draw(self, screen):
        # Generate points for drawing the wave, centered vertically
        points = [(x, EEG_WAVE_CENTER_Y + int(self.wave_points[x]))
                  for x in range(SCREEN_WIDTH)]
        # Draw the wave as a continuous line
        pygame.draw.lines(screen, GREEN, False, points, 2)

# Main application class
class MainApp:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mind Controller")
        self.clock = pygame.time.Clock()

        # Load font and render title (simulated font loading for Pyodide)
        self.font = pygame.font.SysFont(None, 36)  # Fallback font
        self.title = self.font.render("Mind Controller - By winterath", True, WHITE)
        self.title_pos = (SCREEN_WIDTH // 2 - self.title.get_width() // 2, TITLE_Y)

        # Initialize EEG wave
        self.eeg_wave = EEGWave()

        # Initialize tiles with frequencies 3, 6, 9, 12, 15 Hz
        self.tiles = []
        frequencies = [3, 6, 9, 12, 15]
        total_tiles_width = len(frequencies) * TILE_SIZE + (len(frequencies) - 1) * TILE_SPACING
        start_x = (SCREEN_WIDTH - total_tiles_width) // 2 + TILE_SIZE // 2
        for i, freq in enumerate(frequencies):
            x = start_x + i * (TILE_SIZE + TILE_SPACING)
            y = TILE_Y_CENTER
            tile = Tile(x, y, freq)
            self.tiles.append(tile)

        # Dragging state
        self.dragging_tile = None
        self.drag_offset = (0, 0)

    def handle_events(self):
        # Process all Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if platform.system() != "Emscripten":
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if a tile is clicked to start dragging
                for tile in self.tiles:
                    if tile.is_mouse_over(event.pos):
                        self.dragging_tile = tile
                        self.drag_offset = (event.pos[0] - tile.rect.centerx,
                                          event.pos[1] - tile.rect.centery)
                        break
            elif event.type == pygame.MOUSEMOTION:
                # Update tile position if dragging
                if self.dragging_tile:
                    self.dragging_tile.set_position(event.pos[0] - self.drag_offset[0],
                                                 event.pos[1] - self.drag_offset[1])
            elif event.type == pygame.MOUSEBUTTONUP:
                # Stop dragging
                self.dragging_tile = None

    def update(self, current_time):
        # Update all tiles and EEG wave
        for tile in self.tiles:
            tile.update(current_time)
        self.eeg_wave.update(current_time)

    def draw(self):
        # Draw all elements to the screen
        self.screen.fill(BLACK)  # Clear screen with black background
        self.eeg_wave.draw(self.screen)  # Draw EEG wave
        for tile in self.tiles:  # Draw all tiles
            tile.draw(self.screen)
        self.screen.blit(self.title, self.title_pos)  # Draw title
        pygame.display.flip()  # Update display

    async def run(self):
        # Main game loop using asyncio for Pyodide compatibility
        while True:
            current_time = pygame.time.get_ticks() / 1000.0  # Time in seconds
            self.handle_events()
            self.update(current_time)
            self.draw()
            await asyncio.sleep(1.0 / FPS)  # Control frame rate

# Setup function to initialize the game
def setup():
    global app
    app = MainApp()

# Update loop function (placeholder for clarity)
def update_loop():
    pass  # All updates handled in MainApp.run()

# Main entry point compatible with Pyodide
async def main():
    setup()
    await app.run()

# Platform-specific execution
import platform
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
