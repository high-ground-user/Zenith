# Zenith - Space Exploration & Escort Arcade

Welcome to **Zenith**, a fast-paced procedural space action game built using **Pygame-ce**. Fly through hostile asteroid belts, escort convoys, survive solar storms, and upgrade your vessel to defeat the final Citadel.

---

## 🚀 How to Launch the Game

We have provided bootstrap scripts to automatically handle dependencies and run the game:

### 🍏 macOS & Linux
Open your terminal in the game directory and run:
```bash
./run.sh
```

### 🪟 Windows
Double-click `run.bat` or run it from Command Prompt:
```cmd
run.bat
```

---

## 🎮 Game Controls

| Key / Input | Action |
| :--- | :--- |
| **Mouse Move** | Aim primary weapons & Rotate ship bank angle |
| **Left Click / Space** | Fire Primary Weapons (Laser, Shotgun, Railgun) |
| **Right Click** | Launch Heavy Torpedo (in combat zones) |
| **W / S** (or Up/Down) | Main Thrusters: Accelerate / Reverse |
| **A / D** (double-tap) | Evade Dash (Left / Right) |
| **Left Shift** | Deploy Countermeasure Flare (distracts homing missiles) |
| **Q** | Use Class Ability 1 (e.g., missiles, shield crystal) |
| **E** | Use Class Ability 2 (e.g., repair drone, cloaking shield) |
| **P / ESC** | Pause Game / Open Station Upgrades Shop (in Space Station Hub) |
| **F3** | Toggle Developer Panel (Cheat keys to skip zones, get credits) |

---

## 🛠️ Ship Classes

Choose from 5 specialized vessel configurations:
1. **Ranger** - Highly balanced vessel with reduced evade dash cooldowns.
2. **Engineer** - Slow passive shield regeneration; deploys auxiliary repair drones and defense nodes.
3. **Vanguard** - Heavy plating cruiser with maximum hull deflection shields. Ideal for bullet absorption.
4. **Sniper** - Long-range glass cannon armed with high-energy piercing railgun bolts.
5. **Assassin** - Deploys a cloaking drive that yields temporary invisibility and invulnerability.

---

## 💾 Local Save System

Zenith automatically handles saves locally:
* **Manual Save**: Press **P** or **ESC** in game to pause, and click the **[SAVE GAME]** button to save progress.
* **Autosave**: The game autosaves whenever you complete missions or finish upgrades in the Hub station.
* **Load Progress**: If a local save exists in the `saves/` directory, a **[CONTINUE]** button will be displayed next to **[NEW GAME]** on the Main Menu, allowing you to load your pilot callsign, level, credits, scraps, skills, and equipment.