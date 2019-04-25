# flake8: noqa E501
"""
*GameBot* {version}
Copyright (c) 2019 Richard Clark <rick@seerickcode.com> All rights reserved.
Copyright (C) 2015 Slackbot Contributors

Training / Presentation game bot
"""

import logging
import time
import random
import pygame
import pygame.freetype
import re
from better_profanity import profanity
from machine.plugins.base import MachineBasePlugin
from machine.plugins.decorators import respond_to, listen_to
from webcolors import hex_to_rgb, name_to_rgb


logger = logging.getLogger(__name__)

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600


class GameBotPlugin(MachineBasePlugin):
    """
    *GameBot* {version}
    Copyright (c) 2019 Richard Clark <rick@seerickcode.com> All rights reserved.
    Copyright (C) 2015 Slackbot Contributors

    Training / Presentation game bot
    """

    def init(self):

        logger.info("Gamebot Starting")
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.GAME_FONT = pygame.freetype.Font(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=64
        )
        self.GAME_FONT.strong = True
        self.screen.fill((255, 255, 255))
        # or just `render_to` the target surface.
        self.GAME_FONT.render_to(self.screen, (110, 250), "THUNDERDOME", (0, 0, 0))
        self.GAME_FONT.render_to(self.screen, (160, 320), "IS WAITING", (0, 0, 0))
        pygame.display.flip()

    def _center_text(self, text):
        """
        Renders text centered on the display surface
        """
        _rect = self.GAME_FONT.get_rect(text)
        x = DISPLAY_WIDTH / 2 - _rect.width / 2
        y = DISPLAY_HEIGHT / 2 - _rect.height / 2

        self.GAME_FONT.render_to(self.screen, (x, y), text, (0, 0, 0))

    @respond_to(
        r"game ((?P<rgb>#[A-Fa-f0-9]{6}|#[A-Fa-f0-9]{3})|(?P<color>\w+))$",
        re.IGNORECASE,
    )
    def game_color(self, msg, rgb=None, color=None):

        try:
            color_tuple = None
            if rgb is not None:
                color_tuple = hex_to_rgb(rgb)

            if color is not None:
                color_tuple = name_to_rgb(color)

            if color_tuple is not None:
                logger.warn(f"User Stuff = {msg.sender}")
                name = profanity.censor(msg.sender.real_name)
                logger.warn(f"Changing color to {color_tuple} for {name}")
                self.screen.fill(color_tuple)
                self._center_text(name)
                pygame.display.flip()
            else:
                msg.reply(f"Sorry, couldn't work out that color")

        except Exception as e:
            msg.reply(
                f":slightly_frowning_face: Doh, something went wrong, sorry\n`{e}`"
            )

