# -*-coding:Utf-8 -*

# ==============================================================================================================

#              - HARFANG® 3D - www.harfang3d.com

#                          - Python -

#                   Screen mode Requester

#   Usage:
#       Call request_screen_mode(ratio_filter) before Plus.RenderInit()
#       ratio_filter: if you want to restrict the screen resolution to a specific ration (16/9, 4/3...)
#                     0 means all resolutions appears in listing.

# ==============================================================================================================

import harfang as hg


res_w=520
res_h=160
monitors=None
monitors_names=[]
modes=None
current_monitor=0
current_mode=0
ratio_filter=0
flag_windowed=False

screenModes=[hg.WV_FullscreenMonitor1,hg.WV_FullscreenMonitor2,hg.WV_FullscreenMonitor3]
smr_screenMode=hg.WV_FullscreenMonitor1
smr_resolution=hg.Vec2(1280,1024)

hg.InputInit()
hg.WindowSystemInit()

win = hg.NewWindow("Screen Mode Requester", res_w, res_h, 32)#, hg.WV_Fullscreen)
hg.RenderInit(win)
hg.RenderReset(res_w, res_h, hg.RF_MSAA8X | hg.RF_FlipAfterRender | hg.RF_FlushAfterRender | hg.RF_MaxAnisotropy | hg.RF_VSync)

hg.AddAssetsFolder("../assets_compiled")


# initialize ImGui
imgui_prg = hg.LoadProgramFromAssets('shaders/imgui')
imgui_img_prg = hg.LoadProgramFromAssets('shaders/imgui_image')

hg.ImGuiInit(10, imgui_prg, imgui_img_prg)

def gui_ScreenModeRequester():
	global flag_windowed
	global current_monitor,current_mode,monitors_names,modes
	dt = hg.TickClock()

	# ImGui frame
	hg.ImGuiBeginFrame(res_w, res_h, dt, hg.ReadMouse(), hg.ReadKeyboard())
	hg.ImGuiSetNextWindowPosCenter(hg.ImGuiCond_Always)
	hg.ImGuiSetNextWindowSize(hg.Vec2(res_w, res_h), hg.ImGuiCond_Always)
	if hg.ImGuiBegin("Choose screen mode", True, hg.ImGuiWindowFlags_NoTitleBar
										  | hg.ImGuiWindowFlags_MenuBar
										  | hg.ImGuiWindowFlags_NoMove
										  | hg.ImGuiWindowFlags_NoSavedSettings
										  | hg.ImGuiWindowFlags_NoCollapse):

		if hg.ImGuiBeginCombo("Monitor", monitors_names[current_monitor]):
			for i in range(len(monitors_names)):
				f = hg.ImGuiSelectable(monitors_names[i], current_monitor == i)
				if f:
					current_monitor = i
			hg.ImGuiEndCombo()

		if hg.ImGuiBeginCombo("Screen size", modes[current_monitor][current_mode].name):
			for i in range(len(modes[current_monitor])):
				f = hg.ImGuiSelectable(
					f"{modes[current_monitor][i].name}##{str(i)}", current_mode == i
				)
				if f:
					current_mode = i
			hg.ImGuiEndCombo()

		f, d = hg.ImGuiCheckbox("Windowed", flag_windowed)
		if f:
			flag_windowed = d

		ok=hg.ImGuiButton("Ok")
		hg.ImGuiSameLine()
		cancel=hg.ImGuiButton("Quit")
	hg.ImGuiEndFrame(0)

	if ok: return "ok"
	elif cancel: return "quit"
	else: return ""

def request_screen_mode(p_ratio_filter=0):

	global monitors,monitors_names,modes,smr_screenMode,smr_resolution,ratio_filter

	ratio_filter=p_ratio_filter
	monitors = hg.GetMonitors()
	monitors_names = []
	modes = []
	epsilon = 0.01
	for i in range(monitors.size()):
		monitors_names.append(hg.GetMonitorName(monitors.at(i))+str(i))
		f, m = hg.GetMonitorModes(monitors.at(i))
		filtered_modes=[]
		for j in range(m.size()):
			md=m.at(j)
			rect = md.rect
			r = (rect.ex - rect.sx) / (rect.ey - rect.sy)
			if ratio_filter == 0 or r - epsilon < ratio_filter < r + epsilon:
				filtered_modes.append(md)
		modes.append(filtered_modes)
	select=""
	while not select:
		select=gui_ScreenModeRequester()
		hg.SetView2D(0, 0, 0, res_w, res_h, -1, 1, hg.CF_Color | hg.CF_Depth, hg.Color.Black, 1, 0)
		hg.Frame()
		hg.UpdateWindow(win)

	if select=="ok":

		smr_screenMode = hg.Windowed if flag_windowed else screenModes[current_monitor]
		rect=modes[current_monitor][current_mode].rect
		smr_resolution.x,smr_resolution.y=rect.ex-rect.sx,rect.ey-rect.sy
		hg.RenderShutdown()
		hg.DestroyWindow(win)

	return select,smr_screenMode,smr_resolution