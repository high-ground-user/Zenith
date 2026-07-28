"""
This is the main module for the space game.
It handles the overall structure and flow of the game.
"""

import pygame
import random
import sys
import math
import io
import wave
import struct



import os
import json
import zlib
import base64
import hashlib
import tkinter as tk

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
VIRTUAL_WIDTH = 1200
VIRTUAL_HEIGHT = 900
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (44, 44, 44)
GREEN = (0, 255, 0)
SLATE_GRAY = (80, 90, 100)
BLUE = (30, 144, 255)
ORANGE = (255, 140, 0)
GOLD = (255, 215, 0)
INDIGO = (75, 0, 130)
MAGENTA = (255, 0, 255)
PURPLE = (147, 112, 219)

SOUNDS = None

class SaveManager:
    SAVE_DIR = "saves"
    SAVE_FILE = os.path.join(SAVE_DIR, "save.json")
    
    @staticmethod
    def save_exists():
        return os.path.exists(SaveManager.SAVE_FILE)
        
    @staticmethod
    def write_save(game):
        try:
            if not os.path.exists(SaveManager.SAVE_DIR):
                os.makedirs(SaveManager.SAVE_DIR, exist_ok=True)
            p = game.player
            save_dict = {
                "v": 1,
                "name": game.player_name,
                "stage": game.campaign_stage,
                "class": p.class_name,
                "lvl": p.level,
                "xp": p.xp,
                "pts": p.skill_points,
                "creds": p.credits,
                "scraps": p.scraps,
                "wp_p": p.active_primary,
                "wp_s": p.active_secondary,
                "shld": p.equipped_shield,
                "core": p.equipped_core,
                "eng": p.equipped_engine,
                "skills": p.skills,
                "vol": int(SOUNDS.volume * 100) if SOUNDS else 50,
                "tint": game.filter_tint_alpha,
                "vignette": game.filter_vignette_alpha,
                "softness": game.filter_softness
            }
            with open(SaveManager.SAVE_FILE, 'w') as f:
                json.dump(save_dict, f, indent=4)
            return True, "Save successful"
        except Exception as e:
            return False, f"Save failed: {str(e)}"

    @staticmethod
    def load_save(game):
        try:
            if not os.path.exists(SaveManager.SAVE_FILE):
                return False, "No save file found"
                
            with open(SaveManager.SAVE_FILE, 'r') as f:
                save_dict = json.load(f)
                
            game.selected_class = save_dict["class"]
            game.reset_game()
            
            game.player_name = save_dict["name"]
            game.campaign_stage = save_dict["stage"]
            
            p = game.player
            p.name = game.player_name
            p.set_class(game.selected_class)
            p.level = save_dict["lvl"]
            p.xp = save_dict["xp"]
            p.skill_points = save_dict["pts"]
            p.credits = save_dict["creds"]
            p.scraps = save_dict["scraps"]
            p.active_primary = save_dict["wp_p"]
            p.active_secondary = save_dict["wp_s"]
            p.equipped_shield = save_dict["shld"]
            p.equipped_core = save_dict["core"]
            p.equipped_engine = save_dict["eng"]
            p.skills.update(save_dict["skills"])
            
            if SOUNDS and "vol" in save_dict:
                SOUNDS.set_global_volume(save_dict["vol"] / 100.0)
            game.filter_tint_alpha = save_dict.get("tint", 50)
            game.filter_vignette_alpha = save_dict.get("vignette", 100)
            game.filter_softness = save_dict.get("softness", 15)
            
            game.active_quest = game.quests[min(len(game.quests)-1, game.campaign_stage - 1)]
            game.unlocked_zones = {
                'TUTORIAL': True,
                'ASTEROIDS': True, 
                'VULCAN': game.campaign_stage >= 2, 
                'AQUARIS': game.campaign_stage >= 2,
                'NEBULA': game.campaign_stage >= 2, 
                'PLASMA': game.campaign_stage >= 2, 
                'VOID': game.campaign_stage >= 2,
                'QUANTUM': game.campaign_stage >= 2, 
                'SINGULARITY': game.campaign_stage >= 2, 
                'ORION': game.campaign_stage >= 3
            }
            game.current_hub_index = 3 if game.campaign_stage >= 3 else (2 if game.campaign_stage >= 2 else 1)
            
            game.state = 'HUB'
            game.current_zone = 'HUB'
            return True, "Loaded successfully"
        except Exception as e:
            return False, f"Load failed: {str(e)}"

#### player.py

class SoundManager:
    def __init__(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.enabled = True
            self.volume = 0.5
        except Exception:
            self.enabled = False
            return

        self.sounds = {}
        # Create external sounds folder if not exists
        if not os.path.exists(os.path.join("assets", "sounds")):
            try:
                os.makedirs(os.path.join("assets", "sounds"), exist_ok=True)
            except Exception:
                pass

        # Generate basic retro sounds in memory (or load custom ones if available)
        self.sounds['laser'] = self._load_or_synth('laser', 'triangle', 660, 0.12, vol=0.12, sweep=-0.6, decay=4.0)
        self.sounds['shotgun'] = self._load_or_synth('shotgun', 'noise', 80, 0.25, vol=0.25, sweep=-0.2, decay=5.0)
        self.sounds['railgun'] = self._load_or_synth('railgun', 'sine', 180, 0.35, vol=0.22, sweep=-0.4, decay=3.0)
        self.sounds['explosion'] = self._load_or_synth('explosion', 'noise', 40, 0.5, vol=0.35, sweep=-0.4, decay=2.5)
        self.sounds['siren'] = self._load_or_synth('siren', 'sine', 500, 0.4, vol=0.15, sweep=0.1, decay=2.0)
        self.sounds['hit'] = self._load_or_synth('hit', 'noise', 120, 0.08, vol=0.2, sweep=-0.2, decay=6.0)
        self.sounds['collect'] = self._load_or_synth('collect', 'sine', 950, 0.15, vol=0.15, sweep=0.4, decay=4.5)
        self.sounds['launch'] = self._load_or_synth('launch', 'noise', 100, 0.3, vol=0.2, sweep=-0.4, decay=4.0)
        self.sounds['warp'] = self._load_or_synth('warp', 'sine', 150, 1.2, vol=0.3, sweep=1.0, decay=1.5)
        self.sounds['shield_down'] = self._load_or_synth('shield_down', 'sine', 200, 0.4, vol=0.30, sweep=-0.8, decay=2.0)
        self.sounds['shield_recharge'] = self._load_or_synth('shield_recharge', 'sine', 350, 0.8, vol=0.15, sweep=0.2, decay=1.0)
        self.sounds['crash'] = self._load_or_synth('crash', 'noise', 70, 0.35, vol=0.35, sweep=-0.4, decay=2.5)
        self.sounds['metal_hit'] = self._load_or_synth('metal_hit', 'triangle', 1200, 0.06, vol=0.15, sweep=-0.9, decay=8.0)
        self.sounds['engine'] = self._load_or_synth('engine', 'sine', 80, 0.25, vol=0.15, sweep=0.0, decay=1.0)
        self.sounds['tick'] = self._load_or_synth('tick', 'sine', 1500, 0.03, vol=0.08, sweep=-0.8, decay=10.0)
        
        self.sounds['victory'] = self._load_victory_or_synth()
        
        self.music_ambient = None
        self.music_boss = None
        
        self.chan_ambient = None
        self.chan_boss = None

        self.set_global_volume(self.volume)

    def _load_or_synth(self, name, wave_type, freq, duration, vol=0.5, sweep=0.0, decay=3.0):
        path = os.path.join("assets", "sounds", f"{name}.wav")
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(vol)
                return sound
            except Exception:
                pass
        return self._gen_synth(wave_type, freq, duration, vol, sweep, decay)

    def _load_victory_or_synth(self):
        path = os.path.join("assets", "sounds", "victory.wav")
        if os.path.exists(path):
            try:
                return pygame.mixer.Sound(path)
            except Exception:
                pass
        return self._gen_victory_fanfare()

    def _load_music_or_synth(self, filename, music_type):
        for ext in ('.ogg', '.wav', '.mp3'):
            path = os.path.join("assets", "sounds", f"{filename}{ext}")
            if os.path.exists(path):
                try:
                    return pygame.mixer.Sound(path)
                except Exception:
                    pass
        if music_type == 'ambient':
            return self._gen_ambient_music()
        else:
            return self._gen_boss_music()

    def set_global_volume(self, volume):
        if not self.enabled: return
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)

    def _gen_synth(self, wave_type, freq, duration, vol=0.5, sweep=0.0, decay=3.0):
        if not self.enabled: return None
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        buf = io.BytesIO()
        try:
            with wave.open(buf, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                
                data = bytearray()
                noise_state = 0.0
                for i in range(num_samples):
                    t = float(i) / sample_rate
                    current_freq = freq * (1.0 + sweep * (i / num_samples))
                    
                    if wave_type == 'square':
                        v1 = 1.0 if math.sin(2 * math.pi * current_freq * t) > 0 else -1.0
                        v2 = 1.0 if math.sin(2 * math.pi * current_freq * 1.015 * t) > 0 else -1.0
                        val = (v1 + v2) * 0.5
                    elif wave_type == 'triangle':
                        cycle1 = current_freq * t
                        cycle2 = current_freq * 1.015 * t
                        v1 = 2.0 * abs(2.0 * (cycle1 - math.floor(cycle1 + 0.5))) - 1.0
                        v2 = 2.0 * abs(2.0 * (cycle2 - math.floor(cycle2 + 0.5))) - 1.0
                        val = (v1 + v2) * 0.5
                    elif wave_type == 'sawtooth':
                        cycle1 = current_freq * t
                        cycle2 = current_freq * 1.015 * t
                        v1 = 2.0 * (cycle1 - math.floor(cycle1 + 0.5))
                        v2 = 2.0 * (cycle2 - math.floor(cycle2 + 0.5))
                        val = (v1 + v2) * 0.5
                    elif wave_type == 'noise':
                        raw_noise = random.uniform(-1.0, 1.0)
                        noise_state = 0.85 * noise_state + 0.15 * raw_noise
                        val = noise_state * 3.5
                    else: # sine
                        v1 = math.sin(2 * math.pi * current_freq * t)
                        v2 = math.sin(2 * math.pi * current_freq * 1.015 * t)
                        val = (v1 + v2) * 0.5
                        
                    fade_in = min(1.0, float(i) / 100.0)
                    envelope = fade_in * math.exp(-decay * (i / num_samples)) * (1.0 - i / num_samples)
                    sample = int(val * vol * envelope * 32767)
                    sample = max(-32768, min(32767, sample))
                    data += struct.pack('<h', sample)
                wav.writeframes(data)
            buf.seek(0)
            return pygame.mixer.Sound(buf)
        except Exception:
            return None

    def play(self, name):
        if name in ('warp', 'victory'): return
        if self.enabled and name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def play_spatial(self, name, source_x, source_y, player_x, player_y):
        if name in ('warp', 'victory'): return
        if not self.enabled: return
        if name not in self.sounds or not self.sounds[name]: return
        
        dx = source_x - player_x
        dy = source_y - player_y
        dist = math.sqrt(dx**2 + dy**2)
        
        vol_mult = max(0.0, min(1.0, 1.0 - (dist / 1500.0)))
        pan = max(-1.0, min(1.0, dx / 600.0))
        
        left_vol = self.volume * vol_mult * (1.0 - max(0.0, pan))
        right_vol = self.volume * vol_mult * (1.0 - max(0.0, -pan))
        
        channel = self.sounds[name].play()
        if channel:
            channel.set_volume(left_vol, right_vol)

    def _gen_ambient_music(self):
        sample_rate = 22050
        duration = 32.0
        num_samples = int(sample_rate * duration)
        buf = io.BytesIO()
        try:
            with wave.open(buf, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                data = bytearray()
                
                # Dynamic 8-chord progression (Space Opera ambient theme)
                chords = [
                    [164.81, 196.00, 246.94, 329.63], # Em (E3, G3, B3, E4)
                    [130.81, 164.81, 196.00, 246.94], # Cmaj7 (C3, E3, G3, B3)
                    [110.00, 146.83, 174.61, 220.00], # Am9 (A2, D3, F3, A3)
                    [146.83, 185.00, 220.00, 246.94], # D6 (D3, F#3, A3, B3)
                    [164.81, 196.00, 246.94, 329.63], # Em
                    [196.00, 246.94, 293.66, 392.00], # G
                    [130.81, 164.81, 196.00, 261.63], # C
                    [123.47, 164.81, 185.00, 246.94]  # B7
                ]
                roots = [82.41, 65.41, 55.00, 73.42, 82.41, 98.00, 65.41, 61.74]
                
                # Echoing cinematic piano motif (longer structural layout)
                piano_notes = [
                    (0.0, 659.25), (0.75, 783.99), (1.5, 739.99), (2.25, 587.33),
                    (4.0, 659.25), (4.75, 523.25), (5.5, 587.33), (6.25, 493.88),
                    (8.0, 440.00), (8.75, 523.25), (9.5, 587.33), (10.25, 659.25),
                    (12.0, 587.33), (12.75, 739.99), (13.5, 659.25), (14.25, 493.88),
                    (16.0, 659.25), (16.75, 783.99), (17.5, 880.00), (18.25, 987.77),
                    (20.0, 1046.50), (20.75, 987.77), (21.5, 880.00), (22.25, 783.99),
                    (24.0, 783.99), (24.75, 659.25), (25.5, 739.99), (26.25, 587.33),
                    (28.0, 587.33), (28.75, 493.88), (29.5, 523.25), (30.25, 440.00)
                ]
                
                for i in range(num_samples):
                    t = float(i) / sample_rate
                    chord_idx = int((t / 4.0)) % len(chords)
                    notes = chords[chord_idx]
                    
                    # 1. Detuned Choral Choir Pad
                    pad_val = 0.0
                    for freq in notes:
                        osc1 = math.sin(2 * math.pi * freq * t)
                        osc2 = math.sin(2 * math.pi * freq * 1.005 * t)
                        osc3 = math.sin(2 * math.pi * freq * 0.995 * t)
                        lfo = 0.4 + 0.15 * math.sin(2 * math.pi * 0.25 * t)
                        pad_val += (osc1 + osc2 + osc3) * 0.33 * lfo
                    pad_val /= len(notes)
                    
                    # 2. Rich Low Bass Drone (sub-frequency warm sine)
                    bass_val = math.sin(2 * math.pi * roots[chord_idx] * t) * 0.45
                    
                    # 3. Echoing Piano Motif (with secondary decay sweep)
                    piano_val = 0.0
                    for start_t, freq in piano_notes:
                        if t >= start_t and t < start_t + 1.5:
                            note_t = t - start_t
                            env = math.exp(-3.5 * note_t) * (1.0 - note_t / 1.5)
                            piano_val += (math.sin(2 * math.pi * freq * note_t) * 0.70 + 
                                          math.sin(2 * math.pi * freq * 2.0 * note_t) * 0.20 +
                                          math.sin(2 * math.pi * freq * 3.0 * note_t) * 0.10) * env
                    
                    total_val = (pad_val * 0.40 + bass_val * 0.35 + piano_val * 0.25)
                    sample = int(total_val * 0.16 * 32767)
                    sample = max(-32768, min(32767, sample))
                    data += struct.pack('<h', sample)
                wav.writeframes(data)
            buf.seek(0)
            return pygame.mixer.Sound(buf)
        except Exception:
            return None

    def _gen_boss_music(self):
        sample_rate = 22050
        duration = 18.0
        num_samples = int(sample_rate * duration)
        buf = io.BytesIO()
        try:
            with wave.open(buf, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                data = bytearray()
                
                # E-minor driving bass gallop sequence
                bass_notes = [82.41, 82.41, 98.00, 82.41, 82.41, 110.00, 82.41, 82.41]
                
                # Epic brass horns melody sweep (full verse layout)
                brass_notes = [
                    (0.0, 329.63), (0.45, 329.63), (0.9, 392.00), (1.35, 392.00),
                    (1.8, 440.00), (2.25, 440.00), (2.7, 493.88), (3.6, 392.00),
                    (4.05, 440.00), (4.5, 329.63),
                    
                    (5.4, 440.00), (5.85, 440.00), (6.3, 493.88), (6.75, 493.88),
                    (7.2, 523.25), (7.65, 587.33), (8.1, 493.88), (9.0, 523.25),
                    
                    (9.9, 659.25), (10.35, 659.25), (10.8, 783.99), (11.25, 783.99),
                    (11.7, 880.00), (12.15, 880.00), (12.6, 987.77), (13.5, 783.99),
                    (13.95, 880.00), (14.4, 659.25),
                    
                    (15.3, 880.00), (15.75, 880.00), (16.2, 783.99), (16.65, 739.99),
                    (17.1, 659.25)
                ]
                
                for i in range(num_samples):
                    t = float(i) / sample_rate
                    
                    # 1. Driving Bass Gallop (dynamic E-minor groove)
                    bass_step = int(t / 0.18) % len(bass_notes)
                    base_freq = bass_notes[bass_step]
                    bass_t = t % 0.18
                    bass_env = (1.0 - bass_t / 0.18) ** 1.6
                    cycle = base_freq * t
                    bass_val = 2.0 * abs(2.0 * (cycle - math.floor(cycle + 0.5))) - 1.0
                    bass_val = bass_val * bass_env * 0.6
                    
                    # 2. Epic detuned Sawtooth Brass Horn Sweep
                    brass_val = 0.0
                    for start_t, freq in brass_notes:
                        if t >= start_t and t < start_t + 1.2:
                            note_t = t - start_t
                            env = (1.0 - math.exp(-8.0 * note_t)) * math.exp(-2.0 * note_t) * (1.0 - note_t / 1.2)
                            c1 = freq * note_t
                            c2 = freq * 1.008 * note_t
                            v1 = 2.0 * (c1 - math.floor(c1 + 0.5))
                            v2 = 2.0 * (c2 - math.floor(c2 + 0.5))
                            brass_val += (v1 + v2) * 0.5 * env
                    
                    # 3. Dynamic Percussion: Orchestral Kicks & Military Snare Rolls
                    drum_val = 0.0
                    kick_t = t % 0.72
                    if kick_t < 0.18:
                        kick_freq = 130 - (kick_t / 0.18) * 90
                        kick_env = (1.0 - kick_t / 0.18) ** 2.0
                        drum_val += math.sin(2 * math.pi * kick_freq * kick_t) * kick_env * 0.95
                    
                    beat_step = int(t / 0.09) % 16
                    if beat_step in (2, 3, 6, 7, 10, 11, 13, 14, 15):
                        snare_t = t % 0.09
                        snare_env = 1.0 - snare_t / 0.09
                        noise_sample = random.uniform(-1.0, 1.0)
                        drum_val += (noise_sample * 0.75 + math.sin(2 * math.pi * 170 * snare_t) * 0.25) * snare_env * 0.35
                    
                    # Synthesize high-frequency crash cymbal on chord boundary shifts (every 4.5s)
                    crash_t = t % 4.5
                    if crash_t < 0.8:
                        crash_env = math.exp(-4.0 * crash_t) * (1.0 - crash_t / 0.8)
                        drum_val += random.uniform(-1.0, 1.0) * crash_env * 0.30
                    
                    # High Choir pad drone to build final-phase tension
                    choir_val = 0.0
                    if t > 9.0:
                        lfo = 0.5 + 0.2 * math.sin(2 * math.pi * 0.5 * t)
                        choir_val = math.sin(2 * math.pi * 659.25 * t) * lfo * 0.2
                    
                    total_val = (bass_val * 0.28 + brass_val * 0.36 + drum_val * 0.28 + choir_val * 0.08)
                    sample = int(total_val * 0.18 * 32767)
                    sample = max(-32768, min(32767, sample))
                    data += struct.pack('<h', sample)
                wav.writeframes(data)
            buf.seek(0)
            return pygame.mixer.Sound(buf)
        except Exception:
            return None

    def _gen_victory_fanfare(self):
        if not self.enabled: return None
        sample_rate = 22050
        duration = 3.0
        num_samples = int(sample_rate * duration)
        buf = io.BytesIO()
        try:
            with wave.open(buf, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                data = bytearray()
                
                notes = [261.63, 329.63, 392.00, 523.25]
                for i in range(num_samples):
                    t = float(i) / sample_rate
                    note_idx = min(3, int(t / 0.4))
                    freq = notes[note_idx]
                    
                    vib = 1.0 + 0.02 * math.sin(2 * math.pi * 6 * t)
                    osc1 = math.sin(2 * math.pi * freq * vib * t)
                    osc2 = math.sin(2 * math.pi * freq * vib * 1.01 * t)
                    val = (osc1 + osc2) * 0.5
                    
                    env = 1.0 - t / duration
                    sample = int(val * 0.25 * env * 32767)
                    sample = max(-32768, min(32767, sample))
                    data += struct.pack('<h', sample)
                wav.writeframes(data)
            buf.seek(0)
            return pygame.mixer.Sound(buf)
        except Exception:
            return None

    def update_music(self, wants_boss):
        if not self.enabled: return
        
        # Start loops if not running
        if self.chan_ambient is None and self.music_ambient:
            self.chan_ambient = self.music_ambient.play(loops=-1)
        if self.chan_boss is None and self.music_boss:
            self.chan_boss = self.music_boss.play(loops=-1)
            if self.chan_boss: self.chan_boss.set_volume(0.0)
            
        target_ambient = self.volume * 0.5 if not wants_boss else 0.0
        target_boss = self.volume * 0.7 if wants_boss else 0.0
        
        if self.chan_ambient:
            cur_vol = self.chan_ambient.get_volume()
            self.chan_ambient.set_volume(cur_vol + (target_ambient - cur_vol) * 0.05)
        if self.chan_boss:
            cur_vol = self.chan_boss.get_volume()
            self.chan_boss.set_volume(cur_vol + (target_boss - cur_vol) * 0.05)

class Quest:
    def __init__(self, key, title, description, target, reward_credits, reward_xp):
        self.key = key
        self.title = title
        self.description = description
        self.target = target
        self.progress = 0
        self.completed = False
        self.reward_credits = reward_credits
        self.reward_xp = reward_xp

    def is_complete(self):
        return self.progress >= self.target

class LootPickup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        self.rarity = random.choice(['COMMON', 'UNCOMMON', 'RARE'])
        self.effects = {
            'COMMON': [('shield', 1)],
            'UNCOMMON': [('cooldown', 0.05)],
            'RARE': [('damage', 0.15)]
        }[self.rarity]
        self.color = {'COMMON': (100, 200, 255), 'UNCOMMON': (255, 215, 0), 'RARE': (255, 80, 255)}[self.rarity]

    def update(self):
        self.y -= 0.3
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        pulse = int(2 * math.sin(ticks * 0.02))
        
        if self.rarity == 'COMMON':
            # Rotating Octagon wireframe with crosshairs (Common / Shield)
            num_sides = 8
            r = self.radius + pulse
            points = []
            for i in range(num_sides):
                ang = math.radians(i * 45 + ticks * 0.06)
                px = draw_x + int(r * math.cos(ang))
                py = draw_y + int(r * math.sin(ang))
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points, width=1)
            pygame.draw.line(screen, WHITE, (draw_x - r, draw_y), (draw_x + r, draw_y), 1)
            pygame.draw.line(screen, WHITE, (draw_x, draw_y - r), (draw_x, draw_y + r), 1)
            
        elif self.rarity == 'UNCOMMON':
            # Rotating Triangle wireframe (Uncommon / Cooldown)
            num_sides = 3
            r = self.radius + pulse + 2
            points = []
            for i in range(num_sides):
                ang = math.radians(i * 120 + ticks * 0.06)
                px = draw_x + int(r * math.cos(ang))
                py = draw_y + int(r * math.sin(ang))
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points, width=1)
            
            # Inner smaller counter-rotating triangle
            points_in = []
            r_in = max(2, self.radius - 3 - pulse)
            for i in range(num_sides):
                ang = math.radians(i * 120 - ticks * 0.09)
                px = draw_x + int(r_in * math.cos(ang))
                py = draw_y + int(r_in * math.sin(ang))
                points_in.append((px, py))
            pygame.draw.polygon(screen, WHITE, points_in, width=1)
            
        else:
            # Rotating 4-pointed Star wireframe (Rare / Damage)
            r_outer = self.radius + pulse + 3
            r_inner = (self.radius + pulse) // 2
            points = []
            for i in range(8):
                ang = math.radians(i * 45 + ticks * 0.08)
                r = r_outer if i % 2 == 0 else r_inner
                px = draw_x + int(r * math.cos(ang))
                py = draw_y + int(r * math.sin(ang))
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points, width=1)
            
            # Inner rotating diamond
            points_in = []
            r_in = max(2, self.radius - 4 - pulse)
            for i in range(4):
                ang = math.radians(i * 90 - ticks * 0.12)
                px = draw_x + int(r_in * math.cos(ang))
                py = draw_y + int(r_in * math.sin(ang))
                points_in.append((px, py))
            pygame.draw.polygon(screen, WHITE, points_in, width=1)

BIOME_CONFIGS = {
    'TUTORIAL': {'name': 'Training Range', 'theme_color': GREEN, 'desc': 'No-Damage Practice', 'stars_color': GREEN, 'hub': 1, 'order': 3, 'boss_count': 0},
    'ASTEROIDS': {'name': 'Asteroid Belt', 'theme_color': GRAY, 'desc': 'Heavy Meteor Shower', 'stars_color': GRAY, 'hub': 1, 'order': 0, 'boss_count': 0},
    'VULCAN': {'name': 'Vulcan Sector', 'theme_color': ORANGE, 'desc': 'Hyper Fast Speed', 'stars_color': ORANGE, 'hub': 1, 'order': 1, 'boss_count': 0},
    'AQUARIS': {'name': 'Aquaris Nebula', 'theme_color': CYAN, 'desc': 'Armored Ice Fields', 'stars_color': CYAN, 'hub': 1, 'order': 2, 'boss_count': 0},
    
    'NEBULA': {'name': 'Nebula Storm', 'theme_color': PURPLE, 'desc': 'Electrical Storms', 'stars_color': PURPLE, 'hub': 2, 'order': 0, 'boss_count': 2},
    'PLASMA': {'name': 'Plasma Core', 'theme_color': GOLD, 'desc': 'High-Energy Currents', 'stars_color': GOLD, 'hub': 2, 'order': 1, 'boss_count': 0},
    'SINGULARITY': {'name': 'Singularity Factory', 'theme_color': BLUE, 'desc': 'Reactor Meltdown', 'stars_color': BLUE, 'hub': 2, 'order': 2, 'boss_count': 1},
    
    'QUANTUM': {'name': 'Quantum Rift', 'theme_color': GREEN, 'desc': 'Stabilizer Demolition', 'stars_color': GREEN, 'hub': 3, 'order': 0, 'boss_count': 0},
    'VOID': {'name': 'Void Chasm', 'theme_color': INDIGO, 'desc': 'Zero-Gravity Abyss', 'stars_color': INDIGO, 'hub': 3, 'order': 1, 'boss_count': 0},
    'ORION': {'name': 'Orion Citadel', 'theme_color': MAGENTA, 'desc': 'Overlord Fortress', 'stars_color': MAGENTA, 'hub': 3, 'order': 2, 'boss_count': 3}
}

NPC_INFO = {
    'ENGINEERING': {
        'name': 'Chief Sparks',
        'color': GOLD,
        'title': 'CHIEF ENGINEER',
        'dialogue': {
            1: [
                "Ah, Captain {name}! We need 5 Matrix Cores from the Asteroid Belt to jump-start the main Safe Haven reactor.",
                "Docking stabilizers locked. The engines on your {class_name} are running a bit hot, Captain. Try to pulse your thrust in the field.",
                "Watch out for gravity wells in the Asteroids, Captain {name}. Keep your speed up or they will drag you in!"
            ],
            2: [
                "Captain {name}, the Singularity Factory reactor is melting down! We need you to infiltrate the core and shut it down.",
                "Your {class_name} ship has a compact signature. Perfect for squeezing through those tight corridor grids in the Factory.",
                "Be careful of those indestructible space station walls, Captain. One bad crash will eat through your shields instantly!"
            ],
            3: [
                "We're ready for the final jump, Captain {name}. The Orion Citadel is straight ahead. Let's make it count!",
                "I've pushed the reactor output to maximum. If your {class_name}'s systems hold, you'll have all the juice you need.",
                "Chief Vance tells me the Citadel is protected by triple shielding. Knock out the generator ships first!"
            ]
        }
    },
    'WEAPONRY': {
        'name': 'Officer Vance',
        'color': RED,
        'title': 'WEAPONS OFFICER',
        'dialogue': {
            1: [
                "Warp coordinates are locked to the Asteroid Belt. Be careful out there, Captain {name}.",
                "As a {class_name}, you'll want to lean into your tactical ability. Ranger overdrive or Sniper airstrikes can save you when surrounded.",
                "Primary lasers run on a capacitor. Watch your heat gauge at the top left, Captain! Don't overheat in a firefight."
            ],
            2: [
                "This is a tight space station infiltration. Corridors are narrow, watch for turrets, and get to the center!",
                "Dax just stocked our weapon modifiers in the depot. If you have the credits, I highly recommend the Split Shot or Piercing Laser upgrades.",
                "The factory defenses are heavily armored, Captain {name}. If you use secondary weapons, space out your torpedoes for maximum splash impact."
            ],
            3: [
                "The Overlord's fleet is massive, but we believe in you, Captain {name}. Destroy the Citadel Boss!",
                "Officer Vance reporting. Weapons caliber checked. Your {class_name}'s loadout is cleared for deployment. Strike hard!",
                "Remember, Captain: the Overlord's bullets are fast, but your thrusters are faster. Use dash maneuvers to glide through the bullet patterns."
            ]
        }
    },
    'SUPPLY': {
        'name': 'Quartermaster Dax',
        'color': CYAN,
        'title': 'SUPPLY QUARTERMASTER',
        'dialogue': {
            1: [
                "Keep an eye out for scrap debris. We can trade scrap for ship upgrades once you are back.",
                "Need resources, Captain {name}? I've got primary weapon refills and shields ready. Don't go out with an empty clip.",
                "Welcome to the depot. A {class_name} like you should look into boosting maximum shields early on."
            ],
            2: [
                "We've unlocked the Singularity Factory portal. Safe flying, Captain {name}!",
                "Those weapon modifiers are selling out fast. Piercing lasers are great for clearing rows of enemies, and Shield Siphon keeps your shields charged.",
                "Got enough credits, Captain? Don't forget to stock up on flares before warp. They redirect incoming homing missiles."
            ],
            3: [
                "All systems upgraded. This is the final showdown. Bring us home, Captain {name}!",
                "Credits are useless if the Citadel destroys us. Spend everything you've got on refills and active mods now.",
                "I've prepped the cargo bays for our escape. Make sure you make it back in one piece, Captain {name}."
            ]
        }
    }
}


class Bullet:
    def __init__(self, x, y, dx, dy, speed=19.8, life=100, piercing=False, damage=1.0, color=(255, 255, 0)):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.width = 16
        self.height = 16
        self.rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        self.target = None
        self.life = life
        self.piercing = piercing
        self.damage = damage
        self.color = color

    def find_target(self, enemies, meteors, static_obstacles):
        closest_target = None
        min_dist = 300.0
        bullet_pos = pygame.math.Vector2(self.x, self.y)
        bullet_dir = pygame.math.Vector2(self.dx, self.dy).normalize()
        
        for entity in enemies + meteors + static_obstacles:
            entity_center = pygame.math.Vector2(entity.rect.center)
            to_entity = entity_center - bullet_pos
            dist = to_entity.length()
            if dist < min_dist:
                angle = bullet_dir.angle_to(to_entity)
                if abs(angle) < 12.0:  # Narrow field of view for aim assist
                    min_dist = dist
                    closest_target = entity
        self.target = closest_target

    def update(self):
        if self.target and hasattr(self.target, 'rect') and self.target.rect.y < self.y + 100:
            target_center = pygame.math.Vector2(self.target.rect.center)
            bullet_pos = pygame.math.Vector2(self.x, self.y)
            desired_dir = (target_center - bullet_pos).normalize()
            current_dir = pygame.math.Vector2(self.dx, self.dy)
            # Extremely subtle lerp (0.08 -> 0.015) so it barely curves toward targets
            steered_dir = current_dir.lerp(desired_dir, 0.015).normalize()
            self.dx = steered_dir.x
            self.dy = steered_dir.y

        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.rect.x = int(self.x - self.width // 2)
        self.rect.y = int(self.y - self.height // 2)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        start_pt = (int(draw_x - self.dx * 8), int(draw_y - self.dy * 8))
        end_pt = (int(draw_x + self.dx * 4), int(draw_y + self.dy * 4))
        pygame.draw.line(screen, self.color, start_pt, end_pt, width=6)
        pygame.draw.line(screen, (255, 255, 255), start_pt, end_pt, width=2)

class Torpedo:
    def __init__(self, x, y, dx, dy, scale=1.0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 16.5
        self.radius = int(8 * scale)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        self.exploded = False
        self.explosion_radius = int(120 * scale)
        self.explosion_duration = 30
        self.explosion_timer = 0
        self.angle = 0
        self.is_sub = False

    def update(self):
        if not self.exploded:
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed
            self.rect.center = (int(self.x), int(self.y))
        else:
            self.explosion_timer += 1

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        if not self.exploded:
            ticks = pygame.time.get_ticks()
            self.angle = math.degrees(math.atan2(self.dy, self.dx))
            # Use a simpler drawing for torpedo body to save resources
            f_pulse = 4 + int(3 * math.sin(ticks * 0.05))
            body_surf = pygame.Surface((30, 16), pygame.SRCALPHA)
            pygame.draw.rect(body_surf, (100, 100, 110), (0, 2, 22, 12), border_radius=2)
            pygame.draw.polygon(body_surf, ORANGE, [(22, 0), (30, 8), (22, 16)])
            pygame.draw.circle(body_surf, (255, 200, 0), (2, 8), f_pulse)
            rot_body = pygame.transform.rotate(body_surf, -self.angle)
            screen.blit(rot_body, (int(draw_x - rot_body.get_width()//2), int(draw_y - rot_body.get_height()//2)))
        else:
            progress = self.explosion_timer / self.explosion_duration
            current_radius = int(self.explosion_radius * progress)
            surf = pygame.Surface((current_radius * 2, current_radius * 2), pygame.SRCALPHA)
            alpha = int(200 * (1 - progress))
            pygame.draw.circle(surf, (255, 69, 0, alpha), (current_radius, current_radius), current_radius)
            pygame.draw.circle(surf, (255, 215, 0, int(alpha * 0.7)), (current_radius, current_radius), int(current_radius * 0.7))
            pygame.draw.circle(surf, (255, 255, 255, int(alpha * 0.4)), (current_radius, current_radius), int(current_radius * 0.4))
            screen.blit(surf, (int(draw_x) - current_radius, int(draw_y) - current_radius))

class ProxBomb:
    def __init__(self, x, y, dx, dy, scale=1.0):
        self.x = x
        self.y = y
        self.dx = dx * 0.15
        self.dy = dy * 0.15
        self.width = 24
        self.height = 24
        self.rect = pygame.Rect(self.x - 12, self.y - 12, self.width, self.height)
        self.exploded = False
        self.explosion_timer = 0
        self.explosion_duration = 30
        self.explosion_radius = int(160 * scale)
        
    def update(self):
        if self.exploded:
            self.explosion_timer += 1
            return
        self.x += self.dx
        self.y += self.dy
        self.rect.x = int(self.x - 12)
        self.rect.y = int(self.y - 12)
        
    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        if self.exploded:
            progress = self.explosion_timer / self.explosion_duration
            # Avoid per-frame surface creation for explosions
            r = int(self.explosion_radius * progress)
            if r > 0:
                alpha = int(220 * (1.0 - progress))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 69, 0, alpha // 2), (r, r), r)
                pygame.draw.circle(s, (255, 140, 0, alpha), (r, r), r, width=3)
                screen.blit(s, (int(draw_x - r), int(draw_y - r)))
        else:
            ticks = pygame.time.get_ticks()
            pulse = int(3 * math.sin(ticks * 0.015))
            # Draw spiky mine look
            for i in range(8):
                ang = math.radians(i * 45 + ticks * 0.1)
                p1 = (int(draw_x + 6 * math.cos(ang)), int(draw_y + 6 * math.sin(ang)))
                p2 = (int(draw_x + (14 + pulse) * math.cos(ang)), int(draw_y + (14 + pulse) * math.sin(ang)))
                pygame.draw.line(screen, GRAY, p1, p2, width=3)
            pygame.draw.circle(screen, (40, 40, 45), (int(draw_x), int(draw_y)), 10)
            pygame.draw.circle(screen, RED if ticks % 400 < 200 else (60, 0, 0), (int(draw_x), int(draw_y)), 6)

class HomingMissile:
    def __init__(self, x, y, dx, dy, scale=1.0, shooter=None, converge_pos=None):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 11.0
        self.width = 16
        self.height = 16
        self.rect = pygame.Rect(self.x - 8, self.y - 8, self.width, self.height)
        self.exploded = False
        self.explosion_timer = 0
        self.explosion_duration = 20
        self.explosion_radius = int(90 * scale)
        self.target = None
        self.shooter = shooter
        self.converge_pos = converge_pos
        
    def update(self, enemies, camera_y, flares=None):
        if self.exploded:
            self.explosion_timer += 1
            return
            
        # Travel to convergence point if one is set (e.g. travel to player first)
        if self.converge_pos:
            dist = pygame.math.Vector2(self.x, self.y).distance_to(self.converge_pos)
            if dist < 40:
                self.converge_pos = None # Target reached, start tracking
            else:
                desired = (self.converge_pos - pygame.math.Vector2(self.x, self.y)).normalize()
                current = pygame.math.Vector2(self.dx, self.dy)
                steer = current.lerp(desired, 0.1).normalize()
                self.dx = steer.x
                self.dy = steer.y

        # Delete homing missile if shooter is dead
        if self.shooter:
            shooter_dead = getattr(self.shooter, 'is_dead', False)
            if hasattr(self.shooter, 'life') and self.shooter.life <= 0:
                shooter_dead = True
            if shooter_dead:
                self.exploded = True
                self.explosion_timer = self.explosion_duration
                return
            
        # Target tracking
        if not self.converge_pos and (not self.target or self.target.health <= 0):
            closest = None
            min_d = 800.0
            # Player missiles only target enemies, not flares
            for ent in enemies:
                if ent.health > 0:
                    d = pygame.math.Vector2(self.x, self.y).distance_to(pygame.math.Vector2(ent.x, ent.y))
                    if d < min_d:
                        min_d = d
                        closest = ent
            self.target = closest
            
        if not self.converge_pos and self.target:
            target_pos = pygame.math.Vector2(self.target.rect.center)
            missile_pos = pygame.math.Vector2(self.x, self.y)
            desired = (target_pos - missile_pos).normalize()
            current = pygame.math.Vector2(self.dx, self.dy)
            steer = current.lerp(desired, 0.15).normalize()
            self.dx = steer.x
            self.dy = steer.y
            
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.rect.x = int(self.x - 8)
        self.rect.y = int(self.y - 8)
        
    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        if self.exploded:
            progress = self.explosion_timer / self.explosion_duration
            r = int(self.explosion_radius * progress)
            if r > 0:
                pygame.draw.circle(screen, (0, 200, 255), (int(draw_x), int(draw_y)), r, width=2)
        else:
            angle = math.degrees(math.atan2(self.dy, self.dx))
            missile_surf = pygame.Surface((24, 12), pygame.SRCALPHA)
            # Body and Sleek Nose
            pygame.draw.rect(missile_surf, (60, 70, 80), (4, 3, 14, 6), border_radius=1)
            pygame.draw.polygon(missile_surf, CYAN, [(18, 2), (24, 6), (18, 10)])
            # Fins
            pygame.draw.line(missile_surf, GRAY, (6, 3), (2, 0), width=2)
            pygame.draw.line(missile_surf, GRAY, (6, 9), (2, 12), width=2)
            # Ion Exhaust
            pygame.draw.circle(missile_surf, (0, 200, 255), (4, 6), 3)
            
            rot_missile = pygame.transform.rotate(missile_surf, -angle)
            screen.blit(rot_missile, (int(draw_x - rot_missile.get_width() // 2), int(draw_y - rot_missile.get_height() // 2)))

class SentryDrone:
    def __init__(self, owner, color, angle_offset=0.0):
        self.owner = owner
        self.color = color
        self.angle = angle_offset
        self.distance = 70
        self.last_shot = 0
        self.shoot_delay = 500
        self.life = 600 # 10 seconds
        self.x = owner.x
        self.y = owner.y
        self.width, self.height = 16, 16
        self.rect = pygame.Rect(0, 0, self.width, self.height)

    def update(self, current_time, enemies, enemy_bullets):
        self.life -= 1
        self.angle += 0.05
        self.x = self.owner.x + self.owner.width // 2 + math.cos(self.angle) * self.distance
        self.y = self.owner.y + self.owner.height // 2 + math.sin(self.angle) * self.distance
        self.rect.center = (int(self.x), int(self.y))
        
        new_bullets = []
        if current_time - self.last_shot > self.shoot_delay:
            self.last_shot = current_time
            
            # Default direction (tangent to orbit)
            dx, dy = math.cos(self.angle + math.pi/2), math.sin(self.angle + math.pi/2)
            
            # Target finding for initial shot direction
            closest_target_pos = None
            min_dist = 500.0
            drone_center = pygame.math.Vector2(self.rect.center)
            
            for target in enemies + enemy_bullets:
                t_pos = pygame.math.Vector2(target.rect.center)
                dist = drone_center.distance_to(t_pos)
                if dist < min_dist:
                    min_dist = dist
                    closest_target_pos = t_pos
            
            if closest_target_pos:
                diff = closest_target_pos - drone_center
                if diff.length() > 0:
                    to_target = diff.normalize()
                    dx, dy = to_target.x, to_target.y

            new_bullets.append(Bullet(self.x, self.y, dx, dy, speed=12, color=self.color))
        return new_bullets

    def draw(self, screen, camera_y, camera_x=0):
        dx, dy = self.x - camera_x, self.y - camera_y
        pygame.draw.circle(screen, self.color, (int(dx), int(dy)), 8, width=1)
        pygame.draw.circle(screen, WHITE, (int(dx), int(dy)), 2)

class SupportShip:
    def __init__(self, x, y, angle, color, owner=None):
        self.x = x
        self.y = y
        self.angle = angle
        self.color = color
        self.owner = owner
        self.speed = 14.0
        self.life = 180 # 3 seconds
        self.last_shot = 0
        self.shoot_delay = 120
        self.width = 30
        self.height = 30
        rad = math.radians(self.angle)
        self.direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, current_time):
        self.x += self.direction.x * self.speed
        self.y += self.direction.y * self.speed
        self.rect.center = (int(self.x), int(self.y))
        self.life -= 1
        
        new_projectiles = []
        if current_time - self.last_shot > self.shoot_delay:
            self.last_shot = current_time
            conv = pygame.math.Vector2(self.owner.rect.center) if self.owner else None
            new_projectiles.append(HomingMissile(self.x, self.y, self.direction.x, self.direction.y, scale=0.7, shooter=self, converge_pos=conv))
        return new_projectiles

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        center = pygame.math.Vector2(draw_x, draw_y)
        dir_f = self.direction
        dir_r = pygame.math.Vector2(-self.direction.y, self.direction.x)
        ticks = pygame.time.get_ticks()
        pulse = (math.sin(ticks * 0.05) + 1) / 2

        # Engine Flame
        flame_len = (12 + random.randint(-4, 8)) * (0.8 + 0.4 * pulse)
        y_jitter = random.uniform(-2, 2)
        rear_center = center - dir_f * (self.height // 2) + dir_f * y_jitter
        f_col = random.choice([ORANGE, YELLOW, WHITE])
        pygame.draw.polygon(screen, f_col, [rear_center, rear_center - dir_r * 5, rear_center - dir_f * flame_len, rear_center + dir_r * 5], width=1)

        # Hull (Simplified Player style)
        hull_tip = center + dir_f * (self.height // 2)
        hull_l = center - dir_f * (self.height // 4) - dir_r * 6
        hull_r = center - dir_f * (self.height // 4) + dir_r * 6
        pygame.draw.polygon(screen, self.color, [hull_tip, hull_l, hull_r])
        
        # Wings
        lw_tip = center - dir_f * 5 - dir_r * (self.width // 2)
        pygame.draw.line(screen, SLATE_GRAY, center, lw_tip, width=1)
        rw_tip = center - dir_f * 5 + dir_r * (self.width // 2)
        pygame.draw.line(screen, SLATE_GRAY, center, rw_tip, width=1)

class Flare:
    def __init__(self, x, y, dx=0.0, dy=0.0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = 8
        self.life_time = 180 # frames (3 seconds at 60 FPS)
        self.life_timer = self.life_time
        self.color = (255, 165, 0) # Orange
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self):
        self.life_timer -= 1
        # Flares apply velocity plus a bit of turbulence drift
        self.x += self.dx + random.uniform(-0.3, 0.3)
        self.y += self.dy + random.uniform(-0.3, 0.3)
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        alpha = int(255 * (self.life_timer / self.life_time))
        pulse = int(4 * math.sin(pygame.time.get_ticks() * 0.02))
        pygame.draw.circle(screen, (*self.color, alpha // 2), (int(draw_x), int(draw_y)), self.radius + pulse)
        pygame.draw.circle(screen, (*WHITE, alpha), (int(draw_x), int(draw_y)), self.radius)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.radius = random.randint(2, 5)
        self.life = random.randint(15, 30)
        self.max_life = self.life

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        self.dx *= 0.96
        self.dy *= 0.96

    def draw(self, screen, camera_y, camera_x=0):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        r = self.radius
        pygame.draw.rect(screen, self.color, (draw_x - r, draw_y - r, r * 2, r * 2), width=1)

class EngineTrailParticle:
    def __init__(self, x, y, direction, class_name):
        self.x = x + random.uniform(-4, 4)
        self.y = y + random.uniform(-4, 4)
        
        # Eject in the opposite direction of movement with a slight spread
        spread_angle = random.uniform(-0.18, 0.18)
        opposite_dir = (-direction).rotate_rad(spread_angle)
        speed = random.uniform(2.5, 6.0)
        
        self.dx = opposite_dir.x * speed
        self.dy = opposite_dir.y * speed
        self.radius = random.randint(4, 8)
        self.life = random.randint(10, 18)
        self.max_life = self.life
        
        colors = {
            'RANGER': (0, 255, 255),
            'ENGINEER': (255, 215, 0),
            'VANGUARD': (255, 0, 255),
            'SNIPER': (255, 255, 0),
            'ASSASSIN': (138, 43, 226)
        }
        self.color = colors.get(class_name, (255, 120, 0))

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        self.dx *= 0.94
        self.dy *= 0.94
        self.radius = max(0.5, self.radius - 0.3)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        # Fast direct circle draws instead of creating brand new Surfaces per particle per frame
        r = int(self.radius)
        if r > 0:
            pygame.draw.circle(screen, self.color, (draw_x, draw_y), r)

class SmallPortal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 30
        self.rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30)

    def update(self):
        pass

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        
        for i in range(3):
            r = self.radius - i * 8 + int(4 * math.sin(ticks * 0.01 + i))
            if r > 5:
                surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                color = (0, 255, 255, 120 - i * 35)
                pygame.draw.circle(surf, color, (r, r), r, width=2)
                angle = ticks * 0.002 + i * (math.pi / 2)
                dot_x = r + int((r - 2) * math.cos(angle))
                dot_y = r + int((r - 2) * math.sin(angle))
                pygame.draw.circle(surf, WHITE, (dot_x, dot_y), 2)
                
                screen.blit(surf, (int(draw_x - r), int(draw_y - r)))

class ShockwaveRing:
    def __init__(self, x, y, max_radius, color, duration=24):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.color = color
        self.life = duration
        self.max_life = duration
        
    def update(self):
        self.life -= 1
        return self.life > 0
        
    def draw(self, screen, camera_y, camera_x=0):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        progress = 1.0 - (self.life / self.max_life)
        r = int(self.max_radius * progress)
        if r > 0:
            pygame.draw.circle(screen, self.color, (draw_x, draw_y), r, width=1)

class EnemyBullet:
    def __init__(self, x, y, dx, dy, color=(255, 100, 100), speed=6.6, size=8, is_gravity=False, is_homing=False, target_player=None, telegraph_frames=6, life_time=0, shooter=None):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.size = size
        self.width = size * 2
        self.height = size * 2
        self.rect = pygame.Rect(self.x - size, self.y - size, self.width, self.height)
        self.color = color
        self.is_gravity = is_gravity
        self.is_homing = is_homing
        self.target_player = target_player
        self.telegraph_frames = telegraph_frames
        self.telegraph_timer = telegraph_frames # Frames before bullet becomes active
        self.life_time = life_time # Frames before bullet self-detonates
        self.life_timer = life_time
        self.shooter = shooter

    def update(self, flares=None):
        # Delete homing bullet if the shooter died
        if self.is_homing and self.shooter:
            shooter_dead = getattr(self.shooter, 'is_dead', False)
            if hasattr(self.shooter, 'health') and self.shooter.health <= 0:
                shooter_dead = True
            if shooter_dead:
                self.life_time = 1
                self.life_timer = 0
                return

        if self.telegraph_timer > 0:
            self.telegraph_timer -= 1
            return
        
        if self.life_time > 0:
            self.life_timer -= 1

        # Homing missiles target flares if they are nearby
        current_target_pos = None
        if self.is_homing:
            if flares:
                closest_flare = None
                min_dist = 250
                for f in flares:
                    d = pygame.math.Vector2(self.x, self.y).distance_to(pygame.math.Vector2(f.x, f.y))
                    if d < min_dist:
                        min_dist = d
                        closest_flare = f
                if closest_flare:
                    current_target_pos = pygame.math.Vector2(closest_flare.x, closest_flare.y)

            if not current_target_pos and self.target_player:
                current_target_pos = pygame.math.Vector2(self.target_player.rect.center)

        if current_target_pos:
            to_target = current_target_pos - pygame.math.Vector2(self.x, self.y)
            if to_target.length() > 5:
                to_target = to_target.normalize()
                dir_vec = pygame.math.Vector2(self.dx, self.dy).normalize()
                dir_vec += to_target * 0.05
                dir_vec = dir_vec.normalize()
                self.dx = dir_vec.x
                self.dy = dir_vec.y
                
        if self.is_gravity and self.target_player:
            player_center = pygame.math.Vector2(self.target_player.rect.center)
            to_bullet = pygame.math.Vector2(self.x, self.y) - player_center
            dist = to_bullet.length()
            if dist < 180:
                pull_strength = (180 - dist) * 0.003 # 5x weaker pull on player
                self.target_player.x += to_bullet.normalize().x * pull_strength
                self.target_player.y += to_bullet.normalize().y * pull_strength
                self.target_player.rect.x = int(self.target_player.x)
                self.target_player.rect.y = int(self.target_player.y)
                
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.rect.x = int(self.x - self.size)
        self.rect.y = int(self.y - self.size)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        if self.telegraph_timer > 0:
            radius = self.size + 6 + int(2 * math.sin(pygame.time.get_ticks() * 0.03))
            pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), radius, width=2)
            return

        # Direct drawing instead of surface per bullet
        # 1. Laser tracer trail
        trail_len = 16
        back_x = draw_x - self.dx * trail_len
        back_y = draw_y - self.dy * trail_len
        pygame.draw.line(screen, self.color, (int(draw_x), int(draw_y)), (int(back_x), int(back_y)), width=4)
        pygame.draw.line(screen, WHITE, (int(draw_x), int(draw_y)), (int(back_x + self.dx * 4), int(back_y + self.dy * 4)), width=2)

        # 2. Bullet core
        pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), self.size + 2)
        pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), max(1, self.size - 2))
        
        if self.is_gravity:
            pulse = int(4 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.circle(screen, PURPLE, (int(draw_x), int(draw_y)), self.size + 8 + pulse, width=2)

class ShieldCrystal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.rect = pygame.Rect(self.x - 12, self.y - 12, self.width, self.height)
        self.health = 3
        self.color = CYAN
        self.pulse_timer = random.uniform(0, 100)

    def update(self):
        self.rect.x = int(self.x - 12)
        self.rect.y = int(self.y - 12)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        t = pygame.time.get_ticks() * 0.005 + self.pulse_timer
        offset = int(4 * math.sin(t))
        points = [
            (draw_x, draw_y - 14 - offset),
            (draw_x + 10 + offset, draw_y),
            (draw_x, draw_y + 14 + offset),
            (draw_x - 10 - offset, draw_y)
        ]
        pygame.draw.polygon(screen, CYAN, points)
        pygame.draw.polygon(screen, WHITE, points, width=1)
        
        # Shield aura radius indicator
        surf = pygame.Surface((500, 500), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 255, 255, 10), (250, 250), 250, width=1)
        screen.blit(surf, (int(draw_x - 250), int(draw_y - 250)))

class PlayerShieldCrystal(ShieldCrystal):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 5 # Slightly tougher than generic ShieldCrystal

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        t = pygame.time.get_ticks() * 0.005 + self.pulse_timer
        offset = int(4 * math.sin(t))
        points = [ (draw_x, draw_y - 14 - offset), (draw_x + 10 + offset, draw_y), (draw_x, draw_y + 14 + offset), (draw_x - 10 - offset, draw_y) ]
        pygame.draw.polygon(screen, CYAN, points)
        pygame.draw.polygon(screen, WHITE, points, width=1)
        surf = pygame.Surface((500, 500), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 255, 255, 10), (250, 250), 250, width=1)
        screen.blit(surf, (int(draw_x - 250), int(draw_y - 250)))

class GravityWell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 200
        self.rect = pygame.Rect(self.x - 20, self.y - 20, 40, 40)
        self.pull_force = 0.5

    def update(self, player, bullets, meteors, static_obstacles, game_instance=None):
        p_pos = pygame.math.Vector2(player.x + player.width // 2, player.y + player.height // 2)
        well_pos = pygame.math.Vector2(self.x, self.y)
        dist = p_pos.distance_to(well_pos)
        if dist < self.radius and dist > 10:
            # Player pull is 5x weaker now
            pull = (well_pos - p_pos).normalize() * (self.pull_force * 0.2 * (1.0 - dist / self.radius))
            player.x += pull.x
            player.y += pull.y
        
        for b in bullets:
            b_pos = pygame.math.Vector2(b.x, b.y)
            dist = b_pos.distance_to(well_pos)
            if dist < self.radius and dist > 10:
                # Median pull and curve on projectiles (pull = 1.6, lerp = 0.15)
                pull = (well_pos - b_pos).normalize() * (self.pull_force * 1.6 * (1.0 - dist / self.radius))
                b.x += pull.x
                b.y += pull.y
                # Curve bullet flight path towards black hole center
                desired_dir = (well_pos - b_pos).normalize()
                current_dir = pygame.math.Vector2(b.dx, b.dy)
                new_dir = current_dir.lerp(desired_dir, 0.15).normalize()
                b.dx = new_dir.x
                b.dy = new_dir.y

        for m in meteors[:]:
            m_pos = pygame.math.Vector2(m.rect.center)
            dist = m_pos.distance_to(well_pos)
            if dist < self.radius and dist > 10:
                if dist < 30: # Close enough to be sucked in and destroyed
                    if m in meteors:
                        meteors.remove(m)
                    if game_instance:
                        game_instance.spawn_explosion(m.rect.centerx, m.rect.centery, [(138, 43, 226), (75, 0, 130), (255, 255, 255)], 15)
                        if SOUNDS: SOUNDS.play('explosion')
                    continue
                pull = (well_pos - m_pos).normalize() * (self.pull_force * 0.6 * (1.0 - dist / self.radius))
                m.x += pull.x
                m.y += pull.y
                m.rect.center = (int(m.x), int(m.y))
                
        for obs in static_obstacles:
            obs_pos = pygame.math.Vector2(obs.rect.center)
            dist = obs_pos.distance_to(well_pos)
            if dist < self.radius and dist > 10:
                pull = (well_pos - obs_pos).normalize() * (self.pull_force * 0.4 * (1.0 - dist / self.radius))
                obs.x += pull.x
                obs.y += pull.y
                obs.rect.center = (int(obs.x), int(obs.y))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        for i in range(3):
            r = 15 + i * 12 + int(5 * math.sin(ticks * 0.01 + i))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            color = (138, 43, 226, 60 - i * 15)
            pygame.draw.circle(surf, color, (r, r), r)
            screen.blit(surf, (int(draw_x - r), int(draw_y - r)))
        pygame.draw.circle(screen, BLACK, (int(draw_x), int(draw_y)), 10)
        pygame.draw.circle(screen, PURPLE, (int(draw_x), int(draw_y)), 10, width=1)

class DataUplink:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 24
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        self.hacked = False
        self.hack_progress = 0.0 # 0 to 1.0
        
    def update(self, player):
        if self.hacked:
            return False
            
        p_pos = pygame.math.Vector2(player.x + player.width // 2, player.y + player.height // 2)
        u_pos = pygame.math.Vector2(self.x, self.y)
        dist = p_pos.distance_to(u_pos)
        
        if dist < 150: # Hacking radius
            self.hack_progress += 0.0125 # Hacks over ~1.3 seconds
            if self.hack_progress >= 1.0:
                self.hacked = True
                player.add_credits(150)
                player.award_xp(40)
                player.scraps += random.randint(2, 4)
                return True
        else:
            self.hack_progress = max(0.0, self.hack_progress - 0.005)
        return False

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        
        # Draw rotating wireframe hexagon
        num_sides = 6
        glow = int(3 * math.sin(ticks * 0.01))
        r = self.radius + glow
        points = []
        for i in range(num_sides):
            ang = math.radians(i * (360 / num_sides) + ticks * 0.04)
            px = draw_x + int(r * math.cos(ang))
            py = draw_y + int(r * math.sin(ang))
            points.append((px, py))
            
        color = CYAN if not self.hacked else GREEN
        pygame.draw.polygon(screen, color, points, width=1)
        
        # Inner antenna lines
        pygame.draw.line(screen, color, (draw_x, draw_y - r), (draw_x, draw_y + r), 1)
        pygame.draw.line(screen, color, (draw_x - r, draw_y), (draw_x + r, draw_y), 1)
        
        # Draw hack progress circle
        if self.hack_progress > 0 and not self.hacked:
            pct_r = int(self.radius * 0.6 * self.hack_progress)
            pygame.draw.circle(screen, GREEN, (int(draw_x), int(draw_y)), pct_r, width=1)
            
        # Draw label
        font = pygame.font.SysFont("Arial", 12, bold=True)
        lbl_text = "DATA TERMINAL" if not self.hacked else "TERMINAL DOCKED"
        lbl = font.render(lbl_text, True, color)
        screen.blit(lbl, (draw_x - lbl.get_width() // 2, draw_y - r - 16))
        
        if self.hack_progress > 0 and not self.hacked:
            pct_text = f"{int(self.hack_progress * 100)}%"
            pct_lbl = font.render(pct_text, True, GREEN)
            screen.blit(pct_lbl, (draw_x - pct_lbl.get_width() // 2, draw_y + r + 5))

class SubBossEntity:
    def __init__(self, name, max_health, color, width, height, x_offset, y_offset, behavior_type):
        self.is_stabilizer = "STABILIZER" in name.upper()
        self.name = ""
        self.max_health = max_health
        self.health = max_health
        self.color = color
        self.width = width
        self.height = height
        self.x = VIRTUAL_WIDTH // 2
        self.y = 0
        self.rect = pygame.Rect(self.x - width // 2, self.y - height // 2, width, height)
        self.is_dead = False
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.behavior_type = behavior_type
        self.last_shot = 0

    def update_position(self, boss_center_x, boss_center_y, t):
        if self.is_dead:
            return
        if self.behavior_type == 'left':
            self.x = boss_center_x - 120 + 80 * math.sin(t)
            self.y = boss_center_y + 40 * math.cos(t)
        elif self.behavior_type == 'right':
            self.x = boss_center_x + 120 + 80 * math.sin(t + math.pi)
            self.y = boss_center_y + 40 * math.cos(t + math.pi)
        elif self.behavior_type == 'tri_1':
            self.x = boss_center_x + 120 * math.sin(t)
            self.y = boss_center_y - 60 + 30 * math.cos(t)
        elif self.behavior_type == 'tri_2':
            self.x = boss_center_x - 140 + 80 * math.sin(t + 2 * math.pi / 3)
            self.y = boss_center_y + 60 + 30 * math.cos(t + 2 * math.pi / 3)
        elif self.behavior_type == 'tri_3':
            self.x = boss_center_x + 140 + 80 * math.sin(t + 4 * math.pi / 3)
            self.y = boss_center_y + 60 + 30 * math.cos(t + 4 * math.pi / 3)
        else:
            self.x = boss_center_x
            self.y = boss_center_y
            
        self.rect.x = int(self.x - self.width // 2)
        self.rect.y = int(self.y - self.height // 2)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if getattr(self, 'is_stabilizer', False):
            # Draw factory stabilizer/generator
            # Circular outer ring with rotating energy nodes
            pygame.draw.circle(screen, (30, 30, 32), (int(draw_x), int(draw_y)), self.width // 2, width=1)
            # Energy lines
            ticks = pygame.time.get_ticks()
            for angle in range(0, 360, 60):
                rad = math.radians(angle + ticks * 0.05)
                ex = draw_x + (self.width // 2 - 8) * math.cos(rad)
                ey = draw_y + (self.width // 2 - 8) * math.sin(rad)
                pygame.draw.circle(screen, CYAN, (int(ex), int(ey)), 4, width=1)
            # Core
            pulse = 10 + int(5 * math.sin(ticks * 0.02))
            pygame.draw.circle(screen, (0, 100, 255), (int(draw_x), int(draw_y)), pulse, width=1)
            pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), 2)
            return

        center = pygame.math.Vector2(draw_x, draw_y)
        dir_f = pygame.math.Vector2(0, 1) # Forward is down
        dir_r = pygame.math.Vector2(1, 0) # Right is right
        
        # 1. ENGINES FLAMES
        flicker = random.randint(0, 12)
        flame_color = self.color
        
        rear_pos = center - dir_f * (self.height // 2)
        pygame.draw.polygon(screen, flame_color, [
            rear_pos - dir_r * (self.width // 6),
            rear_pos - dir_f * (15 + flicker),
            rear_pos + dir_r * (self.width // 6)
        ], width=1)
        
        # 2. WINGS
        lw_tip = center - dir_f * 5 - dir_r * (self.width // 2)
        lw_base_in = center - dir_f * (self.height // 2) - dir_r * 5
        lw_base_out = center - dir_f * (self.height // 3) - dir_r * (self.width // 2)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, lw_tip, lw_base_out, lw_base_in])
        
        rw_tip = center - dir_f * 5 + dir_r * (self.width // 2)
        rw_base_in = center - dir_f * (self.height // 2) + dir_r * 5
        rw_base_out = center - dir_f * (self.height // 3) + dir_r * (self.width // 2)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, rw_tip, rw_base_out, rw_base_in])

        # 3. MAIN HULL (Triangle shape)
        hull_tip = center + dir_f * (self.height // 2)
        hull_left = center - dir_f * (self.height // 4) - dir_r * (self.width // 5)
        hull_right = center - dir_f * (self.height // 4) + dir_r * (self.width // 5)
        pygame.draw.polygon(screen, self.color, [hull_tip, hull_left, hull_right])

        # 4. COCKPIT GLASS
        glass_tip = center + dir_f * (self.height // 3)
        glass_left = center + dir_f * (self.height // 8) - dir_r * (self.width // 10)
        glass_right = center + dir_f * (self.height // 8) + dir_r * (self.width // 10)
        pygame.draw.polygon(screen, WHITE, [glass_tip, glass_left, glass_right])
        
        pulse_r = 5 + int(3 * math.sin(pygame.time.get_ticks() * 0.02))
        pygame.draw.circle(screen, self.color, (int(center.x), int(center.y + 4)), pulse_r + 2, width=1)
        pygame.draw.circle(screen, WHITE, (int(center.x), int(center.y + 4)), 2)

class Boss:
    def __init__(self, zone, y):
        self.zone = zone
        self.x = VIRTUAL_WIDTH // 2
        self.y = y - 500
        self.appearance_timer = 120
        self.is_dead = False
        self.death_timer = 0
        self.shielded = False
        self.angle_offset = 0.0
        self.boss_player_dist = 350.0
        
        # Retrieve config
        cfg = BIOME_CONFIGS.get(zone, {'name': 'UNKNOWN', 'theme_color': RED, 'boss_count': 1})
        self.name = ""
        self.color = cfg['theme_color']
        self.boss_count = cfg['boss_count']
        
        # Scaling difficulty factors
        zone_keys = ['ASTEROIDS', 'VULCAN', 'AQUARIS', 'NEBULA', 'PLASMA', 'VOID', 'QUANTUM', 'SINGULARITY', 'ORION']
        diff_idx = zone_keys.index(zone) if zone in zone_keys else 0
        
        # Boss difficulty adjustments: scale health strongly based on progression depth
        sub_boss_base_health = 60 + diff_idx * 20
        base_max_health = sub_boss_base_health * self.boss_count
        self.shoot_delay = max(650, 1350 - diff_idx * 75)
        self.max_health = base_max_health
        self.health = self.max_health
        
        # Setup SubBoss Entities
        self.sub_bosses = []
        if zone == 'SINGULARITY':
            self.sub_bosses.append(SubBossEntity("Stabilizer Alpha", self.max_health // 3, self.color, 80, 80, 0, 0, 'tri_1'))
            self.sub_bosses.append(SubBossEntity("Stabilizer Beta", self.max_health // 3, self.color, 80, 80, 0, 0, 'tri_2'))
            self.sub_bosses.append(SubBossEntity("Stabilizer Gamma", self.max_health // 3, self.color, 80, 80, 0, 0, 'tri_3'))
        elif self.boss_count == 1:
            self.sub_bosses.append(SubBossEntity(self.name, self.max_health, self.color, 120, 80, 0, 0, 'center'))
        elif self.boss_count == 2:
            self.sub_bosses.append(SubBossEntity(self.name + " Alpha", self.max_health // 2, self.color, 90, 60, -120, 0, 'left'))
            self.sub_bosses.append(SubBossEntity(self.name + " Beta", self.max_health // 2, self.color, 90, 60, 120, 0, 'right'))
        else: # 3 bosses
            self.sub_bosses.append(SubBossEntity(self.name + " Prime", self.max_health // 3, self.color, 80, 50, 0, -60, 'tri_1'))
            self.sub_bosses.append(SubBossEntity(self.name + " Vex", self.max_health // 3, GOLD, 80, 50, -140, 60, 'tri_2'))
            self.sub_bosses.append(SubBossEntity(self.name + " Void", self.max_health // 3, INDIGO, 80, 50, 140, 60, 'tri_3'))

        # Recalculate max_health and health based on actual subbosses
        self.max_health = sum(ent.max_health for ent in self.sub_bosses)
        self.health = self.max_health
            
        # Specific gimmicks
        if zone == 'AQUARIS':
            self.shield_crystals = []
            for i in range(3):
                angle = i * (2 * math.pi / 3)
                cx = self.x + 120 * math.cos(angle)
                cy = self.y + 120 * math.sin(angle)
                self.shield_crystals.append(ShieldCrystal(cx, cy))
        elif zone == 'ASTEROIDS':
            self.gravity_well = GravityWell(self.x, self.y)

    def update(self, current_time, player, projectiles_list, game_instance):
        if self.is_dead:
            self.death_timer += 1
            if self.death_timer % 4 == 0:
                ent = random.choice(self.sub_bosses)
                game_instance.spawn_explosion(ent.x + random.randint(-30, 30), ent.y + random.randint(-30, 30),
                                             [(255, 69, 0), (255, 140, 0), (255, 255, 0), (255, 255, 255)], 8)
            return

        if self.zone == 'SINGULARITY':
            # Remain stationary at reactor core room center
            self.x = VIRTUAL_WIDTH // 2
            self.y = -3000
            self.appearance_timer = 0
            
            ent_center = pygame.math.Vector2(self.x, self.y)
            player_center = pygame.math.Vector2(player.rect.center)
            dist_to_player = ent_center.distance_to(player_center)
            
            t = pygame.time.get_ticks() * 0.002
            self.angle_offset += 0.03
            for ent in self.sub_bosses:
                ent.update_position(self.x, self.y, t)
                
            active_stabilizers = [sb for sb in self.sub_bosses if not sb.is_dead]
            self.shielded = len(active_stabilizers) > 0
            
            # Firing logic: only fire if player is inside the core room (dist < 700)
            if dist_to_player < 700:
                for ent in self.sub_bosses:
                    if ent.is_dead:
                        continue
                    if current_time - ent.last_shot > self.shoot_delay:
                        ent.last_shot = current_time
                        ent_center_node = pygame.math.Vector2(ent.rect.center)
                        dir_to_player = (player_center - ent_center_node).normalize()
                        spawn_offset = ent.width // 2 + 20
                        spawn_pos = ent_center_node + dir_to_player * spawn_offset
                        
                        # Manageable homing bullet stream (2 tracking projectiles at a time)
                        perp_vec = pygame.math.Vector2(-dir_to_player.y, dir_to_player.x) * 15
                        projectiles_list.append(EnemyBullet(spawn_pos.x - perp_vec.x, spawn_pos.y - perp_vec.y, dir_to_player.x, dir_to_player.y, color=BLUE, speed=5.5, size=11, is_gravity=True, is_homing=True, target_player=player, shooter=ent))
                        projectiles_list.append(EnemyBullet(spawn_pos.x + perp_vec.x, spawn_pos.y + perp_vec.y, dir_to_player.x, dir_to_player.y, color=BLUE, speed=5.5, size=11, is_gravity=True, is_homing=True, target_player=player, shooter=ent))
            return

        if hasattr(self, 'appearance_timer') and self.appearance_timer > 0:
            self.appearance_timer -= 1
            target_y = player.y - 450
            self.y += (target_y - self.y) * 0.05
            self.x = player.x + player.width // 2
            for ent in self.sub_bosses:
                ent.update_position(self.x, self.y, 0)
                # Spawn incoming portal particle sparks
                for _ in range(2):
                    px = ent.x + random.randint(-ent.width // 2, ent.width // 2)
                    py = ent.y + random.randint(-ent.height // 2, ent.height // 2)
                    p = Particle(px, py, self.color)
                    p.dx = random.uniform(-4, 4)
                    p.dy = random.uniform(-4, 4)
                    p.life = random.randint(20, 40)
                    p.max_life = p.life
                    game_instance.particles.append(p)
            if self.zone == 'AQUARIS':
                for i, crystal in enumerate(self.shield_crystals):
                    angle = i * (2 * math.pi / 3) + self.angle_offset
                    crystal.x = self.x + 120 * math.cos(angle)
                    crystal.y = self.y + 120 * math.sin(angle)
                    crystal.update()
            return

        # Boss slowly creeps closer to the player over time while staying visible
        self.boss_player_dist = max(100.0, self.boss_player_dist - 0.25)
        target_y = player.y - self.boss_player_dist
        self.y += (target_y - self.y) * 0.03
        
        t = pygame.time.get_ticks() * 0.002
        target_x = (player.x + player.width // 2) + 220 * math.sin(t)
        self.x += (target_x - self.x) * 0.06
        
        self.angle_offset += 0.03
        
        for ent in self.sub_bosses:
            ent.update_position(self.x, self.y, t)
            
        if self.zone == 'ORION':
            for ent in self.sub_bosses:
                if not ent.is_dead:
                    ent_rect = pygame.Rect(ent.x - ent.width // 2, ent.y - ent.height // 2, ent.width, ent.height)
                    for obs in game_instance.static_obstacles[:]:
                        if ent_rect.colliderect(obs.rect):
                            if obs in game_instance.static_obstacles:
                                game_instance.static_obstacles.remove(obs)
                                game_instance.spawn_explosion(obs.rect.centerx, obs.rect.centery, [(255, 0, 255), (100, 100, 100)], 12)
            
        if self.zone == 'AQUARIS':
            active_crystals = [c for c in self.shield_crystals if c.health > 0]
            self.shielded = len(active_crystals) > 0
            
            for i, crystal in enumerate(self.shield_crystals):
                if crystal.health > 0:
                    angle = i * (2 * math.pi / 3) + self.angle_offset
                    crystal.x = self.x + 120 * math.cos(angle)
                    crystal.y = self.y + 120 * math.sin(angle)
                    crystal.update()
        elif self.zone == 'ASTEROIDS':
            self.gravity_well.x = self.x
            self.gravity_well.y = self.y
            self.gravity_well.update(player, game_instance.bullets, game_instance.meteors, game_instance.static_obstacles, game_instance)
        elif self.zone == 'SINGULARITY':
            active_stabilizers = [sb for sb in self.sub_bosses if not sb.is_dead]
            self.shielded = len(active_stabilizers) > 0
            
        # Firing logic for each active sub-boss
        for ent in self.sub_bosses:
            if ent.is_dead:
                continue
            if current_time - ent.last_shot > self.shoot_delay:
                ent.last_shot = current_time
                ent_center = pygame.math.Vector2(ent.rect.center)
                player_center = pygame.math.Vector2(player.rect.center)
                dir_to_player = (player_center - ent_center).normalize()
                spawn_offset = ent.width // 2 + 20
                spawn_pos = ent_center + dir_to_player * spawn_offset
                
                # Balanced Biome-specific custom bullet attacks (no double duplication, reduced spam)
                if self.zone == 'AQUARIS':
                    for rot in [-15, 0, 15]:
                        r_dir = dir_to_player.rotate(rot)
                        projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, r_dir.x, r_dir.y, color=CYAN, speed=7.0))
                elif self.zone == 'VULCAN':
                    projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, dir_to_player.x, dir_to_player.y, color=ORANGE, speed=8.5))
                    r_vec = pygame.math.Vector2(-dir_to_player.y, dir_to_player.x) * 35
                    projectiles_list.append(EnemyBullet(spawn_pos.x - r_vec.x, spawn_pos.y - r_vec.y, dir_to_player.x, dir_to_player.y, color=YELLOW, speed=7.5))
                    projectiles_list.append(EnemyBullet(spawn_pos.x + r_vec.x, spawn_pos.y + r_vec.y, dir_to_player.x, dir_to_player.y, color=YELLOW, speed=7.5))
                elif self.zone == 'ASTEROIDS':
                    projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, dir_to_player.x, dir_to_player.y, color=PURPLE, speed=7.5))
                    for angle in [0, 90, 180, 270]:
                        rad = math.radians(angle + math.degrees(self.angle_offset))
                        projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, math.cos(rad), math.sin(rad), color=PURPLE, speed=6.0))
                elif self.zone == 'NEBULA':
                    for rot in [-15, 0, 15]:
                        r_dir = dir_to_player.rotate(rot)
                        projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, r_dir.x, r_dir.y, color=PURPLE, speed=7.5, size=9))
                elif self.zone == 'PLASMA':
                    # 2 tracking projectiles at a time
                    perp_vec = pygame.math.Vector2(-dir_to_player.y, dir_to_player.x) * 15
                    projectiles_list.append(EnemyBullet(spawn_pos.x - perp_vec.x, spawn_pos.y - perp_vec.y, dir_to_player.x, dir_to_player.y, color=GOLD, speed=7.5, size=8, is_homing=True, target_player=player, shooter=ent))
                    projectiles_list.append(EnemyBullet(spawn_pos.x + perp_vec.x, spawn_pos.y + perp_vec.y, dir_to_player.x, dir_to_player.y, color=GOLD, speed=7.5, size=8, is_homing=True, target_player=player, shooter=ent))
                elif self.zone == 'VOID':
                    projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, dir_to_player.x, dir_to_player.y, color=INDIGO, speed=6.5, size=10, is_gravity=True, target_player=player))
                elif self.zone == 'QUANTUM':
                    for angle in [0, 60, 120, 180, 240, 300]:
                        rad = math.radians(angle + math.degrees(self.angle_offset))
                        projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, math.cos(rad), math.sin(rad), color=GREEN, speed=6.5, size=8))
                elif self.zone == 'ORION':
                    if ent.behavior_type == 'tri_1':
                        # 2 tracking projectiles at a time
                        perp_vec = pygame.math.Vector2(-dir_to_player.y, dir_to_player.x) * 15
                        projectiles_list.append(EnemyBullet(spawn_pos.x - perp_vec.x, spawn_pos.y - perp_vec.y, dir_to_player.x, dir_to_player.y, color=MAGENTA, speed=7.5, size=8, is_homing=True, target_player=player, shooter=ent))
                        projectiles_list.append(EnemyBullet(spawn_pos.x + perp_vec.x, spawn_pos.y + perp_vec.y, dir_to_player.x, dir_to_player.y, color=MAGENTA, speed=7.5, size=8, is_homing=True, target_player=player, shooter=ent))
                    elif ent.behavior_type == 'tri_2':
                        for offset in [-15, 15]:
                            r = math.radians(math.degrees(math.atan2(dir_to_player.y, dir_to_player.x)) + offset)
                            projectiles_list.append(EnemyBullet(spawn_pos.x, spawn_pos.y, math.cos(r), math.sin(r), color=GOLD, speed=8.0, size=7))
                    else:
                        perp_dx = -dir_to_player.y
                        perp_dy = dir_to_player.x
                        projectiles_list.append(EnemyBullet(spawn_pos.x - perp_dx * 12, spawn_pos.y - perp_dy * 12, dir_to_player.x, dir_to_player.y, color=INDIGO, speed=8.5, size=6))
                        projectiles_list.append(EnemyBullet(spawn_pos.x + perp_dx * 12, spawn_pos.y + perp_dy * 12, dir_to_player.x, dir_to_player.y, color=INDIGO, speed=8.5, size=6))

    def draw(self, screen, camera_y, camera_x=0):
        if self.is_dead:
            for ent in self.sub_bosses:
                orig_color = ent.color
                ent.color = (40, 40, 40)
                ent.draw(screen, camera_y, camera_x)
                ent.color = orig_color
                draw_x = ent.x - camera_x
                draw_y = ent.y - camera_y
                if pygame.time.get_ticks() % 150 < 75:
                    pygame.draw.circle(screen, RED, (int(draw_x + random.randint(-15, 15)), int(draw_y + random.randint(-15, 15))), 10)
                    pygame.draw.circle(screen, ORANGE, (int(draw_x + random.randint(-10, 10)), int(draw_y + random.randint(-10, 10))), 6)
            return
        
        if self.zone == 'SINGULARITY':
            # Draw a massive Central Reactor Core (a black hole inside mechanical shields)
            draw_x = self.x - camera_x
            draw_y = self.y - camera_y
            ticks = pygame.time.get_ticks()
            
            # 1. Outer structure ring
            pygame.draw.circle(screen, (70, 70, 75), (int(draw_x), int(draw_y)), 100)
            pygame.draw.circle(screen, (35, 35, 38), (int(draw_x), int(draw_y)), 100, width=5)
            
            # 2. Rotating warning stripes/girders
            for i in range(8):
                angle = math.radians(i * 45 + ticks * 0.02)
                p1 = (int(draw_x + 95 * math.cos(angle)), int(draw_y + 95 * math.sin(angle)))
                p2 = (int(draw_x + 115 * math.cos(angle)), int(draw_y + 115 * math.sin(angle)))
                pygame.draw.line(screen, (220, 160, 10) if i % 2 == 0 else (40, 40, 45), p1, p2, width=6)
                
            # 3. Outer shield dome (if shielded)
            if self.shielded:
                shield_pulse = 100 + int(8 * math.sin(ticks * 0.01))
                s_surf = pygame.Surface((shield_pulse * 2 + 10, shield_pulse * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(s_surf, (0, 150, 255, 60), (shield_pulse + 5, shield_pulse + 5), shield_pulse)
                pygame.draw.circle(s_surf, (0, 200, 255, 180), (shield_pulse + 5, shield_pulse + 5), shield_pulse, width=3)
                screen.blit(s_surf, (int(draw_x - shield_pulse - 5), int(draw_y - shield_pulse - 5)))

            # 4. The central black hole core itself
            bh_radius = 45 + int(6 * math.sin(ticks * 0.015))
            pygame.draw.circle(screen, (255, 140, 0), (int(draw_x), int(draw_y)), bh_radius + 12, width=4)
            pygame.draw.circle(screen, (0, 100, 255), (int(draw_x), int(draw_y)), bh_radius, width=6)
            pygame.draw.circle(screen, (0, 0, 0), (int(draw_x), int(draw_y)), bh_radius - 4)
            
            # Draw active sub-bosses (the stabilizers)
            for ent in self.sub_bosses:
                if not ent.is_dead:
                    ent.draw(screen, camera_y, camera_x)
            return

        for ent in self.sub_bosses:
            if not ent.is_dead:
                ent.draw(screen, camera_y, camera_x)
                
        # Draw entrance portal halo if spawning
        if hasattr(self, 'appearance_timer') and self.appearance_timer > 0:
            for ent in self.sub_bosses:
                if not ent.is_dead:
                    draw_x = ent.x - camera_x
                    draw_y = ent.y - camera_y
                    progress = self.appearance_timer / 120.0  # 1.0 down to 0.0
                    portal_r = int((progress * 120) + (ent.width // 2) + 5)
                    
                    for w in range(1, 4):
                        alpha = int(200 * (1.0 - progress))
                        surf = pygame.Surface((portal_r * 2 + 10, portal_r * 2 + 10), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (self.color[0], self.color[1], self.color[2], alpha // w), (portal_r + 5, portal_r + 5), portal_r, width=w * 2)
                        
                        for angle in range(0, 360, 45):
                            rad = math.radians(angle + progress * 360)
                            spoke_x = (portal_r + 5) + portal_r * math.cos(rad)
                            spoke_y = (portal_r + 5) + portal_r * math.sin(rad)
                            pygame.draw.line(surf, (255, 255, 255, alpha), (portal_r + 5, portal_r + 5), (int(spoke_x), int(spoke_y)), 1)
                        screen.blit(surf, (int(draw_x - portal_r - 5), int(draw_y - portal_r - 5)))
                        
        if self.shielded:
            for ent in self.sub_bosses:
                if not ent.is_dead:
                    glow = int(4 * math.sin(pygame.time.get_ticks() * 0.01))
                    pygame.draw.circle(screen, CYAN, (int(ent.x - camera_x), int(ent.y - camera_y)), (ent.width // 2) + 12 + glow, width=2)
                    
        if self.zone == 'AQUARIS':
            for crystal in self.shield_crystals:
                if crystal.health > 0:
                    crystal.draw(screen, camera_y, camera_x)
                    
        if self.zone == 'ASTEROIDS':
            self.gravity_well.draw(screen, camera_y, camera_x)
            
        # Draw shared boss health bar at top of screen
        bar_width = 300
        bar_height = 12
        bar_x = VIRTUAL_WIDTH // 2 - bar_width // 2
        bar_y = 60
        pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        health_ratio = max(0.0, min(1.0, self.health / self.max_health))
        pygame.draw.rect(screen, RED, (bar_x, bar_y, int(bar_width * health_ratio), bar_height), border_radius=3)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), width=1, border_radius=3)
        
        pass

class Enemy:
    def __init__(self, x, y, zone='PLAYING', subtype=None):
        self.zone = zone
        self.x = x
        self.y = y
        self.last_shot = pygame.time.get_ticks() + random.randint(-800, 800)
        self.angle = 90.0 # Straight down default
        if subtype is not None:
            self.subtype = subtype
        else:
            self.subtype = random.choice(['STANDARD', 'HEAVY', 'SCOUT', 'ELITE'])
        
        # Default sizes
        self.width = 30
        self.height = 30
        
        # Gimmick init fields
        self.shield_active = False
        self.last_dash = 0
        self.is_dormant = True  # Used by Meteor Dart
        self.last_evade = 0
        self.evade_cooldown = 1500
        self.seen = False
        if self.subtype in ('SCOUT', 'ELITE'):
            self.evade_chance = random.uniform(0.40, 0.65)
        else:
            self.evade_chance = random.uniform(0.15, 0.30)
        
        if zone == 'AQUARIS':
            # Cold/Ice Theme
            if self.subtype == 'STANDARD':
                self.name = "Frost Vanguard"
                self.speed = random.uniform(1.8, 2.6)
                self.color = CYAN
                self.health = 2
                self.shoot_delay = 2200
                self.credits_value = 25
            elif self.subtype == 'HEAVY':
                self.name = "Glacial Sentry"
                self.speed = random.uniform(1.0, 1.5)
                self.color = (0, 100, 255) # Deep Blue
                self.health = 6  # Tanky!
                self.shoot_delay = 3500  # Weak gun (slow fire rate)
                self.width, self.height = 40, 40
                self.credits_value = 45
            elif self.subtype == 'SCOUT':
                self.name = "Ice Charger"
                self.speed = random.uniform(3.5, 4.5)  # Fast rammer
                self.color = (180, 220, 255) # Pale Blue
                self.health = 1
                self.shoot_delay = 9999999 # never shoots (rams player)
                self.width, self.height = 24, 24
                self.credits_value = 20
            else: # ELITE (MINIBOSS)
                self.name = "Snowstorm Skiff"
                self.speed = random.uniform(2.0, 2.8)
                self.color = (0, 200, 200) # Teal
                self.health = 5  # Tanky Miniboss
                self.shoot_delay = 1800  # Strong multi-laser
                self.credits_value = 35
                
        elif zone == 'VULCAN':
            # Fire/Speed Theme
            if self.subtype == 'STANDARD':
                self.name = "Vulcan Scout"
                self.speed = random.uniform(3.5, 4.5)
                self.color = ORANGE
                self.health = 1
                self.shoot_delay = 2200
                self.credits_value = 20
            elif self.subtype == 'HEAVY':
                self.name = "Magma Bomber"
                self.speed = random.uniform(2.0, 2.8)
                self.color = (180, 0, 0) # Dark Red
                self.health = 5  # Tanky!
                self.shoot_delay = 3800  # Slow lava mortar
                self.width, self.height = 42, 42
                self.credits_value = 40
            elif self.subtype == 'SCOUT':
                self.name = "Solar Skiff"
                self.speed = random.uniform(5.0, 6.0)
                self.color = YELLOW
                self.health = 1
                self.shoot_delay = 2500
                self.width, self.height = 24, 24
                self.credits_value = 30
            else: # ELITE (MINIBOSS)
                self.name = "Pyro Interceptor"
                self.speed = random.uniform(3.2, 4.2)
                self.color = (255, 60, 60) # Crimson
                self.health = 4  # Tanky Miniboss
                self.shoot_delay = 2000  # Homing missile
                self.credits_value = 35
                
        elif zone == 'NEBULA':
            if self.subtype == 'STANDARD':
                self.name = "Static Raider"; self.speed = 2.8; self.color = PURPLE; self.health = 2; self.shoot_delay = 2000; self.credits_value = 30
            elif self.subtype == 'HEAVY':
                self.name = "Storm Fortress"; self.speed = 1.4; self.color = (130, 0, 255); self.health = 8; self.shoot_delay = 3500; self.width, self.height = 45, 45; self.credits_value = 60
            elif self.subtype == 'SCOUT':
                self.name = "Lightning Wraith"; self.speed = 4.2; self.color = (255, 100, 255); self.health = 1; self.shoot_delay = 1500; self.width, self.height = 24, 24; self.credits_value = 40
            else:
                self.name = "Nebula Archon"; self.speed = 2.8; self.color = WHITE; self.health = 12; self.shoot_delay = 1800; self.credits_value = 120
        elif zone == 'PLASMA':
            if self.subtype == 'STANDARD':
                self.name = "Flare Grunt"; self.speed = 3.2; self.color = GOLD; self.health = 2; self.shoot_delay = 1800; self.credits_value = 35
            elif self.subtype == 'HEAVY':
                self.name = "Solar Juggernaut"; self.speed = 1.6; self.color = (255, 200, 0); self.health = 10; self.shoot_delay = 4000; self.width, self.height = 48, 48; self.credits_value = 75
            elif self.subtype == 'SCOUT':
                self.name = "Plasma Leaper"; self.speed = 5.5; self.color = (255, 255, 150); self.health = 1; self.shoot_delay = 2000; self.width, self.height = 26, 26; self.credits_value = 45
            else:
                self.name = "Sun Emperor"; self.speed = 3.0; self.color = WHITE; self.health = 15; self.shoot_delay = 1600; self.credits_value = 150
        elif zone == 'VOID':
            if self.subtype == 'STANDARD':
                self.name = "Void Drifter"; self.speed = 2.5; self.color = INDIGO; self.health = 3; self.shoot_delay = 2500; self.credits_value = 40
            elif self.subtype == 'HEAVY':
                self.name = "Abyss Sentinel"; self.speed = 1.2; self.color = (40, 0, 100); self.health = 12; self.shoot_delay = 3000; self.width, self.height = 50, 50; self.credits_value = 80
            elif self.subtype == 'SCOUT':
                self.name = "Shadow Reaper"; self.speed = 4.8; self.color = (100, 80, 255); self.health = 2; self.shoot_delay = 1400; self.width, self.height = 22, 22; self.credits_value = 50
            else:
                self.name = "Void Singularity"; self.speed = 2.4; self.color = BLACK; self.health = 18; self.shoot_delay = 2000; self.credits_value = 180
        elif zone == 'QUANTUM':
            if self.subtype == 'STANDARD':
                self.name = "Phase Grunt"; self.speed = 3.5; self.color = GREEN; self.health = 2; self.shoot_delay = 1800; self.credits_value = 45
            elif self.subtype == 'HEAVY':
                self.name = "Matrix Wall"; self.speed = 1.8; self.color = (0, 200, 100); self.health = 14; self.shoot_delay = 3200; self.width, self.height = 46, 46; self.credits_value = 90
            elif self.subtype == 'SCOUT':
                self.name = "Shift Blink"; self.speed = 6.0; self.color = (150, 255, 150); self.health = 1; self.shoot_delay = 1200; self.width, self.height = 20, 20; self.credits_value = 55
            else:
                self.name = "Quantum Ghost"; self.speed = 3.5; self.color = WHITE; self.health = 20; self.shoot_delay = 1500; self.credits_value = 200
        elif zone == 'SINGULARITY':
            if self.subtype == 'STANDARD':
                self.name = "Event Raider"; self.speed = 3.0; self.color = BLUE; self.health = 4; self.shoot_delay = 2000; self.credits_value = 50
            elif self.subtype == 'HEAVY':
                self.name = "Horizon Guard"; self.speed = 1.5; self.color = (0, 50, 200); self.health = 18; self.shoot_delay = 3500; self.width, self.height = 52, 52; self.credits_value = 110
            elif self.subtype == 'SCOUT':
                self.name = "Grav-Dart"; self.speed = 5.2; self.color = (100, 150, 255); self.health = 2; self.shoot_delay = 1600; self.width, self.height = 24, 24; self.credits_value = 65
            else:
                self.name = "Eternal Warden"; self.speed = 3.2; self.color = WHITE; self.health = 25; self.shoot_delay = 1400; self.credits_value = 250
        elif zone == 'ORION':
            if self.subtype == 'STANDARD':
                self.name = "Citadel Knight"; self.speed = 3.5; self.color = MAGENTA; self.health = 5; self.shoot_delay = 1500; self.credits_value = 60
            elif self.subtype == 'HEAVY':
                self.name = "Dreadnought Core"; self.speed = 2.0; self.color = (150, 0, 150); self.health = 25; self.shoot_delay = 3000; self.width, self.height = 60, 60; self.credits_value = 150
            elif self.subtype == 'SCOUT':
                self.name = "Orion Assassin"; self.speed = 6.5; self.color = (255, 150, 255); self.health = 3; self.shoot_delay = 1000; self.width, self.height = 28, 28; self.credits_value = 80
            else:
                self.name = "Imperial Overlord"; self.speed = 4.0; self.color = WHITE; self.health = 40; self.shoot_delay = 1200; self.credits_value = 500
        elif zone == 'TUTORIAL':
            # Target dummy configuration (tutorial range)
            self.name = "Target Dummy"
            self.speed = random.uniform(0.6, 1.2)
            self.color = GREEN
            self.health = 1
            self.shoot_delay = 999999999
            self.credits_value = 10
        else: # ASTEROIDS or default
            if self.subtype == 'STANDARD':
                self.name = "Scrap Raider"; self.speed = random.uniform(2.2, 3.0); self.color = RED; self.health = 1; self.shoot_delay = 2200; self.credits_value = 15
            elif self.subtype == 'HEAVY':
                self.name = "Gravity Anchor"; self.speed = random.uniform(1.2, 1.8); self.color = PURPLE; self.health = 5; self.shoot_delay = 2500; self.width, self.height = 38, 38; self.credits_value = 35
            elif self.subtype == 'SCOUT':
                self.name = "Meteor Dart"; self.speed = random.uniform(3.8, 4.8); self.color = (200, 100, 255); self.health = 1; self.shoot_delay = 1600; self.width, self.height = 24, 24; self.credits_value = 25
            else:
                self.name = "Cosmic Corsair"; self.speed = random.uniform(2.4, 3.2); self.color = (255, 0, 255); self.health = 4; self.shoot_delay = 2000; self.credits_value = 30
        # Scale difficulty based on zone index
        zone_keys = ['ASTEROIDS', 'VULCAN', 'AQUARIS', 'NEBULA', 'PLASMA', 'VOID', 'QUANTUM', 'SINGULARITY', 'ORION']
        diff_idx = zone_keys.index(zone) if zone in zone_keys else 0
        if zone == 'TUTORIAL':
            pass
        elif diff_idx > 0:
            self.health = max(1, self.health + diff_idx // 5)
            if self.shoot_delay < 5000000:
                self.shoot_delay = max(700, self.shoot_delay - diff_idx * 55)
            self.speed = self.speed * (1.0 + diff_idx * 0.025)
        else:
            self.health = max(1, self.health)
            if self.shoot_delay < 5000000:
                self.shoot_delay = max(700, self.shoot_delay - 70)
            self.speed = self.speed * 1.12
            
        self.name = ""
        self.max_health = self.health
        if zone in BIOME_CONFIGS and zone not in ('AQUARIS', 'VULCAN', 'ASTEROIDS'):
            self.color = BIOME_CONFIGS[zone]['theme_color']
            
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.velocity = pygame.math.Vector2(0, self.speed)
        self.acceleration = 0.1
        self.drag = 0.98
 
    def update(self, current_time, player, projectiles_list, player_bullets=None, torpedoes=None, obstacles=None, convoy=None):
        if getattr(player, 'is_cloaked', False):
            # Drift aimlessly if player is cloaked
            self.velocity *= self.drag
            self.x += self.velocity.x
            self.y += self.velocity.y
            self.rect.topleft = (int(self.x), int(self.y))
            return # Don't target or shoot

        player_center = pygame.math.Vector2(player.rect.center)
        target_center = player_center
        if convoy and convoy.health > 0:
            c_center = pygame.math.Vector2(convoy.rect.center)
            e_center = pygame.math.Vector2(self.rect.center)
            if e_center.distance_to(c_center) < e_center.distance_to(target_center):
                target_center = c_center

        enemy_center = pygame.math.Vector2(self.rect.center)
        to_player = target_center - enemy_center

        # 1. Ambush / Gimmick Logic
        if self.subtype == 'SCOUT':
            if self.zone == 'ASTEROIDS' and getattr(self, 'is_dormant', False):
                if player_center.distance_to(enemy_center) < 250:
                    self.is_dormant = False
                    self.last_shot = current_time + 400
                else:
                    self.y += 0.5
                    self.rect.y = int(self.y)
                    return
            elif self.zone == 'VOID':
                self.is_invisible = to_player.length() > 300
            elif self.zone == 'NEBULA':
                if (current_time // 2000) % 3 == 0:
                    self.velocity += to_player.normalize() * 0.8
            elif self.zone == 'QUANTUM':
                # Shift Blink Teleport gimmick
                if player_bullets:
                    for b in player_bullets:
                        if pygame.math.Vector2(self.rect.center).distance_to(pygame.math.Vector2(b.x, b.y)) < 80:
                            if random.random() < 0.05: # Rare blink
                                self.x += random.choice([-150, 150])
                                self.y += random.choice([-100, 100])
                                self.rect.topleft = (self.x, self.y)

        # 2. Biome Phasing Gimmicks
        if self.zone == 'QUANTUM' and self.subtype == 'HEAVY':
            # Matrix Wall phases in and out of existence
            self.is_phased = (current_time // 1500) % 2 == 0
        
        if self.zone == 'VOID' and self.subtype == 'HEAVY':
            # Abyss Sentinel Gravity Pull
            dist = to_player.length()
            if dist < 300:
                pull = to_player.normalize() * (0.8 * (1.0 - dist/300))
                player.velocity -= pull

        player_center = pygame.math.Vector2(player.rect.center)
        enemy_center = pygame.math.Vector2(self.rect.center)
        to_player = player_center - enemy_center

        avoid_force = pygame.math.Vector2(0, 0)
        
        # Smooth Evasion Mechanic: Swerve around projectiles
        if player_bullets:
            for bullet in player_bullets:
                bullet_pos = pygame.math.Vector2(bullet.x, bullet.y)
                dist_vec = enemy_center - bullet_pos
                dist = dist_vec.length()
                if 0 < dist < 75 and bullet.dy < 0: # Bullet is moving towards the enemy
                    bullet_dir = pygame.math.Vector2(bullet.dx, bullet.dy)
                    if bullet_dir.length() > 0:
                        perp_dir = pygame.math.Vector2(-bullet_dir.y, bullet_dir.x).normalize()
                        if dist_vec.dot(perp_dir) < 0:
                            perp_dir = -perp_dir
                        avoid_force += perp_dir * (75 - dist) * 0.04
        
        # 2. Solar Skiff Dash Gimmick
        if self.zone == 'VULCAN' and self.subtype == 'SCOUT':
            if current_time - self.last_dash > 2000:
                self.last_dash = current_time
                self.velocity.x += random.choice([-7.0, 7.0])
                
        # 3. Frost Vanguard Deflect Shield Gimmick
        if self.zone == 'AQUARIS' and self.subtype == 'STANDARD':
            self.shield_active = (current_time // 1200) % 2 == 0

        # Improved AI: Smooth Obstacle and Torpedo Avoidance
        threats = []
        if obstacles: threats.extend(obstacles)
        if torpedoes: threats.extend([t for t in torpedoes if not t.exploded])
        for threat in threats:
            dist_vec = enemy_center - pygame.math.Vector2(threat.rect.center)
            dist = dist_vec.length()
            if 0 < dist < 180:
                avoid_force += dist_vec.normalize() * (180 - dist) * 0.04
        self.velocity += avoid_force

        # Pursuit Mode: If player has seen the enemy, is traveling away, and the enemy is off-screen, it gains a pursuit speed boost
        current_speed = self.speed
        current_accel = self.acceleration
        if getattr(self, 'seen', False):
            player_vel = pygame.math.Vector2(player.velocity)
            if player_vel.length() > 0.5:
                to_player_dir = to_player.copy()
                if to_player_dir.length() > 0:
                    is_off_screen = (abs(self.x - player.x) > 600 or abs(self.y - player.y) > 450)
                    if player_vel.dot(to_player_dir) > 0 and is_off_screen:
                        current_speed = max(self.speed, player.max_speed + 0.6)
                        current_accel = self.acceleration * 2.2

        if to_player.length() > 5:
            self.angle = math.degrees(math.atan2(to_player.y, to_player.x))
            accel_dir = to_player.normalize()
            self.velocity += accel_dir * current_accel
        else:
            self.angle = 90.0
            
        self.velocity *= self.drag
        if self.velocity.length() > current_speed:
            self.velocity = self.velocity.normalize() * current_speed
            
        self.x += self.velocity.x
        self.y += self.velocity.y
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
            
        if abs(self.y - target_center.y) < 600:
            if current_time - self.last_shot > self.shoot_delay:
                self.last_shot = current_time
                rad = math.radians(self.angle)
                bullet_dx = math.cos(rad)
                bullet_dy = math.sin(rad)
                spawn_offset = self.width // 2 + 10
                spawn_x, spawn_y = enemy_center.x + bullet_dx * spawn_offset, enemy_center.y + bullet_dy * spawn_offset
                
                # Biome-specific behavior overrides
                if self.zone == 'PLASMA' and self.subtype == 'STANDARD':
                    # Flare Grunt Burst Fire
                    for i in range(3):
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=self.color, speed=8 + i*2, telegraph_frames=i*5))
                    return

                if self.zone == 'NEBULA' and self.subtype == 'STANDARD':
                    # Static Raider Spread
                    for ang in [-15, 0, 15]:
                        dir_vec = pygame.math.Vector2(bullet_dx, bullet_dy).rotate(ang)
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, dir_vec.x, dir_vec.y, color=PURPLE, speed=7))
                    return

                if self.zone == 'SINGULARITY' and self.subtype == 'HEAVY':
                    # Horizon Guard Heavy Gravity Shot
                    projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=BLUE, speed=5, size=12, is_gravity=True, target_player=player))
                    return

                if self.zone == 'SINGULARITY' and self.subtype == 'SCOUT':
                    # Grav-Dart High Velocity
                    projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=CYAN, speed=16, size=5))
                    return

                if self.zone == 'ORION' and self.subtype == 'ELITE':
                    # Imperial Overlord Barrage
                    for ang in range(-30, 31, 10):
                        dir_vec = pygame.math.Vector2(bullet_dx, bullet_dy).rotate(ang)
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, dir_vec.x, dir_vec.y, color=WHITE, speed=9, is_homing=(abs(ang) < 5), target_player=player, shooter=self))
                    return

                # Custom shooting patterns for gimmicks
                if self.zone == 'AQUARIS':
                    if self.subtype == 'HEAVY':
                        # Glacial Sentry: Weak slow tiny bullet
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=(150, 200, 255), speed=2.5, size=4))
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=(150, 200, 255), speed=4.0, size=4))
                    elif self.subtype == 'ELITE':
                        # Snowstorm Skiff Miniboss: 3 spreading lasers
                        for offset in [-15, 0, 15]:
                            r = math.radians(self.angle + offset)
                            projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, math.cos(r), math.sin(r), color=self.color, speed=5, size=8))
                            projectiles_list.append(EnemyBullet(spawn_x, spawn_y, math.cos(r), math.sin(r), color=self.color, speed=9.0, size=8))
                    elif self.subtype == 'SCOUT':
                        pass
                    else:
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=self.color, speed=5, size=7))
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=self.color, speed=9.5, size=7))
                        
                elif self.zone == 'VULCAN':
                    if self.subtype == 'HEAVY':
                        # Magma Bomber: Large slow lava mortar
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=ORANGE, speed=2.5, size=15))
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=ORANGE, speed=4.5, size=15))
                    elif self.subtype == 'ELITE':
                        # Pyro Interceptor Miniboss: Homing missile (Only 1 tracking projectile at a time)
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=RED, speed=8.0, size=9, is_homing=True, target_player=player, life_time=180, shooter=self))
                    else:
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=self.color, speed=6, size=7))
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=self.color, speed=14.0, size=7))
                        
                else: # ASTEROIDS or default
                    if self.subtype == 'HEAVY':
                        # Gravity Anchor: Gravity pull bullet
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=PURPLE, speed=4.5, size=10, is_gravity=True, target_player=player))
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=PURPLE, speed=10.5, size=10, is_gravity=True, target_player=player))
                    elif self.subtype == 'ELITE':
                        # Cosmic Corsair Miniboss: Double laser barrage
                        perp_dx = -bullet_dy
                        perp_dy = bullet_dx
                        projectiles_list.append(EnemyBullet(enemy_center.x - perp_dx * 8, enemy_center.y - perp_dy * 8, bullet_dx, bullet_dy, color=self.color, speed=6, size=7))
                        projectiles_list.append(EnemyBullet(enemy_center.x + perp_dx * 8, enemy_center.y + perp_dy * 8, bullet_dx, bullet_dy, color=self.color, speed=6, size=7))
                        projectiles_list.append(EnemyBullet(spawn_x - perp_dx * 8, spawn_y - perp_dy * 8, bullet_dx, bullet_dy, color=self.color, speed=11.5, size=7))
                        projectiles_list.append(EnemyBullet(spawn_x + perp_dx * 8, spawn_y + perp_dy * 8, bullet_dx, bullet_dy, color=self.color, speed=11.5, size=7))
                    else:
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=self.color, speed=5, size=7))
                        projectiles_list.append(EnemyBullet(spawn_x, spawn_y, bullet_dx, bullet_dy, color=self.color, speed=11.0, size=7))

    def on_death(self, projectiles_list, player):
        if self.zone == 'ASTEROIDS' and self.subtype == 'STANDARD':
            # Scrap Raider: Spawns 4 diagonal scrap debris bullets on death
            for dx, dy in [(-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7), (0.7, 0.7)]:
                projectiles_list.append(EnemyBullet(self.rect.centerx, self.rect.centery, dx, dy, color=(160, 160, 160), speed=3.5, size=5))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        # Stealth / Ambush visuals
        if getattr(self, 'is_invisible', False):
            return
        
        # Quantum Phasing Visuals
        if getattr(self, 'is_phased', False) and pygame.time.get_ticks() % 200 < 100:
            return
        if self.zone == 'ASTEROIDS' and self.subtype == 'SCOUT' and self.is_dormant:
            draw_y = self.y - camera_y
            pygame.draw.circle(screen, (80, 80, 80), (int(draw_x + self.width // 2), int(draw_y + self.height // 2)), 12, width=1)
            return

        draw_y = self.y - camera_y
        if 0 <= draw_x <= VIRTUAL_WIDTH and 0 <= draw_y <= VIRTUAL_HEIGHT:
            self.seen = True
        center_x = draw_x + self.width // 2
        center_y = draw_y + self.height // 2
        center = pygame.math.Vector2(center_x, center_y)
        
        # Directions based on self.angle (calculated to face the player)
        rad = math.radians(self.angle)
        dir_f = pygame.math.Vector2(math.cos(rad), math.sin(rad)) # forward
        dir_r = pygame.math.Vector2(-dir_f.y, dir_f.x) # right
        
        # 1. Back engine flame
        flame_len = 8 + random.randint(0, 6)
        rear_center = center - dir_f * (self.height // 2)
        pygame.draw.polygon(screen, RED, [rear_center, rear_center - dir_r * 6, rear_center - dir_f * flame_len, rear_center + dir_r * 6], width=1)
        
        # 2. WINGS
        lw_tip = center - dir_f * 5 - dir_r * (self.width // 2)
        lw_base_in = center - dir_f * (self.height // 2) - dir_r * 5
        lw_base_out = center - dir_f * (self.height // 3) - dir_r * (self.width // 2)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, lw_tip, lw_base_out, lw_base_in])
        
        rw_tip = center - dir_f * 5 + dir_r * (self.width // 2)
        rw_base_in = center - dir_f * (self.height // 2) + dir_r * 5
        rw_base_out = center - dir_f * (self.height // 3) + dir_r * (self.width // 2)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, rw_tip, rw_base_out, rw_base_in])

        # 3. MAIN HULL (Triangle shape)
        hull_tip = center + dir_f * (self.height // 2)
        hull_left = center - dir_f * (self.height // 4) - dir_r * (self.width // 5)
        hull_right = center - dir_f * (self.height // 4) + dir_r * (self.width // 5)
        pygame.draw.polygon(screen, self.color, [hull_tip, hull_left, hull_right])

        # 4. COCKPIT GLASS
        glass_tip = center + dir_f * (self.height // 3)
        glass_left = center + dir_f * (self.height // 8) - dir_r * (self.width // 10)
        glass_right = center + dir_f * (self.height // 8) + dir_r * (self.width // 10)
        pygame.draw.polygon(screen, WHITE, [glass_tip, glass_left, glass_right])
        
        # Muzzle Flash when shooting
        ticks = pygame.time.get_ticks()
        if ticks - self.last_shot < 120:
            tip_x = center.x + dir_f.x * (self.height // 2 + 10)
            tip_y = center.y + dir_f.y * (self.height // 2 + 10)
            pygame.draw.circle(screen, self.color, (int(tip_x), int(tip_y)), 16, width=2)
            pygame.draw.circle(screen, WHITE, (int(tip_x), int(tip_y)), 8)
            pygame.draw.line(screen, WHITE, (int(tip_x - 12), int(tip_y)), (int(tip_x + 12), int(tip_y)), 2)
            pygame.draw.line(screen, WHITE, (int(tip_x), int(tip_y - 12)), (int(tip_x), int(tip_y + 12)), 2)
        
        # Vulcan Scout Trail Gimmick (Fire Trail)
        if self.zone == 'VULCAN' and self.subtype == 'STANDARD':
            if random.random() < 0.4:
                tx = int(rear_center.x + random.randint(-4, 4))
                ty = int(rear_center.y + random.randint(-4, 4))
                pygame.draw.circle(screen, ORANGE, (tx, ty), random.randint(2, 4))

        # Frost Vanguard active deflect shield rendering
        if getattr(self, 'shield_active', False):
            glow = int(2 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.circle(screen, CYAN, (int(center.x), int(center.y)), self.width + 4 + glow, width=2)
        
        # 5. Health Bar and Name Tag
        has_health_bar = self.max_health > 1
        if has_health_bar and self.health > 0:
            draw_rect = pygame.Rect(draw_x, draw_y, self.width, self.height)
            pygame.draw.rect(screen, BLACK, (draw_rect.x, draw_rect.y - 6, self.width, 4))
            health_ratio = max(0.0, min(1.0, self.health / self.max_health))
            pygame.draw.rect(screen, GREEN, (draw_rect.x, draw_rect.y - 6, int(self.width * health_ratio), 4))
            
            pass

class Meteor:
    def __init__(self, x, y, speed_y=None, speed_x=None, is_static=False):
        self.size = random.randint(40, 80)
        self.x = x
        self.y = y
        self.is_static = is_static
        
        if is_static:
            self.speed_y = 0
            self.speed_x = 0
            self.credits_value = 0
        else:
            self.speed_y = speed_y if speed_y is not None else random.uniform(0.8, 2.2)
            self.speed_x = speed_x if speed_x is not None else random.uniform(-0.8, 0.8)
            self.credits_value = 0
            
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        
        self.points = []
        num_points = 8
        for i in range(num_points):
            angle = (i / num_points) * 2 * 3.14159
            radius = random.uniform(self.size // 3, self.size // 2)
            px = self.size // 2 + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x
            py = self.size // 2 + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y
            self.points.append((px, py))

    def update(self):
        if not self.is_static:
            self.x += self.speed_x
            self.y += self.speed_y
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        draw_points = [(p[0] + draw_x, p[1] + draw_y) for p in self.points]
        color = SLATE_GRAY if self.is_static else GRAY
        
        # 1. Fill the main asteroid body with brighter rocky tones
        body_color = (80, 80, 85) if self.is_static else (110, 110, 115)
        pygame.draw.polygon(screen, body_color, draw_points)
        
        # Outer highlighted rim border to stand out against background space
        border_color = (150, 150, 160) if self.is_static else (200, 200, 210)
        pygame.draw.polygon(screen, border_color, draw_points, width=2)
        
        # 2. Draw crater textures
        if not hasattr(self, 'craters'):
            random.seed(int(self.x * 1000 + self.y))
            self.craters = []
            for _ in range(3):
                cx = random.uniform(self.size * 0.3, self.size * 0.7)
                cy = random.uniform(self.size * 0.3, self.size * 0.7)
                cr = random.uniform(self.size * 0.1, self.size * 0.2)
                self.craters.append((cx, cy, cr))
            random.seed()
            
        for cx, cy, cr in self.craters:
            spot_color = (55, 55, 60) if self.is_static else (85, 85, 90)
            pygame.draw.circle(screen, spot_color, (int(draw_x + cx), int(draw_y + cy)), int(cr))
            rim_color = (105, 105, 115) if self.is_static else (145, 145, 155)
            pygame.draw.circle(screen, rim_color, (int(draw_x + cx), int(draw_y + cy)), int(cr), width=1)
            
class FactoryStructure:
    def __init__(self, x, y, width=120, height=120):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.size = width # Alias for size compatibility
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.is_static = True
        self.credits_value = 15
        self.health = 5.0 # Takes a few standard shots to destroy!
        self.color = (60, 60, 65)

    def update(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Outer wireframe box
        pygame.draw.rect(screen, BLUE, (draw_x, draw_y, self.width, self.height), width=1)
        # Inner wireframe box
        pygame.draw.rect(screen, (0, 100, 200), (draw_x + 10, draw_y + 10, self.width - 20, self.height - 20), width=1)
        # Cross lines for structural truss
        pygame.draw.line(screen, (0, 60, 120), (draw_x, draw_y), (draw_x + self.width, draw_y + self.height), 1)
        pygame.draw.line(screen, (0, 60, 120), (draw_x + self.width, draw_y), (draw_x, draw_y + self.height), 1)
        
        # Pulsing center core node
        pulse = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.006))
        core_color = (0, pulse // 2, pulse)
        pygame.draw.circle(screen, core_color, (int(draw_x + self.width // 2), int(draw_y + self.height // 2)), 6)

class Material:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 16
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self, screen, camera_y, camera_x=0):
        ticks = pygame.time.get_ticks()
        glow = int(4 * math.sin(ticks * 0.015))
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        pygame.draw.circle(screen, ORANGE, (int(draw_x), int(draw_y)), self.radius + glow, width=2)
        pygame.draw.circle(screen, PURPLE, (int(draw_x), int(draw_y)), self.radius - 2)
        pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), 5)

class Scrap:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self, screen, camera_y, camera_x=0):
        ticks = pygame.time.get_ticks()
        glow = int(3 * math.sin(ticks * 0.02))
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        pygame.draw.circle(screen, GRAY, (int(draw_x), int(draw_y)), self.radius + glow, width=2)
        pygame.draw.circle(screen, GOLD, (int(draw_x), int(draw_y)), self.radius - 3)
        pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), 3)

class GasCloud:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = random.randint(250, 600)
        self.color = color
        
        # Generate value noise in a low-resolution grid
        # Octave 1: 10x10 grid (large structural features)
        # Octave 2: 20x20 grid (fine cloud details)
        grid_size = 20
        surf_low = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
        center = (grid_size - 1) / 2.0
        max_dist = (grid_size - 1) / 2.0
        
        # Subtle translucent base alpha but clearly visible
        max_alpha = random.randint(50, 90)
        
        # Pre-generate noise tables
        noise_grid_1 = [[random.uniform(0.4, 1.0) for _ in range(grid_size // 2)] for _ in range(grid_size // 2)]
        noise_grid_2 = [[random.uniform(0.3, 1.0) for _ in range(grid_size)] for _ in range(grid_size)]
        
        for gx in range(grid_size):
            for gy in range(grid_size):
                dx = gx - center
                dy = gy - center
                dist = math.hypot(dx, dy)
                
                if dist >= max_dist:
                    falloff = 0.0
                else:
                    falloff = 1.0 - (dist / max_dist)
                    # Smooth step falloff for soft edges
                    falloff = falloff * falloff * (3.0 - 2.0 * falloff)
                
                # Fetch low and high frequency noise values
                n1 = noise_grid_1[min(gx // 2, len(noise_grid_1) - 1)][min(gy // 2, len(noise_grid_1[0]) - 1)]
                n2 = noise_grid_2[gx][gy]
                
                # Blend octaves (60% low frequency, 40% high frequency)
                combined_noise = n1 * 0.6 + n2 * 0.4
                
                alpha = int(max_alpha * falloff * combined_noise)
                surf_low.set_at((gx, gy), (*self.color, alpha))
                
        # Bilinearly upscale the low-res noise surface to the final cloud size
        self.surf = pygame.transform.smoothscale(surf_low, (self.radius * 2, self.radius * 2))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        if -self.radius < draw_x < VIRTUAL_WIDTH + self.radius and -self.radius < draw_y < VIRTUAL_HEIGHT + self.radius:
            screen.blit(self.surf, (int(draw_x - self.radius), int(draw_y - self.radius)))

class AmbientDebris:
    def __init__(self, x, y, dx=None, dy=None):
        self.x = x
        self.y = y
        self.dx = dx if dx is not None else random.uniform(-0.5, 0.5)
        self.dy = dy if dy is not None else random.uniform(-0.5, 0.5)
        self.size = random.randint(1, 3)
        self.color = random.choice([(150, 150, 150), (100, 100, 100), (80, 80, 80)])

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        pygame.draw.rect(screen, self.color, (int(draw_x), int(draw_y), self.size, self.size))

class DerelictHull:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = random.randint(60, 100)
        self.height = random.randint(40, 70)
        self.health = 5
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        self.angle = random.uniform(0, 360)

    def update(self):
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (70, 50, 40), (0, 0, self.width, self.height), border_radius=6)
        pygame.draw.line(surf, (40, 20, 10), (0, self.height//2), (self.width, self.height//2), 3)
        pygame.draw.circle(surf, (30, 15, 10), (self.width//2, self.height//2), 10)
        
        rot_surf = pygame.transform.rotate(surf, self.angle)
        screen.blit(rot_surf, (int(draw_x - rot_surf.get_width()//2), int(draw_y - rot_surf.get_height()//2)))

class Anomaly:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 25
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self):
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        pulse = int(6 * math.sin(ticks * 0.01))
        pygame.draw.circle(screen, MAGENTA, (int(draw_x), int(draw_y)), self.radius + pulse, width=3)
        pygame.draw.circle(screen, (200, 50, 255), (int(draw_x), int(draw_y)), max(1, self.radius - 10 + pulse))
        pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), max(1, self.radius - 18))

class ConvoyShip:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 68
        self.height = 100
        self.health = 100.0
        self.max_health = 100.0
        self.speed = 2.0
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)

    def update(self):
        self.y -= self.speed
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        
        # 1. Side engine nacelles/wings
        pygame.draw.rect(screen, (70, 80, 100), (int(draw_x - 34), int(draw_y - 15), 10, 45), border_radius=3)
        pygame.draw.rect(screen, (70, 80, 100), (int(draw_x + 24), int(draw_y - 15), 10, 45), border_radius=3)
        
        # 2. Main industrial hull core
        pygame.draw.rect(screen, (90, 95, 110), (int(draw_x - 18), int(draw_y - 35), 36, 65), border_radius=5)
        # Cargo containers on ship body
        pygame.draw.rect(screen, GOLD, (int(draw_x - 12), int(draw_y - 15), 24, 30))
        # Hull lining accents
        pygame.draw.line(screen, CYAN, (draw_x - 18, draw_y - 25), (draw_x + 18, draw_y - 25), 2)
        pygame.draw.line(screen, CYAN, (draw_x - 18, draw_y + 15), (draw_x + 18, draw_y + 15), 2)
        
        # 3. Cockpit / Head of the ship (sleek triangle bow)
        pygame.draw.polygon(screen, (110, 115, 130), [
            (draw_x, draw_y - 50),
            (draw_x - 18, draw_y - 35),
            (draw_x + 18, draw_y - 35)
        ])
        # Cyan visor
        pygame.draw.polygon(screen, CYAN, [
            (draw_x, draw_y - 46),
            (draw_x - 8, draw_y - 38),
            (draw_x + 8, draw_y - 38)
        ])
        
        # 4. Engine thrumming plumes (flickering nacelle flame trails)
        flame_len1 = 12 + int(6 * math.sin(ticks * 0.05))
        flame_len2 = 12 + int(6 * math.cos(ticks * 0.05))
        pygame.draw.polygon(screen, ORANGE, [(draw_x - 33, draw_y + 30), (draw_x - 25, draw_y + 30), (draw_x - 29, draw_y + 30 + flame_len1)])
        pygame.draw.polygon(screen, ORANGE, [(draw_x + 25, draw_y + 30), (draw_x + 33, draw_y + 30), (draw_x + 29, draw_y + 30 + flame_len2)])
        
        bar_w = 60
        bar_h = 6
        bx = draw_x - bar_w // 2
        by = draw_y - 62
        pygame.draw.rect(screen, RED, (bx, by, bar_w, bar_h))
        pygame.draw.rect(screen, GREEN, (bx, by, int(bar_w * max(0.0, self.health / self.max_health)), bar_h))
        pygame.draw.rect(screen, WHITE, (bx, by, bar_w, bar_h), width=1)

class QuantumAnchor:
    def __init__(self, x, y, index):
        self.x = x
        self.y = y
        self.index = index
        self.health = 30.0
        self.max_health = 30.0
        self.width = 32
        self.height = 32
        self.rect = pygame.Rect(self.x - 16, self.y - 16, 32, 32)
        
    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        
        points = []
        for i in range(4):
            ang = math.radians(i * 90 + ticks * 0.08)
            r = 16 + int(3 * math.sin(ticks * 0.01 + i))
            points.append((draw_x + r * math.cos(ang), draw_y + r * math.sin(ang)))
        pygame.draw.polygon(screen, GREEN, points, width=2)
        pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), 6)
        
        bar_w = 40
        bar_h = 4
        bx = draw_x - bar_w // 2
        by = draw_y - 24
        pygame.draw.rect(screen, RED, (bx, by, bar_w, bar_h))
        pygame.draw.rect(screen, GREEN, (bx, by, int(bar_w * max(0.0, self.health / self.max_health)), bar_h))
        pygame.draw.rect(screen, WHITE, (bx, by, bar_w, bar_h), width=1)

class EnergyCell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.rect = pygame.Rect(self.x - 12, self.y - 12, self.width, self.height)

    def update(self):
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        pulse = int(4 * math.sin(ticks * 0.02))
        pygame.draw.circle(screen, GOLD, (int(draw_x), int(draw_y)), 10 + pulse)
        pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), 5)

class BlackHoleCore:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 120
        self.height = 120
        self.health = 80.0
        self.max_health = 80.0
        self.rect = pygame.Rect(self.x - 60, self.y - 60, self.width, self.height)
        self.pull_force = 1.2
        self.last_shot = 0

    def update(self, player, bullets, game_instance):
        p_pos = pygame.math.Vector2(player.x + player.width // 2, player.y + player.height // 2)
        core_pos = pygame.math.Vector2(self.x, self.y)
        dist = p_pos.distance_to(core_pos)
        if dist < 400 and dist > 20:
            pull = (core_pos - p_pos).normalize() * (self.pull_force * (1.0 - dist / 400.0))
            player.x += pull.x
            player.y += pull.y
            player.rect.topleft = (player.x, player.y)

        ticks = pygame.time.get_ticks()
        if ticks - self.last_shot > 1500:
            self.last_shot = ticks
            if game_instance:
                for i in range(8):
                    ang = i * (2 * math.pi / 8)
                    dx = math.cos(ang)
                    dy = math.sin(ang)
                    game_instance.enemy_bullets.append(
                        EnemyBullet(self.x, self.y, dx, dy, color=GREEN, speed=5.0, size=8)
                    )

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        
        for i in range(3):
            r = 30 + i * 15 + int(6 * math.sin(ticks * 0.01 + i))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            color = (0, 200, 100, 160 - i * 40)
            pygame.draw.circle(surf, color, (r, r), r, width=3)
            screen.blit(surf, (int(draw_x - r), int(draw_y - r)))
            
        pygame.draw.circle(screen, BLACK, (int(draw_x), int(draw_y)), 15)
        
        bar_w = 80
        bar_h = 8
        bx = draw_x - bar_w // 2
        by = draw_y - 70
        pygame.draw.rect(screen, RED, (bx, by, bar_w, bar_h))
        pygame.draw.rect(screen, GREEN, (bx, by, int(bar_w * max(0.0, self.health / self.max_health)), bar_h))
        pygame.draw.rect(screen, WHITE, (bx, by, bar_w, bar_h), width=1)

class QuantumPortal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 35
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self):
        pass

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        ticks = pygame.time.get_ticks()
        
        glow = int(4 * math.sin(ticks * 0.02))
        color = GREEN if (ticks // 1000) % 2 == 0 else WHITE
        pygame.draw.circle(screen, color, (int(draw_x), int(draw_y)), self.radius + glow, width=2)
        pygame.draw.circle(screen, (0, 150, 50, 100), (int(draw_x), int(draw_y)), self.radius - 5)

class BackgroundStructure:
    def __init__(self, zone):
        self.zone = zone
        self.x = VIRTUAL_WIDTH // 2
        self.y = -3500  # Deep into the level
        self.color = BIOME_CONFIGS.get(zone, {}).get('theme_color', GRAY)
        
    def draw(self, screen, camera_y, camera_x):
        draw_x = self.x - camera_x * 0.05
        draw_y = self.y - camera_y * 0.05
        ticks = pygame.time.get_ticks()
        
        surf = pygame.Surface((1200, 1200), pygame.SRCALPHA)
        cx, cy = 600, 600
        
        if self.zone == 'SINGULARITY':
            # Wireframe fusion core
            pygame.draw.circle(surf, self.color, (cx, cy), 150, width=1)
            pygame.draw.circle(surf, self.color, (cx, cy), 155, width=2)
            for i in range(3):
                ang = ticks * 0.001 + i
                pygame.draw.ellipse(surf, self.color, (cx - 300, cy - 50, 600, 100), width=1)
            pygame.draw.rect(surf, self.color, (cx - 400, cy - 20, 200, 40), width=1)
            pygame.draw.rect(surf, self.color, (cx + 200, cy - 20, 200, 40), width=1)
        elif self.zone == 'ORION':
            # Wireframe Orion Citadel
            pygame.draw.polygon(surf, self.color, [(cx, cy-400), (cx-200, cy+200), (cx+200, cy+200)], width=1)
            pygame.draw.polygon(surf, self.color, [(cx, cy-300), (cx-100, cy+200), (cx+100, cy+200)], width=1)
            pygame.draw.line(surf, self.color, (cx, cy-400), (cx, cy+200), 1)
        elif self.zone == 'ASTEROIDS':
            # Wireframe Space Elevator
            pygame.draw.rect(surf, self.color, (cx - 80, cy - 600, 160, 1200), width=1)
            pygame.draw.rect(surf, self.color, (cx - 30, cy - 600, 60, 1200), width=1)
            for dy in range(-600, 600, 120):
                pygame.draw.line(surf, self.color, (cx - 80, cy + dy), (cx + 80, cy + dy + 120), 1)
                pygame.draw.line(surf, self.color, (cx + 80, cy + dy), (cx - 80, cy + dy + 120), 1)
            pygame.draw.circle(surf, (255, 100, 0), (cx, cy+100), 80, width=2)
            pygame.draw.circle(surf, WHITE, (cx, cy+100), 10)
        elif self.zone == 'VOID':
            pygame.draw.ellipse(surf, self.color, (cx - 300, cy - 150, 600, 300), width=2)
            pygame.draw.circle(surf, self.color, (cx, cy), 130, width=1)
            pygame.draw.line(surf, self.color, (cx, cy-120), (cx, cy+120), 1)
        elif self.zone == 'QUANTUM':
            for r in [100, 200, 350]:
                ang = ticks * 0.0005 * (1 if r == 200 else -1)
                pts = [(cx + r*math.cos(ang + i*math.pi/2), cy + r*math.sin(ang + i*math.pi/2)) for i in range(4)]
                pygame.draw.polygon(surf, self.color, pts, width=1)
                pygame.draw.circle(surf, self.color, (cx, cy), r, width=1)
        elif self.zone == 'PLASMA':
            pygame.draw.circle(surf, self.color, (cx, cy), 200, width=2)
            pygame.draw.circle(surf, self.color, (cx, cy), 100, width=1)
            pygame.draw.rect(surf, self.color, (cx - 300, cy - 10, 600, 20), width=1)
            pygame.draw.rect(surf, self.color, (cx - 10, cy - 300, 20, 600), width=1)
        elif self.zone == 'NEBULA':
            pygame.draw.polygon(surf, self.color, [(cx-150, cy-200), (cx+150, cy-200), (cx, cy+200)], width=1)
            if ticks % 800 < 150:
                pygame.draw.line(surf, WHITE, (cx, cy+200), (cx + random.randint(-150, 150), cy + 500), 2)
        elif self.zone == 'AQUARIS':
            # Wireframe Ice Spires
            pygame.draw.polygon(surf, self.color, [(cx, cy-500), (cx-150, cy+300), (cx+150, cy+300)], width=1)
            pygame.draw.polygon(surf, self.color, [(cx, cy-400), (cx-100, cy+300), (cx+100, cy+300)], width=1)
            pygame.draw.line(surf, self.color, (cx, cy-500), (cx, cy+300), 1)
            pygame.draw.line(surf, self.color, (cx-150, cy+300), (cx+150, cy+300), 1)
        elif self.zone == 'VULCAN':
            # Solar forge wireframe
            pygame.draw.circle(surf, self.color, (cx, cy), 350, width=1)
            pygame.draw.circle(surf, self.color, (cx, cy), 200, width=1)
            for angle in range(0, 360, 30):
                rad = math.radians(angle + ticks * 0.005)
                pygame.draw.line(surf, self.color, (cx + 200 * math.cos(rad), cy + 200 * math.sin(rad)), (cx + 350 * math.cos(rad), cy + 350 * math.sin(rad)), 1)
            
        screen.blit(surf, (draw_x - cx, draw_y - cy))

class Player:
    def __init__(self):
        self.width = 40
        self.height = 40
        self.name = ""
        self.reset()

    def reset(self):
        self.x = VIRTUAL_WIDTH // 2 - self.width // 2
        self.y = 600  # Start altitude
        self.speed = 5
        self.speed_multiplier = 1.0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.last_shot = 0
        self.shoot_delay = 150
        self.last_torpedo = 0
        self.last_secondary = 0
        self.torpedo_delay = 1000
        self.direction = pygame.math.Vector2(0, -1)
        self.angle = 270.0  # angle in degrees, pointing straight up (270)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = 0.35
        self.max_speed = 7.0
        self.rotation_speed = 4.0  # degrees per frame
        self.drag = 0.96  # gradual momentum decay (friction)
        
        # Heat mechanics
        self.heat = 0.0
        self.max_heat = 100.0
        self.overheated = False
        self.heat_per_shot = 6.0
        self.cool_rate = 0.45
        
        # Death mechanics
        self.is_dead = False
        self.death_time = 0
        
        # Economy & Progression
        self.credits = 0
        self.scraps = 0
        self.level = 1
        self.xp = 0
        self.skill_points = 0
        self.class_name = 'RANGER'
        self.base_max_shields = 3
        self.damage_multiplier = 1.0
        self.cool_rate_bonus = 0.0
        self.loot_bonus = 0.0
        self.shield_bonus = 0.0
        
        # Upgrade Part Levels
        self.skills = {
            'shield': 0,          # Max 4 (Base 1 shield capacity, upgrades up to 5)
            'deflector': 0,       # Max 1 (Deflector Shielding. Regen delay: 5s -> 3s)
            'coolant': 0,         # Max 4 (Standard gun cools down +25% faster per level)
            'weapon': 0,          # Max 1 (0: Single, 1: Double)
            'overcharge': 0,      # Max 1 (Overcharged Capacitors. Shoot delay -30%)
            'torpedo': 0,         # Max 4 (-15% cooldown, +15% explosion size per level)
            'cluster_torpedo': 0, # Max 1 (Cluster Torpedo Warhead. Spawns sub-explosions)
            'hyperdrive': 0,      # Max 1 (Hyperdrive Core. Warp charge: 3s -> 1s)
            'shotgun_unlocked': 0,
            'shotgun_mod': 0,     # Max 3 (Shotgun Heat -15%, Damage +15% per rank)
            'railgun_unlocked': 0,
            'railgun_mod': 0,     # Max 3 (Railgun Delay -15% per rank)
            'bomb_unlocked': 0,
            'bomb_cap': 0,        # Max 3 (Bomb Max Ammo +2, Radius +15% per rank)
            'missile_unlocked': 0,
            'missile_cap': 0,     # Max 3 (Missile Max Ammo +3, Speed +15% per rank)
            
            'class_tier1': 0,     # Unique Tier 1 class upgrade (Max 3)
            'class_tier2': 0,     # Unique Tier 2 class upgrade (Max 3)
            'class_tier3': 0,     # Unique Tier 3 class ultimate (Max 1)
            
            'afterburner': 0,     # Max 3 (Dash speed +20% per level)
            'vector_nozzle': 0,   # Max 3 (Rotation speed +20% per level)
            'emergency_recharge': 0, # Max 2 (Regen 50% shield once per run)
            'nanite_repair': 0,   # Max 3 (Hull regen: 0.1/s per level)
            'ammo_loader': 0      # Max 3 (+2 max ammo for secondary weapons)
        }
        
        # Equipped non-weapon slots
        self.equipped_shield = 'shield'
        self.equipped_core = 'coolant'
        self.equipped_engine = 'afterburner'
        
        # Weapon Switching and Ammo Stats
        self.active_primary = 0 # 0: Laser, 1: Shotgun, 2: Railgun
        self.active_secondary = 0 # 0: Torpedo, 1: Bomb, 2: Missile
        
        self.max_torpedo_ammo = 10
        self.torpedo_ammo = 10
        self.max_bomb_ammo = 10
        self.bomb_ammo = 10
        self.max_missile_ammo = 8
        self.missile_ammo = 8
        
        # Shield health stats
        self.max_shields = 3
        self.shields = self.max_shields
        self.invulnerable = False
        self.invulnerable_time = 0
        self.invulnerable_duration = 1000
        self.last_hit_time = 0
        self.shield_regen_delay = 5000 # Default value
        self.debug_invincible = False
        self.last_regen_time = 0
        self.regen_cooldown = 3000
        
        # Special Abilities
        self.last_ability = -20000
        self.ability_cooldown = 15000
        self.ability_timer = 0
        self.last_special = -30000
        self.special_cooldown = 20000
        self.special_timer = 0
        
        # Flares
        self.flare_ammo = 10
        self.max_flare_ammo = 10
        self.last_flare_time = 0
        self.flare_cooldown = 5000 # 5 seconds
        
        # Dash evading mechanics
        self.last_dash = 0
        self.dash_cooldown = 1000
        self.is_cloaked = False
        self.banking_amount = 0.0 # -1.0 to 1.0 based on turn sharpess
        
        # Shield bubble & Weapon Modifiers states
        self.shield_bubble_timer = 0
        self.has_mod_piercing = False
        self.has_mod_split = False
        self.has_mod_siphon = False

    def get_active_skill(self, key):
        base_weapon_map = {
            'overcharge': 'weapon',
            'shotgun_mod': 'shotgun_unlocked',
            'railgun_mod': 'railgun_unlocked',
            'cluster_torpedo': 'torpedo',
            'bomb_cap': 'bomb_unlocked',
            'missile_cap': 'missile_unlocked'
        }
        actual_key = base_weapon_map.get(key or "", key or "")
        slots_map = {
            'shield': 'SHIELD', 'deflector': 'SHIELD', 'emergency_recharge': 'SHIELD',
            'coolant': 'CORE', 'nanite_repair': 'CORE', 'class_tier1': 'CORE', 'class_tier2': 'CORE', 'class_tier3': 'CORE',
            'afterburner': 'ENGINE', 'vector_nozzle': 'ENGINE', 'hyperdrive': 'ENGINE',
            'weapon': 'PRIMARY', 'shotgun_unlocked': 'PRIMARY', 'railgun_unlocked': 'PRIMARY',
            'torpedo': 'SECONDARY', 'bomb_unlocked': 'SECONDARY', 'missile_unlocked': 'SECONDARY'
        }
        slot = slots_map.get(actual_key)
        if slot:
            if slot == 'SHIELD' and getattr(self, 'equipped_shield', '') != actual_key: return 0
            if slot == 'CORE' and getattr(self, 'equipped_core', '') != actual_key: return 0
            if slot == 'ENGINE' and getattr(self, 'equipped_engine', '') != actual_key: return 0
            if slot == 'PRIMARY':
                eq_p = {0: 'weapon', 1: 'shotgun_unlocked', 2: 'railgun_unlocked'}.get(self.active_primary)
                if eq_p != actual_key: return 0
            if slot == 'SECONDARY':
                eq_s = {0: 'torpedo', 1: 'bomb_unlocked', 2: 'missile_unlocked'}.get(self.active_secondary)
                if eq_s != actual_key: return 0
        return self.skills.get(key, 0)

    def set_class(self, class_name):
        self.class_name = class_name
        t1 = self.get_active_skill('class_tier1')
        t2 = self.get_active_skill('class_tier2')
        t3 = self.get_active_skill('class_tier3')
        
        if class_name == 'RANGER':
            self.damage_multiplier = 1.3
            self.max_speed = 9.8 + (t1 * 0.5)
            self.base_max_shields = 3
            self.cool_rate = 0.45
            self.acceleration = 0.5
            self.shoot_delay = 150
            self.bullet_speed = 22
            self.heat_per_shot = 5.0
            self.bullet_color = CYAN
            self.dash_cooldown = max(400, 1000 - (t2 * 200))
            self.ability_duration_mod = 1.0 if t3 == 0 else 2.0
            self.class_upgrades = {
                'tier1_name': 'Advanced Thrusters', 'tier1_desc': '+Speed per rank.',
                'tier2_name': 'Evasion Jets', 'tier2_desc': 'Reduces Dash cooldown.',
                'tier3_name': 'Infinite Overdrive', 'tier3_desc': 'Overdrive lasts twice as long.',
                'special_name': 'Afterburner', 'special_desc': 'Temporary massive speed boost.'
            }
        elif class_name == 'ENGINEER':
            self.damage_multiplier = 1.0
            self.max_speed = 8.8
            self.base_max_shields = 4 + t1
            self.cool_rate = 0.8 + (t2 * 0.2)
            self.acceleration = 0.45
            self.shoot_delay = 180
            self.bullet_speed = 20
            self.heat_per_shot = 3.5
            self.bullet_color = GOLD
            self.shield_regen_delay = 5000 if t3 == 0 else 2000
            self.class_upgrades = {
                'tier1_name': 'Heavy Plating', 'tier1_desc': '+Max Shields per rank.',
                'tier2_name': 'System Overclock', 'tier2_desc': 'Increases drone fire rate.',
                'tier3_name': 'Rapid Recharger', 'tier3_desc': 'Sentry Drones last 50% longer.',
                'special_name': 'System Flush', 'special_desc': 'Instantly restore shield and clear heat.'
            }
        elif class_name == 'VANGUARD':
            self.damage_multiplier = 0.9
            self.max_speed = 7.8
            self.base_max_shields = 6 + t1
            self.cool_rate = 0.35
            self.acceleration = 0.35
            self.shoot_delay = 220
            self.bullet_speed = 17
            self.heat_per_shot = 7.0
            self.bullet_color = MAGENTA
            self.ability_cooldown_mod = 1.0 if t2 == 0 else 0.7
            self.dash_damage = 0 if t3 == 0 else 5.0
            self.class_upgrades = {
                'tier1_name': 'Titanium Hull', 'tier1_desc': '+Max Shields per rank.',
                'tier2_name': 'Hardened Lattice', 'tier2_desc': 'Increases Guardian Crystal health.',
                'tier3_name': 'Kinetic Ram', 'tier3_desc': 'Dashing damages enemies you hit.',
                'special_name': 'Titan Pulse', 'special_desc': 'Unleash a massive invulnerability shockwave.'
            }
        elif class_name == 'SNIPER':
            self.damage_multiplier = 1.8 + (t1 * 0.4)
            self.max_speed = 10.5
            self.base_max_shields = 2
            self.cool_rate = 0.3
            self.acceleration = 0.4
            self.shoot_delay = 350
            self.bullet_speed = 38
            self.heat_per_shot = 9.0
            self.bullet_color = YELLOW
            self.bullet_speed_mod = 1.0 + (t2 * 0.2)
            self.airstrike_count = 2 if t3 == 0 else 4
            self.class_upgrades = {
                'tier1_name': 'Rail Accelerators', 'tier1_desc': '+Damage multiplier per rank.',
                'tier2_name': 'Target Lock', 'tier2_desc': '+Bullet speed per rank.',
                'tier3_name': 'Orbital Fleet', 'tier3_desc': 'Airstrike spawns 4 ships instead of 2.',
                'special_name': 'Missile Swarm', 'special_desc': 'Fires 4 homing missiles.'
            }
        elif class_name == 'ASSASSIN':
            self.damage_multiplier = 1.1 + (t3 * 0.5)
            self.max_speed = 12.0 + (t1 * 0.5)
            self.base_max_shields = 2
            self.cool_rate = 0.6
            self.acceleration = 0.65
            self.shoot_delay = 110
            self.bullet_speed = 25
            self.heat_per_shot = 4.0
            self.bullet_color = PURPLE
            self.cloak_duration = 2000 + (t2 * 500)
            self.specialist_weapon_name = "VENOM NEEDLE"
            self.class_upgrades = {
                'tier1_name': 'Shadow Engines', 'tier1_desc': '+Speed per rank.',
                'tier2_name': 'Stealth Capacitors', 'tier2_desc': '+Cloak duration per rank.',
                'tier3_name': 'Critical Ambush', 'tier3_desc': 'Massively increases damage.',
                'special_name': 'Warp Strike', 'special_desc': 'Teleports forward and clears heat.'
            }
            
        self.max_shields = self.base_max_shields + self.get_active_skill('shield')
        self.shields = min(self.shields, self.max_shields)

    def award_xp(self, amount):
        if self.is_dead:
            return
        self.xp += int(amount)
        while self.xp >= self.xp_to_next_level():
            self.xp -= self.xp_to_next_level()
            self.level += 1
            self.skill_points += 1
            self.max_shields = max(3, self.max_shields + 1)
            self.shields = min(self.max_shields, self.shields + 1)

    def xp_to_next_level(self):
        return 120 + (self.level - 1) * 35

    def apply_loot(self, loot):
        for stat, value in loot.effects:
            if stat == 'shield':
                self.max_shields += 1
                self.shields = min(self.max_shields, self.shields + 1)
            elif stat == 'cooldown':
                self.cool_rate_bonus += value
            elif stat == 'damage':
                self.damage_multiplier += value

    def add_credits(self, amount):
        if self.is_dead:
            return
        self.credits += amount

    def update_regen(self, current_time):
        if self.is_dead:
            return
        
        if self.invulnerable and current_time - self.invulnerable_time > self.invulnerable_duration:
            self.invulnerable = False
            if hasattr(self, 'is_cloaked'):
                self.is_cloaked = False

        # Recalculate max ammo based on ammo_loader skill
        bonus_ammo = self.get_active_skill('ammo_loader') * 2
        self.max_torpedo_ammo = 10 + bonus_ammo
        self.max_bomb_ammo = 10 + bonus_ammo
        self.max_missile_ammo = 8 + bonus_ammo

        self.max_shields = self.base_max_shields + self.get_active_skill('shield')
        nanite_level = self.get_active_skill('nanite_repair')
        if nanite_level > 0 and self.shields < self.max_shields:
            self.shields = min(self.max_shields, self.shields + 0.003 * nanite_level)
            
        regen_delay = 3000 if self.get_active_skill('deflector') > 0 else self.shield_regen_delay
        if self.shields < self.max_shields:
            if current_time - self.last_hit_time > regen_delay:
                if current_time - self.last_regen_time > self.regen_cooldown:
                    self.shields = min(self.max_shields, self.shields + 1)
                    global SOUNDS
                    if SOUNDS: SOUNDS.play('shield_recharge')
                    self.last_regen_time = current_time

    def trigger_dash(self, direction, current_time):
        if self.is_dead:
            return False
        if current_time - self.last_dash > self.dash_cooldown:
            self.last_dash = current_time
            rad = math.radians(self.angle)
            direction_vector = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            dir_r = pygame.math.Vector2(-direction_vector.y, direction_vector.x)
            
            dash_force = 6.0 * (1.0 + self.get_active_skill('afterburner') * 0.20)
            if direction == 'LEFT':
                self.velocity -= dir_r * dash_force
            else:
                self.velocity += dir_r * dash_force
            return True
        return False

    def handle_input(self, current_time, camera_y, scale_info, camera_x=0, is_hub=False, limit_y=False):
        if self.is_dead:
            return [], [], [], [], []

        keys = pygame.key.get_pressed()
        
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        projectiles = []
        new_flares = []
        new_support = []
        new_drones = []
        new_crystals = []

        # 1. MOUSE-FACING ORIENTATION (moved up to define dir_r for abilities)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        offset_x, offset_y, new_w, new_h = scale_info
        mouse_x = (mouse_x - offset_x) * (VIRTUAL_WIDTH / new_w)
        mouse_y = (mouse_y - offset_y) * (VIRTUAL_HEIGHT / new_h)
        if not limit_y:
            mouse_y += camera_y
            mouse_x += camera_x
            
        target_dir = pygame.math.Vector2(mouse_x - center_x, mouse_y - center_y)
        if target_dir.length() > 5:
            target_angle = math.degrees(math.atan2(target_dir.y, target_dir.x)) % 360
            
            # Shortest path interpolation to prevent 360-wraparound jumps
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            
            # Rotation speed (degrees per frame) - lower values mean slower turning
            max_turn = 4.5 * (1.0 + self.get_active_skill('vector_nozzle') * 0.20)
            self.banking_amount = max(-1.0, min(1.0, angle_diff / max_turn))
            if abs(angle_diff) <= max_turn:
                self.angle = target_angle
            else:
                self.angle = (self.angle + math.copysign(max_turn, angle_diff)) % 360
        else:
            self.banking_amount *= 0.9

        rad = math.radians(self.angle)
        self.direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        dir_r = pygame.math.Vector2(-self.direction.y, self.direction.x) # right vector

        # Handle Special Ability (E key)
        is_overdrive = (self.class_name == 'RANGER' and current_time < self.ability_timer)
        if not is_hub and keys[pygame.K_e] and current_time - self.last_ability > self.ability_cooldown * getattr(self, 'ability_cooldown_mod', 1.0):
            self.last_ability = current_time
            if self.class_name == 'RANGER':
                self.ability_timer = current_time + 4000 # 4 second duration
                self.ability_timer = current_time + (4000 * getattr(self, 'ability_duration_mod', 1.0))
                is_overdrive = True
            elif self.class_name == 'ENGINEER':
                new_drones.append(SentryDrone(self, GOLD, 0))
                new_drones.append(SentryDrone(self, GOLD, math.pi))
            elif self.class_name == 'VANGUARD':
                # Spawns the new Player-Specific crystal
                new_crystals.append(PlayerShieldCrystal(center_x, center_y))
            elif self.class_name == 'SNIPER':
                # Airstrike: Spawn support ships coming from the opposite direction
                self.last_ability = current_time
                count = getattr(self, 'airstrike_count', 2)
                offset_step = 80
                
                spawn_center_x = center_x - self.direction.x * 800
                spawn_center_y = center_y - self.direction.y * 800
                airstrike_angle = self.angle
                
                for i in range(count):
                    offset_r = dir_r * (offset_step * (i - (count-1)/2.0))
                    new_support.append(SupportShip(spawn_center_x + offset_r.x, spawn_center_y + offset_r.y, airstrike_angle, YELLOW, owner=self))
            elif self.class_name == 'ASSASSIN':
                # Stealth Cloak: Brief invulnerability and speed burst
                self.invulnerable = True
                self.invulnerable_time = current_time
                self.invulnerable_duration = getattr(self, 'cloak_duration', 2000)
                self.is_cloaked = True
                self.velocity += self.direction * 12.0
        
        # Handle Specialist Ability (Q key)
        if not is_hub and keys[pygame.K_q] and current_time - self.last_special > self.special_cooldown:
            self.last_special = current_time
            if self.class_name == 'RANGER':
                self.special_timer = current_time + 2000
                self.speed_multiplier = 2.0
            elif self.class_name == 'ENGINEER':
                self.shields = min(self.max_shields, self.shields + 1)
                self.heat = 0
                # Release a pulse of 8 bullets
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    projectiles.append(Bullet(center_x, center_y, math.cos(rad), math.sin(rad)))
            elif self.class_name == 'VANGUARD':
                self.invulnerable = True
                self.invulnerable_time = current_time
                self.invulnerable_duration = 3000
                # Release a massive shockwave of 24 bullets
                for angle in range(0, 360, 15):
                    rad = math.radians(angle)
                    projectiles.append(Bullet(center_x, center_y, math.cos(rad), math.sin(rad)))
            elif self.class_name == 'SNIPER':
                for i in range(4):
                    ang = math.radians(self.angle - 30 + i * 20)
                    # Spawn at offset and converge to player
                    start_angle = math.radians(self.angle + 140 + i * 20)
                    sx, sy = center_x + math.cos(start_angle) * 200, center_y + math.sin(start_angle) * 200
                    projectiles.append(HomingMissile(sx, sy, -math.cos(start_angle), -math.sin(start_angle), shooter=self, converge_pos=pygame.math.Vector2(center_x, center_y)))
            elif self.class_name == 'ASSASSIN':
                self.x += self.direction.x * 250
                self.y += self.direction.y * 250
                self.heat = 0
                self.invulnerable = True
                self.invulnerable_time = current_time
                self.invulnerable_duration = 500
                # Small burst
                for offset in [-20, 0, 20]:
                    r_dir = self.direction.rotate(offset)
                    projectiles.append(Bullet(self.x + self.width//2, self.y + self.height//2, r_dir.x, r_dir.y, speed=15, life=18, damage=1.5, color=PURPLE))

        if getattr(self, 'special_timer', 0) > 0 and current_time > self.special_timer:
            self.special_timer = 0
            self.speed_multiplier = 1.0

        # Handle Flares (Left Shift)
        if not is_hub and keys[pygame.K_LSHIFT] and self.flare_ammo > 0 and current_time - self.last_flare_time > self.flare_cooldown:
            self.flare_ammo -= 1
            self.last_flare_time = current_time
            # Spawn 10 flares in a fan-shaped spread behind the player
            flare_x = center_x - self.direction.x * (self.height // 2)
            flare_y = center_y - self.direction.y * (self.height // 2)
            base_angle = math.degrees(math.atan2(-self.direction.y, -self.direction.x))
            for i in range(10):
                angle_offset = -40 + (80 / 9) * i
                rad = math.radians(base_angle + angle_offset)
                speed = random.uniform(2.0, 4.5)
                fdx = math.cos(rad) * speed
                fdy = math.sin(rad) * speed
                new_flares.append(Flare(flare_x, flare_y, fdx, fdy))

        # 2. ACCELERATION / MOVEMENT THRUSTER INPUTS
        accel = self.acceleration * self.speed_multiplier
        max_sp = self.max_speed * self.speed_multiplier
        if is_overdrive:
            accel *= 1.5
            max_sp *= 1.5
        
        # Up/W -> thrust forward
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity += self.direction * accel
        # Down/S -> thrust backward
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity -= self.direction * (accel * 0.6)
        # Left/A -> strafe left
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity -= dir_r * (accel * 0.8)
        # Right/D -> strafe right
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity += dir_r * (accel * 0.8)

        # Apply drag / decay momentum gradually
        self.velocity *= self.drag

        # Clamp speed to max_speed (decay smoothly if exceeding max_sp from a dash)
        if self.velocity.length() > max_sp:
            self.velocity = self.velocity.lerp(self.velocity.normalize() * max_sp, 0.15)

        # Update position based on momentum
        self.x += self.velocity.x
        self.y += self.velocity.y

        if limit_y:
            self.x = max(0, min(VIRTUAL_WIDTH - self.width, self.x))
            self.y = max(0, min(VIRTUAL_HEIGHT - self.height, self.y))
        else:
            # Wrap around the planet (X-axis) seamlessly
            map_width = 5200
            if self.x < -2600:
                self.x += map_width
            elif self.x > 2600:
                self.x -= map_width
            # Constrain player so they cannot fly below the camera's viewport
            self.y = min(self.y, camera_y + VIRTUAL_HEIGHT - self.height)
            
        self.rect.topleft = (self.x, self.y)

        if is_hub:
            return [], [], [], [], []

        mouse_buttons = pygame.mouse.get_pressed()
        
        actual_cool_rate = self.cool_rate * (1.0 + 0.25 * self.get_active_skill('coolant'))
        
        # Plasma Biome Heat Gimmick
        is_plasma = getattr(self, 'in_plasma_biome', False) # Set by Game instance
        if is_plasma:
            actual_cool_rate *= 0.6

        if self.heat > 0:
            # Purge heat twice as fast during overdrive
            self.heat = max(0.0, self.heat - (actual_cool_rate * 2.0 if is_overdrive else actual_cool_rate))
            if self.overheated and self.heat == 0.0:
                self.overheated = False

        # Left click to shoot standard bullets
        if not is_hub and mouse_buttons[0]:
            if not self.overheated:
                actual_shoot_delay = self.shoot_delay * 0.70 if self.get_active_skill('overcharge') > 0 else self.shoot_delay
                if is_overdrive:
                    actual_shoot_delay *= 0.5 # Double fire rate
                
                if current_time - self.last_shot > actual_shoot_delay:
                    self.last_shot = current_time
                    tip_x = center_x + self.direction.x * (self.height // 2)
                    tip_y = center_y + self.direction.y * (self.height // 2)
                    
                    b_speed = 26 * getattr(self, 'bullet_speed_mod', 1.0)

                    if self.active_primary == 0: # Laser
                        weapon_level = self.get_active_skill('weapon')
                        if weapon_level == 0:
                            b = Bullet(tip_x, tip_y, self.direction.x, self.direction.y, speed=b_speed)
                            if self.has_mod_piercing: b.piercing = True
                            projectiles.append(b)
                        else: # Level 1 (Double)
                            right_vector = pygame.math.Vector2(-self.direction.y, self.direction.x) * 8
                            b1 = Bullet(tip_x - right_vector.x, tip_y - right_vector.y, self.direction.x, self.direction.y, speed=b_speed)
                            b2 = Bullet(tip_x + right_vector.x, tip_y + right_vector.y, self.direction.x, self.direction.y, speed=b_speed)
                            if self.has_mod_piercing:
                                b1.piercing = True
                                b2.piercing = True
                            projectiles.append(b1)
                            projectiles.append(b2)
                        
                        if self.has_mod_split:
                            left_dir = self.direction.rotate(-15)
                            right_dir = self.direction.rotate(15)
                            bl = Bullet(tip_x, tip_y, left_dir.x, left_dir.y, speed=b_speed)
                            br = Bullet(tip_x, tip_y, right_dir.x, right_dir.y, speed=b_speed)
                            if self.has_mod_piercing:
                                bl.piercing = True
                                br.piercing = True
                            projectiles.append(bl)
                            projectiles.append(br)
                        
                        if not is_overdrive:
                            heat_gain = self.heat_per_shot * (1.25 if is_plasma else 1.0)
                            self.heat = min(self.max_heat, self.heat + heat_gain)
                            if self.heat >= self.max_heat:
                                self.overheated = True

                    elif self.active_primary == 1 and self.get_active_skill('shotgun_unlocked'): # Shotgun
                        sm = self.get_active_skill('shotgun_mod')
                        final_heat = 12.0 - (sm * 1.5)
                        for offset in [-20, -10, 0, 10, 20]:
                            r_dir = self.direction.rotate(offset)
                            projectiles.append(Bullet(tip_x, tip_y, r_dir.x, r_dir.y, speed=15, life=36, damage=0.5 + 0.15*sm, color=ORANGE))
                        
                        if not is_overdrive:
                            heat_gain = final_heat * (1.25 if is_plasma else 1.0)
                            self.heat = min(self.max_heat, self.heat + heat_gain)
                            if self.heat >= self.max_heat:
                                self.overheated = True
 
                    elif self.active_primary == 2 and self.get_active_skill('railgun_unlocked'): # Railgun
                        rm = self.get_active_skill('railgun_mod')
                        final_heat = 15.0
                        projectiles.append(Bullet(tip_x, tip_y, self.direction.x, self.direction.y, speed=25, life=100, piercing=True, damage=6.0 + 2.0*rm, color=CYAN))
                        
                        if not is_overdrive:
                            heat_gain = final_heat * (1.25 if is_plasma else 1.0)
                            self.heat = min(self.max_heat, self.heat + heat_gain)
                            if self.heat >= self.max_heat:
                                self.overheated = True
 
        # Right click to shoot Secondary weapons
        if not is_hub and mouse_buttons[2]:
            tip_x = center_x + self.direction.x * (self.height // 2)
            tip_y = center_y + self.direction.y * (self.height // 2)
            
            if self.active_secondary == 0: # Torpedo
                actual_torpedo_delay = self.torpedo_delay * (1.0 - 0.15 * self.get_active_skill('torpedo'))
                if current_time - self.last_torpedo > actual_torpedo_delay:
                    self.last_torpedo = current_time
                    scale = 1.0 + 0.15 * self.get_active_skill('torpedo')
                    projectiles.append(Torpedo(tip_x, tip_y, self.direction.x, self.direction.y, scale))
            
            elif self.active_secondary == 1 and self.get_active_skill('bomb_unlocked') and self.bomb_ammo > 0: # Bomb
                if current_time - self.last_secondary > 500:
                    self.last_secondary = current_time
                    self.bomb_ammo -= 1
                    projectiles.append(ProxBomb(tip_x, tip_y, self.direction.x, self.direction.y, scale=1.0 + 0.15*self.get_active_skill('bomb_cap')))
                    
            elif self.active_secondary == 2 and self.get_active_skill('missile_unlocked') and self.missile_ammo > 0: # Missile
                if current_time - self.last_secondary > 400:
                    self.last_secondary = current_time
                    self.missile_ammo -= 1
                    projectiles.append(HomingMissile(tip_x, tip_y, self.direction.x, self.direction.y, scale=1.0 + 0.15*self.get_active_skill('missile_cap'), shooter=self))

        return projectiles, new_flares, new_support, new_drones, new_crystals

    def draw(self, screen, camera_y, camera_x=0):
        if self.is_dead:
            return

        current_time = pygame.time.get_ticks()
        if getattr(self, 'is_cloaked', False):
            # Draw a shimmer effect instead of the full ship
            draw_x = self.x - camera_x
            draw_y = self.y - camera_y
            center_x = draw_x + self.width // 2
            center_y = draw_y + self.height // 2
            
            radius = self.width // 2 + 5
            alpha = 80 + 40 * math.sin(current_time * 0.02)
            pygame.draw.circle(screen, (200, 200, 255, alpha), (int(center_x), int(center_y)), radius, width=3)
            return # Don't draw the rest of the ship

        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        center_x = draw_x + self.width // 2
        center_y = draw_y + self.height // 2
        center = pygame.math.Vector2(center_x, center_y)
        
        # Directions
        dir_f = self.direction # forward
        dir_r = pygame.math.Vector2(-self.direction.y, self.direction.x) # right
        
        # Banking perspective shift
        bank_squeeze = 1.0 - abs(self.banking_amount) * 0.35
        lw_sqz = 1.0 - max(0, -self.banking_amount) * 0.6
        rw_sqz = 1.0 - max(0, self.banking_amount) * 0.6

        # Ability state for visuals
        is_overdrive = (self.class_name == 'RANGER' and current_time < self.ability_timer)
        
        # Color palettes
        color = CYAN
        if self.class_name == 'ENGINEER':
            color = GOLD
        elif self.class_name == 'VANGUARD':
            color = MAGENTA
        elif self.class_name == 'SNIPER':
            color = YELLOW
        elif self.class_name == 'ASSASSIN':
            color = PURPLE
        
        if (is_overdrive or (self.class_name == 'ASSASSIN' and self.invulnerable)) and current_time % 200 < 100:
            color = WHITE

        if self.invulnerable:
            if pygame.time.get_ticks() % 100 < 50:
                color = WHITE
        elif self.overheated:
            if pygame.time.get_ticks() % 200 < 100:
                color = RED
                
        # 1. THRUSTER FLAMES (flickers based on movement inputs)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w] or self.velocity.length() > 1:
            pulse = (math.sin(current_time * 0.05) + 1) / 2
            flame_len = (18 + random.randint(-5, 15)) * (0.8 + 0.4 * pulse)
            if not (keys[pygame.K_UP] or keys[pygame.K_w]): flame_len *= 0.5
            y_jitter = random.uniform(-2, 2)
            rear_center = center - dir_f * (self.height // 2) + dir_f * y_jitter
            flame_tip = rear_center - dir_f * flame_len
            flame_l = rear_center - dir_r * (8 * bank_squeeze)
            flame_r = rear_center + dir_r * (8 * bank_squeeze)
            flame_col = random.choice([CYAN, WHITE]) if is_overdrive else random.choice([ORANGE, YELLOW, RED])
            pygame.draw.polygon(screen, flame_col, [rear_center, flame_l, flame_tip, flame_r])
            pygame.draw.line(screen, WHITE if is_overdrive else YELLOW, rear_center, rear_center - dir_f * (flame_len * 0.65), 1)

        # 2. WINGS
        lw_tip = center - dir_f * 5 - dir_r * (self.width // 2 * lw_sqz)
        lw_base_in = center - dir_f * (self.height // 2) - dir_r * 5
        lw_base_out = center - dir_f * (self.height // 3) - dir_r * (self.width // 2 * lw_sqz)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, lw_tip, lw_base_out, lw_base_in])
        
        rw_tip = center - dir_f * 5 + dir_r * (self.width // 2 * rw_sqz)
        rw_base_in = center - dir_f * (self.height // 2) + dir_r * 5
        rw_base_out = center - dir_f * (self.height // 3) + dir_r * (self.width // 2 * rw_sqz)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, rw_tip, rw_base_out, rw_base_in])

        # 3. WING CANNONS (Based on Weapon Level)
        weapon_level = self.skills['weapon']
        if weapon_level >= 1:
            pygame.draw.line(screen, color, lw_tip, lw_tip + dir_f * 12, width=2)
            pygame.draw.line(screen, color, rw_tip, rw_tip + dir_f * 12, width=2)

        # 4. MAIN HULL (Triangle shape with 3D tilt parallax)
        hull_center = center + dir_r * (self.banking_amount * 6)
        hull_tip = hull_center + dir_f * (self.height // 2)
        hull_left = hull_center - dir_f * (self.height // 4) - dir_r * (8 * bank_squeeze)
        hull_right = hull_center - dir_f * (self.height // 4) + dir_r * (8 * bank_squeeze)
        pygame.draw.polygon(screen, color, [hull_tip, hull_left, hull_right])

        # 5. COCKPIT GLASS (Enhanced 3D tilt parallax)
        cockpit_center = center + dir_r * (self.banking_amount * 10)
        glass_tip = cockpit_center + dir_f * (self.height // 3)
        glass_left = cockpit_center + dir_f * (self.height // 8) - dir_r * (4 * bank_squeeze)
        glass_right = cockpit_center + dir_f * (self.height // 8) + dir_r * (4 * bank_squeeze)
        pygame.draw.polygon(screen, WHITE, [glass_tip, glass_left, glass_right])

        # 6. SHIELD FORCEFIELD (flashes brighter and thicker when hit)
        if self.shields > 0:
            is_hit_recently = (current_time - getattr(self, 'shield_bubble_timer', 0) < 300)
            if is_hit_recently:
                glow_color = (0, 255, 255, 200)
                width_val = 4
                radius = int(self.width * 1.0)
            else:
                glow_intensity = 30 + int(15 * math.sin(current_time * 0.01))
                glow_color = (0, 255, 255, glow_intensity)
                width_val = 2
                radius = int(self.width * 0.9)
            pygame.draw.circle(screen, glow_color, (int(center_x), int(center_y)), radius, width=width_val)

class Game:
    def __init__(self):
        pygame.init()
        global SOUNDS
        if SOUNDS is None:
            SOUNDS = SoundManager()
        # Enable RESIZABLE screen mode
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        self.ui_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        pygame.display.set_caption("Zenith")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.large_font = pygame.font.SysFont("Arial", 64)
        
        # State Variables
        self.player_name = ""
        self.state = 'INTRO'
        self.intro_start_time = pygame.time.get_ticks()
        # State Transitions
        self.transition_state = None
        self.transition_start_time = 0
        self.transition_duration = 1000
        self.current_zone = 'HUB'
        self.selected_class = 'RANGER'
        self.camera_y = 0
        self.camera_x = 0
        self.screen_shake = 0
        self.debug_invincible = False
        self.dev_mode = False
        self.tutorial_stage = 0
        self.tutorial_dialogues = [
            {
                "title": "WELCOME TO TRAINING RANGE",
                "text": "Greetings, Pilot! This range is completely safe. Let's learn the cockpit controls first. Press W to accelerate/thrust, S to decelerate/reverse, and A/D to steer your ship's banking angle.",
                "action": "Next Tip"
            },
            {
                "title": "WEAPON SYSTEMS",
                "text": "Your ship is armed. Left-Click or Hold SPACEBAR to fire your Primary Cannons. Press Q to fire Homing Missiles, E to drop Proximity Bombs, and SHIFT to execute a Tactical Phase Shift (Dash).",
                "action": "Next Tip"
            },
            {
                "title": "MATERIALS & UPGRADES",
                "text": "Enemies and meteors drop Scrap Metals (golden boxes). Gather them to purchase permanent upgrades and interchangeable modules at the Engineering Hub.",
                "action": "Next Tip"
            },
            {
                "title": "SLOT-BASED INVENTORY",
                "text": "In the Hub shops, you can drag and drop modules to customize your Ship Class. Drag parts into the recycle bin for a scrap refund, or equip them into slots to gain unique passive bonuses.",
                "action": "Next Tip"
            },
            {
                "title": "WARPING OUT",
                "text": "Collect 5 Matrix Cores in normal levels to spawn the exit wormhole warp gates. Enter the warp gate to return to the Hub station or complete your campaign objectives.",
                "action": "Finish Tutorial"
            }
        ]
        self.input_active = False # For player name input
        self.dragging_volume = False
        self.dragging_tint = False
        self.dragging_vignette = False
        self.dragging_softness = False
        
        # Drag and drop upgrades variables
        self.dragged_part = None
        self.dragged_origin = None
        self.dragged_part_key = None
        self.drag_mouse_offset = (0, 0)
        self.filter_tint_alpha = 50
        self.filter_vignette_alpha = 100
        self.filter_softness = 15
        self.vignette_surface = self._generate_vignette()
        self.hub_station_active = None
        self.shop_tab = 'MAIN'
        
        # Letterbox offsets & sizes to prevent scaling distortion
        self.offset_x = 0
        self.offset_y = 0
        self.new_width = SCREEN_WIDTH
        self.new_height = SCREEN_HEIGHT
        
        # Procedural surroundings states
        self.highest_y_generated = 0
        self.materials_spawned_count = 0
        self.wormhole_spawned = False
        self.wormhole_pos = pygame.math.Vector2(600, -800)
        
        self.reset_game()
        self._update_scaling()

    def _generate_vignette(self):
        w, h = 120, 90
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w / 2, h / 2
        max_dist = math.sqrt(cx**2 + cy**2)
        for y in range(h):
            for x in range(w):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                ratio = dist / max_dist
                alpha = int(255 * (ratio ** 2))
                surf.set_at((x, y), (0, 0, 0, min(255, alpha)))
        return pygame.transform.smoothscale(surf, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

    def _update_scaling(self):
        aspect_ratio = VIRTUAL_WIDTH / VIRTUAL_HEIGHT
        window_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        
        if window_ratio > aspect_ratio:
            self.new_width = int(SCREEN_HEIGHT * aspect_ratio)
            self.new_height = SCREEN_HEIGHT
            self.offset_x = (SCREEN_WIDTH - self.new_width) // 2
            self.offset_y = 0
        else:
            self.new_width = SCREEN_WIDTH
            self.new_height = int(SCREEN_WIDTH / aspect_ratio)
            self.offset_x = 0
            self.offset_y = (SCREEN_HEIGHT - self.new_height) // 2

    def reset_game(self):
        self.player = Player()
        self.player.set_class(self.selected_class)
        self.bullets = []
        self.torpedoes = []
        self.bombs = []
        self.missiles = []
        self.enemies = []
        self.support_ships = []
        self.drones = []
        self.flares = [] # New
        self.meteors = []
        self.stars = []
        self.particles = []
        self.materials = []
        self.scraps = []
        self.gas_clouds = []
        self.ambient_debris = []
        self.derelicts = []
        self.anomalies = []
        self.small_portals = []
        self.data_uplinks = []
        self.shockwaves = []
        self.static_obstacles = []
        self.materials_collected = 0
        self.game_over = False
        self.running = True
        self.loot_pickups = []
        self.planet_features = []
        self.planet_texture = None
        self.planet_clouds = None
        self.campaign_stage = 1
        self.min_y_generated = 600
        self.max_y_generated = 600
        # Pre-cache planet mask for performance - ensured here so it exists if pausing in Hub
        self.planet_mask = pygame.Surface((1600, 1600), pygame.SRCALPHA)
        pygame.draw.circle(self.planet_mask, (255, 255, 255, 255), (800, 800), 800)

        self.zoom_level = 1.0
        self.quests = [
            Quest('collect_cores', 'Reactor Jumpstart', 'Gather 5 Matrix Cores in the Asteroid Belt.', 5, 250, 120),
            Quest('defeat_boss', 'Reactor Meltdown', 'Infiltrate Singularity Factory and defeat Reactor Boss.', 1, 400, 180),
            Quest('defeat_orion', 'Citadel Siege', 'Defeat the Orion Citadel Boss to save the galaxy.', 1, 600, 300)
        ]
        self.active_quest = self.quests[min(len(self.quests)-1, self.campaign_stage - 1)]
        
        self.unlocked_zones = {
            'TUTORIAL': True,
            'ASTEROIDS': True, 
            'VULCAN': self.campaign_stage >= 2, 
            'AQUARIS': self.campaign_stage >= 2,
            'NEBULA': self.campaign_stage >= 2, 
            'PLASMA': self.campaign_stage >= 2, 
            'VOID': self.campaign_stage >= 2,
            'QUANTUM': self.campaign_stage >= 2, 
            'SINGULARITY': self.campaign_stage >= 2, 
            'ORION': self.campaign_stage >= 3
        }
        self.current_hub_index = 3 if self.campaign_stage >= 3 else (2 if self.campaign_stage >= 2 else 1)

        
        # New gimmick / boss objects
        self.enemy_bullets = []
        self.boss = None
        self.boss_defeated = False
        self.escape_sequence_active = False
        self.escape_blackhole_pos = None
        self.escape_blackhole_radius = 0.0
        self.victory_start_time = 0
        self._played_victory_music = False
        self.dragged_part = None
        self.dragged_origin = None
        self.dragged_part_key = None
        self.drag_mouse_offset = (0, 0)
        self._emergency_recharge_used = 0
        self.player_death_timer = 0
        self.active_hub_portal = None
        self.shield_crystals = []
        self.gravity_wells = []
        self.solar_flare_state = 'IDLE'
        self.solar_flare_timer = 0
        self.solar_flare_y = 0
        
        self.enemy_spawn_time = 0
        self.enemy_spawn_delay = 3200
        self.meteor_spawn_time = 0
        self.meteor_spawn_delay = 1600
        
        # Procedural height states
        self.highest_y_generated = 600
        self.materials_spawned_count = 0
        self.wormhole_spawned = False
        self.wormhole_charge_timer = 0
        
        # Pre-render a beautiful default nebula surface (for HUB / Menu)
        self.nebula_surf = pygame.Surface((400, 300), pygame.SRCALPHA)
        self.nebula_surf.fill((0, 0, 0, 0))
        theme_color = BLUE
        for _ in range(6):
            cx = random.randint(50, 350)
            cy = random.randint(50, 250)
            radius = random.randint(80, 150)
            r_var = max(0, min(255, theme_color[0] + random.randint(-30, 30)))
            g_var = max(0, min(255, theme_color[1] + random.randint(-30, 30)))
            b_var = max(0, min(255, theme_color[2] + random.randint(-30, 30)))
            for layer in range(5):
                alpha = int(18 / (layer + 1))
                lr = int(radius * (1.0 + layer * 0.25))
                pygame.draw.circle(self.nebula_surf, (r_var, g_var, b_var, alpha), (cx, cy), lr)

        self.stars_color = WHITE
        self._build_stars()

    def _build_stars(self):
        self.stars = []
        for _ in range(120):
            x = random.randint(0, VIRTUAL_WIDTH)
            y = random.randint(0, VIRTUAL_HEIGHT)
            depth = random.uniform(0.1, 1.0)
            size = max(1, int(depth * 3))
            color = random.choice([
                (255, 255, 255),
                (200, 220, 255),
                (255, 240, 220),
                (200, 255, 255),
            ])
            twinkle_speed = random.uniform(0.01, 0.05)
            twinkle_offset = random.uniform(0, 100)
            self.stars.append([x, y, depth, size, color, twinkle_speed, twinkle_offset])

    def _draw_background_nebula(self, screen, camera_y, camera_x, theme_color):
        if getattr(self, 'nebula_surf', None) is not None:
            # Scroll slowly in parallax
            ny = int(-camera_y * 0.08) % VIRTUAL_HEIGHT
            nx = int(-camera_x * 0.08) % VIRTUAL_WIDTH
            
            # Smooth scale pre-rendered low-res nebula surface for soft gaussian look
            scaled_nebula = pygame.transform.smoothscale(self.nebula_surf, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            
            # Draw tiled
            screen.blit(scaled_nebula, (nx, ny))
            screen.blit(scaled_nebula, (nx - VIRTUAL_WIDTH, ny))
            screen.blit(scaled_nebula, (nx, ny - VIRTUAL_HEIGHT))
            screen.blit(scaled_nebula, (nx - VIRTUAL_WIDTH, ny - VIRTUAL_HEIGHT))

    def _draw_cyber_grid(self, surface, camera_y, camera_x, theme_color):
        grid_spacing = 80
        grid_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        
        offset_y = int(-camera_y) % grid_spacing
        offset_x = int(-camera_x) % grid_spacing
        
        line_color = (theme_color[0], theme_color[1], theme_color[2], 12)
        
        for gy in range(offset_y - grid_spacing, VIRTUAL_HEIGHT + grid_spacing, grid_spacing):
            pygame.draw.line(grid_surf, line_color, (0, gy), (VIRTUAL_WIDTH, gy), 1)
        for gx in range(offset_x - grid_spacing, VIRTUAL_WIDTH + grid_spacing, grid_spacing):
            pygame.draw.line(grid_surf, line_color, (gx, 0), (gx, VIRTUAL_HEIGHT), 1)
            
        ticks = pygame.time.get_ticks()
        node_color = (theme_color[0], theme_color[1], theme_color[2], 40)
        
        shift_y = int(ticks * 0.04) % grid_spacing
        for gy in range(offset_y - grid_spacing + shift_y, VIRTUAL_HEIGHT + grid_spacing, grid_spacing):
            for gx in range(offset_x - grid_spacing, VIRTUAL_WIDTH + grid_spacing, grid_spacing * 2):
                pygame.draw.circle(grid_surf, node_color, (gx, gy), 2)
                
        surface.blit(grid_surf, (0, 0))

    def _generate_planet_clouds(self, zone_name):
        tex_w, tex_h = 1024, 1024
        tex = pygame.Surface((tex_w, tex_h), pygame.SRCALPHA)
        tex.fill((0, 0, 0, 0)) # transparent background
        
        # Seed random number generator with zone name to ensure consistency
        random.seed(zone_name + "_clouds")
        
        # Draw some soft white/translucent cloud bands
        for _ in range(15):
            cy = random.randint(0, tex_h)
            cx = random.randint(0, tex_w)
            cloud_w = random.randint(120, 320)
            cloud_h = random.randint(32, 80)
            alpha = random.randint(40, 110)
            
            # Draw elongated horizontal cloud strips
            for ox in (-tex_w, 0, tex_w):
                pygame.draw.ellipse(tex, (255, 255, 255, alpha), (cx + ox - cloud_w // 2, cy - cloud_h // 2, cloud_w, cloud_h))
                
        # Draw some soft round cloud puffs
        for _ in range(20):
            cx = random.randint(0, tex_w)
            cy = random.randint(0, tex_h)
            radius = random.randint(40, 120)
            alpha = random.randint(30, 90)
            
            for ox in (-tex_w, 0, tex_w):
                pygame.draw.circle(tex, (255, 255, 255, alpha), (cx + ox, cy), radius)
                
        random.seed()
        return tex

    def _generate_planet_texture(self, zone_name):
        zone_color = BIOME_CONFIGS.get(zone_name, {'theme_color': GRAY})['theme_color']
        tex_w, tex_h = 1024, 1024
        tex = pygame.Surface((tex_w, tex_h))
        
        base_r = max(10, int(zone_color[0] * 0.15))
        base_g = max(10, int(zone_color[1] * 0.15))
        base_b = max(10, int(zone_color[2] * 0.15))
        tex.fill((base_r, base_g, base_b))
        
        # Seed random number generator with zone name for consistency
        random.seed(zone_name)
        
        # Draw horizontal clouds / bands (step size 8 for speed & smoothness)
        for y in range(0, tex_h, 8):
            factor = 0.05 + 0.15 * math.sin(y * 0.0125) + random.uniform(-0.02, 0.02)
            br = max(0, min(255, int(base_r + zone_color[0] * factor)))
            bg = max(0, min(255, int(base_g + zone_color[1] * factor)))
            bb = max(0, min(255, int(base_b + zone_color[2] * factor)))
            pygame.draw.rect(tex, (br, bg, bb), (0, y, tex_w, 8))
            
        # Draw some soft organic continent/cloud shapes
        for _ in range(25):
            cx = random.randint(0, tex_w)
            cy = random.randint(0, tex_h)
            radius = random.randint(60, 180)
            factor = random.uniform(-0.08, 0.18)
            cr = max(0, min(255, int(base_r + zone_color[0] * factor)))
            cg = max(0, min(255, int(base_g + zone_color[1] * factor)))
            cb = max(0, min(255, int(base_b + zone_color[2] * factor)))
            
            for ox in (-tex_w, 0, tex_w):
                pygame.draw.circle(tex, (cr, cg, cb), (cx + ox, cy), radius)
                
        # Draw some craters with shading
        for _ in range(12):
            cx = random.randint(0, tex_w)
            cy = random.randint(0, tex_h)
            crater_r = random.randint(24, 64)
            
            sr = max(0, base_r - 20)
            sg = max(0, base_g - 20)
            sb = max(0, base_b - 20)
            
            hr = max(0, min(255, int(base_r + zone_color[0] * 0.25)))
            hg = max(0, min(255, int(base_g + zone_color[1] * 0.25)))
            hb = max(0, min(255, int(base_b + zone_color[2] * 0.25)))
            
            for ox in (-tex_w, 0, tex_w):
                pygame.draw.circle(tex, (sr, sg, sb), (cx + ox, cy), crater_r)
                pygame.draw.circle(tex, (hr, hg, hb), (cx + ox, cy), crater_r, width=4)
                
        random.seed()
        return tex

    def setup_exploration_zone(self, zone_name):
        self.state = 'PLAYING'
        self.current_zone = zone_name
        self.bullets = []
        self.torpedoes = []
        self.bombs = []
        self.missiles = []
        self.support_ships = []
        self.drones = []
        self.flares = [] # New
        self.enemies = []
        self.meteors = []
        self.materials = []
        self.scraps = []
        self.gas_clouds = []
        self.ambient_debris = []
        self.derelicts = []
        self.anomalies = []
        self.small_portals = []
        self.static_obstacles = []
        self.data_uplinks = []
        self.shockwaves = []
        self.particles = []
        self.shooting_stars = []
        self.materials_collected = 0
        self.player.speed_multiplier = 1.0
        
        # New gimmick / boss objects
        self.enemy_bullets = []
        if zone_name == 'SINGULARITY':
            self.boss = Boss('SINGULARITY', -2500)
        else:
            self.boss = None
        self.boss_defeated = False
        self.boss_defeated_time = 0
        self.escape_sequence_active = False
        self.escape_blackhole_pos = None
        self.escape_blackhole_radius = 0.0
        self.active_hub_portal = None
        self.shield_crystals = []
        self.gravity_wells = []
        self.solar_flare_state = 'IDLE'
        self.solar_flare_timer = 0
        self.solar_flare_y = 0
        
        # Custom objective variables
        self.convoy = None
        self.convoy_defend_timer = 0.0
        if zone_name == 'VULCAN':
            self.convoy = ConvoyShip(VIRTUAL_WIDTH // 2, 700)
            self.convoy_defend_timer = 45.0
            self.player.x = VIRTUAL_WIDTH // 2 - 150
            self.player.y = 800
        
        self.supernova_y = None
        if zone_name == 'NEBULA':
            self.supernova_y = 1200
            self.supernova_speed = 3.0
            
        self.energy_cells = []
        self.energy_cells_collected = 0
        
        self.black_hole_core = None
        self.quantum_portals = []
        self.quantum_anchors = []
        self.quantum_dimension = 'NORMAL'
        if zone_name == 'QUANTUM':
            self.black_hole_core = BlackHoleCore(VIRTUAL_WIDTH // 2, -3500)
            self.quantum_portals.append(QuantumPortal(400, -800))
            self.quantum_portals.append(QuantumPortal(800, -1800))
            self.quantum_portals.append(QuantumPortal(500, -2800))
            self.quantum_anchors.append(QuantumAnchor(300, -1000, 1))
            self.quantum_anchors.append(QuantumAnchor(900, -2000, 2))
            self.quantum_anchors.append(QuantumAnchor(450, -3000, 3))
            
        self.void_enemies_killed = 0
        self.tutorial_stage = 0
        
        self.min_y_generated = 600
        self.max_y_generated = 600
        self.materials_spawned_count = 0
        self.wormhole_spawned = False
        self.wormhole_charge_timer = 0
        
        # Vary planet sizes dynamically per biome run (consistent for same biome)
        random.seed(zone_name)
        self.planet_radius = random.randint(400, 750)
        random.seed()
        
        self.planet_mask = pygame.Surface((self.planet_radius * 2, self.planet_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.planet_mask, (255, 255, 255, 255), (self.planet_radius, self.planet_radius), self.planet_radius)

        # Generate pseudo-random terrain features for the planet scaled to dynamic dimensions
        random.seed(self.current_zone)
        self.planet_features = []
        for _ in range(60):
            fx = random.randint(0, 4000)
            fy = random.randint(0, self.planet_radius * 2)
            fr = random.randint(20, int(self.planet_radius * 0.22))
            self.planet_features.append((fx, fy, fr))
        random.seed()
        
        # Generate planet texture
        raw_tex = self._generate_planet_texture(zone_name)
        self.planet_texture = pygame.transform.smoothscale(raw_tex, (self.planet_radius * 2, self.planet_radius * 2))
        
        raw_clouds = self._generate_planet_clouds(zone_name)
        self.planet_clouds = pygame.transform.smoothscale(raw_clouds, (self.planet_radius * 2, self.planet_radius * 2))
        
        if zone_name in BIOME_CONFIGS:
            self.stars_color = BIOME_CONFIGS[zone_name]['stars_color']
        else:
            self.stars_color = GRAY
            
        self.player.x = VIRTUAL_WIDTH // 2 - self.player.width // 2
        self.player.y = 600
        self.camera_y = self.player.y - VIRTUAL_HEIGHT // 2
        self.camera_x = self.player.x - VIRTUAL_WIDTH // 2
        
        # Pre-render a beautiful biome-specific nebula surface
        self.nebula_surf = pygame.Surface((400, 300), pygame.SRCALPHA)
        self.nebula_surf.fill((0, 0, 0, 0))
        theme_color = BIOME_CONFIGS.get(zone_name, {'theme_color': GRAY})['theme_color']
        for _ in range(6):
            cx = random.randint(50, 350)
            cy = random.randint(50, 250)
            radius = random.randint(80, 150)
            r_var = max(0, min(255, theme_color[0] + random.randint(-30, 30)))
            g_var = max(0, min(255, theme_color[1] + random.randint(-30, 30)))
            b_var = max(0, min(255, theme_color[2] + random.randint(-30, 30)))
            for layer in range(5):
                alpha = int(18 / (layer + 1))
                lr = int(radius * (1.0 + layer * 0.25))
                pygame.draw.circle(self.nebula_surf, (r_var, g_var, b_var, alpha), (cx, cy), lr)

        # Procedurally generate initial starting surroundings chunk
        self.bg_structure = BackgroundStructure(zone_name)
        self._procedurally_generate_chunk(600, -1000)
        self.level_start_time = pygame.time.get_ticks()
        self.boss_spawned_orion = False

    def _procedurally_generate_chunk(self, from_y, to_y):
        min_y = min(int(from_y), int(to_y))
        max_y = max(int(from_y), int(to_y))
        # Generate static obstacles as player flies up
        if self.current_zone in ('SINGULARITY', 'ORION'):
            if self.current_zone == 'SINGULARITY':
                # Core Room y coordinate is -3000, x center is 600
                
                # Place Core Room walls if this chunk covers y = -3000
                if to_y <= -2500 and from_y >= -3500:
                    self.static_obstacles = [obs for obs in self.static_obstacles if not (abs(obs.x - 600) < 550 and abs(obs.y - (-3000)) < 550)]
                    bx_min, bx_max = 200, 1000
                    by_min, by_max = -3400, -2600
                    
                    # Draw top wall with 240px wide gate at center (480 to 720)
                    for wx in range(bx_min, bx_max + 120, 120):
                        if not (480 <= wx <= 720):
                            self.static_obstacles.append(FactoryStructure(wx, by_min, 120, 120))
                            
                    # Draw bottom wall with 240px wide gate at center (480 to 720)
                    for wx in range(bx_min, bx_max + 120, 120):
                        if not (480 <= wx <= 720):
                            self.static_obstacles.append(FactoryStructure(wx, by_max, 120, 120))
                            
                    # Draw left and right walls
                    for wy in range(by_min + 120, by_max, 120):
                        self.static_obstacles.append(FactoryStructure(bx_min, wy, 120, 120))
                        self.static_obstacles.append(FactoryStructure(bx_max, wy, 120, 120))
                
                # Regular corridor grid outside of the Core Room
                cols = [-1800, -1200, -600, 0, 600, 1200, 1800, 2400, 3000]
                grid_spacing = 600
            else: # ORION
                # Spaced wider: cols every 1200px
                cols = [-2400, -1200, 0, 1200, 2400]
                grid_spacing = 1200

            random.seed(min_y // 120)
            
            for y_step in range(min_y, max_y, 120):
                if self.current_zone == 'SINGULARITY' and abs(y_step - (-3000)) < 600:
                    continue
                if y_step > 300:
                    continue
                    
                if y_step % grid_spacing == 0:
                    # Place a horizontal gate row with some open lanes
                    open_lanes = [random.randint(0, len(cols)-1)]
                    for col_idx, cx in enumerate(cols):
                        if col_idx not in open_lanes:
                            for wx in [cx - 120, cx, cx + 120]:
                                if not any(abs(obs.x - wx) < 60 and abs(obs.y - y_step) < 60 for obs in self.static_obstacles):
                                    self.static_obstacles.append(FactoryStructure(wx, y_step, 120, 120))
                else:
                    # Place vertical corridor walls along the column lines
                    for cx in cols:
                        if random.random() < 0.60:
                            if not any(abs(obs.x - cx) < 60 and abs(obs.y - y_step) < 60 for obs in self.static_obstacles):
                                self.static_obstacles.append(FactoryStructure(cx, y_step, 120, 120))
            random.seed()
        else:
            # Generate static obstacles (asteroids) as player flies up
            num_obstacles = 12
            for _ in range(num_obstacles):
                ox = random.randint(-2600, 2600)
                oy = random.randint(min_y, max_y)
                
                overlap = False
                for obs in self.static_obstacles:
                    if pygame.math.Vector2(ox, oy).distance_to(pygame.math.Vector2(obs.x, obs.y)) < 150:
                        overlap = True
                if not overlap:
                    self.static_obstacles.append(Meteor(ox, oy, is_static=True))

        # Spawn Matrix Cores only in ASTEROIDS
        if self.current_zone == 'ASTEROIDS':
            core_chance = 0.30
            if random.random() < core_chance:
                cx = random.randint(-2600, 2600)
                cy = random.randint(min_y, max_y)
                overlap = False
                for mat in self.materials:
                    if pygame.math.Vector2(cx, cy).distance_to(pygame.math.Vector2(mat.x, mat.y)) < 300:
                        overlap = True
                if not overlap:
                    self.materials.append(Material(cx, cy))
                    self.materials_spawned_count += 1

        # Spawn Energy Cells only in PLASMA
        if self.current_zone == 'PLASMA':
            cell_chance = 0.35
            if random.random() < cell_chance:
                cx = random.randint(-2600, 2600)
                cy = random.randint(min_y, max_y)
                overlap = False
                for cell in self.energy_cells:
                    if pygame.math.Vector2(cx, cy).distance_to(pygame.math.Vector2(cell.x, cell.y)) < 300:
                        overlap = True
                if not overlap:
                    self.energy_cells.append(EnergyCell(cx, cy))

        theme_color = BIOME_CONFIGS.get(self.current_zone, {}).get('theme_color', PURPLE)
        for _ in range(random.randint(3, 5)):
            gx = random.randint(-2600, 2600)
            gy = random.randint(min_y, max_y)
            self.gas_clouds.append(GasCloud(gx, gy, theme_color))
            
        num_derelicts = random.randint(1, 3) if self.current_zone in ('ASTEROIDS', 'VULCAN', 'AQUARIS') else random.randint(0, 2)
        for _ in range(num_derelicts):
            dx = random.randint(-2600, 2600)
            dy = random.randint(min_y, max_y)
            self.derelicts.append(DerelictHull(dx, dy))
            
        if random.random() < 0.6:  # 60% chance per chunk
            ax = random.randint(-2600, 2600)
            ay = random.randint(min_y, max_y)
            self.anomalies.append(Anomaly(ax, ay))
                
        # Spawn level-specific gimmicks
        if self.current_zone == 'AQUARIS':
            for _ in range(random.randint(2, 4)):
                cx = random.randint(-2600, 2600)
                cy = random.randint(min_y, max_y)
                self.shield_crystals.append(ShieldCrystal(cx, cy))
        elif self.current_zone == 'ASTEROIDS':
            for _ in range(random.randint(1, 2)):
                gx = random.randint(-2600, 2600)
                gy = random.randint(min_y, max_y)
                self.gravity_wells.append(GravityWell(gx, gy))

        # Spawn Data Uplink terminals in starting levels
        if self.current_zone in ('ASTEROIDS', 'VULCAN', 'AQUARIS'):
            if random.random() < 0.35:
                dx = random.randint(-2600, 2600)
                dy = random.randint(min_y, max_y)
                self.data_uplinks.append(DataUplink(dx, dy))

        # Spawn small bypass portals with a 15% chance per chunk
        if random.random() < 0.15:
            px = random.randint(-2600, 2600)
            py = random.randint(min_y, max_y)
            self.small_portals.append(SmallPortal(px, py))

    def spawn_explosion(self, x, y, color_palette, count=15):
        if count >= 10 and SOUNDS:
            SOUNDS.play('explosion')
        for _ in range(count):
            color = random.choice(color_palette)
            self.particles.append(Particle(x, y, color))
        if count >= 10:
            ring_color = color_palette[0] if color_palette else CYAN
            self.shockwaves.append(ShockwaveRing(x, y, count * 3, ring_color))
        self.screen_shake = min(15, self.screen_shake + int(count * 0.5))

    def _damage_player(self, current_time, damage=1.0, sound_type='hit'):
        if damage <= 0:
            return
        if self.player.is_dead or self.player.invulnerable or self.debug_invincible:
            return
        if SOUNDS: SOUNDS.play(sound_type)
        
        had_shields = self.player.shields > 0
        if self.player.shields > 0:
            self.player.shield_bubble_timer = current_time
        self.player.shields -= damage
        if had_shields and self.player.shields <= 0 and not self.player.is_dead:
            recharges_remaining = self.player.skills.get('emergency_recharge', 0)
            used_count = getattr(self, '_emergency_recharge_used', 0)
            if recharges_remaining > used_count:
                self._emergency_recharge_used = used_count + 1
                self.player.shields = self.player.max_shields * 0.5
                if SOUNDS: SOUNDS.play('shield_recharge')
                for _ in range(25):
                    self.particles.append(Particle(self.player.x + self.player.width//2, self.player.y + self.player.height//2, CYAN))
            else:
                if SOUNDS: SOUNDS.play('shield_down')
        self.player.last_hit_time = current_time
        self.player.last_regen_time = current_time
        self.player.invulnerable = True
        self.player.invulnerable_time = current_time
        self.screen_shake = 15
        
        self.spawn_explosion(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2,
                             [(255, 255, 0), (255, 0, 0)], 15)
        
        if self.player.shields < 0 and not self.player.is_dead:
            self.player.is_dead = True
            self.player_death_timer = 90
            self.player.invulnerable = False

    def detonate_anomaly(self, anomaly):
        if anomaly in self.anomalies: self.anomalies.remove(anomaly)
        self.spawn_explosion(anomaly.x, anomaly.y, [(255, 0, 255), (0, 255, 255), (255, 255, 255)], 60)
        self.screen_shake = max(self.screen_shake, 35)
        radius = 160 # Reduced from 350
        anomaly_pos = pygame.math.Vector2(anomaly.x, anomaly.y)
        
        for enemy in self.enemies[:]:
            if anomaly_pos.distance_to(pygame.math.Vector2(enemy.rect.center)) < radius:
                enemy.health -= 20
                if enemy.health <= 0: self._kill_enemy(enemy)
                
        for meteor in self.meteors[:]:
            if anomaly_pos.distance_to(pygame.math.Vector2(meteor.rect.center)) < radius:
                self._destroy_meteor(meteor)
                
        for obs in self.static_obstacles[:]:
            if anomaly_pos.distance_to(pygame.math.Vector2(obs.rect.center)) < radius:
                if obs in self.static_obstacles: self.static_obstacles.remove(obs)
                self.spawn_explosion(obs.rect.centerx, obs.rect.centery, [(128, 128, 128)], 10)
                
        for d in self.derelicts[:]:
            if anomaly_pos.distance_to(pygame.math.Vector2(d.rect.center)) < radius:
                d.health = 0
                self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                for _ in range(random.randint(5, 10)):
                    self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                if d in self.derelicts: self.derelicts.remove(d)
                
        for eb in self.enemy_bullets[:]:
            if anomaly_pos.distance_to(pygame.math.Vector2(eb.x, eb.y)) < radius:
                if eb in self.enemy_bullets: self.enemy_bullets.remove(eb)

        if anomaly_pos.distance_to(pygame.math.Vector2(self.player.rect.center)) < radius:
            self._damage_player(pygame.time.get_ticks(), damage=4)
            
        # Chain reaction
        for a in self.anomalies[:]:
            if anomaly_pos.distance_to(pygame.math.Vector2(a.rect.center)) < radius:
                self.detonate_anomaly(a)

    def draw_part_icon(self, screen, x, y, key, color, ticks):
        hex_pts = []
        for a in range(6):
            ang = math.radians(a * 60 - 30)
            hex_pts.append((x + 11 * math.cos(ang), y + 11 * math.sin(ang)))
        pygame.draw.polygon(screen, (30, 30, 45), hex_pts)
        pygame.draw.polygon(screen, color, hex_pts, 1)
        
        if key in ('shield', 'deflector', 'emergency_recharge'):
            pygame.draw.polygon(screen, color, [
                (x, y - 6), (x + 6, y - 3), (x + 5, y + 3), (x, y + 7), (x - 5, y + 3), (x - 6, y - 3)
            ], 1)
            pygame.draw.line(screen, color, (x, y - 3), (x, y + 4))
        elif key in ('coolant', 'nanite_repair'):
            if key == 'coolant':
                pygame.draw.lines(screen, color, True, [
                    (x, y - 7), (x + 4, y - 1), (x + 4, y + 5), (x - 4, y + 5), (x - 4, y - 1)
                ], 1)
            else:
                pygame.draw.line(screen, color, (x - 5, y), (x + 5, y), 2)
                pygame.draw.line(screen, color, (x, y - 5), (x, y + 5), 2)
        elif key in ('class_tier1', 'class_tier2', 'class_tier3'):
            pygame.draw.lines(screen, color, False, [
                (x - 5, y - 3), (x, y - 7), (x + 5, y - 3)
            ], 1)
            pygame.draw.lines(screen, color, False, [
                (x - 5, y + 1), (x, y - 3), (x + 5, y + 1)
            ], 1)
        elif key in ('afterburner', 'vector_nozzle', 'hyperdrive'):
            pygame.draw.polygon(screen, color, [
                (x - 4, y - 5), (x + 4, y - 5), (x + 6, y + 3), (x - 6, y + 3)
            ], 1)
            pygame.draw.line(screen, ORANGE, (x, y + 3), (x, y + 7))
        elif key in ('weapon', 'overcharge', 'shotgun_unlocked', 'railgun_unlocked', 'shotgun_mod', 'railgun_mod'):
            pygame.draw.circle(screen, color, (x, y), 6, width=1)
            pygame.draw.line(screen, color, (x - 8, y), (x + 8, y))
            pygame.draw.line(screen, color, (x, y - 8), (x, y + 8))
        elif key in ('torpedo', 'cluster_torpedo', 'bomb_unlocked', 'missile_unlocked', 'bomb_cap', 'missile_cap', 'ammo_loader'):
            pygame.draw.polygon(screen, color, [
                (x, y - 7), (x - 4, y + 1), (x - 3, y + 6), (x + 3, y + 6), (x + 4, y + 1)
            ], 1)
        else:
            pygame.draw.circle(screen, color, (x, y), 4)

    def get_all_parts(self):
        all_parts = {
            # --- ENGINEERING / SHIELD slot ---
            'shield':           {'name': 'Shield Gen',    'slot': 'SHIELD',  'type': 'ENGINEERING', 'max_level': 4,
                                 'icon_color': (0, 180, 255),
                                 'desc': '+1 Max Shield per rank (up to 4 ranks).',
                                 'cost_func': lambda p: (p.skills['shield'] + 1) * 75,
                                 'scrap_func': lambda p: (p.skills['shield'] + 1) * 1,   'deps': []},
            'deflector':        {'name': 'Deflector',     'slot': 'SHIELD',  'type': 'ENGINEERING', 'max_level': 1,
                                 'icon_color': (0, 140, 220),
                                 'desc': 'Cuts shield recharge delay from 5 s → 3 s.',
                                 'cost_func': lambda p: 200,
                                 'scrap_func': lambda p: 3,                              'deps': [('shield', 2)]},
            'emergency_recharge':{'name': 'E-Recharge',   'slot': 'SHIELD',  'type': 'ENGINEERING', 'max_level': 2,
                                 'icon_color': (60, 210, 255),
                                 'desc': 'Restores 50 % of max shield once on depletion.',
                                 'cost_func': lambda p: (p.skills['emergency_recharge'] + 1) * 150,
                                 'scrap_func': lambda p: (p.skills['emergency_recharge'] + 1) * 3, 'deps': [('shield', 2)]},
            # --- ENGINEERING / CORE slot ---
            'coolant':          {'name': 'Coolant',       'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 4,
                                 'icon_color': (0, 255, 200),
                                 'desc': '+25 % weapon cool-down rate per rank.',
                                 'cost_func': lambda p: (p.skills['coolant'] + 1) * 60,
                                 'scrap_func': lambda p: (p.skills['coolant'] + 1) * 1, 'deps': []},
            'nanite_repair':    {'name': 'Nanite Rep',    'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 3,
                                 'icon_color': (0, 255, 150),
                                 'desc': '+0.003 passive shield regen per frame per rank.',
                                 'cost_func': lambda p: (p.skills['nanite_repair'] + 1) * 120,
                                 'scrap_func': lambda p: (p.skills['nanite_repair'] + 1) * 2, 'deps': [('coolant', 1)]},
            'class_tier1':      {'name': self.player.class_upgrades.get('tier1_name', 'Class Upgrade I'),
                                 'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 3,
                                 'icon_color': (180, 100, 255),
                                 'desc': self.player.class_upgrades.get('tier1_desc', 'Class trait upgrade.'),
                                 'cost_func': lambda p: (p.skills['class_tier1'] + 1) * 120,
                                 'scrap_func': lambda p: (p.skills['class_tier1'] + 1) * 2, 'deps': []},
            'class_tier2':      {'name': self.player.class_upgrades.get('tier2_name', 'Class Upgrade II'),
                                 'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 2,
                                 'icon_color': (200, 120, 255),
                                 'desc': self.player.class_upgrades.get('tier2_desc', 'Advanced class trait.'),
                                 'cost_func': lambda p: (p.skills['class_tier2'] + 1) * 180,
                                 'scrap_func': lambda p: (p.skills['class_tier2'] + 1) * 3, 'deps': [('class_tier1', 1)]},
            'class_tier3':      {'name': self.player.class_upgrades.get('tier3_name', 'Class Upgrade III'),
                                 'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 1,
                                 'icon_color': (230, 150, 255),
                                 'desc': self.player.class_upgrades.get('tier3_desc', 'Elite class specialisation.'),
                                 'cost_func': lambda p: 350,
                                 'scrap_func': lambda p: 5, 'deps': [('class_tier2', 1)]},
            # --- ENGINEERING / ENGINE slot ---
            'hyperdrive':       {'name': 'Hyperdrive',    'slot': 'ENGINE',  'type': 'ENGINEERING', 'max_level': 1,
                                 'icon_color': (255, 200, 0),
                                 'desc': 'Reduces warp charge delay 3 s → 1 s.',
                                 'cost_func': lambda p: 350,
                                 'scrap_func': lambda p: 6, 'deps': [('shield', 2), ('coolant', 2)]},
            'afterburner':      {'name': 'Afterburner',   'slot': 'ENGINE',  'type': 'ENGINEERING', 'max_level': 3,
                                 'icon_color': (255, 140, 0),
                                 'desc': '+20 % dash burst speed per rank.',
                                 'cost_func': lambda p: (p.skills['afterburner'] + 1) * 100,
                                 'scrap_func': lambda p: (p.skills['afterburner'] + 1) * 2, 'deps': []},
            'vector_nozzle':    {'name': 'Vector Nozzle', 'slot': 'ENGINE',  'type': 'ENGINEERING', 'max_level': 3,
                                 'icon_color': (255, 170, 50),
                                 'desc': '+20 % turn rate per rank.',
                                 'cost_func': lambda p: (p.skills['vector_nozzle'] + 1) * 80,
                                 'scrap_func': lambda p: (p.skills['vector_nozzle'] + 1) * 2, 'deps': []},
            # --- WEAPONRY / WEAPON slot ---
            'weapon':           {'name': 'Multi-Cannon',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                 'icon_color': (255, 80, 80),
                                 'desc': 'Unlocks dual Laser fire mode.',
                                 'cost_func': lambda p: 200,
                                 'scrap_func': lambda p: 4, 'deps': []},
            'overcharge':       {'name': 'Overcharger',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                 'icon_color': (255, 50, 50),
                                 'desc': 'Laser fire-rate -30 % shoot delay.',
                                 'cost_func': lambda p: 250,
                                 'scrap_func': lambda p: 4, 'deps': [('weapon', 1)]},
            'shotgun_unlocked': {'name': 'Buy Shotgun',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                 'icon_color': (200, 80, 40),
                                 'desc': 'Unlock CQC Scatter Shotgun primary.',
                                 'cost_func': lambda p: 300,
                                 'scrap_func': lambda p: 5, 'deps': []},
            'shotgun_mod':      {'name': 'Shotgun Tune',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                 'icon_color': (220, 100, 60),
                                 'desc': '+15 % shotgun stats per rank.',
                                 'cost_func': lambda p: (p.skills['shotgun_mod'] + 1) * 100,
                                 'scrap_func': lambda p: (p.skills['shotgun_mod'] + 1) * 2, 'deps': [('shotgun_unlocked', 1)]},
            'railgun_unlocked': {'name': 'Buy Railgun',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                 'icon_color': (160, 60, 200),
                                 'desc': 'Unlock Tachyonic Railgun primary.',
                                 'cost_func': lambda p: 500,
                                 'scrap_func': lambda p: 10, 'deps': []},
            'railgun_mod':      {'name': 'Railgun Tune',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                 'icon_color': (180, 80, 220),
                                 'desc': 'Reduce charge delay & boost projectile velocity.',
                                 'cost_func': lambda p: (p.skills['railgun_mod'] + 1) * 150,
                                 'scrap_func': lambda p: (p.skills['railgun_mod'] + 1) * 4, 'deps': [('railgun_unlocked', 1)]},
            'torpedo':          {'name': 'Fusion Torpedo', 'slot': 'WEAPON', 'type': 'WEAPONRY',    'max_level': 4,
                                 'icon_color': (255, 200, 0),
                                 'desc': '-15 % cooldown, +15 % blast radius per rank.',
                                 'cost_func': lambda p: (p.skills['torpedo'] + 1) * 80,
                                 'scrap_func': lambda p: (p.skills['torpedo'] + 1) * 1, 'deps': []},
            'cluster_torpedo':  {'name': 'Cluster War',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                 'icon_color': (255, 220, 30),
                                 'desc': 'Torpedo spawns 3 secondary blasts on impact.',
                                 'cost_func': lambda p: 300,
                                 'scrap_func': lambda p: 5, 'deps': [('torpedo', 2)]},
            'bomb_unlocked':    {'name': 'Buy Prox Bomb', 'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                 'icon_color': (200, 120, 0),
                                 'desc': 'Unlock Proximity-fused Detonation Bomb.',
                                 'cost_func': lambda p: 200,
                                 'scrap_func': lambda p: 3, 'deps': []},
            'bomb_cap':         {'name': 'Bomb Payload',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                 'icon_color': (220, 140, 20),
                                 'desc': '+1 max bomb cap & larger blast radius per rank.',
                                 'cost_func': lambda p: (p.skills['bomb_cap'] + 1) * 80,
                                 'scrap_func': lambda p: (p.skills['bomb_cap'] + 1) * 2, 'deps': [('bomb_unlocked', 1)]},
            'missile_unlocked': {'name': 'Buy Missile',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                 'icon_color': (100, 200, 80),
                                 'desc': 'Unlock Smart-Targeting Homing Missile.',
                                 'cost_func': lambda p: 400,
                                 'scrap_func': lambda p: 7, 'deps': []},
            'missile_cap':      {'name': 'Missile Pay',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                 'icon_color': (120, 220, 100),
                                 'desc': '+1 max missile cap & +20 % flight speed per rank.',
                                 'cost_func': lambda p: (p.skills['missile_cap'] + 1) * 120,
                                 'scrap_func': lambda p: (p.skills['missile_cap'] + 1) * 3, 'deps': [('missile_unlocked', 1)]},
            'ammo_loader':      {'name': 'Ammo Loader',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                 'icon_color': (80, 220, 180),
                                 'desc': '+2 max ammo cap for all secondary weapons per rank.',
                                 'cost_func': lambda p: (p.skills['ammo_loader'] + 1) * 100,
                                 'scrap_func': lambda p: (p.skills['ammo_loader'] + 1) * 2, 'deps': []},
        }
        coords = {
            'shield': (0, 0, 'SHIELD'), 'deflector': (0, 1, 'SHIELD'), 'emergency_recharge': (0, 2, 'SHIELD'),
            'coolant': (1, 0, 'CORE'), 'nanite_repair': (1, 1, 'CORE'),
            'class_tier1': (2, 0, 'CORE'), 'class_tier2': (2, 1, 'CORE'), 'class_tier3': (2, 2, 'CORE'),
            'afterburner': (3, 0, 'ENGINE'), 'vector_nozzle': (3, 1, 'ENGINE'), 'hyperdrive': (3, 2, 'ENGINE'),
            
            'weapon': (0, 0, 'PRIMARY'), 'overcharge': (0, 1, 'PRIMARY'), 'ammo_loader': (0, 2, 'SECONDARY'),
            'shotgun_unlocked': (1, 0, 'PRIMARY'), 'shotgun_mod': (1, 1, 'PRIMARY'), 'bomb_unlocked': (1, 2, 'SECONDARY'), 'bomb_cap': (1, 3, 'SECONDARY'),
            'railgun_unlocked': (2, 0, 'PRIMARY'), 'railgun_mod': (2, 1, 'PRIMARY'), 'missile_unlocked': (2, 2, 'SECONDARY'), 'missile_cap': (2, 3, 'SECONDARY'),
            'torpedo': (3, 0, 'SECONDARY'), 'cluster_torpedo': (3, 1, 'SECONDARY')
        }
        for k, (c, r, s) in coords.items():
            if k in all_parts:
                all_parts[k]['col'] = c
                all_parts[k]['row'] = r
                all_parts[k]['slot'] = s
        return all_parts

    def _get_virtual_mouse_pos(self):
        mx, my = pygame.mouse.get_pos()
        vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
        vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
        return vmx, vmy

    def _handle_events(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                self._update_scaling()
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_volume = False
                self.dragging_tint = False
                self.dragging_vignette = False
                self.dragging_softness = False
                
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
                if self.dragging_volume and SOUNDS:
                    val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                    SOUNDS.set_global_volume(val)
                elif self.dragging_tint:
                    val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                    self.filter_tint_alpha = int(val * 150)
                elif self.dragging_vignette:
                    val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                    self.filter_vignette_alpha = int(val * 200)
                elif self.dragging_softness:
                    val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                    self.filter_softness = int(val * 60)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Map coordinates using current letterbox settings
                vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
                vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
                
                if getattr(self, 'dev_mode', False):
                    panel_x = VIRTUAL_WIDTH - 230
                    panel_y = 20
                    panel_w = 210
                    
                    btn_invincible = pygame.Rect(panel_x + 10, panel_y + 45, panel_w - 20, 35)
                    btn_resources = pygame.Rect(panel_x + 10, panel_y + 95, panel_w - 20, 35)
                    btn_skip_level = pygame.Rect(panel_x + 10, panel_y + 145, panel_w - 20, 35)
                    btn_skip_ending = pygame.Rect(panel_x + 10, panel_y + 195, panel_w - 20, 35)
                    
                    if btn_invincible.collidepoint(vmx, vmy):
                        self.debug_invincible = not getattr(self, 'debug_invincible', False)
                        if SOUNDS: SOUNDS.play('upgrade')
                        return
                    elif btn_resources.collidepoint(vmx, vmy):
                        self.player.credits += 1000000
                        self.player.scraps += 100000
                        if SOUNDS: SOUNDS.play('purchase')
                        return
                    elif btn_skip_level.collidepoint(vmx, vmy):
                        if self.state == 'PLAYING' and self.current_zone != 'HUB':
                            self.boss_defeated = True
                            self.boss_defeated_time = pygame.time.get_ticks()
                            self.wormhole_pos = pygame.math.Vector2(self.player.x, self.player.y - 300)
                            self.wormhole_spawned = True
                            if self.boss:
                                self.boss.is_dead = True
                            if SOUNDS: SOUNDS.play('warp')
                        return
                    elif btn_skip_ending.collidepoint(vmx, vmy):
                        self.victory_start_time = pygame.time.get_ticks()
                        self.escape_sequence_active = False
                        self.boss_defeated = False
                        self.wormhole_spawned = False
                        self.state = 'VICTORY'
                        if SOUNDS: SOUNDS.play('warp')
                        return
                        
                if self.state == 'INTRO':
                    if not self.transition_state:
                        self.transition_state = 'INTRO_TO_MAIN_MENU'
                        self.transition_start_time = pygame.time.get_ticks()
                    return

                # Sliders checks
                if self.state in ('MAIN_MENU', 'CLASS_SELECT', 'PAUSED'):
                    # Volume slider
                    if SOUNDS:
                        slider_rect = pygame.Rect(980 - 15, 25, 150 + 30, 45)
                        if slider_rect.collidepoint(vmx, vmy):
                            self.dragging_volume = True
                            val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                            SOUNDS.set_global_volume(val)
                    
                    # Tint slider (y=110)
                    tint_rect = pygame.Rect(980 - 15, 90, 150 + 30, 45)
                    if tint_rect.collidepoint(vmx, vmy):
                        self.dragging_tint = True
                        val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                        self.filter_tint_alpha = int(val * 150)
                        
                    # Vignette slider (y=175)
                    vignette_rect = pygame.Rect(980 - 15, 155, 150 + 30, 45)
                    if vignette_rect.collidepoint(vmx, vmy):
                        self.dragging_vignette = True
                        val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                        self.filter_vignette_alpha = int(val * 200)
                        
                    # Softness slider (y=240)
                    softness_rect = pygame.Rect(980 - 15, 220, 150 + 30, 45)
                    if softness_rect.collidepoint(vmx, vmy):
                        self.dragging_softness = True
                        val = max(0.0, min(1.0, (vmx - 980) / 150.0))
                        self.filter_softness = int(val * 60)
                
                if self.state == 'MAIN_MENU':
                    input_box_rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 200, 350, 400, 50)
                    has_save = SaveManager.save_exists()
                    if has_save:
                        new_game_btn = pygame.Rect(VIRTUAL_WIDTH // 2 - 210, 430, 200, 50)
                        continue_btn = pygame.Rect(VIRTUAL_WIDTH // 2 + 10, 430, 200, 50)
                    else:
                        new_game_btn = pygame.Rect(VIRTUAL_WIDTH // 2 - 100, 430, 200, 50)
                        continue_btn = None
                        
                    if input_box_rect.collidepoint(vmx, vmy):
                        self.input_active = True
                    elif new_game_btn.collidepoint(vmx, vmy):
                        self.player_name = self.player_name.strip()
                        if self.player_name != "":
                            self.input_active = False
                            self.player.name = self.player_name
                            self.state = 'CLASS_SELECT'
                    elif continue_btn and continue_btn.collidepoint(vmx, vmy):
                        self.input_active = False
                        success, msg = SaveManager.load_save(self)
                        self.save_feedback_msg = msg
                        self.save_feedback_time = pygame.time.get_ticks()
                        if success:
                            if SOUNDS: SOUNDS.play('warp')
                    else:
                        self.input_active = False
                        
                elif self.state == 'CLASS_SELECT':
                    classes = ['RANGER', 'ENGINEER', 'VANGUARD', 'SNIPER', 'ASSASSIN']
                    for idx, cls in enumerate(classes):
                        btn_rect = pygame.Rect(100 + idx * 200, 220, 180, 50)
                        if btn_rect.collidepoint(vmx, vmy):
                            self.selected_class = cls
                            self.player.set_class(self.selected_class)
                            
                    launch_btn = pygame.Rect(VIRTUAL_WIDTH // 2 - 150, 740, 300, 60)
                    if launch_btn.collidepoint(vmx, vmy):
                        self.reset_game()
                        self.player.name = self.player_name.strip()
                        self.player.set_class(self.selected_class)
                        self.state = 'HUB'
                        self.current_zone = 'HUB'

                if self.state == 'PAUSED':
                    save_btn = pygame.Rect(100, 780, 300, 45)
                    if save_btn.collidepoint(vmx, vmy):
                        success, msg = SaveManager.write_save(self)
                        self.save_feedback_msg = msg
                        self.save_feedback_time = pygame.time.get_ticks()
                        if success:
                            if SOUNDS: SOUNDS.play('collect')

                # Upgrade Shop clicks (only permitted in the Hub)
                if self.state == 'PAUSED' and self.current_zone == 'HUB' and self.hub_station_active not in ('WEAPONRY', 'ENGINEERING'):
                    # Weapon Selection logic
                    # Primary selection
                    for i in range(3):
                        rect = pygame.Rect(100 + i * 140, 520, 130, 50)
                        if rect.collidepoint(vmx, vmy):
                            if i == 0 or (i == 1 and self.player.skills['shotgun_unlocked']) or (i == 2 and self.player.skills['railgun_unlocked']):
                                self.player.active_primary = i
                    
                    # Secondary selection
                    for i in range(3):
                        rect = pygame.Rect(100 + i * 140, 680, 130, 50)
                        if rect.collidepoint(vmx, vmy):
                            if i == 0 or (i == 1 and self.player.skills['bomb_unlocked']) or (i == 2 and self.player.skills['missile_unlocked']):
                                self.player.active_secondary = i

                if self.state == 'PAUSED' and self.current_zone == 'HUB' and self.hub_station_active in ('ENGINEERING', 'WEAPONRY'):
                    all_parts = self.get_all_parts()
                    nodes_data = {
                        'shield': {'name': 'Shield Gen', 'max_level': 4, 'cost_func': lambda p: (p.skills['shield'] + 1) * 75, 'scrap_cost_func': lambda p: (p.skills['shield'] + 1) * 1, 'deps': [], 'type': 'ENGINEERING', 'slot': 'SHIELD'},
                        'deflector': {'name': 'Deflector', 'max_level': 1, 'cost_func': lambda p: 200, 'scrap_cost_func': lambda p: 3, 'deps': [('shield', 2)], 'type': 'ENGINEERING', 'slot': 'SHIELD'},
                        'emergency_recharge': {'name': 'E-Recharge', 'max_level': 2, 'cost_func': lambda p: (p.skills['emergency_recharge'] + 1) * 150, 'scrap_cost_func': lambda p: (p.skills['emergency_recharge'] + 1) * 3, 'deps': [('shield', 2)], 'type': 'ENGINEERING', 'slot': 'SHIELD'},
                        
                        'coolant': {'name': 'Coolant', 'max_level': 4, 'cost_func': lambda p: (p.skills['coolant'] + 1) * 60, 'scrap_cost_func': lambda p: (p.skills['coolant'] + 1) * 1, 'deps': [], 'type': 'ENGINEERING', 'slot': 'CORE'},
                        'nanite_repair': {'name': 'Nanite Rep', 'max_level': 3, 'cost_func': lambda p: (p.skills['nanite_repair'] + 1) * 120, 'scrap_cost_func': lambda p: (p.skills['nanite_repair'] + 1) * 2, 'deps': [('coolant', 1)], 'type': 'ENGINEERING', 'slot': 'CORE'},
                        'class_tier1': {'name': 'Class I', 'max_level': 3, 'cost_func': lambda p: (p.skills['class_tier1'] + 1) * 120, 'scrap_cost_func': lambda p: (p.skills['class_tier1'] + 1) * 2, 'deps': [], 'type': 'ENGINEERING', 'slot': 'CORE'},
                        'class_tier2': {'name': 'Class II', 'max_level': 2, 'cost_func': lambda p: (p.skills['class_tier2'] + 1) * 180, 'scrap_cost_func': lambda p: (p.skills['class_tier2'] + 1) * 3, 'deps': [('class_tier1', 1)], 'type': 'ENGINEERING', 'slot': 'CORE'},
                        'class_tier3': {'name': 'Class III', 'max_level': 1, 'cost_func': lambda p: 350, 'scrap_cost_func': lambda p: 5, 'deps': [('class_tier2', 1)], 'type': 'ENGINEERING', 'slot': 'CORE'},
                        
                        'hyperdrive': {'name': 'Hyperdrive', 'max_level': 1, 'cost_func': lambda p: 350, 'scrap_cost_func': lambda p: 6, 'deps': [('shield', 2), ('coolant', 2)], 'type': 'ENGINEERING', 'slot': 'ENGINE'},
                        'afterburner': {'name': 'Afterburner', 'max_level': 3, 'cost_func': lambda p: (p.skills['afterburner'] + 1) * 100, 'scrap_cost_func': lambda p: (p.skills['afterburner'] + 1) * 2, 'deps': [], 'type': 'ENGINEERING', 'slot': 'ENGINE'},
                        'vector_nozzle': {'name': 'Vector Noz', 'max_level': 3, 'cost_func': lambda p: (p.skills['vector_nozzle'] + 1) * 80, 'scrap_cost_func': lambda p: (p.skills['vector_nozzle'] + 1) * 2, 'deps': [], 'type': 'ENGINEERING', 'slot': 'ENGINE'},

                        'weapon': {'name': 'Multi-Cannon', 'max_level': 1, 'cost_func': lambda p: 200, 'scrap_cost_func': lambda p: 4, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'overcharge': {'name': 'Overcharger', 'max_level': 1, 'cost_func': lambda p: 250, 'scrap_cost_func': lambda p: 4, 'deps': [('weapon', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'shotgun_unlocked': {'name': 'Buy Shotgun', 'max_level': 1, 'cost_func': lambda p: 300, 'scrap_cost_func': lambda p: 5, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'shotgun_mod': {'name': 'Shotgun Tune', 'max_level': 3, 'cost_func': lambda p: (p.skills['shotgun_mod'] + 1) * 100, 'scrap_cost_func': lambda p: (p.skills['shotgun_mod'] + 1) * 2, 'deps': [('shotgun_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'railgun_unlocked': {'name': 'Buy Railgun', 'max_level': 1, 'cost_func': lambda p: 500, 'scrap_cost_func': lambda p: 10, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'railgun_mod': {'name': 'Railgun Tune', 'max_level': 3, 'cost_func': lambda p: (p.skills['railgun_mod'] + 1) * 150, 'scrap_cost_func': lambda p: (p.skills['railgun_mod'] + 1) * 4, 'deps': [('railgun_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'torpedo': {'name': 'Torpedo Sys', 'max_level': 4, 'cost_func': lambda p: (p.skills['torpedo'] + 1) * 80, 'scrap_cost_func': lambda p: (p.skills['torpedo'] + 1) * 1, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'cluster_torpedo': {'name': 'Cluster War', 'max_level': 1, 'cost_func': lambda p: 300, 'scrap_cost_func': lambda p: 5, 'deps': [('torpedo', 2)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'bomb_unlocked': {'name': 'Buy Bomb', 'max_level': 1, 'cost_func': lambda p: 200, 'scrap_cost_func': lambda p: 3, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'bomb_cap': {'name': 'Bomb Payload', 'max_level': 3, 'cost_func': lambda p: (p.skills['bomb_cap'] + 1) * 80, 'scrap_cost_func': lambda p: (p.skills['bomb_cap'] + 1) * 2, 'deps': [('bomb_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'missile_unlocked': {'name': 'Buy Missile', 'max_level': 1, 'cost_func': lambda p: 400, 'scrap_cost_func': lambda p: 7, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'missile_cap': {'name': 'Missile Pay', 'max_level': 3, 'cost_func': lambda p: (p.skills['missile_cap'] + 1) * 120, 'scrap_cost_func': lambda p: (p.skills['missile_cap'] + 1) * 3, 'deps': [('missile_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                        'ammo_loader': {'name': 'Ammo Loader', 'max_level': 3, 'cost_func': lambda p: (p.skills['ammo_loader'] + 1) * 100, 'scrap_cost_func': lambda p: (p.skills['ammo_loader'] + 1) * 2, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'}
                    }
                    
                    # 1. Grab from shelf
                    active_nodes = [k for k, n in nodes_data.items() if n['type'] == self.hub_station_active]
                    grabbed = False
                    
                    CARD_W, CARD_H = 140, 78
                    COLS = 4
                    CARD_PAD_X, CARD_PAD_Y = 6, 6
                    shelf_origin_x = 5 + 8  # shelf_panel.x + 8
                    shelf_origin_y = 175 + 30  # shelf_panel.y + 30
                    
                    for idx, key in enumerate(active_nodes):
                        part_meta = all_parts.get(key)
                        if not part_meta:
                            continue
                        col = part_meta['col']
                        row = part_meta['row']
                        node_x = shelf_origin_x + col * (CARD_W + CARD_PAD_X)
                        node_y = shelf_origin_y + row * (CARD_H + CARD_PAD_Y)
                        rect = pygame.Rect(node_x, node_y, CARD_W, CARD_H)
                        if rect.collidepoint(vmx, vmy):
                            node = nodes_data[key]
                            unlocked = True
                            for dep_key, req_lvl in node['deps']:
                                if self.player.skills[dep_key] < req_lvl:
                                    unlocked = False
                            if unlocked and (self.player.skills[key] < node['max_level'] or self.player.skills[key] > 0):
                                self.dragged_part_key = key
                                self.dragged_origin = 'SHELF'
                                self.drag_start_x = node_x + CARD_W // 2
                                self.drag_start_y = node_y + CARD_H // 2
                                self.drag_mouse_offset = (vmx - (node_x + CARD_W // 2), vmy - (node_y + CARD_H // 2))
                                if SOUNDS: SOUNDS.play('collect')
                                grabbed = True
                                break
                                
                    # 2. Grab from active ship blueprint slots
                    if not grabbed:
                        slot_coords = {
                            'ENGINE': (1000, 310),
                            'SHIELD': (870, 480),
                            'CORE': (1000, 480),
                            'PRIMARY': (1130, 410),
                            'SECONDARY': (1130, 550)
                        }
                        for slot_name, (cx, cy) in slot_coords.items():
                            dist = math.sqrt((vmx - cx)**2 + (vmy - cy)**2)
                            if dist < 35:
                                if slot_name == 'SHIELD':
                                    chosen_key = self.player.equipped_shield
                                elif slot_name == 'CORE':
                                    chosen_key = self.player.equipped_core
                                elif slot_name == 'ENGINE':
                                    chosen_key = self.player.equipped_engine
                                elif slot_name == 'PRIMARY':
                                    eq_map = {0: 'weapon', 1: 'shotgun_unlocked', 2: 'railgun_unlocked'}
                                    chosen_key = eq_map.get(self.player.active_primary)
                                elif slot_name == 'SECONDARY':
                                    eq_map = {0: 'torpedo', 1: 'bomb_unlocked', 2: 'missile_unlocked'}
                                    chosen_key = eq_map.get(self.player.active_secondary)
                                else:
                                    chosen_key = None
                                    
                                if chosen_key and self.player.skills.get(chosen_key, 0) > 0:
                                    self.dragged_part_key = chosen_key
                                    self.dragged_origin = 'SHIP_SLOT'
                                    self.drag_start_x = cx
                                    self.drag_start_y = cy
                                    self.drag_mouse_offset = (vmx - cx, vmy - cy)
                                    if SOUNDS: SOUNDS.play('collect')
                                    grabbed = True
                                    break
                                    
                    # 3. Grab from owned inventory (WEAPONS or ENGINEERING parts)
                    if not grabbed:
                        owned_items = []
                        drag_origin_type = 'OWNED_WEAPONS'
                        if self.hub_station_active == 'WEAPONRY':
                            weapon_keys = ['weapon', 'shotgun_unlocked', 'railgun_unlocked', 'torpedo', 'bomb_unlocked', 'missile_unlocked']
                            equipped_keys = []
                            eq_p = {0: 'weapon', 1: 'shotgun_unlocked', 2: 'railgun_unlocked'}.get(self.player.active_primary)
                            if eq_p and self.player.skills.get(eq_p, 0) > 0:
                                equipped_keys.append(eq_p)
                            eq_s = {0: 'torpedo', 1: 'bomb_unlocked', 2: 'missile_unlocked'}.get(self.player.active_secondary)
                            if eq_s and self.player.skills.get(eq_s, 0) > 0:
                                equipped_keys.append(eq_s)
                            owned_items = [k for k in weapon_keys if self.player.skills.get(k, 0) > 0 and k not in equipped_keys]
                            drag_origin_type = 'OWNED_WEAPONS'
                        elif self.hub_station_active == 'ENGINEERING':
                            item_keys = ['shield', 'deflector', 'emergency_recharge', 'coolant', 'nanite_repair', 'class_tier1', 'class_tier2', 'class_tier3', 'afterburner', 'vector_nozzle', 'hyperdrive']
                            equipped_keys = [self.player.equipped_shield, self.player.equipped_core, self.player.equipped_engine]
                            owned_items = [k for k in item_keys if self.player.skills.get(k, 0) > 0 and k not in equipped_keys]
                            drag_origin_type = 'OWNED_ITEMS'
                            
                        if owned_items:
                            sep_y = 650
                            if self.hub_station_active == 'WEAPONRY':
                                inv_origin_x = 640
                                cols_num = 3
                            else:
                                inv_origin_x = 820
                                cols_num = 2
                            inv_origin_y = 710
                            INV_CARD_W, INV_CARD_H = 170, 70
                            INV_PAD_X, INV_PAD_Y = 10, 10
                            for idx, key in enumerate(owned_items):
                                col = idx % cols_num
                                row = idx // cols_num
                                cx = inv_origin_x + col * (INV_CARD_W + INV_PAD_X)
                                cy = inv_origin_y + row * (INV_CARD_H + INV_PAD_Y)
                                rect = pygame.Rect(cx, cy, INV_CARD_W, INV_CARD_H)
                                if rect.collidepoint(vmx, vmy):
                                    self.dragged_part_key = key
                                    self.dragged_origin = drag_origin_type
                                    self.drag_start_x = cx + INV_CARD_W // 2
                                    self.drag_start_y = cy + INV_CARD_H // 2
                                    self.drag_mouse_offset = (vmx - (cx + INV_CARD_W // 2), vmy - (cy + INV_CARD_H // 2))
                                    if SOUNDS: SOUNDS.play('collect')
                                    grabbed = True
                                    break
                
                if self.state == 'PAUSED' and self.current_zone == 'HUB' and self.hub_station_active == 'SUPPLY':
                    items = [
                        ('Shield Repair', 75),
                        ('Torpedo Refill', 100),
                        ('Bomb Refill', 150),
                        ('Missile Refill', 200),
                        ('Flare Refill', 50),
                        ('Mod: Piercing Rounds', 300),
                        ('Mod: Split Shot', 400),
                        ('Mod: Shield Siphon', 350)
                    ]
                    for i, (name, cost) in enumerate(items):
                        rect = pygame.Rect(650, 210 + i * 80, 480, 68)
                        if rect.collidepoint(vmx, vmy):
                            if self.player.credits >= cost:
                                success = False
                                if i == 0: # Shield Repair
                                    if self.player.shields < self.player.max_shields:
                                        self.player.credits -= cost
                                        self.player.shields = min(self.player.max_shields, self.player.shields + 1)
                                        success = True
                                elif i == 1: # Torpedo Refill
                                    if self.player.torpedo_ammo < self.player.max_torpedo_ammo:
                                        self.player.credits -= cost
                                        self.player.torpedo_ammo = self.player.max_torpedo_ammo
                                        success = True
                                elif i == 2: # Bomb Refill
                                    if self.player.bomb_ammo < self.player.max_bomb_ammo:
                                        self.player.credits -= cost
                                        self.player.bomb_ammo = self.player.max_bomb_ammo
                                        success = True
                                elif i == 3: # Missile Refill
                                    if self.player.missile_ammo < self.player.max_missile_ammo:
                                        self.player.credits -= cost
                                        self.player.missile_ammo = self.player.max_missile_ammo
                                        success = True
                                elif i == 4: # Flare Refill
                                    if self.player.flare_ammo < self.player.max_flare_ammo:
                                        self.player.credits -= cost
                                        self.player.flare_ammo = self.player.max_flare_ammo
                                        success = True
                                elif i == 5: # Mod Piercing
                                    if not self.player.has_mod_piercing:
                                        self.player.credits -= cost
                                        self.player.has_mod_piercing = True
                                        success = True
                                elif i == 6: # Mod Split Shot
                                    if not self.player.has_mod_split:
                                        self.player.credits -= cost
                                        self.player.has_mod_split = True
                                        success = True
                                elif i == 7: # Mod Siphon
                                    if not self.player.has_mod_siphon:
                                        self.player.credits -= cost
                                        self.player.has_mod_siphon = True
                                        success = True
                                        
                                if success:
                                    if SOUNDS: SOUNDS.play('collect')
                                    for _ in range(15):
                                        self.particles.append(Particle(rect.centerx, rect.centery, GREEN))
                                        
                # Tutorial level guide card clicks
                if self.current_zone == 'TUTORIAL' and self.state == 'PLAYING':
                    panel_rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 350, VIRTUAL_HEIGHT - 170, 700, 140)
                    action_rect = pygame.Rect(panel_rect.x + 575, panel_rect.y + 100, 110, 30)
                    if action_rect.collidepoint(vmx, vmy):
                        if SOUNDS: SOUNDS.play('select')
                        if self.tutorial_stage < len(self.tutorial_dialogues) - 1:
                            self.tutorial_stage += 1
                        else:
                            # Finished tutorial! Return to Hub
                            self.state = 'HUB'
                            self.current_zone = 'HUB'
                            self.player.x = VIRTUAL_WIDTH // 2 - self.player.width // 2
                            self.player.y = 350
                            self.reset_game() # Clean tutorial entities
                    
                    if self.tutorial_stage > 0:
                        prev_rect = pygame.Rect(panel_rect.x + 460, panel_rect.y + 100, 100, 30)
                        if prev_rect.collidepoint(vmx, vmy):
                            if SOUNDS: SOUNDS.play('select')
                            self.tutorial_stage -= 1

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_volume = False
                self.dragging_tint = False
                self.dragging_vignette = False
                self.dragging_softness = False
                if self.state == 'PAUSED' and self.current_zone == 'HUB' and self.hub_station_active in ('ENGINEERING', 'WEAPONRY'):
                    if self.dragged_part_key is not None:
                        all_parts = self.get_all_parts()
                        nodes_data = {
                            'shield': {'name': 'Shield Gen', 'max_level': 4, 'cost_func': lambda p: (p.skills['shield'] + 1) * 75, 'scrap_cost_func': lambda p: (p.skills['shield'] + 1) * 1, 'deps': [], 'type': 'ENGINEERING', 'slot': 'SHIELD'},
                            'deflector': {'name': 'Deflector', 'max_level': 1, 'cost_func': lambda p: 200, 'scrap_cost_func': lambda p: 3, 'deps': [('shield', 2)], 'type': 'ENGINEERING', 'slot': 'SHIELD'},
                            'emergency_recharge': {'name': 'E-Recharge', 'max_level': 2, 'cost_func': lambda p: (p.skills['emergency_recharge'] + 1) * 150, 'scrap_cost_func': lambda p: (p.skills['emergency_recharge'] + 1) * 3, 'deps': [('shield', 2)], 'type': 'ENGINEERING', 'slot': 'SHIELD'},
                            'coolant': {'name': 'Coolant', 'max_level': 4, 'cost_func': lambda p: (p.skills['coolant'] + 1) * 60, 'scrap_cost_func': lambda p: (p.skills['coolant'] + 1) * 1, 'deps': [], 'type': 'ENGINEERING', 'slot': 'CORE'},
                            'nanite_repair': {'name': 'Nanite Rep', 'max_level': 3, 'cost_func': lambda p: (p.skills['nanite_repair'] + 1) * 120, 'scrap_cost_func': lambda p: (p.skills['nanite_repair'] + 1) * 2, 'deps': [('coolant', 1)], 'type': 'ENGINEERING', 'slot': 'CORE'},
                            'class_tier1': {'name': 'Class I', 'max_level': 3, 'cost_func': lambda p: (p.skills['class_tier1'] + 1) * 120, 'scrap_cost_func': lambda p: (p.skills['class_tier1'] + 1) * 2, 'deps': [], 'type': 'ENGINEERING', 'slot': 'CORE'},
                            'class_tier2': {'name': 'Class II', 'max_level': 2, 'cost_func': lambda p: (p.skills['class_tier2'] + 1) * 180, 'scrap_cost_func': lambda p: (p.skills['class_tier2'] + 1) * 3, 'deps': [('class_tier1', 1)], 'type': 'ENGINEERING', 'slot': 'CORE'},
                            'class_tier3': {'name': 'Class III', 'max_level': 1, 'cost_func': lambda p: 350, 'scrap_cost_func': lambda p: 5, 'deps': [('class_tier2', 1)], 'type': 'ENGINEERING', 'slot': 'CORE'},
                            'hyperdrive': {'name': 'Hyperdrive', 'max_level': 1, 'cost_func': lambda p: 350, 'scrap_cost_func': lambda p: 6, 'deps': [('shield', 2), ('coolant', 2)], 'type': 'ENGINEERING', 'slot': 'ENGINE'},
                            'afterburner': {'name': 'Afterburner', 'max_level': 3, 'cost_func': lambda p: (p.skills['afterburner'] + 1) * 100, 'scrap_cost_func': lambda p: (p.skills['afterburner'] + 1) * 2, 'deps': [], 'type': 'ENGINEERING', 'slot': 'ENGINE'},
                            'vector_nozzle': {'name': 'Vector Noz', 'max_level': 3, 'cost_func': lambda p: (p.skills['vector_nozzle'] + 1) * 80, 'scrap_cost_func': lambda p: (p.skills['vector_nozzle'] + 1) * 2, 'deps': [], 'type': 'ENGINEERING', 'slot': 'ENGINE'},
                            'weapon': {'name': 'Multi-Cannon', 'max_level': 1, 'cost_func': lambda p: 200, 'scrap_cost_func': lambda p: 4, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'overcharge': {'name': 'Overcharger', 'max_level': 1, 'cost_func': lambda p: 250, 'scrap_cost_func': lambda p: 4, 'deps': [('weapon', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'shotgun_unlocked': {'name': 'Buy Shotgun', 'max_level': 1, 'cost_func': lambda p: 300, 'scrap_cost_func': lambda p: 5, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'shotgun_mod': {'name': 'Shotgun Tune', 'max_level': 3, 'cost_func': lambda p: (p.skills['shotgun_mod'] + 1) * 100, 'scrap_cost_func': lambda p: (p.skills['shotgun_mod'] + 1) * 2, 'deps': [('shotgun_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'railgun_unlocked': {'name': 'Buy Railgun', 'max_level': 1, 'cost_func': lambda p: 500, 'scrap_cost_func': lambda p: 10, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'railgun_mod': {'name': 'Railgun Tune', 'max_level': 3, 'cost_func': lambda p: (p.skills['railgun_mod'] + 1) * 150, 'scrap_cost_func': lambda p: (p.skills['railgun_mod'] + 1) * 4, 'deps': [('railgun_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'torpedo': {'name': 'Torpedo Sys', 'max_level': 4, 'cost_func': lambda p: (p.skills['torpedo'] + 1) * 80, 'scrap_cost_func': lambda p: (p.skills['torpedo'] + 1) * 1, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'cluster_torpedo': {'name': 'Cluster War', 'max_level': 1, 'cost_func': lambda p: 300, 'scrap_cost_func': lambda p: 5, 'deps': [('torpedo', 2)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'bomb_unlocked': {'name': 'Buy Bomb', 'max_level': 1, 'cost_func': lambda p: 200, 'scrap_cost_func': lambda p: 3, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'bomb_cap': {'name': 'Bomb Payload', 'max_level': 3, 'cost_func': lambda p: (p.skills['bomb_cap'] + 1) * 80, 'scrap_cost_func': lambda p: (p.skills['bomb_cap'] + 1) * 2, 'deps': [('bomb_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'missile_unlocked': {'name': 'Buy Missile', 'max_level': 1, 'cost_func': lambda p: 400, 'scrap_cost_func': lambda p: 7, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'missile_cap': {'name': 'Missile Pay', 'max_level': 3, 'cost_func': lambda p: (p.skills['missile_cap'] + 1) * 120, 'scrap_cost_func': lambda p: (p.skills['missile_cap'] + 1) * 3, 'deps': [('missile_unlocked', 1)], 'type': 'WEAPONRY', 'slot': 'WEAPON'},
                            'ammo_loader': {'name': 'Ammo Loader', 'max_level': 3, 'cost_func': lambda p: (p.skills['ammo_loader'] + 1) * 100, 'scrap_cost_func': lambda p: (p.skills['ammo_loader'] + 1) * 2, 'deps': [], 'type': 'WEAPONRY', 'slot': 'WEAPON'}
                        }
                        
                        node = nodes_data[self.dragged_part_key]
                        mx, my = pygame.mouse.get_pos()
                        vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
                        vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
                        
                        # Click to buy checking
                        click_dist = math.sqrt((vmx - getattr(self, 'drag_start_x', vmx))**2 + (vmy - getattr(self, 'drag_start_y', vmy))**2)
                        
                        # 1. Dropping from Shelf onto Ship Blueprint Slot (or click-to-buy)
                        if self.dragged_origin == 'SHELF':
                            target_slot = all_parts[self.dragged_part_key]['slot']
                            slot_coords = {
                                'ENGINE': (1000, 310),
                                'SHIELD': (870, 480),
                                'CORE': (1000, 480),
                                'PRIMARY': (1130, 410),
                                'SECONDARY': (1130, 550)
                            }
                            tx, ty = slot_coords[target_slot]
                            dist = math.sqrt((vmx - tx)**2 + (vmy - ty)**2)
                            if dist < 80 or (click_dist < 10):
                                is_upgrade = self.player.skills[self.dragged_part_key] < node['max_level']
                                cost = node['cost_func'](self.player)
                                scrap_cost = node['scrap_cost_func'](self.player)
                                can_afford = (self.player.credits >= cost and self.player.scraps >= scrap_cost)
                                did_action = False
                                
                                if is_upgrade and can_afford:
                                    self.player.credits -= cost
                                    self.player.scraps -= scrap_cost
                                    self.player.skills[self.dragged_part_key] += 1
                                    did_action = True
                                elif self.player.skills[self.dragged_part_key] > 0:
                                    did_action = True
                                    
                                if did_action:
                                    # Equip logic: set active selection to the new weapon/part
                                    if target_slot == 'PRIMARY':
                                        if self.dragged_part_key == 'weapon': self.player.active_primary = 0
                                        elif self.dragged_part_key == 'shotgun_unlocked': self.player.active_primary = 1
                                        elif self.dragged_part_key == 'railgun_unlocked': self.player.active_primary = 2
                                    elif target_slot == 'SECONDARY':
                                        if self.dragged_part_key == 'torpedo': self.player.active_secondary = 0
                                        elif self.dragged_part_key == 'bomb_unlocked': self.player.active_secondary = 1
                                        elif self.dragged_part_key == 'missile_unlocked': self.player.active_secondary = 2
                                    elif target_slot == 'SHIELD':
                                        self.player.equipped_shield = self.dragged_part_key
                                    elif target_slot == 'CORE':
                                        self.player.equipped_core = self.dragged_part_key
                                    elif target_slot == 'ENGINE':
                                        self.player.equipped_engine = self.dragged_part_key
                                        
                                    if SOUNDS: SOUNDS.play('warp')
                                    for _ in range(25):
                                        self.particles.append(Particle(tx, ty, CYAN))
                                        
                                    if self.dragged_part_key == 'shield':
                                        self.player.max_shields = 3 + self.player.get_active_skill('shield')
                                        self.player.shields = self.player.max_shields
                                    self.player.set_class(self.player.class_name)
                                    
                        # 2. Equipping owned weapons/items from inventory onto Ship Blueprint Slots
                        elif self.dragged_origin in ('OWNED_WEAPONS', 'OWNED_ITEMS'):
                            slot_coords = {
                                'PRIMARY': (1130, 410),
                                'SECONDARY': (1130, 550),
                                'SHIELD': (870, 480),
                                'CORE': (1000, 480),
                                'ENGINE': (1000, 310)
                            }
                            equipped = False
                            for slot_name, (cx, cy) in slot_coords.items():
                                dist = math.sqrt((vmx - cx)**2 + (vmy - cy)**2)
                                if dist < 80:
                                    target_slot = all_parts[self.dragged_part_key]['slot']
                                    if target_slot == slot_name:
                                        if target_slot == 'PRIMARY':
                                            val_map = {'weapon': 0, 'shotgun_unlocked': 1, 'railgun_unlocked': 2}
                                            self.player.active_primary = val_map[self.dragged_part_key]
                                        elif target_slot == 'SECONDARY':
                                            val_map = {'torpedo': 0, 'bomb_unlocked': 1, 'missile_unlocked': 2}
                                            self.player.active_secondary = val_map[self.dragged_part_key]
                                        elif target_slot == 'SHIELD':
                                            self.player.equipped_shield = self.dragged_part_key
                                        elif target_slot == 'CORE':
                                            self.player.equipped_core = self.dragged_part_key
                                        elif target_slot == 'ENGINE':
                                            self.player.equipped_engine = self.dragged_part_key
                                        if SOUNDS: SOUNDS.play('warp')
                                        for _ in range(25):
                                            self.particles.append(Particle(cx, cy, CYAN))
                                        equipped = True
                                        break
                            
                            # If not equipped onto slot, check if dropped into Recycling Bin
                            if not equipped:
                                bin_rect = pygame.Rect(640, 580, 150, 70)
                                if bin_rect.collidepoint(vmx, vmy):
                                    if self.player.skills[self.dragged_part_key] > 0:
                                        weapon_mods = {
                                            'weapon': 'overcharge',
                                            'shotgun_unlocked': 'shotgun_mod',
                                            'railgun_unlocked': 'railgun_mod',
                                            'torpedo': 'cluster_torpedo',
                                            'bomb_unlocked': 'bomb_cap',
                                            'missile_unlocked': 'missile_cap'
                                        }
                                        refund_scraps = 0
                                        refund_scraps += node['scrap_cost_func'](self.player)
                                        self.player.skills[self.dragged_part_key] = 0
                                        
                                        mod_key = weapon_mods.get(self.dragged_part_key)
                                        if mod_key and self.player.skills.get(mod_key, 0) > 0:
                                            mod_node = nodes_data.get(mod_key)
                                            if mod_node:
                                                refund_scraps += mod_node['scrap_cost_func'](self.player)
                                            self.player.skills[mod_key] = 0
                                            
                                        self.player.scraps += max(1, refund_scraps)
                                        if SOUNDS: SOUNDS.play('explosion')
                                        for _ in range(20):
                                            self.particles.append(Particle(vmx, vmy, GOLD))
                                        self.player.set_class(self.player.class_name)

                        # 3. Dropping from Ship Slot into Recycling Bin
                        elif self.dragged_origin == 'SHIP_SLOT':
                            bin_rect = pygame.Rect(640, 580, 150, 70)
                            if bin_rect.collidepoint(vmx, vmy):
                                if self.player.skills[self.dragged_part_key] > 0:
                                    weapon_mods = {
                                        'weapon': 'overcharge',
                                        'shotgun_unlocked': 'shotgun_mod',
                                        'railgun_unlocked': 'railgun_mod',
                                        'torpedo': 'cluster_torpedo',
                                        'bomb_unlocked': 'bomb_cap',
                                        'missile_unlocked': 'missile_cap'
                                    }
                                    refund_scraps = 0
                                    refund_scraps += node['scrap_cost_func'](self.player)
                                    self.player.skills[self.dragged_part_key] = 0
                                    
                                    if self.dragged_part_key == self.player.equipped_shield:
                                        self.player.equipped_shield = None
                                    elif self.dragged_part_key == self.player.equipped_core:
                                        self.player.equipped_core = None
                                    elif self.dragged_part_key == self.player.equipped_engine:
                                        self.player.equipped_engine = None
                                        
                                    mod_key = weapon_mods.get(self.dragged_part_key)
                                    if mod_key and self.player.skills.get(mod_key, 0) > 0:
                                        mod_node = nodes_data.get(mod_key)
                                        if mod_node:
                                            refund_scraps += mod_node['scrap_cost_func'](self.player)
                                        self.player.skills[mod_key] = 0
                                        
                                    self.player.scraps += max(1, refund_scraps)
                                    if SOUNDS: SOUNDS.play('explosion')
                                    for _ in range(20):
                                        self.particles.append(Particle(vmx, vmy, GOLD))
                                        
                                    if self.dragged_part_key == 'shield':
                                        self.player.max_shields = 3 + self.player.get_active_skill('shield')
                                        self.player.shields = min(self.player.shields, self.player.max_shields)
                                    self.player.set_class(self.player.class_name)
                                    
                        self.dragged_part_key = None

            if event.type == pygame.KEYDOWN:
                # Toggle Developer Mode with F3
                if event.key == pygame.K_F3:
                    self.dev_mode = not self.dev_mode
                    if SOUNDS: SOUNDS.play('upgrade')
                    
                if self.state == 'INTRO':
                    if not self.transition_state:
                        self.transition_state = 'INTRO_TO_MAIN_MENU'
                        self.transition_start_time = pygame.time.get_ticks()
                    return
                if self.state == 'MAIN_MENU':
                    if self.input_active:
                        if event.key == pygame.K_BACKSPACE:
                            self.player_name = self.player_name[:-1]
                        elif event.key == pygame.K_RETURN:
                            self.player_name = self.player_name.strip()
                            if self.player_name != "":
                                self.input_active = False
                                self.player.name = self.player_name
                                self.state = 'CLASS_SELECT'
                        elif len(self.player_name) < 24:
                            self.player_name += event.unicode.upper()
                    else:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            self.player_name = self.player_name.strip()
                            if self.player_name != "":
                                self.player.name = self.player_name
                                self.state = 'CLASS_SELECT'
                            
                elif self.state == 'CLASS_SELECT':
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                        if event.key == pygame.K_1:
                            self.selected_class = 'RANGER'
                        elif event.key == pygame.K_2:
                            self.selected_class = 'ENGINEER'
                        elif event.key == pygame.K_3:
                            self.selected_class = 'VANGUARD'
                        elif event.key == pygame.K_4:
                            self.selected_class = 'SNIPER'
                        elif event.key == pygame.K_5:
                            self.selected_class = 'ASSASSIN'
                        self.player.set_class(self.selected_class)
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.reset_game()
                        self.player.name = self.player_name.strip()
                        self.player.set_class(self.selected_class)
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                
                elif self.state in ('PLAYING', 'HUB'):
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.state = 'PAUSED'
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        now = pygame.time.get_ticks()
                        last_press = getattr(self, '_last_press_left', 0)
                        self._last_press_left = now
                        if now - last_press < 250:
                            if self.player.trigger_dash('LEFT', current_time):
                                # Spawn burst particles to the right (opposite to dash direction)
                                px = self.player.x + self.player.width // 2
                                py = self.player.y + self.player.height // 2
                                rad = math.radians(self.player.angle)
                                direction_vector = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                                dir_r = pygame.math.Vector2(-direction_vector.y, direction_vector.x)
                                for _ in range(15):
                                    p = Particle(px, py, (0, 255, 255))
                                    p.dx = dir_r.x * random.uniform(3, 8) + random.uniform(-2, 2)
                                    p.dy = dir_r.y * random.uniform(3, 8) + random.uniform(-2, 2)
                                    p.radius = random.randint(3, 6)
                                    p.life = random.randint(20, 40)
                                    p.max_life = p.life
                                    self.particles.append(p)
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        now = pygame.time.get_ticks()
                        last_press = getattr(self, '_last_press_right', 0)
                        self._last_press_right = now
                        if now - last_press < 250:
                            if self.player.trigger_dash('RIGHT', current_time):
                                # Spawn burst particles to the left (opposite to dash direction)
                                px = self.player.x + self.player.width // 2
                                py = self.player.y + self.player.height // 2
                                rad = math.radians(self.player.angle)
                                direction_vector = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                                dir_r = pygame.math.Vector2(-direction_vector.y, direction_vector.x)
                                for _ in range(15):
                                    p = Particle(px, py, (0, 255, 255))
                                    p.dx = -dir_r.x * random.uniform(3, 8) + random.uniform(-2, 2)
                                    p.dy = -dir_r.y * random.uniform(3, 8) + random.uniform(-2, 2)
                                    p.radius = random.randint(3, 6)
                                    p.life = random.randint(20, 40)
                                    p.max_life = p.life
                                    self.particles.append(p)
                
                elif self.state == 'PAUSED':
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.state = 'PLAYING' if self.current_zone != 'HUB' else 'HUB'
                        if self.state == 'HUB':
                            success, msg = SaveManager.write_save(self)
                            self.save_feedback_msg = "SYSTEM: AUTOSAVED" if success else "SYSTEM: AUTOSAVE FAILED"
                            self.save_feedback_time = pygame.time.get_ticks()
                    elif event.key == pygame.K_m:
                        self.state = 'MAIN_MENU'
                
                elif self.state == 'GAME_OVER':
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif event.key == pygame.K_m:
                        self.state = 'MAIN_MENU'
                        self.input_active = True
                        
                elif self.state == 'VICTORY':
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif event.key == pygame.K_m:
                        self.state = 'MAIN_MENU'
                        self.input_active = True

    def _update(self):
        current_time = pygame.time.get_ticks()
        self.zoom_level = 1.0
        
        # Dynamic Music crossfade
        if SOUNDS and SOUNDS.enabled:
            wants_boss_music = False
            if self.state in ('PLAYING', 'PAUSED'):
                boss_obj = getattr(self, 'boss', None)
                if (boss_obj and not boss_obj.is_dead) or (self.player.shields <= self.player.max_shields * 0.3):
                    wants_boss_music = True
            elif self.state == 'VICTORY':
                if SOUNDS.chan_ambient: SOUNDS.chan_ambient.set_volume(0.0)
                if SOUNDS.chan_boss: SOUNDS.chan_boss.set_volume(0.0)
                if not getattr(self, '_played_victory_music', False):
                    SOUNDS.play('victory')
                    self._played_victory_music = True
            SOUNDS.update_music(wants_boss_music)
        
        # Intro sequence processing
        if self.state == 'INTRO' or self.transition_state == 'INTRO_TO_MAIN_MENU':
            if self.state == 'INTRO':
                intro_time = current_time - getattr(self, 'intro_start_time', 0)
                if intro_time > 5500 and not self.transition_state:
                    self.transition_state = 'INTRO_TO_MAIN_MENU'
                    self.transition_start_time = current_time
            
            if self.transition_state == 'INTRO_TO_MAIN_MENU':
                elapsed = current_time - self.transition_start_time
                if elapsed >= self.transition_duration:
                    self.state = 'MAIN_MENU'
                    self.transition_state = None
                    self.input_active = True
            return  # Skip updating game objects during intro/transition
            
        # Player Death sequence processing
        if getattr(self, 'player_death_timer', 0) > 0:
            self.player_death_timer -= 1
            px = self.player.x + self.player.width // 2
            py = self.player.y + self.player.height // 2
            self.spawn_explosion(px + random.randint(-20, 20), py + random.randint(-20, 20),
                                 [(255, 69, 0), (255, 140, 0), (255, 255, 0)], 4)
            if self.player_death_timer == 0:
                self.spawn_explosion(px, py, [(255, 255, 255), (0, 255, 255), (0, 191, 255)], 45)
                self.player.credits = max(0, self.player.credits - 50)
                self.player.shields = self.player.max_shields
                self.player.heat = 0
                self.player.name = self.player_name.strip() # Ensure player name is set on reset
                self.player.overheated = False
                self.player.is_dead = False
                
                self.state = 'GAME_OVER'
                self.game_over_start_time = current_time
                self.current_zone = 'HUB'
                self.player.x = VIRTUAL_WIDTH // 2 - self.player.width // 2
                self.player.y = VIRTUAL_HEIGHT // 2 + 100
                self.bullets = []
                self.torpedoes = []
                self.enemies = []
                self.meteors = []
                self.stars_color = WHITE
                self.boss_defeated = False
                self.wormhole_spawned = False
                self.escape_sequence_active = False

        for star in self.stars:
            star[1] += star[2] * 2.0
            if star[1] > VIRTUAL_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, VIRTUAL_WIDTH)

        # Spawn Engine Particles
        keys = pygame.key.get_pressed()
        has_movement_input = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]
        if (keys[pygame.K_UP] or keys[pygame.K_w] or self.player.velocity.length() > 0.5) and not self.player.is_dead and self.state in ('PLAYING', 'HUB'):
            if has_movement_input and pygame.time.get_ticks() % 220 < 15:
                if SOUNDS: SOUNDS.play('engine')
            rad = math.radians(self.player.angle)
            dir_f = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            rear_center = pygame.math.Vector2(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2) - dir_f * (self.player.height // 2)
            
            for _ in range(2):
                p = Particle(rear_center.x + random.uniform(-4, 4), rear_center.y + random.uniform(-4, 4), random.choice([(255, 69, 0), (255, 140, 0), (255, 215, 0)]))
                p.dx = -dir_f.x * random.uniform(2, 5) + random.uniform(-1, 1)
                p.dy = -dir_f.y * random.uniform(2, 5) + random.uniform(-1, 1)
                p.radius = random.randint(2, 4)
                p.life = random.randint(10, 20)
                p.max_life = p.life
                self.particles.append(p)

        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

        for sw in self.shockwaves[:]:
            if not sw.update():
                self.shockwaves.remove(sw)

        for loot in self.loot_pickups[:]:
            loot.update()
            if not self.player.is_dead and self.player.rect.colliderect(loot.rect):
                if SOUNDS: SOUNDS.play('collect')
                self.player.apply_loot(loot)
                self.loot_pickups.remove(loot)
                self.spawn_explosion(loot.x, loot.y, [(255, 215, 0), (255, 255, 255)], 10)
            elif loot.y < self.camera_y - 200:
                self.loot_pickups.remove(loot)

        for obs in self.static_obstacles:
            obs.update()

        if self.state in ('PLAYING', 'HUB'):
            self.player.update_regen(current_time)
            
            # Spawn engine trail particles
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] or keys[pygame.K_w] or self.player.velocity.length() > 0.5:
                rear_x = self.player.x + self.player.width // 2 - self.player.direction.x * 15
                rear_y = self.player.y + self.player.height // 2 - self.player.direction.y * 15
                self.particles.append(EngineTrailParticle(rear_x, rear_y, self.player.direction, self.player.class_name))

            max_sp = self.player.max_speed * self.player.speed_multiplier
            if self.player.velocity.length() > max_sp * 1.05:
                px = self.player.x + self.player.width // 2
                py = self.player.y + self.player.height // 2
                self.spawn_explosion(px, py, [(0, 255, 255), (255, 255, 255)], count=2)

        # ---------------- HUB STATE ----------------
        if self.state == 'HUB':
            self.player.handle_input(current_time, camera_y=0, scale_info=(self.offset_x, self.offset_y, self.new_width, self.new_height), camera_x=0, is_hub=True, limit_y=True)
            player_vec = pygame.math.Vector2(self.player.rect.center)
            
            # Hub Station Detection
            self.hub_station_active = None
            if player_vec.distance_to(pygame.math.Vector2(300, 450)) < 150:
                self.hub_station_active = 'ENGINEERING'
            elif player_vec.distance_to(pygame.math.Vector2(600, 450)) < 150:
                self.hub_station_active = 'WEAPONRY'
            elif player_vec.distance_to(pygame.math.Vector2(900, 450)) < 150:
                self.hub_station_active = 'SUPPLY'

            # Check Cheat Portals collisions (if dev mode enabled)
            if getattr(self, 'dev_mode', False):
                cheat_zones = ['ASTEROIDS', 'VULCAN', 'AQUARIS', 'NEBULA', 'PLASMA', 'VOID', 'QUANTUM', 'SINGULARITY', 'ORION']
                for i, zone in enumerate(cheat_zones):
                    cx = 100 + i * 125
                    cy = 130
                    cheat_portal_pos = pygame.math.Vector2(cx, cy)
                    if player_vec.distance_to(cheat_portal_pos) < 25:
                        self.unlocked_zones[zone] = True
                        self.current_hub_index = BIOME_CONFIGS[zone]['hub']
                        self.setup_exploration_zone(zone)
                        self.wormhole_charge_timer = 0
                        self.active_hub_portal = None
                        return
                    
            # Warp Gates with Stay Timer based on active hub index
            active_portal = None
            portal_pos_vec = None
            for zone, cfg in BIOME_CONFIGS.items():
                if cfg['hub'] == self.current_hub_index and self.unlocked_zones.get(zone, False):
                    order = cfg['order']
                    if order == 0:
                        portal_pos = pygame.math.Vector2(150, 750)
                    elif order == 1:
                        portal_pos = pygame.math.Vector2(1050, 180)
                    elif order == 3:
                        portal_pos = pygame.math.Vector2(1050, 750)
                    else:
                        portal_pos = pygame.math.Vector2(150, 180)
                        
                    if player_vec.distance_to(portal_pos) < 60:
                        active_portal = zone
                        portal_pos_vec = portal_pos
                        break
                
            if active_portal and portal_pos_vec is not None:
                if self.wormhole_charge_timer == 0 and SOUNDS: SOUNDS.play('warp')
                dt = self.clock.get_time()
                self.wormhole_charge_timer += dt
                self.active_hub_portal = active_portal
                
                target_charge = 1000 if self.player.skills.get('hyperdrive', 0) > 0 else 3000
                
                # Vacuum and Zoom Effect
                charge_pct = min(1.0, self.wormhole_charge_timer / target_charge)
                self.zoom_level = 1.0 + charge_pct * 0.6
                
                # Pull player towards center
                to_portal = (portal_pos_vec - player_vec)
                if to_portal.length() > 2:
                    pull = to_portal.normalize() * (charge_pct * 5.5)
                    self.player.x += pull.x
                    self.player.y += pull.y
                    self.player.rect.x = int(self.player.x)
                    self.player.rect.y = int(self.player.y)
                    self.player.velocity *= (1.0 - charge_pct * 0.12) # Gravity friction
                
                if random.random() < 0.25:
                    self.particles.append(Particle(portal_pos_vec.x + random.randint(-120, 120), portal_pos_vec.y + random.randint(-120, 120), WHITE))

                if self.wormhole_charge_timer >= target_charge:
                    self.zoom_level = 1.0
                    self.setup_exploration_zone(active_portal)
                    self.wormhole_charge_timer = 0
                    self.active_hub_portal = None
            else:
                if getattr(self, 'active_hub_portal', None) is not None:
                    self.wormhole_charge_timer = 0
                    self.active_hub_portal = None
            return

        # ---------------- PLAYING COMBAT ZONE ----------------
        if self.state != 'PLAYING':
            return

        # Sector Collapse Environmental Damage
        if getattr(self, 'boss_defeated', False) and self.wormhole_spawned:
            # Give a few seconds of grace before sector collapse damage begins
            if current_time - getattr(self, 'boss_defeated_time', 0) > 3000:
                player_vec = pygame.math.Vector2(self.player.rect.center)
                if player_vec.distance_to(self.wormhole_pos) >= 100:
                    self.screen_shake = max(self.screen_shake, 2)
                    self.player.shields -= 0.01  # Slower drain: ~0.6 shield segments per second
                    if self.player.shields < 0 and not self.player.is_dead:
                        self.player.is_dead = True
                        self.player_death_timer = 90

        # Global Biome Physics Gimmicks
        if self.current_zone == 'VOID':
            self.player.drag = 0.99  # Less friction in the abyss
        else:
            self.player.drag = 0.96  # Standard drag

        # Screen shake from speed tamer (shake intensity based on velocity)
        speed_ratio = self.player.velocity.length() / self.player.max_speed
        if speed_ratio > 0.85:
            self.screen_shake = max(self.screen_shake, int((speed_ratio - 0.85) * 12))
            self.screen_shake = max(self.screen_shake, int((speed_ratio - 0.85) * 6))

        # Update Convoy in Level 2
        if self.current_zone == 'VULCAN' and self.convoy:
            self.convoy.update()
            
            # Decrement defend timer
            dt = self.clock.get_time()
            self.convoy_defend_timer = max(0.0, self.convoy_defend_timer - dt / 1000.0)
            
            for enemy in self.enemies:
                e_pos = pygame.math.Vector2(enemy.rect.center)
                c_pos = pygame.math.Vector2(self.convoy.rect.center)
                if e_pos.distance_to(c_pos) < 300:
                    enemy.angle = math.degrees(math.atan2(c_pos.y - e_pos.y, c_pos.x - e_pos.x))
            
            for eb in self.enemy_bullets[:]:
                if self.convoy.rect.colliderect(eb.rect):
                    self.convoy.health -= 2.0
                    self.spawn_explosion(eb.x, eb.y, [(255, 100, 0), (255, 255, 255)], 8)
                    if eb in self.enemy_bullets:
                        self.enemy_bullets.remove(eb)
            
            if self.convoy.health <= 0:
                self.spawn_explosion(self.convoy.x, self.convoy.y, [(255, 0, 0), (255, 100, 0), (255, 255, 255)], 50)
                self.convoy = None
                self.player.is_dead = True
                self.player_death_timer = 90
            elif self.convoy_defend_timer <= 0:
                if not self.wormhole_spawned:
                    self.wormhole_pos = pygame.math.Vector2(self.convoy.x, self.convoy.y - 150)
                    self.wormhole_spawned = True
                    self.boss_defeated = True
                    self.boss_defeated_time = current_time

        # Update Supernova in Level 4
        if self.current_zone == 'NEBULA' and self.supernova_y is not None:
            self.supernova_y -= self.supernova_speed
            if self.player.y >= self.supernova_y:
                self._damage_player(current_time, damage=0.45)
                self.screen_shake = max(self.screen_shake, 5)
                if random.random() < 0.1:
                    self.spawn_explosion(self.player.x + 20, self.player.y + 20, [(255, 69, 0), (255, 255, 0)], 10)
            
            if self.player.y <= -6000 and not self.wormhole_spawned:
                self.wormhole_pos = pygame.math.Vector2(self.player.x, self.player.y - 450)
                self.wormhole_spawned = True
                self.boss_defeated = True
                self.boss_defeated_time = current_time

        # Update and collect Energy Cells in Level 5
        if self.current_zone == 'PLASMA':
            for cell in self.energy_cells[:]:
                cell.update()
                if not self.player.is_dead and self.player.rect.colliderect(cell.rect):
                    if SOUNDS: SOUNDS.play('collect')
                    self.energy_cells.remove(cell)
                    self.energy_cells_collected += 1
                    self.spawn_explosion(cell.x, cell.y, [(255, 215, 0), (255, 255, 255)], 20)
                    self.player.add_credits(50)
                    self.player.award_xp(25)
            
            if self.energy_cells_collected >= 5 and not self.wormhole_spawned:
                self.wormhole_pos = pygame.math.Vector2(self.player.x, self.player.y - 450)
                self.wormhole_spawned = True
                self.boss_defeated = True
                self.boss_defeated_time = current_time
        if self.current_zone == 'QUANTUM':
            for portal in self.quantum_portals[:]:
                portal.update()
                if not self.player.is_dead and self.player.rect.colliderect(portal.rect):
                    if SOUNDS: SOUNDS.play('warp')
                    self.quantum_dimension = 'OTHER' if self.quantum_dimension == 'NORMAL' else 'NORMAL'
                    self.player.y -= 100
                    self.player.rect.topleft = (self.player.x, self.player.y)
                    self.spawn_explosion(portal.x, portal.y, [(0, 255, 100), (255, 255, 255)], 30)
            
            if self.quantum_dimension == 'OTHER':
                # Damage anchors in other dimension
                for anchor in self.quantum_anchors[:]:
                    for b in self.bullets[:]:
                        if anchor.rect.collidepoint(b.x, b.y):
                            anchor.health -= 1.0 * (self.player.damage_multiplier if hasattr(self.player, 'damage_multiplier') else 1.0)
                            self.spawn_explosion(b.x, b.y, [(0, 255, 100), (255, 255, 255)], 8)
                            if b in self.bullets: self.bullets.remove(b)
                    for tor in self.torpedoes[:]:
                        if anchor.rect.colliderect(tor.rect):
                            anchor.health -= 8.0
                            self.spawn_explosion(tor.x, tor.y, [(0, 255, 100), (255, 255, 255)], 25)
                            if tor in self.torpedoes: self.torpedoes.remove(tor)
                    
                    if anchor.health <= 0:
                        self.spawn_explosion(anchor.x, anchor.y, [(0, 255, 100), (255, 255, 255)], 40)
                        self.quantum_anchors.remove(anchor)
                        if SOUNDS: SOUNDS.play('crash')
            
            elif self.quantum_dimension == 'NORMAL' and not self.quantum_anchors and self.black_hole_core:
                # Core is now vulnerable in normal dimension!
                self.black_hole_core.update(self.player, self.enemy_bullets, self)
                
                for b in self.bullets[:]:
                    if self.black_hole_core.rect.collidepoint(b.x, b.y):
                        self.black_hole_core.health -= 1.0 * (self.player.damage_multiplier if hasattr(self.player, 'damage_multiplier') else 1.0)
                        self.spawn_explosion(b.x, b.y, [(0, 255, 100), (255, 255, 255)], 8)
                        if b in self.bullets: self.bullets.remove(b)
                for tor in self.torpedoes[:]:
                    if self.black_hole_core.rect.colliderect(tor.rect):
                        self.black_hole_core.health -= 8.0
                        self.spawn_explosion(tor.x, tor.y, [(0, 255, 100), (255, 255, 255)], 25)
                        if tor in self.torpedoes: self.torpedoes.remove(tor)
                
                if self.black_hole_core.health <= 0:
                    self.spawn_explosion(self.black_hole_core.x, self.black_hole_core.y, [(0, 255, 150), (255, 255, 255)], 60)
                    self.black_hole_core = None
                    self.wormhole_pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, -3700)
                    self.wormhole_spawned = True
                    self.boss_defeated = True
                    self.boss_defeated_time = current_time
 
        # Update Level 8 Void Hunter progression
        if self.current_zone == 'VOID':
            if self.void_enemies_killed >= 4 and not self.wormhole_spawned:
                self.wormhole_pos = pygame.math.Vector2(self.player.x, self.player.y - 450)
                self.wormhole_spawned = True
                self.boss_defeated = True
                self.boss_defeated_time = current_time

        # Camera dynamic tracking with follow inertia and velocity-based look-ahead sway
        target_cam_y = self.player.y - VIRTUAL_HEIGHT // 2 + self.player.velocity.y * 8
        target_cam_x = self.player.x - VIRTUAL_WIDTH // 2 + self.player.velocity.x * 8
        
        # Prevent camera sliding behavior when player wraps horizontally
        map_width = 5200
        if target_cam_x - self.camera_x > map_width // 2:
            self.camera_x += map_width
        elif target_cam_x - self.camera_x < -map_width // 2:
            self.camera_x -= map_width
            
        self.camera_y += (target_cam_y - self.camera_y) * 0.08
        self.camera_x += (target_cam_x - self.camera_x) * 0.08

        # Procedural surroundings generation on-the-fly!
        # Every time player advances 1000px up or down, generate next block
        if self.player.y - 1200 < self.min_y_generated:
            self._procedurally_generate_chunk(self.min_y_generated, self.min_y_generated - 1200)
            self.min_y_generated -= 1200
        if self.player.y + 1200 > self.max_y_generated:
            self._procedurally_generate_chunk(self.max_y_generated, self.max_y_generated + 1200)
            self.max_y_generated += 1200



        # Trigger Orion boss spawn after 5 seconds of entering Orion
        if self.current_zone == 'ORION' and self.boss is None and not getattr(self, 'boss_spawned_orion', False):
            if current_time - getattr(self, 'level_start_time', 0) > 5000:
                self.boss = Boss('ORION', self.player.y - 450)
                self.enemies = []
                self.meteors = []
                self.enemy_bullets = []
                self.boss_spawned_orion = True

        # Trigger Boss spawn or direct exit wormhole spawn once player has collected 5 matrix cores
        if self.materials_collected >= 5 and not self.wormhole_spawned and self.boss is None:
            cfg = BIOME_CONFIGS.get(self.current_zone, {'boss_count': 0})
            if cfg.get('boss_count', 0) > 0:
                self.boss = Boss(self.current_zone, self.player.y - 450)
                self.enemies = []
                self.meteors = []
                self.enemy_bullets = []
            else:
                self.wormhole_pos = pygame.math.Vector2(self.player.x, self.player.y - 450)
                self.wormhole_spawned = True
                self.boss_defeated = True
                self.boss_defeated_time = current_time

        # Check if player enters active wormhole
        if self.wormhole_spawned:
            player_vec = pygame.math.Vector2(self.player.rect.center)
            if player_vec.distance_to(self.wormhole_pos) < 60:
                if self.wormhole_charge_timer == 0 and SOUNDS: SOUNDS.play('warp')
                dt = self.clock.get_time()
                self.wormhole_charge_timer += dt
                
                target_charge = 1000 if self.player.skills.get('hyperdrive', 0) > 0 else 3000
                
                # Vacuum and Zoom Effect
                charge_pct = min(1.0, self.wormhole_charge_timer / target_charge)
                self.zoom_level = 1.0 + charge_pct * 0.6
                
                # Pull player towards center
                to_portal = (self.wormhole_pos - player_vec)
                if to_portal.length() > 2:
                    pull = to_portal.normalize() * (charge_pct * 5.5)
                    self.player.x += pull.x
                    self.player.y += pull.y
                    self.player.rect.x = int(self.player.x)
                    self.player.rect.y = int(self.player.y)
                    self.player.velocity *= (1.0 - charge_pct * 0.12)
                
                if random.random() < 0.25:
                    self.particles.append(Particle(self.wormhole_pos.x + random.randint(-120, 120), self.wormhole_pos.y + random.randint(-120, 120), WHITE))

                if self.wormhole_charge_timer >= target_charge:
                    if SOUNDS: SOUNDS.play('victory')
                    self.player.add_credits(250)
                    
                    # Open-world Exploration progression: 
                    # Hub 1: Asteroids -> Vulcan -> Aquaris (Unlocks Nebula & transitions hub index to 2)
                    # Hub 2: Nebula -> Plasma -> Singularity (Unlocks Quantum & transitions hub index to 3)
                    # Hub 3: Quantum -> Void -> Orion (Victory)
                    if self.current_zone == 'ASTEROIDS':
                        self.unlocked_zones['VULCAN'] = True
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'VULCAN':
                        self.unlocked_zones['AQUARIS'] = True
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'AQUARIS':
                        self.unlocked_zones['NEBULA'] = True
                        self.current_hub_index = 2
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'NEBULA':
                        self.unlocked_zones['PLASMA'] = True
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'PLASMA':
                        self.unlocked_zones['SINGULARITY'] = True
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'SINGULARITY':
                        self.unlocked_zones['QUANTUM'] = True
                        self.current_hub_index = 3
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'QUANTUM':
                        self.unlocked_zones['VOID'] = True
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'VOID':
                        self.unlocked_zones['ORION'] = True
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'ORION':
                        self.victory_start_time = pygame.time.get_ticks()
                        self.escape_sequence_active = False
                        self.state = 'VICTORY'
                    else:
                        self.escape_sequence_active = False
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                        
                    self.player.x = VIRTUAL_WIDTH // 2 - self.player.width // 2
                    self.player.y = VIRTUAL_HEIGHT // 2 + 100
                    self.bullets = []
                    self.torpedoes = []
                    self.enemies = []
                    self.meteors = []
                    self.stars_color = WHITE
                    self.wormhole_charge_timer = 0
                    self.boss_defeated = False
                    self.wormhole_spawned = False
                    self.zoom_level = 1.0
                    
                    # Trigger autosave when warping back to Hub
                    success, msg = SaveManager.write_save(self)
                    self.save_feedback_msg = "SYSTEM: AUTOSAVED" if success else "SYSTEM: AUTOSAVE FAILED"
                    self.save_feedback_time = pygame.time.get_ticks()
                    return
            else:
                self.wormhole_charge_timer = 0

        # Update Singularity Escape sequence
        if getattr(self, 'escape_sequence_active', False):
            # Grow black hole radius
            self.escape_blackhole_radius = min(1400.0, self.escape_blackhole_radius + 1.2)
            
            # Singularity escape sequence gravity pull
            core_pos = self.escape_blackhole_pos
            player_pos = pygame.math.Vector2(self.player.x + self.player.width//2, self.player.y + self.player.height//2)
            to_bh = core_pos - player_pos
            dist = to_bh.length()
            if dist > 0:
                # Stronger pull based on distance and size of black hole
                pull_strength = min(6.0, (self.escape_blackhole_radius * 1.5) / max(60.0, dist))
                self.player.x += to_bh.normalize().x * pull_strength
                self.player.y += to_bh.normalize().y * pull_strength
                self.player.rect.x = int(self.player.x)
                self.player.rect.y = int(self.player.y)
                
                # If player touches the event horizon, they take heavy damage
                event_horizon_r = self.escape_blackhole_radius * 0.45
                if dist < event_horizon_r:
                    if current_time % 30 == 0 or random.random() < 0.03:
                        self._damage_player(current_time, damage=0.5)
                        self.spawn_explosion(player_pos.x, player_pos.y, [(255, 0, 0), (255, 100, 0)], 10)

        scale_info = (self.offset_x, self.offset_y, self.new_width, self.new_height)
        new_projectiles, new_flares, new_support, new_drones, new_crystals = self.player.handle_input(current_time, self.camera_y, scale_info, camera_x=int(self.camera_x), limit_y=False)
        
        # AABB Collision pushback/sliding against indestructible FactoryStructure walls
        for obs in self.static_obstacles:
            if isinstance(obs, FactoryStructure):
                if self.player.rect.colliderect(obs.rect):
                    self._damage_player(current_time, damage=0.03) # low tick rate damage
                    overlap_left = (self.player.x + self.player.width) - obs.rect.left
                    overlap_right = obs.rect.right - self.player.x
                    overlap_top = (self.player.y + self.player.height) - obs.rect.top
                    overlap_bottom = obs.rect.bottom - self.player.y
                    
                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    if min_overlap > 0:
                        if min_overlap == overlap_left:
                            self.player.x -= overlap_left
                            self.player.velocity.x = 0
                        elif min_overlap == overlap_right:
                            self.player.x += overlap_right
                            self.player.velocity.x = 0
                        elif min_overlap == overlap_top:
                            self.player.y -= overlap_top
                            self.player.velocity.y = 0
                        else:
                            self.player.y += overlap_bottom
                            self.player.velocity.y = 0
                        
                        self.player.rect.topleft = (self.player.x, self.player.y)
        boss_ents = []
        if self.boss and not self.boss.is_dead:
            boss_ents = [ent for ent in self.boss.sub_bosses if not ent.is_dead]
        for proj in new_projectiles:
            if isinstance(proj, Torpedo):
                self.torpedoes.append(proj)
            elif isinstance(proj, ProxBomb):
                self.bombs.append(proj)
            elif isinstance(proj, HomingMissile):
                self.missiles.append(proj)
            else:
                proj.find_target(self.enemies + boss_ents, self.meteors, self.static_obstacles)
                self.bullets.append(proj)
        self.flares.extend(new_flares) # Add new flares
        self.support_ships.extend(new_support)
        self.drones.extend(new_drones)
        self.shield_crystals.extend(new_crystals)
        
        # Check Material Core collections
        for mat in self.materials[:]:
            if not self.player.is_dead and self.player.rect.colliderect(mat.rect):
                if SOUNDS: SOUNDS.play('collect')
                self.materials.remove(mat)
                self.materials_collected += 1
                self.active_quest.progress = min(self.active_quest.target, self.materials_collected)
                self.spawn_explosion(mat.x, mat.y, [(255, 165, 0), (128, 0, 128), (255, 255, 255)], 20)
                self.player.add_credits(50)
                self.player.award_xp(25)
                self._update_quests()

        # Check Scrap collections
        for scrap in self.scraps[:]:
            if not self.player.is_dead and self.player.rect.colliderect(scrap.rect):
                if SOUNDS: SOUNDS.play('collect')
                if scrap in self.scraps:
                    self.scraps.remove(scrap)
                self.player.scraps += 1
                self.spawn_explosion(scrap.x, scrap.y, [(255, 215, 0), (255, 255, 255)], 10)
                    
        # ITEM MAGNET SYSTEM
        if not self.player.is_dead:
            player_center = pygame.math.Vector2(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2)
            for collection in (self.scraps, self.materials, self.loot_pickups):
                for item in collection:
                    item_pos = pygame.math.Vector2(item.x, item.y)
                    dist = player_center.distance_to(item_pos)
                    if dist < 250:
                        pull = (player_center - item_pos).normalize() * (12.0 * (1.0 - dist / 250.0))
                        item.x += pull.x
                        item.y += pull.y
                        if hasattr(item, 'rect'):
                            item.rect.center = (int(item.x), int(item.y))

        # Update Gas Clouds
        for gc in self.gas_clouds[:]:
            pass

        # Update Derelicts
        for d in self.derelicts[:]:
            d.update()
            if not self.player.is_dead and self.player.rect.colliderect(d.rect):
                # Automatically destroy the scrap box derelicts on collision
                self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                for _ in range(random.randint(5, 10)):
                    self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                if d in self.derelicts: self.derelicts.remove(d)

        # Update Data Uplinks
        for du in self.data_uplinks[:]:
            hacked = du.update(self.player)
            if hacked:
                self.spawn_explosion(du.x, du.y, [(0, 255, 255), (0, 255, 0), (255, 255, 255)], count=35)

        # Update Anomalies
        for a in self.anomalies[:]:
            a.update()
            if not self.player.is_dead and self.player.rect.colliderect(a.rect):
                self.detonate_anomaly(a)
                
        # Update Ambient Debris (spawn based on player motion)
        if self.state == 'PLAYING' and self.player.velocity.length() > 0.5:
            if random.random() < 0.25:
                mv = self.player.velocity.normalize()
                # Spawn ahead of the player relative to screen
                ax = self.camera_x + VIRTUAL_WIDTH/2 + mv.x * (VIRTUAL_WIDTH/2 + 200) + random.randint(-600, 600)
                ay = self.camera_y + VIRTUAL_HEIGHT/2 + mv.y * (VIRTUAL_HEIGHT/2 + 200) + random.randint(-600, 600)
                # Move opposite to player travel
                self.ambient_debris.append(AmbientDebris(ax, ay, -mv.x * 3, -mv.y * 3))

        for ad in self.ambient_debris[:]:
            ad.update()
            if ad.y > self.camera_y + VIRTUAL_HEIGHT + 200:
                self.ambient_debris.remove(ad)

        if getattr(self, 'wormhole_spawned', False):
            # Preserving on-screen enemies, despawning off-screen ones
            on_screen_enemies = []
            for enemy in self.enemies:
                if (enemy.rect.right >= self.camera_x and 
                    enemy.rect.left <= self.camera_x + VIRTUAL_WIDTH and 
                    enemy.rect.bottom >= self.camera_y and 
                    enemy.rect.top <= self.camera_y + VIRTUAL_HEIGHT):
                    on_screen_enemies.append(enemy)
            self.enemies = on_screen_enemies

            # Preserving on-screen enemy bullets, despawning off-screen ones
            on_screen_bullets = []
            for eb in self.enemy_bullets:
                if (eb.rect.right >= self.camera_x and 
                    eb.rect.left <= self.camera_x + VIRTUAL_WIDTH and 
                    eb.rect.bottom >= self.camera_y and 
                    eb.rect.top <= self.camera_y + VIRTUAL_HEIGHT):
                    on_screen_bullets.append(eb)
            self.enemy_bullets = on_screen_bullets

        # Spawning parameters
        actual_enemy_delay = self.enemy_spawn_delay
        actual_meteor_delay = self.meteor_spawn_delay
        
        if self.current_zone == 'ASTEROIDS':
            actual_enemy_delay = 3500 # 45% faster
            actual_meteor_delay = 1200
        elif self.current_zone == 'VULCAN':
            actual_enemy_delay = 2500 # 48% faster
            actual_meteor_delay = 5000
        else: # Slower spawning for all other zones after asteroids/vulcan
            actual_enemy_delay = 5000 # 58% faster
            actual_meteor_delay = 4000
            
        if self.boss is None and not self.boss_defeated and not getattr(self, 'wormhole_spawned', False):
            can_spawn = True
            if self.current_zone == 'QUANTUM' and getattr(self, 'quantum_dimension', 'NORMAL') == 'NORMAL':
                can_spawn = False
            if can_spawn and current_time - self.enemy_spawn_time > actual_enemy_delay:
                # Spawning logic: Ensure enemies always appear outside the viewport
                spawn_roll = random.random()
                if spawn_roll < 0.6: # Top
                    spawn_x = int(self.camera_x) + random.randint(-250, VIRTUAL_WIDTH + 250)
                    spawn_y = self.camera_y - 250
                elif spawn_roll < 0.8: # Left
                    spawn_x = self.camera_x - 250
                    spawn_y = int(self.camera_y) + random.randint(-250, VIRTUAL_HEIGHT + 250)
                else: # Right
                    spawn_x = self.camera_x + VIRTUAL_WIDTH + 250
                    spawn_y = int(self.camera_y) + random.randint(-250, VIRTUAL_HEIGHT + 250)
                
                roll = random.random()
                if roll < 0.07: chosen_subtype = 'ELITE' # 7% Rare Miniboss
                elif roll < 0.25: chosen_subtype = 'HEAVY' # 18% Tanky
                elif roll < 0.55: chosen_subtype = 'SCOUT' # 30% Ambushing
                else: chosen_subtype = 'STANDARD' # 45% Standard
                if self.current_zone == 'VULCAN':
                    # Reduce chance of ELITE (Pyro Interceptor) in Vulcan
                    if random.random() < 0.15: # 15% chance for ELITE
                        chosen_subtype = 'ELITE'
                    else:
                        chosen_subtype = random.choice(['STANDARD', 'HEAVY', 'SCOUT']) # 85% chance for others
                self.enemies.append(Enemy(spawn_x, spawn_y, self.current_zone, chosen_subtype))
                self.enemy_spawn_time = current_time
                
            if current_time - self.meteor_spawn_time > actual_meteor_delay:
                spawn_y = self.camera_y - 50
                self.meteors.append(Meteor(random.randint(50, VIRTUAL_WIDTH - 50), spawn_y))
                self.meteor_spawn_time = current_time

        # Update Support Ships
        for ss in self.support_ships[:]:
            support_projectiles = ss.update(current_time)
            for proj in support_projectiles:
                if isinstance(proj, HomingMissile):
                    self.missiles.append(proj)
                else:
                    self.bullets.append(proj)
            if ss.life <= 0 or ss.y < self.camera_y - 300:
                self.support_ships.remove(ss)
        
        # Update Drones
        for dr in self.drones[:]:
            drone_bullets = dr.update(current_time, self.enemies + boss_ents, self.enemy_bullets)
            for b in drone_bullets:
                b.find_target(self.enemies + boss_ents + self.enemy_bullets, self.meteors, self.static_obstacles)
                self.bullets.append(b)
            if dr.life <= 0:
                self.drones.remove(dr)

        # Update flares
        for flare in self.flares[:]:
            flare.update()
            if flare.life_timer <= 0 or flare.y < self.camera_y - 200 or flare.y > self.camera_y + VIRTUAL_HEIGHT + 200:
                self.flares.remove(flare)

        
        # Update level shield crystals
        for crystal in self.shield_crystals[:]:
            crystal.update()

        # Update level gravity wells
        for gw in self.gravity_wells:
            gw.update(self.player, self.bullets, self.meteors, self.static_obstacles)

        # Update solar flare gimmick (Vulcan only)
        if self.current_zone == 'VULCAN' and (self.boss is None or not self.boss.is_dead):
            dt = self.clock.get_time()
            if self.solar_flare_state == 'IDLE':
                self.solar_flare_timer += dt
                if self.solar_flare_timer > 7000:
                    self.solar_flare_state = 'WARNING'
                    self.solar_flare_timer = 0
                    self.solar_flare_y = self.camera_y + random.randint(100, VIRTUAL_HEIGHT - 200)
            elif self.solar_flare_state == 'WARNING':
                self.solar_flare_timer += dt
                if self.solar_flare_timer > 1500:
                    self.solar_flare_state = 'ACTIVE'
                    self.solar_flare_timer = 0
                    player_center_y = self.player.y + self.player.height // 2
                    if self.solar_flare_y <= player_center_y <= self.solar_flare_y + 120:
                        shielded = False
                        player_center_x = self.player.x + self.player.width // 2
                        for obs in self.static_obstacles:
                            if isinstance(obs, FactoryStructure):
                                if obs.rect.left <= player_center_x <= obs.rect.right and obs.rect.bottom <= self.player.y <= obs.rect.bottom + 300:
                                    shielded = True
                                    break
                        if not shielded:
                            self._damage_player(current_time)
                            self.player.heat = self.player.max_heat
                            self.player.overheated = True
            elif self.solar_flare_state == 'ACTIVE':
                self.solar_flare_timer += dt
                player_center_y = self.player.y + self.player.height // 2
                if self.solar_flare_y <= player_center_y <= self.solar_flare_y + 120:
                    shielded = False
                    player_center_x = self.player.x + self.player.width // 2
                    for obs in self.static_obstacles:
                        if isinstance(obs, FactoryStructure):
                            if obs.rect.left <= player_center_x <= obs.rect.right and obs.rect.bottom <= self.player.y <= obs.rect.bottom + 300:
                                    shielded = True
                                    break
                    if not shielded:
                        self._damage_player(current_time)
                        self.player.heat = self.player.max_heat
                        self.player.overheated = True
                if self.solar_flare_timer > 800:
                    self.solar_flare_state = 'IDLE'
                    self.solar_flare_timer = 0
        
        # Update Nebula Lightning gimmick
        if self.current_zone == 'NEBULA':
            if not hasattr(self, 'lightning_timer'): self.lightning_timer = 0
            if not hasattr(self, 'lightning_pos'): self.lightning_pos = (0, 0)
            self.lightning_timer += self.clock.get_time()
            
            if self.lightning_timer > 5000: # Strike every 5s
                self.lightning_timer = 0
                lx = random.randint(int(self.camera_x), int(self.camera_x + VIRTUAL_WIDTH))
                self.lightning_pos = (lx, self.camera_y)
                self.screen_shake = 10
                # Visual strike
                self.particles.append(Particle(lx, self.player.y, WHITE))
                # Damage check
                if abs(self.player.x + self.player.width//2 - lx) < 60:
                    self._damage_player(current_time, 2)

        # Update Quantum Glitch gimmick
        if self.current_zone == 'QUANTUM':
            if random.random() < 0.01: # 1% chance per frame to glitch
                self.screen_shake = 5
                offset = random.randint(-20, 20)
                self.camera_x += offset
        
        # Update Singularity Drift gimmick
        if self.current_zone == 'SINGULARITY':
            if self.boss and not self.boss.is_dead:
                # Pull player toward the reactor core
                to_core = pygame.math.Vector2(self.boss.x, self.boss.y) - pygame.math.Vector2(self.player.x + self.player.width//2, self.player.y + self.player.height//2)
                dist = to_core.length()
                if dist > 0:
                    pull_force = min(3.5, 450.0 / max(50.0, dist))
                    self.player.x += to_core.normalize().x * pull_force
                    self.player.y += to_core.normalize().y * pull_force
            elif getattr(self, 'escape_sequence_active', False):
                # Handled separately below in the escape logic
                pass
            else:
                # Global pull downwards before boss spawns
                self.player.y += 1.2
                for e in self.enemies: e.y += 0.8

        # Update boss
        if self.boss:
            self.boss.update(current_time, self.player, self.enemy_bullets, self)
            if self.boss.is_dead and self.boss.death_timer > 120:
                for ent in self.boss.sub_bosses:
                    self.spawn_explosion(ent.x, ent.y, [(255, 255, 255), (0, 255, 255), (0, 100, 255)], 40)
                if self.current_zone == 'SINGULARITY':
                    # Start escape sequence instead of instantly ending
                    self.escape_sequence_active = True
                    self.escape_blackhole_pos = pygame.math.Vector2(self.boss.x, self.boss.y)
                    self.escape_blackhole_radius = 80.0
                    # Spawn escape wormhole inside the black hole center
                    self.wormhole_pos = pygame.math.Vector2(self.boss.x + random.randint(-500, 500), self.boss.y - 1800)
                    self.wormhole_spawned = True
                    self.boss_defeated = True
                else:
                    self.wormhole_pos = pygame.math.Vector2(self.boss.x, self.boss.y)
                    self.wormhole_spawned = True
                    self.boss_defeated = True
                self.boss_defeated_time = current_time
                self.boss = None

        # Update enemy bullets
        # Remove bullets that have expired their life_time
        for eb in self.enemy_bullets[:]:
            if eb.life_time > 0 and eb.life_timer <= 0:
                self.enemy_bullets.remove(eb)
                self.spawn_explosion(eb.x, eb.y, [(255, 100, 100), (255, 255, 255)], 6) # Explosion on self-detonate
                continue # Skip further processing for this bullet
        for eb in self.enemy_bullets[:]:
            eb.update(self.flares)
            if eb.y < self.camera_y - 100 or eb.y > self.camera_y + VIRTUAL_HEIGHT + 100:
                if eb in self.enemy_bullets:
                    self.enemy_bullets.remove(eb)
            else:
                # Enemy bullets impact with Player, Asteroids, and other Enemies
                hit = False
                if not self.player.is_dead and self.player.rect.colliderect(eb.rect):
                    self._damage_player(current_time, damage=1)
                    self._damage_player(current_time, damage=0.5)
                    hit = True
                
                if not hit:
                    for obj in self.meteors + self.static_obstacles:
                        if eb.rect.colliderect(obj.rect):
                            hit = True
                            break
                
                if hit:
                    if eb in self.enemy_bullets: self.enemy_bullets.remove(eb)
                    self.spawn_explosion(eb.x, eb.y, [(255, 100, 100), (255, 255, 255)], 6)
                for a in self.anomalies[:]:
                    if eb.rect.colliderect(a.rect):
                        if eb in self.enemy_bullets: self.enemy_bullets.remove(eb)
                        self.detonate_anomaly(a)
                
        # Update Bombs
        for b in self.bombs[:]:
            b.update()
            if b.exploded:
                if b.explosion_timer >= b.explosion_duration:
                    self.bombs.remove(b)
            else:
                # Check proximity trigger
                triggered = False
                for ent in self.enemies + boss_ents:
                    if pygame.math.Vector2(b.x, b.y).distance_to(pygame.math.Vector2(ent.rect.center)) < 80:
                        triggered = True
                        break
                if triggered:
                    self.detonate_bomb(b, boss_ents)

        # Update Homing Missiles
        for m in self.missiles[:]:
            m.update(self.enemies + boss_ents, self.camera_y, self.flares) # Pass flares to homing missiles
            if m.exploded:
                if m.explosion_timer >= m.explosion_duration:
                    self.missiles.remove(m)
            else:
                for ent in self.enemies + boss_ents:
                    if m.rect.colliderect(ent.rect):
                        self.detonate_missile(m, boss_ents)
                        break
            if m.y < self.camera_y - 200 or m.y > self.camera_y + VIRTUAL_HEIGHT + 200:
                if m in self.missiles: self.missiles.remove(m)

        # Update bullets
        for bullet in self.bullets[:]:
            # Apply gravitational pull from gravity wells (strongly attracts other projectiles)
            bullet_pos = pygame.math.Vector2(bullet.x, bullet.y)
            for eb in self.enemy_bullets:
                if getattr(eb, 'is_gravity', False):
                    gw = pygame.math.Vector2(eb.x, eb.y)
                    dist = bullet_pos.distance_to(gw)
                    if 0 < dist < 450:
                        to_gw = (gw - bullet_pos).normalize()
                        dir_vec = pygame.math.Vector2(bullet.dx, bullet.dy).normalize()
                        dir_vec += to_gw * (450 - dist) * 0.0025 # Median influence
                        dir_vec = dir_vec.normalize()
                        bullet.dx, bullet.dy = dir_vec.x, dir_vec.y

            # Quantum Bullet Phasing
            if self.current_zone == 'QUANTUM' and random.random() < 0.02:
                bullet.x += random.randint(-40, 40)

            bullet.update()
            # Bullet life/range check (Shotgun bullets die faster)
            if hasattr(bullet, 'life'): bullet.life -= 1
            bullet_life = getattr(bullet, 'life', 100)
            
            if (bullet_life <= 0 or bullet.y < self.camera_y - 100 or bullet.y > self.camera_y + VIRTUAL_HEIGHT + 100 or
                bullet.x < self.camera_x - 100 or bullet.x > self.camera_x + VIRTUAL_WIDTH + 100):
                self.bullets.remove(bullet)

        # Check gravitational projectile collisions with other player weapons (torpedoes/missiles)
        for eb in self.enemy_bullets[:]:
            if getattr(eb, 'is_gravity', False):
                for torpedo in self.torpedoes[:]:
                    if not torpedo.exploded and torpedo.rect.colliderect(eb.rect):
                        if eb in self.enemy_bullets: self.enemy_bullets.remove(eb)
                        torpedo.exploded = True
                        torpedo.explosion_timer = 0
                        self.spawn_explosion(eb.x, eb.y, [(255, 255, 255), (100, 100, 255)], 15)
                        break
                for missile in self.missiles[:]:
                    if not missile.exploded and missile.rect.colliderect(eb.rect):
                        if eb in self.enemy_bullets: self.enemy_bullets.remove(eb)
                        self.detonate_missile(missile, self.boss.sub_bosses if self.boss else [])
                        break

        # Update torpedoes
        for torpedo in self.torpedoes[:]:
            torpedo.update()
            if torpedo.exploded:
                if torpedo.explosion_timer >= torpedo.explosion_duration:
                    if torpedo in self.torpedoes:
                        self.torpedoes.remove(torpedo)
                        if self.player.skills.get('cluster_torpedo', 0) > 0 and not getattr(torpedo, 'is_sub', False):
                            for angle in (0, 120, 240):
                                rad = math.radians(angle)
                                offset_dist = 60
                                sx = torpedo.x + math.cos(rad) * offset_dist
                                sy = torpedo.y + math.sin(rad) * offset_dist
                                sub_t = Torpedo(sx, sy, 0, 0, scale=0.5)
                                sub_t.exploded = True
                                sub_t.explosion_radius = int(sub_t.explosion_radius * 0.7)
                                sub_t.is_sub = True
                                self.torpedoes.append(sub_t)
            elif (torpedo.y < self.camera_y - 100 or torpedo.y > self.camera_y + VIRTUAL_HEIGHT + 100 or
                  torpedo.x < self.camera_x - 100 or torpedo.x > self.camera_x + VIRTUAL_WIDTH + 100):
                if torpedo in self.torpedoes:
                    self.torpedoes.remove(torpedo)
        
        for enemy in self.enemies[:]:
            if getattr(enemy, 'is_phased', False): pass # Skip collision if phased
            enemy.update(current_time, self.player, self.enemy_bullets, self.bullets, self.torpedoes, self.meteors + self.static_obstacles, convoy=self.convoy)
            # Better Despawn: only remove if far from player and haven't shot recently
            dist_to_player = pygame.math.Vector2(enemy.rect.center).distance_to(pygame.math.Vector2(self.player.rect.center))
            if dist_to_player > 2000 and current_time - enemy.last_shot > 5000:
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
            elif not self.player.is_dead and self.player.rect.colliderect(enemy.rect):
                crash_dmg = 2 if enemy.subtype not in ('HEAVY', 'ELITE') else 3
                if getattr(enemy, 'zone', '') == 'AQUARIS' and getattr(enemy, 'subtype', '') == 'SCOUT': crash_dmg = 4
                if getattr(enemy, 'zone', '') == 'TUTORIAL': crash_dmg = 0
                
                # Vanguard Dash Ram
                dash_ram = getattr(self.player, 'dash_damage', 0)
                if dash_ram > 0 and current_time - self.player.last_dash < 350:
                    enemy.health -= dash_ram
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(255, 0, 0), (255, 255, 0)], 15)
                    if enemy.health <= 0:
                        self._kill_enemy(enemy)
                    continue
                    
                self._damage_player(current_time, damage=crash_dmg)
                self._kill_enemy(enemy)
        
        # Update meteors
        for meteor in self.meteors[:]:
            meteor.update()
            if not self.player.is_dead and self.player.rect.colliderect(meteor.rect):
                self._damage_player(current_time, damage=0.5, sound_type='crash')
                self._destroy_meteor(meteor)

        # Update small portals collisions (warp player forward by 2000px on entry)
        for portal in self.small_portals[:]:
            if not self.player.is_dead and self.player.rect.colliderect(portal.rect):
                if portal in self.small_portals:
                    self.small_portals.remove(portal)
                self.player.y -= 2000
                self.player.rect.y = int(self.player.y)
                self.camera_y -= 2000
                self.screen_shake = max(self.screen_shake, 35)
                if SOUNDS: SOUNDS.play('warp')
                px = self.player.x + self.player.width // 2
                py = self.player.y + self.player.height // 2
                self.spawn_explosion(px, py, [(0, 191, 255), (0, 255, 255), (255, 255, 255)], 40)
                self.enemies = [e for e in self.enemies if pygame.math.Vector2(e.rect.center).distance_to(pygame.math.Vector2(px, py)) > 400]
                self.meteors = [m for m in self.meteors if pygame.math.Vector2(m.rect.center).distance_to(pygame.math.Vector2(px, py)) > 400]

        # Update static obstacles collisions
        for obs in self.static_obstacles[:]:
            if not self.player.is_dead and self.player.rect.colliderect(obs.rect):
                if isinstance(obs, FactoryStructure):
                    # We handle pushback in the update step; only apply minor damage tick here
                    self._damage_player(current_time, damage=0.1, sound_type='crash')
                else:
                    self._damage_player(current_time, damage=0.5, sound_type='crash')
                    self.spawn_explosion(obs.x + obs.size // 2, obs.y + obs.size // 2, 
                                         [(128, 128, 128), (80, 80, 80)], 20)
                    if obs in self.static_obstacles:
                        self.static_obstacles.remove(obs)
        
        # Bullet vs Enemy Laser collision
        for bullet in self.bullets[:]:
            for eb in self.enemy_bullets[:]:
                if bullet.rect.colliderect(eb.rect):
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    if eb in self.enemy_bullets: self.enemy_bullets.remove(eb)
                    self.spawn_explosion(eb.x, eb.y, [(255, 255, 255), (100, 100, 255)], 6)
        
        # Bullet vs Enemy collision
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if abs(bullet.y - enemy.y) > 150: continue
                if getattr(enemy, 'is_phased', False): continue
                if bullet.rect.colliderect(enemy.rect):
                    if getattr(self.player, 'has_mod_siphon', False) and self.player.shields < self.player.max_shields:
                        self.player.shields = min(self.player.max_shields, self.player.shields + 0.05)
                    if not bullet.piercing and bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if self.is_enemy_shielded(enemy):
                        self.spawn_explosion(bullet.x, bullet.y, [(0, 255, 255), (255, 255, 255)], 6)
                    else:
                        enemy.health -= 0.5 * self.player.damage_multiplier
                        enemy.health -= bullet.damage * self.player.damage_multiplier
                        self.spawn_explosion(bullet.x, bullet.y, [bullet.color, WHITE], 6)
                        if SOUNDS: SOUNDS.play_spatial('metal_hit', bullet.x, bullet.y, self.player.x, self.player.y)
                        if enemy.health <= 0:
                            self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, 
                                                 [(255, 0, 0), (255, 128, 0), (255, 255, 0)], 15)
                            self._kill_enemy(enemy)
                            
            for d in self.derelicts[:]:
                if bullet.rect.colliderect(d.rect):
                    if not bullet.piercing and bullet in self.bullets:
                        self.bullets.remove(bullet)
                    d.health -= bullet.damage * self.player.damage_multiplier
                    self.spawn_explosion(bullet.x, bullet.y, [bullet.color, WHITE], 6)
                    if SOUNDS: SOUNDS.play_spatial('metal_hit', bullet.x, bullet.y, self.player.x, self.player.y)
                    if d.health <= 0:
                        self.spawn_explosion(d.x, d.y, [(200,100,50), (100,50,20)], 20)
                        for _ in range(random.randint(5, 10)):
                            self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                        if d in self.derelicts: self.derelicts.remove(d)
            for a in self.anomalies[:]:
                if bullet.rect.colliderect(a.rect):
                    if not bullet.piercing and bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.spawn_explosion(bullet.x, bullet.y, [bullet.color, WHITE], 6)
                    self.detonate_anomaly(a)
                        
        # Bullet vs Meteor collision
        for bullet in self.bullets[:]:
            for meteor in self.meteors[:]:
                if bullet.rect.colliderect(meteor.rect):
                    if not bullet.piercing and bullet in self.bullets: 
                        self.bullets.remove(bullet)
                    if meteor in self.meteors:
                        self.spawn_explosion(bullet.x, bullet.y, [bullet.color, WHITE], 6)
                        self._destroy_meteor(meteor)

        # Bullet vs Static Obstacle
        for bullet in self.bullets[:]:
            for obs in self.static_obstacles[:]:
                if bullet.rect.colliderect(obs.rect):
                    if not bullet.piercing and bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.spawn_explosion(bullet.x, bullet.y, [bullet.color, WHITE], 6)
                    if SOUNDS: SOUNDS.play_spatial('metal_hit', bullet.x, bullet.y, self.player.x, self.player.y)
                    if hasattr(obs, 'health'):
                        if isinstance(obs, FactoryStructure):
                            pass
                        else:
                            obs.health -= bullet.damage * self.player.damage_multiplier
                            if obs.health <= 0:
                                self.spawn_explosion(obs.rect.centerx, obs.rect.centery, 
                                                     [(110, 110, 115), (70, 70, 75)], 25)
                                if obs in self.static_obstacles:
                                    self.static_obstacles.remove(obs)
                                self.player.add_credits(obs.credits_value)
                    else:
                        self.spawn_explosion(obs.rect.centerx, obs.rect.centery, 
                                             [(128, 128, 128), (80, 80, 80)], 20)
                        if obs in self.static_obstacles:
                            self.static_obstacles.remove(obs)
                        self.player.add_credits(obs.credits_value)

        # Torpedo trigger and AOE logic
        for torpedo in self.torpedoes[:]:
            if not torpedo.exploded:
                hit = False
                for enemy in self.enemies:
                    if torpedo.rect.colliderect(enemy.rect):
                        hit = True
                        break
                if not hit:
                    for meteor in self.meteors:
                        if torpedo.rect.colliderect(meteor.rect):
                            hit = True
                            break
                if not hit:
                    for obs in self.static_obstacles:
                        if torpedo.rect.colliderect(obs.rect):
                            hit = True
                            break
                if not hit:
                    for d in self.derelicts:
                        if torpedo.rect.colliderect(d.rect):
                            hit = True
                            break
                if not hit:
                    for a in self.anomalies:
                        if torpedo.rect.colliderect(a.rect):
                            hit = True
                            break
                if hit:
                    torpedo.exploded = True
                    for enemy in self.enemies[:]:
                        if torpedo.rect.colliderect(enemy.rect):
                            if self.is_enemy_shielded(enemy):
                                self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(0, 255, 255), (255, 255, 255)], 10)
                            else:
                                self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, 
                                                     [(255, 0, 0), (255, 128, 0), (255, 255, 0)], 15)
                                enemy.health -= 3 * self.player.damage_multiplier
                                if enemy.health <= 0:
                                    self._kill_enemy(enemy)
                    for meteor in self.meteors[:]:
                        if torpedo.rect.colliderect(meteor.rect):
                            self._destroy_meteor(meteor)
                    for obs in self.static_obstacles[:]:
                        if torpedo.rect.colliderect(obs.rect):
                            if isinstance(obs, FactoryStructure):
                                continue
                            self.spawn_explosion(obs.rect.centerx, obs.rect.centery, 
                                                 [(128, 128, 128), (80, 80, 80)], 20)
                            if obs in self.static_obstacles:
                                self.static_obstacles.remove(obs)
                            self.player.add_credits(obs.credits_value)
                    for d in self.derelicts[:]:
                        if torpedo.rect.colliderect(d.rect):
                            d.health -= 3 * self.player.damage_multiplier
                            if d.health <= 0:
                                self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                                for _ in range(random.randint(5, 10)):
                                    self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                                if d in self.derelicts: self.derelicts.remove(d)
                    for a in self.anomalies[:]:
                        if torpedo.rect.colliderect(a.rect):
                            self.detonate_anomaly(a)

            if torpedo.exploded:
                progress = torpedo.explosion_timer / torpedo.explosion_duration
                current_radius = torpedo.explosion_radius * progress
                torpedo_center = pygame.math.Vector2(torpedo.x, torpedo.y)
                
                for enemy in self.enemies[:]:
                    enemy_center = pygame.math.Vector2(enemy.rect.center)
                    if torpedo_center.distance_to(enemy_center) <= current_radius:
                        if enemy in self.enemies:
                            if self.is_enemy_shielded(enemy):
                                self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(0, 255, 255), (255, 255, 255)], 10)
                            else:
                                self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, 
                                                     [(255, 0, 0), (255, 128, 0), (255, 255, 0)], 15)
                                enemy.health -= 1.5 * self.player.damage_multiplier
                                if enemy.health <= 0:
                                    self._kill_enemy(enemy)
                            
                for meteor in self.meteors[:]:
                    meteor_center = pygame.math.Vector2(meteor.rect.center)
                    if torpedo_center.distance_to(meteor_center) <= current_radius:
                        if meteor in self.meteors:
                            self._destroy_meteor(meteor)

                for obs in self.static_obstacles[:]:
                    obs_center = pygame.math.Vector2(obs.rect.center)
                    if torpedo_center.distance_to(obs_center) <= current_radius:
                        if obs in self.static_obstacles:
                            self.spawn_explosion(obs.rect.centerx, obs.rect.centery, 
                                                 [(128, 128, 128), (80, 80, 80)], 20)
                            self.static_obstacles.remove(obs)
                            self.player.add_credits(obs.credits_value)
                            
                for d in self.derelicts[:]:
                    obs_center = pygame.math.Vector2(d.rect.center)
                    if torpedo_center.distance_to(obs_center) <= current_radius:
                        if d in self.derelicts:
                            d.health -= 1.5 * self.player.damage_multiplier
                            self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 4)
                            if d.health <= 0:
                                self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                                for _ in range(random.randint(5, 10)):
                                    self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                                if d in self.derelicts: self.derelicts.remove(d)
                for a in self.anomalies[:]:
                    obs_center = pygame.math.Vector2(a.rect.center)
                    if torpedo_center.distance_to(obs_center) <= current_radius:
                        if a in self.anomalies:
                            self.detonate_anomaly(a)
                            
                for eb in self.enemy_bullets[:]:
                    eb_pos = pygame.math.Vector2(eb.x, eb.y)
                    if torpedo_center.distance_to(eb_pos) <= current_radius:
                        if eb in self.enemy_bullets:
                            self.spawn_explosion(eb.x, eb.y, [(255, 255, 255), (100, 100, 255)], 6)
                            self.enemy_bullets.remove(eb)

        # Player Bullet vs Shield Crystals (Level crystals & Boss crystals)
        for bullet in self.bullets[:]:
            for crystal in self.shield_crystals[:]:
                if bullet.rect.colliderect(crystal.rect):
                    if not bullet.piercing and bullet in self.bullets: 
                        self.bullets.remove(bullet)
                    crystal.health -= 0.5
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                    if crystal.health <= 0:
                        if crystal in self.shield_crystals: self.shield_crystals.remove(crystal)
                        self.player.add_credits(40)
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 25)

            if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
                for crystal in self.boss.shield_crystals[:]:
                    if crystal.health > 0 and bullet.rect.colliderect(crystal.rect):
                        if not bullet.piercing and bullet in self.bullets:
                            self.bullets.remove(bullet)
                        crystal.health -= 0.5
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                        if crystal.health <= 0:
                            self.player.add_credits(50)
                            self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 25)

        # Player Torpedo vs Shield Crystals
        for torpedo in self.torpedoes[:]:
            for crystal in self.shield_crystals[:]:
                if torpedo.rect.colliderect(crystal.rect):
                    torpedo.exploded = True
                    crystal.health -= 1
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 12)
                    if crystal.health <= 0:
                        if crystal in self.shield_crystals: self.shield_crystals.remove(crystal)
                        self.player.add_credits(40)
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 25)

            if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
                for crystal in self.boss.shield_crystals[:]:
                    if crystal.health > 0 and torpedo.rect.colliderect(crystal.rect):
                        torpedo.exploded = True
                        crystal.health -= 1
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 12)
                        if crystal.health <= 0:
                            self.player.add_credits(50)
                            self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 25)

        # Torpedo AoE vs Shield Crystals
        for torpedo in self.torpedoes[:]:
            if torpedo.exploded:
                progress = torpedo.explosion_timer / torpedo.explosion_duration
                current_radius = torpedo.explosion_radius * progress
                torpedo_center = pygame.math.Vector2(torpedo.x, torpedo.y)
                
                for crystal in self.shield_crystals[:]:
                    crystal_pos = pygame.math.Vector2(crystal.x, crystal.y)
                    if torpedo_center.distance_to(crystal_pos) <= current_radius:
                        if crystal in self.shield_crystals:
                            crystal.health -= 0.5
                            self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                            if crystal.health <= 0:
                                self.shield_crystals.remove(crystal)
                                self.player.add_credits(40)
                                self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 25)
                                
                if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
                    for crystal in self.boss.shield_crystals[:]:
                        if crystal.health > 0:
                            crystal_pos = pygame.math.Vector2(crystal.x, crystal.y)
                            if torpedo_center.distance_to(crystal_pos) <= current_radius:
                                crystal.health -= 0.5
                                self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)

        # Player Weapons vs Boss
        if self.boss and not self.boss.is_dead:
            # Bullet vs Boss
            for bullet in self.bullets[:]:
                hit_ent = None
                for ent in self.boss.sub_bosses:
                    if not ent.is_dead and bullet.rect.colliderect(ent.rect):
                        hit_ent = ent
                        break
                if hit_ent:
                        # Boss has 40% resistance towards standard bullets
                        bullet_resistance_mult = 0.60
                        hit_ent.health -= bullet.damage * self.player.damage_multiplier * bullet_resistance_mult
                        self.boss.health = sum(e.health for e in self.boss.sub_bosses if not e.is_dead)
                        self.spawn_explosion(bullet.x, bullet.y, [(255, 0, 0), (255, 128, 0)], 6)
                        if hit_ent.health <= 0:
                            hit_ent.is_dead = True
                            self.spawn_explosion(hit_ent.x, hit_ent.y, [hit_ent.color, (255, 255, 255)], 15)
                            if all(e.is_dead for e in self.boss.sub_bosses):
                                self._defeat_boss()
                                break

            # Torpedo vs Boss
            for torpedo in self.torpedoes[:]:
                if not torpedo.exploded:
                    hit_ent = None
                    for ent in self.boss.sub_bosses:
                        if not ent.is_dead and torpedo.rect.colliderect(ent.rect):
                            hit_ent = ent
                            break
                    if hit_ent:
                        torpedo.exploded = True
                        if not self.boss.shielded:
                            hit_ent.health -= 2
                            self.boss.health = sum(e.health for e in self.boss.sub_bosses if not e.is_dead)
                            self.spawn_explosion(torpedo.x, torpedo.y, [(255, 0, 0), (255, 128, 0)], 20)
                            if hit_ent.health <= 0:
                                hit_ent.is_dead = True
                                self.spawn_explosion(hit_ent.x, hit_ent.y, [hit_ent.color, (255, 255, 255)], 15)
                                if all(e.is_dead for e in self.boss.sub_bosses):
                                    self._defeat_boss()
                                    break
                else:
                    progress = torpedo.explosion_timer / torpedo.explosion_duration
                    current_radius = torpedo.explosion_radius * progress
                    torpedo_center = pygame.math.Vector2(torpedo.x, torpedo.y)
                    if not hasattr(torpedo, 'hit_subbosses'):
                        torpedo.hit_subbosses = set()
                    for ent in self.boss.sub_bosses:
                        if not ent.is_dead and ent not in torpedo.hit_subbosses:
                            ent_center = pygame.math.Vector2(ent.rect.center)
                            if torpedo_center.distance_to(ent_center) <= current_radius:
                                if not self.boss.shielded:
                                    ent.health -= 1
                                    self.boss.health = sum(e.health for e in self.boss.sub_bosses if not e.is_dead)
                                    torpedo.hit_subbosses.add(ent)
                                    if ent.health <= 0:
                                        ent.is_dead = True
                                        self.spawn_explosion(ent.x, ent.y, [ent.color, (255, 255, 255)], 15)
                                        if all(e.is_dead for e in self.boss.sub_bosses):
                                            self._defeat_boss()
                                            break

        # Seamless wrapping for all entities relative to the player
        if self.state in ('PLAYING', 'PAUSED', 'GAME_OVER'):
            map_width = 5200
            for lists in [self.bullets, self.torpedoes, self.bombs, self.missiles, 
                          self.support_ships, self.enemies, self.enemy_bullets, 
                          self.meteors, self.materials, self.scraps, self.gas_clouds, 
                          self.ambient_debris, self.derelicts, self.anomalies, self.static_obstacles,
                          self.particles, self.flares, self.loot_pickups, self.shield_crystals,
                          self.gravity_wells, self.drones]:
                for obj in lists:
                    if hasattr(obj, 'x'):
                        dx = obj.x - self.player.x
                        dx_wrapped = (dx + map_width // 2) % map_width - map_width // 2
                        x_wrapped = self.player.x + dx_wrapped
                        delta_x = x_wrapped - obj.x
                        if delta_x != 0:
                            obj.x = x_wrapped
                            if hasattr(obj, 'rect') and obj.rect is not None:
                                obj.rect.x += int(delta_x)

            if self.boss:
                dx = self.boss.x - self.player.x
                dx_wrapped = (dx + map_width // 2) % map_width - map_width // 2
                x_wrapped = self.player.x + dx_wrapped
                delta_x = x_wrapped - self.boss.x
                if delta_x != 0:
                    self.boss.x = x_wrapped
                
                for sb in self.boss.sub_bosses:
                    dx = sb.x - self.player.x
                    dx_wrapped = (dx + map_width // 2) % map_width - map_width // 2
                    x_wrapped = self.player.x + dx_wrapped
                    delta_x = x_wrapped - sb.x
                    if delta_x != 0:
                        sb.x = x_wrapped
                        if hasattr(sb, 'rect') and sb.rect is not None:
                            sb.rect.x += int(delta_x)
                
                if hasattr(self.boss, 'shield_crystals'):
                    for c in self.boss.shield_crystals:
                        dx = c.x - self.player.x
                        dx_wrapped = (dx + map_width // 2) % map_width - map_width // 2
                        x_wrapped = self.player.x + dx_wrapped
                        delta_x = x_wrapped - c.x
                        if delta_x != 0:
                            c.x = x_wrapped
                            if hasattr(c, 'rect') and c.rect is not None:
                                c.rect.x += int(delta_x)

    def is_enemy_shielded(self, enemy):
        # Shielded by level crystals
        for crystal in self.shield_crystals:
            enemy_center = pygame.math.Vector2(enemy.rect.center)
            crystal_center = pygame.math.Vector2(crystal.x, crystal.y)
            if enemy_center.distance_to(crystal_center) < 250:
                return True
        # Passive shield deflect gimmick
        if getattr(enemy, 'shield_active', False):
            return True
        return False

    def detonate_missile(self, m, boss_ents):
        m.exploded = True
        m.explosion_timer = 0
        damage_mult = self.player.damage_multiplier
        
        # 1. Direct hit damage to colliding entities
        # Check enemies
        for enemy in self.enemies[:]:
            if m.rect.colliderect(enemy.rect):
                if self.is_enemy_shielded(enemy):
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(0, 255, 255), (255, 255, 255)], 10)
                else:
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(255, 0, 0), (255, 128, 0)], 12)
                    enemy.health -= 2.4 * damage_mult
                    if enemy.health <= 0:
                        self._kill_enemy(enemy)
        
        # Check boss entities
        for ent in boss_ents:
            if m.rect.colliderect(ent.rect):
                if self.boss and not self.boss.shielded:
                    ent.health -= 1.6
                    self.boss.health = sum(e.health for e in self.boss.sub_bosses if not e.is_dead)
                    self.spawn_explosion(m.x, m.y, [(255, 0, 0), (255, 128, 0)], 15)
                    if ent.health <= 0:
                        ent.is_dead = True
                        self.spawn_explosion(ent.x, ent.y, [ent.color, (255, 255, 255)], 15)
                        if self.boss and all(e.is_dead for e in self.boss.sub_bosses):
                            self._defeat_boss()

        # Check shield crystals
        for crystal in self.shield_crystals[:]:
            if m.rect.colliderect(crystal.rect):
                crystal.health -= 0.8
                self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 10)
                if crystal.health <= 0:
                    if crystal in self.shield_crystals: self.shield_crystals.remove(crystal)
                    self.player.add_credits(40)
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
            for crystal in self.boss.shield_crystals[:]:
                if crystal.health > 0 and m.rect.colliderect(crystal.rect):
                    crystal.health -= 0.8
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 10)
                    if crystal.health <= 0:
                        self.player.add_credits(50)
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        # Check derelicts
        for d in self.derelicts[:]:
            if m.rect.colliderect(d.rect):
                d.health -= 2.4 * damage_mult
                if d.health <= 0:
                    self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                    for _ in range(random.randint(5, 10)):
                        self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                    if d in self.derelicts: self.derelicts.remove(d)

        # Check meteors
        for meteor in self.meteors[:]:
            if m.rect.colliderect(meteor.rect):
                self._destroy_meteor(meteor)

        # Check static obstacles
        for obs in self.static_obstacles[:]:
            if m.rect.colliderect(obs.rect):
                self.spawn_explosion(obs.rect.centerx, obs.rect.centery, [(128, 128, 128), (80, 80, 80)], 18)
                if obs in self.static_obstacles: self.static_obstacles.remove(obs)
                self.player.add_credits(obs.credits_value)

        # Check anomalies
        for a in self.anomalies[:]:
            if m.rect.colliderect(a.rect):
                self.detonate_anomaly(a)

        # 2. AoE / Splash damage to entities within explosion radius
        m_pos = pygame.math.Vector2(m.x, m.y)
        
        # Enemies AoE
        for enemy in self.enemies[:]:
            if m_pos.distance_to(pygame.math.Vector2(enemy.rect.center)) < m.explosion_radius:
                if self.is_enemy_shielded(enemy):
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(0, 255, 255), (255, 255, 255)], 8)
                else:
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(255, 0, 0), (255, 128, 0)], 10)
                    enemy.health -= 1.2 * damage_mult
                    if enemy.health <= 0:
                        self._kill_enemy(enemy)

        # Boss AoE
        for ent in boss_ents:
            if m_pos.distance_to(pygame.math.Vector2(ent.rect.center)) < m.explosion_radius:
                if self.boss and not self.boss.shielded:
                    ent.health -= 0.8
                    self.boss.health = sum(e.health for e in self.boss.sub_bosses if not e.is_dead)
                    self.spawn_explosion(ent.x, ent.y, [(255, 0, 0), (255, 128, 0)], 12)
                    if ent.health <= 0:
                        ent.is_dead = True
                        self.spawn_explosion(ent.x, ent.y, [ent.color, (255, 255, 255)], 15)
                        if self.boss and all(e.is_dead for e in self.boss.sub_bosses):
                            self._defeat_boss()

        # Shield crystals AoE
        for crystal in self.shield_crystals[:]:
            if m_pos.distance_to(pygame.math.Vector2(crystal.x, crystal.y)) < m.explosion_radius:
                crystal.health -= 0.4
                self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                if crystal.health <= 0:
                    if crystal in self.shield_crystals: self.shield_crystals.remove(crystal)
                    self.player.add_credits(40)
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
            for crystal in self.boss.shield_crystals[:]:
                if crystal.health > 0 and m_pos.distance_to(pygame.math.Vector2(crystal.x, crystal.y)) < m.explosion_radius:
                    crystal.health -= 0.4
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                    if crystal.health <= 0:
                        self.player.add_credits(50)
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        # Derelicts AoE
        for d in self.derelicts[:]:
            if m_pos.distance_to(pygame.math.Vector2(d.rect.center)) < m.explosion_radius:
                d.health -= 1.2 * damage_mult
                if d.health <= 0:
                    self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                    for _ in range(random.randint(5, 10)):
                        self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                    if d in self.derelicts: self.derelicts.remove(d)

        # Enemy Bullets AoE (destroy them)
        for eb in self.enemy_bullets[:]:
            if m_pos.distance_to(pygame.math.Vector2(eb.x, eb.y)) < m.explosion_radius:
                if eb in self.enemy_bullets:
                    self.spawn_explosion(eb.x, eb.y, [(255, 255, 255), (100, 100, 255)], 6)
                    self.enemy_bullets.remove(eb)

    def detonate_bomb(self, b, boss_ents):
        b.exploded = True
        b.explosion_timer = 0
        damage_mult = self.player.damage_multiplier
        
        # 1. Direct hit damage to colliding entities
        # Check enemies
        for enemy in self.enemies[:]:
            if b.rect.colliderect(enemy.rect):
                if self.is_enemy_shielded(enemy):
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(0, 255, 255), (255, 255, 255)], 10)
                else:
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(255, 0, 0), (255, 128, 0)], 18)
                    enemy.health -= 4.5 * damage_mult
                    if enemy.health <= 0:
                        self._kill_enemy(enemy)
        
        # Check boss entities
        for ent in boss_ents:
            if b.rect.colliderect(ent.rect):
                if self.boss and not self.boss.shielded:
                    ent.health -= 3.0
                    self.boss.health = sum(e.health for e in self.boss.sub_bosses if not e.is_dead)
                    self.spawn_explosion(b.x, b.y, [(255, 0, 0), (255, 128, 0)], 22)
                    if ent.health <= 0:
                        ent.is_dead = True
                        self.spawn_explosion(ent.x, ent.y, [ent.color, (255, 255, 255)], 15)
                        if self.boss and all(e.is_dead for e in self.boss.sub_bosses):
                            self._defeat_boss()

        # Check shield crystals
        for crystal in self.shield_crystals[:]:
            if b.rect.colliderect(crystal.rect):
                crystal.health -= 1.5
                self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 12)
                if crystal.health <= 0:
                    if crystal in self.shield_crystals: self.shield_crystals.remove(crystal)
                    self.player.add_credits(40)
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
            for crystal in self.boss.shield_crystals[:]:
                if crystal.health > 0 and b.rect.colliderect(crystal.rect):
                    crystal.health -= 1.5
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 12)
                    if crystal.health <= 0:
                        self.player.add_credits(50)
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        # Check derelicts
        for d in self.derelicts[:]:
            if b.rect.colliderect(d.rect):
                d.health -= 4.5 * damage_mult
                if d.health <= 0:
                    self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                    for _ in range(random.randint(5, 10)):
                        self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                    if d in self.derelicts: self.derelicts.remove(d)

        # Check meteors
        for meteor in self.meteors[:]:
            if b.rect.colliderect(meteor.rect):
                self._destroy_meteor(meteor)

        # Check static obstacles
        for obs in self.static_obstacles[:]:
            if b.rect.colliderect(obs.rect):
                if isinstance(obs, FactoryStructure):
                    continue
                self.spawn_explosion(obs.rect.centerx, obs.rect.centery, [(128, 128, 128), (80, 80, 80)], 22)
                if obs in self.static_obstacles: self.static_obstacles.remove(obs)
                self.player.add_credits(obs.credits_value)

        # Check anomalies
        for a in self.anomalies[:]:
            if b.rect.colliderect(a.rect):
                self.detonate_anomaly(a)

        # 2. AoE / Splash damage to entities within explosion radius
        b_pos = pygame.math.Vector2(b.x, b.y)
        
        # Enemies AoE
        for enemy in self.enemies[:]:
            if b_pos.distance_to(pygame.math.Vector2(enemy.rect.center)) < b.explosion_radius:
                if self.is_enemy_shielded(enemy):
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(0, 255, 255), (255, 255, 255)], 8)
                else:
                    self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(255, 0, 0), (255, 128, 0)], 12)
                    enemy.health -= 2.25 * damage_mult
                    if enemy.health <= 0:
                        self._kill_enemy(enemy)

        # Boss AoE
        for ent in boss_ents:
            if b_pos.distance_to(pygame.math.Vector2(ent.rect.center)) < b.explosion_radius:
                if self.boss and not self.boss.shielded:
                    ent.health -= 1.5
                    self.boss.health = sum(e.health for e in self.boss.sub_bosses if not e.is_dead)
                    self.spawn_explosion(ent.x, ent.y, [(255, 0, 0), (255, 128, 0)], 14)
                    if ent.health <= 0:
                        ent.is_dead = True
                        self.spawn_explosion(ent.x, ent.y, [ent.color, (255, 255, 255)], 15)
                        if self.boss and all(e.is_dead for e in self.boss.sub_bosses):
                            self._defeat_boss()

        # Shield crystals AoE
        for crystal in self.shield_crystals[:]:
            if b_pos.distance_to(pygame.math.Vector2(crystal.x, crystal.y)) < b.explosion_radius:
                crystal.health -= 0.75
                self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                if crystal.health <= 0:
                    if crystal in self.shield_crystals: self.shield_crystals.remove(crystal)
                    self.player.add_credits(40)
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
            for crystal in self.boss.shield_crystals[:]:
                if crystal.health > 0 and b_pos.distance_to(pygame.math.Vector2(crystal.x, crystal.y)) < b.explosion_radius:
                    crystal.health -= 0.75
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                    if crystal.health <= 0:
                        self.player.add_credits(50)
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 20)

        # Derelicts AoE
        for d in self.derelicts[:]:
            if b_pos.distance_to(pygame.math.Vector2(d.rect.center)) < b.explosion_radius:
                d.health -= 2.25 * damage_mult
                if d.health <= 0:
                    self.spawn_explosion(d.x, d.y, [(200, 100, 50), (100, 50, 20)], 20)
                    for _ in range(random.randint(5, 10)):
                        self.scraps.append(Scrap(d.x + random.randint(-20, 20), d.y + random.randint(-20, 20)))
                    if d in self.derelicts: self.derelicts.remove(d)

        # Enemy Bullets AoE (destroy them)
        for eb in self.enemy_bullets[:]:
            if b_pos.distance_to(pygame.math.Vector2(eb.x, eb.y)) < b.explosion_radius:
                if eb in self.enemy_bullets:
                    self.spawn_explosion(eb.x, eb.y, [(255, 255, 255), (100, 100, 255)], 6)
                    self.enemy_bullets.remove(eb)

    def _defeat_boss(self):
        if self.boss:
            self.boss.is_dead = True
            for ent in self.boss.sub_bosses:
                for _ in range(3):
                    self.spawn_explosion(ent.x + random.randint(-20, 20), ent.y + random.randint(-20, 20),
                                         [(255, 255, 0), (255, 128, 0), (255, 255, 255), (255, 0, 0)], 25)
        self.player.add_credits(300)
        self.player.award_xp(180)
        self.active_quest.progress = 1
        self._update_quests()

    def _update_quests(self):
        for quest in self.quests:
            if quest.completed:
                continue
            if quest.key == 'collect_cores':
                quest.progress = min(quest.target, self.materials_collected)
            elif quest.key == 'defeat_boss':
                quest.progress = 1 if (self.boss_defeated and self.current_zone == 'SINGULARITY') else 0
            elif quest.key == 'defeat_orion':
                quest.progress = 1 if (self.boss_defeated and self.current_zone == 'ORION') else 0
                
            if quest.is_complete():
                quest.completed = True
                self.player.add_credits(quest.reward_credits)
                self.player.award_xp(quest.reward_xp)
                self.spawn_explosion(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2, [(0, 255, 255), (255, 215, 0)], 20)
                
                # Advance campaign stage!
                if quest.key == 'collect_cores' and self.campaign_stage == 1:
                    self.campaign_stage = 2
                    for z in ['VULCAN', 'AQUARIS', 'NEBULA', 'PLASMA', 'VOID', 'QUANTUM', 'SINGULARITY']:
                        self.unlocked_zones[z] = True
                    self.current_hub_index = 2
                elif quest.key == 'defeat_boss' and self.campaign_stage == 2:
                    self.campaign_stage = 3
                    self.unlocked_zones['ORION'] = True
                    self.current_hub_index = 3
                
                self.active_quest = self.quests[min(len(self.quests)-1, self.campaign_stage - 1)]

    def _kill_enemy(self, enemy):
        if enemy in self.enemies:
            if self.current_zone == 'VOID' and getattr(enemy, 'name', '') == 'Abyss Sentinel':
                self.void_enemies_killed += 1
            if hasattr(enemy, 'on_death'):
                enemy.on_death(self.enemy_bullets, self.player)
            self.enemies.remove(enemy)
            self.player.add_credits(enemy.credits_value)
            self.player.award_xp(10 + enemy.credits_value // 10)
            if random.random() < 0.80:
                scrap_count = 1
                if enemy.credits_value >= 35 or enemy.health > 3:
                    scrap_count += 1
                if random.random() < 0.25:
                    scrap_count += 1
                for _ in range(scrap_count):
                    self.scraps.append(Scrap(enemy.rect.centerx, enemy.rect.centery))
            if random.random() < 0.25:
                self.loot_pickups.append(LootPickup(enemy.rect.centerx, enemy.rect.centery))

    def _destroy_meteor(self, meteor):
        if meteor not in self.meteors:
            return
        self.meteors.remove(meteor)
        
        # Add credits
        self.player.add_credits(meteor.credits_value)
        
        # Centralized explosion (spawn spatial explosion if audio enabled)
        if SOUNDS:
            SOUNDS.play_spatial('explosion', meteor.rect.centerx, meteor.rect.centery, self.player.x, self.player.y)
        
        self.spawn_explosion(meteor.rect.centerx, meteor.rect.centery, 
                             [(128, 128, 128), (100, 100, 100), (80, 80, 80)], 25)
        
        # Asteroid Fragmentation
        if meteor.size >= 45:
            num_fragments = random.randint(2, 3)
            for _ in range(num_fragments):
                frag_size = random.randint(15, 25)
                fx = meteor.x + random.uniform(-15, 15)
                fy = meteor.y + random.uniform(-15, 15)
                
                fspeed_y = meteor.speed_y + random.uniform(-1.8, 1.8)
                fspeed_x = meteor.speed_x + random.uniform(-1.8, 1.8)
                if fspeed_y == 0 and fspeed_x == 0:
                    fspeed_y = 1.0
                
                frag = Meteor(fx, fy, speed_y=fspeed_y, speed_x=fspeed_x)
                frag.size = frag_size
                frag.rect = pygame.Rect(fx, fy, frag_size, frag_size)
                frag.is_static = meteor.is_static
                
                # Regenerate polygon points for the fragment
                frag.points = []
                num_points = 6
                for i in range(num_points):
                    angle = (i / num_points) * 2 * math.pi
                    radius = random.uniform(frag_size // 3, frag_size // 2)
                    px = frag_size // 2 + radius * math.cos(angle)
                    py = frag_size // 2 + radius * math.sin(angle)
                    frag.points.append((px, py))
                
                self.meteors.append(frag)

    def _draw_cinematic_ship(self, surface, x, y, dir_x, dir_y, scale=1.0, damaged=False, thruster_intensity=1.0, rotation_angle=0):
        current_time = pygame.time.get_ticks()
        dir_f = pygame.math.Vector2(dir_x, dir_y)
        if dir_f.length() > 0:
            dir_f = dir_f.normalize()
        else:
            dir_f = pygame.math.Vector2(1, 0)
            
        if rotation_angle != 0:
            dir_f = dir_f.rotate(rotation_angle)
            
        dir_r = pygame.math.Vector2(-dir_f.y, dir_f.x)
        
        # Determine player class color
        cls = self.player.class_name if (hasattr(self, 'player') and self.player) else 'RANGER'
        base_color = CYAN
        if cls == 'ENGINEER':
            base_color = GOLD
        elif cls == 'VANGUARD':
            base_color = MAGENTA
        elif cls == 'SNIPER':
            base_color = YELLOW
        elif cls == 'ASSASSIN':
            base_color = PURPLE
            
        color = (40, 40, 45) if damaged else base_color
        wing_color = (25, 25, 28) if damaged else SLATE_GRAY
        glass_color = (15, 15, 18) if damaged else WHITE
        
        center = pygame.math.Vector2(x, y)
        w = 40 * scale
        h = 40 * scale
        
        # 1. THRUSTER FLAMES
        if thruster_intensity > 0 and not damaged:
            flame_len = (15 + random.randint(0, 10)) * scale * thruster_intensity
            rear_center = center - dir_f * (h // 2)
            flame_tip = rear_center - dir_f * flame_len
            flame_l = rear_center - dir_r * (8 * scale)
            flame_r = rear_center + dir_r * (8 * scale)
            flame_col = CYAN if cls == 'RANGER' else ORANGE
            pygame.draw.polygon(surface, flame_col, [rear_center, flame_l, flame_tip, flame_r], width=1)
            pygame.draw.line(surface, WHITE if cls == 'RANGER' else YELLOW, rear_center, rear_center - dir_f * (flame_len * 0.65), max(1, int(scale)))
            
        # 2. WINGS
        lw_tip = center - dir_f * (5 * scale) - dir_r * (w // 2)
        lw_base_in = center - dir_f * (h // 2) - dir_r * (5 * scale)
        lw_base_out = center - dir_f * (h // 3) - dir_r * (w // 2)
        pygame.draw.polygon(surface, wing_color, [center, lw_tip, lw_base_out, lw_base_in])
        
        rw_tip = center - dir_f * (5 * scale) + dir_r * (w // 2)
        rw_base_in = center - dir_f * (h // 2) + dir_r * (5 * scale)
        rw_base_out = center - dir_f * (h // 3) + dir_r * (w // 2)
        pygame.draw.polygon(surface, wing_color, [center, rw_tip, rw_base_out, rw_base_in])
        
        # 3. WING CANNONS
        weapon_level = self.player.skills['weapon'] if (hasattr(self, 'player') and self.player) else 0
        if weapon_level >= 1 and not damaged:
            pygame.draw.line(surface, color, lw_tip, lw_tip + dir_f * (12 * scale), width=max(1, int(3*scale)))
            pygame.draw.line(surface, color, rw_tip, rw_tip + dir_f * (12 * scale), width=max(1, int(3*scale)))
            
        # 4. MAIN HULL (Triangle shape)
        hull_tip = center + dir_f * (h // 2)
        hull_left = center - dir_f * (h // 4) - dir_r * (8 * scale)
        hull_right = center - dir_f * (h // 4) + dir_r * (8 * scale)
        pygame.draw.polygon(surface, color, [hull_tip, hull_left, hull_right])
        
        # 5. COCKPIT GLASS
        glass_tip = center + dir_f * (h // 3)
        glass_left = center + dir_f * (h // 8) - dir_r * (4 * scale)
        glass_right = center + dir_f * (h // 8) + dir_r * (4 * scale)
        pygame.draw.polygon(surface, glass_color, [glass_tip, glass_left, glass_right])
        
        # 6. SHIELD FORCEFIELD (light pulsing during cinematic if not damaged)
        if not damaged and hasattr(self, 'player') and self.player and self.player.shields > 0 and thruster_intensity > 0.5:
            glow_surf = pygame.Surface((int(w * 2), int(h * 2)), pygame.SRCALPHA)
            glow_intensity = 30 + int(15 * math.sin(current_time * 0.01))
            pygame.draw.circle(glow_surf, (0, 255, 255, glow_intensity), (int(w), int(h)), int(w * 0.9), width=2)
            surface.blit(glow_surf, (int(x - w), int(y - h)))

    def _draw_targeting_reticle(self, screen, target_x, target_y):
        ticks = pygame.time.get_ticks()
        draw_x = target_x - self.camera_x
        draw_y = target_y - self.camera_y
        
        size = 60 + int(10 * math.sin(ticks * 0.02))
        angle = ticks * 0.005
        
        # Rotating brackets
        for i in range(4):
            ang = angle + i * (math.pi / 2)
            p1 = (draw_x + math.cos(ang) * size, draw_y + math.sin(ang) * size)
            p2 = (draw_x + math.cos(ang + 0.3) * size, draw_y + math.sin(ang + 0.3) * size)
            pygame.draw.line(screen, RED, p1, p2, width=3)
            
            # Inner small lines
            isize = size - 15
            pygame.draw.line(screen, RED, (draw_x + math.cos(ang)*isize, draw_y + math.sin(ang)*isize), 
                                          (draw_x + math.cos(ang)*(isize-10), draw_y + math.sin(ang)*(isize-10)), 1)
        
        # Lock-on text
        if ticks % 500 < 250:
            font = pygame.font.SysFont("Arial", 12, bold=True)
            txt = font.render("THREAT TRACKING", True, RED)
            screen.blit(txt, (draw_x - txt.get_width()//2, draw_y + size + 10))

    def draw_intro_overlay(self, surf, intro_time, ticks):
        surf.fill((3, 3, 6))
        # Draw cyber background grid
        grid_spacing = 50
        grid_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        for gx_line in range(0, VIRTUAL_WIDTH, grid_spacing):
            pygame.draw.line(grid_surf, (0, 255, 255, 6), (gx_line, 0), (gx_line, VIRTUAL_HEIGHT))
        for gy_line in range(0, VIRTUAL_HEIGHT, grid_spacing):
            pygame.draw.line(grid_surf, (0, 255, 255, 6), (0, gy_line), (VIRTUAL_WIDTH, gy_line))
        surf.blit(grid_surf, (0, 0))
        
        boot_lines = [
            ">> BOOTING ZENITH SYSTEMS KERNEL v9.42...",
            ">> MOUNTING CRYPTO-DRIVE SYSTEM... [ OK ]",
            ">> SYSTEM CALIBRATION: ACTIVE",
            "   THRUST CONTROL INTERFACE.... [ READY ]",
            "   DEFLECTOR SHIELD MATRIX..... [ ONLINE ]",
            "   WEAPON COOLDOWN SYSTEMS..... [ CALIBRATED ]",
            "   HYPERDRIVE NAVIGATION....... [ READY ]",
            ">> CONNECTING TO NEURAL PILOT DATASTREAM...",
            ">> STATUS: ZENITH CORE SECURE. BOOT COMPLETE."
        ]
        
        char_speed = 0.08
        y_offset = 120
        
        for i, line in enumerate(boot_lines):
            line_start_time = i * 450
            if intro_time > line_start_time:
                chars_to_show = int((intro_time - line_start_time) * char_speed)
                visible_text = line[:chars_to_show]
                color = CYAN
                if "[ OK ]" in visible_text or "[ ONLINE ]" in visible_text or "[ READY ]" in visible_text or "[ CALIBRATED ]" in visible_text:
                    color = GREEN
                text_surf = self.small_font.render(visible_text, True, color)
                surf.blit(text_surf, (60, y_offset + i * 32))
        
        if intro_time >= 2800:
            reveal_time = intro_time - 2800
            alpha = min(255, int((reveal_time / 1800.0) * 255))
            
            cx, cy = VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2
            shift_x = int(4 * math.sin(ticks * 0.08))
            shift_y = int(3 * math.cos(ticks * 0.06))
            
            title_red = self.large_font.render("ZENITH", True, (255, 40, 40))
            title_cyan = self.large_font.render("ZENITH", True, (40, 255, 255))
            title_main = self.large_font.render("ZENITH", True, WHITE)
            
            title_red.set_alpha(alpha)
            title_cyan.set_alpha(alpha)
            title_main.set_alpha(alpha)
            
            glow = pygame.Surface((title_main.get_width() + 160, title_main.get_height() + 160), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 255, 255, int((alpha // 5) * (0.6 + 0.4 * math.sin(ticks * 0.015)))), (glow.get_width()//2, glow.get_height()//2), 120)
            surf.blit(glow, (cx - glow.get_width()//2, cy - glow.get_height()//2 - 60))
            
            surf.blit(title_red, (cx - title_red.get_width()//2 - shift_x, cy - title_red.get_height()//2 - 60 - shift_y), special_flags=pygame.BLEND_ADD)
            surf.blit(title_cyan, (cx - title_cyan.get_width()//2 + shift_x, cy - title_cyan.get_height()//2 - 60 + shift_y), special_flags=pygame.BLEND_ADD)
            surf.blit(title_main, (cx - title_main.get_width()//2, cy - title_main.get_height()//2 - 60))
            
            if reveal_time > 800:
                bar_w = 460
                bar_h = 6
                bar_x = cx - bar_w // 2
                bar_y = cy + 60
                progress = min(1.0, (reveal_time - 800) / 1200.0)
                pygame.draw.rect(surf, (40, 40, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
                pygame.draw.rect(surf, CYAN, (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=3)
                
                if progress >= 1.0:
                    ready_text = self.small_font.render("PILOT INTERFACE: INITIALIZED // PRESS ANY KEY TO DEPLOY", True, GREEN)
                    ready_text.set_alpha(int(140 + 115 * math.sin(pygame.time.get_ticks() * 0.008)))
                    surf.blit(ready_text, (cx - ready_text.get_width()//2, bar_y + 35))
                    
        for gy in range(0, VIRTUAL_HEIGHT, 4):
            pygame.draw.line(surf, (0, 0, 0, 30), (0, gy), (VIRTUAL_WIDTH, gy), 1)
            
        if random.random() < 0.015:
            flicker_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            flicker_surf.fill((0, 255, 255, random.randint(8, 25)))
            surf.blit(flicker_surf, (0, 0))

    def draw_main_menu_overlay(self, surf, ticks, draw_state=None):
        current_state = draw_state if draw_state is not None else self.state
        for star in self.stars:
            val = math.sin(pygame.time.get_ticks() * star[5] + star[6])
            alpha = int(128 + 127 * val)
            color = tuple(max(0, min(255, int(c * (alpha / 255.0)))) for c in star[4])
            pygame.draw.circle(surf, color, (int(star[0]), int(star[1])), star[3])

        nebula_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        clouds = [
            (PURPLE, 300, 300, 0.0002),
            (INDIGO, 900, 600, -0.00015),
            (MAGENTA, 200, 700, 0.0003),
            (BLUE, 1000, 200, -0.00025)
        ]
        for col, bx, by, speed in clouds:
            nx = bx + math.sin(ticks * speed) * 80
            ny = by + math.cos(ticks * speed * 0.7) * 80
            base_r = 220 + math.sin(ticks * 0.0004) * 30
            for layer in range(5):
                alpha = int(22 / (layer + 1))
                lr = int(base_r * (1.0 + layer * 0.3))
                pygame.draw.circle(nebula_surf, (*col, alpha), (int(nx), int(ny)), lr)
        surf.blit(nebula_surf, (0, 0))

        grid_spacing = 40
        grid_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        for gx_line in range(0, VIRTUAL_WIDTH, grid_spacing):
            pygame.draw.line(grid_surf, (0, 255, 255, 15), (gx_line, 0), (gx_line, VIRTUAL_HEIGHT))
        for gy_line in range(0, VIRTUAL_HEIGHT, grid_spacing):
            pygame.draw.line(grid_surf, (0, 255, 255, 15), (0, gy_line), (VIRTUAL_WIDTH, gy_line))
        scan_y = (pygame.time.get_ticks() // 4) % VIRTUAL_HEIGHT
        pygame.draw.line(grid_surf, (0, 255, 255, 35), (0, scan_y), (VIRTUAL_WIDTH, scan_y), width=2)
        surf.blit(grid_surf, (0, 0))
        
        border_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (0, 255, 255, 40), (10, 10, VIRTUAL_WIDTH - 20, VIRTUAL_HEIGHT - 20), width=1, border_radius=12)
        
        br_len = 30
        pygame.draw.rect(border_surf, CYAN, (10, 10, br_len, 4))
        pygame.draw.rect(border_surf, CYAN, (10, 10, 4, br_len))
        pygame.draw.rect(border_surf, CYAN, (VIRTUAL_WIDTH - 10 - br_len, 10, br_len, 4))
        pygame.draw.rect(border_surf, CYAN, (VIRTUAL_WIDTH - 14, 10, 4, br_len))
        pygame.draw.rect(border_surf, CYAN, (10, VIRTUAL_HEIGHT - 14, br_len, 4))
        pygame.draw.rect(border_surf, CYAN, (10, VIRTUAL_HEIGHT - 10 - br_len, 4, br_len))
        pygame.draw.rect(border_surf, CYAN, (VIRTUAL_WIDTH - 10 - br_len, VIRTUAL_HEIGHT - 14, br_len, 4))
        pygame.draw.rect(border_surf, CYAN, (VIRTUAL_WIDTH - 14, VIRTUAL_HEIGHT - 10 - br_len, 4, br_len))
        surf.blit(border_surf, (0, 0))

        mx, my = pygame.mouse.get_pos()
        vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
        vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)

        if current_state == 'MAIN_MENU':
            pulse = math.sin(pygame.time.get_ticks() * 0.005)
            cx, cy = VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 200
            
            shift_x = int(3 * math.sin(ticks * 0.06))
            shift_y = int(2 * math.cos(ticks * 0.04))
            
            title_red = self.large_font.render("ZENITH", True, (255, 50, 50))
            title_cyan = self.large_font.render("ZENITH", True, (50, 255, 255))
            title_main = self.large_font.render("ZENITH", True, (int(200 + 55 * pulse), 255, 255))
            
            surf.blit(title_red, (cx - title_red.get_width()//2 - shift_x, cy - title_red.get_height()//2 - shift_y), special_flags=pygame.BLEND_ADD)
            surf.blit(title_cyan, (cx - title_cyan.get_width()//2 + shift_x, cy - title_cyan.get_height()//2 + shift_y), special_flags=pygame.BLEND_ADD)
            surf.blit(title_main, (cx - title_main.get_width()//2, cy - title_main.get_height()//2))
            
            input_prompt = self.font.render("ENTER PILOT CALLSIGN:", True, WHITE)
            input_box_rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 200, 350, 400, 50)
            pygame.draw.rect(surf, DARK_GRAY, input_box_rect, border_radius=5)
            
            border_color = CYAN if self.input_active else SLATE_GRAY
            if self.input_active and pygame.time.get_ticks() % 1000 < 500:
                border_color = WHITE
            pygame.draw.rect(surf, border_color, input_box_rect, width=2, border_radius=5)
            
            surf.blit(input_prompt, (VIRTUAL_WIDTH // 2 - input_prompt.get_width() // 2, 300))
            
            name_text = self.player_name + ("|" if self.input_active and pygame.time.get_ticks() % 1000 < 500 else "")
            name_surf = self.font.render(name_text, True, YELLOW)
            name_rect = name_surf.get_rect(center=input_box_rect.center)
            surf.blit(name_surf, name_rect)
            
            has_save = SaveManager.save_exists()
            is_valid = self.player_name.strip() != ""
            
            if has_save:
                new_game_btn = pygame.Rect(VIRTUAL_WIDTH // 2 - 210, 430, 200, 50)
                continue_btn = pygame.Rect(VIRTUAL_WIDTH // 2 + 10, 430, 200, 50)
            else:
                new_game_btn = pygame.Rect(VIRTUAL_WIDTH // 2 - 100, 430, 200, 50)
                continue_btn = None
                
            # Draw New Game Button
            if is_valid:
                new_btn_color = CYAN if new_game_btn.collidepoint(vmx, vmy) else BLUE
                new_border_color = WHITE
                new_text_color = BLACK if new_btn_color == CYAN else WHITE
                new_btn_text = "NEW GAME"
            else:
                new_btn_color = (40, 40, 40)
                new_border_color = SLATE_GRAY
                new_text_color = GRAY
                new_btn_text = "ENTER NAME"
                
            pygame.draw.rect(surf, new_btn_color, new_game_btn, border_radius=8)
            pygame.draw.rect(surf, new_border_color, new_game_btn, width=1, border_radius=8)
            new_btn_lbl = self.font.render(new_btn_text, True, new_text_color)
            surf.blit(new_btn_lbl, (new_game_btn.centerx - new_btn_lbl.get_width() // 2, new_game_btn.centery - new_btn_lbl.get_height() // 2))
            
            # Draw Continue Button if save exists
            if continue_btn:
                cont_btn_color = CYAN if continue_btn.collidepoint(vmx, vmy) else GREEN
                cont_border_color = WHITE
                cont_text_color = BLACK if cont_btn_color == CYAN else WHITE
                
                pygame.draw.rect(surf, cont_btn_color, continue_btn, border_radius=8)
                pygame.draw.rect(surf, cont_border_color, continue_btn, width=1, border_radius=8)
                cont_btn_lbl = self.font.render("CONTINUE", True, cont_text_color)
                surf.blit(cont_btn_lbl, (continue_btn.centerx - cont_btn_lbl.get_width() // 2, continue_btn.centery - cont_btn_lbl.get_height() // 2))
                
            # Draw Feedback Message
            if getattr(self, 'save_feedback_msg', '') != "" and pygame.time.get_ticks() - getattr(self, 'save_feedback_time', 0) < 3000:
                fb_color = GREEN if "success" in self.save_feedback_msg.lower() or "loaded" in self.save_feedback_msg.lower() or "saved" in self.save_feedback_msg.lower() else RED
                fb_lbl = self.font.render(self.save_feedback_msg, True, fb_color)
                surf.blit(fb_lbl, (VIRTUAL_WIDTH // 2 - fb_lbl.get_width() // 2, 490))

            controls_box = pygame.Rect(VIRTUAL_WIDTH // 2 - 260, 500, 520, 360)
            box_surf = pygame.Surface((controls_box.width, controls_box.height), pygame.SRCALPHA)
            box_surf.fill((5, 5, 8, 120))
            pygame.draw.rect(box_surf, (0, 255, 255, 120), (0, 0, controls_box.width, controls_box.height), width=1)
            surf.blit(box_surf, (controls_box.x, controls_box.y))
            
            controls_title = self.font.render("CONTROLS & HOW TO PLAY:", True, CYAN)
            surf.blit(controls_title, (controls_box.x + 20, controls_box.y + 15))
            
            controls = [
                "W/S (or UP/DOWN)   : Thrust Forward / Reverse",
                "A/D (or L/R keys)  : Evade Dash (on Cooldown)",
                "LEFT SHIFT         : Drop Anti-Missile Flare",
                "MOUSE MOVEMENT     : Aim / Rotate Ship",
                "LEFT MOUSE CLICK   : Shoot Primary Weapon",
                "RIGHT MOUSE CLICK  : Heavy Torpedo (In Combat)",
                "GOAL: Fly UP, Collect 5 Cores & Warp Out",
                "P / ESCAPE KEY     : Open Upgrades at Space Station",
                "Q / E              : Use Class Abilities"
            ]
            for idx, text in enumerate(controls):
                ctrl_txt = self.small_font.render(text, True, (220, 240, 255))
                surf.blit(ctrl_txt, (controls_box.x + 20, controls_box.y + 50 + idx * 30))

        elif current_state == 'CLASS_SELECT':
            sel_lbl = self.large_font.render("SELECT SHIP CLASS", True, CYAN)
            surf.blit(sel_lbl, (VIRTUAL_WIDTH // 2 - sel_lbl.get_width() // 2, 70))
            
            pilot_lbl = self.font.render(f"PILOT CALLSIGN: {self.player_name.upper()}", True, YELLOW)
            surf.blit(pilot_lbl, (VIRTUAL_WIDTH // 2 - pilot_lbl.get_width() // 2, 150))
            
            classes = ['RANGER', 'ENGINEER', 'VANGUARD', 'SNIPER', 'ASSASSIN']
            for idx, cls in enumerate(classes):
                btn_rect = pygame.Rect(100 + idx * 200, 220, 180, 50)
                is_hover = btn_rect.collidepoint(vmx, vmy)
                is_active = self.selected_class == cls
                
                bg_col = (40, 40, 45)
                if is_active:
                    bg_col = CYAN
                elif is_hover:
                    bg_col = (80, 80, 85)
                    
                pygame.draw.rect(surf, bg_col, btn_rect, border_radius=6)
                pygame.draw.rect(surf, WHITE if is_active else SLATE_GRAY, btn_rect, width=1, border_radius=6)
                
                lbl_col = BLACK if is_active else WHITE
                lbl = self.font.render(cls, True, lbl_col)
                surf.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2, btn_rect.centery - lbl.get_height() // 2))

            prev_box = pygame.Rect(100, 310, 400, 400)
            pygame.draw.rect(surf, (10, 10, 15, 180), prev_box, border_radius=8)
            pygame.draw.rect(surf, CYAN, prev_box, width=1, border_radius=8)
            prev_title = self.font.render("VESSEL HULL PREVIEW", True, CYAN)
            surf.blit(prev_title, (prev_box.centerx - prev_title.get_width() // 2, prev_box.y + 15))
            
            self.player.x = prev_box.centerx - self.player.width // 2
            self.player.y = prev_box.centery - self.player.height // 2 - 20
            self.player.angle = (pygame.time.get_ticks() // 25) % 360
            
            self.player.draw(surf, camera_y=0)

            desc_box = pygame.Rect(520, 310, 580, 400)
            pygame.draw.rect(surf, (10, 10, 15, 180), desc_box, border_radius=8)
            pygame.draw.rect(surf, CYAN, desc_box, width=1, border_radius=8)
            
            desc_title = self.font.render(f"CLASS SPECIFICATION: {self.selected_class}", True, YELLOW)
            surf.blit(desc_title, (desc_box.x + 20, desc_box.y + 15))
            
            class_desc = {
                'RANGER': "Patrol and intercept class. Balanced stats and versatile loadout. Employs special maneuver thrusters that reduce evade dash cooldown.",
                'ENGINEER': "Tactical support vessel. Slow shield automatic regeneration capability. Deploys custom auxiliary repair drones and defense nodes.",
                'VANGUARD': "Heavy armor cruiser. Maximum plating integrity and deflection shields. Built for ramming attacks and bullet absorption.",
                'SNIPER': "Long-range bombardment asset. Possesses high-energy piercing weapons. Fires high-damage precision railgun bolts.",
                'ASSASSIN': "Infiltration model. Deploys a cloaking drive that makes the ship temporarily invisible and invulnerable, ideal for sneak attacks."
            }
            
            desc_text = class_desc.get(self.selected_class, "")
            words = desc_text.split(' ')
            lines = []
            curr_line = ""
            for w in words:
                test_line = curr_line + " " + w if curr_line else w
                if self.font.size(test_line)[0] < desc_box.width - 40:
                    curr_line = test_line
                else:
                    lines.append(curr_line)
                    curr_line = w
            if curr_line:
                lines.append(curr_line)
                
            for idx, line in enumerate(lines):
                line_surf = self.font.render(line, True, (220, 230, 245))
                surf.blit(line_surf, (desc_box.x + 20, desc_box.y + 55 + idx * 26))

            stats_y = desc_box.y + 190
            stats_lbl = self.font.render("VESSEL STATISTICS:", True, CYAN)
            surf.blit(stats_lbl, (desc_box.x + 20, stats_y))
            
            class_stats = {
                'RANGER':    {'shields': 4, 'speed': 8.5, 'dmg': 7, 'special': "Fast Dash CD"},
                'ENGINEER':  {'shields': 5, 'speed': 6.5, 'dmg': 5, 'special': "Repair Drones"},
                'VANGUARD':  {'shields': 6, 'speed': 5.5, 'dmg': 6, 'special': "Heavy Plating"},
                'SNIPER':    {'shields': 3, 'speed': 7.5, 'dmg': 10, 'special': "Railgun Snipe"},
                'ASSASSIN':  {'shields': 3, 'speed': 9.0, 'dmg': 8, 'special': "Cloaking Drive"}
            }
            
            stats = class_stats.get(self.selected_class, {'shields': 4, 'speed': 8.0, 'dmg': 6, 'special': "None"})
            
            sh_txt = self.small_font.render(f"Shield Matrix Capacity: {stats['shields']}/6", True, WHITE)
            surf.blit(sh_txt, (desc_box.x + 20, stats_y + 25))
            pygame.draw.rect(surf, (40, 40, 45), (desc_box.x + 20, stats_y + 43, 350, 8), border_radius=3)
            pygame.draw.rect(surf, CYAN, (desc_box.x + 20, stats_y + 43, int(350 * (stats['shields'] / 6.0)), 8), border_radius=3)
            
            sp_txt = self.small_font.render(f"Max Engine Impulse: {stats['speed']}/10.0", True, WHITE)
            surf.blit(sp_txt, (desc_box.x + 20, stats_y + 60))
            pygame.draw.rect(surf, (40, 40, 45), (desc_box.x + 20, stats_y + 78, 350, 8), border_radius=3)
            pygame.draw.rect(surf, GOLD, (desc_box.x + 20, stats_y + 78, int(350 * (stats['speed'] / 10.0)), 8), border_radius=3)
            
            dmg_txt = self.small_font.render(f"Weapon Damage Caliber: {stats['dmg']}/10", True, WHITE)
            surf.blit(dmg_txt, (desc_box.x + 20, stats_y + 95))
            pygame.draw.rect(surf, (40, 40, 45), (desc_box.x + 20, stats_y + 113, 350, 8), border_radius=3)
            pygame.draw.rect(surf, RED, (desc_box.x + 20, stats_y + 113, int(350 * (stats['dmg'] / 10.0)), 8), border_radius=3)
            
            spec_txt = self.font.render(f"SYSTEM OVERDRIVE: {stats['special'].upper()}", True, GREEN)
            surf.blit(spec_txt, (desc_box.x + 20, stats_y + 135))

            launch_btn = pygame.Rect(VIRTUAL_WIDTH // 2 - 150, 740, 300, 60)
            pulse_amt = math.sin(pygame.time.get_ticks() * 0.01)
            launch_color = (0, 200 + int(55 * pulse_amt), 200 + int(55 * pulse_amt))
            if launch_btn.collidepoint(vmx, vmy):
                launch_color = GREEN
            pygame.draw.rect(surf, launch_color, launch_btn, border_radius=8)
            pygame.draw.rect(surf, WHITE, launch_btn, width=1, border_radius=8)
            
            launch_lbl = self.font.render("LAUNCH MISSION", True, BLACK if launch_color == GREEN else WHITE)
            surf.blit(launch_lbl, (launch_btn.centerx - launch_lbl.get_width() // 2, launch_btn.centery - launch_lbl.get_height() // 2))

    def _draw(self):
        self.virtual_screen.fill(BLACK)
        self.ui_surface.fill((0, 0, 0, 0))
        
        ticks = pygame.time.get_ticks()
        current_time = ticks
        
        # 1. TACTICAL OVERLAYS & BACKGROUNDS
        has_major_threat = False
        if self.boss and not self.boss.is_dead:
            has_major_threat = True
        else:
            for e in self.enemies:
                if getattr(e, 'subtype', '') == 'ELITE':
                    has_major_threat = True
                    break
        
        if self.state == 'PLAYING' and has_major_threat and not self.player.is_dead:
            self._draw_targeting_reticle(self.virtual_screen, self.player.x + self.player.width//2, self.player.y + self.player.height//2)

        # Restored Background rendering for Combat Zones (Stars & Planets)
        if self.state in ('PLAYING', 'PAUSED', 'GAME_OVER') and self.current_zone != 'HUB':
            for star in self.stars:
                star_speed = star[2]
                star_draw_y = (star[1] - self.camera_y * star_speed * 0.40) % VIRTUAL_HEIGHT
                star_draw_x = (star[0] - self.camera_x * star_speed * 0.15) % VIRTUAL_WIDTH
                
                val = math.sin(ticks * star[5] + star[6])
                alpha = int(128 + 127 * val)
                color = tuple(max(0, min(255, int(c * (alpha / 255.0)))) for c in star[4])
                pygame.draw.circle(self.virtual_screen, color, (int(star_draw_x), int(star_draw_y)), star[3])

            # Update and draw shooting stars (meteor streaks)
            if not hasattr(self, 'shooting_stars'):
                self.shooting_stars = []
            if random.random() < 0.008:
                sx = random.randint(100, VIRTUAL_WIDTH)
                sy = random.randint(-50, VIRTUAL_HEIGHT // 2)
                speed = random.uniform(8.0, 15.0)
                angle = random.uniform(130, 150)
                length = random.randint(40, 80)
                life = random.randint(15, 30)
                self.shooting_stars.append({'x': sx, 'y': sy, 'speed': speed, 'angle': angle, 'length': length, 'life': life, 'max_life': life})
            for ss in self.shooting_stars[:]:
                rad = math.radians(ss['angle'])
                ss['x'] += ss['speed'] * math.cos(rad)
                ss['y'] += ss['speed'] * math.sin(rad)
                ss['life'] -= 1
                if ss['life'] <= 0:
                    self.shooting_stars.remove(ss)
                else:
                    salpha = int(255 * (ss['life'] / ss['max_life']))
                    trail_x = ss['x'] - ss['length'] * math.cos(rad)
                    trail_y = ss['y'] - ss['length'] * math.sin(rad)
                    trail_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.line(trail_surf, (200, 240, 255, salpha), (int(ss['x']), int(ss['y'])), (int(trail_x), int(trail_y)), 2)
                    self.virtual_screen.blit(trail_surf, (0, 0))

            zone_color = BIOME_CONFIGS.get(self.current_zone, {'theme_color': GRAY})['theme_color']
            self._draw_background_nebula(self.virtual_screen, self.camera_y, self.camera_x, zone_color)
            self._draw_cyber_grid(self.virtual_screen, self.camera_y, self.camera_x, zone_color)
            
            # Render massive planet (raised center and dynamic size)
            planet_radius = getattr(self, 'planet_radius', 800)
            planet_y = (planet_radius + 80) - self.camera_y * 0.02
            planet_x = VIRTUAL_WIDTH // 2
            
            pygame.draw.circle(self.virtual_screen, (zone_color[0] // 4, zone_color[1] // 4, zone_color[2] // 4), (int(planet_x), int(planet_y)), planet_radius + 35, width=1)
            pygame.draw.circle(self.virtual_screen, zone_color, (int(planet_x), int(planet_y)), planet_radius, width=2)
            
            planet_tex = getattr(self, 'planet_texture', None)
            if planet_tex is not None:
                dim = planet_radius * 2
                temp_planet = pygame.Surface((dim, dim), pygame.SRCALPHA)
                
                map_width = 5200
                orbit_offset = int((self.camera_x * (dim / map_width)) % dim)
                temp_planet.blit(planet_tex, (-orbit_offset, 0))
                temp_planet.blit(planet_tex, (dim - orbit_offset, 0))
                
                planet_cld = getattr(self, 'planet_clouds', None)
                if planet_cld is not None:
                    cloud_offset = int(((self.camera_x * (dim / map_width)) + (ticks * 0.04)) % dim)
                    temp_planet.blit(planet_cld, (-cloud_offset, 0))
                    temp_planet.blit(planet_cld, (dim - cloud_offset, 0))
                planet_msk = getattr(self, 'planet_mask', None)
                if planet_msk is not None:
                    temp_planet.blit(planet_msk, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.virtual_screen.blit(temp_planet, (int(planet_x - planet_radius), int(planet_y - planet_radius)))

            # Render imposing background structure
            if hasattr(self, 'bg_structure'):
                self.bg_structure.draw(self.virtual_screen, self.camera_y, self.camera_x)

        # Calculate screen shake for game world entities (keeps HUD static)
        swx, swy = 0, 0
        if self.screen_shake > 0:
            shake_amt = min(self.screen_shake, 5)
            swx = random.randint(-shake_amt, shake_amt)
            swy = random.randint(-shake_amt, shake_amt)
            self.screen_shake = max(0, self.screen_shake - 1)

        if self.state == 'HUB' or (self.state == 'PAUSED' and self.current_zone == 'HUB'):
            for star in self.stars:
                val = math.sin(ticks * star[5] + star[6])
                alpha = int(128 + 127 * val)
                color = tuple(max(0, min(255, int(c * (alpha / 255.0)))) for c in star[4])
                pygame.draw.circle(self.virtual_screen, color, (int(star[0] + swx), int(star[1] + swy)), star[3])
            
            self._draw_background_nebula(self.virtual_screen, ticks * 0.05, ticks * 0.05, BLUE)
            self._draw_cyber_grid(self.virtual_screen, ticks * 0.05, ticks * 0.05, CYAN)
            
            # Draw Stations (Rotating cyber-octagons)
            stations = [
                ((300 + swx, 450 + swy), "ENGINEERING", CYAN, (0, 100, 150)),
                ((600 + swx, 450 + swy), "WEAPONRY", ORANGE, (150, 50, 0)),
                ((900 + swx, 450 + swy), "SUPPLY DEPOT", GREEN, (0, 120, 0))
            ]
            
            for center, name, color, ring_color in stations:
                ring_pulse = int(5 * math.sin(ticks * 0.003))
                num_sides = 8
                outer_r = 110 + ring_pulse
                points = []
                for side in range(num_sides):
                    ang = math.radians(side * (360 / num_sides) + ticks * 0.015)
                    sx = center[0] + int(outer_r * math.cos(ang))
                    sy = center[1] + int(outer_r * math.sin(ang))
                    points.append((sx, sy))
                pygame.draw.polygon(self.virtual_screen, color, points, width=1)
                
                points_in = []
                inner_r = 80 - ring_pulse
                for side in range(num_sides):
                    ang = math.radians(side * (360 / num_sides) - ticks * 0.02)
                    sx = center[0] + int(inner_r * math.cos(ang))
                    sy = center[1] + int(inner_r * math.sin(ang))
                    points_in.append((sx, sy))
                pygame.draw.polygon(self.virtual_screen, ring_color, points_in, width=1)
                
                lbl = self.font.render(name, True, color)
                self.virtual_screen.blit(lbl, (center[0] - lbl.get_width() // 2, center[1] - 15))
            
            # Dynamic Portals
            glow = int(5 * math.sin(ticks * 0.005))
            for zone, cfg in BIOME_CONFIGS.items():
                if cfg['hub'] == self.current_hub_index and self.unlocked_zones.get(zone, False):
                    theme_color = cfg['theme_color']
                    dark_color = (theme_color[0] // 3, theme_color[1] // 3, theme_color[2] // 3)
                    
                    order = cfg['order']
                    if order == 0:
                        center = (150 + swx, 750 + swy)
                        lbl_y = 650 + swy
                        info_y = 620 + swy
                    elif order == 1:
                        center = (1050 + swx, 180 + swy)
                        lbl_y = 260 + swy
                        info_y = 290 + swy
                    elif order == 3:
                        center = (1050 + swx, 750 + swy)
                        lbl_y = 650 + swy
                        info_y = 620 + swy
                    else:
                        center = (150 + swx, 180 + swy)
                        lbl_y = 260 + swy
                        info_y = 290 + swy
                        
                    pygame.draw.circle(self.virtual_screen, theme_color, center, 60 + glow, width=3)
                    pygame.draw.circle(self.virtual_screen, dark_color, center, 50)
                    pygame.draw.circle(self.virtual_screen, WHITE, center, 15 + glow // 2)
                    
                    for orbital in range(3):
                        o_ang = ticks * 0.004 + orbital * (2 * math.pi / 3)
                        ox = center[0] + int((55 + glow) * math.cos(o_ang))
                        oy = center[1] + int((55 + glow) * math.sin(o_ang))
                        pygame.draw.circle(self.virtual_screen, theme_color, (ox, oy), 5)
                    
                    lbl_text = f"{cfg['name'].upper()} PORTAL"
                    lbl = self.font.render(lbl_text, True, theme_color)
                    self.virtual_screen.blit(lbl, (center[0] - lbl.get_width() // 2, lbl_y))
            
            welcome_text = f"SAFE HAVEN HUB STATION - SEGMENT {self.current_hub_index}"
            welcome = self.large_font.render(welcome_text, True, WHITE)
            self.virtual_screen.blit(welcome, (VIRTUAL_WIDTH // 2 - welcome.get_width() // 2, 30))
            
            # Draw Cheat Portals for developer testing (if dev mode enabled)
            if getattr(self, 'dev_mode', False):
                cheat_lbl = self.font.render("DEV CHEAT PORTALS (INSTANT WARP):", True, RED)
                self.virtual_screen.blit(cheat_lbl, (VIRTUAL_WIDTH // 2 - cheat_lbl.get_width() // 2, 85))
                
                cheat_zones = ['ASTEROIDS', 'VULCAN', 'AQUARIS', 'NEBULA', 'PLASMA', 'VOID', 'QUANTUM', 'SINGULARITY', 'ORION']
                for i, zone in enumerate(cheat_zones):
                    cx = 100 + i * 125
                    cy = 130
                    cfg = BIOME_CONFIGS[zone]
                    color = cfg['theme_color']
                    pygame.draw.circle(self.virtual_screen, color, (cx, cy), 18, width=1)
                    pygame.draw.circle(self.virtual_screen, (40, 40, 40), (cx, cy), 14)
                    lbl = self.font.render(str(i + 1), True, color)
                    self.virtual_screen.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))
                    name_lbl = pygame.font.SysFont("Arial", 10).render(zone[:4], True, GRAY)
                    self.virtual_screen.blit(name_lbl, (cx - name_lbl.get_width() // 2, cy + 20))
            
            self.player.draw(self.virtual_screen, camera_y=0)
            
            # Draw stay timer charging progress in the Hub
            if self.wormhole_charge_timer > 0 and getattr(self, 'active_hub_portal', None) is not None:
                portal_center = (600, 450)
                cfg = BIOME_CONFIGS.get(self.active_hub_portal) if self.active_hub_portal else None
                if cfg:
                    order = cfg['order']
                    if order == 0:
                        portal_center = (150, 750)
                    elif order == 1:
                        portal_center = (1050, 180)
                    elif order == 3:
                        portal_center = (1050, 750)
                    else:
                        portal_center = (150, 180)
                    
                target_charge = 1000.0 if self.player.skills.get('hyperdrive', 0) > 0 else 3000.0
                pct = min(1.0, self.wormhole_charge_timer / target_charge)
                bar_w = 200
                bar_h = 12
                bar_x = portal_center[0] - bar_w // 2
                bar_y = portal_center[1] + 70
                
                # Background
                pygame.draw.rect(self.virtual_screen, (44, 44, 44), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                # Progress bar
                pygame.draw.rect(self.virtual_screen, GREEN, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)
                # Border
                pygame.draw.rect(self.virtual_screen, WHITE, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)
                
                # Text countdown
                secs_left = max(0.0, (target_charge - self.wormhole_charge_timer) / 1000.0)
                charge_lbl = self.font.render(f"WARPING IN {secs_left:.1f}s...", True, GREEN)
                self.virtual_screen.blit(charge_lbl, (portal_center[0] - charge_lbl.get_width() // 2, bar_y + 18))
            
            if self.hub_station_active and self.hub_station_active in NPC_INFO:
                npc = NPC_INFO[self.hub_station_active]
                # Main Dialogue Box
                box_w = 800
                box_h = 130
                box_x = VIRTUAL_WIDTH // 2 - box_w // 2
                box_y = VIRTUAL_HEIGHT - 170
                
                # Draw semi-transparent background
                box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                box_surf.fill((10, 10, 15, 230))
                pygame.draw.rect(box_surf, npc['color'], (0, 0, box_w, box_h), width=2, border_radius=8)
                self.virtual_screen.blit(box_surf, (box_x, box_y))
                
                # Draw character avatar box
                avatar_size = 90
                avatar_x = box_x + 20
                avatar_y = box_y + 20
                pygame.draw.rect(self.virtual_screen, (25, 25, 30), (avatar_x, avatar_y, avatar_size, avatar_size), border_radius=6)
                pygame.draw.rect(self.virtual_screen, npc['color'], (avatar_x, avatar_y, avatar_size, avatar_size), width=1, border_radius=6)
                
                # Draw vector silhouette for avatar
                pygame.draw.circle(self.virtual_screen, npc['color'], (avatar_x + avatar_size // 2, avatar_y + 35), 18, width=2)
                pygame.draw.arc(self.virtual_screen, npc['color'], (avatar_x + 15, avatar_y + 55, avatar_size - 30, 40), 0, math.pi, width=2)
                
                # NPC Name & Title
                name_lbl = self.font.render(f"{npc['name'].upper()}", True, npc['color'])
                title_lbl = self.small_font.render(f"[{npc['title']}]", True, WHITE)
                self.virtual_screen.blit(name_lbl, (box_x + 130, box_y + 15))
                self.virtual_screen.blit(title_lbl, (box_x + 130 + name_lbl.get_width() + 10, box_y + 21))
                
                # Wrap and draw dialogue text
                dialogue_list = npc['dialogue'].get(self.campaign_stage, ["Hello, Pilot."])
                dialogue_idx = (ticks // 5000) % len(dialogue_list)
                raw_text = dialogue_list[dialogue_idx]
                formatted_text = raw_text.format(
                    name=self.player_name if self.player_name else "PILOT",
                    class_name=getattr(self.player, 'class_name', 'RANGER')
                )
                
                words = formatted_text.split(' ')
                lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if self.small_font.size(test_line)[0] < box_w - 160:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                    
                for idx, line in enumerate(lines):
                    line_surf = self.small_font.render(line, True, (220, 230, 245))
                    self.virtual_screen.blit(line_surf, (box_x + 130, box_y + 50 + idx * 22))
                    
                # Action prompt
                trade_prompt = self.small_font.render("Press P or ESC to Trade / Upgrade", True, GREEN)
                self.virtual_screen.blit(trade_prompt, (box_x + box_w - trade_prompt.get_width() - 20, box_y + 15))
            
        # ---------------- DRAW PLAYING SCROLLING COMBAT ZONE ----------------
        elif (self.state in ('PLAYING', 'GAME_OVER')) or (self.state == 'PAUSED' and self.current_zone != 'HUB'):
            # Draw the Wormhole gate (if active)
            if self.wormhole_spawned:
                exit_center = (int(self.wormhole_pos.x - self.camera_x), int(self.wormhole_pos.y - self.camera_y))
                ticks = pygame.time.get_ticks()
                
                for r_idx, (color, radius_mult, speed) in enumerate([
                    (GREEN, 1.0, 0.003),
                    (PURPLE, 0.8, -0.005),
                    (CYAN, 0.6, 0.007),
                    (WHITE, 0.3, -0.01)
                ]):
                    glow = int(5 * math.sin(ticks * 0.004 + r_idx))
                    radius = int(50 * radius_mult) + glow
                    pygame.draw.circle(self.virtual_screen, color, exit_center, radius, width=2)
                    
                    angle = ticks * speed
                    ox = exit_center[0] + int(radius * math.cos(angle))
                    oy = exit_center[1] + int(radius * math.sin(angle))
                    pygame.draw.circle(self.virtual_screen, color, (ox, oy), 4)
                exit_lbl = self.font.render("WORMHOLE ACTIVE (Enter to Warp)", True, GREEN) # No shake for text
                self.virtual_screen.blit(exit_lbl, ((self.wormhole_pos.x - (self.camera_x + swx)) - exit_lbl.get_width() // 2, self.wormhole_pos.y - (self.camera_y + swy) - 90))
                
                # Draw warp charging progress HUD
                if self.wormhole_charge_timer > 0:
                    target_charge = 1000.0 if self.player.skills.get('hyperdrive', 0) > 0 else 3000.0
                    pct = min(1.0, self.wormhole_charge_timer / target_charge)
                    bar_w = 200
                    bar_h = 12
                    bar_x = (self.wormhole_pos.x - (self.camera_x + swx)) - bar_w // 2
                    bar_y = self.wormhole_pos.y - (self.camera_y + swy) + 80
                    
                    # Background
                    pygame.draw.rect(self.virtual_screen, (44, 44, 44), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                    # Progress bar
                    pygame.draw.rect(self.virtual_screen, GREEN, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)
                    # Border
                    pygame.draw.rect(self.virtual_screen, WHITE, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)
                    
                    # Text countdown
                    secs_left = max(0.0, (target_charge - self.wormhole_charge_timer) / 1000.0)
                    charge_lbl = self.font.render(f"WARPING IN {secs_left:.1f}s... Preparing Hyperdrive...", True, GREEN) # No shake for text
                    self.virtual_screen.blit(charge_lbl, ((self.wormhole_pos.x - (self.camera_x + swx)) - charge_lbl.get_width() // 2, bar_y + 18))
            
            # Level Gimmicks drawing
            for gc in self.gas_clouds:
                gc.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for ad in self.ambient_debris:
                ad.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for crystal in self.shield_crystals:
                crystal.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for gw in self.gravity_wells:
                gw.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)

            # Solar Flare visualization
            if self.current_zone == 'VULCAN' and self.solar_flare_state != 'IDLE':
                draw_fy = self.solar_flare_y - (self.camera_y + swy)
                if self.solar_flare_state == 'WARNING':
                    if pygame.time.get_ticks() % 400 < 200:
                        pygame.draw.rect(self.virtual_screen, (255, 69, 0), (0, draw_fy, VIRTUAL_WIDTH, 120), width=4)
                        warn_text = self.font.render("!!! SOLAR FLARE DETECTED !!!", True, ORANGE)
                        self.virtual_screen.blit(warn_text, (VIRTUAL_WIDTH // 2 - warn_text.get_width() // 2, draw_fy + 45))
                elif self.solar_flare_state == 'ACTIVE':
                    pygame.draw.rect(self.virtual_screen, (255, 140, 0), (0, draw_fy, VIRTUAL_WIDTH, 120)) # No shake here
                    pygame.draw.rect(self.virtual_screen, WHITE, (0, draw_fy + 20, VIRTUAL_WIDTH, 80)) # No shake here
                    for _ in range(3):
                        px = random.randint(0, VIRTUAL_WIDTH)
                        py = self.solar_flare_y + random.randint(0, 120)
                        self.spawn_explosion(px, py, [(255, 69, 0), (255, 215, 0)], count=1)

            for bullet in self.bullets:
                bullet.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for torpedo in self.torpedoes:
                torpedo.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for bomb in self.bombs:
                bomb.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for missile in self.missiles:
                missile.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            
            # Draw enemies with optional shield highlighting
            for enemy in self.enemies:
                enemy.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
                if self.is_enemy_shielded(enemy):
                    draw_ey = enemy.y - (self.camera_y + swy)
                    draw_ex = enemy.x - (self.camera_x + swx)
                    pygame.draw.circle(self.virtual_screen, CYAN, (int(draw_ex + enemy.width // 2), int(draw_ey + enemy.height // 2)), enemy.width + 6, width=2)
                    
            for eb in self.enemy_bullets:
                eb.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
                
            if self.boss:
                self.boss.draw(self.virtual_screen, int(self.camera_y + swy), int(self.camera_x + swx))
                
            for meteor in self.meteors:
                meteor.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for obs in self.static_obstacles:
                obs.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)

            if getattr(self, 'escape_sequence_active', False):
                # Draw the massive expanding black hole
                draw_x = self.escape_blackhole_pos.x - (self.camera_x + swx)
                draw_y = self.escape_blackhole_pos.y - (self.camera_y + swy)
                ticks = pygame.time.get_ticks()
                
                # 1. Accretion disk (outer expanding swirling ring)
                r_outer = int(self.escape_blackhole_radius)
                pygame.draw.circle(self.virtual_screen, (255, 69, 0), (int(draw_x), int(draw_y)), r_outer, width=8)
                pygame.draw.circle(self.virtual_screen, (255, 140, 0), (int(draw_x), int(draw_y)), max(1, r_outer - 15), width=4)
                
                # Swirling particles in the accretion disk
                for i in range(12):
                    angle = math.radians(i * 30 + ticks * 0.04)
                    px = draw_x + (r_outer - 30) * math.cos(angle)
                    py = draw_y + (r_outer - 30) * math.sin(angle)
                    pygame.draw.circle(self.virtual_screen, (255, 200, 0), (int(px), int(py)), 6)
                
                # 2. Outer blue energy boundary
                r_inner = int(self.escape_blackhole_radius * 0.5)
                if r_inner > 5:
                    pygame.draw.circle(self.virtual_screen, (0, 100, 255), (int(draw_x), int(draw_y)), r_inner, width=5)
                    # 3. Pure black event horizon core
                    pygame.draw.circle(self.virtual_screen, (0, 0, 0), (int(draw_x), int(draw_y)), r_inner - 5)

            for d in self.derelicts:
                d.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for du in self.data_uplinks:
                du.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for a in self.anomalies:
                a.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for portal in self.small_portals:
                portal.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for mat in self.materials:
                mat.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for scrap in self.scraps:
                scrap.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            
            # Draw Convoy in Level 2
            if self.current_zone == 'VULCAN' and self.convoy:
                self.convoy.draw(self.virtual_screen, int(self.camera_y + swy), int(self.camera_x + swx))
                
            # Draw Energy Cells in Level 5
            if self.current_zone == 'PLASMA':
                for cell in self.energy_cells:
                    cell.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
                    
            if self.current_zone == 'QUANTUM':
                for portal in self.quantum_portals:
                    portal.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
                if self.quantum_dimension == 'OTHER':
                    for anchor in self.quantum_anchors:
                        anchor.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
                elif self.quantum_dimension == 'NORMAL' and self.black_hole_core:
                    self.black_hole_core.draw(self.virtual_screen, int(self.camera_y + swy), int(self.camera_x + swx))
                    
            # Draw Supernova in Level 4
            if self.current_zone == 'NEBULA' and self.supernova_y is not None:
                draw_y = self.supernova_y - (self.camera_y + swy)
                if draw_y < VIRTUAL_HEIGHT + 400:
                    ticks = pygame.time.get_ticks()
                    wave_surf = pygame.Surface((VIRTUAL_WIDTH, max(200, int(VIRTUAL_HEIGHT + 400 - draw_y))), pygame.SRCALPHA)
                    wave_surf.fill((255, 69, 0, 90))
                    for i in range(3):
                        wave_offset = int(15 * math.sin(ticks * 0.02 + i))
                        pygame.draw.rect(wave_surf, (255, 140 + i * 30, 0, 160 - i * 40), (0, wave_offset, VIRTUAL_WIDTH, 40))
                    self.virtual_screen.blit(wave_surf, (0, int(draw_y)))
            
            self.player.draw(self.virtual_screen, int(self.camera_y + swy), int(self.camera_x + swx))
            
            for ss in self.support_ships:
                ss.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)
            for dr in self.drones:
                dr.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)

            for flare in self.flares: # Draw flares
                flare.draw(self.virtual_screen, self.camera_y + swy, self.camera_x + swx)

            # Boss incoming overlay warning
            if self.boss and not self.boss.is_dead:
                if self.boss.health == self.boss.max_health and pygame.time.get_ticks() % 1000 < 500:
                    warning_lbl = self.large_font.render("BOSS INCOMING!", True, RED)
                    self.virtual_screen.blit(warning_lbl, (VIRTUAL_WIDTH // 2 - warning_lbl.get_width() // 2, 200))

            # Sector start intro overlay
            level_time = pygame.time.get_ticks() - getattr(self, 'level_start_time', 0)
            if self.state == 'PLAYING' and level_time < 3500:
                intro_h = 160
                intro_y = VIRTUAL_HEIGHT // 2 - intro_h // 2
                overlay = pygame.Surface((VIRTUAL_WIDTH, intro_h), pygame.SRCALPHA)
                overlay.fill((5, 5, 8, 180))
                pygame.draw.line(overlay, (0, 255, 255, 150), (0, 0), (VIRTUAL_WIDTH, 0), 1)
                pygame.draw.line(overlay, (0, 255, 255, 150), (0, intro_h - 1), (VIRTUAL_WIDTH, intro_h - 1), 1)
                self.virtual_screen.blit(overlay, (0, intro_y))
                
                cfg = BIOME_CONFIGS.get(self.current_zone, {'name': 'Unknown Sector', 'desc': 'Hostile Environment'})
                lbl_zone = self.large_font.render(cfg['name'].upper(), True, CYAN)
                
                lbl_desc_str = "OBJECTIVE: RETRIEVE 5 MATRIX CORES"
                lbl_extra_str = "WARNING: HEAVY ASTEROID IMPACT HAZARDS & GRAVITY WELLS"
                if self.current_zone == 'TUTORIAL':
                    lbl_desc_str = "OBJECTIVE: COMPLETE PILOT WEAPONS & CONTROLS TRAINING"
                    lbl_extra_str = "SYSTEM STATUS: NO-DAMAGE COCKPIT PRACTICE FIELD"
                elif self.current_zone == 'VULCAN':
                    lbl_desc_str = "OBJECTIVE: ESCORT CONVOY SHIP TO SAFETY"
                    lbl_extra_str = "WARNING: ENEMY INTERCEPTOR RAIDERS INBOUND // STAY CLOSE"
                elif self.current_zone == 'AQUARIS':
                    lbl_desc_str = "OBJECTIVE: LOCATE & DEFEAT FROST ARCH-TEMPEST MINIBOSS"
                    lbl_extra_str = "WARNING: CRYOGENIC SHIELDS ACTIVE // DODGE MISSILES"
                elif self.current_zone == 'NEBULA':
                    lbl_desc_str = "OBJECTIVE: RACE UPWARD AND ESCAPE SUPERNOVA SHOCKWAVE"
                    lbl_extra_str = "DANGER: HIGH RADIATION STORM INCOMING FROM BELOW // FLY UPWARD IMMEDIATELY"
                elif self.current_zone == 'PLASMA':
                    lbl_desc_str = "OBJECTIVE: CHARGE SECTOR GENERATORS WITH 5 ENERGY CELLS"
                    lbl_extra_str = "WARNING: AVOID VOLATILE ELECTRICAL CURRENTS & SOLAR JUGGERNAUTS"
                elif self.current_zone == 'VOID':
                    lbl_desc_str = "OBJECTIVE: HUNT & DEFEAT 4 ABYSS SENTINELS"
                    lbl_extra_str = "WARNING: EXTRADIMENSIONAL SINGULARITIES DETECTED"
                elif self.current_zone == 'QUANTUM':
                    lbl_desc_str = "OBJECTIVE: SHATTER 3 DIMENSIONAL STABILIZERS"
                    lbl_extra_str = "WARNING: WEAVE BETWEEN NORMAL & SPIRIT REALMS TO ATTACK Hidden CORE"
                elif self.current_zone == 'SINGULARITY':
                    lbl_desc_str = "OBJECTIVE: INFILTRATE FACTORY CORE & SABOTAGE MELTDOWN"
                    lbl_extra_str = "WARNING: NARROW GRID CORRIDORS & INDESTRUCTIBLE WALL HAZARDS"
                elif self.current_zone == 'ORION':
                    lbl_desc_str = "OBJECTIVE: LAY SIEGE TO ORION OVERLORD CITADEL"
                    lbl_extra_str = "WARNING: FINAL ENEMY CITADEL FORTRESS // CRUSH SHIELD DRONES"
                    
                lbl_desc = self.font.render(lbl_desc_str, True, WHITE)
                lbl_extra = self.small_font.render(lbl_extra_str, True, GREEN)
                
                self.virtual_screen.blit(lbl_zone, (VIRTUAL_WIDTH // 2 - lbl_zone.get_width() // 2, intro_y + 20))
                self.virtual_screen.blit(lbl_desc, (VIRTUAL_WIDTH // 2 - lbl_desc.get_width() // 2, intro_y + 90))
                self.virtual_screen.blit(lbl_extra, (VIRTUAL_WIDTH // 2 - lbl_extra.get_width() // 2, intro_y + 125))
        for particle in self.particles:
            particle.draw(self.virtual_screen, (self.camera_y + swy) if self.state == 'PLAYING' else swy, (self.camera_x + swx) if self.state == 'PLAYING' else swx)
            
        for sw in self.shockwaves:
            sw.draw(self.virtual_screen, (self.camera_y + swy) if self.state == 'PLAYING' else swy, (self.camera_x + swx) if self.state == 'PLAYING' else swx)
            
        # Redirect drawing to dedicated UI layer
        original_virtual_screen = self.virtual_screen
        self.virtual_screen = self.ui_surface

        # Draw HUD UI
        if self.state in ('PLAYING', 'PAUSED', 'GAME_OVER', 'HUB'):
            hud_bg = pygame.Surface((250, 135), pygame.SRCALPHA)
            hud_bg.fill((5, 5, 8, 120))
            pygame.draw.rect(hud_bg, (0, 255, 255, 120), (0, 0, 250, 135), width=1)
            self.virtual_screen.blit(hud_bg, (5, 5))
            
            credits_text = self.font.render(f"Credits: {self.player.credits} C", True, GREEN)
            self.virtual_screen.blit(credits_text, (15, 12))
            
            scrap_text = self.font.render(f"Scrap: {self.player.scraps}", True, GOLD)
            self.virtual_screen.blit(scrap_text, (15 + credits_text.get_width() + 15, 12))
            
            zone_text = self.font.render(f"Location: {self.current_zone}", True, WHITE)
            self.virtual_screen.blit(zone_text, (15, 42))
            
            player_name_lbl = self.small_font.render(f"PILOT: {self.player_name}", True, WHITE)
            self.virtual_screen.blit(player_name_lbl, (15, 58))
            
            shield_lbl = self.small_font.render("SHIELDS:", True, CYAN)
            self.virtual_screen.blit(shield_lbl, (15, 74))
            
            shield_x = 15
            shield_y = 92
            segment_width = 25
            segment_height = 12
            for i in range(self.player.max_shields):
                rect = pygame.Rect(shield_x + i * (segment_width + 5), shield_y, segment_width, segment_height)
                if i < int(self.player.shields):
                    pygame.draw.rect(self.virtual_screen, CYAN, rect)
                elif i < self.player.shields:
                    fill_pct = self.player.shields - i
                    fill_w = int(segment_width * fill_pct)
                    pygame.draw.rect(self.virtual_screen, (0, 60, 60), rect)
                    pygame.draw.rect(self.virtual_screen, CYAN, rect, width=1)
                    if fill_w > 0:
                        part_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
                        pygame.draw.rect(self.virtual_screen, CYAN, part_rect)
                else:
                    pygame.draw.rect(self.virtual_screen, (0, 40, 40), rect, width=1)
            
            flare_label = self.small_font.render("FLARES:", True, ORANGE)
            self.virtual_screen.blit(flare_label, (15, 110))
            for i in range(self.player.max_flare_ammo):
                fx = 15 + flare_label.get_width() + 10 + i * 15
                fy = 118
                color = ORANGE if i < self.player.flare_ammo else (60, 40, 20)
                pygame.draw.rect(self.virtual_screen, color, (fx - 4, fy - 4, 8, 8), width=1)
                if i < self.player.flare_ammo:
                    pygame.draw.rect(self.virtual_screen, WHITE, (fx - 2, fy - 2, 4, 4))
            
            # ---------------- TACTICAL MINIMAP HUD (RELATIVE SCROLLING) ----------------
            if self.state == 'PLAYING':
                mm_w = 130
                mm_h = 130
                mm_x = VIRTUAL_WIDTH - mm_w - 15
                mm_y = 115
                
                pygame.draw.rect(self.virtual_screen, (5, 5, 8, 120), (mm_x, mm_y, mm_w, mm_h))
                pygame.draw.rect(self.virtual_screen, (0, 255, 255, 120), (mm_x, mm_y, mm_w, mm_h), width=1)
                
                # Radar bounds checking
                def inside_mm(mx, my):
                    return mm_x <= mx <= mm_x + mm_w and mm_y <= my <= mm_y + mm_h
                
                map_radius = 2000.0
                scale_x = (mm_w / 2.0) / map_radius
                scale_y = (mm_h / 2.0) / map_radius
                
                px_center = self.player.x + self.player.width // 2
                py_center = self.player.y + self.player.height // 2
                
                def to_mm(x_coord, y_coord):
                    dx = x_coord - px_center
                    dy = y_coord - py_center
                    mx = mm_x + mm_w // 2 + dx * scale_x
                    my = mm_y + mm_h // 2 + dy * scale_y
                    return int(mx), int(my)
                
                # Draw Active Wormhole Gate when spawned
                if self.wormhole_spawned:
                    wg_x, wg_y = to_mm(self.wormhole_pos.x, self.wormhole_pos.y)
                    if inside_mm(wg_x, wg_y):
                        pygame.draw.circle(self.virtual_screen, GREEN, (wg_x, wg_y), 5)
                
                # Draw Matrix Cores
                for mat in self.materials:
                    mx, my = to_mm(mat.x, mat.y)
                    if inside_mm(mx, my):
                        pygame.draw.rect(self.virtual_screen, ORANGE, (mx - 3, my - 3, 6, 6))
                    
                # Draw Static obstacles
                for obs in self.static_obstacles:
                    ox, oy = to_mm(obs.x, obs.y)
                    if inside_mm(ox, oy):
                        pygame.draw.circle(self.virtual_screen, SLATE_GRAY, (ox, oy), 2)
                    
                # Draw enemies
                for enemy in self.enemies:
                    ex, ey = to_mm(enemy.x, enemy.y)
                    if inside_mm(ex, ey):
                        pygame.draw.circle(self.virtual_screen, RED, (ex, ey), 2)
                    
                # Draw Player exactly in the center
                px, py = to_mm(px_center, py_center)
                pulse_color = CYAN if pygame.time.get_ticks() % 500 < 250 else WHITE
                pygame.draw.circle(self.virtual_screen, pulse_color, (px, py), 4)
                
                mm_label = self.small_font.render("MAP SCANNER", True, SLATE_GRAY)
                self.virtual_screen.blit(mm_label, (mm_x, mm_y - 20))
                
                objective_text_str = f"CORES: {self.materials_collected}/5"
                if self.current_zone == 'TUTORIAL':
                    objective_text_str = "TRAINING RANGE"
                elif self.current_zone == 'VULCAN' and self.convoy:
                    objective_text_str = f"CONVOY HP: {int(self.convoy.health)}%  |  TIME LEFT: {int(self.convoy_defend_timer)}s"
                elif self.current_zone == 'NEBULA':
                    objective_text_str = f"ESCAPE: {max(0, int(-self.player.y))}/6000"
                elif self.current_zone == 'PLASMA':
                    objective_text_str = f"CELLS: {self.energy_cells_collected}/5"
                elif self.current_zone == 'QUANTUM':
                    if self.quantum_anchors:
                        objective_text_str = f"ANCHORS LEFT: {len(self.quantum_anchors)}/3  ({self.quantum_dimension})"
                    elif self.black_hole_core:
                        objective_text_str = f"DESTROY CORE: {int(self.black_hole_core.health)}%  ({self.quantum_dimension})"
                    else:
                        objective_text_str = "CORE DESTROYED"
                elif self.current_zone == 'VOID':
                    objective_text_str = f"SENTINELS DESTROYED: {self.void_enemies_killed}/4"
                elif self.boss:
                    objective_text_str = f"BOSS HP: {int(self.boss.health)}"

                core_label = self.small_font.render(objective_text_str, True, WHITE)
                self.virtual_screen.blit(core_label, (mm_x, mm_y + mm_h + 8))

            # Screen-edge Radar for off-screen cores / power cells
            if self.state == 'PLAYING':
                player_pos = pygame.math.Vector2(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2)
                closest_core = None
                min_dist = float('inf')
                
                targets_list = []
                if self.materials:
                    targets_list = self.materials
                elif self.current_zone == 'PLASMA' and self.energy_cells:
                    targets_list = self.energy_cells
                    
                for mat in targets_list:
                    core_pos = pygame.math.Vector2(mat.x, mat.y)
                    dist = player_pos.distance_to(core_pos)
                    if dist < min_dist:
                        min_dist = dist
                        closest_core = mat
                
                if closest_core:
                    core_screen_x = closest_core.x - self.camera_x
                    core_screen_y = closest_core.y - self.camera_y
                    
                    is_offscreen = (core_screen_x < 40 or core_screen_x > VIRTUAL_WIDTH - 40 or
                                    core_screen_y < 40 or core_screen_y > VIRTUAL_HEIGHT - 40)
                    
                    if is_offscreen:
                        center_screen = pygame.math.Vector2(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2)
                        target_screen = pygame.math.Vector2(core_screen_x, core_screen_y)
                        dir_vector = (target_screen - center_screen).normalize()
                        
                        margin_x = 70
                        margin_y = 70
                        edge_x = VIRTUAL_WIDTH // 2 + dir_vector.x * (VIRTUAL_WIDTH // 2 - margin_x)
                        edge_y = VIRTUAL_HEIGHT // 2 + dir_vector.y * (VIRTUAL_HEIGHT // 2 - margin_y)
                        edge_x = max(margin_x, min(VIRTUAL_WIDTH - margin_x, edge_x))
                        edge_y = max(margin_y, min(VIRTUAL_HEIGHT - margin_y, edge_y))
                        
                        angle = math.degrees(math.atan2(dir_vector.y, dir_vector.x))
                        arrow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                        pygame.draw.polygon(arrow_surf, GOLD, [(8, 4), (24, 15), (8, 26), (14, 15)])
                        rot_arrow = pygame.transform.rotate(arrow_surf, -angle)
                        
                        glow = int(2 * math.sin(pygame.time.get_ticks() * 0.015))
                        pygame.draw.circle(self.virtual_screen, (218, 165, 32, 120 + int(30 * glow)), (int(edge_x), int(edge_y)), 18, width=2)
                        
                        dist_text = self.small_font.render(f"{int(min_dist)}m", True, GOLD)
                        self.virtual_screen.blit(rot_arrow, (int(edge_x - rot_arrow.get_width() // 2), int(edge_y - rot_arrow.get_height() // 2)))
                        self.virtual_screen.blit(dist_text, (int(edge_x - dist_text.get_width() // 2), int(edge_y + 20)))

            # Persistent Escape Portal Radar
            if self.state == 'PLAYING' and self.wormhole_spawned:
                player_pos = pygame.math.Vector2(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2)
                to_portal = self.wormhole_pos - player_pos
                dist = to_portal.length()
                
                portal_screen_x = self.wormhole_pos.x - self.camera_x
                portal_screen_y = self.wormhole_pos.y - self.camera_y
                
                is_offscreen = (portal_screen_x < 120 or portal_screen_x > VIRTUAL_WIDTH - 120 or
                                portal_screen_y < 120 or portal_screen_y > VIRTUAL_HEIGHT - 120)
                
                if is_offscreen or dist > 200:
                    target_dir = to_portal.normalize()
                    margin = 90
                    edge_x = VIRTUAL_WIDTH // 2 + target_dir.x * (VIRTUAL_WIDTH // 2 - margin)
                    edge_y = VIRTUAL_HEIGHT // 2 + target_dir.y * (VIRTUAL_HEIGHT // 2 - margin)
                    edge_x = max(margin, min(VIRTUAL_WIDTH - margin, edge_x))
                    edge_y = max(margin, min(VIRTUAL_HEIGHT - margin, edge_y))
                    
                    angle = math.degrees(math.atan2(target_dir.y, target_dir.x))
                    arrow_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
                    pygame.draw.polygon(arrow_surf, GREEN, [(10, 5), (42, 25), (10, 45), (20, 25)])
                    rot_arrow = pygame.transform.rotate(arrow_surf, -angle)
                    
                    self.virtual_screen.blit(rot_arrow, (int(edge_x - rot_arrow.get_width() // 2), int(edge_y - rot_arrow.get_height() // 2)))
                    dist_lbl = self.font.render(f"EXIT: {int(dist)}m", True, GREEN)
                    self.virtual_screen.blit(dist_lbl, (int(edge_x - dist_lbl.get_width() // 2), int(edge_y + 35)))

            if getattr(self, 'boss_defeated', False) and self.wormhole_spawned:
                # Pulse red overlay on screen to indicate collapse
                ticks = pygame.time.get_ticks()
                pulse = int(25 + 20 * math.sin(ticks * 0.007))
                red_overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                red_overlay.fill((255, 0, 0, pulse))
                self.virtual_screen.blit(red_overlay, (0, 0))
                
                if current_time - getattr(self, 'last_siren_play', 0) > 1000:
                    self.last_siren_play = current_time
                    if SOUNDS: SOUNDS.play('siren')
                
                # Warning text
                warning_font = pygame.font.SysFont("Arial", 36, bold=True)
                if getattr(self, 'escape_sequence_active', False):
                    warning_lbl = warning_font.render("WARNING: REACTOR MELTDOWN!", True, (255, 69, 0))
                    
                    evac_lbl = warning_font.render("ESCAPE THE COLLAPSE TO THE PORTAL!", True, (255, 255, 255))
                    
                else:
                    warning_lbl = warning_font.render("WARNING: SECTOR DE-STABILIZING", True, (255, 69, 0))
                    evac_lbl = warning_font.render("EVACUATE TO PORTAL IMMEDIATELY!", True, (255, 255, 255))
                self.virtual_screen.blit(warning_lbl, (VIRTUAL_WIDTH // 2 - warning_lbl.get_width() // 2, 220))
                self.virtual_screen.blit(evac_lbl, (VIRTUAL_WIDTH // 2 - evac_lbl.get_width() // 2, 270))

            if self.state == 'PLAYING':
                panel_w = 320
                panel_h = 160
                panel_x = VIRTUAL_WIDTH - panel_w - 5
                panel_y = 5
                
                hud_bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                hud_bg.fill((5, 5, 8, 120))
                pygame.draw.rect(hud_bg, (0, 255, 255, 120), (0, 0, panel_w, panel_h), width=1)
                self.virtual_screen.blit(hud_bg, (panel_x, panel_y))
                
                bar_width = 120
                bar_height = 8
                bar_x = panel_x + panel_w - bar_width - 15
                
                # Secondary Weapon HUD (Torpedo, Bombs, or Missiles)
                sec_y = panel_y + 18
                if self.player.active_secondary == 0:
                    actual_delay = self.player.torpedo_delay * (1.0 - 0.15 * self.player.skills['torpedo'])
                    time_since = current_time - self.player.last_torpedo
                    ratio = min(1.0, time_since / actual_delay)
                    label_txt = "TORPEDO:"
                elif self.player.active_secondary == 1:
                    actual_delay = 500
                    time_since = current_time - self.player.last_secondary
                    ratio = min(1.0, time_since / actual_delay) if self.player.bomb_ammo > 0 else 0.0
                    label_txt = f"BOMBS ({self.player.bomb_ammo}):"
                else:
                    actual_delay = 400
                    time_since = current_time - self.player.last_secondary
                    ratio = min(1.0, time_since / actual_delay) if self.player.missile_ammo > 0 else 0.0
                    label_txt = f"MISSILES ({self.player.missile_ammo}):"
                    
                pygame.draw.rect(self.virtual_screen, (30, 40, 50), (bar_x, sec_y, bar_width, bar_height), border_radius=2)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, (bar_x, sec_y, bar_width, bar_height), width=1, border_radius=2)
                fill_width = int(bar_width * ratio)
                fill_color = (0, 255, 100) if ratio == 1.0 else (255, 150, 0)
                pygame.draw.rect(self.virtual_screen, fill_color, (bar_x, sec_y, fill_width, bar_height), border_radius=2)
                
                sec_label = self.small_font.render(label_txt, True, WHITE if ratio == 1.0 else (180, 180, 180))
                self.virtual_screen.blit(sec_label, (panel_x + 15, sec_y - 4))
                
                # Laser Heat
                # Primary Weapon Heat
                p_names = ["LASER", "SHOTGUN", "RAILGUN"]
                heat_y = panel_y + 46
                pygame.draw.rect(self.virtual_screen, (30, 40, 50), (bar_x, heat_y, bar_width, bar_height), border_radius=2)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, (bar_x, heat_y, bar_width, bar_height), width=1, border_radius=2)
                heat_ratio = self.player.heat / self.player.max_heat
                heat_fill_width = int(bar_width * heat_ratio)
                
                r = int(255 * heat_ratio)
                g = int(255 * (1.0 - heat_ratio))
                heat_color = (r, g, 0)
                if self.player.overheated:
                    heat_color = RED if pygame.time.get_ticks() % 200 < 100 else WHITE
                    
                pygame.draw.rect(self.virtual_screen, heat_color, (bar_x, heat_y, heat_fill_width, bar_height), border_radius=2)
                
                heat_label_text = "OVERHEAT!" if self.player.overheated else f"{p_names[self.player.active_primary]} HEAT:"
                heat_label_color = RED if self.player.overheated else WHITE
                heat_label = self.small_font.render(heat_label_text, True, heat_label_color)
                self.virtual_screen.blit(heat_label, (panel_x + 15, heat_y - 4))
                
                # Dash
                dash_y = panel_y + 74
                pygame.draw.rect(self.virtual_screen, (30, 40, 50), (bar_x, dash_y, bar_width, bar_height), border_radius=2)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, (bar_x, dash_y, bar_width, bar_height), width=1, border_radius=2)
                time_since_dash = current_time - self.player.last_dash
                dash_ratio = min(1.0, time_since_dash / self.player.dash_cooldown)
                dash_fill_width = int(bar_width * dash_ratio)
                
                if dash_ratio == 1.0:
                    pulse_val = abs(math.sin(pygame.time.get_ticks() * 0.01))
                    dash_color = (int(0 + 50 * pulse_val), int(200 + 55 * pulse_val), 255)
                else:
                    dash_color = (138, 43, 226)
                
                pygame.draw.rect(self.virtual_screen, dash_color, (bar_x, dash_y, dash_fill_width, bar_height), border_radius=2)
                
                dash_label_text = "THRUST DASH:" if dash_ratio == 1.0 else "DASH COOLDOWN:"
                dash_label_color = CYAN if dash_ratio == 1.0 else (160, 160, 160)
                dash_label = self.small_font.render(dash_label_text, True, dash_label_color)
                self.virtual_screen.blit(dash_label, (panel_x + 15, dash_y - 4))
                
                # Special Ability Cooldown
                ability_y = panel_y + 102
                pygame.draw.rect(self.virtual_screen, (30, 40, 50), (bar_x, ability_y, bar_width, bar_height), border_radius=2)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, (bar_x, ability_y, bar_width, bar_height), width=1, border_radius=2)
                time_since_ability = current_time - self.player.last_ability
                ability_ratio = min(1.0, time_since_ability / self.player.ability_cooldown)
                ability_fill_width = int(bar_width * ability_ratio)
                
                ability_names = {'RANGER': 'OVERDRIVE', 'ENGINEER': 'SENTRY DRONES', 'VANGUARD': 'GUARDIAN CRYSTAL', 'SNIPER': 'PRECISION STRIKE', 'ASSASSIN': 'STEALTH CLOAK'}
                ability_name = ability_names.get(self.player.class_name, 'SPECIAL')
                
                if ability_ratio == 1.0:
                    ability_color = (0, 255, 150)
                else:
                    ability_color = (100, 100, 150)
                pygame.draw.rect(self.virtual_screen, ability_color, (bar_x, ability_y, ability_fill_width, bar_height), border_radius=2)
                
                ability_label = self.small_font.render(f"{ability_name}:", True, WHITE if ability_ratio == 1.0 else (160, 160, 160))
                self.virtual_screen.blit(ability_label, (panel_x + 15, ability_y - 4))

                # Specialist Ability Cooldown
                special_y = panel_y + 130
                pygame.draw.rect(self.virtual_screen, (30, 40, 50), (bar_x, special_y, bar_width, bar_height), border_radius=2)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, (bar_x, special_y, bar_width, bar_height), width=1, border_radius=2)
                time_since_special = current_time - self.player.last_special
                special_ratio = min(1.0, time_since_special / self.player.special_cooldown)
                special_fill_width = int(bar_width * special_ratio)
                
                special_name = self.player.class_upgrades.get('special_name', 'SPECIALIST')
                
                if special_ratio == 1.0:
                    special_color = (0, 200, 255)
                else:
                    special_color = (60, 100, 120)
                pygame.draw.rect(self.virtual_screen, special_color, (bar_x, special_y, special_fill_width, bar_height), border_radius=2)
                
                special_label = self.small_font.render(f"{special_name}:", True, WHITE if special_ratio == 1.0 else (160, 160, 160))
                self.virtual_screen.blit(special_label, (panel_x + 15, special_y - 4))
                
                if self.current_zone == 'TUTORIAL':
                    # Draw beautiful semi-transparent guide card at the bottom
                    panel_rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 350, VIRTUAL_HEIGHT - 170, 700, 140)
                    pygame.draw.rect(self.virtual_screen, (15, 25, 30, 230), panel_rect, border_radius=10)
                    pygame.draw.rect(self.virtual_screen, GREEN, panel_rect, width=2, border_radius=10)
                    
                    # Title
                    slide = self.tutorial_dialogues[self.tutorial_stage]
                    title_surf = self.font.render(slide["title"], True, GREEN)
                    self.virtual_screen.blit(title_surf, (panel_rect.x + 20, panel_rect.y + 12))
                    
                    # Text wrapping helper
                    words = slide["text"].split(" ")
                    lines = []
                    current_line = ""
                    for word in words:
                        test_line = current_line + " " + word if current_line else word
                        test_surf = self.small_font.render(test_line, True, WHITE)
                        if test_surf.get_width() < 660:
                            current_line = test_line
                        else:
                            lines.append(current_line)
                            current_line = word
                    if current_line:
                        lines.append(current_line)
                        
                    for idx, line in enumerate(lines[:3]):
                        line_surf = self.small_font.render(line, True, WHITE)
                        self.virtual_screen.blit(line_surf, (panel_rect.x + 20, panel_rect.y + 42 + idx * 20))
                        
                    # Dialogue Buttons
                    vmx, vmy = self._get_virtual_mouse_pos()
                    if self.tutorial_stage > 0:
                        prev_rect = pygame.Rect(panel_rect.x + 460, panel_rect.y + 100, 100, 30)
                        prev_hover = prev_rect.collidepoint(vmx, vmy)
                        prev_color = (0, 150, 80) if prev_hover else (0, 80, 40)
                        pygame.draw.rect(self.virtual_screen, prev_color, prev_rect, border_radius=5)
                        pygame.draw.rect(self.virtual_screen, GREEN, prev_rect, width=1, border_radius=5)
                        prev_lbl = self.small_font.render("BACK", True, WHITE)
                        self.virtual_screen.blit(prev_lbl, (prev_rect.x + prev_rect.width // 2 - prev_lbl.get_width() // 2, prev_rect.y + 6))
                        
                    action_rect = pygame.Rect(panel_rect.x + 575, panel_rect.y + 100, 110, 30)
                    action_hover = action_rect.collidepoint(vmx, vmy)
                    action_color = (0, 180, 100) if action_hover else (0, 110, 50)
                    pygame.draw.rect(self.virtual_screen, action_color, action_rect, border_radius=5)
                    pygame.draw.rect(self.virtual_screen, GREEN, action_rect, width=1, border_radius=5)
                    action_lbl = self.small_font.render(slide["action"], True, WHITE)
                    self.virtual_screen.blit(action_lbl, (action_rect.x + action_rect.width // 2 - action_lbl.get_width() // 2, action_rect.y + 6))

            # Boss approaching warning overlay
            if self.boss and self.boss.zone != 'SINGULARITY' and getattr(self.boss, 'appearance_timer', 0) > 0 and not self.boss.is_dead:
                banner_y = VIRTUAL_HEIGHT // 2 - 80
                banner_surf = pygame.Surface((VIRTUAL_WIDTH, 140), pygame.SRCALPHA)
                ticks = pygame.time.get_ticks()
                pulse_alpha = int(100 + 80 * math.sin(ticks * 0.01))
                banner_surf.fill((30, 0, 0, pulse_alpha))
                pygame.draw.rect(banner_surf, RED, (0, 0, VIRTUAL_WIDTH, 140), width=3)
                self.virtual_screen.blit(banner_surf, (0, banner_y))
                
                warn_lbl1 = self.large_font.render("ALERT: THREAT INCOMING", True, RED)
                warn_lbl2 = self.font.render(f"=== {self.boss.name} EN ROUTE ===", True, YELLOW)
                
                self.virtual_screen.blit(warn_lbl1, (VIRTUAL_WIDTH // 2 - warn_lbl1.get_width() // 2, banner_y + 20))
                self.virtual_screen.blit(warn_lbl2, (VIRTUAL_WIDTH // 2 - warn_lbl2.get_width() // 2, banner_y + 85))

        # Restore virtual screen for zoom processing
        self.virtual_screen = original_virtual_screen

        # 2. ZOOM PROCESSING (Apply zoom to world slice before HUD is drawn)
        if getattr(self, 'zoom_level', 1.0) > 1.0:
            zoom_w = int(VIRTUAL_WIDTH / self.zoom_level)
            zoom_h = int(VIRTUAL_HEIGHT / self.zoom_level)
            
            px, py = self.player.rect.center
            draw_cam_x = self.camera_x if self.state != 'HUB' else 0
            draw_cam_y = self.camera_y if self.state != 'HUB' else 0
            
            px_scr = px - draw_cam_x
            py_scr = py - draw_cam_y
            
            cx = max(zoom_w // 2, min(VIRTUAL_WIDTH - zoom_w // 2, px_scr))
            cy = max(zoom_h // 2, min(VIRTUAL_HEIGHT - zoom_h // 2, py_scr))
            
            src_rect = pygame.Rect(cx - zoom_w // 2, cy - zoom_h // 2, zoom_w, zoom_h)
            src_rect = src_rect.clamp(pygame.Rect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            
            try:
                # Capture zoomed view and stretch it back onto virtual_screen before HUD blitting
                zoomed_view = self.virtual_screen.subsurface(src_rect).copy()
                self.virtual_screen.fill(BLACK)
                pygame.transform.smoothscale(zoomed_view, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT), self.virtual_screen)
            except:
                pass

        # Swap back to UI layer for overlays
        self.virtual_screen = self.ui_surface

        # Transition handling
        if getattr(self, 'transition_state', None) == 'INTRO_TO_MAIN_MENU':
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.transition_start_time
            progress = min(1.0, elapsed / float(self.transition_duration))
            # Smooth Ease-in-out transition curve
            t = progress * progress * (3.0 - 2.0 * progress)
            
            # Temporary surfaces to render states separately
            intro_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            menu_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            
            intro_time = current_time - getattr(self, 'intro_start_time', 0)
            self.draw_intro_overlay(intro_surf, intro_time, ticks)
            self.draw_main_menu_overlay(menu_surf, ticks, draw_state='MAIN_MENU')
            
            # Fade out intro
            intro_surf.set_alpha(int((1.0 - t) * 255))
            # Fade in menu
            menu_surf.set_alpha(int(t * 255))
            
            self.virtual_screen.blit(intro_surf, (0, 0))
            self.virtual_screen.blit(menu_surf, (0, 0))
            
        elif self.state == 'INTRO':
            intro_time = pygame.time.get_ticks() - getattr(self, 'intro_start_time', 0)
            self.draw_intro_overlay(self.virtual_screen, intro_time, ticks)

        elif self.state in ('MAIN_MENU', 'CLASS_SELECT'):
            self.draw_main_menu_overlay(self.virtual_screen, ticks)

        # Pause Menu with Ship Upgrades Shop
        elif self.state == 'PAUSED':
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.virtual_screen.blit(overlay, (0, 0))
            
            # Recalculate mouse positions using letterbox scale for hover effects
            mx, my = pygame.mouse.get_pos()
            vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
            vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
            
            # Helper to fit text into boxes dynamically by adjusting font size
            def render_fit_text(text, color, max_w, base_font_size=15, is_bold=True):
                font_size = base_font_size
                while font_size > 8:
                    test_font = pygame.font.SysFont("Arial", font_size, bold=is_bold)
                    lbl = test_font.render(text, True, color)
                    if lbl.get_width() <= max_w:
                        return lbl
                    font_size -= 1
                test_font = pygame.font.SysFont("Arial", 8)
                return test_font.render(text, True, color)
                
            title = self.large_font.render("GAME PAUSED", True, YELLOW)
            self.virtual_screen.blit(title, (100, 250))
            
            # Class / Weapon Loadout Selector
            if self.current_zone == 'HUB' and self.hub_station_active and self.hub_station_active not in ('WEAPONRY', 'ENGINEERING'):
                loadout_lbl = self.font.render("ACTIVE STATION LOADOUT:", True, CYAN)
                self.virtual_screen.blit(loadout_lbl, (100, 470))

                # Primary Selector
                p_names = [getattr(self.player, 'specialist_weapon_name', 'LASER'), "SHOTGUN", "RAILGUN"]
                for i, name in enumerate(p_names):
                    rect = pygame.Rect(100 + i * 140, 520, 130, 50)
                    color = GREEN if self.player.active_primary == i else (40, 40, 40)
                    pygame.draw.rect(self.virtual_screen, color, rect, border_radius=5)
                    pygame.draw.rect(self.virtual_screen, WHITE, rect, width=2, border_radius=5)
                    lbl = self.small_font.render(name, True, WHITE)
                    self.virtual_screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))
                
                # Secondary Selector
                s_names = ["TORPEDO", "MINE", "MISSILE"]
                self.virtual_screen.blit(self.small_font.render("SECONDARY WEAPON:", True, WHITE), (100, 650))
                for i, name in enumerate(s_names):
                    rect = pygame.Rect(100 + i * 140, 680, 130, 50)
                    color = GOLD if self.player.active_secondary == i else (40, 40, 40)
                    pygame.draw.rect(self.virtual_screen, color, rect, border_radius=5)
                    pygame.draw.rect(self.virtual_screen, WHITE, rect, width=2, border_radius=5)
                    lbl = self.small_font.render(name, True, WHITE)
                    self.virtual_screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

                resume_y = 350
                quit_y = 410
            else:
                resume_y = 350
                quit_y = 410
                
            resume = self.font.render("Press ESC or P to Resume", True, WHITE)
            self.virtual_screen.blit(resume, (100, resume_y))
            
            quit_lbl = self.font.render("Press M to Quit to Main Menu", True, RED)
            self.virtual_screen.blit(quit_lbl, (100, quit_y))
            
            # Save Game Button (one-click file saving)
            save_btn = pygame.Rect(100, 780, 300, 45)
            save_hover = save_btn.collidepoint(vmx, vmy)
            save_btn_color = CYAN if save_hover else BLUE
            save_border_color = WHITE if save_hover else SLATE_GRAY
            pygame.draw.rect(self.virtual_screen, save_btn_color, save_btn, border_radius=6)
            pygame.draw.rect(self.virtual_screen, save_border_color, save_btn, width=1, border_radius=6)
            
            save_btn_lbl = self.font.render("SAVE GAME", True, BLACK if save_hover else WHITE)
            self.virtual_screen.blit(save_btn_lbl, (save_btn.centerx - save_btn_lbl.get_width() // 2, save_btn.centery - save_btn_lbl.get_height() // 2))
            
            # Save feedback message
            if getattr(self, 'save_feedback_msg', '') != "" and pygame.time.get_ticks() - getattr(self, 'save_feedback_time', 0) < 3000:
                fb_color = GREEN if "success" in self.save_feedback_msg.lower() or "loaded" in self.save_feedback_msg.lower() or "saved" in self.save_feedback_msg.lower() else RED
                fb_lbl = self.small_font.render(self.save_feedback_msg, True, fb_color)
                self.virtual_screen.blit(fb_lbl, (save_btn.centerx - fb_lbl.get_width() // 2, save_btn.bottom + 5))
            
            pygame.draw.line(self.virtual_screen, SLATE_GRAY, (600, 150), (600, 800), 2)
            
            if self.current_zone != 'HUB' or not self.hub_station_active:
                tree_title = self.large_font.render("COMMUNICATIONS LINK...", True, RED)
                self.virtual_screen.blit(tree_title, (650, 250))

                sp_text = self.font.render("Ship upgrades are only available at the Space Station Hub.", True, WHITE)
                self.virtual_screen.blit(sp_text, (650, 330))

                wallet_lbl1 = self.font.render(f"Wallet: {self.player.credits} Credits", True, GREEN)
                self.virtual_screen.blit(wallet_lbl1, (650, 380))
                wallet_lbl2 = self.font.render(f"  |  {self.player.scraps} Scrap", True, GOLD)
                self.virtual_screen.blit(wallet_lbl2, (650 + wallet_lbl1.get_width(), 380))

                hint_lbl = self.small_font.render("Safely return to Hub via Warp Portals to upgrade equipment.", True, YELLOW)
                self.virtual_screen.blit(hint_lbl, (650, 430))
            elif self.hub_station_active == 'SUPPLY':
                tree_title = self.large_font.render("SUPPLY DEPOT", True, GREEN)
                self.virtual_screen.blit(tree_title, (650, 100))
                
                wallet_lbl = self.font.render(f"Credits: {self.player.credits}", True, GREEN)
                self.virtual_screen.blit(wallet_lbl, (650, 170))
                
                owned_list = [self.player.has_mod_piercing, self.player.has_mod_split, self.player.has_mod_siphon]
                items = [
                    ('Shield Repair', 75, f"Restore 1 unit of shield. Current: {self.player.shields}/{self.player.max_shields}"),
                    ('Torpedo Refill', 100, f"Full ammo reload. Current: {self.player.torpedo_ammo}"),
                    ('Bomb Refill', 150, f"Full ammo reload. Current: {self.player.bomb_ammo}"),
                    ('Missile Refill', 200, f"Full ammo reload. Current: {self.player.missile_ammo}"),
                    ('Flare Refill', 50, f"Full ammo reload. Current: {self.player.flare_ammo}"),
                    ('Mod: Piercing Rounds', 300, "Lasers pierce through 1 target. (Mod Slot)"),
                    ('Mod: Split Shot', 400, "Fires 2 extra diagonal side lasers. (Mod Slot)"),
                    ('Mod: Shield Siphon', 350, "Siphons 0.05 shield points on laser hit. (Mod Slot)")
                ]
                for i, (name, cost, desc) in enumerate(items):
                    rect = pygame.Rect(650, 210 + i * 80, 480, 68)
                    color = (20, 30, 40)
                    if rect.collidepoint(vmx, vmy): color = (40, 50, 60)
                    pygame.draw.rect(self.virtual_screen, color, rect, border_radius=5)
                    pygame.draw.rect(self.virtual_screen, GREEN, rect, width=1, border_radius=5)
                    
                    self.virtual_screen.blit(self.font.render(name, True, WHITE), (rect.x + 15, rect.y + 10))
                    self.virtual_screen.blit(self.small_font.render(desc, True, GRAY), (rect.x + 15, rect.y + 35))
                    
                    is_owned_mod = (i >= 5 and owned_list[i-5])
                    if is_owned_mod:
                        cost_lbl = self.font.render("OWNED", True, GOLD)
                    else:
                        cost_lbl = self.font.render(f"{cost} C", True, GREEN if self.player.credits >= cost else RED)
                    self.virtual_screen.blit(cost_lbl, (rect.right - cost_lbl.get_width() - 15, rect.y + 15))
            else:
                # ─── DRAG & DROP SHOP ────────────────────────────────────────
                # Shared parts catalogue used by both ENGINEERING and WEAPONRY
                all_parts = {
                    # --- ENGINEERING / SHIELD slot ---
                    'shield':           {'name': 'Shield Gen',    'slot': 'SHIELD',  'type': 'ENGINEERING', 'max_level': 4,
                                         'icon_color': (0, 180, 255),
                                         'desc': '+1 Max Shield per rank (up to 4 ranks).',
                                         'cost_func': lambda p: (p.skills['shield'] + 1) * 75,
                                         'scrap_func': lambda p: (p.skills['shield'] + 1) * 1,   'deps': []},
                    'deflector':        {'name': 'Deflector',     'slot': 'SHIELD',  'type': 'ENGINEERING', 'max_level': 1,
                                         'icon_color': (0, 140, 220),
                                         'desc': 'Cuts shield recharge delay from 5 s → 3 s.',
                                         'cost_func': lambda p: 200,
                                         'scrap_func': lambda p: 3,                              'deps': [('shield', 2)]},
                    'emergency_recharge':{'name': 'E-Recharge',   'slot': 'SHIELD',  'type': 'ENGINEERING', 'max_level': 2,
                                         'icon_color': (60, 210, 255),
                                         'desc': 'Restores 50 % of max shield once on depletion.',
                                         'cost_func': lambda p: (p.skills['emergency_recharge'] + 1) * 150,
                                         'scrap_func': lambda p: (p.skills['emergency_recharge'] + 1) * 3, 'deps': [('shield', 2)]},
                    # --- ENGINEERING / CORE slot ---
                    'coolant':          {'name': 'Coolant',       'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 4,
                                         'icon_color': (0, 255, 200),
                                         'desc': '+25 % weapon cool-down rate per rank.',
                                         'cost_func': lambda p: (p.skills['coolant'] + 1) * 60,
                                         'scrap_func': lambda p: (p.skills['coolant'] + 1) * 1, 'deps': []},
                    'nanite_repair':    {'name': 'Nanite Rep',    'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 3,
                                         'icon_color': (0, 255, 150),
                                         'desc': '+0.003 passive shield regen per frame per rank.',
                                         'cost_func': lambda p: (p.skills['nanite_repair'] + 1) * 120,
                                         'scrap_func': lambda p: (p.skills['nanite_repair'] + 1) * 2, 'deps': [('coolant', 1)]},
                    'class_tier1':      {'name': self.player.class_upgrades.get('tier1_name', 'Class Upgrade I'),
                                         'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 3,
                                         'icon_color': (180, 100, 255),
                                         'desc': self.player.class_upgrades.get('tier1_desc', 'Class trait upgrade.'),
                                         'cost_func': lambda p: (p.skills['class_tier1'] + 1) * 120,
                                         'scrap_func': lambda p: (p.skills['class_tier1'] + 1) * 2, 'deps': []},
                    'class_tier2':      {'name': self.player.class_upgrades.get('tier2_name', 'Class Upgrade II'),
                                         'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 2,
                                         'icon_color': (200, 120, 255),
                                         'desc': self.player.class_upgrades.get('tier2_desc', 'Advanced class trait.'),
                                         'cost_func': lambda p: (p.skills['class_tier2'] + 1) * 180,
                                         'scrap_func': lambda p: (p.skills['class_tier2'] + 1) * 3, 'deps': [('class_tier1', 1)]},
                    'class_tier3':      {'name': self.player.class_upgrades.get('tier3_name', 'Class Upgrade III'),
                                         'slot': 'CORE',    'type': 'ENGINEERING', 'max_level': 1,
                                         'icon_color': (230, 150, 255),
                                         'desc': self.player.class_upgrades.get('tier3_desc', 'Elite class specialisation.'),
                                         'cost_func': lambda p: 350,
                                         'scrap_func': lambda p: 5, 'deps': [('class_tier2', 1)]},
                    # --- ENGINEERING / ENGINE slot ---
                    'hyperdrive':       {'name': 'Hyperdrive',    'slot': 'ENGINE',  'type': 'ENGINEERING', 'max_level': 1,
                                         'icon_color': (255, 200, 0),
                                         'desc': 'Reduces warp charge delay 3 s → 1 s.',
                                         'cost_func': lambda p: 350,
                                         'scrap_func': lambda p: 6, 'deps': [('shield', 2), ('coolant', 2)]},
                    'afterburner':      {'name': 'Afterburner',   'slot': 'ENGINE',  'type': 'ENGINEERING', 'max_level': 3,
                                         'icon_color': (255, 140, 0),
                                         'desc': '+20 % dash burst speed per rank.',
                                         'cost_func': lambda p: (p.skills['afterburner'] + 1) * 100,
                                         'scrap_func': lambda p: (p.skills['afterburner'] + 1) * 2, 'deps': []},
                    'vector_nozzle':    {'name': 'Vector Nozzle', 'slot': 'ENGINE',  'type': 'ENGINEERING', 'max_level': 3,
                                         'icon_color': (255, 170, 50),
                                         'desc': '+20 % turn rate per rank.',
                                         'cost_func': lambda p: (p.skills['vector_nozzle'] + 1) * 80,
                                         'scrap_func': lambda p: (p.skills['vector_nozzle'] + 1) * 2, 'deps': []},
                    # --- WEAPONRY / WEAPON slot ---
                    'weapon':           {'name': 'Multi-Cannon',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                         'icon_color': (255, 80, 80),
                                         'desc': 'Unlocks dual Laser fire mode.',
                                         'cost_func': lambda p: 200,
                                         'scrap_func': lambda p: 4, 'deps': []},
                    'overcharge':       {'name': 'Overcharger',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                         'icon_color': (255, 50, 50),
                                         'desc': 'Laser fire-rate -30 % shoot delay.',
                                         'cost_func': lambda p: 250,
                                         'scrap_func': lambda p: 4, 'deps': [('weapon', 1)]},
                    'shotgun_unlocked': {'name': 'Buy Shotgun',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                         'icon_color': (200, 80, 40),
                                         'desc': 'Unlock CQC Scatter Shotgun primary.',
                                         'cost_func': lambda p: 300,
                                         'scrap_func': lambda p: 5, 'deps': []},
                    'shotgun_mod':      {'name': 'Shotgun Tune',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                         'icon_color': (220, 100, 60),
                                         'desc': '+15 % shotgun stats per rank.',
                                         'cost_func': lambda p: (p.skills['shotgun_mod'] + 1) * 100,
                                         'scrap_func': lambda p: (p.skills['shotgun_mod'] + 1) * 2, 'deps': [('shotgun_unlocked', 1)]},
                    'railgun_unlocked': {'name': 'Buy Railgun',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                         'icon_color': (160, 60, 200),
                                         'desc': 'Unlock Tachyonic Railgun primary.',
                                         'cost_func': lambda p: 500,
                                         'scrap_func': lambda p: 10, 'deps': []},
                    'railgun_mod':      {'name': 'Railgun Tune',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                         'icon_color': (180, 80, 220),
                                         'desc': 'Reduce charge delay & boost projectile velocity.',
                                         'cost_func': lambda p: (p.skills['railgun_mod'] + 1) * 150,
                                         'scrap_func': lambda p: (p.skills['railgun_mod'] + 1) * 4, 'deps': [('railgun_unlocked', 1)]},
                    'torpedo':          {'name': 'Fusion Torpedo', 'slot': 'WEAPON', 'type': 'WEAPONRY',    'max_level': 4,
                                         'icon_color': (255, 200, 0),
                                         'desc': '-15 % cooldown, +15 % blast radius per rank.',
                                         'cost_func': lambda p: (p.skills['torpedo'] + 1) * 80,
                                         'scrap_func': lambda p: (p.skills['torpedo'] + 1) * 1, 'deps': []},
                    'cluster_torpedo':  {'name': 'Cluster War',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                         'icon_color': (255, 220, 30),
                                         'desc': 'Torpedo spawns 3 secondary blasts on impact.',
                                         'cost_func': lambda p: 300,
                                         'scrap_func': lambda p: 5, 'deps': [('torpedo', 2)]},
                    'bomb_unlocked':    {'name': 'Buy Prox Bomb', 'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                         'icon_color': (200, 120, 0),
                                         'desc': 'Unlock Proximity-fused Detonation Bomb.',
                                         'cost_func': lambda p: 200,
                                         'scrap_func': lambda p: 3, 'deps': []},
                    'bomb_cap':         {'name': 'Bomb Payload',  'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                         'icon_color': (220, 140, 20),
                                         'desc': '+1 max bomb cap & larger blast radius per rank.',
                                         'cost_func': lambda p: (p.skills['bomb_cap'] + 1) * 80,
                                         'scrap_func': lambda p: (p.skills['bomb_cap'] + 1) * 2, 'deps': [('bomb_unlocked', 1)]},
                    'missile_unlocked': {'name': 'Buy Missile',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 1,
                                         'icon_color': (100, 200, 80),
                                         'desc': 'Unlock Smart-Targeting Homing Missile.',
                                         'cost_func': lambda p: 400,
                                         'scrap_func': lambda p: 7, 'deps': []},
                    'missile_cap':      {'name': 'Missile Pay',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                         'icon_color': (120, 220, 100),
                                         'desc': '+1 max missile cap & +20 % flight speed per rank.',
                                         'cost_func': lambda p: (p.skills['missile_cap'] + 1) * 120,
                                         'scrap_func': lambda p: (p.skills['missile_cap'] + 1) * 3, 'deps': [('missile_unlocked', 1)]},
                    'ammo_loader':      {'name': 'Ammo Loader',   'slot': 'WEAPON',  'type': 'WEAPONRY',    'max_level': 3,
                                         'icon_color': (80, 220, 180),
                                         'desc': '+2 max ammo cap for all secondary weapons per rank.',
                                         'cost_func': lambda p: (p.skills['ammo_loader'] + 1) * 100,
                                         'scrap_func': lambda p: (p.skills['ammo_loader'] + 1) * 2, 'deps': []},
                }

                coords = {
                    'shield': (0, 0, 'SHIELD'), 'deflector': (0, 1, 'SHIELD'), 'emergency_recharge': (0, 2, 'SHIELD'),
                    'coolant': (1, 0, 'CORE'), 'nanite_repair': (1, 1, 'CORE'),
                    'class_tier1': (2, 0, 'CORE'), 'class_tier2': (2, 1, 'CORE'), 'class_tier3': (2, 2, 'CORE'),
                    'afterburner': (3, 0, 'ENGINE'), 'vector_nozzle': (3, 1, 'ENGINE'), 'hyperdrive': (3, 2, 'ENGINE'),
                    
                    'weapon': (0, 0, 'PRIMARY'), 'overcharge': (0, 1, 'PRIMARY'), 'ammo_loader': (0, 2, 'SECONDARY'),
                    'shotgun_unlocked': (1, 0, 'PRIMARY'), 'shotgun_mod': (1, 1, 'PRIMARY'), 'bomb_unlocked': (1, 2, 'SECONDARY'), 'bomb_cap': (1, 3, 'SECONDARY'),
                    'railgun_unlocked': (2, 0, 'PRIMARY'), 'railgun_mod': (2, 1, 'PRIMARY'), 'missile_unlocked': (2, 2, 'SECONDARY'), 'missile_cap': (2, 3, 'SECONDARY'),
                    'torpedo': (3, 0, 'SECONDARY'), 'cluster_torpedo': (3, 1, 'SECONDARY')
                }
                for k, (c, r, s) in coords.items():
                    if k in all_parts:
                        all_parts[k]['col'] = c
                        all_parts[k]['row'] = r
                        all_parts[k]['slot'] = s

                # title + wallet
                title_text = "ZENITH UPGRADE PROTOCOL" if self.hub_station_active == 'ENGINEERING' else "ZENITH ARMAMENT MATRIX"
                tree_title = self.large_font.render(title_text, True, CYAN)
                self.virtual_screen.blit(tree_title, (10, 100))
                
                sub_text = "SYSTEM INTEGRATION MATRIX" if self.hub_station_active == 'ENGINEERING' else "TACTICAL WEAPON ASSEMBLY"
                tree_sub = self.small_font.render(sub_text, True, (160, 190, 220))
                self.virtual_screen.blit(tree_sub, (15, 142))
                
                wallet_c = self.small_font.render(f"Credits: {self.player.credits}", True, GREEN)
                wallet_s = self.small_font.render(f"  | Scrap: {self.player.scraps}", True, GOLD)
                self.virtual_screen.blit(wallet_c, (400, 142))
                self.virtual_screen.blit(wallet_s, (400 + wallet_c.get_width(), 142))

                # ── Slot colours & labels ──────────────────────────────────
                slot_meta = {
                    'ENGINE': {'cx': 1000, 'cy': 310, 'col': (255, 140, 0),  'label': 'ENGINE'},
                    'SHIELD': {'cx': 870,  'cy': 480, 'col': (0, 180, 255),  'label': 'SHIELD'},
                    'CORE':   {'cx': 1000, 'cy': 480, 'col': (0, 255, 180),  'label': 'CORE'},
                    'PRIMARY': {'cx': 1130, 'cy': 410, 'col': (255, 80, 80),  'label': 'PRIMARY WP'},
                    'SECONDARY': {'cx': 1130, 'cy': 550, 'col': (255, 200, 0),  'label': 'SECONDARY WP'},
                }

                # ── SHELF PANEL (left / centre-left) ──────────────────────
                shelf_panel = pygame.Rect(5, 175, 595, 700)
                pygame.draw.rect(self.virtual_screen, (14, 18, 28), shelf_panel, border_radius=8)
                pygame.draw.rect(self.virtual_screen, (40, 50, 70), shelf_panel, width=1, border_radius=8)

                shelf_lbl = self.small_font.render("◀  PARTS SHELF — drag a part onto the ship blueprint slot  ▶", True, (120, 160, 200))
                self.virtual_screen.blit(shelf_lbl, (shelf_panel.x + 10, shelf_panel.y + 8))

                active_parts = [k for k, v in all_parts.items() if v['type'] == self.hub_station_active]

                CARD_W, CARD_H = 140, 78
                CARD_PAD_X, CARD_PAD_Y = 6, 6
                shelf_origin_x = shelf_panel.x + 8
                shelf_origin_y = shelf_panel.y + 30

                # Store card rects for hover tooltip detection
                hovered_key = None

                # Draw tree connection lines first so they are behind cards
                for key in active_parts:
                    part = all_parts[key]
                    cx = shelf_origin_x + part['col'] * (CARD_W + CARD_PAD_X)
                    cy = shelf_origin_y + part['row'] * (CARD_H + CARD_PAD_Y)
                    for dep_key, req_lvl in part['deps']:
                        if dep_key in all_parts:
                            dep_part = all_parts[dep_key]
                            if dep_part['type'] == self.hub_station_active:
                                dcx = shelf_origin_x + dep_part['col'] * (CARD_W + CARD_PAD_X)
                                dcy = shelf_origin_y + dep_part['row'] * (CARD_H + CARD_PAD_Y)
                                start_pt = (dcx + CARD_W // 2, dcy + CARD_H)
                                end_pt = (cx + CARD_W // 2, cy)
                                line_col = CYAN if self.player.skills.get(dep_key, 0) >= req_lvl else (60, 60, 70)
                                mid_y = (start_pt[1] + end_pt[1]) // 2
                                pygame.draw.lines(self.virtual_screen, line_col, False, [
                                    start_pt,
                                    (start_pt[0], mid_y),
                                    (end_pt[0], mid_y),
                                    end_pt
                                ], 2)

                for idx, key in enumerate(active_parts):
                    part = all_parts[key]
                    col = part['col']
                    row = part['row']
                    cx = shelf_origin_x + col * (CARD_W + CARD_PAD_X)
                    cy = shelf_origin_y + row * (CARD_H + CARD_PAD_Y)
                    card_rect = pygame.Rect(cx, cy, CARD_W, CARD_H)

                    curr_lvl = self.player.skills.get(key, 0)
                    max_lvl  = part['max_level']
                    is_maxed = curr_lvl >= max_lvl

                    # Dep check
                    unlocked = all(self.player.skills.get(dk, 0) >= dv for dk, dv in part['deps'])

                    # Can afford?
                    cost_c  = part['cost_func'](self.player)
                    cost_s  = part['scrap_func'](self.player)

                    # being dragged?
                    is_dragging = (self.dragged_part_key == key and self.dragged_origin == 'SHELF')

                    hovered = card_rect.collidepoint(vmx, vmy)
                    if hovered:
                        hovered_key = key

                    # Card BG
                    if is_dragging:
                        bg = (20, 40, 60)
                        border = CYAN
                        bw = 2
                    elif is_maxed:
                        bg = (15, 35, 15)
                        border = GREEN
                        bw = 2
                    elif not unlocked:
                        bg = (30, 15, 15)
                        border = (150, 40, 40)
                        bw = 1
                    elif hovered:
                        bg = (30, 40, 60)
                        border = CYAN
                        bw = 2
                    else:
                        bg = (18, 22, 34)
                        border = (60, 70, 90)
                        bw = 1

                    pygame.draw.rect(self.virtual_screen, bg,     card_rect, border_radius=5)
                    if hovered and unlocked and not is_maxed:
                        scan_y = card_rect.y + int((ticks * 0.08) % card_rect.height)
                        pygame.draw.line(self.virtual_screen, (0, 150, 180), (card_rect.x + 2, scan_y), (card_rect.right - 2, scan_y), 1)
                    pygame.draw.rect(self.virtual_screen, border, card_rect, width=bw, border_radius=5)

                    # Part icon (coloured hex shape with custom vector)
                    ico_x = cx + 10
                    ico_y = cy + 12
                    ico_col = part['icon_color'] if unlocked else (80, 80, 80)
                    if is_maxed:
                        ico_col = GREEN
                    self.draw_part_icon(self.virtual_screen, ico_x + 12, ico_y + 12, key, ico_col, ticks)

                    # Part name
                    name_surf = render_fit_text(part['name'], WHITE if unlocked else (150, 100, 100), CARD_W - 44, base_font_size=13)
                    self.virtual_screen.blit(name_surf, (cx + 36, cy + 8))

                    # Rank dots
                    for d in range(max_lvl):
                        dot_col = ico_col if d < curr_lvl else (50, 50, 60)
                        pygame.draw.circle(self.virtual_screen, dot_col, (cx + 36 + d * 14, cy + 32), 5)
                        pygame.draw.circle(self.virtual_screen, WHITE,   (cx + 36 + d * 14, cy + 32), 5, 1)

                    # Status line
                    if is_maxed:
                        status_surf = render_fit_text("✓ MAXED", GREEN, CARD_W - 12, base_font_size=11)
                        self.virtual_screen.blit(status_surf, (cx + 6, cy + 54))
                    elif not unlocked:
                        status_surf = render_fit_text("🔒 LOCKED", RED, CARD_W - 12, base_font_size=11)
                        self.virtual_screen.blit(status_surf, (cx + 6, cy + 54))
                    else:
                        cc = GREEN if self.player.credits >= cost_c else (200, 80, 80)
                        sc = GOLD  if self.player.scraps  >= cost_s  else (200, 80, 80)
                        c_surf = render_fit_text(f"{cost_c}c", cc, 55, base_font_size=11)
                        s_surf = render_fit_text(f"{cost_s}sc", sc, 55, base_font_size=11)
                        self.virtual_screen.blit(c_surf, (cx + 6,  cy + 54))
                        self.virtual_screen.blit(s_surf, (cx + 68, cy + 54))



                # ── RIGHT PANEL: SHIP BLUEPRINT ───────────────────────────
                bp_panel = pygame.Rect(625, 175, 575, 700)
                pygame.draw.rect(self.virtual_screen, (10, 14, 24), bp_panel, border_radius=8)
                pygame.draw.rect(self.virtual_screen, (30, 50, 80), bp_panel, width=1, border_radius=8)

                bp_title = self.font.render("SHIP BLUEPRINT", True, (60, 100, 160))
                self.virtual_screen.blit(bp_title, (bp_panel.x + 10, bp_panel.y + 8))

                # Draw cyan vector ship outline centred in blueprint panel
                bp_cx = 1000
                bp_cy = 450
                T = pygame.time.get_ticks()

                def _bp_line(a, b, col=(30, 70, 120), w=1):
                    pygame.draw.line(self.virtual_screen, col,
                                     (int(bp_cx + a[0]), int(bp_cy + a[1])),
                                     (int(bp_cx + b[0]), int(bp_cy + b[1])), w)

                # Hull
                _bp_line(( 0, -130), (-55,  20), (40, 100, 160), 2)
                _bp_line(( 0, -130), ( 55,  20), (40, 100, 160), 2)
                _bp_line((-55,  20), (  0,  40), (40, 100, 160), 2)
                _bp_line(( 55,  20), (  0,  40), (40, 100, 160), 2)
                # Cockpit
                _bp_line(( 0, -130), (-15, -80), (60, 140, 200))
                _bp_line(( 0, -130), ( 15, -80), (60, 140, 200))
                _bp_line((-15, -80), ( 15, -80), (60, 140, 200))
                # Wings
                _bp_line((-55,  20), (-120, 60), (30, 80, 130), 2)
                _bp_line((-120, 60), ( -80, 80), (30, 80, 130), 2)
                _bp_line(( -80, 80), ( -40, 50), (30, 80, 130), 2)
                _bp_line(( 55,  20), ( 120, 60), (30, 80, 130), 2)
                _bp_line(( 120, 60), (  80, 80), (30, 80, 130), 2)
                _bp_line((  80, 80), (  40, 50), (30, 80, 130), 2)
                # Engine nozzles
                _bp_line((-25,  40), (-30,  80), (50, 80, 120))
                _bp_line(( 25,  40), ( 30,  80), (50, 80, 120))
                _bp_line((-30,  80), ( 30,  80), (50, 80, 120))
                # Center spine
                _bp_line((0, -80), (0, 40), (20, 60, 100))
                # Grid dots
                for gx in range(-80, 81, 40):
                    for gy in range(-100, 101, 40):
                        pygame.draw.circle(self.virtual_screen, (20, 35, 55), (bp_cx + gx, bp_cy + gy), 1)

                # ── Slot circles ──────────────────────────────────────────
                for slot_name, sm in slot_meta.items():
                    scx, scy = sm['cx'], sm['cy']
                    s_col = sm['col']

                    # Check if parts in this slot installed
                    if slot_name == 'PRIMARY':
                        eq_map = {0: 'weapon', 1: 'shotgun_unlocked', 2: 'railgun_unlocked'}
                        eq_key = eq_map.get(self.player.active_primary)
                        installed = [eq_key] if (eq_key and self.player.skills.get(eq_key, 0) > 0) else []
                    elif slot_name == 'SECONDARY':
                        eq_map = {0: 'torpedo', 1: 'bomb_unlocked', 2: 'missile_unlocked'}
                        eq_key = eq_map.get(self.player.active_secondary)
                        installed = [eq_key] if (eq_key and self.player.skills.get(eq_key, 0) > 0) else []
                    elif slot_name == 'SHIELD':
                        eq_key = self.player.equipped_shield
                        installed = [eq_key] if (eq_key and self.player.skills.get(eq_key, 0) > 0) else []
                    elif slot_name == 'CORE':
                        eq_key = self.player.equipped_core
                        installed = [eq_key] if (eq_key and self.player.skills.get(eq_key, 0) > 0) else []
                    elif slot_name == 'ENGINE':
                        eq_key = self.player.equipped_engine
                        installed = [eq_key] if (eq_key and self.player.skills.get(eq_key, 0) > 0) else []
                    else:
                        installed = [k for k, v in all_parts.items() if v['slot'] == slot_name and self.player.skills.get(k, 0) > 0]

                    is_target = (self.dragged_part_key is not None and
                                 all_parts.get(self.dragged_part_key, {}).get('slot') == slot_name and
                                 self.dragged_origin == 'SHELF')

                    pulse = 0.5 + 0.5 * math.sin(T * 0.004)
                    ring_r = 32 if not is_target else 36

                    if is_target:
                        # Green glow ring when dragging valid part over its slot
                        dist_to_slot = math.hypot(vmx - scx, vmy - scy)
                        is_hovering_slot = (dist_to_slot < 45)
                        ring_col = GREEN if is_hovering_slot else CYAN
                        ring_w = 4 if is_hovering_slot else 2
                        pygame.draw.circle(self.virtual_screen, ring_col, (scx, scy), ring_r, ring_w)
                        # Draw rotating outer dotted locking rings
                        for a in range(8):
                            ang = math.radians(a * 45 + ticks * 0.05)
                            ox = scx + int((ring_r + 6) * math.cos(ang))
                            oy = scy + int((ring_r + 6) * math.sin(ang))
                            pygame.draw.circle(self.virtual_screen, ring_col, (ox, oy), 2)
                        # inner fill flash
                        flash_surf = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
                        flash_surf.fill((0, 0, 0, 0))
                        pygame.draw.circle(flash_surf, (*ring_col, int(60 * pulse)), (ring_r, ring_r), ring_r - 3)
                        self.virtual_screen.blit(flash_surf, (scx - ring_r, scy - ring_r))
                        
                        if is_hovering_slot:
                            # Highly visible drop indicator overlay
                            drop_lbl = self.small_font.render("DROP TO INSTALL", True, GREEN)
                            self.virtual_screen.blit(drop_lbl, (scx - drop_lbl.get_width() // 2, scy - ring_r - 18))
                    elif installed:
                        # Draw high-tech slot box
                        pygame.draw.circle(self.virtual_screen, s_col, (scx, scy), ring_r, 2)
                        
                        # Draw rotating nested pattern
                        for r_offset in range(3):
                            o_ang = ticks * 0.003 + r_offset * (2 * math.pi / 3)
                            ox = scx + int(ring_r * 0.8 * math.cos(o_ang))
                            oy = scy + int(ring_r * 0.8 * math.sin(o_ang))
                            pygame.draw.circle(self.virtual_screen, s_col, (ox, oy), 3)
                            
                        # Draw slot-specific glowing graphics
                        ticks = pygame.time.get_ticks()
                        if slot_name == 'PRIMARY':
                            # Draw primary double gun barrel design
                            pygame.draw.line(self.virtual_screen, WHITE, (scx - 4, scy - 12), (scx - 4, scy + 8), 2)
                            pygame.draw.line(self.virtual_screen, WHITE, (scx + 4, scy - 12), (scx + 4, scy + 8), 2)
                            pygame.draw.rect(self.virtual_screen, s_col, (scx - 8, scy + 8, 16, 6))
                        elif slot_name == 'SECONDARY':
                            # Draw rocket / missile outline
                            pygame.draw.polygon(self.virtual_screen, WHITE, [(scx, scy - 12), (scx - 6, scy + 2), (scx + 6, scy + 2)])
                            pygame.draw.rect(self.virtual_screen, s_col, (scx - 4, scy + 2, 8, 8))
                            pygame.draw.line(self.virtual_screen, RED, (scx, scy + 10), (scx, scy + 14), 2)
                        elif slot_name == 'SHIELD':
                            # Hexagon shield dome
                            pts = []
                            for a in range(6):
                                ang = math.radians(a * 60 + ticks * 0.02)
                                pts.append((scx + 12 * math.cos(ang), scy + 12 * math.sin(ang)))
                            pygame.draw.polygon(self.virtual_screen, s_col, pts, 1)
                            pygame.draw.circle(self.virtual_screen, WHITE, (scx, scy), 4)
                        elif slot_name == 'CORE':
                            # Microchip/nuclear core
                            pygame.draw.rect(self.virtual_screen, s_col, (scx - 10, scy - 10, 20, 20), width=1)
                            pygame.draw.circle(self.virtual_screen, WHITE, (scx, scy), 6 + int(2 * math.sin(ticks * 0.05)))
                        elif slot_name == 'ENGINE':
                            # Thruster nozzle with fire
                            pygame.draw.polygon(self.virtual_screen, s_col, [(scx - 8, scy - 8), (scx + 8, scy - 8), (scx + 4, scy + 6), (scx - 4, scy + 6)])
                            pygame.draw.circle(self.virtual_screen, ORANGE, (scx, scy + 10), 4 + int(2 * math.sin(ticks * 0.08)))
                    else:
                        pygame.draw.circle(self.virtual_screen, (50, 60, 80), (scx, scy), ring_r, 1)

                    # Slot label
                    slot_tag_surf = render_fit_text(sm['label'], s_col if installed else (80, 100, 120), 80, base_font_size=11)
                    self.virtual_screen.blit(slot_tag_surf, (scx - slot_tag_surf.get_width() // 2, scy + ring_r + 4))

                    # Installed part names stacked
                    for ii, ik in enumerate(installed):
                        ivl = self.player.skills.get(ik, 0)
                        iname = all_parts[ik]['name']
                        i_col = all_parts[ik]['icon_color']
                        ip_surf = render_fit_text(f"▪ {iname} Lv{ivl}", i_col, 120, base_font_size=9)
                        self.virtual_screen.blit(ip_surf, (scx - ip_surf.get_width() // 2, scy - ring_r - 16 - ii * 14))

                # ── RECYCLING BIN ─────────────────────────────────────────
                bin_rect = pygame.Rect(640, 580, 150, 70)
                bin_hov  = bin_rect.collidepoint(vmx, vmy)
                bin_glow = self.dragged_part_key is not None and self.dragged_origin in ('SHIP_SLOT', 'OWNED_WEAPONS')
                bin_bg   = (70, 30, 30) if (bin_glow and bin_hov) else ((50, 20, 20) if bin_glow else (20, 20, 25))
                bin_brd  = (255, 120, 60) if (bin_glow and bin_hov) else ((220, 80, 30) if bin_glow else (100, 60, 40))
                pygame.draw.rect(self.virtual_screen, bin_bg,  bin_rect, border_radius=6)
                pygame.draw.rect(self.virtual_screen, bin_brd, bin_rect, width=2, border_radius=6)

                # Bin icon
                bx, by = bin_rect.x + 12, bin_rect.y + 10
                pygame.draw.rect(self.virtual_screen, bin_brd, (bx, by + 6, 26, 22))           # body
                pygame.draw.rect(self.virtual_screen, bin_brd, (bx + 4, by, 18, 5))             # lid
                for sl in range(3):                                                              # bin lines
                    pygame.draw.line(self.virtual_screen, (180, 90, 60), (bx + 5 + sl * 8, by + 9), (bx + 5 + sl * 8, by + 25), 1)

                bin_lbl1 = render_fit_text("RECYCLE BIN", (220, 110, 60), 95, base_font_size=11)
                bin_lbl2 = render_fit_text("Drop here to sell", (160, 100, 60), 95, base_font_size=9)
                self.virtual_screen.blit(bin_lbl1, (bx + 32, by + 3))
                self.virtual_screen.blit(bin_lbl2, (bx + 32, by + 22))

                # ── OWNED PARTS / WEAPONS INVENTORY (BOTTOM OF BLUEPRINT) ─────────
                if self.hub_station_active in ('WEAPONRY', 'ENGINEERING'):
                    sep_y = 650
                    pygame.draw.line(self.virtual_screen, (40, 50, 70), (bp_panel.x + 10, sep_y), (bp_panel.x + bp_panel.width - 10, sep_y), 1)
                    
                    inv_title = "OWNED WEAPONS INVENTORY" if self.hub_station_active == 'WEAPONRY' else "OWNED UPGRADES INVENTORY"
                    inv_lbl = self.font.render(inv_title, True, CYAN)
                    self.virtual_screen.blit(inv_lbl, (bp_panel.x + 15, sep_y + 10))
                    inv_sub = self.small_font.render("Drag to RECYCLE BIN to sell / refund", True, (120, 160, 200))
                    self.virtual_screen.blit(inv_sub, (bp_panel.x + 15, sep_y + 35))
                    
                    if self.hub_station_active == 'WEAPONRY':
                        weapon_keys = ['weapon', 'shotgun_unlocked', 'railgun_unlocked', 'torpedo', 'bomb_unlocked', 'missile_unlocked']
                        equipped_keys = []
                        eq_p = {0: 'weapon', 1: 'shotgun_unlocked', 2: 'railgun_unlocked'}.get(self.player.active_primary)
                        if eq_p and self.player.skills.get(eq_p, 0) > 0:
                            equipped_keys.append(eq_p)
                        eq_s = {0: 'torpedo', 1: 'bomb_unlocked', 2: 'missile_unlocked'}.get(self.player.active_secondary)
                        if eq_s and self.player.skills.get(eq_s, 0) > 0:
                            equipped_keys.append(eq_s)
                        owned_items = [k for k in weapon_keys if self.player.skills.get(k, 0) > 0 and k not in equipped_keys]
                        inv_origin_type = 'OWNED_WEAPONS'
                        inv_origin_x = bp_panel.x + 15
                        cols_num = 3
                    else:
                        item_keys = ['shield', 'deflector', 'emergency_recharge', 'coolant', 'nanite_repair', 'class_tier1', 'class_tier2', 'class_tier3', 'afterburner', 'vector_nozzle', 'hyperdrive']
                        equipped_keys = [self.player.equipped_shield, self.player.equipped_core, self.player.equipped_engine]
                        owned_items = [k for k in item_keys if self.player.skills.get(k, 0) > 0 and k not in equipped_keys]
                        inv_origin_type = 'OWNED_ITEMS'
                        inv_origin_x = 820 # Bottom-right alignment
                        cols_num = 2
                    
                    inv_origin_y = sep_y + 60
                    INV_CARD_W, INV_CARD_H = 170, 70
                    INV_PAD_X, INV_PAD_Y = 10, 10
                    
                    for idx, key in enumerate(owned_items):
                        col = idx % cols_num
                        row = idx // cols_num
                        cx = inv_origin_x + col * (INV_CARD_W + INV_PAD_X)
                        cy = inv_origin_y + row * (INV_CARD_H + INV_PAD_Y)
                        
                        card_rect = pygame.Rect(cx, cy, INV_CARD_W, INV_CARD_H)
                        part = all_parts[key]
                        
                        is_dragging = (self.dragged_part_key == key and self.dragged_origin == inv_origin_type)
                        hovered = card_rect.collidepoint(vmx, vmy)
                        if hovered and not self.dragged_part_key:
                            hovered_key = key
                            
                        bg = (24, 28, 40)
                        border = CYAN if hovered or is_dragging else (60, 70, 90)
                        bw = 2 if (hovered or is_dragging) else 1
                        
                        pygame.draw.rect(self.virtual_screen, bg, card_rect, border_radius=5)
                        pygame.draw.rect(self.virtual_screen, border, card_rect, width=bw, border_radius=5)
                        
                        ico_x = cx + 8
                        ico_y = cy + 8
                        ico_col = part['icon_color']
                        self.draw_part_icon(self.virtual_screen, ico_x + 12, ico_y + 12, key, ico_col, ticks)
                        
                        name_surf = render_fit_text(part['name'], WHITE, INV_CARD_W - 36, base_font_size=12)
                        self.virtual_screen.blit(name_surf, (cx + 34, cy + 6))
                        
                        lvl_surf = self.small_font.render(f"Lvl {self.player.skills[key]}", True, YELLOW)
                        self.virtual_screen.blit(lvl_surf, (cx + 34, cy + 24))
                        
                        drag_info = self.small_font.render("DRAG TO SELL", True, (160, 100, 60))
                        self.virtual_screen.blit(drag_info, (cx + 34, cy + 42))

                # ── Tooltip strip at bottom of left shelf panel ─────────────────────
                tip_rect = pygame.Rect(10, 780, 585, 85)
                pygame.draw.rect(self.virtual_screen, (10, 14, 24), tip_rect, border_radius=6)
                pygame.draw.rect(self.virtual_screen, (30, 50, 80), tip_rect, width=1, border_radius=6)
                if hovered_key:
                    hv = all_parts[hovered_key]
                    tip_name = self.font.render(hv['name'].upper(), True, hv['icon_color'])
                    self.virtual_screen.blit(tip_name, (20, 785))
                    words = hv['desc'].split()
                    line, lines = '', []
                    for w in words:
                        if len(line + w) < 70: line += w + ' '
                        else: lines.append(line.strip()); line = w + ' '
                    lines.append(line.strip())
                    for li, ln in enumerate(lines[:3]):
                        self.virtual_screen.blit(self.small_font.render(ln, True, WHITE), (20, 807 + li * 16))
                    slot_col = slot_meta.get(hv['slot'], {}).get('col', WHITE)
                    sl_lbl = self.small_font.render(f"Slot: {hv['slot']}", True, slot_col)
                    self.virtual_screen.blit(sl_lbl, (480, 785))
                    dep_names = []
                    for dk, dv in hv['deps']:
                        dep_part = all_parts.get(dk)
                        dep_name = dep_part['name'] if dep_part else dk
                        dep_names.append(f"{dep_name} Lv{dv}")
                    dep_text = "Reqs: " + (", ".join(dep_names) if dep_names else "None")
                    dep_col_list = [GREEN if self.player.skills.get(dk, 0) >= dv else RED for dk, dv in hv['deps']]
                    dep_col = GREEN if all(self.player.skills.get(dk, 0) >= dv for dk, dv in hv['deps']) else RED
                    dep_surf = self.small_font.render(dep_text, True, dep_col)
                    self.virtual_screen.blit(dep_surf, (480, 803))
                else:
                    help_surf = self.small_font.render("Hover a shelf card to inspect  |  Drag → slot to install  |  Drag installed → Bin to recycle", True, (70, 90, 120))
                    self.virtual_screen.blit(help_surf, (20, 812))

                # ── GHOST drag rendering ────────────────────────────────────
                if self.dragged_part_key is not None:
                    dp = all_parts.get(self.dragged_part_key)
                    if dp:
                        # Draw dotted connector line
                        start_pos = (getattr(self, 'drag_start_x', vmx), getattr(self, 'drag_start_y', vmy))
                        end_pos = (vmx, vmy)
                        dx = end_pos[0] - start_pos[0]
                        dy = end_pos[1] - start_pos[1]
                        dist = math.hypot(dx, dy)
                        if dist > 0:
                            num_dots = int(dist / 10)
                            for d_idx in range(num_dots):
                                t_val = d_idx / num_dots
                                px = start_pos[0] + dx * t_val
                                py = start_pos[1] + dy * t_val
                                pygame.draw.circle(self.virtual_screen, (0, 255, 255), (int(px), int(py)), 2)
                                
                        gx = int(vmx - 50)
                        gy = int(vmy - 35)
                        ghost = pygame.Surface((100, 70), pygame.SRCALPHA)
                        ghost.fill((0, 0, 0, 0))
                        pygame.draw.rect(ghost, (*dp['icon_color'], 160), (0, 0, 100, 70), border_radius=6)
                        pygame.draw.rect(ghost, (*WHITE, 200),            (0, 0, 100, 70), width=2, border_radius=6)
                        g_lbl = render_fit_text(dp['name'], WHITE, 90, base_font_size=12)
                        ghost.blit(g_lbl, (5, 10))
                        lvl_text = f"Lv {self.player.skills.get(self.dragged_part_key, 0)} → {self.player.skills.get(self.dragged_part_key, 0) + 1}"
                        g_sub = render_fit_text(lvl_text if self.dragged_origin == 'SHELF' else "↩ RECYCLE", YELLOW, 90, base_font_size=10)
                        ghost.blit(g_sub, (5, 45))
                        self.virtual_screen.blit(ghost, (gx, gy))
                
                if hovered_key != getattr(self, 'last_hovered_key', None):
                    self.last_hovered_key = hovered_key
                    if hovered_key and SOUNDS:
                        SOUNDS.play('tick')


        # Game Over Overlay
        elif self.state == 'GAME_OVER':
            go_time = pygame.time.get_ticks() - getattr(self, 'game_over_start_time', 0)
            
            # Darkening overlay
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            alpha = min(220, int(go_time / 10))
            overlay.fill((10, 0, 0, alpha))
            self.virtual_screen.blit(overlay, (0, 0))
            
            if go_time > 1000:
                msg_y = VIRTUAL_HEIGHT // 2 - 150
                msg = self.large_font.render("SIGNAL LOST", True, RED)
                
                # Glitch effect for text
                if random.random() < 0.15:
                    glitch_offset = random.randint(-15, 15)
                    msg_rect = msg.get_rect(center=(VIRTUAL_WIDTH // 2 + glitch_offset, msg_y))
                else:
                    msg_rect = msg.get_rect(center=(VIRTUAL_WIDTH // 2, msg_y))
                
                self.virtual_screen.blit(msg, msg_rect)
                
                # Floating debris/embers
                ship_x, ship_y = VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2
                for i in range(20):
                    dx = ship_x + math.sin(go_time * 0.001 + i) * (go_time * 0.05 + 80)
                    dy = ship_y + math.cos(go_time * 0.0015 + i) * (go_time * 0.05 + 80)
                    pygame.draw.circle(self.virtual_screen, (150, 40, 40), (int(dx), int(dy)), 2 + i % 3)
                
                # Draw shattered/dead ship silhouette rotating slowly
                self._draw_cinematic_ship(self.virtual_screen, ship_x, ship_y, 0, 1, scale=1.5, damaged=True, thruster_intensity=0.0, rotation_angle=int(go_time*0.02))
            
            if go_time > 3000:
                prompt_alpha = min(255, int((go_time - 3000) / 4))
                
                retry_msg = self.font.render("[ R ] REBOOT SYSTEM", True, WHITE)
                retry_msg.set_alpha(prompt_alpha)
                retry_rect = retry_msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 120))
                self.virtual_screen.blit(retry_msg, retry_rect)
                
                menu_msg = self.font.render("[ M ] MAIN MENU", True, CYAN)
                menu_msg.set_alpha(prompt_alpha)
                menu_rect = menu_msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 180))
                self.virtual_screen.blit(menu_msg, menu_rect)
        # Victory Overlay
        elif self.state == 'VICTORY':
            v_time = current_time - self.victory_start_time
            
            def draw_first_person_cockpit(screen, state_phase):
                # 1. Dashboard console panel at the bottom
                pygame.draw.rect(screen, (15, 18, 22), (0, VIRTUAL_HEIGHT - 180, VIRTUAL_WIDTH, 180))
                pygame.draw.line(screen, (30, 36, 44), (0, VIRTUAL_HEIGHT - 180), (VIRTUAL_WIDTH, VIRTUAL_HEIGHT - 180), width=4)
                
                # 2. Diagonal support canopy struts
                pygame.draw.polygon(screen, (25, 30, 35), [(0, 0), (60, 0), (180, VIRTUAL_HEIGHT - 180), (0, VIRTUAL_HEIGHT - 180)])
                pygame.draw.polygon(screen, (25, 30, 35), [(VIRTUAL_WIDTH, 0), (VIRTUAL_WIDTH - 60, 0), (VIRTUAL_WIDTH - 180, VIRTUAL_HEIGHT - 180), (VIRTUAL_WIDTH, VIRTUAL_HEIGHT - 180)])
                
                pygame.draw.line(screen, (50, 60, 70), (60, 0), (180, VIRTUAL_HEIGHT - 180), width=2)
                pygame.draw.line(screen, (50, 60, 70), (VIRTUAL_WIDTH - 60, 0), (VIRTUAL_WIDTH - 180, VIRTUAL_HEIGHT - 180), width=2)
                
                # 3. Radar sphere/Compass display
                radar_cx, radar_cy = VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 90
                pygame.draw.circle(screen, (8, 24, 16), (radar_cx, radar_cy), 65)
                pygame.draw.circle(screen, GREEN if state_phase < 4 else (100, 20, 20), (radar_cx, radar_cy), 65, width=2)
                pygame.draw.circle(screen, GREEN if state_phase < 4 else (80, 20, 20), (radar_cx, radar_cy), 30, width=1)
                pygame.draw.line(screen, GREEN if state_phase < 4 else (80, 20, 20), (radar_cx - 65, radar_cy), (radar_cx + 65, radar_cy), width=1)
                pygame.draw.line(screen, GREEN if state_phase < 4 else (80, 20, 20), (radar_cx, radar_cy - 65), (radar_cx, radar_cy + 65), width=1)
                
                ticks = pygame.time.get_ticks()
                if state_phase < 4:
                    sweep_ang = ticks * 0.003
                    sweep_x = radar_cx + int(63 * math.cos(sweep_ang))
                    sweep_y = radar_cy + int(63 * math.sin(sweep_ang))
                    pygame.draw.line(screen, (0, 255, 100, 150), (radar_cx, radar_cy), (sweep_x, sweep_y), width=2)
                
                # 4. Diagnostic gauges
                # Left gauge: Portal Charge
                pygame.draw.rect(screen, (10, 12, 15), (260, VIRTUAL_HEIGHT - 130, 120, 25))
                if state_phase == 1:
                    gauge_w = int(120 * (0.8 + 0.1 * math.sin(ticks * 0.002)))
                    gauge_color = GREEN
                elif state_phase == 2:
                    gauge_w = int(120 * (0.4 + 0.15 * math.sin(ticks * 0.01)))
                    gauge_color = RED
                elif state_phase == 3:
                    gauge_w = int(120 * (0.05 + 0.05 * random.random()))
                    gauge_color = RED
                else:
                    gauge_w = 0
                    gauge_color = GRAY
                if gauge_w > 0:
                    pygame.draw.rect(screen, gauge_color, (260, VIRTUAL_HEIGHT - 130, gauge_w, 25))
                pygame.draw.rect(screen, WHITE if state_phase < 4 else GRAY, (260, VIRTUAL_HEIGHT - 130, 120, 25), width=2)
                lbl_eng = self.small_font.render("PORTAL CHARGE", True, WHITE if state_phase < 4 else GRAY)
                screen.blit(lbl_eng, (260, VIRTUAL_HEIGHT - 155))
                
                # Right gauge: Gate Sync / Vector drift
                pygame.draw.rect(screen, (10, 12, 15), (VIRTUAL_WIDTH - 380, VIRTUAL_HEIGHT - 130, 120, 25))
                if state_phase == 1:
                    gauge_w = int(120 * 0.9)
                    gauge_color = CYAN
                elif state_phase == 2:
                    gauge_w = int(120 * (0.3 + 0.1 * math.sin(ticks * 0.005)))
                    gauge_color = YELLOW
                elif state_phase == 3:
                    gauge_w = int(120 * (0.05 + 0.05 * math.sin(ticks * 0.02)))
                    gauge_color = ORANGE
                else:
                    gauge_w = 0
                    gauge_color = GRAY
                if gauge_w > 0:
                    pygame.draw.rect(screen, gauge_color, (VIRTUAL_WIDTH - 380, VIRTUAL_HEIGHT - 130, gauge_w, 25))
                pygame.draw.rect(screen, WHITE if state_phase < 4 else GRAY, (VIRTUAL_WIDTH - 380, VIRTUAL_HEIGHT - 130, 120, 25), width=2)
                lbl_g = self.small_font.render("GATE SYNC", True, WHITE if state_phase < 4 else GRAY)
                screen.blit(lbl_g, (VIRTUAL_WIDTH - 380, VIRTUAL_HEIGHT - 155))
                
                # Warning status messages
                if state_phase == 2:
                    if ticks % 400 < 200:
                        pygame.draw.circle(screen, RED, (VIRTUAL_WIDTH // 2 - 130, VIRTUAL_HEIGHT - 100), 10)
                        pygame.draw.circle(screen, RED, (VIRTUAL_WIDTH // 2 + 130, VIRTUAL_HEIGHT - 100), 10)
                    warn_lbl = self.small_font.render("PORTAL COLLAPSE ALERT", True, RED)
                    screen.blit(warn_lbl, (VIRTUAL_WIDTH // 2 - warn_lbl.get_width() // 2, VIRTUAL_HEIGHT - 170))
                elif state_phase == 3:
                    if ticks % 200 < 100:
                        pygame.draw.circle(screen, RED, (VIRTUAL_WIDTH // 2 - 130, VIRTUAL_HEIGHT - 100), 10)
                        pygame.draw.circle(screen, RED, (VIRTUAL_WIDTH // 2 + 130, VIRTUAL_HEIGHT - 100), 10)
                    warn_lbl = self.small_font.render("CRITICAL DIMENSIONAL TURBULENCE", True, RED)
                    screen.blit(warn_lbl, (VIRTUAL_WIDTH // 2 - warn_lbl.get_width() // 2, VIRTUAL_HEIGHT - 170))
                elif state_phase == 4:
                    warn_lbl = self.small_font.render("COCKPIT SYSTEM OFFLINE", True, (150, 30, 30))
                    screen.blit(warn_lbl, (VIRTUAL_WIDTH // 2 - warn_lbl.get_width() // 2, VIRTUAL_HEIGHT - 170))
                    
                    # Draw cockpit canopy glass cracks
                    pygame.draw.line(screen, (230, 230, 235), (280, 120), (330, 190), width=2)
                    pygame.draw.line(screen, (230, 230, 235), (330, 190), (310, 260), width=2)
                    pygame.draw.line(screen, (230, 230, 235), (330, 190), (440, 210), width=1)
                    pygame.draw.line(screen, (230, 230, 235), (VIRTUAL_WIDTH - 380, 210), (VIRTUAL_WIDTH - 300, 250), width=2)
                    pygame.draw.line(screen, (230, 230, 235), (VIRTUAL_WIDTH - 300, 250), (VIRTUAL_WIDTH - 330, 320), width=1)

            if v_time < 8000:
                # PHASE 1: Galaxy Flight & Portal Entry (Cockpit View)
                self.virtual_screen.fill((2, 4, 10))
                
                # Draw passing warp starfield in the background (layered behind portal)
                center_x, center_y = VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2
                random.seed(99)
                for j in range(50):
                    angle = (j * 17.3) % (2 * math.pi)
                    speed = 8 + (j % 5) * 3
                    dist = ((v_time * 0.08 * speed) + j * 50) % 700
                    if dist < 10: continue
                    sx = center_x + math.cos(angle) * dist
                    sy = center_y + math.sin(angle) * dist
                    pygame.draw.circle(self.virtual_screen, (200, 220, 255), (int(sx), int(sy)), max(1, int(dist * 0.004)))
                random.seed()
                
                # Swirling Portal ring getting larger
                portal_radius = int(50 + (v_time / 8000.0) * 450)
                
                # Render glowing portal circles
                ticks = pygame.time.get_ticks()
                portal_color = CYAN if v_time < 6200 else RED  # portal collapses / turns red near the end of phase 1!
                
                for r in range(4):
                    pygame.draw.circle(self.virtual_screen, portal_color, (center_x, center_y), portal_radius + r * 15, width=2)
                
                for angle in range(0, 360, 30):
                    rad = math.radians(angle + ticks * 0.05)
                    px = center_x + portal_radius * math.cos(rad)
                    py = center_y + portal_radius * math.sin(rad)
                    pygame.draw.line(self.virtual_screen, portal_color, (center_x, center_y), (int(px), int(py)), 1)
                
                # Draw mini neural constellation hologram on dashboard
                h_surf = pygame.Surface((220, 130), pygame.SRCALPHA)
                h_surf.fill((0, 255, 100, 20))
                pygame.draw.rect(h_surf, (0, 255, 120), (0, 0, 220, 130), width=1)
                h_lbl = self.small_font.render("NET RESTORED: 100%", True, GREEN)
                h_surf.blit(h_lbl, (10, 10))
                self.virtual_screen.blit(h_surf, (80, VIRTUAL_HEIGHT - 150))
                
                # Telemetry text on dashboard
                telemetry = [
                    ">> TARGET SECTOR WARP GATES LINKED...",
                    ">> INITIATING TRANS-DIMENSIONAL JUMP PROTOCOL",
                    ">> WARNING: GEOMETRICAL DRIFT DETECTED IN CORE RIFT..."
                ]
                for idx, line in enumerate(telemetry):
                    if v_time > 1200 + idx * 700:
                        t_surf = self.small_font.render(line, True, GREEN if v_time < 6200 else RED)
                        self.virtual_screen.blit(t_surf, (80, 50 + idx * 25))
                        
                draw_first_person_cockpit(self.virtual_screen, 1)
                
                # Smooth white flash near the end of Phase 1
                if v_time > 7500:
                    alpha = int((v_time - 7500) / 500.0 * 255)
                    flash = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                    flash.fill(WHITE)
                    flash.set_alpha(alpha)
                    self.virtual_screen.blit(flash, (0, 0))
                
                msg = self.large_font.render("GALAXY LIBERATED", True, WHITE)
                self.virtual_screen.blit(msg, (VIRTUAL_WIDTH//2 - msg.get_width()//2, 120))

            elif v_time < 14000:
                # PHASE 2: Hyper-jump Failure & Collapse (Cockpit View)
                self.virtual_screen.fill(BLACK)
                
                # Unstable distorted crimson hyper-warp vortex
                center_x, center_y = VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2
                ticks = pygame.time.get_ticks()
                random.seed(42)
                for j in range(60):
                    angle = (j * 13.7 + ticks * 0.01) % (2 * math.pi)
                    speed = 12 + (j % 12) * 6
                    dist = ((v_time * 0.18 * speed) + j * 45) % 800
                    if dist < 20: continue
                    distort = math.sin(ticks * 0.005 + j) * 60
                    sx = center_x + distort + math.cos(angle) * dist
                    sy = center_y + distort + math.sin(angle) * dist
                    pygame.draw.circle(self.virtual_screen, (255, 30, j % 150), (int(sx), int(sy)), max(2, int(dist * 0.005)))
                random.seed()
                
                # Visual Glitches & CRT overlay flashing
                if v_time % 300 < 150:
                    alert_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                    alert_surf.fill((255, 0, 0, 50))
                    self.virtual_screen.blit(alert_surf, (0, 0))
                    
                    # Dashboard warning labels
                    warn = self.large_font.render("PORTAL COLLAPSE", True, RED)
                    self.virtual_screen.blit(warn, (VIRTUAL_WIDTH//2 - warn.get_width()//2, 100))
                    
                    system_fail = self.font.render("SINGULARITY DRIFT DETECTED // PROTOCOL RUPTURED", True, WHITE)
                    self.virtual_screen.blit(system_fail, (VIRTUAL_WIDTH//2 - system_fail.get_width()//2, 200))
                
                # Scanline glitches
                if random.random() < 0.35:
                    glitch_y = random.randint(0, VIRTUAL_HEIGHT)
                    pygame.draw.rect(self.virtual_screen, (255, 0, 0, 90), (0, glitch_y, VIRTUAL_WIDTH, random.randint(4, 15)))
                
                draw_first_person_cockpit(self.virtual_screen, 2)
                self.screen_shake = 14
                
                # Smooth white flash fade-out at start of Phase 2
                if v_time < 8500:
                    alpha = int((8500 - v_time) / 500.0 * 255)
                    flash = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                    flash.fill(WHITE)
                    flash.set_alpha(alpha)
                    self.virtual_screen.blit(flash, (0, 0))
                
                # Smooth magenta flash at end of Phase 2
                if v_time > 13500:
                    alpha = int((v_time - 13500) / 500.0 * 255)
                    flash = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                    flash.fill((255, 0, 100))
                    flash.set_alpha(alpha)
                    self.virtual_screen.blit(flash, (0, 0))

            elif v_time < 20000:
                # PHASE 3: Dimensional Turbulence (Cockpit View)
                entry_time = v_time - 14000
                self.virtual_screen.fill((20, 5, 25))
                
                # Swirling dimensional storm currents rising
                for _ in range(25):
                    fx = random.randint(50, VIRTUAL_WIDTH - 50)
                    fy = VIRTUAL_HEIGHT - 180 - random.randint(0, 380)
                    f_size = random.randint(20, 70)
                    f_color = (random.choice([150, 220]), 0, random.choice([200, 255]), 110)
                    f_surf = pygame.Surface((f_size * 2, f_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(f_surf, f_color, (f_size, f_size), f_size)
                    self.virtual_screen.blit(f_surf, (fx - f_size, fy - f_size))
                    
                # Electrical arcs outside the canopy window
                if random.random() < 0.4:
                    px1 = random.randint(100, VIRTUAL_WIDTH - 100)
                    py1 = random.randint(50, VIRTUAL_HEIGHT - 220)
                    px2 = px1 + random.randint(-150, 150)
                    py2 = py1 + random.randint(-100, 100)
                    pygame.draw.line(self.virtual_screen, (100, 255, 255), (px1, py1), (px2, py2), width=3)
                
                # Dimensional tint overlay
                overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                overlay.fill((200, 0, 255, min(140, int(entry_time * 0.03))))
                self.virtual_screen.blit(overlay, (0, 0))
                
                draw_first_person_cockpit(self.virtual_screen, 3)
                self.screen_shake = 10
                
                # Smooth magenta flash fade-out at start of Phase 3
                if v_time < 14500:
                    alpha = int((14500 - v_time) / 500.0 * 255)
                    flash = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                    flash.fill((255, 0, 100))
                    flash.set_alpha(alpha)
                    self.virtual_screen.blit(flash, (0, 0))
                
                # Smooth white flash near the end of Phase 3 before crashing
                if entry_time > 5200:
                    alpha = int((entry_time - 5200) / 800.0 * 255)
                    flash = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                    flash.fill(WHITE)
                    flash.set_alpha(alpha)
                    self.virtual_screen.blit(flash, (0,0))

            else:
                # PHASE 4: Alien Forest Planet (Cockpit View)
                self.virtual_screen.fill((4, 12, 10)) # Dark teal atmosphere
                
                # Alien sky glow / background nebula
                neb_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(neb_surf, (20, 60, 50, 50), (VIRTUAL_WIDTH // 3, VIRTUAL_HEIGHT // 3), 400)
                pygame.draw.circle(neb_surf, (80, 0, 100, 30), (2 * VIRTUAL_WIDTH // 3, VIRTUAL_HEIGHT // 2), 500)
                self.virtual_screen.blit(neb_surf, (0, 0))
                
                # Double moons
                # Moon 1 (Luminescent Cyan)
                m1x, m1y = 920, 140
                pygame.draw.circle(self.virtual_screen, (100, 255, 230), (m1x, m1y), 45)
                pygame.draw.circle(self.virtual_screen, (150, 255, 240), (m1x - 10, m1y - 10), 38)
                # Moon 2 (Smaller, Purple)
                m2x, m2y = 810, 210
                pygame.draw.circle(self.virtual_screen, (150, 50, 200), (m2x, m2y), 25)
                
                # Draw rolling terrain / alien forest floor (overlapping hills)
                # Back hills (dark indigo)
                pygame.draw.ellipse(self.virtual_screen, (8, 20, 28), (-200, 480, VIRTUAL_WIDTH + 400, 350))
                # Mid hills (dark teal/green)
                pygame.draw.ellipse(self.virtual_screen, (12, 32, 28), (-100, 520, VIRTUAL_WIDTH + 200, 300))
                # Foreground hills (deep forest floor green)
                pygame.draw.ellipse(self.virtual_screen, (5, 22, 16), (-150, 560, VIRTUAL_WIDTH + 300, 250))
                
                # Draw alien forest trees!
                random.seed(88)
                for _ in range(15):
                    tx = random.randint(100, VIRTUAL_WIDTH - 100)
                    ty = random.randint(530, 680)
                    
                    # Scale based on depth
                    scale = (ty - 480) / 200.0  # 0.25 to 1.0
                    t_height = int(240 * scale)
                    t_width = int(14 * scale)
                    
                    # Tree trunk (massive sequoia tapering upward polygon)
                    base_w = int(t_width * 1.5)
                    top_w = int(t_width * 0.45)
                    pygame.draw.polygon(self.virtual_screen, (40, 28, 20), [
                        (tx - base_w, ty), 
                        (tx + base_w, ty), 
                        (tx + top_w, ty - t_height), 
                        (tx - top_w, ty - t_height)
                    ])
                    
                    # Branches (thick limbs starting high up)
                    br_w = max(2, int(6 * scale))
                    pygame.draw.line(self.virtual_screen, (40, 28, 20), (tx, ty - int(t_height * 0.65)), (tx - int(30 * scale), ty - int(t_height * 0.75)), width=br_w)
                    pygame.draw.line(self.virtual_screen, (40, 28, 20), (tx, ty - int(t_height * 0.70)), (tx + int(35 * scale), ty - int(t_height * 0.80)), width=br_w)
                    pygame.draw.line(self.virtual_screen, (40, 28, 20), (tx, ty - int(t_height * 0.85)), (tx - int(25 * scale), ty - int(t_height * 0.92)), width=br_w)
                    pygame.draw.line(self.virtual_screen, (40, 28, 20), (tx, ty - int(t_height * 0.88)), (tx + int(25 * scale), ty - int(t_height * 0.95)), width=br_w)
                    
                    # Overlapping foliage colors
                    c_color = random.choice([
                        (255, 0, 150), # Neon magenta
                        (0, 240, 255), # Neon cyan
                        (200, 80, 255) # Light purple
                    ])
                    
                    def draw_dense_cluster(cx, cy, radius):
                        for dx, dy in [(0, 0), (-int(5*scale), -int(3*scale)), (int(4*scale), -int(5*scale)), (int(2*scale), int(3*scale))]:
                            c_x, c_y = cx + dx, cy + dy
                            pygame.draw.circle(self.virtual_screen, c_color, (c_x, c_y), radius)
                            pygame.draw.circle(self.virtual_screen, (max(0, c_color[0]-45), max(0, c_color[1]-45), max(0, c_color[2]-45)), (c_x - 2, c_y - 2), int(radius * 0.75))
                        if random.random() < 0.3:
                            pygame.draw.circle(self.virtual_screen, WHITE, (cx, cy), int(4 * scale))
                            
                    # Draw dense clusters at each branch tip and main crown
                    draw_dense_cluster(tx, ty - t_height, int(22 * scale))
                    draw_dense_cluster(tx - int(30 * scale), ty - int(t_height * 0.75), int(16 * scale))
                    draw_dense_cluster(tx + int(35 * scale), ty - int(t_height * 0.80), int(16 * scale))
                    draw_dense_cluster(tx - int(25 * scale), ty - int(t_height * 0.92), int(14 * scale))
                    draw_dense_cluster(tx + int(25 * scale), ty - int(t_height * 0.95), int(14 * scale))
                random.seed()
                
                draw_first_person_cockpit(self.virtual_screen, 4)
                
                # Smooth white crash flash fade-out at start of Phase 4
                fade_time = v_time - 20000
                if fade_time < 1200:
                    alpha = int((1200 - fade_time) / 1200.0 * 255)
                    flash = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                    flash.fill(WHITE)
                    flash.set_alpha(alpha)
                    self.virtual_screen.blit(flash, (0, 0))
                
                # UI Teaser reveal
                if v_time > 26000:
                    alpha = min(255, (v_time - 26000) // 10)
                    teaser_surf = self.large_font.render("ZENITH", True, (0, 255, 255))
                    teaser_surf.set_alpha(alpha)
                    self.virtual_screen.blit(teaser_surf, (VIRTUAL_WIDTH//2 - teaser_surf.get_width()//2, VIRTUAL_HEIGHT//2 - 120))
                    
                    sub_surf = self.font.render("NEW FRONTIER", True, (255, 255, 255))
                    sub_surf.set_alpha(alpha)
                    self.virtual_screen.blit(sub_surf, (VIRTUAL_WIDTH//2 - sub_surf.get_width()//2, VIRTUAL_HEIGHT//2 - 40))
                    
                    coming_surf = self.small_font.render("Coming Soon...", True, GRAY)
                    coming_surf.set_alpha(alpha)
                    self.virtual_screen.blit(coming_surf, (VIRTUAL_WIDTH//2 - coming_surf.get_width()//2, VIRTUAL_HEIGHT//2 + 10))
                
                if v_time > 18000:
                    retry_msg = self.small_font.render("Press R to Restart Exploration", True, (100, 100, 100))
                    self.virtual_screen.blit(retry_msg, (VIRTUAL_WIDTH // 2 - retry_msg.get_width() // 2, VIRTUAL_HEIGHT - 60))
                    menu_msg = self.small_font.render("Press M for Main Menu", True, (100, 100, 100))
                    self.virtual_screen.blit(menu_msg, (VIRTUAL_WIDTH // 2 - menu_msg.get_width() // 2, VIRTUAL_HEIGHT - 35))
            
        # Draw sliders if in menu/paused
        if self.state in ('MAIN_MENU', 'CLASS_SELECT', 'PAUSED'):
            mx, my = pygame.mouse.get_pos()
            vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
            vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
            
            slider_x = 980
            slider_w = 150
            track_h = 6
            
            def draw_slider(label, y_pos, current_val, max_val, is_dragging):
                vol_ratio = max(0.0, min(1.0, current_val / max_val))
                
                # Simple colored rectangle panel with rounded corners
                pygame.draw.rect(self.virtual_screen, (15, 15, 20, 210), (slider_x - 15, y_pos - 25, slider_w + 30, 50), border_radius=6)
                pygame.draw.rect(self.virtual_screen, (75, 75, 85), (slider_x - 15, y_pos - 25, slider_w + 30, 50), width=1, border_radius=6)
                
                lbl = self.small_font.render(f"{label}: {int(current_val)}", True, CYAN)
                self.virtual_screen.blit(lbl, (slider_x, y_pos - 20))
                
                pygame.draw.rect(self.virtual_screen, (30, 30, 35), (slider_x, y_pos, slider_w, track_h), border_radius=3)
                pygame.draw.rect(self.virtual_screen, CYAN, (slider_x, y_pos, int(slider_w * vol_ratio), track_h), border_radius=3)
                
                kx = slider_x + int(slider_w * vol_ratio)
                ky = y_pos + track_h // 2
                
                is_hover = False
                slider_rect = pygame.Rect(slider_x - 15, y_pos - 25, slider_w + 30, 50)
                if slider_rect.collidepoint(vmx, vmy):
                    is_hover = True
                    
                knob_r = 8 if (is_hover or is_dragging) else 6
                knob_color = WHITE if (is_hover or is_dragging) else CYAN
                pygame.draw.circle(self.virtual_screen, knob_color, (kx, ky), knob_r)
            
            # 1. Volume Slider (y=45)
            if SOUNDS:
                draw_slider("SOUND VOL", 45, SOUNDS.volume * 100, 100, self.dragging_volume)
            else:
                draw_slider("SOUND VOL", 45, 0, 100, self.dragging_volume)
            
            # 2. Tint Alpha Slider (y=110)
            draw_slider("TINT ALPHA", 110, self.filter_tint_alpha, 150, self.dragging_tint)
            
            # 3. Vignette Alpha Slider (y=175)
            draw_slider("VIGNETTE", 175, self.filter_vignette_alpha, 200, self.dragging_vignette)
            
            # 4. Softness/Blur Slider (y=240)
            draw_slider("SOFT FOCUS", 240, self.filter_softness, 60, self.dragging_softness)
            
        # Draw save feedback message on HUD during gameplay/Hub
        if getattr(self, 'save_feedback_msg', '') != "" and pygame.time.get_ticks() - getattr(self, 'save_feedback_time', 0) < 3000:
            fb_color = GREEN if "success" in self.save_feedback_msg.lower() or "loaded" in self.save_feedback_msg.lower() or "saved" in self.save_feedback_msg.lower() or "autosav" in self.save_feedback_msg.lower() else RED
            fb_lbl = self.small_font.render(self.save_feedback_msg, True, fb_color)
            self.virtual_screen.blit(fb_lbl, (VIRTUAL_WIDTH - fb_lbl.get_width() - 15, VIRTUAL_HEIGHT - fb_lbl.get_height() - 15))

        # Hub active portals pointer / radar
        if self.state == 'HUB':
            player_pos = pygame.math.Vector2(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2)
            for zone, cfg in BIOME_CONFIGS.items():
                if cfg['hub'] == self.current_hub_index and self.unlocked_zones.get(zone, False):
                    order = cfg['order']
                    if order == 0:
                        portal_center = pygame.math.Vector2(150, 750)
                    elif order == 1:
                        portal_center = pygame.math.Vector2(1050, 180)
                    elif order == 3:
                        portal_center = pygame.math.Vector2(1050, 750)
                    else:
                        portal_center = pygame.math.Vector2(150, 180)
                        
                    to_portal = portal_center - player_pos
                    dist = to_portal.length()
                    
                    # Only show pointer if the portal is off screen (player is relatively far)
                    if dist > 350:
                        target_dir = to_portal.normalize()
                        angle = math.degrees(math.atan2(target_dir.y, target_dir.x))
                        
                        # Place arrow on a radius of 120 pixels around player
                        arrow_x = VIRTUAL_WIDTH // 2 + target_dir.x * 120
                        arrow_y = VIRTUAL_HEIGHT // 2 + target_dir.y * 120
                        
                        arrow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                        pygame.draw.polygon(arrow_surf, cfg['theme_color'], [(8, 4), (24, 15), (8, 26), (14, 15)])
                        rot_arrow = pygame.transform.rotate(arrow_surf, -angle)
                        
                        self.virtual_screen.blit(rot_arrow, (int(arrow_x - rot_arrow.get_width() // 2), int(arrow_y - rot_arrow.get_height() // 2)))
                        
                        # Small text indicator
                        p_lbl = self.small_font.render(cfg['name'].split(' ')[0], True, cfg['theme_color'])
                        self.virtual_screen.blit(p_lbl, (int(arrow_x - p_lbl.get_width() // 2), int(arrow_y + 15)))

        # Restore original virtual screen and apply post-processing filters
        self.virtual_screen = original_virtual_screen
        
        # 1. Soft Focus / Edge Softening effect (offset overlay blits)
        if self.filter_softness > 0:
            soft_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            soft_surf.blit(self.virtual_screen, (-1, 0))
            soft_surf.blit(self.virtual_screen, (1, 0))
            soft_surf.blit(self.virtual_screen, (0, -1))
            soft_surf.blit(self.virtual_screen, (0, 1))
            soft_surf.set_alpha(int(self.filter_softness))
            self.virtual_screen.blit(soft_surf, (0, 0))
            
        # 2. Biome-based Color Tint Filter
        if self.filter_tint_alpha > 0:
            tint_color = BIOME_CONFIGS.get(self.current_zone, {'theme_color': GRAY})['theme_color']
            tint_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            tint_surf.fill((*tint_color, int(self.filter_tint_alpha)))
            self.virtual_screen.blit(tint_surf, (0, 0))
            
        # 3. Vignette Overlay
        if self.filter_vignette_alpha > 0 and getattr(self, 'vignette_surface', None) is not None:
            temp_vignette = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            temp_vignette.blit(self.vignette_surface, (0, 0))
            factor = min(255, int(self.filter_vignette_alpha * 255 / 200))
            temp_vignette.fill((255, 255, 255, factor), special_flags=pygame.BLEND_RGBA_MULT)
            self.virtual_screen.blit(temp_vignette, (0, 0))

        # Floating Dev Panel (if dev mode active)
        if getattr(self, 'dev_mode', False):
            # Recalculate mouse positions using letterbox scale for hover effects
            mx, my = pygame.mouse.get_pos()
            vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
            vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
            
            panel_x = VIRTUAL_WIDTH - 230
            panel_y = 20
            panel_w = 210
            panel_h = 240
            
            # Draw panel background
            panel_bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_bg.fill((15, 15, 20, 220))
            pygame.draw.rect(panel_bg, RED, (0, 0, panel_w, panel_h), width=2, border_radius=8)
            self.ui_surface.blit(panel_bg, (panel_x, panel_y))
            
            # Header
            hdr_lbl = self.font.render("DEV CONTROL PANEL", True, RED)
            self.ui_surface.blit(hdr_lbl, (panel_x + panel_w // 2 - hdr_lbl.get_width() // 2, panel_y + 12))
            
            # Draw clickable buttons
            buttons = [
                ("INVINCIBLE", "invincible", pygame.Rect(panel_x + 10, panel_y + 45, panel_w - 20, 35)),
                ("ADD RESOURCES", "resources", pygame.Rect(panel_x + 10, panel_y + 95, panel_w - 20, 35)),
                ("SKIP LEVEL", "skip_level", pygame.Rect(panel_x + 10, panel_y + 145, panel_w - 20, 35)),
                ("SKIP TO ENDING", "skip_ending", pygame.Rect(panel_x + 10, panel_y + 195, panel_w - 20, 35))
            ]
            
            for text, action_type, btn_rect in buttons:
                is_hover = btn_rect.collidepoint(vmx, vmy)
                
                if action_type == "invincible":
                    btn_color = GREEN if getattr(self, 'debug_invincible', False) else (50, 50, 55)
                    text_color = WHITE if getattr(self, 'debug_invincible', False) else (200, 200, 200)
                else:
                    btn_color = (70, 70, 75) if is_hover else (45, 45, 50)
                    text_color = WHITE if is_hover else (200, 200, 200)
                
                pygame.draw.rect(self.ui_surface, btn_color, btn_rect, border_radius=5)
                pygame.draw.rect(self.ui_surface, WHITE if is_hover else RED, btn_rect, width=1, border_radius=5)
                
                btn_lbl = self.small_font.render(text, True, text_color)
                self.ui_surface.blit(btn_lbl, (btn_rect.centerx - btn_lbl.get_width() // 2, btn_rect.centery - btn_lbl.get_height() // 2))

        # Composite the dedicated UI layer on top
        self.virtual_screen.blit(self.ui_surface, (0, 0))

        # Render to logical screen with letterbox padding
        scaled_screen = pygame.transform.smoothscale(self.virtual_screen, (self.new_width, self.new_height))

        self.screen.fill(BLACK)
        
        bx, by = self.offset_x, self.offset_y
            
        self.screen.blit(scaled_screen, (bx, by))
        pygame.display.flip()

    def run(self):
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
