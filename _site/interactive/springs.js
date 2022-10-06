// spring layout
let attr = "overlap";

let repulsive_force = 0.0001;
let repulsion_exponent = 2;

let attractive_force = 0.01;

let center_repulsion = 0.01;
let center_repulsion_exponent = 0.5;

// let desired_deviation = 3;

function update_positions(nodes_to_update) {
  // initialize forces as zeros
  let forces = {};
  for (const node_id of nodes_to_update) {
    forces[node_id] = [0, 0];
  }
  let start;
  let end;

  // center nodes
  let center_of_mass = [0, 0];
  for (const node_id of nodes_to_update) {
    center_of_mass[0] += nodes[node_id].pos[0];
    center_of_mass[1] += nodes[node_id].pos[1];
  }
  center_of_mass[0] /= nodes_to_update.length;
  center_of_mass[1] /= nodes_to_update.length;
  for (const node_id of nodes_to_update) {
    nodes[node_id].pos[0] -= center_of_mass[0];
    nodes[node_id].pos[1] -= center_of_mass[1];
  }

  //   start = performance.now();
  //   // calculate repulsive forces
  //   for (let i = 0; i < nodes_to_update.length; i++) {
  //     for (let j = 0; j < nodes_to_update.length; j++) {
  //       if (i >= j) continue;
  //       let n1 = nodes_to_update[i];
  //       let n2 = nodes_to_update[j];
  //       let pos1 = nodes[n1].pos;
  //       let pos2 = nodes[n2].pos;
  //       let diffX = pos2[0] - pos1[0];
  //       let diffY = pos2[1] - pos1[1];
  //       let dist = Math.sqrt(diffX ** 2 + diffY ** 2);
  //       if (dist < 0.001) dist = 0.001;
  //       let forceX = (diffX / dist) * (1 / dist) ** repulsion_exponent * repulsive_force;
  //       let forceY = (diffY / dist) * (1 / dist) ** repulsion_exponent * repulsive_force;
  //       forces[n1][0] -= forceX;
  //       forces[n1][1] -= forceY;
  //       forces[n2][0] += forceX;
  //       forces[n2][1] += forceY;
  //     }
  //   }
  //   end = performance.now();
  //   console.log("repulsive forces:  " + Math.round(end - start) + "ms");

    // calculate center repulsion
    start = performance.now();
    for (const node_id of nodes_to_update) {
      let node_pos = nodes[node_id].pos;
      let dist = Math.sqrt(node_pos[0] ** 2 + node_pos[1] ** 2);
      if (dist < 0.001) dist = 0.001;
      let forceX = (node_pos[0] / dist) * (1 / dist) ** center_repulsion_exponent * center_repulsion;
      let forceY = (node_pos[1] / dist) * (1 / dist) ** center_repulsion_exponent * center_repulsion;
      forces[node_id][0] += forceX;
      forces[node_id][1] += forceY;
    }
    end = performance.now();
    console.log("center repulsion:  " + Math.round(end - start) + "ms");

  start = performance.now();
  // calculate attractive forces
  for (let i = 0; i < nodes_to_update.length; i++) {
    for (let j = 0; j < nodes_to_update.length; j++) {
      if (i >= j) continue;
      let n1 = nodes_to_update[i];
      let n2 = nodes_to_update[j];

      //   if (edges[n1][n2] == undefined) continue;
      if (!(n2 in edges[n1])) continue;

      let pos1 = nodes[n1].pos;
      let pos2 = nodes[n2].pos;
      let diffX = pos2[0] - pos1[0];
      let diffY = pos2[1] - pos1[1];
      let dist = Math.sqrt(diffX ** 2 + diffY ** 2);
      if (dist < 0.001) dist = 0.001;
      let forceX = (diffX / dist) * dist ** 2 * attractive_force * edges[n1][n2][attr];
      let forceY = (diffY / dist) * dist ** 2 * attractive_force * edges[n1][n2][attr];
      forces[n1][0] += forceX;
      forces[n1][1] += forceY;
      forces[n2][0] -= forceX;
      forces[n2][1] -= forceY;
    }
  }
  end = performance.now();
  console.log("attractive forces: " + Math.round(end - start) + "ms");

  // update positions
  for (const node_id of nodes_to_update) {
    // nodes[node_id].pos = nj.add(nodes[node_id].pos, forces[node_id]).tolist();
    nodes[node_id].pos = [
      nodes[node_id].pos[0] + forces[node_id][0],
      nodes[node_id].pos[1] + forces[node_id][1],
    ];
  }

  // // normalize distances in L(inf) metric
  // let max_dist = 0;
  // for (const node_id of nodes_to_update) {
  //     let dist = Math.max(Math.abs(nodes[node_id].pos[0]), Math.abs(nodes[node_id].pos[1]));
  //     if (dist > max_dist) max_dist = dist;
  // }
  // for (const node_id of nodes_to_update) {
  //     nodes[node_id].pos[0] /= max_dist;
  //     nodes[node_id].pos[1] /= max_dist;
  // }
}
