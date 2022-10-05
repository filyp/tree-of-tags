let symmetry = 6;
let alpha = 255;
let decay = 1;

let blending_mode = 0;
let blending_modes;

let size = 200;

function setup() {
  zoom = windowHeight / 2;
  createCanvas(windowWidth, windowHeight);
  background(0);
  blending_modes = [BLEND, DODGE, ADD, SOFT_LIGHT];
}

// change size with mouse wheel
function mouseWheel(event) {
  size += event.delta / 4;
}

// middle mutton cycles through blending modes
function mousePressed() {
  if (mouseButton === CENTER) {
    blending_mode = (blending_mode + 1) % blending_modes.length;
  }
}

// number keys choose symmetry
function keyTyped() {
  if (key >= "1" && key <= "9") {
    symmetry = int(key);
  }
}

function draw() {
  // make the screen darker
  blendMode(DIFFERENCE);
  background(decay);
  blendMode(blending_modes[blending_mode]);

  // circle colors around the color wheel
  let time = millis() / 1000;
  let color = [
    255 * (0.5 + 0.5 * Math.sin(time)),
    255 * (0.5 + 0.5 * Math.sin(time + (2 * Math.PI) / 3)),
    255 * (0.5 + 0.5 * Math.sin(time + (4 * Math.PI) / 3)),
  ];

  if (mouseIsPressed && mouseButton === LEFT) {
    fill(color[0], color[1], color[2], alpha);
    strokeWeight(1);
    stroke(0);
  } else {
    noFill();
    // use alpha
    stroke(color[0], color[1], color[2], alpha);
  }

  // draw in a 6 symmetry caleidoscope around center
  let mx = mouseX - width / 2;
  let my = mouseY - height / 2;
  for (let i = symmetry - 1; i >= 0; i--) {
    push();
    translate(width / 2, height / 2);
    rotate((TWO_PI / symmetry) * i);
    // line(pmx, pmy, mx, my);
    circle(mx, my, size);
    pop();
  }
}