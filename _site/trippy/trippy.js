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

function keyPressed() {
  handle_key_press(key, ui)
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
    // let left_eye = createGraphics(width / 2, height)
    draw_sunflower(mx, my, shape_size, color)
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


function draw_sunflower(mx, my, shape_size, color, max_binocular_offset=0) {
  background(0)
  const mouse_dist = dist(0, 0, mx, my)
  const mouse_angle = atan2(my, mx)
  const old_mouse_dist = dist(0, 0, clickedX - width / 2, clickedY - height / 2)
  const old_mouse_angle = atan2(clickedY - height / 2, clickedX - width / 2)
  const angle = TWO_PI / ui.symmetry + (mouse_angle - old_mouse_angle) / ui.symmetry
  const offset_factor = mouse_dist / old_mouse_dist
  for (let i = sunflower_limit - 1; i >= 0; i--) {
    const offset = offset_factor ** i
    const r =  mouse_dist * offset
    const x = r * Math.cos(mouse_angle + angle * i)
    const y = r * Math.sin(mouse_angle + angle * i)
    styled_shape(x + offset * max_binocular_offset, y, shape_size * offset, color)
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

