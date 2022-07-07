"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""
from enum import Enum
import arcade


SPRITE_SCALING = 0.5
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


class Player(arcade.Sprite):
    """
    The player
    """

    def __init__(self, tile_pos, **kwargs):
        """
        Setup new Player object
        """
        self._tile_pos = tile_pos

        # Graphics to use for Player
        kwargs["filename"] = "images/playerShip1_red.png"

        # How much to scale the graphics
        kwargs["scale"] = SPRITE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

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

    T__ = 0
    T_T = 1
    TR_ = 2
    T_B = 3
    TL_ = 4
    TLT = 5
    TRT = 6
    TRB = 7
    TLB = 8


class Tile(arcade.Sprite):
    """
    A tile :)
    """

    types = {
        0: {"out_dir": (0, 0), "block_dirs": [], "image": "wall_none.png"},
        1: {"out_dir": (1, 0), "block_dirs": [(0, 1)], "image": "wall_top.png"},
        2: {"out_dir": (0, -1), "block_dirs": [(1, 0)], "image": "wall_right.png"},
        3: {"out_dir": (-1, 0), "block_dirs": [(0, -1)], "image": "wall_bottom.png"},
        4: {"out_dir": (0, 1), "block_dirs": [(-1, 0)], "image": "wall_left.png"},
        5: {
            "out_dir": (1, 0),
            "block_dirs": [(0, 1), (-1, 0)],
            "image": "wall_top_left.png",
        },
        6: {
            "out_dir": (0, -1),
            "block_dirs": [(0, 1), (1, 0)],
            "image": "wall_top_right.png",
        },
        7: {
            "out_dir": (-1, 0),
            "block_dirs": [(1, 0), (0, -1)],
            "image": "wall_bottom_right.png",
        },
        8: {
            "out_dir": (0, 1),
            "block_dirs": [(-1, 0), (0, -1)],
            "image": "wall_bottom_left.png",
        },
    }

    def __init__(self, type=0, center_x=0, center_y=0, **kwargs):
        """
        Setup new Tile object
        """
        self.my_type = Tile.types[type]

        # Graphics to use for Tile
        kwargs["filename"] = f'images/Tiles/{self.my_type["image"]}'

        # How much to scale the graphics
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

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
        self.my_direction = None

        # Steps per tile
        self.my_speed = my_speed

        # Graphics
        kwargs["filename"] = "images/Chuchu/Chuchu.png"

        # Scale the graphics
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        # The screen coordinates I'm moving towards
        self.my_destination_screen_coordinates = (self.center_x, self.center_y)

        # All chuchus start at their emitter
        self.position = my_emitter.position

        # My first move is in emit direction
        # This will calculate my destination screen coordinates
        self.move(my_emitter.emit_vector)

        # I have reached my destination, and I'm waiting for a new direction to move in.
        self.waiting_for_orders = False

    def drained(self):
        """
        When a Chuchu reaches a drain and should no longer exist
        """

        print("I was drained. Yes!")
        self.kill()

    def move(self, new_direction):
        """
        Takes a direction and updates destination screen coordinates.
        """
        # If the new_direction is NOT the null vector,
        # I will continue in my current direction. Otherwise,
        # I will change direction to new_direction
        if new_direction != (0, 0):
            # Current direction is updated
            self.my_direction = new_direction

        # Update my screen destination relative to lower left of martrix
        self.my_destination_screen_coordinates = [
            n * TILE_SIZE for n in self.my_direction
        ]

        # Translate to screen position relative to lower left of window
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
        self, on_tile, type=0, capacity=5, emit_vector=(-1, 0), emit_rate=2.0, **kwargs
    ):
        """
        Setup new Emitter
        """

        # How fast will Chuchus spawn
        self.emit_rate = emit_rate

        # Ready to emit a chuchu
        self.emit_timer = 0

        self.capacity = capacity

        kwargs["filename"] = Emitter.emitter_types[type]
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.go_to_tile(on_tile)

        # Direction for the outspitted Chuchus
        self.emit_vector = emit_vector

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
        kwargs["filename"] = "images/Drain/Drain_cream.png"
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.position = on_tile.position

        # Number of Chuchus drained
        self.no_drained = 0

    def drained(self, chuchu):
        """
        <chuchu> has been drained by me
        """
        self.no_drained += 1
        print(f"I have drained a total number of {self.no_drained} chuchus :D")


class Annotation(arcade.Sprite):
    def __init__(self, **kwargs):
        kwargs["filename"] = "images/Annotations/Annotation_2.png"
        kwargs["scale"] = TILE_SCALING
        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)


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
        # Create matrix
        self.matrix = arcade.SpriteList()

        self.matrix_width = len(level_data["tiles"][0])
        self.matrix_height = len(level_data["tiles"])
        self.matrix_offset_x = matrix_offset_x
        self.matrix_offset_y = matrix_offset_y

        # Append tile objects with correct screen positions to matrix
        new_tile_x = matrix_offset_x
        new_tile_y = matrix_offset_y + (self.matrix_height - 1) * tile_size
        for row in level_data["tiles"]:
            self.matrix.extend(
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

        # Create list for chuchus
        self.chuchus = arcade.SpriteList()

        # Create list for Players
        self.players = arcade.SpriteList()
        # Append player to playerlist with start position
        self.players.append(Player(tile_pos=(1, 1)))

        # Create list for Emitters
        self.emitters = arcade.SpriteList()

        # Add an emitter
        self.add_emitter(
            Emitter(
                self.get_tile(level_data["emitter"]["pos"]),
                type=level_data["emitter"]["image"],
            )
        )

        # Create list for drains
        self.drains = arcade.SpriteList()

        # Add a drain
        self.add_drain(Drain(self.get_tile(level_data["drain"]["pos"])))

        # Create list for annotations
        self.annotations = arcade.SpriteList()

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
        return self.matrix[
            position[1] * self.matrix_width + position[0] % self.matrix_width
        ]

    def move_player(self, player_no: int, dir: list):
        """
        The player is moved
        """
        p = self.players[player_no]
        # Current grid position
        current_pos = p.tile_pos
        # New position in grid
        new_pos = (current_pos[0] + dir[0], current_pos[1] + dir[1])

        # Check if new position is legal
        if not -1 < new_pos[0] < self.matrix_width:
            return None
        if not -1 < new_pos[1] < self.matrix_height:
            return None

        # Update player position in grid
        self.players[player_no].tile_pos = new_pos

        # FIXME this should be handled in the player
        # Update player position on screen
        p.center_x = p.tile_pos[0] * TILE_SIZE + self.matrix_offset_x
        p.center_y = p.tile_pos[1] * TILE_SIZE + self.matrix_offset_y

    def add_annotation(self, player_no, annotation: Annotation):
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

    def draw(self):
        self.matrix.draw()
        self.annotations.draw()
        self.emitters.draw()
        self.drains.draw()
        self.chuchus.draw()
        self.players.draw()

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
                    c.position, self.matrix
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


class PlayerShot(arcade.Sprite):
    """
    A shot fired by the Player
    """

    def __init__(self, center_x=0, center_y=0):
        """
        Setup new PlayerShot object
        """

        # Set the graphics to use for the sprite
        super().__init__("images/Lasers/laserBlue01.png", SPRITE_SCALING)

        self.center_x = center_x
        self.center_y = center_y
        self.change_y = PLAYER_SHOT_SPEED

    def update(self, delta_time):
        """
        Move the sprite
        """

        # Update y position
        self.center_y += self.change_y

        # Remove shot when over top of screen
        if self.bottom > SCREEN_HEIGHT:
            self.kill()


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
            "emitter": {"pos": (1, 1), "image": 0},
            "drain": {"pos": (2, 0)},
        },
        2: {
            "tiles": [
                [5, 1, 6, 5, 6],
                [4, 0, 2, 4, 2],
                [4, 0, 2, 4, 2],
                [4, 0, 0, 0, 2],
                [8, 3, 3, 3, 7],
            ],
            "emitter": {"pos": (3, 4), "image": 0},
            "drain": {"pos": (2, 1)},
        },
    }

    def __init__(self, width, height):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__(width, height)

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = None

        # Set up the player info
        self.player_sprite = None
        self.player_score = None
        self.player_lives = None

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

        # Sprite lists
        self.player_shot_list = arcade.SpriteList()

        # Start at level 1
        self.level = 1

        self.start_level()

    def start_level(self):
        # Create tile matrix
        assert (
            self.level in MyGame.levels.keys()
        ), f"Error: no data for level {self.level}"
        self.tile_matrix = TileMatrix(level_data=MyGame.levels[self.level])

    def end_level(self):
        self.level += 1
        self.start_level()

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the player shot
        self.player_shot_list.draw()

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

        # Update the player shots
        # self.player_shot_list.update()

        self.tile_matrix.update(delta_time)

        if self.tile_matrix.level_clear:
            self.end_level()

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """

        # Track state of arrow keys
        if key == arcade.key.UP:
            self.up_pressed = True
            self.tile_matrix.move_player(0, (0, 1))
        elif key == arcade.key.DOWN:
            self.down_pressed = True
            self.tile_matrix.move_player(0, (0, -1))
        elif key == arcade.key.LEFT:
            self.left_pressed = True
            self.tile_matrix.move_player(0, (-1, 0))
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
            self.tile_matrix.move_player(0, (1, 0))

        if key == FIRE_KEY:
            # new_shot = PlayerShot(
            #    self.player_sprite.center_x, self.player_sprite.center_y
            # )
            self.tile_matrix.add_annotation(0, Annotation())

            # self.player_shot_list.append(new_shot)

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
