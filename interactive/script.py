from dataclasses import dataclass
import pickle
from time import time

import asyncio
import numpy as np
from js import document, requestAnimationFrame, setInterval, window
from pyodide import create_proxy, http

canvas_element = document.getElementById("canvas")
canvas = canvas_element.getContext("2d")


def cnv_coords(x, y):
    global scale, center, canvas_size
    # convert (-1.1, 1.1) to (0, canvas_size)
    # using int values draws faster
    x -= center[0]
    y -= center[1]
    return int((x * scale + 1.1) / 2.2 * canvas_size), int((y * scale + 1.1) / 2.2 * canvas_size)


def draw(time_millis=None):
    global net_data, frame_changed, canvas_size
    if not frame_changed:
        return
    canvas_size = window.innerHeight
    canvas_element.height = canvas_element.width = canvas_size
    pos = net_data.pos
    node_names = net_data.node_names
    node_weights = net_data.node_weights
    adj = net_data.adj
    max_node_weight = net_data.max_node_weight
    max_edge_weight = net_data.max_edge_weight

    # clear
    canvas.textAlign = "center"
    canvas.textBaseline = "middle"

    canvas.fillStyle = "black"
    canvas.fillRect(0, 0, canvas_size, canvas_size)

    # print edges
    # for n1, n2, edge_data in To_draw.edges(data=True):
    for n1, nei in zip(adj["nodes"], adj["adjacency"]):
        n1 = n1["id"]
        for edge in nei:
            n2 = edge["id"]
            canvas.strokeStyle = "blue"
            canvas.lineWidth = edge["weight"] / max_edge_weight * 10
            canvas.beginPath()
            canvas.moveTo(*cnv_coords(*pos[n1]))
            canvas.lineTo(*cnv_coords(*pos[n2]))
            canvas.stroke()
            canvas.closePath()

    # print nodes
    canvas.fillStyle = "white"
    for node, (x, y) in pos.items():
        # TODO text wrap with multiple fill_text calls (chars ~16)
        name = node_names[node]
        size = (node_weights[node] / max_node_weight) ** 0.4 * 25
        canvas.font = f"{int(size)}px sans-serif"
        canvas.fillText(name, *cnv_coords(x, y))
    frame_changed = False


def on_wheel(event):
    global scale, center, frame_changed, canvas_size
    delta = event.deltaY

    mouse_pos = np.array([event.offsetX, event.offsetY])
    # invert cnv_coords on mouse_pos
    mouse_pos = (mouse_pos / canvas_size * 2.2 - 1.1) / scale + center

    # change scale
    old_scale = scale
    scale /= 2 ** (delta / 700)
    # change center so that mouse_pos stays in the same place
    center = mouse_pos - (mouse_pos - center) * old_scale / scale
    frame_changed = True


def on_mouse_move(event):
    global center, frame_changed, clicked, scale, canvas_size
    if clicked is None:
        return
    mouse_pos = np.array([event.offsetX, event.offsetY])
    mouse_diff = mouse_pos - clicked
    # update center
    center -= mouse_diff / canvas_size * 2.2 / scale
    clicked = mouse_pos
    frame_changed = True

def on_mouse_down(event):
    global clicked
    clicked = np.array([event.offsetX, event.offsetY])

def on_mouse_up(event):
    global clicked
    clicked = None


@dataclass
class NetworkData:
    adj: dict
    node_weights: dict
    node_names: dict
    pos: dict


async def main():
    global scale, clicked, center, frame_changed, net_data
    scale = 1
    clicked = None
    center = np.array([0, 0])
    frame_changed = True

    # download piclke with data
    url = "http://localhost:3000/graph_info.pickle"
    # no cache
    # header = {"Cache-Control": "no-cache"}
    # response = await http.pyfetch(url=url, method="GET", headers=header)
    response = await http.pyfetch(url=url, method="GET")
    content = await response.bytes()
    adj, node_weights, node_names, pos = pickle.loads(content)
    net_data = NetworkData(adj, node_weights, node_names, pos)
    net_data.max_node_weight = max(node_weights.values())
    net_data.max_edge_weight = max([edge["weight"] for nei in adj["adjacency"] for edge in nei])

    canvas_element.addEventListener("wheel", create_proxy(on_wheel))
    canvas_element.addEventListener("mousedown", create_proxy(on_mouse_down))
    canvas_element.addEventListener("mouseup", create_proxy(on_mouse_up))
    canvas_element.addEventListener("mousemove", create_proxy(on_mouse_move))
    # requestAnimationFrame(create_proxy(draw))
    setInterval(create_proxy(draw), 1000 / 60)
    # document.getElementById("add-memory-button").addEventListener("click", create_proxy(add_memory))


main()
