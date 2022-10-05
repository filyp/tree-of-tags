let num_of_nodes = 30;
let num_of_fading_nodes = 20;
let min_num_of_opaque_nodes = 10;

// spring layout
let attr = "overlap";
let repulsive_force = 0.0001;
let attractive_force = 0.1;
let repulsion_exponent = 2;


let off_screen_decay_factor = 10;
let zoom = 1 / 2;
let _zoom_speed = 0.001;

let position_on_plane = [0, 0];
let nodes, edges, nodes_sorted, largest_node_weight, _tag_net;
let clickedX, clickedY;
let diagonal;

function preload() {
  _tag_net = loadJSON("tag_net.json");
}

function setup() {
  createCanvas(windowWidth, windowHeight);
  textAlign(CENTER, CENTER);
  diagonal = Math.sqrt(width ** 2 + height ** 2);
  [nodes, edges] = [_tag_net[0], _tag_net[1]];
  largest_node_weight = Math.max(...Object.values(nodes).map((node) => node.weight));

  // create a sorted list of node ids
  nodes_sorted = Object.keys(nodes).sort((a, b) => nodes[b].weight - nodes[a].weight);

  initialize_positions();
}

function draw() {
  background(0);
  draw_graph();
  // noLoop();
}

function mouseWheel(event) {
  let old_zoom = zoom;
  zoom /= 2 ** (event.delta * _zoom_speed);
  position_on_plane[0] += ((mouseX - width / 2) * (1 / old_zoom - 1 / zoom)) / height;
  position_on_plane[1] += ((mouseY - height / 2) * (1 / old_zoom - 1 / zoom)) / height;
  loop();
}

function mousePressed() {
  clickedX = mouseX;
  clickedY = mouseY;
}

function mouseDragged() {
  position_on_plane[0] -= (mouseX - clickedX) / zoom / height;
  position_on_plane[1] -= (mouseY - clickedY) / zoom / height;
  clickedX = mouseX;
  clickedY = mouseY;
  loop();
}

function plane_to_pix(pos) {
  // convert a plane coordinate to a pixel coordinate
  // plane coordinates are in the range [-1, 1]
  return [
    (pos[0] - position_on_plane[0]) * zoom * height + width / 2,
    (pos[1] - position_on_plane[1]) * zoom * height + height / 2,
  ];
}

function pix_to_plane(pix_pos) {
  // convert a pixel coordinate to a plane coordinate
  return [
    (pix_pos[0] - width / 2) / zoom / height + position_on_plane[0],
    (pix_pos[1] - height / 2) / zoom / height + position_on_plane[1],
  ];
}

function draw_graph() {
  // choose nodes to draw
  // while there are less than num_of_nodes nodes to draw, try to add the next node
  let nodes_to_draw = [];
  let i = 0;
  while (nodes_to_draw.length < num_of_nodes) {
    let node_id = nodes_sorted[i];
    let node = nodes[node_id];
    let visibility = is_in_view(node.pos);
    let priority = node.weight * visibility;
    // node_id, priority, visibility
    if (visibility > 0) nodes_to_draw.push([node_id, priority, 255]);
    i++;
    // break if array ended
    if (i >= nodes_sorted.length) break;
  }

  update_positions(nodes_to_draw.map((node) => node[0]));

  // // sort nodes by priority
  // nodes_to_draw.sort((a, b) => b[1] - a[1]);
  // // last nodes should gradually fade out
  // let current_num_of_fading_nodes = Math.min(
  //   num_of_fading_nodes,
  //   nodes_to_draw.length - min_num_of_opaque_nodes
  // );
  // if (current_num_of_fading_nodes > 0) {
  //   for (let i = 0; i < current_num_of_fading_nodes; i++) {
  //     nodes_to_draw[nodes_to_draw.length - i - 1][2] =
  //       (255 * i) / current_num_of_fading_nodes;
  //   }
  // }

  // draw edges
  for (const [n1, priority1, n1_alpha] of nodes_to_draw) {
    let [x1, y1] = plane_to_pix(nodes[n1].pos);
    for (const [n2, priority2, n2_alpha] of nodes_to_draw) {
      let edge_data = edges[n1][n2];
      // if there is no edge, continue
      if (edge_data == undefined) continue;

      let [x2, y2] = plane_to_pix(nodes[n2].pos);
      strokeWeight(get_edge_width(edge_data.overlap));
      // strokeWeight(edge_data.weight / 300);

      // let n2_alpha = 255 // node_visibility(nodes[n2]);
      let line_alpha = Math.min(n1_alpha, n2_alpha);
      stroke(12, 134, 155, line_alpha); // #0c869b
      line(x1, y1, x2, y2);
    }
  }

  // draw nodes
  noStroke();
  for (const [n1, priority1, n1_alpha] of nodes_to_draw) {
    let node = nodes[n1];
    let [x, y] = plane_to_pix(node.pos);
    textSize(node_size(node.weight));
    // text_alpha = 255 // node_visibility(node);
    fill(255, n1_alpha);
    text(node.name, x, y);
  }
}

function is_in_view(pos) {
  let [x, y] = plane_to_pix(pos);
  let dist_to_center = Math.sqrt((x - width / 2) ** 2 + (y - height / 2) ** 2);
  // sharply decay visibility when distance to center is > diagonal / 2
  let decay = (off_screen_decay_factor * (dist_to_center - diagonal / 2)) / diagonal;
  // clip to [0, 1]
  decay = Math.max(0, Math.min(1, decay));
  return 1 - decay;
}

// function node_visibility(node) {
//   // establish visibility based on zoom
//   let rel_weight = node.weight / largest_node_weight;
//   let inv_zoom = 1 / zoom / 2;
//   let zoom_visibility = 16 * rel_weight - 4 * inv_zoom;
//   // clip to [0, 1]
//   zoom_visibility = Math.max(0, Math.min(1, zoom_visibility));
//   in_view_visibility = is_in_view(node.pos);
//   return 255 * zoom_visibility * in_view_visibility;
// }

function node_size(weight) {
  let rel_weight = weight / largest_node_weight;
  return rel_weight ** 0.5 * 25;
  // return 20;
}

function get_edge_width(overlap) {
  return 20 * Math.max(0, overlap - 0.03);
  // return 20 * overlap ** 2;
}

function initialize_positions() {
  for (const node of Object.values(nodes)) {
    node.pos = [Math.random() * 2 - 1, Math.random() * 2 - 1];
  }
}

function update_positions(nodes_to_update) {
  // initialize forces as zeros
  let forces = {};
  for (const node_id of nodes_to_update) {
    forces[node_id] = [0, 0];
  }

  // calculate repulsive forces
  for (let i = 0; i < nodes_to_update.length; i++) {
    for (let j = 0; j < nodes_to_update.length; j++) {
      if (i >= j) continue;
      let n1 = nodes_to_update[i];
      let n2 = nodes_to_update[j];
      let pos1 = nodes[n1].pos;
      let pos2 = nodes[n2].pos;

      // let diff = nj.subtract(pos2, pos1);
      // let dist = nj.sqrt(nj.dot(diff, diff)).get(0);
      // if (dist == 0) dist = 0.00001;
      // let force = nj.divide(diff, dist).multiply((1 / dist) ** 2).multiply(repulsive_force);
      // forces[n1] = nj.subtract(forces[n1], force).tolist();
      // forces[n2] = nj.add(forces[n2], force).tolist();

      let diffX = pos2[0] - pos1[0];
      let diffY = pos2[1] - pos1[1];
      let dist = Math.sqrt(diffX ** 2 + diffY ** 2);
      if (dist == 0) dist = 0.00001;
      let forceX = (diffX / dist) * (1 / dist) ** repulsion_exponent * repulsive_force;
      let forceY = (diffY / dist) * (1 / dist) ** repulsion_exponent * repulsive_force;
      forces[n1][0] -= forceX;
      forces[n1][1] -= forceY;
      forces[n2][0] += forceX;
      forces[n2][1] += forceY;
    }
  }

  // calculate attractive forces
  for (const n1 of nodes_to_update) {
    for (const n2 of nodes_to_update) {
      if (edges[n1][n2] == undefined) continue;
      if (n1 == n2) continue;
      let pos1 = nodes[n1].pos;
      let pos2 = nodes[n2].pos;

      // let diff = nj.subtract(pos2, pos1);
      // let dist = nj.sqrt(nj.dot(diff, diff)).get(0);
      // if (dist == 0) dist = 0.00001;
      // let force = nj.divide(diff, dist).multiply((dist ** 2)).multiply(attractive_force).multiply(edges[n1][n2][attr]);
      // forces[n1] = nj.add(forces[n1], force).tolist();
      // forces[n2] = nj.subtract(forces[n2], force).tolist();

      let diffX = pos2[0] - pos1[0];
      let diffY = pos2[1] - pos1[1];
      let dist = Math.sqrt(diffX ** 2 + diffY ** 2);
      if (dist == 0) dist = 0.00001;
      let forceX = (diffX / dist) * dist ** 2 * attractive_force * edges[n1][n2][attr];
      let forceY = (diffY / dist) * dist ** 2 * attractive_force * edges[n1][n2][attr];
      forces[n1][0] += forceX;
      forces[n1][1] += forceY;
      forces[n2][0] -= forceX;
      forces[n2][1] -= forceY;
    }
  }

  // update positions
  for (const node_id of nodes_to_update) {
    // nodes[node_id].pos = nj.add(nodes[node_id].pos, forces[node_id]).tolist();
    nodes[node_id].pos = [
      nodes[node_id].pos[0] + forces[node_id][0],
      nodes[node_id].pos[1] + forces[node_id][1],
    ];
  }
}
