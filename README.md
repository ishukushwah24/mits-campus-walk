MITS Gwalior - Campus Walk 🏫 3D Engine

A custom 3D campus walkthrough of Madhav Institute of Technology & Science (MITS), Gwalior built from scratch using pure Python, Pygame, and NumPy—without using any traditional 3D graphics engines, GPU shaders, or external game development frameworks.

🌟 Key Features

Software Renderer: Built entirely with Python libraries (pygame and numpy) utilizing custom mathematical rendering techniques.

Painter's Algorithm Pipeline: Objects are rendered sequentially from back to front (Sky ➔ Floor ➔ Outer Trees ➔ Boundary Walls ➔ Building ➔ Inner Trees ➔ UI overlays).

Signed Distance Fields (SDF): Pre-baked math fields allow smooth, non-blocky road curves, kerbs, and continuous player collision detection.

Vectorized Floor Casting: NumPy maps 2D ground coordinates to screen pixels dynamically without slow Python loops.

Raycasting & Ray-Box Buildings: 300 vertical rays perform fisheye-corrected wall height calculations alongside accurate 4-story building facade box intersections.

Depth-Sorted Billboard Sprites: Trees face the camera dynamically and are sorted relative to building depth.

Interactive Minimap & HUD: Features live coordinate dots, field-of-view directional indicators, compass heading, and real-time FPS monitoring.

⚙️ Installation & Prerequisites

Prerequisites

Make sure you have Python 3.8+ installed on your system.

Dependencies

Install the required packages using pip:

pip install pygame numpy


🚀 How to Run

Run the main project file directly using Python:

python trypython.py


🎮 Controls

Key

Action

W / S or Up / Down

Walk Forward / Backward

A / D

Strafe Left / Right

Left / Right Arrows

Turn / Look Around

Shift

Hold to Run (Fast Movement)

ESC

Exit Application

📁 Technical Overview & Rendering Architecture

1. Sky Panorama (360° cloud & sun glow texture)
       │
2. Per-Pixel Floor Casting (Vectorized NumPy calculations)
       │
3. Outer Trees (Boundary background foliage)
       │
4. Raycasted Boundary Walls (Fisheye-corrected height arrays)
       │
5. Building & Inner Trees (Ray-box intersection & depth sorting)
       │
6. HUD Overlay (Vignette effect, Minimap, and Compass text)


Core Settings (trypython.py)

FLOOR_SCALE: Set to 2 by default for performance optimization (1 for maximum sharpness).

RAYS: 300 vertical ray columns cast across the screen width.

FOV: Field of View set to $\pi / 3$ ($60^\circ$).

STOREYS: Configured for a 4-story main campus building.

📜 License

This project is created for educational and demonstration purposes representing the MITS Gwalior campus layout.
