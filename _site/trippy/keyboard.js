
function handle_key_press(key, ui) {
  // number pressed with control and alt changes ellipse shape
  if (key >= "1" && key <= "9" && keyIsDown(CONTROL) && keyIsDown(ALT)) {
    ui.ellipseness = int(key) - 1
    return
  }

  // number pressed with control  changes shape
  if (key >= "0" && key <= "9" && keyIsDown(CONTROL)) {
    ui.n_vertices = int(key)
    return
  }

  // number keys choose symmetry
  if (key >= "1" && key <= "9") {
    ui.symmetry = int(key)
    return
  }

  // top row sets blending mode
  let blending_modes = {
    "q": BLEND,
    "w": ADD,
    "e": DODGE,
    "r": SOFT_LIGHT,
    "t": LIGHTEST,
  }
  if (key in blending_modes) {
    ui.blending_mode = blending_modes[key]
    return
  }

  // middle row sets ring width
  let ring_widths = {
    "a": 0.0625,
    "s": 0.25,
    "d": 1,
    "f": 4,
    "g": 16,
    "h": 64,
    "j": 256,
  }
  if (key in ring_widths) {
    ui.ring_width = ring_widths[key]
    return
  }

  // bottom row sets border width
  let border_widths = {
    "z": 0.03125,
    "x": 0.125,
    "c": 0.5,
    "v": 2,
    "b": 8,
    "n": 32,
    "m": 128,
  }
  if (key in border_widths) {
    ui.border_width = border_widths[key]
    return
  }

  switch (key) {
    // space pauses and unpauses
    case " ":
      if (isLooping()) {
        noLoop()
      } else {
        loop()
      }
      break
    // u toggles UI panel
    case "u":
      ui.visible = !ui.visible
      if (ui.visible) {
        ui.show_ui()
      } else {
        ui.hide_ui()
      }
      break
  }
}