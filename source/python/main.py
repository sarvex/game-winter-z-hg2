# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                   WinterZ - Main module

#           Original created by Wizital (Jerôme Sentex)

# ===========================================================

import harfang as hg
from math import sin, radians, pi
from random import uniform, random
from ScreenModeRequester import *


# ===================================================================================================

#   Classes

# ===================================================================================================

class Main:
	# Display settings:
	plus = None
	original_resolution = hg.Vec2(455, 256)
	resolution = hg.Vec2(1280, 720)
	game_scale = resolution.y / original_resolution.y
	antialiasing = 0

	# --- Sprites:
	sprites = []
	ship = None
	flames = None

	# --- Game parameters:
	scrolls_x = [0] * 10
	scrolling_speed = 0
	distance_min = 26 * 3.5
	num_doors = 4
	num_pillars_bottom = 16
	doors_counter = 0
	pillars_doors = []
	pillars_bottom = []
	animations = []
	game_speed = {"easy": 0.8, "normal": 1.0, "hard": 1.1}
	collision_accuracy = {"easy": 0.5, "normal": 0.75, "hard": 1.0}
	difficulty_level = "normal"

	score = 0
	score_max = 0

	delta_t = 0

	# --- Flash:
	collision_time = 0
	flash_delay = 0.5

	# --- Sfx:
	audio = None
	sounds = {}


class Sprite:

	z_depth = 100
	vtx_layout = None
	@classmethod
	def createvtxlayout(cls):
		cls.vtx_layout = hg.VertexLayoutPosFloatTexCoord0UInt8()


	def __init__(self, fileName, scale, center=None):
		self.color = hg.Color.White
		self.position = hg.Vec2(0, 0)
		self.position_prec = hg.Vec2(0, 0)
		self.vertices = hg.Vertices(Sprite.vtx_layout, 4)
		self.texture, self.textureinfo = hg.LoadTextureFromAssets(fileName, hg.TF_UClamp | hg.TF_VClamp | hg.TF_SamplerMinPoint | hg.TF_SamplerMagPoint)
		print("width: ", self.textureinfo.width, "height: ", self.textureinfo.height)
		self.scale = scale
		if center is None:
			self.center = hg.Vec2(self.textureinfo.width // 2, self.textureinfo.height // 2)
		else:
			self.center = hg.Vec2(center)

	def draw(self, position=None, color=None):
		self.draw_rot(0, position, color)

	def draw_rot(self, angle=0, position=None, color=None):
		if position is None:
			position = self.position
		if color is None:
			color = self.color
		w, h = self.textureinfo.width, self.textureinfo.height
		# Rotate:
		p0 = self.center * -1
		p1 = p0 + hg.Vec2(w, h)
		Sprite.z_depth -= 0.1

		mat = hg.TransformationMat4(
			hg.Vec3(position.x * Main.resolution.x, position.y * Main.resolution.y, 0), hg.Vec3(0, 0, angle),
			hg.Vec3(self.scale, self.scale, 1))

		self.vertices.Clear()
		self.vertices.Begin(0).SetPos(mat * hg.Vec3(p0.x, p0.y, Sprite.z_depth)).SetTexCoord0(hg.Vec2(0, 1)).End()
		self.vertices.Begin(1).SetPos(mat * hg.Vec3(p0.x, p1.y, Sprite.z_depth)).SetTexCoord0(hg.Vec2(0, 0)).End()
		self.vertices.Begin(2).SetPos(mat * hg.Vec3(p1.x, p1.y, Sprite.z_depth)).SetTexCoord0(hg.Vec2(1, 0)).End()
		self.vertices.Begin(3).SetPos(mat * hg.Vec3(p1.x, p0.y, Sprite.z_depth)).SetTexCoord0(hg.Vec2(1, 1)).End()
		quad_idx = [0, 3, 2, 0, 2, 1]

		# Display:
		uniformvalues = hg.MakeUniformSetValue("color", hg.Vec4(color.r, color.g, color.b, color.a))
		hg.DrawTriangles(0, quad_idx, self.vertices, shader_texture, [uniformvalues], [hg.MakeUniformSetTexture("s_texTexture", self.texture, 0)], render_state_quad)


	def set_center(self, cx, cy):
		self.center.x, self.center.y = cx, cy

	def get_width(self):
		return self.textureinfo.width

	def get_height(self):
		return self.textureinfo.height


class SpriteAnimator:
	def __init__(self, sprite: Sprite, end_position: hg.Vec2, end_color=hg.Color.White, start_delay=0,
				 duration=0.25):
		self.sprite = sprite
		self.start_position = hg.Vec2(sprite.position)
		self.start_color = sprite.color
		self.end_color = end_color
		self.end_position = end_position
		self.duration = duration
		self.start_delay = start_delay
		self.start_date = -1

	def update_animation(self, time):

		# Start animation:
		if self.start_date < 0:
			self.start_date = time
			return True

		# Interpolate position / orientation / color:
		if self.start_date + self.start_delay < time:
			if self.start_date + self.duration + self.start_delay > time:
				tl = (time - self.start_date - self.start_delay) / self.duration
				t = pow(sin(tl * pi / 2), 4)
				self.sprite.position = (self.start_position * (1 - t) + self.end_position * t)
				self.sprite.color = hg.Color(self.start_color * (1 - tl) + self.end_color * tl)
				return True

			# End of animation:
			else:
				return False
		else:
			return True


class SpriteInstance:
	def __init__(self, sprite, position=hg.Vec2.Zero):
		self.sprite = sprite
		self.position = hg.Vec2(position)

	def draw(self):
		self.sprite.draw(self.position)


class Ship:
	def __init__(self, frames):
		self.position = hg.Vec2(1 / 3, 0)
		self.frames = frames
		self.angle = 0
		self.frame = 0
		self.y_speed = 0
		self.gravity = 4
		self.booster_delay = 0.25
		self.booster_counter = 0
		self.is_broken = False
		self.broken_face = False
		self.width = 32
		self.height = 16

	def inc_frame(self):
		self.frame = (self.frame + 1) % 4

	def draw(self, ):
		self.frames[self.frame].draw_rot(self.angle, self.position)

	def start_booster(self):
		self.booster_counter = self.booster_delay
		self.y_speed = 1

	def waiting(self):
		self.inc_frame()
		self.position.y = 0.67 + convy(5) * sin(hg.time_to_sec_f(hg.GetClock()) * 4)

	def update_kinetic(self):
		# Sprite animation:
		if self.booster_counter > 0:
			self.booster_counter -= Main.delta_t
			self.inc_frame()
		else:
			self.frame = 0

		# Gravity and ground clamp:
		if self.position.y > convx(80):
			self.y_speed -= self.gravity * Main.delta_t
			self.position.y += self.y_speed * Main.delta_t
		else:
			self.position.y = convx(80)

		# Rotation:
		angle_max = 30
		self.angle = radians(max(min(self.y_speed * angle_max, angle_max), -angle_max))

	def reset(self):
		self.y_speed = 0
		self.is_broken = False
		self.broken_face = False
		self.angle = 0


class Particle:
	def __init__(self):
		self.position = None
		self.angle = 0
		self.color = None
		self.age = -1
		self.scale = 1
		self.x_speed = 0


class ParticlesEngine:
	def __init__(self, sprite):
		self.particles_cnt = 0
		self.particles_cnt_f = 0
		self.sprite = sprite
		self.main_scale = sprite.scale
		self.start_scale = 0.5
		self.end_scale = 1
		self.num_particles = 24
		self.flames_delay = 1
		self.flow = 8
		self.particles_delay = 3
		self.y_speed = 0.2
		self.particles = []
		self.min_scale = 0.75
		self.max_scale = 1.25

	def reset(self):
		self.particles_cnt = 0
		self.particles_cnt_f = 0
		self.particles = []
		self.particles.extend(Particle() for _ in range(self.num_particles))

	def draw(self, position, scrool_x_speed):
		if Main.collision_time < self.flames_delay:
			f = Main.collision_time / self.flames_delay
			color = hg.Color(hg.Color.White * 1 - f + hg.Color.Black * f)
			self.min_scale = 1
			self.max_scale = 3
		else:
			color = hg.Color(hg.Color.Black)
			self.min_scale = 0.75
			self.max_scale = 1.25

		self.particles_cnt_f += Main.delta_t * self.flow
		n = int(self.particles_cnt_f) - self.particles_cnt
		if n > 0:
			for i in range(n):
				particle = self.particles[(self.particles_cnt + i) % self.num_particles]
				particle.scale = uniform(self.min_scale, self.max_scale)
				particle.color = color
				particle.color.a = max(0.5, 1 - (particle.scale - self.min_scale) / (self.max_scale - self.min_scale))
				particle.age = 0
				particle.position = hg.Vec2(position)

				particle.x_speed = uniform(-0.02, 0.02)
			self.particles_cnt += n

		for particle in self.particles:
			if 0 <= particle.age < self.particles_delay:
				particle.position.y += Main.delta_t * self.y_speed
				particle.position.x += scrool_x_speed + particle.x_speed * Main.delta_t
				particle.angle -= 1.8 * Main.delta_t
				particle.age += Main.delta_t
				t = particle.age / self.particles_delay
				self.sprite.scale = self.main_scale * particle.scale * (self.start_scale * (1 - t) + self.end_scale * t)
				color = hg.Color(particle.color)
				color.a *= (1 - t)
				self.sprite.draw_rot(particle.angle, particle.position, color)


# ===================================================================================================

#   Functions

# ===================================================================================================

def convx(x):
	return x * Main.game_scale / Main.resolution.x


def convy(y):
	return y * Main.game_scale / Main.resolution.y


def init_game():
	# --- Sprites:
	init_sprites()

	Main.ship = Ship(Main.sprites["ship"])
	Main.flames = ParticlesEngine(Main.sprites["explode"])

	# --- Sfx:
	Main.sounds = {"collision": hg.LoadWAVSoundAsset("pipecollision.wav"),
	 			   "crash": hg.LoadWAVSoundAsset("crash.wav"),
	 			   "checkpoint": hg.LoadWAVSoundAsset("pipe.wav"),
	 			   "thrust": hg.LoadWAVSoundAsset("thrust.wav")}

	# --- Game parameters:
	Main.scrolls_x = [0] * 10
	Main.distance_min = 26 * 3
	Main.num_doors = 4
	Main.num_pillars_bottom = 16


def start_ambient_sound():
	sound = hg.LoadWAVSoundAsset("winterZ.wav")
	hg.PlayStereo(sound, hg.StereoSourceState(1, hg.SR_Loop))



def init_sprites():
	Sprite.createvtxlayout()
	Main.sprites = {"ship": [], "numbers": [], "min_numbers": [], "pillars": [], "parallaxes": [], "vapors": [],
					"background": Sprite("bg4_16_9.png", Main.game_scale, hg.Vec2(0, 0)),
					"flag": Sprite("checkpoint.png", Main.game_scale, hg.Vec2(5, 0)),
					"explode": Sprite("boom2.png", Main.game_scale),
					"title": Sprite("title_x2.png", Main.game_scale),
					"get_ready": Sprite("getready.png", Main.game_scale),
					"explain": Sprite("explain_space.png", Main.game_scale),
					"gameover": Sprite("gameover.png", Main.game_scale),
					"panel": Sprite("panel.png", Main.game_scale),
					"difficulty_level":{"easy":Sprite("level_easy.png", Main.game_scale),
										"normal": Sprite("level_normal.png", Main.game_scale),
										"hard": Sprite("level_hard.png", Main.game_scale)
										}
					}
	# Ship frames:
	for n in range(4):
		Main.sprites["ship"].append(
			Sprite(f"ship_{str(n)}.png", Main.game_scale, hg.Vec2(28, 20))
		)

	# Numbers font:
	for n in range(10):
		Main.sprites["numbers"].append(Sprite(f"{str(n)}.png", Main.game_scale))
		Main.sprites["min_numbers"].append(Sprite(f"min{str(n)}.png", Main.game_scale))

	# Pillars:
	for n in range(4):
		Main.sprites["pillars"].append(
			Sprite(f"pillar_{str(n)}.png", Main.game_scale, hg.Vec2(0, 0))
		)

	# Parallaxes:
	for key in ["front2bottom", "front2top", "front1bottom", "front1top", "ground", "bg1", "bg2", "bg3", "bg3b"]:
		Main.sprites["parallaxes"].append(
			Sprite(f"{key}.png", Main.game_scale, hg.Vec2(0, 0))
		)

	# Vapors:
	for key in ["vapor0", "vapor1"]:
		Main.sprites["vapors"].append(Sprite(f"{key}.png", Main.game_scale))

def draw_flash():
	Main.collision_time += Main.delta_t
	if Main.collision_time < Main.flash_delay:
		f = Main.collision_time / Main.flash_delay
		color = hg.Color(1, 1, 1, 1 - f)
		#Main.plus.Quad2D(0, 0, 0, Main.resolution.y, Main.resolution.x, Main.resolution.y, Main.resolution.x, 0, color,
						 #color, color, color)


def draw_score():
	digits = [int(x) for x in list(str(Main.score))]
	total_width = sum(
		Main.sprites['numbers'][digit].get_width() for digit in digits
	)
	x_offset = 0.5 - convx(total_width) / 2

	for digit in digits:
		Main.sprites["numbers"][digit].draw(hg.Vec2(x_offset, convy(216)))
		x_offset += convx(Main.sprites['numbers'][digit].get_width())


def draw_score_panel():
	score_digits = [int(x) for x in list(str(Main.score))]
	score_max_digits = [int(x) for x in list(str(Main.score_max))]
	score_digits.reverse()
	score_max_digits.reverse()
	pos = Main.sprites["panel"].position
	y_score = pos.y + convy(2)
	y_score_max = pos.y + convy(-18)

	x = pos.x + convx(51)
	for digit in score_digits:
		x -= convx(Main.sprites['min_numbers'][digit].get_width())
		Main.sprites["min_numbers"][digit].draw(hg.Vec2(x, y_score))

	x = pos.x + convx(51)
	for digit in score_max_digits:
		x -= convx(Main.sprites['min_numbers'][digit].get_width())
		Main.sprites["min_numbers"][digit].draw(hg.Vec2(x, y_score_max))


def reset_pillars():
	Main.pillars_doors = []
	x = Main.original_resolution.x
	for _ in range(Main.num_doors):
		x += (Main.original_resolution.x + 26) / Main.num_doors
		Main.pillars_doors.append(SpriteInstance(Main.sprites["pillars"][int(uniform(0, 4))], hg.Vec2(convx(x), 0)))
		Main.pillars_doors.append(SpriteInstance(Main.sprites["pillars"][int(uniform(0, 4))], hg.Vec2(convx(x), 0)))
		random_pillars_doors_y(Main.pillars_doors[-2], Main.pillars_doors[-1])

	Main.pillars_bottom = []
	x = Main.original_resolution.x
	for _ in range(Main.num_pillars_bottom):
		x += (Main.original_resolution.x + 26) / Main.num_pillars_bottom
		Main.pillars_bottom.append(SpriteInstance(Main.sprites["pillars"][int(uniform(0, 4))], hg.Vec2(convx(x), 0)))
		Main.pillars_bottom[-1].position.y = random_pillar_bottom_y()


def random_pillar_bottom_y():
	return convy(uniform(-80, - 20))


def random_pillars_doors_y(pillar_top, pillar_bottom):
	y_bottom = uniform(40, 160)
	y_top_min = max(Main.original_resolution.y - 121, y_bottom + Main.distance_min)
	y_top = uniform(y_top_min, y_top_min + 75)
	pillar_bottom.position.y = convy(y_bottom - 121)
	pillar_top.position.y = convy(y_top)


def draw_pillars(speed):
	x_restart = speed + convx(Main.original_resolution.x + 26)
	if Main.pillars_doors[0].position.x < -convx(26) + speed:
		x = Main.pillars_doors[0].position.x
		Main.pillars_doors.pop(0)
		Main.pillars_doors.pop(0)
		Main.pillars_doors.append(
			SpriteInstance(Main.sprites["pillars"][int(uniform(0, 4))], hg.Vec2(x + x_restart, 0)))
		Main.pillars_doors.append(
			SpriteInstance(Main.sprites["pillars"][int(uniform(0, 4))], hg.Vec2(x + x_restart, 0)))
		random_pillars_doors_y(Main.pillars_doors[-2], Main.pillars_doors[-1])
		Main.doors_counter -= 1
		if Main.doors_counter < 0:
			Main.doors_counter = Main.num_doors - 1

	if Main.pillars_bottom[0].position.x < -convx(26) + speed:
		x = Main.pillars_bottom[0].position.x
		Main.pillars_bottom.pop(0)
		Main.pillars_bottom.append(
			SpriteInstance(Main.sprites["pillars"][int(uniform(0, 4))], hg.Vec2(x + x_restart, 0)))
		Main.pillars_bottom[-1].position.y = random_pillar_bottom_y()

	# Movement:
	for pillar in Main.pillars_bottom:
		pillar.position.x -= speed
		pillar.draw()

	for pillar in Main.pillars_doors:
		pillar.position.x -= speed
		pillar.draw()

	# draw flag:
	pos = Main.pillars_doors[2 * Main.doors_counter + 1].position
	Main.sprites["flag"].position_prec = Main.sprites["flag"].position
	Main.sprites["flag"].position = hg.Vec2(pos.x + convx(13), pos.y + convy(121))
	Main.sprites["flag"].draw()


def random_vapor_pos(id):
	rds = [[convy(14), convy(80)], [convy(100), convy(200)]]
	Main.sprites["vapors"][id].position.x = 0
	Main.sprites["vapors"][id].position.y = uniform(rds[id][0], rds[id][1])


def draw_vapor(id, x_speed):
	vapors_speed = [[0.04, 0.04], [0.05, 0.03]]
	pos = Main.sprites["vapors"][id].position
	pos.x += (vapors_speed[id][0] * Main.delta_t - x_speed)
	pos.y += vapors_speed[id][1] * Main.delta_t
	if pos.x < convx(-110):
		random_vapor_pos(id)
		pos.x = convx(Main.original_resolution.x + 97)
	if pos.x > convx(Main.original_resolution.x + 110):
		random_vapor_pos(id)
		pos.x = convx(-97)
	Main.sprites["vapors"][id].draw()


def draw_title():
	Main.sprites["title"].draw()
	Main.sprites["explain"].draw()


def draw_panel():
	Main.sprites["gameover"].draw()
	Main.sprites["panel"].draw()


def update_score():
	if Main.sprites["flag"].position.x < Main.ship.position.x < Main.sprites["flag"].position_prec.x:
		Main.score += 1
		hg.PlayStereo(Main.sounds["checkpoint"], hg.StereoSourceState(1))

def update_difficulty_level():

	# Display sprite:
	Main.sprites["difficulty_level"][Main.difficulty_level].draw()

	# Set level:
	if keyboard.Pressed(hg.K_F1):
		if Main.difficulty_level=="easy": Main.difficulty_level="normal"
		elif Main.difficulty_level=="normal": Main.difficulty_level="hard"
		elif Main.difficulty_level=="hard": Main.difficulty_level="easy"


def collisions():

	# Ground collision:
	if Main.ship.position.y < convy(79):
		Main.ship.is_broken = True

	# Pillars collision:
	else:
		ws = (convx(Main.ship.width) / 2) * Main.collision_accuracy[Main.difficulty_level]
		hs = (convy(Main.ship.height) / 2) * Main.collision_accuracy[Main.difficulty_level]
		wp = (convx(Main.pillars_doors[0].sprite.get_width())) * Main.collision_accuracy[Main.difficulty_level]
		xmax = Main.ship.position.x + ws + Main.scrolls_x[3]
		xmin = Main.ship.position.x - ws + Main.scrolls_x[3]
		# Doors pillars (only the 2 ones at the left of screen):
		for i in range(2):
			pillar_top = Main.pillars_doors[i * 2]
			if xmin - wp < pillar_top.position.x < xmax:
				pillar_bot = Main.pillars_doors[i * 2 + 1]
				if Main.ship.position.y + hs > pillar_top.position.y or Main.ship.position.y - hs < pillar_bot.position.y + convy(
						121):
					Main.ship.is_broken = True
					hg.PlayStereo(Main.sounds["collision"], hg.StereoSourceState(1))
					if Main.ship.position.x + ws < pillar_top.position.x + Main.scrolls_x[3]:
						Main.ship.broken_face = True
					return

		# Bottom pillars:
		for pillar in Main.pillars_bottom:
			if pillar.position.x > xmax:    # Don't test pillars in front of the ship
				break
			if xmin - wp < pillar.position.x < xmax:
				if Main.ship.position.y - hs < pillar.position.y + convy(121):
					Main.ship.is_broken = True
					hg.PlayStereo(Main.sounds["collision"], hg.StereoSourceState(1))
					if Main.ship.position.x + ws < pillar.position.x + Main.scrolls_x[3]:
						Main.ship.broken_face = True
					return


def parallax_scrolling():
	scrolls_sizes = [convx(512), convx(512), convx(256), convx(0), convx(256), convx(0), convx(256), convx(0),
					 convx(256), convx(256)]
	x_step = Main.scrolling_speed
	for i in range(len(Main.scrolls_x)):
		if i in [3, 5, 7]:
			Main.scrolls_x[i] = x_step * Main.delta_t
		else:
			Main.scrolls_x[i] -= x_step * Main.delta_t
			if Main.scrolls_x[i] < -scrolls_sizes[i]:
				Main.scrolls_x[i] += scrolls_sizes[i]
		x_step *= 0.75


def draw_parallaxes():
	# plan 10
	Main.sprites["parallaxes"][8].draw(hg.Vec2(Main.scrolls_x[9], convy(65)))
	Main.sprites["parallaxes"][8].draw(hg.Vec2(Main.scrolls_x[9] + convx(256), convy(65)))
	Main.sprites["parallaxes"][8].draw(hg.Vec2(Main.scrolls_x[9] + convx(512), convy(65)))

	# plan 9
	Main.sprites["parallaxes"][7].draw(hg.Vec2(Main.scrolls_x[8], convy(65)))
	Main.sprites["parallaxes"][7].draw(hg.Vec2(Main.scrolls_x[8] + convx(256), convy(65)))
	Main.sprites["parallaxes"][7].draw(hg.Vec2(Main.scrolls_x[8] + convx(512), convy(65)))

	# plan 8: vapor 1
	draw_vapor(1, Main.scrolls_x[7])

	# plan 7
	Main.sprites["parallaxes"][6].draw(hg.Vec2(Main.scrolls_x[6], convy(24)))
	Main.sprites["parallaxes"][6].draw(hg.Vec2(Main.scrolls_x[6] + convx(256), convy(24)))
	Main.sprites["parallaxes"][6].draw(hg.Vec2(Main.scrolls_x[6] + convx(512), convy(24)))

	# plan 6 vapor 0
	draw_vapor(0, Main.scrolls_x[5])

	# plan 5
	Main.sprites["parallaxes"][5].draw(hg.Vec2(Main.scrolls_x[4], convy(14)))
	Main.sprites["parallaxes"][5].draw(hg.Vec2(Main.scrolls_x[4] + convx(256), convy(14)))
	Main.sprites["parallaxes"][5].draw(hg.Vec2(Main.scrolls_x[4] + convx(512), convy(14)))

	# plan 4 : pillars
	if len(Main.pillars_doors) > 0:
		draw_pillars(Main.scrolls_x[3])

	# plan ship:
	Main.ship.draw()

	if Main.ship.is_broken:
		Main.flames.draw(Main.ship.position, -Main.scrolls_x[3] * 0.75)
		draw_flash()

	# plan 3
	Main.sprites["parallaxes"][4].draw(hg.Vec2(Main.scrolls_x[2], convy(-6)))
	Main.sprites["parallaxes"][4].draw(hg.Vec2(Main.scrolls_x[2] + convx(256), convy(-6)))
	Main.sprites["parallaxes"][4].draw(hg.Vec2(Main.scrolls_x[2] + convx(512), convy(-6)))

	# plan 2
	Main.sprites["parallaxes"][3].draw(hg.Vec2(Main.scrolls_x[1], convy(195)))
	Main.sprites["parallaxes"][2].draw(hg.Vec2(Main.scrolls_x[1], 0))
	Main.sprites["parallaxes"][3].draw(hg.Vec2(Main.scrolls_x[1] + convx(512), convy(195)))
	Main.sprites["parallaxes"][2].draw(hg.Vec2(Main.scrolls_x[1] + convx(512), 0))

	# plan 1
	Main.sprites["parallaxes"][1].draw(hg.Vec2(Main.scrolls_x[0], convy(195)))
	Main.sprites["parallaxes"][0].draw(hg.Vec2(Main.scrolls_x[0], -convy(5)))
	Main.sprites["parallaxes"][1].draw(hg.Vec2(Main.scrolls_x[0] + convx(512), convy(195)))
	Main.sprites["parallaxes"][0].draw(hg.Vec2(Main.scrolls_x[0] + convx(512), -convy(5)))

def play_animations():
	anims_playing = False
	for animation in Main.animations:
		anims_playing |= animation.update_animation(hg.time_to_sec_f(hg.GetClock()))
	return anims_playing

# -----------------------------------------------
#       Game phases
# -----------------------------------------------


def reset_intro_phase():
	Main.pillars_doors, Main.pillars_bottom = [], []
	Main.ship.reset()
	Main.flames.reset()
	Main.scrolling_speed = 0.9

	Main.sprites["vapors"][0].position = hg.Vec2()
	Main.sprites["vapors"][1].position = hg.Vec2()

	random_vapor_pos(0)
	random_vapor_pos(1)

	Main.doors_counter = 0

	Main.sprites["title"].position = hg.Vec2(0.5, convy(300))
	Main.sprites["explain"].position = hg.Vec2(0.5, 0.67)
	Main.sprites["explain"].color = hg.Color(1, 1, 1, 0)

	Main.animations = [SpriteAnimator(Main.sprites["title"], hg.Vec2(0.5, convy(221)), hg.Color.White, 0, 0.5),
	 				   SpriteAnimator(Main.sprites["explain"], hg.Vec2(0.5, 0.67), hg.Color.White, 0.5, 0.5)]

	for sprite in Main.sprites["difficulty_level"].values():
	 	sprite.position=hg.Vec2(0.5,convy(120))


def intro_phase():
	Main.ship.waiting()

	draw_parallaxes()

	parallax_scrolling()

	game_phase = intro_phase

	draw_title()
	update_difficulty_level()

	if not play_animations():

		if keyboard.Pressed(hg.K_Space):
			reset_ingame_phase()
			game_phase = ingame_phase

	return game_phase


def reset_ingame_phase():
	Main.doors_counter = Main.num_doors - 1
	reset_pillars()
	Main.flames.reset()
	Main.scrolling_speed = 0.9
	Main.score = 0
	Main.collision_time = 0


def ingame_phase():
	Main.ship.update_kinetic()

	draw_parallaxes()
	parallax_scrolling()
	update_score()
	draw_score()

	# Ship control:
	game_phase = ingame_phase
	if not Main.ship.is_broken:
		if keyboard.Pressed(hg.K_Space) and Main.ship.position.y < 1:
			Main.ship.start_booster()
			hg.PlayStereo(Main.sounds["thrust"], hg.StereoSourceState(1))
		collisions()
	else:
		if Main.ship.broken_face:
			Main.scrolling_speed *= 0.5
		else:
			Main.scrolling_speed *= 0.97

		if Main.ship.position.y < convy(79):
			hg.PlayStereo(Main.sounds["crash"], hg.StereoSourceState(1))
			reset_score_phase()
			game_phase = score_phase

	return game_phase


def reset_score_phase():
	Main.sprites["title"] = Main.sprites["get_ready"]
	Main.sprites["gameover"].position = hg.Vec2(0.5, convy(224 + 150))
	Main.sprites["panel"].position = hg.Vec2(0.5, convy(164 + 150))
	if Main.score > Main.score_max:
		Main.score_max = Main.score

	Main.animations = [SpriteAnimator(Main.sprites["gameover"], hg.Vec2(0.5, convy(224)), hg.Color.White, 0, 0.5),
					   SpriteAnimator(Main.sprites["panel"], hg.Vec2(0.5, convy(164)), hg.Color.White, 0, 0.5)]


def score_phase():
	Main.ship.update_kinetic()

	draw_parallaxes()
	parallax_scrolling()
	Main.scrolling_speed *= 0.97

	# Ship control:
	game_phase = score_phase

	draw_panel()

	if not play_animations():

		draw_score_panel()

		if keyboard.Pressed(hg.K_Space):
			reset_intro_phase()
			game_phase = intro_phase

	return game_phase


# ==================================================================================================

#                                   Program start here

# ==================================================================================================

# initialize  Harfang
hg.InputInit()
hg.AudioInit()
hg.WindowSystemInit()

keyboard = hg.Keyboard()
mouse = hg.Mouse()

sel,scr_mode,scr_res = request_screen_mode(16/9)

if sel == "ok":
	Main.resolution.x,Main.resolution.y=scr_res.x,scr_res.y
	Main.game_scale=Main.resolution.y / Main.original_resolution.y
	Main.screenMode=scr_mode

	win = hg.NewWindow("WinterZ", int(Main.resolution.x), int(Main.resolution.y), 32)#, hg.WV_Fullscreen)
	hg.RenderInit(win)
	hg.RenderReset(int(Main.resolution.x), int(Main.resolution.y), hg.RF_MSAA8X | hg.RF_FlipAfterRender | hg.RF_FlushAfterRender | hg.RF_MaxAnisotropy | hg.RF_VSync)

	hg.AddAssetsFolder("../assets_compiled")

	render_state_quad = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Less, hg.FC_Disabled)
	shader_texture = hg.LoadProgramFromAssets("shaders/texture")
	shader_white = hg.LoadProgramFromAssets("shaders/white")

	init_game()
	start_ambient_sound()

	Main.score = 0
	Main.score_max = 0
	reset_intro_phase()
	game_phase = intro_phase

	while not keyboard.Pressed(hg.K_Escape):
		keyboard.Update()
		mouse.Update()
		dt = hg.TickClock()
		Sprite.z_depth = 100

		hg.SetViewClear(0, hg.CF_Color | hg.CF_Depth, hg.ColorI(64, 64, 64), 1, 0)
		hg.SetViewRect(0, 0, 0, int(Main.resolution.x), int(Main.resolution.y))

		Main.delta_t = hg.time_to_sec_f(dt) * Main.game_speed[Main.difficulty_level]

		hg.SetViewOrthographic(0, 0, 0, int(Main.resolution.x), int(Main.resolution.y), hg.TransformationMat4(hg.Vec3(Main.resolution.x / 2, Main.resolution.y / 2, 0), hg.Vec3(0, 0, 0), hg.Vec3(1, 1, 1)), 0, 101, int(Main.resolution.y))

		Main.sprites["background"].draw()

		game_phase = game_phase()

		hg.Frame()
		hg.UpdateWindow(win)

	hg.AudioShutdown()
	hg.InputShutdown()
	hg.RenderShutdown()
	hg.DestroyWindow(win)