import pygame
import random
import sys
import math

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

BIOME_CONFIGS = {
    'ASTEROIDS': {'name': 'Asteroid Belt', 'theme_color': GRAY, 'desc': 'Heavy Meteor Shower', 'stars_color': GRAY, 'hub': 1, 'order': 0, 'boss_count': 1},
    'VULCAN': {'name': 'Vulcan Sector', 'theme_color': ORANGE, 'desc': 'Hyper Fast Speed', 'stars_color': ORANGE, 'hub': 1, 'order': 1, 'boss_count': 1},
    'AQUARIS': {'name': 'Aquaris Nebula', 'theme_color': CYAN, 'desc': 'Armored Ice Fields', 'stars_color': CYAN, 'hub': 1, 'order': 2, 'boss_count': 1},
    
    'NEBULA': {'name': 'Nebula Storm', 'theme_color': PURPLE, 'desc': 'Electrical Storms', 'stars_color': PURPLE, 'hub': 2, 'order': 0, 'boss_count': 2},
    'PLASMA': {'name': 'Plasma Core', 'theme_color': GOLD, 'desc': 'High-Energy Currents', 'stars_color': GOLD, 'hub': 2, 'order': 1, 'boss_count': 2},
    'VOID': {'name': 'Void Chasm', 'theme_color': INDIGO, 'desc': 'Zero-Gravity Abyss', 'stars_color': INDIGO, 'hub': 2, 'order': 2, 'boss_count': 2},
    
    'QUANTUM': {'name': 'Quantum Rift', 'theme_color': GREEN, 'desc': 'Dimensional Shifting', 'stars_color': GREEN, 'hub': 3, 'order': 0, 'boss_count': 2},
    'SINGULARITY': {'name': 'Singularity Edge', 'theme_color': BLUE, 'desc': 'Gravitational Shears', 'stars_color': BLUE, 'hub': 3, 'order': 1, 'boss_count': 2},
    'ORION': {'name': 'Orion Citadel', 'theme_color': MAGENTA, 'desc': 'Overlord Fortress', 'stars_color': MAGENTA, 'hub': 3, 'order': 2, 'boss_count': 3}
}

class Bullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 18
        self.width = 16
        self.height = 16
        self.rect = pygame.Rect(self.x - 8, self.y - 8, self.width, self.height)
        self.target = None

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
        self.rect.x = int(self.x - 8)
        self.rect.y = int(self.y - 8)

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        start_pt = (int(draw_x - self.dx * 8), int(draw_y - self.dy * 8))
        end_pt = (int(draw_x + self.dx * 4), int(draw_y + self.dy * 4))
        pygame.draw.line(screen, (255, 255, 0), start_pt, end_pt, width=6)
        pygame.draw.line(screen, (255, 255, 255), start_pt, end_pt, width=2)

class Torpedo:
    def __init__(self, x, y, dx, dy, scale=1.0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 10
        self.radius = int(8 * scale)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        self.exploded = False
        self.explosion_radius = int(120 * scale)
        self.explosion_duration = 30
        self.explosion_timer = 0

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
            glow = int(2 * math.sin(pygame.time.get_ticks() * 0.02))
            pygame.draw.circle(screen, (255, 69, 0), (int(draw_x), int(draw_y)), self.radius + glow)
            pygame.draw.circle(screen, (255, 215, 0), (int(draw_x), int(draw_y)), self.radius - 2)
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
        self.explosion_radius = int(140 * scale)
        
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
            r = int(self.explosion_radius * progress)
            alpha = int(220 * (1.0 - progress))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 69, 0, alpha // 2), (r, r), r)
            pygame.draw.circle(surf, (255, 140, 0, alpha), (r, r), r, width=3)
            screen.blit(surf, (int(draw_x - r), int(draw_y - r)))
        else:
            pulse = int(3 * math.sin(pygame.time.get_ticks() * 0.015))
            pygame.draw.circle(screen, RED, (int(draw_x), int(draw_y)), 10 + pulse)
            pygame.draw.circle(screen, GOLD, (int(draw_x), int(draw_y)), 6 + pulse)
            pygame.draw.circle(screen, WHITE, (int(draw_x), int(draw_y)), 2)

class HomingMissile:
    def __init__(self, x, y, dx, dy, scale=1.0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 10.0
        self.width = 16
        self.height = 16
        self.rect = pygame.Rect(self.x - 8, self.y - 8, self.width, self.height)
        self.exploded = False
        self.explosion_timer = 0
        self.explosion_duration = 20
        self.explosion_radius = int(90 * scale)
        self.target = None
        
    def update(self, enemies, camera_y):
        if self.exploded:
            self.explosion_timer += 1
            return
            
        # Target tracking
        if not self.target or self.target.health <= 0:
            closest = None
            min_d = 800.0
            for ent in enemies:
                if ent.health > 0:
                    d = pygame.math.Vector2(self.x, self.y).distance_to(pygame.math.Vector2(ent.x, ent.y))
                    if d < min_d:
                        min_d = d
                        closest = ent
            self.target = closest
            
        if self.target:
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
            alpha = int(220 * (1.0 - progress))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (0, 200, 255, alpha // 2), (r, r), r)
            pygame.draw.circle(surf, (255, 255, 255, alpha), (r, r), r, width=2)
            screen.blit(surf, (int(draw_x - r), int(draw_y - r)))
        else:
            angle = math.degrees(math.atan2(self.dy, self.dx))
            missile_surf = pygame.Surface((20, 10), pygame.SRCALPHA)
            pygame.draw.rect(missile_surf, CYAN, (0, 2, 14, 6), border_radius=2)
            pygame.draw.polygon(missile_surf, WHITE, [(14, 0), (20, 5), (14, 10)])
            rot_missile = pygame.transform.rotate(missile_surf, -angle)
            screen.blit(rot_missile, (int(draw_x - rot_missile.get_width() // 2), int(draw_y - rot_missile.get_height() // 2)))

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
        alpha = int(255 * (self.life / self.max_life))
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        r, g, b = self.color
        pygame.draw.circle(surf, (r, g, b, alpha), (self.radius, self.radius), self.radius)
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        screen.blit(surf, (int(draw_x) - self.radius, int(draw_y) - self.radius))

class EnemyBullet:
    def __init__(self, x, y, dx, dy, color=(255, 100, 100), speed=6, size=8, is_gravity=False, is_homing=False, target_player=None):
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

    def update(self):
        if self.is_homing and self.target_player:
            player_center = pygame.math.Vector2(self.target_player.rect.center)
            to_player = player_center - pygame.math.Vector2(self.x, self.y)
            if to_player.length() > 5:
                to_player = to_player.normalize()
                dir_vec = pygame.math.Vector2(self.dx, self.dy).normalize()
                dir_vec += to_player * 0.05
                dir_vec = dir_vec.normalize()
                self.dx = dir_vec.x
                self.dy = dir_vec.y
                
        if self.is_gravity and self.target_player:
            player_center = pygame.math.Vector2(self.target_player.rect.center)
            to_bullet = pygame.math.Vector2(self.x, self.y) - player_center
            dist = to_bullet.length()
            if dist < 180:
                pull_strength = (180 - dist) * 0.015
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
        glow_size = self.size + 4 + int(2 * math.sin(pygame.time.get_ticks() * 0.03))
        surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, 80), (glow_size, glow_size), glow_size)
        pygame.draw.circle(surf, (*self.color, 160), (glow_size, glow_size), self.size)
        pygame.draw.circle(surf, (255, 255, 255, 245), (glow_size, glow_size), max(1, self.size - 2))
        screen.blit(surf, (int(draw_x) - glow_size, int(draw_y) - glow_size))
        
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

class GravityWell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 200
        self.rect = pygame.Rect(self.x - 20, self.y - 20, 40, 40)
        self.pull_force = 0.5

    def update(self, player, bullets, meteors, static_obstacles):
        p_pos = pygame.math.Vector2(player.x + player.width // 2, player.y + player.height // 2)
        well_pos = pygame.math.Vector2(self.x, self.y)
        dist = p_pos.distance_to(well_pos)
        if dist < self.radius and dist > 10:
            pull = (well_pos - p_pos).normalize() * (self.pull_force * (1.0 - dist / self.radius))
            player.x += pull.x
            player.y += pull.y
        
        for b in bullets:
            b_pos = pygame.math.Vector2(b.x, b.y)
            dist = b_pos.distance_to(well_pos)
            if dist < self.radius and dist > 10:
                pull = (well_pos - b_pos).normalize() * (self.pull_force * 0.7 * (1.0 - dist / self.radius))
                b.x += pull.x
                b.y += pull.y
                # Curve bullet flight path slightly
                desired_dir = (well_pos - b_pos).normalize()
                current_dir = pygame.math.Vector2(b.dx, b.dy)
                new_dir = current_dir.lerp(desired_dir, 0.05).normalize()
                b.dx = new_dir.x
                b.dy = new_dir.y

        for m in meteors + static_obstacles:
            m_pos = pygame.math.Vector2(m.rect.center)
            dist = m_pos.distance_to(well_pos)
            if dist < self.radius and dist > 10:
                pull = (well_pos - m_pos).normalize() * (self.pull_force * 0.4 * (1.0 - dist / self.radius))
                m.x += pull.x
                m.y += pull.y
                m.rect.center = (int(m.x), int(m.y))

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

class SubBossEntity:
    def __init__(self, name, max_health, color, width, height, x_offset, y_offset, behavior_type):
        self.name = name
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
        center = pygame.math.Vector2(draw_x, draw_y)
        dir_f = pygame.math.Vector2(0, 1) # Forward is down
        dir_r = pygame.math.Vector2(1, 0) # Right is right
        
        # 1. ENGINES FLAMES
        flicker = random.randint(0, 12)
        flame_color = self.color
        flame_inner = WHITE if self.color != WHITE else YELLOW
        
        rear_pos = center - dir_f * (self.height // 2)
        pygame.draw.polygon(screen, flame_color, [
            rear_pos - dir_r * (self.width // 6),
            rear_pos - dir_f * (15 + flicker),
            rear_pos + dir_r * (self.width // 6)
        ])
        pygame.draw.polygon(screen, flame_inner, [
            rear_pos - dir_r * (self.width // 12),
            rear_pos - dir_f * (8 + flicker * 0.6),
            rear_pos + dir_r * (self.width // 12)
        ])
        
        # 2. HULL DRAWING
        lw_tip = center - dir_r * (self.width // 2) - dir_f * (self.height // 4)
        rw_tip = center + dir_r * (self.width // 2) - dir_f * (self.height // 4)
        nose = center + dir_f * (self.height // 2)
        tail = center - dir_f * (self.height // 3)
        
        pygame.draw.polygon(screen, SLATE_GRAY, [nose, lw_tip, tail, rw_tip])
        pygame.draw.polygon(screen, self.color, [nose, lw_tip, tail, rw_tip], width=2)
        
        pygame.draw.polygon(screen, self.color, [
            center + dir_f * (self.height // 4),
            center - dir_r * (self.width // 4) - dir_f * (self.height // 6),
            center - dir_f * (self.height // 4),
            center + dir_r * (self.width // 4) - dir_f * (self.height // 6)
        ])
        
        pulse_r = 5 + int(3 * math.sin(pygame.time.get_ticks() * 0.02))
        pygame.draw.circle(screen, self.color, (int(center.x), int(center.y + 4)), pulse_r + 2)
        pygame.draw.circle(screen, WHITE, (int(center.x), int(center.y + 4)), max(1, pulse_r - 2))

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
        self.name = cfg['name'].upper()
        self.color = cfg['theme_color']
        self.boss_count = cfg['boss_count']
        
        # Scaling difficulty factors
        zone_keys = ['ASTEROIDS', 'VULCAN', 'AQUARIS', 'NEBULA', 'PLASMA', 'VOID', 'QUANTUM', 'SINGULARITY', 'ORION']
        diff_idx = zone_keys.index(zone) if zone in zone_keys else 0
        
        # Boss difficulty adjustments: health scales up, delays scale down in later levels
        base_max_health = 35 + diff_idx * 12
        self.shoot_delay = max(500, 1500 - diff_idx * 110)
        self.max_health = base_max_health
        self.health = self.max_health
        
        # Setup SubBoss Entities
        self.sub_bosses = []
        if self.boss_count == 1:
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

        if hasattr(self, 'appearance_timer') and self.appearance_timer > 0:
            self.appearance_timer -= 1
            target_y = player.y - 450
            self.y += (target_y - self.y) * 0.05
            self.x = VIRTUAL_WIDTH // 2
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

        # Boss slowly creeps closer to the player over time
        self.boss_player_dist = max(100.0, self.boss_player_dist - 0.25)
        target_y = player.y - self.boss_player_dist
        self.y += (target_y - self.y) * 0.03
        
        t = pygame.time.get_ticks() * 0.002
        self.x = VIRTUAL_WIDTH // 2 + 250 * math.sin(t)
        
        self.angle_offset += 0.03
        
        for ent in self.sub_bosses:
            ent.update_position(self.x, self.y, t)
            
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
            self.gravity_well.update(player, game_instance.bullets, game_instance.meteors, game_instance.static_obstacles)
            
        # Firing logic for each active sub-boss
        for ent in self.sub_bosses:
            if ent.is_dead:
                continue
            if current_time - ent.last_shot > self.shoot_delay:
                ent.last_shot = current_time
                ent_center = pygame.math.Vector2(ent.rect.center)
                player_center = pygame.math.Vector2(player.rect.center)
                dir_to_player = (player_center - ent_center).normalize()
                
                # Biome-specific custom bullet attacks (harder in later levels!)
                if self.zone == 'AQUARIS':
                    for rot in [-15, 0, 15]:
                        r_dir = dir_to_player.rotate(rot)
                        projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, r_dir.x, r_dir.y, color=CYAN, speed=5.5))
                elif self.zone == 'VULCAN':
                    projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, dir_to_player.x, dir_to_player.y, color=ORANGE, speed=6.5))
                    r_vec = pygame.math.Vector2(-dir_to_player.y, dir_to_player.x) * 35
                    projectiles_list.append(EnemyBullet(ent_center.x - r_vec.x, ent_center.y - r_vec.y, dir_to_player.x, dir_to_player.y, color=YELLOW, speed=6.5))
                    projectiles_list.append(EnemyBullet(ent_center.x + r_vec.x, ent_center.y + r_vec.y, dir_to_player.x, dir_to_player.y, color=YELLOW, speed=6.5))
                elif self.zone == 'ASTEROIDS':
                    projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, dir_to_player.x, dir_to_player.y, color=PURPLE, speed=5))
                    for angle in range(0, 360, 90):
                        rad = math.radians(angle + math.degrees(self.angle_offset))
                        projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, math.cos(rad), math.sin(rad), color=PURPLE, speed=5))
                elif self.zone == 'NEBULA':
                    for rot in [-20, 0, 20]:
                        r_dir = dir_to_player.rotate(rot)
                        projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, r_dir.x, r_dir.y, color=PURPLE, speed=6.0, size=9))
                elif self.zone == 'PLASMA':
                    projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, dir_to_player.x, dir_to_player.y, color=GOLD, speed=5.5, size=8, is_homing=True, target_player=player))
                elif self.zone == 'VOID':
                    projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, dir_to_player.x, dir_to_player.y, color=INDIGO, speed=4.5, size=10, is_gravity=True, target_player=player))
                elif self.zone == 'QUANTUM':
                    for angle in range(0, 360, 60):
                        rad = math.radians(angle + math.degrees(self.angle_offset))
                        projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, math.cos(rad), math.sin(rad), color=GREEN, speed=5.0, size=8))
                elif self.zone == 'SINGULARITY':
                    projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, dir_to_player.x, dir_to_player.y, color=BLUE, speed=4.0, size=11, is_gravity=True, is_homing=True, target_player=player))
                elif self.zone == 'ORION':
                    if ent.behavior_type == 'tri_1':
                        projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, dir_to_player.x, dir_to_player.y, color=MAGENTA, speed=6.0, size=8, is_homing=True, target_player=player))
                    elif ent.behavior_type == 'tri_2':
                        for offset in [-25, 0, 25]:
                            r = math.radians(math.degrees(math.atan2(dir_to_player.y, dir_to_player.x)) + offset)
                            projectiles_list.append(EnemyBullet(ent_center.x, ent_center.y, math.cos(r), math.sin(r), color=GOLD, speed=6.5, size=7))
                    else:
                        perp_dx = -dir_to_player.y
                        perp_dy = dir_to_player.x
                        projectiles_list.append(EnemyBullet(ent_center.x - perp_dx * 12, ent_center.y - perp_dy * 12, dir_to_player.x, dir_to_player.y, color=INDIGO, speed=7.0, size=6))
                        projectiles_list.append(EnemyBullet(ent_center.x + perp_dx * 12, ent_center.y + perp_dy * 12, dir_to_player.x, dir_to_player.y, color=INDIGO, speed=7.0, size=6))

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
        
        name_lbl = pygame.font.SysFont("Arial", 16, bold=True).render(self.name, True, WHITE)
        screen.blit(name_lbl, (VIRTUAL_WIDTH // 2 - name_lbl.get_width() // 2, bar_y - 24))

class Enemy:
    def __init__(self, x, y, zone='PLAYING'):
        self.zone = zone
        self.x = x
        self.y = y
        self.last_shot = pygame.time.get_ticks() + random.randint(-800, 800)
        self.angle = 90.0 # Straight down default
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
        if self.subtype in ('SCOUT', 'ELITE'):
            self.evade_chance = random.uniform(0.40, 0.65)
        else:
            self.evade_chance = random.uniform(0.15, 0.30)
        
        if zone == 'AQUARIS':
            # Cold/Ice Theme
            if self.subtype == 'STANDARD':
                self.name = "Frost Vanguard"
                self.speed = random.uniform(1.0, 1.6)
                self.color = CYAN
                self.health = 2
                self.shoot_delay = 1800
                self.credits_value = 25
            elif self.subtype == 'HEAVY':
                self.name = "Glacial Sentry"
                self.speed = random.uniform(0.6, 0.9)
                self.color = (0, 100, 255) # Deep Blue
                self.health = 6  # Tanky!
                self.shoot_delay = 3000  # Weak gun (slow fire rate)
                self.width, self.height = 40, 40
                self.credits_value = 45
            elif self.subtype == 'SCOUT':
                self.name = "Ice Charger"
                self.speed = random.uniform(2.5, 3.2)  # Fast rammer
                self.color = (180, 220, 255) # Pale Blue
                self.health = 1
                self.shoot_delay = 9999999 # never shoots (rams player)
                self.width, self.height = 24, 24
                self.credits_value = 20
            else: # ELITE (MINIBOSS)
                self.name = "Snowstorm Skiff"
                self.speed = random.uniform(1.2, 1.8)
                self.color = (0, 200, 200) # Teal
                self.health = 5  # Tanky Miniboss
                self.shoot_delay = 1400  # Strong multi-laser
                self.credits_value = 35
                
        elif zone == 'VULCAN':
            # Fire/Speed Theme
            if self.subtype == 'STANDARD':
                self.name = "Vulcan Scout"
                self.speed = random.uniform(2.8, 3.8)
                self.color = ORANGE
                self.health = 1
                self.shoot_delay = 1800
                self.credits_value = 20
            elif self.subtype == 'HEAVY':
                self.name = "Magma Bomber"
                self.speed = random.uniform(1.5, 2.0)
                self.color = (180, 0, 0) # Dark Red
                self.health = 5  # Tanky!
                self.shoot_delay = 3200  # Slow lava mortar
                self.width, self.height = 42, 42
                self.credits_value = 40
            elif self.subtype == 'SCOUT':
                self.name = "Solar Skiff"
                self.speed = random.uniform(4.0, 4.8)
                self.color = YELLOW
                self.health = 1
                self.shoot_delay = 2000
                self.width, self.height = 24, 24
                self.credits_value = 30
            else: # ELITE (MINIBOSS)
                self.name = "Pyro Interceptor"
                self.speed = random.uniform(2.5, 3.2)
                self.color = (255, 60, 60) # Crimson
                self.health = 4  # Tanky Miniboss
                self.shoot_delay = 1500  # Homing missile
                self.credits_value = 35
                
        else: # ASTEROIDS or default PLAYING
            # Void/Scrap Theme
            if self.subtype == 'STANDARD':
                self.name = "Scrap Raider"
                self.speed = random.uniform(1.5, 2.2)
                self.color = RED
                self.health = 1
                self.shoot_delay = 1800
                self.credits_value = 15
            elif self.subtype == 'HEAVY':
                self.name = "Gravity Anchor"
                self.speed = random.uniform(0.8, 1.2)
                self.color = PURPLE
                self.health = 5  # Tanky!
                self.shoot_delay = 2000  # Gravity bullet
                self.width, self.height = 38, 38
                self.credits_value = 35
            elif self.subtype == 'SCOUT':
                self.name = "Meteor Dart"
                self.speed = random.uniform(2.8, 3.5)
                self.color = (200, 100, 255) # Violet
                self.health = 1
                self.shoot_delay = 1100
                self.width, self.height = 24, 24
                self.credits_value = 25
            else: # ELITE (MINIBOSS)
                self.name = "Cosmic Corsair"
                self.speed = random.uniform(1.6, 2.4)
                self.color = (255, 0, 255) # Magenta
                self.health = 4  # Tanky Miniboss
                self.shoot_delay = 1500  # Double parallel lasers
                self.credits_value = 30
        # Scale difficulty based on zone index
        zone_keys = ['ASTEROIDS', 'VULCAN', 'AQUARIS', 'NEBULA', 'PLASMA', 'VOID', 'QUANTUM', 'SINGULARITY', 'ORION']
        diff_idx = zone_keys.index(zone) if zone in zone_keys else 0
        if diff_idx > 0:
            self.health = max(1, self.health + diff_idx // 3)
            if self.shoot_delay < 5000000:
                self.shoot_delay = max(600, self.shoot_delay - diff_idx * 80)
            self.speed = self.speed * (1.0 + diff_idx * 0.05)
            
        self.max_health = self.health
        if zone in BIOME_CONFIGS and zone not in ('AQUARIS', 'VULCAN', 'ASTEROIDS'):
            self.color = BIOME_CONFIGS[zone]['theme_color']
            
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.velocity = pygame.math.Vector2(0, self.speed)
        self.acceleration = 0.1
        self.drag = 0.98
 
    def update(self, current_time, player, projectiles_list, player_bullets=None):
        # 1. Meteor Dart Camouflage Gimmick
        if self.zone == 'ASTEROIDS' and self.subtype == 'SCOUT' and self.is_dormant:
            player_center = pygame.math.Vector2(player.rect.center)
            enemy_center = pygame.math.Vector2(self.rect.center)
            if player_center.distance_to(enemy_center) < 250:
                self.is_dormant = False
                self.last_shot = current_time + 400
            else:
                self.y += 0.5
                self.rect.y = int(self.y)
                return

        player_center = pygame.math.Vector2(player.rect.center)
        enemy_center = pygame.math.Vector2(self.rect.center)
        to_player = player_center - enemy_center

        # Evasion mechanic: dodge player bullets if close
        if player_bullets and current_time - self.last_evade > self.evade_cooldown:
            for bullet in player_bullets:
                bullet_pos = pygame.math.Vector2(bullet.x, bullet.y)
                dist_vec = bullet_pos - enemy_center
                if dist_vec.length() < 130 and bullet_pos.y > self.y:
                    if random.random() < self.evade_chance:
                        # Dodge sideways
                        dodge_dir = -1.0 if dist_vec.x > 0 else 1.0
                        dodge_impulse = dodge_dir * 8.5
                        self.velocity.x += dodge_impulse
                        self.velocity.y -= 1.5
                        self.last_evade = current_time
                        break
        
        # 2. Solar Skiff Dash Gimmick
        if self.zone == 'VULCAN' and self.subtype == 'SCOUT':
            if current_time - self.last_dash > 2000:
                self.last_dash = current_time
                self.velocity.x += random.choice([-7.0, 7.0])
                
        # 3. Frost Vanguard Deflect Shield Gimmick
        if self.zone == 'AQUARIS' and self.subtype == 'STANDARD':
            self.shield_active = (current_time // 1200) % 2 == 0

        if to_player.length() > 5:
            self.angle = math.degrees(math.atan2(to_player.y, to_player.x))
            accel_dir = to_player.normalize()
            self.velocity += accel_dir * self.acceleration
        else:
            self.angle = 90.0
            
        self.velocity *= self.drag
        if self.velocity.length() > self.speed:
            self.velocity = self.velocity.normalize() * self.speed
            
        self.x += self.velocity.x
        self.y += self.velocity.y
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
            
        if abs(self.y - player_center.y) < 600:
            if current_time - self.last_shot > self.shoot_delay:
                self.last_shot = current_time
                rad = math.radians(self.angle)
                bullet_dx = math.cos(rad)
                bullet_dy = math.sin(rad)
                
                # Custom shooting patterns for gimmicks
                if self.zone == 'AQUARIS':
                    if self.subtype == 'HEAVY':
                        # Glacial Sentry: Weak slow tiny bullet
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=(150, 200, 255), speed=2.5, size=4))
                    elif self.subtype == 'ELITE':
                        # Snowstorm Skiff Miniboss: 3 spreading lasers
                        for offset in [-15, 0, 15]:
                            r = math.radians(self.angle + offset)
                            projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, math.cos(r), math.sin(r), color=self.color, speed=5, size=8))
                    elif self.subtype == 'SCOUT':
                        pass
                    else:
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=self.color, speed=5, size=7))
                        
                elif self.zone == 'VULCAN':
                    if self.subtype == 'HEAVY':
                        # Magma Bomber: Large slow lava mortar
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=ORANGE, speed=2.5, size=15))
                    elif self.subtype == 'ELITE':
                        # Pyro Interceptor Miniboss: Homing missile
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=RED, speed=4, size=9, is_homing=True, target_player=player))
                    else:
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=self.color, speed=6, size=7))
                        
                else: # ASTEROIDS or default
                    if self.subtype == 'HEAVY':
                        # Gravity Anchor: Gravity pull bullet
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=PURPLE, speed=4.5, size=10, is_gravity=True, target_player=player))
                    elif self.subtype == 'ELITE':
                        # Cosmic Corsair Miniboss: Double laser barrage
                        perp_dx = -bullet_dy
                        perp_dy = bullet_dx
                        projectiles_list.append(EnemyBullet(enemy_center.x - perp_dx * 8, enemy_center.y - perp_dy * 8, bullet_dx, bullet_dy, color=self.color, speed=6, size=7))
                        projectiles_list.append(EnemyBullet(enemy_center.x + perp_dx * 8, enemy_center.y + perp_dy * 8, bullet_dx, bullet_dy, color=self.color, speed=6, size=7))
                    else:
                        projectiles_list.append(EnemyBullet(enemy_center.x, enemy_center.y, bullet_dx, bullet_dy, color=self.color, speed=5, size=7))

    def on_death(self, projectiles_list, player):
        if self.zone == 'ASTEROIDS' and self.subtype == 'STANDARD':
            # Scrap Raider: Spawns 4 diagonal scrap debris bullets on death
            for dx, dy in [(-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7), (0.7, 0.7)]:
                projectiles_list.append(EnemyBullet(self.rect.centerx, self.rect.centery, dx, dy, color=(160, 160, 160), speed=3.5, size=5))

    def draw(self, screen, camera_y, camera_x=0):
        draw_x = self.x - camera_x
        # Camouflage rendering for Meteor Dart scout
        if self.zone == 'ASTEROIDS' and self.subtype == 'SCOUT' and self.is_dormant:
            draw_y = self.y - camera_y
            pygame.draw.circle(screen, (100, 100, 100), (int(draw_x + self.width // 2), int(draw_y + self.height // 2)), 12)
            pygame.draw.circle(screen, (80, 80, 80), (int(draw_x + self.width // 2), int(draw_y + self.height // 2)), 12, width=2)
            return

        draw_y = self.y - camera_y
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
        pygame.draw.polygon(screen, RED, [rear_center, rear_center - dir_r * 6, rear_center - dir_f * flame_len, rear_center + dir_r * 6])
        
        # 2. Swept wings/mandibles pointing forward
        lw_tip = center + dir_f * (self.height // 2) - dir_r * (self.width // 2)
        lw_base = center - dir_f * (self.height // 4) - dir_r * 6
        pygame.draw.polygon(screen, SLATE_GRAY, [center, lw_tip, lw_base])
        
        rw_tip = center + dir_f * (self.height // 2) + dir_r * (self.width // 2)
        rw_base = center - dir_f * (self.height // 4) + dir_r * 6
        pygame.draw.polygon(screen, SLATE_GRAY, [center, rw_tip, rw_base])
        
        # 3. Main Hull Core
        hull_tip = center + dir_f * (self.height // 3)
        hull_l = center - dir_f * (self.height // 2) - dir_r * 6
        hull_r = center - dir_f * (self.height // 2) + dir_r * 6
        pygame.draw.polygon(screen, self.color, [hull_tip, hull_l, hull_r])
        
        # 4. Glowing eye/engine core
        eye_color = YELLOW if self.zone == 'VULCAN' else (WHITE if self.zone == 'AQUARIS' else ORANGE)
        pygame.draw.circle(screen, eye_color, (int(center.x), int(center.y)), 4)
        
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
            
        if hasattr(self, 'name'):
            if not hasattr(self, 'name_font'):
                self.name_font = pygame.font.SysFont("Arial", 10, bold=True)
            name_surf = self.name_font.render(self.name, True, WHITE)
            y_offset = 12 if has_health_bar else 6
            name_rect = name_surf.get_rect(centerx=int(draw_x + self.width // 2), bottom=draw_y - y_offset)
            bg_rect = name_rect.inflate(4, 2)
            pygame.draw.rect(screen, (20, 20, 20), bg_rect)
            screen.blit(name_surf, name_rect)

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
        pygame.draw.polygon(screen, color, draw_points)

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

class Player:
    def __init__(self):
        self.width = 40
        self.height = 40
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
        self.torpedo_delay = 1000
        self.direction = pygame.math.Vector2(0, -1)
        self.angle = 270.0  # angle in degrees, pointing straight up (270)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = 0.35
        self.max_speed = 6.0
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
        
        # Upgrade Part Levels
        self.skills = {
            'shield': 0,          # Max 4 (Base 1 shield capacity, upgrades up to 5)
            'deflector': 0,       # Max 1 (Deflector Shielding. Regen delay: 5s -> 3s)
            'coolant': 0,         # Max 4 (Standard gun cools down +25% faster per level)
            'weapon': 0,          # Max 2 (0: Single, 1: Double, 2: spreading Triple)
            'overcharge': 0,      # Max 1 (Overcharged Capacitors. Shoot delay -30%)
            'torpedo': 0,         # Max 4 (-15% cooldown, +15% explosion size per level)
            'cluster_torpedo': 0, # Max 1 (Cluster Torpedo Warhead. Spawns sub-explosions)
            'hyperdrive': 0,      # Max 1 (Hyperdrive Core. Warp charge: 3s -> 1s)
            'shotgun_mod': 0,     # Max 3 (Shotgun Heat -15%, Damage +15% per rank)
            'railgun_mod': 0,     # Max 3 (Railgun Delay -15% per rank)
            'bomb_cap': 0,        # Max 3 (Bomb Max Ammo +2, Radius +15% per rank)
            'missile_cap': 0,     # Max 3 (Missile Max Ammo +3, Speed +15% per rank)
        }
        
        # Weapon Switching and Ammo Stats
        self.active_primary = 0 # 0: Laser, 1: Shotgun, 2: Railgun
        self.active_secondary = 0 # 0: Torpedo, 1: Bomb, 2: Missile
        
        self.max_torpedo_ammo = 10
        self.torpedo_ammo = 10
        self.max_bomb_ammo = 5
        self.bomb_ammo = 5
        self.max_missile_ammo = 8
        self.missile_ammo = 8
        
        # Shield health stats
        self.max_shields = 3
        self.shields = self.max_shields
        self.invulnerable = False
        self.invulnerable_time = 0
        self.invulnerable_duration = 1000
        self.last_hit_time = 0
        self.shield_regen_delay = 5000
        self.last_regen_time = 0
        self.regen_cooldown = 3000
        
        # Dash evading mechanics
        self.last_dash = 0
        self.dash_cooldown = 1000

    def add_credits(self, amount):
        if self.is_dead:
            return
        self.credits += amount

    def update_regen(self, current_time):
        if self.is_dead:
            return
        
        if self.invulnerable and current_time - self.invulnerable_time > self.invulnerable_duration:
            self.invulnerable = False

        self.max_shields = 3 + self.skills['shield']
        regen_delay = 3000 if self.skills.get('deflector', 0) > 0 else self.shield_regen_delay
        if self.shields < self.max_shields:
            if current_time - self.last_hit_time > regen_delay:
                if current_time - self.last_regen_time > self.regen_cooldown:
                    self.shields = min(self.max_shields, self.shields + 1)
                    self.last_regen_time = current_time

    def trigger_dash(self, direction, current_time):
        if self.is_dead:
            return False
        if current_time - self.last_dash > self.dash_cooldown:
            self.last_dash = current_time
            rad = math.radians(self.angle)
            direction_vector = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            dir_r = pygame.math.Vector2(-direction_vector.y, direction_vector.x)
            
            dash_force = 6.0
            if direction == 'LEFT':
                self.velocity -= dir_r * dash_force
            else:
                self.velocity += dir_r * dash_force
            return True
        return False

    def handle_input(self, current_time, camera_y, scale_info, camera_x=0, is_hub=False, limit_y=False):
        if self.is_dead:
            return []

        keys = pygame.key.get_pressed()
        
        # 1. MOUSE-FACING ORIENTATION (smooth turning over time)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        offset_x, offset_y, new_w, new_h = scale_info
        mouse_x = (mouse_x - offset_x) * (VIRTUAL_WIDTH / new_w)
        mouse_y = (mouse_y - offset_y) * (VIRTUAL_HEIGHT / new_h)
        if not limit_y:
            mouse_y += camera_y
            mouse_x += camera_x
            
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        target_dir = pygame.math.Vector2(mouse_x - center_x, mouse_y - center_y)
        if target_dir.length() > 5:
            target_angle = math.degrees(math.atan2(target_dir.y, target_dir.x)) % 360
            
            # Shortest path interpolation to prevent 360-wraparound jumps
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            
            # Rotation speed (degrees per frame) - lower values mean slower turning
            max_turn = 4.5
            if abs(angle_diff) <= max_turn:
                self.angle = target_angle
            else:
                self.angle = (self.angle + math.copysign(max_turn, angle_diff)) % 360

        # Calculate current directional vectors from the actual current angle
        rad = math.radians(self.angle)
        self.direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        dir_r = pygame.math.Vector2(-self.direction.y, self.direction.x) # right vector

        # 2. ACCELERATION / MOVEMENT THRUSTER INPUTS
        accel = self.acceleration * self.speed_multiplier
        max_sp = self.max_speed * self.speed_multiplier
        
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

        self.x = max(-3000, min(VIRTUAL_WIDTH + 3000 - self.width, self.x))
        if limit_y:
            self.y = max(0, min(VIRTUAL_HEIGHT - self.height, self.y))
        else:
            # Constrain player so they cannot fly below the camera's viewport
            self.y = min(self.y, camera_y + VIRTUAL_HEIGHT - self.height)
            
        self.rect.topleft = (self.x, self.y)

        if is_hub:
            return []

        projectiles = []
        mouse_buttons = pygame.mouse.get_pressed()
        
        actual_cool_rate = self.cool_rate * (1.0 + 0.25 * self.skills['coolant'])
        if self.heat > 0:
            self.heat = max(0.0, self.heat - actual_cool_rate)
            if self.overheated and self.heat == 0.0:
                self.overheated = False

        # Left click to shoot standard bullets
        if mouse_buttons[0]:
            if not self.overheated:
                actual_shoot_delay = self.shoot_delay * 0.70 if self.skills.get('overcharge', 0) > 0 else self.shoot_delay
                if current_time - self.last_shot > actual_shoot_delay:
                    self.last_shot = current_time
                    self.heat += self.heat_per_shot
                    if self.heat >= self.max_heat:
                        self.heat = self.max_heat
                        self.overheated = True
                        
                    tip_x = center_x + self.direction.x * (self.height // 2)
                    tip_y = center_y + self.direction.y * (self.height // 2)
                    
                    weapon_level = self.skills['weapon']
                    if weapon_level == 0:
                        projectiles.append(Bullet(tip_x, tip_y, self.direction.x, self.direction.y))
                    elif weapon_level == 1:
                        right_vector = pygame.math.Vector2(-self.direction.y, self.direction.x) * 8
                        projectiles.append(Bullet(tip_x - right_vector.x, tip_y - right_vector.y, self.direction.x, self.direction.y))
                        projectiles.append(Bullet(tip_x + right_vector.x, tip_y + right_vector.y, self.direction.x, self.direction.y))
                    else:
                        projectiles.append(Bullet(tip_x, tip_y, self.direction.x, self.direction.y))
                        dir_left = self.direction.rotate(-15)
                        dir_right = self.direction.rotate(15)
                        projectiles.append(Bullet(tip_x, tip_y, dir_left.x, dir_left.y))
                        projectiles.append(Bullet(tip_x, tip_y, dir_right.x, dir_right.y))

        # Right click to shoot AOE torpedoes
        if mouse_buttons[2]:
            actual_torpedo_delay = self.torpedo_delay * (1.0 - 0.15 * self.skills['torpedo'])
            if current_time - self.last_torpedo > actual_torpedo_delay:
                self.last_torpedo = current_time
                tip_x = center_x + self.direction.x * (self.height // 2)
                tip_y = center_y + self.direction.y * (self.height // 2)
                scale = 1.0 + 0.15 * self.skills['torpedo']
                projectiles.append(Torpedo(tip_x, tip_y, self.direction.x, self.direction.y, scale))

        return projectiles

    def draw(self, screen, camera_y, camera_x=0):
        if self.is_dead:
            return

        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        center_x = draw_x + self.width // 2
        center_y = draw_y + self.height // 2
        center = pygame.math.Vector2(center_x, center_y)
        
        # Directions
        dir_f = self.direction # forward
        dir_r = pygame.math.Vector2(-self.direction.y, self.direction.x) # right
        
        # Color palettes
        color = CYAN
        if self.invulnerable:
            if pygame.time.get_ticks() % 100 < 50:
                color = WHITE
        elif self.overheated:
            if pygame.time.get_ticks() % 200 < 100:
                color = RED
                
        # 1. THRUSTER FLAMES (flickers based on movement inputs)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w] or self.velocity.length() > 1:
            flame_len = 15 + random.randint(0, 10) if (keys[pygame.K_UP] or keys[pygame.K_w]) else 5 + random.randint(0, 5)
            rear_center = center - dir_f * (self.height // 2)
            flame_tip = rear_center - dir_f * flame_len
            flame_l = rear_center - dir_r * 8
            flame_r = rear_center + dir_r * 8
            pygame.draw.polygon(screen, ORANGE, [rear_center, flame_l, flame_tip, flame_r])
            pygame.draw.polygon(screen, YELLOW, [rear_center, rear_center - dir_r * 4, rear_center - dir_f * (flame_len * 0.6), rear_center + dir_r * 4])

        # 2. WINGS
        lw_tip = center - dir_f * 5 - dir_r * (self.width // 2)
        lw_base_in = center - dir_f * (self.height // 2) - dir_r * 5
        lw_base_out = center - dir_f * (self.height // 3) - dir_r * (self.width // 2)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, lw_tip, lw_base_out, lw_base_in])
        
        rw_tip = center - dir_f * 5 + dir_r * (self.width // 2)
        rw_base_in = center - dir_f * (self.height // 2) + dir_r * 5
        rw_base_out = center - dir_f * (self.height // 3) + dir_r * (self.width // 2)
        pygame.draw.polygon(screen, SLATE_GRAY, [center, rw_tip, rw_base_out, rw_base_in])

        # 3. WING CANNONS (Based on Weapon Level)
        weapon_level = self.skills['weapon']
        if weapon_level >= 1:
            pygame.draw.line(screen, color, lw_tip, lw_tip + dir_f * 12, width=3)
            pygame.draw.line(screen, color, rw_tip, rw_tip + dir_f * 12, width=3)
        if weapon_level >= 2:
            pygame.draw.line(screen, color, center + dir_f * (self.height // 2), center + dir_f * (self.height // 2 + 15), width=4)

        # 4. MAIN HULL
        hull_tip = center + dir_f * (self.height // 2)
        hull_left = center - dir_f * (self.height // 4) - dir_r * 8
        hull_right = center - dir_f * (self.height // 4) + dir_r * 8
        pygame.draw.polygon(screen, color, [hull_tip, hull_left, hull_right])

        # 5. COCKPIT GLASS
        glass_tip = center + dir_f * (self.height // 3)
        glass_left = center + dir_f * (self.height // 8) - dir_r * 4
        glass_right = center + dir_f * (self.height // 8) + dir_r * 4
        pygame.draw.polygon(screen, WHITE, [glass_tip, glass_left, glass_right])

        # 6. SHIELD FORCEFIELD (pulsing cyan circle when shields > 0)
        if self.shields > 0:
            glow_surf = pygame.Surface((self.width * 2, self.height * 2), pygame.SRCALPHA)
            glow_intensity = 30 + int(15 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.circle(glow_surf, (0, 255, 255, glow_intensity), (self.width, self.height), int(self.width * 0.9), width=2)
            screen.blit(glow_surf, (int(center_x - self.width), int(center_y - self.height)))

class Game:
    def __init__(self):
        pygame.init()
        # Enable RESIZABLE screen mode
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        pygame.display.set_caption("Space Shooter")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.large_font = pygame.font.SysFont("Arial", 64)
        
        # State Variables
        self.state = 'MAIN_MENU'
        self.current_zone = 'HUB'
        self.camera_y = 0
        self.camera_x = 0
        self.screen_shake = 0
        
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

    def reset_game(self):
        self.player = Player()
        self.bullets = []
        self.torpedoes = []
        self.enemies = []
        self.meteors = []
        self.stars = []
        self.particles = []
        self.materials = []
        self.scraps = []
        self.static_obstacles = []
        self.materials_collected = 0
        self.game_over = False
        self.running = True
        
        self.unlocked_zones = {
            'ASTEROIDS': True, 'VULCAN': False, 'AQUARIS': False,
            'NEBULA': False, 'PLASMA': False, 'VOID': False,
            'QUANTUM': False, 'SINGULARITY': False, 'ORION': False
        }
        self.current_hub_index = 1
        
        # New gimmick / boss objects
        self.enemy_bullets = []
        self.boss = None
        self.boss_defeated = False
        self.player_death_timer = 0
        self.active_hub_portal = None
        self.shield_crystals = []
        self.gravity_wells = []
        self.solar_flare_state = 'IDLE'
        self.solar_flare_timer = 0
        self.solar_flare_y = 0
        
        self.enemy_spawn_time = 0
        self.enemy_spawn_delay = 4000
        self.meteor_spawn_time = 0
        self.meteor_spawn_delay = 2000
        
        # Procedural height states
        self.highest_y_generated = 600
        self.materials_spawned_count = 0
        self.wormhole_spawned = False
        self.wormhole_charge_timer = 0
        
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

    def setup_exploration_zone(self, zone_name):
        self.state = 'PLAYING'
        self.current_zone = zone_name
        self.bullets = []
        self.torpedoes = []
        self.enemies = []
        self.meteors = []
        self.materials = []
        self.scraps = []
        self.static_obstacles = []
        self.materials_collected = 0
        self.player.speed_multiplier = 1.0
        
        # New gimmick / boss objects
        self.enemy_bullets = []
        self.boss = None
        self.boss_defeated = False
        self.active_hub_portal = None
        self.shield_crystals = []
        self.gravity_wells = []
        self.solar_flare_state = 'IDLE'
        self.solar_flare_timer = 0
        self.solar_flare_y = 0
        
        self.highest_y_generated = 600
        self.materials_spawned_count = 0
        self.wormhole_spawned = False
        self.wormhole_charge_timer = 0
        
        if zone_name in BIOME_CONFIGS:
            self.stars_color = BIOME_CONFIGS[zone_name]['stars_color']
        else:
            self.stars_color = GRAY
            
        self.player.x = VIRTUAL_WIDTH // 2 - self.player.width // 2
        self.player.y = 600
        self.camera_y = self.player.y - VIRTUAL_HEIGHT // 2
        self.camera_x = self.player.x - VIRTUAL_WIDTH // 2
        
        # Procedurally generate initial starting surroundings chunk
        self._procedurally_generate_chunk(600, -1000)

    def _procedurally_generate_chunk(self, from_y, to_y):
        # Generate static obstacles (asteroids) as player flies up
        # from_y is larger (bottom), to_y is smaller (top)
        num_obstacles = 12
        for _ in range(num_obstacles):
            ox = random.randint(-1800, VIRTUAL_WIDTH + 1800)
            oy = random.randint(int(to_y), int(from_y))
            
            overlap = False
            for obs in self.static_obstacles:
                if pygame.math.Vector2(ox, oy).distance_to(pygame.math.Vector2(obs.x, obs.y)) < 150:
                    overlap = True
            if not overlap:
                self.static_obstacles.append(Meteor(ox, oy, is_static=True))

        # Spawn Matrix Cores rarely and without limit (20% chance per 1200px chunk generated)
        if random.random() < 0.20:
            cx = random.randint(-2500, VIRTUAL_WIDTH + 2500)
            cy = random.randint(int(to_y), int(from_y))
            # Space them out to prevent clusters
            overlap = False
            for mat in self.materials:
                if pygame.math.Vector2(cx, cy).distance_to(pygame.math.Vector2(mat.x, mat.y)) < 300:
                    overlap = True
            if not overlap:
                self.materials.append(Material(cx, cy))
                self.materials_spawned_count += 1
                
        # Spawn level-specific gimmicks
        if self.current_zone == 'AQUARIS':
            for _ in range(random.randint(2, 4)):
                cx = random.randint(-1500, VIRTUAL_WIDTH + 1500)
                cy = random.randint(int(to_y), int(from_y))
                self.shield_crystals.append(ShieldCrystal(cx, cy))
        elif self.current_zone == 'ASTEROIDS':
            for _ in range(random.randint(1, 2)):
                gx = random.randint(-1500, VIRTUAL_WIDTH + 1500)
                gy = random.randint(int(to_y), int(from_y))
                self.gravity_wells.append(GravityWell(gx, gy))

    def spawn_explosion(self, x, y, color_palette, count=15):
        for _ in range(count):
            color = random.choice(color_palette)
            self.particles.append(Particle(x, y, color))
        self.screen_shake = min(15, self.screen_shake + int(count * 0.5))

    def _damage_player(self, current_time, damage=1):
        if self.player.is_dead or self.player.invulnerable:
            return
        
        self.player.shields -= damage
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

    def _handle_events(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Map coordinates using current letterbox settings
                vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
                vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
                
                # Upgrade Shop clicks (only permitted in the Hub)
                if self.state == 'PAUSED' and self.current_zone == 'HUB':
                    nodes_data = {
                        'shield': {'max_level': 4, 'cost_func': lambda p: (p.skills['shield'] + 1) * 75, 'scrap_cost_func': lambda p: (p.skills['shield'] + 1) * 2, 'deps': [], 'col': 1, 'row': 1},
                        'deflector': {'max_level': 1, 'cost_func': lambda p: 200, 'scrap_cost_func': lambda p: 5, 'deps': [('shield', 2)], 'col': 2, 'row': 1},
                        'coolant': {'max_level': 4, 'cost_func': lambda p: (p.skills['coolant'] + 1) * 60, 'scrap_cost_func': lambda p: (p.skills['coolant'] + 1) * 2, 'deps': [], 'col': 1, 'row': 2},
                        'weapon': {'max_level': 2, 'cost_func': lambda p: 200 if p.skills['weapon'] == 0 else 400, 'scrap_cost_func': lambda p: 8 if p.skills['weapon'] == 0 else 15, 'deps': [('coolant', 1)], 'col': 2, 'row': 2},
                        'overcharge': {'max_level': 1, 'cost_func': lambda p: 250, 'scrap_cost_func': lambda p: 8, 'deps': [('weapon', 1)], 'col': 3, 'row': 2},
                        'torpedo': {'max_level': 4, 'cost_func': lambda p: (p.skills['torpedo'] + 1) * 80, 'scrap_cost_func': lambda p: (p.skills['torpedo'] + 1) * 2, 'deps': [], 'col': 1, 'row': 3},
                        'cluster_torpedo': {'max_level': 1, 'cost_func': lambda p: 300, 'scrap_cost_func': lambda p: 10, 'deps': [('torpedo', 2)], 'col': 2, 'row': 3},
                        'hyperdrive': {'max_level': 1, 'cost_func': lambda p: 350, 'scrap_cost_func': lambda p: 12, 'deps': [('shield', 2), ('coolant', 2)], 'col': 1, 'row': 4}
                    }
                    
                    for key, node in nodes_data.items():
                        node_x = 630 + (node['col'] - 1) * 180
                        node_y = 210 + (node['row'] - 1) * 100
                        rect = pygame.Rect(node_x, node_y, 160, 80)
                        
                        if rect.collidepoint(vmx, vmy):
                            unlocked = True
                            for dep_key, req_lvl in node['deps']:
                                if self.player.skills[dep_key] < req_lvl:
                                    unlocked = False
                                    break
                                    
                            if unlocked:
                                current_level = self.player.skills[key]
                                max_level = node['max_level']
                                cost = node['cost_func'](self.player)
                                scrap_cost = node['scrap_cost_func'](self.player)
                                if current_level < max_level and self.player.credits >= cost and self.player.scraps >= scrap_cost:
                                    self.player.credits -= cost
                                    self.player.scraps -= scrap_cost
                                    self.player.skills[key] += 1
                                    if key == 'shield':
                                        self.player.max_shields = 3 + self.player.skills['shield']
                                        self.player.shields = self.player.max_shields

            if event.type == pygame.KEYDOWN:
                if self.state == 'MAIN_MENU':
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.reset_game()
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
                    elif event.key == pygame.K_m:
                        self.state = 'MAIN_MENU'
                
                elif self.state == 'GAME_OVER':
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif event.key == pygame.K_m:
                        self.state = 'MAIN_MENU'
                        
                elif self.state == 'VICTORY':
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif event.key == pygame.K_m:
                        self.state = 'MAIN_MENU'

    def _update(self):
        current_time = pygame.time.get_ticks()
        
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
                self.player.overheated = False
                self.player.is_dead = False
                
                self.state = 'GAME_OVER'
                self.current_zone = 'HUB'
                self.player.x = VIRTUAL_WIDTH // 2 - self.player.width // 2
                self.player.y = VIRTUAL_HEIGHT // 2 + 100
                self.bullets = []
                self.torpedoes = []
                self.enemies = []
                self.meteors = []
                self.stars_color = WHITE

        for star in self.stars:
            star[1] += star[2] * 2.0
            if star[1] > VIRTUAL_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, VIRTUAL_WIDTH)

        # Spawn Engine Particles
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_UP] or keys[pygame.K_w] or self.player.velocity.length() > 0.5) and not self.player.is_dead and self.state in ('PLAYING', 'HUB'):
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

        for obs in self.static_obstacles:
            obs.update()

        if self.state in ('PLAYING', 'HUB'):
            self.player.update_regen(current_time)
            max_sp = self.player.max_speed * self.player.speed_multiplier
            if self.player.velocity.length() > max_sp * 1.05:
                px = self.player.x + self.player.width // 2
                py = self.player.y + self.player.height // 2
                self.spawn_explosion(px, py, [(0, 255, 255), (255, 255, 255)], count=2)

        # ---------------- HUB STATE ----------------
        if self.state == 'HUB':
            scale_info = (self.offset_x, self.offset_y, self.new_width, self.new_height)
            self.player.handle_input(current_time, camera_y=0, scale_info=scale_info, camera_x=0, is_hub=True, limit_y=True)
            player_vec = pygame.math.Vector2(self.player.rect.center)
            
            # Dock Upgrade station
            station_center = pygame.math.Vector2(600, 450)
            if player_vec.distance_to(station_center) < 120:
                self.player.shields = self.player.max_shields
                
            # Check Cheat Portals collisions
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
            for zone, cfg in BIOME_CONFIGS.items():
                if cfg['hub'] == self.current_hub_index and self.unlocked_zones.get(zone, False):
                    order = cfg['order']
                    if order == 0:
                        portal_pos = pygame.math.Vector2(600, 780)
                    elif order == 1:
                        portal_pos = pygame.math.Vector2(1000, 220)
                    else:
                        portal_pos = pygame.math.Vector2(200, 220)
                        
                    if player_vec.distance_to(portal_pos) < 60:
                        active_portal = zone
                        break
                
            if active_portal:
                dt = self.clock.get_time()
                self.wormhole_charge_timer += dt
                self.active_hub_portal = active_portal
                
                target_charge = 1000 if self.player.skills.get('hyperdrive', 0) > 0 else 3000
                if self.wormhole_charge_timer >= target_charge:
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

        # Camera dynamic tracking
        self.camera_y = self.player.y - VIRTUAL_HEIGHT // 2
        self.camera_x = self.player.x - VIRTUAL_WIDTH // 2

        # Procedural surroundings generation on-the-fly!
        # Every time player advances 1000px up, generate next block
        if self.player.y - 1200 < self.highest_y_generated:
            self._procedurally_generate_chunk(self.highest_y_generated, self.highest_y_generated - 1200)
            self.highest_y_generated -= 1200

        # Memory Cleanup: De-spawn static asteroids that are far below camera viewport
        for obs in self.static_obstacles[:]:
            if obs.y > self.camera_y + VIRTUAL_HEIGHT + 400:
                self.static_obstacles.remove(obs)

        # Trigger Boss spawn once player has collected 5 matrix cores
        if self.materials_collected >= 5 and not self.wormhole_spawned and self.boss is None:
            self.boss = Boss(self.current_zone, self.player.y - 450)
            self.enemies = []
            self.meteors = []
            self.enemy_bullets = []

        # Check if player enters active wormhole
        if self.wormhole_spawned:
            player_vec = pygame.math.Vector2(self.player.rect.center)
            if player_vec.distance_to(self.wormhole_pos) < 60:
                dt = self.clock.get_time()
                self.wormhole_charge_timer += dt
                target_charge = 1000 if self.player.skills.get('hyperdrive', 0) > 0 else 3000
                if self.wormhole_charge_timer >= target_charge:
                    # WORMHOLE WARP: Complete exploration and earn Credits
                    self.player.add_credits(250)
                    
                    # Open-world Exploration progression: Asteroids -> Vulcan -> Aquaris -> Nebula -> Plasma -> Void -> Quantum -> Singularity -> Orion
                    if self.current_zone == 'ASTEROIDS':
                        self.unlocked_zones['VULCAN'] = True
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'VULCAN':
                        self.unlocked_zones['AQUARIS'] = True
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'AQUARIS':
                        self.unlocked_zones['NEBULA'] = True
                        self.current_hub_index = 2
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'NEBULA':
                        self.unlocked_zones['PLASMA'] = True
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'PLASMA':
                        self.unlocked_zones['VOID'] = True
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'VOID':
                        self.unlocked_zones['QUANTUM'] = True
                        self.current_hub_index = 3
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'QUANTUM':
                        self.unlocked_zones['SINGULARITY'] = True
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'SINGULARITY':
                        self.unlocked_zones['ORION'] = True
                        self.state = 'HUB'
                        self.current_zone = 'HUB'
                    elif self.current_zone == 'ORION':
                        self.state = 'VICTORY'
                    else:
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
                    return
            else:
                self.wormhole_charge_timer = 0

        scale_info = (self.offset_x, self.offset_y, self.new_width, self.new_height)
        new_projectiles = self.player.handle_input(current_time, self.camera_y, scale_info, camera_x=self.camera_x, limit_y=False)
        boss_ents = []
        if self.boss and not self.boss.is_dead:
            boss_ents = [ent for ent in self.boss.sub_bosses if not ent.is_dead]
        for proj in new_projectiles:
            if isinstance(proj, Torpedo):
                self.torpedoes.append(proj)
            else:
                proj.find_target(self.enemies + boss_ents, self.meteors, self.static_obstacles)
                self.bullets.append(proj)
        
        # Check Material Core collections
        for mat in self.materials[:]:
            if not self.player.is_dead and self.player.rect.colliderect(mat.rect):
                self.materials.remove(mat)
                self.materials_collected += 1
                self.spawn_explosion(mat.x, mat.y, [(255, 165, 0), (128, 0, 128), (255, 255, 255)], 20)
                self.player.add_credits(50)

        # Check Scrap collections
        for scrap in self.scraps[:]:
            if not self.player.is_dead and self.player.rect.colliderect(scrap.rect):
                if scrap in self.scraps:
                    self.scraps.remove(scrap)
                self.player.scraps += 1
                self.spawn_explosion(scrap.x, scrap.y, [(255, 215, 0), (255, 255, 255)], 10)
            elif scrap.y > self.camera_y + VIRTUAL_HEIGHT + 400:
                if scrap in self.scraps:
                    self.scraps.remove(scrap)

        # Check Solar Radiation zone damage
        if self.state == 'PLAYING' and (self.player.x < -2000 or self.player.x > VIRTUAL_WIDTH + 2000 - self.player.width):
            if not self.player.is_dead:
                px = self.player.x + self.player.width // 2
                py = self.player.y + self.player.height // 2
                if random.random() < 0.4:
                    self.particles.append(Particle(px + random.randint(-15, 15), py + random.randint(-15, 15), (255, 69, 0)))
                
                if not hasattr(self, 'last_radiation_damage'):
                    self.last_radiation_damage = 0
                if current_time - self.last_radiation_damage > 1500:
                    self._damage_player(current_time, damage=1)
                    self.last_radiation_damage = current_time

        # Spawning parameters
        actual_enemy_delay = self.enemy_spawn_delay
        actual_meteor_delay = self.meteor_spawn_delay
        
        if self.current_zone == 'ASTEROIDS':
            actual_enemy_delay = 8000
            actual_meteor_delay = 2000  # Increased delay (rarer asteroids)
        elif self.current_zone == 'VULCAN':
            actual_enemy_delay = 3000
            actual_meteor_delay = 8000  # Increased delay (rarer asteroids)
            
        if self.boss is None and not self.boss_defeated:
            if current_time - self.enemy_spawn_time > actual_enemy_delay:
                # 60% chance to spawn from top, 20% from left, 20% from right
                spawn_roll = random.random()
                if spawn_roll < 0.6:
                    spawn_x = random.randint(50, VIRTUAL_WIDTH - 50)
                    spawn_y = self.camera_y - 50
                elif spawn_roll < 0.8:
                    spawn_x = -50
                    spawn_y = self.camera_y + random.randint(50, VIRTUAL_HEIGHT - 150)
                else:
                    spawn_x = VIRTUAL_WIDTH + 50
                    spawn_y = self.camera_y + random.randint(50, VIRTUAL_HEIGHT - 150)
                
                self.enemies.append(Enemy(spawn_x, spawn_y, self.current_zone))
                self.enemy_spawn_time = current_time
                
            if current_time - self.meteor_spawn_time > actual_meteor_delay:
                spawn_y = self.camera_y - 50
                self.meteors.append(Meteor(random.randint(50, VIRTUAL_WIDTH - 50), spawn_y))
                self.meteor_spawn_time = current_time
        
        # Increase general spawn delay for meteors outside specific zone parameters
        self.meteor_spawn_delay = 6000
        
        # Update level shield crystals
        for crystal in self.shield_crystals[:]:
            crystal.update()
            if crystal.y > self.camera_y + VIRTUAL_HEIGHT + 100:
                if crystal in self.shield_crystals:
                    self.shield_crystals.remove(crystal)

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
                        self._damage_player(current_time)
                        self.player.heat = self.player.max_heat
                        self.player.overheated = True
            elif self.solar_flare_state == 'ACTIVE':
                self.solar_flare_timer += dt
                player_center_y = self.player.y + self.player.height // 2
                if self.solar_flare_y <= player_center_y <= self.solar_flare_y + 120:
                    self._damage_player(current_time)
                    self.player.heat = self.player.max_heat
                    self.player.overheated = True
                if self.solar_flare_timer > 800:
                    self.solar_flare_state = 'IDLE'
                    self.solar_flare_timer = 0

        # Update boss
        if self.boss:
            self.boss.update(current_time, self.player, self.enemy_bullets, self)
            if self.boss.is_dead and self.boss.death_timer > 120:
                for ent in self.boss.sub_bosses:
                    self.spawn_explosion(ent.x, ent.y, [(255, 255, 255), (0, 255, 255), (0, 100, 255)], 40)
                self.wormhole_pos = pygame.math.Vector2(self.boss.x, self.boss.y)
                self.wormhole_spawned = True
                self.boss = None
                self.boss_defeated = True

        # Update enemy bullets
        for eb in self.enemy_bullets[:]:
            eb.update()
            if eb.y < self.camera_y - 100 or eb.y > self.camera_y + VIRTUAL_HEIGHT + 100:
                if eb in self.enemy_bullets:
                    self.enemy_bullets.remove(eb)
            elif not self.player.is_dead and self.player.rect.colliderect(eb.rect):
                if eb in self.enemy_bullets:
                    self.enemy_bullets.remove(eb)
                self._damage_player(current_time, damage=1)

        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if (bullet.y < self.camera_y - 100 or bullet.y > self.camera_y + VIRTUAL_HEIGHT + 100 or
                bullet.x < self.camera_x - 100 or bullet.x > self.camera_x + VIRTUAL_WIDTH + 100):
                self.bullets.remove(bullet)

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
            enemy.update(current_time, self.player, self.enemy_bullets, self.bullets)
            if enemy.y > self.camera_y + VIRTUAL_HEIGHT + 100:
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
            elif not self.player.is_dead and self.player.rect.colliderect(enemy.rect):
                # Scale crash damage: scouts/standards deal 2, heavy/elites deal 3, ice charger deals 4
                crash_dmg = 2
                if enemy.subtype == 'HEAVY':
                    crash_dmg = 3
                elif enemy.subtype == 'ELITE':
                    crash_dmg = 3
                if getattr(enemy, 'zone', '') == 'AQUARIS' and getattr(enemy, 'subtype', '') == 'SCOUT':
                    crash_dmg = 4
                
                self._damage_player(current_time, damage=crash_dmg)
                self._kill_enemy(enemy)
        
        # Update meteors
        for meteor in self.meteors[:]:
            meteor.update()
            if meteor.y > self.camera_y + VIRTUAL_HEIGHT + 100:
                if meteor in self.meteors:
                    self.meteors.remove(meteor)
            elif not self.player.is_dead and self.player.rect.colliderect(meteor.rect):
                self._damage_player(current_time, damage=0.5)
                if meteor in self.meteors:
                    self.meteors.remove(meteor)

        # Update static obstacles collisions
        for obs in self.static_obstacles[:]:
            if not self.player.is_dead and self.player.rect.colliderect(obs.rect):
                self._damage_player(current_time, damage=0.5)
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
                if bullet.rect.colliderect(enemy.rect):
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    if self.is_enemy_shielded(enemy):
                        self.spawn_explosion(bullet.x, bullet.y, [(0, 255, 255), (255, 255, 255)], 6)
                    else:
                        enemy.health -= 0.5
                        if enemy.health <= 0:
                            self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, 
                                                 [(255, 0, 0), (255, 128, 0), (255, 255, 0)], 15)
                            self._kill_enemy(enemy)
                        
        # Bullet vs Meteor collision
        for bullet in self.bullets[:]:
            for meteor in self.meteors[:]:
                if bullet.rect.colliderect(meteor.rect):
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    if meteor in self.meteors:
                        self.spawn_explosion(meteor.rect.centerx, meteor.rect.centery, 
                                             [(128, 128, 128), (100, 100, 100), (80, 80, 80)], 25)
                        self.meteors.remove(meteor)
                        self.player.add_credits(meteor.credits_value)

        # Bullet vs Static Obstacle
        for bullet in self.bullets[:]:
            for obs in self.static_obstacles[:]:
                if bullet.rect.colliderect(obs.rect):
                    if bullet in self.bullets: self.bullets.remove(bullet)
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
                if hit:
                    torpedo.exploded = True
                    for enemy in self.enemies[:]:
                        if torpedo.rect.colliderect(enemy.rect):
                            if self.is_enemy_shielded(enemy):
                                self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, [(0, 255, 255), (255, 255, 255)], 10)
                            else:
                                self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, 
                                                     [(255, 0, 0), (255, 128, 0), (255, 255, 0)], 15)
                                enemy.health -= 3
                                if enemy.health <= 0:
                                    self._kill_enemy(enemy)
                    for meteor in self.meteors[:]:
                        if torpedo.rect.colliderect(meteor.rect):
                            self.spawn_explosion(meteor.rect.centerx, meteor.rect.centery, 
                                                 [(128, 128, 128), (100, 100, 100), (80, 80, 80)], 25)
                            if meteor in self.meteors:
                                self.meteors.remove(meteor)
                            self.player.add_credits(meteor.credits_value)
                    for obs in self.static_obstacles[:]:
                        if torpedo.rect.colliderect(obs.rect):
                            self.spawn_explosion(obs.rect.centerx, obs.rect.centery, 
                                                 [(128, 128, 128), (80, 80, 80)], 20)
                            if obs in self.static_obstacles:
                                self.static_obstacles.remove(obs)
                            self.player.add_credits(obs.credits_value)

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
                                enemy.health -= 1.5
                                if enemy.health <= 0:
                                    self._kill_enemy(enemy)
                            
                for meteor in self.meteors[:]:
                    meteor_center = pygame.math.Vector2(meteor.rect.center)
                    if torpedo_center.distance_to(meteor_center) <= current_radius:
                        if meteor in self.meteors:
                            self.spawn_explosion(meteor.rect.centerx, meteor.rect.centery, 
                                                 [(128, 128, 128), (100, 100, 100), (80, 80, 80)], 25)
                            self.meteors.remove(meteor)
                            self.player.add_credits(meteor.credits_value)

                for obs in self.static_obstacles[:]:
                    obs_center = pygame.math.Vector2(obs.rect.center)
                    if torpedo_center.distance_to(obs_center) <= current_radius:
                        if obs in self.static_obstacles:
                            self.spawn_explosion(obs.rect.centerx, obs.rect.centery, 
                                                 [(128, 128, 128), (80, 80, 80)], 20)
                            self.static_obstacles.remove(obs)
                            self.player.add_credits(obs.credits_value)
                            
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
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    crystal.health -= 0.5
                    self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 8)
                    if crystal.health <= 0:
                        if crystal in self.shield_crystals: self.shield_crystals.remove(crystal)
                        self.player.add_credits(40)
                        self.spawn_explosion(crystal.x, crystal.y, [(0, 255, 255), (255, 255, 255)], 25)

            if self.boss and self.boss.zone == 'AQUARIS' and not self.boss.is_dead:
                for crystal in self.boss.shield_crystals[:]:
                    if crystal.health > 0 and bullet.rect.colliderect(crystal.rect):
                        if bullet in self.bullets: self.bullets.remove(bullet)
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
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if self.boss.shielded:
                        self.spawn_explosion(bullet.x, bullet.y, [(0, 255, 255), (255, 255, 255)], 6)
                    else:
                        hit_ent.health -= 0.5
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

    def _defeat_boss(self):
        self.boss.is_dead = True
        for ent in self.boss.sub_bosses:
            for _ in range(3):
                self.spawn_explosion(ent.x + random.randint(-20, 20), ent.y + random.randint(-20, 20),
                                     [(255, 255, 0), (255, 128, 0), (255, 255, 255), (255, 0, 0)], 25)
        self.player.add_credits(300)

    def _kill_enemy(self, enemy):
        if enemy in self.enemies:
            if hasattr(enemy, 'on_death'):
                enemy.on_death(self.enemy_bullets, self.player)
            self.enemies.remove(enemy)
            self.player.add_credits(enemy.credits_value)
            if random.random() < 0.60:
                self.scraps.append(Scrap(enemy.rect.centerx, enemy.rect.centery))

    def _draw(self):
        self.virtual_screen.fill(BLACK)
        
        if self.state == 'HUB':
            for star in self.stars:
                val = math.sin(pygame.time.get_ticks() * star[5] + star[6])
                alpha = int(128 + 127 * val)
                color = tuple(max(0, min(255, int(c * (alpha / 255.0)))) for c in star[4])
                pygame.draw.circle(self.virtual_screen, color, (int(star[0]), int(star[1])), star[3])
            
            station_center = (600, 450)
            ticks = pygame.time.get_ticks()
            
            # Outer rotating shield ring
            ring_pulse = int(5 * math.sin(ticks * 0.003))
            pygame.draw.circle(self.virtual_screen, (0, 150, 255), station_center, 120 + ring_pulse, width=2)
            
            # Struts connecting inner and outer station parts
            for angle in range(0, 360, 60):
                rad = math.radians(angle + ticks * 0.01)
                sx1 = station_center[0] + int(40 * math.cos(rad))
                sy1 = station_center[1] + int(40 * math.sin(rad))
                sx2 = station_center[0] + int(110 * math.cos(rad))
                sy2 = station_center[1] + int(110 * math.sin(rad))
                pygame.draw.line(self.virtual_screen, (100, 110, 120), (sx1, sy1), (sx2, sy2), width=4)
                pygame.draw.circle(self.virtual_screen, CYAN, (sx2, sy2), 4)
                
            # Base station body
            pygame.draw.circle(self.virtual_screen, (25, 30, 40), station_center, 100)
            pygame.draw.circle(self.virtual_screen, SLATE_GRAY, station_center, 100, width=6)
            pygame.draw.circle(self.virtual_screen, (10, 15, 20), station_center, 60)
            
            # Station inner core glow
            core_pulse = 15 + int(5 * math.sin(ticks * 0.01))
            pygame.draw.circle(self.virtual_screen, (0, 200, 255), station_center, core_pulse, width=2)
            
            station_lbl = self.font.render("DOCKING BAY", True, CYAN)
            self.virtual_screen.blit(station_lbl, (600 - station_lbl.get_width() // 2, 435))
            
            player_vec = pygame.math.Vector2(self.player.rect.center)
            if player_vec.distance_to(pygame.math.Vector2(station_center)) < 120:
                dock_prompt = self.font.render("DOCKED: Press ESC or P to open Ship Upgrades Shop!", True, GREEN)
                self.virtual_screen.blit(dock_prompt, (VIRTUAL_WIDTH // 2 - dock_prompt.get_width() // 2, VIRTUAL_HEIGHT - 60))
            
            # Dynamic Portals
            glow = int(5 * math.sin(ticks * 0.005))
            for zone, cfg in BIOME_CONFIGS.items():
                if cfg['hub'] == self.current_hub_index and self.unlocked_zones.get(zone, False):
                    theme_color = cfg['theme_color']
                    dark_color = (theme_color[0] // 3, theme_color[1] // 3, theme_color[2] // 3)
                    
                    order = cfg['order']
                    if order == 0:
                        center = (600, 780)
                        lbl_y = 690
                        info_y = 660
                    elif order == 1:
                        center = (1000, 220)
                        lbl_y = 290
                        info_y = 320
                    else:
                        center = (200, 220)
                        lbl_y = 290
                        info_y = 320
                        
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
                    
                    info_text = f"({cfg['desc']})"
                    info = self.font.render(info_text, True, WHITE)
                    self.virtual_screen.blit(info, (center[0] - info.get_width() // 2, info_y))
            
            welcome_text = f"SAFE HAVEN HUB STATION - SEGMENT {self.current_hub_index}"
            welcome = self.large_font.render(welcome_text, True, WHITE)
            self.virtual_screen.blit(welcome, (VIRTUAL_WIDTH // 2 - welcome.get_width() // 2, 30))
            
            # Draw Cheat Portals for developer testing
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
                cfg = BIOME_CONFIGS.get(self.active_hub_portal)
                if cfg:
                    order = cfg['order']
                    if order == 0:
                        portal_center = (600, 780)
                    elif order == 1:
                        portal_center = (1000, 220)
                    else:
                        portal_center = (200, 220)
                    
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
            
        # ---------------- DRAW PLAYING SCROLLING COMBAT ZONE ----------------
        elif self.state in ('PLAYING', 'PAUSED', 'GAME_OVER'):
            for star in self.stars:
                star_speed = star[2]
                star_draw_y = (star[1] - self.camera_y * star_speed * 0.40) % VIRTUAL_HEIGHT
                
                val = math.sin(pygame.time.get_ticks() * star[5] + star[6])
                alpha = int(128 + 127 * val)
                color = tuple(max(0, min(255, int(c * (alpha / 255.0)))) for c in star[4])
                pygame.draw.circle(self.virtual_screen, color, (int(star[0]), int(star_draw_y)), star[3])

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
                exit_lbl = self.font.render("WORMHOLE ACTIVE (Enter to Warp)", True, GREEN)
                self.virtual_screen.blit(exit_lbl, ((self.wormhole_pos.x - self.camera_x) - exit_lbl.get_width() // 2, self.wormhole_pos.y - self.camera_y - 90))
                
                # Draw warp charging progress HUD
                if self.wormhole_charge_timer > 0:
                    target_charge = 1000.0 if self.player.skills.get('hyperdrive', 0) > 0 else 3000.0
                    pct = min(1.0, self.wormhole_charge_timer / target_charge)
                    bar_w = 200
                    bar_h = 12
                    bar_x = (self.wormhole_pos.x - self.camera_x) - bar_w // 2
                    bar_y = self.wormhole_pos.y - self.camera_y + 80
                    
                    # Background
                    pygame.draw.rect(self.virtual_screen, (44, 44, 44), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                    # Progress bar
                    pygame.draw.rect(self.virtual_screen, GREEN, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)
                    # Border
                    pygame.draw.rect(self.virtual_screen, WHITE, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)
                    
                    # Text countdown
                    secs_left = max(0.0, (target_charge - self.wormhole_charge_timer) / 1000.0)
                    charge_lbl = self.font.render(f"WARPING IN {secs_left:.1f}s... STAY INSIDE!", True, GREEN)
                    self.virtual_screen.blit(charge_lbl, ((self.wormhole_pos.x - self.camera_x) - charge_lbl.get_width() // 2, bar_y + 18))
            
            # Level Gimmicks drawing
            for crystal in self.shield_crystals:
                crystal.draw(self.virtual_screen, self.camera_y, self.camera_x)
            for gw in self.gravity_wells:
                gw.draw(self.virtual_screen, self.camera_y, self.camera_x)

            # Solar Flare visualization
            if self.current_zone == 'VULCAN' and self.solar_flare_state != 'IDLE':
                draw_fy = self.solar_flare_y - self.camera_y
                if self.solar_flare_state == 'WARNING':
                    if pygame.time.get_ticks() % 400 < 200:
                        pygame.draw.rect(self.virtual_screen, (255, 69, 0), (0, draw_fy, VIRTUAL_WIDTH, 120), width=4)
                        warn_text = self.font.render("!!! SOLAR FLARE DETECTED !!!", True, ORANGE)
                        self.virtual_screen.blit(warn_text, (VIRTUAL_WIDTH // 2 - warn_text.get_width() // 2, draw_fy + 45))
                elif self.solar_flare_state == 'ACTIVE':
                    pygame.draw.rect(self.virtual_screen, (255, 140, 0), (0, draw_fy, VIRTUAL_WIDTH, 120))
                    pygame.draw.rect(self.virtual_screen, WHITE, (0, draw_fy + 20, VIRTUAL_WIDTH, 80))
                    for _ in range(3):
                        px = random.randint(0, VIRTUAL_WIDTH)
                        py = self.solar_flare_y + random.randint(0, 120)
                        self.spawn_explosion(px, py, [(255, 69, 0), (255, 215, 0)], count=1)

            for bullet in self.bullets:
                bullet.draw(self.virtual_screen, self.camera_y, self.camera_x)
            for torpedo in self.torpedoes:
                torpedo.draw(self.virtual_screen, self.camera_y, self.camera_x)
            
            # Draw enemies with optional shield highlighting
            for enemy in self.enemies:
                enemy.draw(self.virtual_screen, self.camera_y, self.camera_x)
                if self.is_enemy_shielded(enemy):
                    draw_ey = enemy.y - self.camera_y
                    draw_ex = enemy.x - self.camera_x
                    pygame.draw.circle(self.virtual_screen, CYAN, (int(draw_ex + enemy.width // 2), int(draw_ey + enemy.height // 2)), enemy.width + 6, width=2)
                    
            for eb in self.enemy_bullets:
                eb.draw(self.virtual_screen, self.camera_y, self.camera_x)
                
            if self.boss:
                self.boss.draw(self.virtual_screen, self.camera_y, self.camera_x)
                
            for meteor in self.meteors:
                meteor.draw(self.virtual_screen, self.camera_y, self.camera_x)
            for obs in self.static_obstacles:
                obs.draw(self.virtual_screen, self.camera_y, self.camera_x)
            for mat in self.materials:
                mat.draw(self.virtual_screen, self.camera_y, self.camera_x)
            for scrap in self.scraps:
                scrap.draw(self.virtual_screen, self.camera_y, self.camera_x)
            
            self.player.draw(self.virtual_screen, self.camera_y, self.camera_x)

            # Boss incoming overlay warning
            if self.boss and not self.boss.is_dead:
                if self.boss.health == self.boss.max_health and pygame.time.get_ticks() % 1000 < 500:
                    warning_lbl = self.large_font.render("BOSS INCOMING!", True, RED)
                    self.virtual_screen.blit(warning_lbl, (VIRTUAL_WIDTH // 2 - warning_lbl.get_width() // 2, 200))

        for particle in self.particles:
            particle.draw(self.virtual_screen, self.camera_y if self.state == 'PLAYING' else 0, self.camera_x if self.state == 'PLAYING' else 0)
            
        # Draw HUD UI
        if self.state in ('PLAYING', 'PAUSED', 'GAME_OVER', 'HUB'):
            hud_bg = pygame.Surface((250, 125), pygame.SRCALPHA)
            hud_bg.fill((10, 16, 26, 150))
            pygame.draw.rect(hud_bg, (0, 255, 255, 60), (0, 0, 250, 125), width=1, border_radius=4)
            self.virtual_screen.blit(hud_bg, (5, 5))
            
            credits_text = self.font.render(f"Credits: {self.player.credits} C", True, GREEN)
            self.virtual_screen.blit(credits_text, (15, 12))
            
            scrap_text = self.font.render(f"Scrap: {self.player.scraps}", True, GOLD)
            self.virtual_screen.blit(scrap_text, (15 + credits_text.get_width() + 15, 12))
            
            zone_text = self.font.render(f"Location: {self.current_zone}", True, WHITE)
            self.virtual_screen.blit(zone_text, (15, 42))
            
            shield_lbl = self.small_font.render("SHIELDS:", True, CYAN)
            self.virtual_screen.blit(shield_lbl, (15, 72))
            
            shield_x = 15
            shield_y = 90
            segment_width = 25
            segment_height = 12
            for i in range(self.player.max_shields):
                rect = pygame.Rect(shield_x + i * (segment_width + 5), shield_y, segment_width, segment_height)
                if i < int(self.player.shields):
                    pygame.draw.rect(self.virtual_screen, CYAN, rect, border_radius=3)
                    pygame.draw.line(self.virtual_screen, WHITE, (rect.x + 2, rect.y + 2), (rect.x + rect.width - 3, rect.y + 2), width=1)
                elif i < self.player.shields:
                    fill_pct = self.player.shields - i
                    fill_w = int(segment_width * fill_pct)
                    pygame.draw.rect(self.virtual_screen, (40, 40, 40), rect, border_radius=3)
                    pygame.draw.rect(self.virtual_screen, CYAN, rect, width=1, border_radius=3)
                    if fill_w > 0:
                        part_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
                        pygame.draw.rect(self.virtual_screen, CYAN, part_rect, border_radius=3)
                        pygame.draw.line(self.virtual_screen, WHITE, (part_rect.x + 2, part_rect.y + 2), (part_rect.x + part_rect.width - 3, part_rect.y + 2), width=1)
                else:
                    pygame.draw.rect(self.virtual_screen, (40, 40, 40), rect, border_radius=3)
                    pygame.draw.rect(self.virtual_screen, CYAN, rect, width=1, border_radius=3)
            
            # ---------------- TACTICAL MINIMAP HUD (RELATIVE SCROLLING) ----------------
            if self.state == 'PLAYING':
                mm_w = 130
                mm_h = 130
                mm_x = VIRTUAL_WIDTH - mm_w - 15
                mm_y = 115
                
                pygame.draw.rect(self.virtual_screen, (10, 10, 15, 200), (mm_x, mm_y, mm_w, mm_h), border_radius=4)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, (mm_x, mm_y, mm_w, mm_h), width=2, border_radius=4)
                
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
                
                core_label = self.small_font.render(f"CORES: {self.materials_collected}/5", True, WHITE)
                self.virtual_screen.blit(core_label, (mm_x, mm_y + mm_h + 8))

            # Screen-edge Radar for off-screen cores
            if self.state == 'PLAYING' and self.materials:
                player_pos = pygame.math.Vector2(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2)
                closest_core = None
                min_dist = float('inf')
                for mat in self.materials:
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

            if self.state == 'PLAYING':
                panel_w = 280
                panel_h = 100
                panel_x = VIRTUAL_WIDTH - panel_w - 5
                panel_y = 5
                
                hud_bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                hud_bg.fill((10, 16, 26, 150))
                pygame.draw.rect(hud_bg, (0, 255, 255, 60), (0, 0, panel_w, panel_h), width=1, border_radius=4)
                self.virtual_screen.blit(hud_bg, (panel_x, panel_y))
                
                bar_width = 120
                bar_height = 8
                bar_x = panel_x + panel_w - bar_width - 15
                current_time = pygame.time.get_ticks()
                
                # Torpedo
                actual_torpedo_delay = self.player.torpedo_delay * (1.0 - 0.15 * self.player.skills['torpedo'])
                time_since_torpedo = current_time - self.player.last_torpedo
                cooldown_ratio = min(1.0, time_since_torpedo / actual_torpedo_delay)
                
                torpedo_y = panel_y + 18
                pygame.draw.rect(self.virtual_screen, (30, 40, 50), (bar_x, torpedo_y, bar_width, bar_height), border_radius=2)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, (bar_x, torpedo_y, bar_width, bar_height), width=1, border_radius=2)
                fill_width = int(bar_width * cooldown_ratio)
                fill_color = (0, 255, 100) if cooldown_ratio == 1.0 else (255, 150, 0)
                pygame.draw.rect(self.virtual_screen, fill_color, (bar_x, torpedo_y, fill_width, bar_height), border_radius=2)
                
                torpedo_label = self.small_font.render("TORPEDO CAP:", True, WHITE if cooldown_ratio == 1.0 else (180, 180, 180))
                self.virtual_screen.blit(torpedo_label, (panel_x + 15, torpedo_y - 4))
                
                # Laser Heat
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
                
                heat_label_text = "OVERHEAT!" if self.player.overheated else "LASER HEAT:"
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

            # Solar Radiation zone warnings
            if self.state == 'PLAYING' and (self.player.x < -2000 or self.player.x > VIRTUAL_WIDTH + 2000 - self.player.width):
                if not self.player.is_dead:
                    rad_text = self.large_font.render("CRITICAL RADIATION DETECTED", True, RED)
                    sub_text = self.font.render("WARNING: SOLAR FLARES ACTIVE IN DEEP SPACE. TURN BACK!", True, ORANGE)
                    
                    if pygame.time.get_ticks() % 600 < 300:
                        self.virtual_screen.blit(rad_text, (VIRTUAL_WIDTH // 2 - rad_text.get_width() // 2, VIRTUAL_HEIGHT // 2 - 120))
                    
                    self.virtual_screen.blit(sub_text, (VIRTUAL_WIDTH // 2 - sub_text.get_width() // 2, VIRTUAL_HEIGHT // 2 - 50))
                    
                    pulse_alpha = int(40 + 35 * math.sin(pygame.time.get_ticks() * 0.01))
                    vignette = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.rect(vignette, (255, 0, 0, pulse_alpha), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT), width=30)
                    self.virtual_screen.blit(vignette, (0, 0))

            # Boss approaching warning overlay
            if self.boss and getattr(self.boss, 'appearance_timer', 0) > 0 and not self.boss.is_dead:
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

        # Main Menu overlay
        if self.state == 'MAIN_MENU':
            grid_spacing = 40
            grid_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            for gx_line in range(0, VIRTUAL_WIDTH, grid_spacing):
                pygame.draw.line(grid_surf, (0, 255, 255, 15), (gx_line, 0), (gx_line, VIRTUAL_HEIGHT))
            for gy_line in range(0, VIRTUAL_HEIGHT, grid_spacing):
                pygame.draw.line(grid_surf, (0, 255, 255, 15), (0, gy_line), (VIRTUAL_WIDTH, gy_line))
            scan_y = (pygame.time.get_ticks() // 4) % VIRTUAL_HEIGHT
            pygame.draw.line(grid_surf, (0, 255, 255, 35), (0, scan_y), (VIRTUAL_WIDTH, scan_y), width=2)
            self.virtual_screen.blit(grid_surf, (0, 0))
            
            border_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (0, 255, 255, 60), (10, 10, VIRTUAL_WIDTH - 20, VIRTUAL_HEIGHT - 20), width=2, border_radius=12)
            pygame.draw.rect(border_surf, (0, 255, 255, 25), (15, 15, VIRTUAL_WIDTH - 30, VIRTUAL_HEIGHT - 30), width=1, border_radius=10)
            self.virtual_screen.blit(border_surf, (0, 0))
            
            preview_y = VIRTUAL_HEIGHT // 2 - 120
            self.player.x = VIRTUAL_WIDTH // 2 - self.player.width // 2
            self.player.y = preview_y
            self.player.draw(self.virtual_screen, camera_y=0)
            
            pulse = math.sin(pygame.time.get_ticks() * 0.005)
            title_shadow = self.large_font.render("NEBULON RPG", True, (0, 30, 40))
            self.virtual_screen.blit(title_shadow, title_shadow.get_rect(center=(VIRTUAL_WIDTH // 2 + 4, VIRTUAL_HEIGHT // 2 - 198)))
            
            title_color = (int(128 + 127 * pulse), 255, 255)
            title = self.large_font.render("NEBULON RPG", True, title_color)
            title_rect = title.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 200))
            self.virtual_screen.blit(title, title_rect)
            
            prompt_color = WHITE if pygame.time.get_ticks() % 1000 < 500 else CYAN
            prompt = self.font.render("Press SPACE or ENTER to Enter Hub World", True, prompt_color)
            prompt_rect = prompt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))
            self.virtual_screen.blit(prompt, prompt_rect)
            
            controls_box = pygame.Rect(VIRTUAL_WIDTH // 2 - 260, VIRTUAL_HEIGHT // 2 + 60, 520, 260)
            box_surf = pygame.Surface((controls_box.width, controls_box.height), pygame.SRCALPHA)
            box_surf.fill((10, 20, 30, 180))
            pygame.draw.rect(box_surf, (0, 255, 255, 100), (0, 0, controls_box.width, controls_box.height), width=2, border_radius=8)
            self.virtual_screen.blit(box_surf, (controls_box.x, controls_box.y))
            
            controls_title = self.font.render("CONTROLS & HOW TO PLAY:", True, CYAN)
            self.virtual_screen.blit(controls_title, (controls_box.x + 20, controls_box.y + 15))
            
            controls = [
                "W/S (or UP/DOWN)   : Thrust Forward / Reverse",
                "A/D (or L/R keys)  : Evade Dash (on Cooldown)",
                "MOUSE MOVEMENT     : Aim / Rotate Ship",
                "LEFT MOUSE CLICK   : Shoot Laser (In Combat)",
                "RIGHT MOUSE CLICK  : Heavy Torpedo (In Combat)",
                "GOAL: Fly UP, Collect 5 Cores & Warp Out",
                "P / ESCAPE KEY     : Open Upgrades at Space Station"
            ]
            for idx, text in enumerate(controls):
                ctrl_txt = self.small_font.render(text, True, (220, 240, 255))
                self.virtual_screen.blit(ctrl_txt, (controls_box.x + 20, controls_box.y + 50 + idx * 26))

        # Pause Menu with Ship Upgrades Shop
        elif self.state == 'PAUSED':
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.virtual_screen.blit(overlay, (0, 0))
            
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
            
            resume = self.font.render("Press ESC or P to Resume", True, WHITE)
            self.virtual_screen.blit(resume, (100, 350))
            
            quit_lbl = self.font.render("Press M to Quit to Main Menu", True, RED)
            self.virtual_screen.blit(quit_lbl, (100, 410))
            
            pygame.draw.line(self.virtual_screen, SLATE_GRAY, (600, 150), (600, 800), 2)
            
            if self.current_zone != 'HUB':
                tree_title = self.large_font.render("UPGRADES LOCKED", True, RED)
                self.virtual_screen.blit(tree_title, (650, 250))
                
                sp_text = self.font.render("Ship upgrades are only available at the Space Station Hub.", True, WHITE)
                self.virtual_screen.blit(sp_text, (650, 330))
                
                wallet_lbl1 = self.font.render(f"Wallet: {self.player.credits} Credits", True, GREEN)
                self.virtual_screen.blit(wallet_lbl1, (650, 380))
                wallet_lbl2 = self.font.render(f"  |  {self.player.scraps} Scrap", True, GOLD)
                self.virtual_screen.blit(wallet_lbl2, (650 + wallet_lbl1.get_width(), 380))
                
                hint_lbl = self.small_font.render("Safely return to Hub via Warp Portals to upgrade equipment.", True, YELLOW)
                self.virtual_screen.blit(hint_lbl, (650, 430))
            else:
                tree_title = self.large_font.render("SHIP PARTS SHOP", True, CYAN)
                self.virtual_screen.blit(tree_title, (650, 100))
                
                sp_text1 = self.font.render(f"Your Wallet: {self.player.credits} Credits", True, GREEN)
                self.virtual_screen.blit(sp_text1, (650, 175))
                sp_text2 = self.font.render(f"  |  {self.player.scraps} Scrap", True, GOLD)
                self.virtual_screen.blit(sp_text2, (650 + sp_text1.get_width(), 175))
                
                # Recalculate mouse positions using letterbox scale
                mx, my = pygame.mouse.get_pos()
                vmx = (mx - self.offset_x) * (VIRTUAL_WIDTH / self.new_width)
                vmy = (my - self.offset_y) * (VIRTUAL_HEIGHT / self.new_height)
                
                # Define Tech Tree nodes
                nodes_info = {
                    'shield': {
                        'name': 'Shield Generator',
                        'desc': 'Upgrade hull capacitors to absorb more energy (+1 Max Shield per rank).',
                        'col': 1, 'row': 1, 'max_level': 4,
                        'cost': (self.player.skills['shield'] + 1) * 75,
                        'scrap_cost': (self.player.skills['shield'] + 1) * 2,
                        'deps': []
                    },
                    'deflector': {
                        'name': 'Deflector Shield',
                        'desc': 'Unlock a passive shield deflector that reduces shield recharge delay from 5s to 3s.',
                        'col': 2, 'row': 1, 'max_level': 1,
                        'cost': 200,
                        'scrap_cost': 5,
                        'deps': [('shield', 2)]
                    },
                    'coolant': {
                        'name': 'Thermal Coolant',
                        'desc': 'Install cryogenic liquid heatsinks (+25% faster weapon cool-down rate per rank).',
                        'col': 1, 'row': 2, 'max_level': 4,
                        'cost': (self.player.skills['coolant'] + 1) * 60,
                        'scrap_cost': (self.player.skills['coolant'] + 1) * 2,
                        'deps': []
                    },
                    'weapon': {
                        'name': 'Multi-Cannon',
                        'desc': 'Modify weapon mount slots to unlock fire configurations (Dual -> Spreading Triple).',
                        'col': 2, 'row': 2, 'max_level': 2,
                        'cost': 200 if self.player.skills['weapon'] == 0 else 400,
                        'scrap_cost': 8 if self.player.skills['weapon'] == 0 else 15,
                        'deps': [('coolant', 1)]
                    },
                    'overcharge': {
                        'name': 'Overcharged Cap',
                        'desc': 'Overclock gun firing rate (reduces standard laser shoot delay by 30%).',
                        'col': 3, 'row': 2, 'max_level': 1,
                        'cost': 250,
                        'scrap_cost': 8,
                        'deps': [('weapon', 1)]
                    },
                    'torpedo': {
                        'name': 'Fusion Torpedo',
                        'desc': 'Upgrade heavy torpedo systems (-15% cooldown and +15% explosion size per rank).',
                        'col': 1, 'row': 3, 'max_level': 4,
                        'cost': (self.player.skills['torpedo'] + 1) * 80,
                        'scrap_cost': (self.player.skills['torpedo'] + 1) * 2,
                        'deps': []
                    },
                    'cluster_torpedo': {
                        'name': 'Cluster Warhead',
                        'desc': 'Modify torpedo shell casings to trigger 3 smaller secondary sub-explosions upon detonation.',
                        'col': 2, 'row': 3, 'max_level': 1,
                        'cost': 300,
                        'scrap_cost': 10,
                        'deps': [('torpedo', 2)]
                    },
                    'hyperdrive': {
                        'name': 'Hyperdrive Core',
                        'desc': 'Assemble hyper-dense tachyonic fields to speed up warp charging (reduces warp delay from 3s to 1s).',
                        'col': 1, 'row': 4, 'max_level': 1,
                        'cost': 350,
                        'scrap_cost': 12,
                        'deps': [('shield', 2), ('coolant', 2)]
                    }
                }

                hovered_key = None
                for key, node in nodes_info.items():
                    node_x = 630 + (node['col'] - 1) * 180
                    node_y = 210 + (node['row'] - 1) * 100
                    rect = pygame.Rect(node_x, node_y, 160, 80)
                    if rect.collidepoint(vmx, vmy):
                        hovered_key = key
                        
                # 1. Draw dependency lines first
                for key, node in nodes_info.items():
                    node_x = 630 + (node['col'] - 1) * 180
                    node_y = 210 + (node['row'] - 1) * 100
                    
                    for dep_key, req_lvl in node['deps']:
                        dep_node = nodes_info[dep_key]
                        dep_x = 630 + (dep_node['col'] - 1) * 180
                        dep_y = 210 + (dep_node['row'] - 1) * 100
                        
                        met = self.player.skills[dep_key] >= req_lvl
                        line_color = GREEN if met else (100, 30, 30)
                        
                        if dep_node['col'] == node['col']:
                            # Vertical connection
                            start_pos = (dep_x + 80, dep_y + 80)
                            end_pos = (node_x + 80, node_y)
                        else:
                            # Horizontal or diagonal connection
                            start_pos = (dep_x + 160, dep_y + 40)
                            end_pos = (node_x, node_y + 40)
                            
                        pygame.draw.line(self.virtual_screen, line_color, start_pos, end_pos, width=3)
                        
                        mid_x = (start_pos[0] + end_pos[0]) // 2
                        mid_y = (start_pos[1] + end_pos[1]) // 2
                        pygame.draw.circle(self.virtual_screen, line_color, (mid_x, mid_y), 4)

                # 2. Draw nodes
                for key, node in nodes_info.items():
                    node_x = 630 + (node['col'] - 1) * 180
                    node_y = 210 + (node['row'] - 1) * 100
                    rect = pygame.Rect(node_x, node_y, 160, 80)
                    
                    unlocked = True
                    for dep_key, req_lvl in node['deps']:
                        if self.player.skills[dep_key] < req_lvl:
                            unlocked = False
                            break
                    
                    curr_lvl = self.player.skills[key]
                    is_max = curr_lvl >= node['max_level']
                    
                    bg_color = (25, 25, 30)
                    border_color = SLATE_GRAY
                    border_width = 1
                    
                    if not unlocked:
                        bg_color = (40, 15, 15)
                        border_color = (180, 50, 50)
                    elif is_max:
                        bg_color = (15, 40, 15)
                        border_color = (50, 200, 50)
                        border_width = 2
                    elif rect.collidepoint(vmx, vmy):
                        bg_color = (40, 40, 50)
                        border_color = CYAN
                        border_width = 2
                    elif curr_lvl > 0:
                        border_color = CYAN
                    
                    pygame.draw.rect(self.virtual_screen, bg_color, rect, border_radius=6)
                    pygame.draw.rect(self.virtual_screen, border_color, rect, width=border_width, border_radius=6)
                    
                    title_lbl = render_fit_text(node['name'], WHITE if unlocked else (180, 120, 120), 140, base_font_size=15)
                    self.virtual_screen.blit(title_lbl, (node_x + 10, node_y + 12))
                    
                    rank_lbl = self.small_font.render(f"Rank: {curr_lvl}/{node['max_level']}", True, YELLOW if unlocked else (160, 160, 160))
                    self.virtual_screen.blit(rank_lbl, (node_x + 10, node_y + 35))
                    
                    if not unlocked:
                        cost_text = "LOCKED"
                        cost_color = RED
                        cost_lbl = self.small_font.render(cost_text, True, cost_color)
                        self.virtual_screen.blit(cost_lbl, (node_x + 10, node_y + 55))
                    elif is_max:
                        cost_text = "MAXED"
                        cost_color = GREEN
                        cost_lbl = self.small_font.render(cost_text, True, cost_color)
                        self.virtual_screen.blit(cost_lbl, (node_x + 10, node_y + 55))
                    else:
                        # Render Credits cost
                        credits_color = GREEN if self.player.credits >= node['cost'] else ORANGE
                        credits_lbl = self.small_font.render(f"{node['cost']} C", True, credits_color)
                        self.virtual_screen.blit(credits_lbl, (node_x + 10, node_y + 55))
                        
                        # Render Scrap cost
                        scrap_color = GOLD if self.player.scraps >= node['scrap_cost'] else (200, 100, 50)
                        scrap_lbl = self.small_font.render(f"{node['scrap_cost']} Scrap", True, scrap_color)
                        self.virtual_screen.blit(scrap_lbl, (node_x + 10 + credits_lbl.get_width() + 10, node_y + 55))

                # 3. Draw tooltip area at the bottom
                tooltip_rect = pygame.Rect(630, 620, 520, 180)
                pygame.draw.rect(self.virtual_screen, (15, 15, 20), tooltip_rect, border_radius=8)
                pygame.draw.rect(self.virtual_screen, SLATE_GRAY, tooltip_rect, width=1, border_radius=8)
                
                if hovered_key is not None:
                    hovered = nodes_info[hovered_key]
                    name_lbl = self.font.render(hovered['name'].upper(), True, CYAN)
                    self.virtual_screen.blit(name_lbl, (650, 635))
                    
                    desc_text = hovered['desc']
                    words = desc_text.split(' ')
                    line1, line2 = "", ""
                    for w in words:
                        if len(line1 + w) < 48:
                            line1 += w + " "
                        else:
                            line2 += w + " "
                    
                    desc1_lbl = self.small_font.render(line1.strip(), True, WHITE)
                    self.virtual_screen.blit(desc1_lbl, (650, 675))
                    if line2:
                        desc2_lbl = self.small_font.render(line2.strip(), True, WHITE)
                        self.virtual_screen.blit(desc2_lbl, (650, 698))
                    
                    if hovered['deps']:
                        rx_draw = 650
                        ry_draw = 730
                        req_label = self.small_font.render("Requires: ", True, WHITE)
                        self.virtual_screen.blit(req_label, (rx_draw, ry_draw))
                        rx_draw += req_label.get_width()
                        
                        for idx, (dep_key, req_lvl) in enumerate(hovered['deps']):
                            dep_name = nodes_info[dep_key]['name']
                            met = self.player.skills[dep_key] >= req_lvl
                            color = GREEN if met else RED
                            sep = ", " if idx < len(hovered['deps']) - 1 else ""
                            req_lbl = self.small_font.render(f"{dep_name} (Rank {req_lvl}+){sep}", True, color)
                            self.virtual_screen.blit(req_lbl, (rx_draw, ry_draw))
                            rx_draw += req_lbl.get_width()
                    else:
                        req_lbl = self.small_font.render("Requirements: None", True, GREEN)
                        self.virtual_screen.blit(req_lbl, (650, 730))
                else:
                    help_lbl = self.font.render("HOVER OVER A TECH NODE TO VIEW SPECIFICATIONS.", True, SLATE_GRAY)
                    help_rect = help_lbl.get_rect(center=(630 + 260, 620 + 90))
                    self.virtual_screen.blit(help_lbl, help_rect)

        # Game Over Overlay
        elif self.state == 'GAME_OVER':
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.virtual_screen.blit(overlay, (0, 0))
            
            msg = self.large_font.render("GAME OVER", True, RED)
            msg_rect = msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 50))
            self.virtual_screen.blit(msg, msg_rect)
            
            retry_msg = self.font.render("Press R to Restart", True, WHITE)
            retry_rect = retry_msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 50))
            self.virtual_screen.blit(retry_msg, retry_rect)
            
            menu_msg = self.font.render("Press M for Main Menu", True, CYAN)
            menu_rect = menu_msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 100))
            self.virtual_screen.blit(menu_msg, menu_rect)
            
        # Victory Overlay
        elif self.state == 'VICTORY':
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 20, 40, 200)) # Dark blue-ish background
            self.virtual_screen.blit(overlay, (0, 0))
            
            # Spawn some victory sparks/fireworks dynamically for rich aesthetics!
            for _ in range(5):
                fx = random.randint(0, VIRTUAL_WIDTH)
                fy = random.randint(0, VIRTUAL_HEIGHT)
                fcolor = random.choice([CYAN, GREEN, YELLOW, ORANGE, PURPLE])
                pygame.draw.circle(self.virtual_screen, fcolor, (fx, fy), random.randint(3, 10))
            
            msg = self.large_font.render("VICTORY", True, GREEN)
            msg_rect = msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 80))
            self.virtual_screen.blit(msg, msg_rect)
            
            congrats_msg1 = self.font.render("ALL BIOMES SECURED & HARVESTED!", True, WHITE)
            congrats_rect1 = congrats_msg1.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 10))
            self.virtual_screen.blit(congrats_msg1, congrats_rect1)
            
            congrats_msg2 = self.small_font.render("You conquered the Asteroids, Vulcan, and the glacial depths of Aquaris!", True, CYAN)
            congrats_rect2 = congrats_msg2.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 30))
            self.virtual_screen.blit(congrats_msg2, congrats_rect2)
            
            retry_msg = self.font.render("Press R to Play Again", True, WHITE)
            retry_rect = retry_msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 100))
            self.virtual_screen.blit(retry_msg, retry_rect)
            
            menu_msg = self.font.render("Press M for Main Menu", True, YELLOW)
            menu_rect = menu_msg.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 150))
            self.virtual_screen.blit(menu_msg, menu_rect)
            
        # ASPECT-RATIO LETTERBOX SCALING (Prevents stretching & distortion of text/images)
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
            
        scaled_screen = pygame.transform.scale(self.virtual_screen, (self.new_width, self.new_height))
        self.screen.fill(BLACK)
        bx = self.offset_x
        by = self.offset_y
        if self.screen_shake > 0:
            bx += random.randint(-self.screen_shake, self.screen_shake)
            by += random.randint(-self.screen_shake, self.screen_shake)
            self.screen_shake = max(0, self.screen_shake - 1)
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
