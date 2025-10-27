"""Remote control data model"""

from dataclasses import dataclass
from enum import Enum


class KeyCode(Enum):
    """Android key codes"""
    HOME = 3
    BACK = 4
    MENU = 82
    POWER = 26
    VOLUME_UP = 24
    VOLUME_DOWN = 25
    VOLUME_MUTE = 164
    
    # D-Pad (TV)
    DPAD_UP = 19
    DPAD_DOWN = 20
    DPAD_LEFT = 21
    DPAD_RIGHT = 22
    DPAD_CENTER = 23
    
    # Media controls
    PLAY_PAUSE = 85
    STOP = 86
    NEXT = 87
    PREVIOUS = 88
    
    # Special keys
    ENTER = 66
    DELETE = 67
    SPACE = 62


@dataclass
class TouchEvent:
    """Touch event data"""
    x: int
    y: int
    action: str  # 'tap', 'swipe_start', 'swipe_end'
