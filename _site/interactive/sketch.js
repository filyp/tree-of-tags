let min_node_size = 15;
let scale_size_exponent = 0.5;
let scale_size_factor = 2.5;

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
  // initialize positions
  for (const node of Object.values(nodes)) {
    node.pos = [Math.random() * 2 - 1, Math.random() * 2 - 1];
  }

  // // limit nodes_sorted to the top n nodes
  // nodes_sorted = nodes_sorted.slice(0, 600);
}

function draw() {
  background(0);
  draw_graph();
  // noLoop();
}

function mouseWheel(event) {
  pos.zoom(event.delta, mouseX, mouseY);
  // loop();
}

function mousePressed() {
  clickedX = mouseX;
  clickedY = mouseY;
}

function mouseDragged() {
  pos.drag(mouseX - clickedX, mouseY - clickedY);
  clickedX = mouseX;
  clickedY = mouseY;
  // loop();
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
  let max_size = 50;
  let rel_weight = weight / largest_node_weight;
  let raw_size = rel_weight * (pos.scale * 2) ** scale_size_exponent * scale_size_factor;
  return (max_size * Math.atan(raw_size)) / (Math.PI / 2);
}

function get_edge_width(overlap) {
  return 20 * Math.max(0, overlap - 0.03);
}

function draw_graph() {
  update_positions(nodes_sorted);

  // choose nodes to draw
  let nodes_to_draw = [];
  for (const node_id of nodes_sorted) {
    let node = nodes[node_id];
    let visibility = 255 * pos.is_in_view(node.pos);
    if (visibility > 0) nodes_to_draw.push([node_id, visibility]);
    if (node_size(node.weight) < min_node_size) break;
  }

  // update_positions(nodes_to_draw.map((node) => node[0]));

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
