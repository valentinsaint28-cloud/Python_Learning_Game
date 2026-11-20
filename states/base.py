class State:
    """Base class: every state overrides what it needs."""

    # If True, the state below is still drawn underneath (dialogue boxes, menus...)
    transparent = False

    def __init__(self, game):
        self.game = game

    def enter(self):
        """Called when the state is added to the stack."""

    def exit(self):
        """Called when the state is removed from the stack."""

    def pause(self):
        """Called when another state is pushed on top of this one."""

    def resume(self):
        """Called when the state above is removed."""

    def handle_event(self, event):
        """Receive one pygame event (KEYDOWN, MOUSEBUTTONDOWN...)."""

    def update(self, dt):
        """dt = seconds since last frame."""

    def draw(self, screen):
        """Draw onto the screen."""
