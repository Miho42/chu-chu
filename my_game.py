"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""
from enum import Enum
from os import DirEntry
from typing import List, Optional, Union
import arcade

# Print debug information
DEBUG_ON = not True

SPRITE_SCALING = 4
TILE_SCALING = 4
TILE_SIZE = TILE_SCALING * 16

# When Chuchu is closer to destination than this, it has arrived
IS_ON_TILE_DIFF = 1.0

# Set the size of the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Variables controlling the player
PLAYER_LIVES = 3
PLAYER_SPEED_X = 5
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_START_Y = 50
PLAYER_SHOT_SPEED = 4

FIRE_KEY = arcade.key.SPACE

TEXTURES = arcade.load_spritesheet(
    file_name="images/urbanrpg/tilemap.png",
    sprite_width=16,
    sprite_height=16,
    columns=27,
    count=18 * 27,
    margin=1,
)

# Indexes for tiles
T_TILE_TL = 0
T_TILE_T = 1
T_TILE_TR = 2
T_TILE_L = 1 * 27
T_TILE_NONE = 1 * 27 + 1
T_TILE_R = 1 * 27 + 2
T_TILE_BR = 2 * 27 + 2
T_TILE_BL = 2 * 27
T_TILE_B = 2 * 27 + 1

# Indexes for chuchus
C1_UP1 = 25
C1_UP2 = C1_UP1 + 27
C1_UP3 = C1_UP2 + 27

# Emitters
E_E1 = 11 * 27 + 9

# Drains
D_D1 = 11 * 27 + 13

# Annotations
A_UP1 = 7 * 27 + 1

# Players
P_P1 = 9 * 27 + 2


class Direction(Enum):
    """
    Directions in the game matrix.
    """

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

    def __bool__(self) -> bool:
        """
        The None direction is False
        """
        return self.value != (0, 0)

    def __mul__(self, other: Union[float, int]) -> List[Union[float, int]]:
        """
        Multiply all values in Direction
        """
        return [other * v for v in self.value]


class Player(arcade.Sprite):
    """
    The player
    """

    def __init__(self, **kwargs):
        """
        Setup new Player object
        """
        self._tile_pos = (0, 0)

        # How much to scale the graphics
        kwargs["scale"] = SPRITE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.texture = TEXTURES[P_P1]

    @property
    def tile_pos(self):
        return self._tile_pos

    @tile_pos.setter
    def tile_pos(self, new_pos):
        self._tile_pos = new_pos

    def update(self, delta_time):
        """
        Move the sprite
        """
        pass


class TileType(Enum):
    """
    Tiles with wall. Prefix T mean tile. next character is wall on x-axis, last character is wall on y-axis.
    """


class Tile(arcade.Sprite):
    """
    A tile :)
    """

    types = {
        0: {"out_dir": Direction.NONE, "block_dirs": [], "texture_no": T_TILE_NONE},
        1: {
            "out_dir": Direction.RIGHT,
            "block_dirs": [Direction.UP],
            "texture_no": T_TILE_T,
        },
        2: {
            "out_dir": Direction.DOWN,
            "block_dirs": [Direction.RIGHT],
            "texture_no": T_TILE_R,
        },
        3: {
            "out_dir": Direction.LEFT,
            "block_dirs": [Direction.DOWN],
            "texture_no": T_TILE_B,
        },
        4: {
            "out_dir": Direction.UP,
            "block_dirs": [Direction.LEFT],
            "texture_no": T_TILE_L,
        },
        5: {
            "out_dir": Direction.RIGHT,
            "block_dirs": [Direction.UP, Direction.LEFT],
            "texture_no": T_TILE_TL,
        },
        6: {
            "out_dir": Direction.DOWN,
            "block_dirs": [Direction.UP, Direction.RIGHT],
            "texture_no": T_TILE_TR,
        },
        7: {
            "out_dir": Direction.LEFT,
            "block_dirs": [Direction.RIGHT, Direction.DOWN],
            "texture_no": T_TILE_BR,
        },
        8: {
            "out_dir": Direction.UP,
            "block_dirs": [Direction.LEFT, Direction.DOWN],
            "texture_no": T_TILE_BL,
        },
    }

    def __init__(self, type=0, center_x=0, center_y=0, **kwargs):
        """
        Setup new Tile object
        """
        self.my_type = Tile.types[type]

        # How much to scale the graphics
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.texture = TEXTURES[self.my_type["texture_no"]]

        self.position = center_x, center_y


class Chuchu(arcade.Sprite):
    """
    A Chuchu (AKA a mouse)
    """

    def __init__(self, my_emitter, my_speed=2, **kwargs):
        """
        Setup new Chuchu. It always moves towards <my_destination_screen_coordinates>.
        When the destination is reached. I waits for a new dircetion passed to it with
        move().
        """
        # The direction I'm moving in
        self.my_direction = Direction.NONE

        # Steps per tile
        self.my_speed = my_speed

        # Scale the graphics
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        # Graphics
        self.texture = TEXTURES[C1_UP2]

        # The screen coordinates I'm moving towards
        self.my_destination_screen_coordinates = self.center_x, self.center_y

        # All chuchus start at their emitter
        self.position = my_emitter.position

        # My first move is in emit direction
        # This will calculate my destination screen coordinates
        self.move(my_emitter.emit_direction)

        # I have reached my destination, and I'm waiting for a new direction to move in.
        self.waiting_for_orders = False

    def drained(self):
        """
        When a Chuchu reaches a drain and should no longer exist
        """
        if DEBUG_ON:
            print("I was drained. Yes!")
        self.kill()

    def move(self, new_direction: Direction):
        """
        Takes a direction and updates destination screen coordinates.
        """
        assert new_direction != Direction.NONE, "Told to move in direction None"
        # Current direction is updated
        self.my_direction = new_direction

        # Update my screen destination relative to lower left of matrix
        self.my_destination_screen_coordinates = self.my_direction * TILE_SIZE

        # Update my screen destination relative to current position
        self.my_destination_screen_coordinates[0] += self.center_x
        self.my_destination_screen_coordinates[1] += self.center_y

        # Calculating speed by (new destination - current destination) / number of steps
        self.change_x = (
            self.my_destination_screen_coordinates[0] - self.center_x
        ) / self.my_speed
        self.change_y = (
            self.my_destination_screen_coordinates[1] - self.center_y
        ) / self.my_speed

        self.waiting_for_orders = False

    def update(self, delta_time):
        """
        Move chuchu towards destination coordinates if not there yet.
        """
        if (
            arcade.get_distance(
                self.my_destination_screen_coordinates[0],
                self.my_destination_screen_coordinates[1],
                self.position[0],
                self.position[1],
            )
            > IS_ON_TILE_DIFF
        ):
            self.center_x += self.change_x * delta_time
            self.center_y += self.change_y * delta_time
        else:
            # Move to exact destination
            self.position = self.my_destination_screen_coordinates
            self.waiting_for_orders = True


class Emitter(arcade.Sprite):
    """
    An emitter spawning chuchus
    """

    emitter_types = {0: "images/Emitter/Emitter_jar.png"}

    def __init__(
        self,
        on_tile,
        emit_direction: Direction,
        type,
        capacity=5,
        emit_rate=2.0,
        **kwargs,
    ):
        """
        Setup new Emitter
        """

        # How fast will Chuchus spawn
        self.emit_rate = emit_rate

        # Ready to emit a chuchu
        self.emit_timer = 0

        self.capacity = capacity

        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        # kwargs["filename"] = Emitter.emitter_types[type]

        self.texture = TEXTURES[E_E1]

        self.go_to_tile(on_tile)

        # Direction for the outspitted Chuchus
        self.emit_direction = emit_direction

        # Create queue for waiting Chuchus
        self.chuchus_queue = arcade.SpriteList()
        for n in range(capacity):
            self.chuchus_queue.append(Chuchu(self))

    @property
    def no_emitted(self):
        return self.capacity - len(self.chuchus_queue)

    def go_to_tile(self, tile):
        self.on_tile = tile
        self.position = self.on_tile.position

    def get_chuchu(self):
        if any(self.chuchus_queue) and self.emit_timer <= 0:
            self.emit_timer = self.emit_rate
            c = self.chuchus_queue.pop()
            if DEBUG_ON:
                print(f"Number of Chuchus emitted: {self.no_emitted}")
            return c

    def update(self, delta_time):
        if self.emit_timer > 0:
            self.emit_timer -= delta_time


class Drain(arcade.Sprite):
    """
    A Drain for draining Chuchus
    """

    def __init__(self, on_tile, **kwargs):

        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.texture = TEXTURES[D_D1]
        self.position = on_tile.position

        # Number of Chuchus drained
        self.no_drained = 0

    def drained(self, chuchu):
        """
        <chuchu> has been drained by me
        """
        self.no_drained += 1
        if DEBUG_ON:
            print(f"I have drained a total number of {self.no_drained} chuchus :D")


class Annotation(arcade.Sprite):
    def __init__(self, **kwargs):
        # kwargs["filename"] = "images/Annotations/Annotation_2.png"
        kwargs["scale"] = TILE_SCALING
        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.texture = TEXTURES[A_UP1]


class TileMatrix:
    """
    Matrix of Tile(s) >:)
    Consists of chuchus
    """

    def __init__(
        self,
        level_data,
        tile_size=TILE_SIZE,
        matrix_offset_x=100,
        matrix_offset_y=100,
    ):
        # Ceate sprite lists
        self.tiles = arcade.SpriteList()
        self.chuchus = arcade.SpriteList()
        self.emitters = arcade.SpriteList()
        self.drains = arcade.SpriteList()
        self.annotations = arcade.SpriteList()
        self.players = arcade.SpriteList()

        self.matrix_width = len(level_data["tiles"][0])
        self.matrix_height = len(level_data["tiles"])
        self.matrix_offset_x = matrix_offset_x
        self.matrix_offset_y = matrix_offset_y

        # Add Tile objects with correct screen positions
        new_tile_x = matrix_offset_x
        new_tile_y = matrix_offset_y + (self.matrix_height - 1) * tile_size
        for row in level_data["tiles"]:
            self.tiles.extend(
                [
                    Tile(
                        type=type,
                        center_x=index * tile_size + new_tile_x,
                        center_y=new_tile_y,
                    )
                    for index, type in enumerate(row)
                ]
            )
            new_tile_y -= tile_size

        # self.tiles[0].texture = TileMatrix.textures[0]

        # Add emitters
        for e in level_data["emitters"]:
            self.add_emitter(
                Emitter(
                    self.get_tile(e["pos"]),
                    type=e["image"],
                    emit_direction=e["emit_direction"],
                )
            )

        # Add drains
        for d in level_data["drains"]:
            self.add_drain(Drain(self.get_tile(d["pos"])))

    @property
    def level_clear(self):
        """
        If all Chuchus are drained, level ends :P
        """
        if sum([d.no_drained for d in self.drains]) is sum(
            [e.capacity for e in self.emitters]
        ):
            return True
        else:
            return False

    def get_tile(self, position):
        """
        Return tile object on <position> in matrix
        """
        return self.tiles[
            position[1] * self.matrix_width + position[0] % self.matrix_width
        ]

    def move_player(self, player_no: int, direction: Direction) -> None:
        """
        The player is moved
        """
        p = self.players[player_no]
        # Current grid position
        current_pos = p.tile_pos
        # New position in grid (Y axis inverted for pos)
        new_pos = (
            current_pos[0] + direction.value[0],
            current_pos[1] + -1 * direction.value[1],
        )

        # Return if new position is illegal
        if not -1 < new_pos[0] < self.matrix_width:
            return None
        if not -1 < new_pos[1] < self.matrix_height:
            return None

        # Update player position in grid
        p.tile_pos = new_pos
        # Update player's screen coordinates to
        # match tile on new position
        p.position = self.get_tile(new_pos).position

    def add_player(self, player: Player, tile_pos) -> int:
        """
        Add a player to the game
        """
        player.tile_pos = tile_pos
        player.position = self.get_tile(tile_pos).position
        self.players.append(player)
        return self.players.index(player)

    def add_annotation(self, player_no, annotation: Annotation):
        """
        Add an annotation at the position of the player
        """
        annotation.position = self.players[player_no].position
        self.annotations.append(annotation)

    def add_emitter(self, emitter: arcade.Sprite):
        """
        Append emitter to list of emitters
        """
        self.emitters.append(emitter)

    def add_drain(self, drain: arcade.Sprite):
        """
        Append drain to list of drains
        """
        self.drains.append(drain)

    def get_sprite_from_screen_coordinates(self, coordinates, sprite_list):
        """
        Returns a sprite from <sprite_list> matching screen <coordinates>
        """
        for t in sprite_list:
            if (
                arcade.get_distance(
                    t.position[0], t.position[1], coordinates[0], coordinates[1]
                )
                < IS_ON_TILE_DIFF
            ):
                return t
        return None

    def draw(self, pixelated=True):
        self.tiles.draw(pixelated=pixelated)
        self.annotations.draw(pixelated=pixelated)
        self.emitters.draw(pixelated=pixelated)
        self.drains.draw(pixelated=pixelated)
        self.chuchus.draw(pixelated=pixelated)
        self.players.draw(pixelated=pixelated)

    def update(self, delta_time):

        # Pull chuchus from emitters
        for e in self.emitters:
            c = e.get_chuchu()

            if c is not None:
                self.chuchus.append(c)

            # Update emitter
            e.update(delta_time)

        # Handle waiting Chuchus
        for c in self.chuchus:
            if c.waiting_for_orders is True:

                # Is Chuchu on a drain
                current_drain = self.get_sprite_from_screen_coordinates(
                    c.position, self.drains
                )
                if not current_drain is None:
                    c.drained()
                    current_drain.drained(c)

                    # Nothing more to do for this Chuchu
                    break

                # Look at tiles
                current_tile = self.get_sprite_from_screen_coordinates(
                    c.position, self.tiles
                )
                assert current_tile is not None, "Chuchu was not on any tile"
                # Assume Chuchu is moving on
                new_direction = c.my_direction

                # If Chuchus current direction is blocked by the tile the direction is changed to the tile's out direction
                if c.my_direction in current_tile.my_type["block_dirs"]:
                    new_direction = current_tile.my_type["out_dir"]

                c.move(new_direction)

            c.update(delta_time)

        for p in self.players:
            p.update(delta_time)


class MyGame(arcade.Window):
    """
    Main application class.
    """

    # Drawn upside down
    levels = {
        1: {
            "tiles": [
                [5, 1, 1, 1, 1, 6],
                [4, 0, 0, 0, 0, 2],
                [4, 0, 0, 0, 0, 2],
                [4, 0, 0, 0, 0, 2],
                [8, 3, 3, 3, 3, 7],
            ],
            "emitters": [
                {"pos": (4, 1), "emit_direction": Direction.LEFT, "image": 0},
                {"pos": (2, 3), "emit_direction": Direction.UP, "image": 0},
            ],
            "drains": [{"pos": (2, 0)}],
        },
        2: {
            "tiles": [
                [5, 1, 6, 5, 6],
                [4, 0, 2, 4, 2],
                [4, 0, 2, 4, 2],
                [4, 0, 0, 0, 2],
                [8, 3, 3, 3, 7],
            ],
            "emitters": [{"pos": (3, 4), "emit_direction": Direction.UP, "image": 0}],
            "drains": [{"pos": (2, 1)}],
        },
    }

    def __init__(self, width, height):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__(width, height)

        # Set up the player info
        self.player_sprite = None
        self.player_score = None
        self.player_lives = None
        self.players = None

        # Set up matrix
        self.tile_matrix = None

        # What level is it
        self.level = None

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # Get list of joysticks
        joysticks = arcade.get_joysticks()

        if joysticks:
            print("Found {} joystick(s)".format(len(joysticks)))

            # Use 1st joystick found
            self.joystick = joysticks[0]

            # Communicate with joystick
            self.joystick.open()

            # Map joysticks functions to local functions
            self.joystick.on_joybutton_press = self.on_joybutton_press
            self.joystick.on_joybutton_release = self.on_joybutton_release
            self.joystick.on_joyaxis_motion = self.on_joyaxis_motion
            self.joystick.on_joyhat_motion = self.on_joyhat_motion

        else:
            print("No joysticks found")
            self.joystick = None

            # self.joystick.
        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

    def setup(self):
        """Set up the game and initialize the variables."""

        # No points when the game starts
        self.player_score = 0

        # No of lives
        self.player_lives = PLAYER_LIVES

        # Start at level 1
        self.level = 1

        self.players = arcade.SpriteList()
        self.players.append(Player())
        self.start_level()

    def start_level(self):
        # Create tile matrix
        assert (
            self.level in MyGame.levels.keys()
        ), f"Error: no data for level {self.level}"
        self.tile_matrix = TileMatrix(level_data=MyGame.levels[self.level])
        # Add a player to the game
        for p in self.players:
            p_no = self.tile_matrix.add_player(p, (1, 1))
            if DEBUG_ON:
                print(f"Added player as no. {p_no}")

    def end_level(self):
        self.level += 1
        self.start_level()

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw players score on screen
        arcade.draw_text(
            "SCORE: {}".format(self.player_score),  # Text to show
            10,  # X position
            SCREEN_HEIGHT - 20,  # Y positon
            arcade.color.WHITE,  # Color of text
        )

        # Draw matrix on screen
        self.tile_matrix.draw()

    def on_update(self, delta_time):
        """
        Movement and game logic
        """

        self.tile_matrix.update(delta_time)

        if self.tile_matrix.level_clear:
            self.end_level()

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """

        # Track state of arrow keys
        # These directions are in level coordinates,
        # that is y is opposite of screen coordinatesystem.
        if key == arcade.key.UP:
            self.up_pressed = True
            self.tile_matrix.move_player(0, Direction.UP)
        elif key == arcade.key.DOWN:
            self.down_pressed = True
            self.tile_matrix.move_player(0, Direction.DOWN)
        elif key == arcade.key.LEFT:
            self.left_pressed = True
            self.tile_matrix.move_player(0, Direction.LEFT)
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
            self.tile_matrix.move_player(0, Direction.RIGHT)

        if key == FIRE_KEY:
            self.tile_matrix.add_annotation(0, Annotation())

    def on_key_release(self, key, modifiers):
        """
        Called whenever a key is released.
        """

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

    def on_joybutton_press(self, joystick, button_no):
        print("Button pressed:", button_no)
        # Press the fire key
        self.on_key_press(FIRE_KEY, [])

    def on_joybutton_release(self, joystick, button_no):
        print("Button released:", button_no)

    def on_joyaxis_motion(self, joystick, axis, value):
        print("Joystick axis {}, value {}".format(axis, value))

    def on_joyhat_motion(self, joystick, hat_x, hat_y):
        print("Joystick hat ({}, {})".format(hat_x, hat_y))


def main():
    """
    Main method
    """

    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
