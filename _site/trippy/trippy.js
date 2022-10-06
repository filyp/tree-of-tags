let alpha = 255
let decay = 1
let scroll_speed = 0.7
let sunflower_limit = 100

// initial values
let shape_size = 400

let clickedX, clickedY
let ui


function setup() {
  zoom = windowHeight / 2
  createCanvas(windowWidth, windowHeight)
  background(0)
  // imageMode(CENTER)

  ui = new UI();
}

// change size with mouse wheel
function mouseWheel(event) {
  shape_size -= event.delta * scroll_speed
  shape_size = max(0, shape_size)
}

function mousePressed() {
  // record mouse position
  clickedX = mouseX
  clickedY = mouseY
}

function draw() {
  // make the screen darker
  blendMode(DIFFERENCE)
  background(decay)
  blendMode(ui.blending_mode)

  // circle colors around the color wheel
  let t = millis() / 1000 * ui.color_speed
  let color = [
    255 * (0.5 + 0.5 * Math.sin(t)),
    255 * (0.5 + 0.5 * Math.sin(t + (2 * Math.PI) / 3)),
    255 * (0.5 + 0.5 * Math.sin(t + (4 * Math.PI) / 3)),
  ]

  let mx = mouseX - width / 2
  let my = mouseY - height / 2

  push()
  translate(width / 2, height / 2)
  if (mouseIsPressed) {
    // draw sunflower pattern
    background(0)
    let mouse_dist = dist(0, 0, mx, my)
    let mouse_angle = atan2(my, mx)
    let old_mouse_dist = dist(0, 0, clickedX - width / 2, clickedY - height / 2)
    let old_mouse_angle = atan2(clickedY - height / 2, clickedX - width / 2)
    let angle = TWO_PI / ui.symmetry + (mouse_angle - old_mouse_angle) / ui.symmetry
    let size_offset = mouse_dist / old_mouse_dist
    for (let i = sunflower_limit - 1; i >= 0; i--) {
      let r =  mouse_dist * (size_offset ** i)
      let x = r * Math.cos(mouse_angle + angle * i)
      let y = r * Math.sin(mouse_angle + angle * i)
      styled_shape(x, y, shape_size * (size_offset ** i), color)
    }
  } else {
    // draw in a caleidoscope around center
    for (let i = ui.symmetry - 1; i >= 0; i--) {
      push()
      rotate((TWO_PI / ui.symmetry) * i)
      // line(pmx, pmy, mx, my)
      styled_shape(mx, my, shape_size, color)
      pop()
    }
  }
  pop()

  // TODO make this really disappear
  if (ui.visible) {
    imageMode(CORNER)
    image(ui.panel, 0, 0)
  }
}


function shape(x, y, radius) {
  if (ui.n_vertices == 0) {
    let skewness = 1.3 ** ui.ellipseness
    ellipse(x, y, radius, radius * skewness)
    return
  }

  let angle = TWO_PI / ui.n_vertices
  beginShape()
  for (let a = 0; a < TWO_PI; a += angle) {
    let sx = x + cos(a) * radius
    let sy = y + sin(a) * radius
    vertex(sx, sy)
  }
  endShape(CLOSE)
}


function styled_shape(x, y, shape_size, color) {
  if (ui.if_to_fill()) {
    // draw full filled shape
    fill(color[0], color[1], color[2], alpha)
    if (ui.border_visible()) {
      strokeWeight(ui.border_width)
      stroke("black")
    } else {
      noStroke()
    }
    shape(x, y, shape_size)
  } else {
    // draw a contour
    noFill()
    if (ui.border_visible()) {
      strokeWeight(ui.ring_width + ui.border_width)
      stroke("black")
      shape(x, y, shape_size)
    }
    strokeWeight(ui.ring_width)
    stroke(color[0], color[1], color[2], alpha)
    shape(x, y, shape_size)
  }
}


// transformations on existing image
// some blur will be added with each transformation, so it's a bad approach
  // let im = get()
  // let scaler = 1 //0.995
  // im.resize(width * scaler, height * scaler)
  // // push()
  // // rotate(1)
  // // image(im)         // no effect
  // // set(im)           // crisp but slow
  // // image(im, 0, 0)   // fast but blurry
  // // set(0, 0, im)     // fast but blurry
  // // fast, crisp, but aliasing
  // noSmooth()
  // image(im, width/2, height/2)
  // // set(0, 0, im)
  // smooth()
  // // pop()


function keyPressed() {
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
