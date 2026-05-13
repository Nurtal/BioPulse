"""End-to-end example: animate the IL-6 → JAK1 → STAT3 → SOCS3 cascade.

Run in a Jupyter notebook::

    from examples.play_cascade import widget
    widget   # displays the animation in the cell

Or load the widget manually::

    import biopulse
    from biopulse.io.json_loader import load_scene
    from pathlib import Path

    graph, events = load_scene(Path("examples/data/il6_stat3.scene.json"))
    biopulse.play(graph, events, speed=1.0)
"""

from pathlib import Path

import biopulse
from biopulse.io.json_loader import load_scene

_SCENE = Path(__file__).parent / "data" / "il6_stat3.scene.json"

graph, events = load_scene(_SCENE)

# speed=1.0 → real-time  |  autoplay=True → starts immediately
widget = biopulse.play(graph, events, speed=1.0, width=900, height=600)
