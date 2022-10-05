let off_screen_decay_factor = 4;
let _zoom_speed = 0.001;

class Positioning {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.position_on_plane = [0, 0];
    this.diagonal = Math.sqrt(width ** 2 + height ** 2);

    this.scale = 1 / 2;
  }

  zoom(delta, mouseX, mouseY) {
    let old_scale = this.scale;
    this.scale /= 2 ** (delta * _zoom_speed);
    this.position_on_plane[0] +=
      ((mouseX - this.width / 2) * (1 / old_scale - 1 / this.scale)) / this.height;
    this.position_on_plane[1] +=
      ((mouseY - this.height / 2) * (1 / old_scale - 1 / this.scale)) / this.height;
  }

  drag(deltaX, deltaY) {
    this.position_on_plane[0] -= deltaX / this.scale / this.height;
    this.position_on_plane[1] -= deltaY / this.scale / this.height;
  }

  plane_to_pix(pos) {
    // convert a plane coordinate to a pixel coordinate
    // plane coordinates are in the range [-1, 1]
    return [
      (pos[0] - this.position_on_plane[0]) * this.scale * this.height + this.width / 2,
      (pos[1] - this.position_on_plane[1]) * this.scale * this.height + this.height / 2,
    ];
  }

  pix_to_plane(pos) {
    // convert a pixel coordinate to a plane coordinate
    return [
      (pix_pos[0] - this.width / 2) / this.scale / this.height + this.position_on_plane[0],
      (pix_pos[1] - this.height / 2) / this.scale / this.height + this.position_on_plane[1],
    ];
  }

  is_in_view(pos) {
    let [x, y] = this.plane_to_pix(pos);
    let dist_to_center = Math.sqrt((x - this.width / 2) ** 2 + (y - this.height / 2) ** 2);
    // sharply decay visibility when distance to center is > diagonal / 2
    let decay = (off_screen_decay_factor * (dist_to_center - this.diagonal / 2)) / this.diagonal;
    // clip to [0, 1]
    decay = Math.max(0, Math.min(1, decay));
    return 1 - decay;
  }
}
