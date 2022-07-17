"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""
from enum import Enum
from os import DirEntry
from random import randint
from typing import List, Optional, Union
import arcade

# Print debug information
DEBUG_ON = not True

SPRITE_SCALING = 4
TILE_SCALING = 4
TILE_SIZE = TILE_SCALING * 16
# Time in ms for each keyframe
CHUCHU_ANIMATION_SPEED = 300
CHUCHU_NO_OF_TYPES = 5

# When Chuchu is closer to destination than this, it has arrived
IS_ON_TILE_DIFF = 1.0

# Set the size of the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 650

# Variables controlling the player
PLAYER_LIVES = 3
PLAYER_SPEED_X = 5
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_START_Y = 50
PLAYER_SHOT_SPEED = 4

# Number of seconds to show alternative texture
# for drains when a ChuChu has been drained
DRAIN_OPEN_TIME = 0.5

# Annotations will disapear after this many seconds
ANNOTATION_LIFETIME_SECONDS = 10

# The minimal alpha value to use with fading annotations.
ANNOTATION_MIN_ALPHA = 0

# The maximum number of sumultanious annotations for a player
ANNOTATION_MAX_NO = 3

BUTTON_UP = 3
BUTTON_RIGHT = 2
BUTTON_DOWN = 1
BUTTON_LEFT = 0

# Load a textures from a tilemap
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
C1_LEFT1 = 23
C1_LEFT2 = C1_LEFT1 + 27
C1_LEFT3 = C1_LEFT2 + 27

C1_DOWN1 = C1_LEFT1 + 1
C1_DOWN2 = C1_DOWN1 + 27
C1_DOWN3 = C1_DOWN2 + 27

C1_UP1 = C1_LEFT1 + 2
C1_UP2 = C1_UP1 + 27
C1_UP3 = C1_UP2 + 27

C1_RIGHT1 = C1_LEFT1 + 3
C1_RIGHT2 = C1_RIGHT1 + 27
C1_RIGHT3 = C1_RIGHT2 + 27


# Emitters
E_E1 = 11 * 27 + 9

# Drains
D1_CLOSED = 10 * 27 + 13
D1_OPEN = D1_CLOSED + 27

# Annotations
A_UP1 = 7 * 27 + 1

# Players
P_P1 = 9 * 27 + 2

# Walls
W_H1 = 11 * 27 + 1
W_V1 = W_H1 + 1


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

        # How much to scale the graphics
        kwargs["scale"] = SPRITE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.texture: arcade.Texture = TEXTURES[P_P1]

        # The level the Player is currently playing
        self.level: Level = None

        # The joystick used to control the player
        self.__joystick = None

    @property
    def joystick(self):
        return self.__joystick

    @joystick.setter
    def joystick(self, joystick):
        self.__joystick = joystick

        # Map joystick methods to local methods
        self.__joystick.on_joybutton_press = self.__on_joybutton_press
        self.__joystick.on_joyaxis_motion = self.__on_joyaxis_motion
        self.__joystick.on_joyhat_motion = self.__on_joyhat_motion

        # Communicate with joystick
        self.__joystick.open()

        if DEBUG_ON:
            print(
                f"Added joystick to Player: {self.__joystick.device.name} ({self.__joystick.device.manufacturer})"
            )
            print(
                f"Joystick has these controls: {self.__joystick.device.get_controls()}"
            )

    def __on_joybutton_press(self, joystick, button_no):
        if DEBUG_ON:
            print(f"Button {button_no} pressed in player")

        # Add an annotation to the level being played
        ad = None
        if self.level:
            if button_no == BUTTON_UP:
                ad = Direction.UP
            elif button_no == BUTTON_RIGHT:
                ad = Direction.RIGHT
            elif button_no == BUTTON_DOWN:
                ad = Direction.DOWN
            elif button_no == BUTTON_LEFT:
                ad = Direction.LEFT
            if ad:
                self.level.add_annotation(self, ad)

    def __on_joyaxis_motion(self, joystick, axis, value):
        """
        Move the player on joyaxis motion (Integer values)
        """
        if DEBUG_ON:
            print(f"Joystick axis: {axis}, value: {value}")

        # assert value in [-1, 0, 1], f"Value '{value}' from joystick motion must be -1, 0 or 1"
        if value in [-1, 0, 1]:
            if axis == "hat_x":
                d = Direction((int(value), 0))
            else:
                d = Direction((0, int(value)))
            if d:
                self.level.move_player(self, d)
        else:
            if DEBUG_ON:
                print(f"Ignoring invalid joyaxis value '{value}' in Player")

    def __on_joyhat_motion(self, joystick, hat_x, hat_y):
        if DEBUG_ON:
            print("Joystick hat ({}, {})".format(hat_x, hat_y))


class Tile(arcade.Sprite):
    """
    A tile :)
    """

    # The value of Direction keys, are the Directions a ChuChu should move
    # after having entered the tile from the key Direction
    types = {
        0: {"texture_no": T_TILE_NONE},
        1: {
            Direction.UP: Direction.RIGHT,
        },
        2: {
            Direction.RIGHT: Direction.DOWN,
        },
        3: {
            Direction.DOWN: Direction.LEFT,
        },
        4: {
            Direction.LEFT: Direction.UP,
        },
        5: {
            Direction.UP: Direction.RIGHT,
            Direction.LEFT: Direction.DOWN,
        },
        6: {
            Direction.RIGHT: Direction.DOWN,
            Direction.UP: Direction.LEFT,
        },
        7: {
            Direction.DOWN: Direction.LEFT,
            Direction.RIGHT: Direction.UP,
        },
        8: {
            Direction.LEFT: Direction.UP,
            Direction.DOWN: Direction.RIGHT,
        },
    }

    def __init__(self, type=0, center_x=0, center_y=0, **kwargs):
        """
        Setup new Tile object
        """
        self.__type = type

        # How much to scale the graphics
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

        self.texture = TEXTURES[T_TILE_NONE]

        self.position = center_x, center_y

    def get_out_direction(self, direction_in: Direction) -> Direction:
        """
        Return the direction to move in if Tile was entered from <direction_in>
        """
        return Tile.types[self.__type].get(direction_in, direction_in)

    def get_walls(self) -> List[arcade.Sprite]:
        """
        Get a list of tile's wall Sprites.
        """
        walls = []
        for k in Tile.types[self.__type].keys():
            if type(k) == Direction:
                w = arcade.Sprite(scale=SPRITE_SCALING)
                w.position = [sum(x) for x in zip(k * (TILE_SIZE / 2), self.position)]
                if k in (Direction.LEFT, Direction.RIGHT):
                    w.texture = TEXTURES[W_V1]
                else:
                    w.texture = TEXTURES[W_H1]
                walls.append(w)
        return walls


class Chuchu(arcade.AnimatedTimeBasedSprite):
    """
    A Chuchu (AKA a mouse)
    """

    def __init__(self, my_emitter, my_speed=2, type: Optional[int] = None, **kwargs):
        """
        Setup new Chuchu. It always moves towards <my_destination_screen_coordinates>.
        When the destination is reached. I waits for a new direction passed to it with
        move().
        """
        # The direction I'm moving in
        self.my_direction = Direction.NONE

        # Type is random if not specified
        if type is None:
            self.type = randint(0, CHUCHU_NO_OF_TYPES)

        # Steps per tile
        self.my_speed = my_speed

        # Scale the graphics
        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)

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
        When a Chuchu reaches a drain it should no longer exist
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

        self.frames = self.get_keyframes(
            self.my_direction
        )  # Chuchu.frames[self.my_direction]

        self.waiting_for_orders = False

    def get_keyframes(self, direction: Direction) -> List[arcade.AnimationKeyframe]:

        if direction == Direction.UP:
            texture_nos = (C1_UP1, C1_UP2, C1_UP1, C1_UP3)
        elif direction == Direction.RIGHT:
            texture_nos = (C1_RIGHT1, C1_RIGHT2, C1_RIGHT1, C1_RIGHT3)
        elif direction == Direction.DOWN:
            texture_nos = (C1_DOWN1, C1_DOWN2, C1_DOWN1, C1_DOWN3)
        else:
            texture_nos = (C1_LEFT1, C1_LEFT2, C1_LEFT1, C1_LEFT3)

        # How many rows to skip in spritesheet
        type_offset = self.type * (3 * 27)

        texture_nos = [n + type_offset for n in texture_nos]

        # Create Keyframe objects
        return [
            arcade.AnimationKeyframe(
                tile_id=i, duration=CHUCHU_ANIMATION_SPEED, texture=TEXTURES[t]
            )
            for i, t in enumerate(texture_nos)
        ]

    def on_update(self, delta_time):
        """
        Move chuchu towards destination coordinates if not there yet.
        """
        self.update_animation(delta_time)
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

    def on_update(self, delta_time):
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

        # self.texture = TEXTURES[D1_CLOSED]
        self.position = on_tile.position

        # Number of Chuchus drained
        self.no_drained = 0

        # How long to show alternative texture when darining a ChuChu
        self.open_time_seconds = 0

        self.frames = [TEXTURES[D1_CLOSED], TEXTURES[D1_OPEN]]
        self.texture = self.frames[0]

    def drained(self, chuchu):
        """
        <chuchu> has been drained by me
        """
        self.no_drained += 1
        self.texture = self.frames[1]
        self.open_time_seconds = DRAIN_OPEN_TIME
        if DEBUG_ON:
            print(f"I have drained a total number of {self.no_drained} chuchus :D")

    def on_update(self, delta_time):

        if self.open_time_seconds > 0:
            self.open_time_seconds -= delta_time
        elif self.open_time_seconds < 0:
            self.texture = self.frames[0]
            self.open_time_seconds = 0


class Annotation(arcade.Sprite):
    """
    Annotations will guide ChuChus in the direction the Annotation is pointing.
    The Annotation is deleted after <lifetime> seconds.
    """

    def __init__(self, direction: Direction, owner: Player, lifetime, **kwargs):

        kwargs["scale"] = TILE_SCALING

        # Pass arguments to class arcade.Sprite
        super().__init__(**kwargs)
        self.direction = direction
        self.texture = TEXTURES[A_UP1]
        self.owner = owner
        self.position = owner.position

        # Rotate based on direction
        self.angle = -90 * (
            Direction.UP,
            Direction.RIGHT,
            Direction.DOWN,
            Direction.LEFT,
        ).index(self.direction)

        self.max_lifetime = lifetime
        self.lifetime = lifetime

    def on_update(self, delta_time):
        if self.lifetime <= 0:
            self.kill()
        self.alpha = max(255 * self.lifetime / self.max_lifetime, ANNOTATION_MIN_ALPHA)
        self.lifetime -= delta_time


class Level:
    """
    An instantiated level in the game
    """

    def __init__(
        self,
        level_data,
        tile_size: int = TILE_SIZE,
        matrix_offset_x: int = 50,
        matrix_offset_y: int = 50,
        level_time_seconds: int = 60,
    ):
        # Ceate sprite lists
        self.tiles = arcade.SpriteList()
        self.chuchus = arcade.SpriteList()
        self.emitters = arcade.SpriteList()
        self.drains = arcade.SpriteList()
        self.annotations = arcade.SpriteList()
        self.players = arcade.SpriteList()
        self.walls = arcade.SpriteList()

        self.__time_left = level_time_seconds

        self.matrix_width = len(level_data["tiles"][0])
        self.matrix_height = len(level_data["tiles"])
        self.matrix_offset_x = matrix_offset_x
        self.matrix_offset_y = matrix_offset_y

        # Add Tile objects with correct screen positions
        new_tile_x = matrix_offset_x
        new_tile_y = matrix_offset_y + (self.matrix_height - 1) * tile_size
        for row in level_data["tiles"]:
            for index, type in enumerate(row):
                t = Tile(
                    type=type,
                    center_x=index * tile_size + new_tile_x,
                    center_y=new_tile_y,
                )
                self.tiles.append(t)
                # Add the walls for the tile
                self.walls.extend(t.get_walls())
            new_tile_y -= tile_size

        # Add emitters
        for e in level_data["emitters"]:
            self.emitters.append(
                Emitter(
                    self.get_tile(e["pos"]),
                    type=e["image"],
                    emit_direction=e["emit_direction"],
                )
            )

        # Add drains
        for d in level_data["drains"]:
            self.drains.append(Drain(self.get_tile(d["pos"])))

    @property
    def time_left(self) -> float:
        """
        Time left in the level
        """
        return self.__time_left

    @property
    def level_clear(self) -> bool:
        """
        Is the level done/clear
        """

        # If all Chuchus have been drained
        if sum([d.no_drained for d in self.drains]) is sum(
            [e.capacity for e in self.emitters]
        ):
            return True

        # Time has expired
        if self.__time_left <= 0:
            return True

        # Level is not clear/done
        return False

    def get_tile(self, position) -> arcade.Sprite:
        """
        Return tile object on <position> in level list
        """
        return self.tiles[
            position[1] * self.matrix_width + position[0] % self.matrix_width
        ]

    def move_player(self, player: Player, direction: Direction) -> None:
        """
        Move a player
        """
        assert player in self.players, "Player is not in Level"
        if DEBUG_ON:
            print(f"Move player {player} in direction:", direction)

        # Calculate new position
        new_pos = [sum(x) for x in zip(player.position, direction * TILE_SIZE)]

        # Move to new screen position, if it has a tile.
        if self.get_sprite_from_screen_coordinates(new_pos, self.tiles):
            player.position = new_pos

    def add_player(self, player: Player, tile_pos) -> int:
        """
        Add a player to the game
        """
        # Let Player know, the game they are in (So they can move)
        player.level = self
        # Add the Player to the game
        self.players.append(player)
        # Player's position is same as Emitter with same index as Player
        player.position = self.drains[self.players.index(player)].position

        return self.players.index(player)

    def add_annotation(self, owner: Player, direction: Direction):
        """
        Add an annotation at the position of the player
        """
        # Don't place an Annotation if one exists at player's position
        if self.get_sprite_from_screen_coordinates(owner.position, self.annotations):
            return None

        # If player has reached the limit, remove oldest Annotation
        a = [a for a in self.annotations if a.owner == owner]
        if len(a) >= ANNOTATION_MAX_NO:
            self.annotations[self.annotations.index(a[0])].kill()

        # Add new annotation
        self.annotations.append(
            Annotation(direction, owner, ANNOTATION_LIFETIME_SECONDS)
        )

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
        self.walls.draw(pixelated=pixelated)
        self.annotations.draw(pixelated=pixelated)
        self.emitters.draw(pixelated=pixelated)
        self.drains.draw(pixelated=pixelated)
        self.chuchus.draw(pixelated=pixelated)
        self.players.draw(pixelated=pixelated)

    def on_update(self, delta_time):

        # Remove expired annotations
        self.annotations.on_update(delta_time)
        self.drains.on_update(delta_time)

        # Pull ChuChus from emitters
        for e in self.emitters:
            c = e.get_chuchu()

            if c is not None:
                self.chuchus.append(c)

            # Update emitter
            e.on_update(delta_time)

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

                # Change direction if on an Annotation
                if current_annotation := self.get_sprite_from_screen_coordinates(
                    c.position, self.annotations
                ):
                    c.move(current_annotation.direction)

                # Get the tile the waiting ChuChu is on
                current_tile = self.get_sprite_from_screen_coordinates(
                    c.position, self.tiles
                )
                assert current_tile is not None, "Chuchu was not on any tile"
                # Potentially change direction
                c.move(current_tile.get_out_direction(c.my_direction))

            c.on_update(delta_time)

        self.__time_left -= delta_time


class MyGame(arcade.Window):
    """
    Main application class.
    """

    levels = {
        1: {
            "tiles": [
                [5, 1, 1, 1, 6, 5, 1, 1, 1, 1, 1, 6],
                [4, 0, 0, 0, 2, 4, 0, 0, 0, 0, 0, 2],
                [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                [4, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 7],
                [8, 3, 3, 0, 0, 0, 0, 0, 0, 1, 1, 6],
                [5, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                [4, 0, 0, 0, 0, 0, 2, 4, 0, 0, 0, 2],
                [8, 3, 3, 3, 3, 3, 7, 8, 3, 3, 3, 7],
            ],
            "emitters": [
                {"pos": (4, 3), "emit_direction": Direction.RIGHT, "image": 0},
                {"pos": (7, 3), "emit_direction": Direction.DOWN, "image": 0},
                {"pos": (4, 5), "emit_direction": Direction.LEFT, "image": 0},
                {"pos": (7, 5), "emit_direction": Direction.UP, "image": 0},
            ],
            "drains": [
                {"pos": (1, 1)},
                {"pos": (10, 1)},
                {"pos": (10, 7)},
                {"pos": (1, 7)},
            ],
        },
        2: {
            "tiles": [
                [5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6],
                [5, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 7],
                [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
                [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7],
                [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
                [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7],
                [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
                [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                [8, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 7],
            ],
            "emitters": [
                {"pos": (0, 0), "emit_direction": Direction.RIGHT, "image": 0},
                {"pos": (3, 0), "emit_direction": Direction.RIGHT, "image": 0},
                {"pos": (6, 0), "emit_direction": Direction.RIGHT, "image": 0},
                {"pos": (9, 0), "emit_direction": Direction.RIGHT, "image": 0},
            ],
            "drains": [
                {"pos": (1, 7)},
                {"pos": (4, 7)},
                {"pos": (7, 7)},
                {"pos": (10, 7)},
            ],
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
        self.joysticks = arcade.get_joysticks()

        """
        if joysticks:
            print("Found {} joystick(s)".format(len(joysticks)))

            # Use 1st joystick found
            self.joystick = joysticks[0]

            # Communicate with joystick
            self.joystick.open()

            print(self.joystick.get_controls())

            # Map joysticks functions to local functions
            self.joystick.on_joybutton_press = self.on_joybutton_press
            self.joystick.on_joybutton_release = self.on_joybutton_release
            self.joystick.on_joyaxis_motion = self.on_joyaxis_motion
            self.joystick.on_joyhat_motion = self.on_joyhat_motion

        else:
            print("No joysticks found")
            self.joystick = None
        """

        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

    def setup(self):
        """Set up the game and initialize the variables."""

        # No points when the game starts
        self.player_score = 0

        # No of lives
        self.player_lives = PLAYER_LIVES

        # Start at this level
        self.level = 1

        self.players = arcade.SpriteList()
        p = Player()
        try:
            p.joystick = self.joysticks[0]
        except IndexError:
            print("No joystick to add to Player.")
        self.players.append(p)
        self.start_level()

    def start_level(self):
        # Create tile matrix
        assert (
            self.level in MyGame.levels.keys()
        ), f"Error: no data for level {self.level}"
        self.tile_matrix = Level(level_data=MyGame.levels[self.level])
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

        # Draw matrix on screen
        self.tile_matrix.draw()

        # Draw players score on screen
        arcade.draw_text(
            "Time left: {}".format(int(self.tile_matrix.time_left)),
            10,  # X position
            SCREEN_HEIGHT - 20,  # Y positon
            arcade.color.WHITE,  # Color of text
        )

    def on_update(self, delta_time):
        """
        Movement and game logic
        """

        self.tile_matrix.on_update(delta_time)

        if self.tile_matrix.level_clear:
            self.end_level()

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """

        # Track state of arrow keys
        # Move player 0
        if key == arcade.key.W:
            self.up_pressed = True
            self.tile_matrix.move_player(self.players[0], Direction.UP)
        elif key == arcade.key.S:
            self.down_pressed = True
            self.tile_matrix.move_player(self.players[0], Direction.DOWN)
        elif key == arcade.key.A:
            self.left_pressed = True
            self.tile_matrix.move_player(self.players[0], Direction.LEFT)
        elif key == arcade.key.D:
            self.right_pressed = True
            self.tile_matrix.move_player(self.players[0], Direction.RIGHT)

        ad = None
        if key == arcade.key.UP:
            ad = Direction.UP
        elif key == arcade.key.RIGHT:
            ad = Direction.RIGHT
        elif key == arcade.key.DOWN:
            ad = Direction.DOWN
        elif key == arcade.key.LEFT:
            ad = Direction.LEFT
        if ad:
            self.tile_matrix.add_annotation(self.players[0], ad)

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
