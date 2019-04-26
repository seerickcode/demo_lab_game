# flake8: noqa E501
"""
*GameBot* {version}
Copyright (c) 2019 Richard Clark <rick@seerickcode.com> All rights reserved.
Copyright (C) 2015 Slackbot Contributors

Training / Presentation game bot
"""

import os
import logging
import time
import random
import pygame
import pygame.freetype
import re
import operator
import datetime
from better_profanity import profanity
from machine.plugins.base import MachineBasePlugin
from machine.plugins.decorators import respond_to, listen_to, schedule
from webcolors import hex_to_rgb, name_to_rgb

logger = logging.getLogger(__name__)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600
OPERATORS = [
    ("+", operator.add),
    ("-", operator.sub),
    ("x", operator.mul),
    ("/", operator.truediv),
    ("xor", operator.xor),
]
DIFFICULTY = [
    # ( _min, _max, _operator_start, _operator_end)
    (1, 100, 0, 0),
    (1000, 1999, 0, 1),
    (1, 999, 0, 2),
    (1, 999, 0, 3),
    (1, 9999, 0, 3),
    (1, 9999, 2, 3),
    (1, 1000, 2, 3),
    (1, 128, 2, 4),
    (1, 1024, 2, 4),
    (1, 9999, 2, 4),
]


class GameBotPlugin(MachineBasePlugin):
    """
    *GameBot* {version}
    Copyright (c) 2019 Richard Clark <rick@seerickcode.com> All rights reserved.
    Copyright (C) 2015 Slackbot Contributors

    Training / Presentation game bot
    """

    def init(self):

        logger.info("Gamebot Starting")
        self.generating = True
        self.game_channel = self.settings.get("GAME_CHANNEL", None)
        self.admin_channel = self.settings.get("ADMIN_CHANNEL", None)
        self.delay = int(self.settings.get("DEFAULT_DELAY", 15))
        self.question = self.settings.get("START_QUESTION", "We don't know")
        self.difficulty = int(self.settings.get("GAME_DIFFICULTY", 0))
        self.modulus = int(self.settings.get("DIFFICULTY_MODULUS", 5))
        self.pending_answer = float(self.settings.get("START_ANSWER", 0))
        self.answered = False
        self.answered_at = datetime.datetime.now()
        self.total = 0
        logger.info("Getting pygame ready")
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
        logger.info("Gamebot Ready")
        self.generating = False

    def _center_text(self, text):
        """
        Renders text centered on the display surface
        """
        _rect = self.GAME_FONT.get_rect(text)
        x = DISPLAY_WIDTH / 2 - _rect.width / 2
        y = DISPLAY_HEIGHT / 2 - _rect.height / 2

        self.GAME_FONT.render_to(self.screen, (x, y), text, (0, 0, 0))

    @respond_to(
        r"game (?P<answer>\d*.\d*)(?:\s+)((?P<rgb>#[A-Fa-f0-9]{6}|#[A-Fa-f0-9]{3})|(?P<color>\w+))$",
        re.IGNORECASE,
    )
    def game_color(self, msg, answer=None, rgb=None, color=None):

        if self.game_channel is None:
            self.game_channel = msg.channel.id
            logger.warn(f"game channel set to {self.game_channel}\n{msg.channel}")

        try:
            _answer = float(answer)

            if (
                self.answered is True
                or self.generating is True
                or _answer != self.pending_answer
            ):
                return

            self.answered_at = datetime.datetime.now()
            self.answered = True
            self.total += 1
            name = profanity.censor(msg.sender.real_name)
            msg.react("heavy_check_mark")
            msg.say(
                f":champagne: :fireworks: The answer has been found!"
                f".. it was {self.pending_answer}\nWait for new question"
            )

            color_tuple = None
            if rgb is not None:
                color_tuple = hex_to_rgb(rgb)

            if color is not None:
                color_tuple = name_to_rgb(color)

            if color_tuple is not None:
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

    @schedule(second="*/10")
    def generate_answer(self):
        if not self.answered or self.generating:
            return

        if (
            self.answered_at + datetime.timedelta(seconds=self.delay)
            > datetime.datetime.now()
        ):
            return

        self.generating = True

        _range = 1
        _opstart = 0
        _opend = 0

        if not self.total % self.modulus and self.difficulty < (len(DIFFICULTY) - 1):
            self.difficulty += 1
            self.say(
                self.game_channel,
                f"THUNDERDOME ! Increasing the difficulty to {self.difficulty}",
            )

        logger.warn(f"New Question and difficulty {self.difficulty}")

        _min, _max, _opstart, _opend = DIFFICULTY[self.difficulty]

        _op1 = random.randint(_min, _max)
        _op2 = random.randint(_min, _max)
        _opfunc = OPERATORS[random.randint(_opstart, _opend)]
        self.pending_answer = round(_opfunc[1](_op1, _op2), 2)
        self.question = f"{_op1} {_opfunc[0]} {_op2}"
        self.answered = False

        self.say(
            self.game_channel,
            (
                f'The Question is "{self.question}"\n'
                "Respond with: !game <answer> <color name or #xxxxxx>"
                "example:\n"
                "`!game 42 blue`\n"
                "`!game 33.33 #deadbe`\n"
                "(answer is rounded to 2 decimal places)"
            ),
        )
        self.generating = False

    @respond_to(r"^admin reset$", re.IGNORECASE)
    def admin_reset(self, msg):

        if self.admin_channel is None:
            self.admin_channel = msg.channel.id
            logger.warn(f"admin channel set to {self.admin_channel}\n{msg.channel}")

        if msg.channel.id != self.admin_channel:
            logger.warn(f"Unauthorized admin command")
            return

        logger.warn(f"Admin Channel Reset issued")
        self.generating = True
        self.game_channel = self.settings.get("GAME_CHANNEL", None)
        self.admin_channel = self.settings.get("ADMIN_CHANNEL", None)
        self.delay = int(self.settings.get("DEFAULT_DELAY", 30))
        self.question = self.settings.get("START_QUESTION", "We don't know")
        self.difficulty = int(self.settings.get("GAME_DIFFICULTY", 0))
        self.modulus = int(self.settings.get("DIFFICULTY_MODULUS", 5))
        self.pending_answer = float(self.settings.get("START_ANSWER", 0))
        self.answered = False
        self.answered_at = datetime.datetime.now()

        if self.game_channel:
            self.say(
                self.game_channel,
                (
                    f'The Question is "{self.question}"\n'
                    "Respond with: !game <answer> <color name or #xxxxxx>"
                    "example:\n"
                    "`!game 42 blue`\n"
                    "`!game 33.33 #deadbe`\n"
                ),
            )
        self.generating = False

    @respond_to(r"^admin delay (?P<delay>\d*)$", re.IGNORECASE)
    def admin_delay(self, msg, delay):

        if msg.channel.id != self.admin_channel:
            logger.warn(f"Unauthorized admin command")
            return

        try:
            _delay = int(delay)
        except ValueError as e:
            logger.error(f"Admin Channel - {e}")
            return

        logger.warn(f"Admin Channel - Delay {_delay}")
        self.delay = int(_delay)

    @respond_to(r"^admin diff (?P<difficulty>\d*)(?:.+)?$", re.IGNORECASE)
    def admin_difficulty(self, msg, difficulty):

        if msg.channel.id != self.admin_channel:
            logger.warn(f"Unauthorized admin command")
            return

        try:
            _diff = int(difficulty)
        except ValueError as e:
            logger.error(f"Admin Channel - {e}")
            return

        logger.warn(f"Admin Channel - Difficulty {_diff}")
        self.difficulty = int(_diff)

    @respond_to(r"^admin mod (?P<modulus>\d*)(?:.+)?$", re.IGNORECASE)
    def admin_modulus(self, msg, modulus):

        if msg.channel.id != self.admin_channel:
            logger.warn(f"Unauthorized admin command")
            return

        try:
            _mod = int(modulus)
        except ValueError as e:
            logger.error(f"Admin Channel - {e}")
            return

        logger.warn(f"Admin Channel - Modulus {_mod}")
        self.modulus = int(_mod)

    @respond_to(r"^admin status$", re.IGNORECASE)
    def admin_status(self, msg):

        if msg.channel.id != self.admin_channel:
            logger.warn(f"Unauthorized admin command")
            return

        msg.reply(f"```{self.__dict__}```")
