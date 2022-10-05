// spring layout
let attr = "overlap";
let repulsive_force = 0.0001;
let attractive_force = 0.1;
let repulsion_exponent = 2;

let nodes, edges, nodes_sorted, largest_node_weight, _tag_net;
let clickedX, clickedY;
let pos;

function preload() {
  _tag_net = loadJSON("tag_net.json");
}

function setup() {
  createCanvas(windowWidth, windowHeight);
  textAlign(CENTER, CENTER);
  pos = new Positioning(width, height);

  [nodes, edges] = [_tag_net[0], _tag_net[1]];
  largest_node_weight = Math.max(...Object.values(nodes).map((node) => node.weight));

  // create a sorted list of node ids
  nodes_sorted = Object.keys(nodes).sort((a, b) => nodes[b].weight - nodes[a].weight);

  // limit nodes_sorted to the top 100 nodes
  nodes_sorted = nodes_sorted.slice(0, 100);

  initialize_positions();
}

function draw() {
  background(0);
  draw_graph();
  // noLoop();
}

function mouseWheel(event) {
  pos.zoom(event.delta, mouseX, mouseY);
  loop();
}

function mousePressed() {
  clickedX = mouseX;
  clickedY = mouseY;
}

function mouseDragged() {
  pos.drag(mouseX - clickedX, mouseY - clickedY);
  clickedX = mouseX;
  clickedY = mouseY;
  loop();
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
  return 20 * Math.max(0, overlap - 0.02);
  // return 20 * overlap ** 2;
}

function initialize_positions() {
  for (const node of Object.values(nodes)) {
    node.pos = [Math.random() * 2 - 1, Math.random() * 2 - 1];
  }
}


function draw_graph() {
  // choose nodes to draw
  let nodes_to_draw = [];
  for (const node_id of nodes_sorted) {
    let node = nodes[node_id];
    let visibility = 255 * pos.is_in_view(node.pos);
    if (visibility > 0) nodes_to_draw.push([node_id, visibility]);
  }

  update_positions(nodes_to_draw.map((node) => node[0]));


  // draw edges
  for (const [n1, n1_alpha] of nodes_to_draw) {
    let [x1, y1] = pos.plane_to_pix(nodes[n1].pos);
    for (const [n2, n2_alpha] of nodes_to_draw) {
      let edge_data = edges[n1][n2];
      // if there is no edge, continue
      if (edge_data == undefined) continue;

      let [x2, y2] = pos.plane_to_pix(nodes[n2].pos);
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
  for (const [n1, n1_alpha] of nodes_to_draw) {
    let node = nodes[n1];
    let [x, y] = pos.plane_to_pix(node.pos);
    textSize(node_size(node.weight));
    fill(255, n1_alpha);
    text(node.name, x, y);
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
