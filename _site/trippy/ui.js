class UI {
    constructor() {
        this.visible = true
        this.symmetry_slider = createSlider(1, 9, 6)
        this.symmetry_slider.position(20, 20)
        this.ring_width_slider = createSlider(-4, 8, 2, 0)   // values are log2
        this.ring_width_slider.position(20, 50)
        this.border_width_slider = createSlider(-5, 7, 1, 0) // values are log2
        this.border_width_slider.position(20, 80)
        this.vertices_slider = createSlider(0, 9, 0)
        this.vertices_slider.position(20, 110)
        this.ellipseness_slider = createSlider(0, 8, 0, 0)
        this.ellipseness_slider.position(20, 140)
        this.color_speed_slider = createSlider(-6, 6, 0, 0)  // values are log2
        this.color_speed_slider.position(20, 170)
        this.blending_mode_select = createSelect()
        this.blending_mode_select.position(20, 200)
        this.blending_mode_select.option(BLEND)
        this.blending_mode_select.option(ADD)
        this.blending_mode_select.option(LIGHTEST)
        this.blending_mode_select.option(DODGE)
        this.blending_mode_select.option(SOFT_LIGHT)

        // construct panel to display
        let panel = createGraphics(300, 300)
        panel.textSize(15)
        panel.noStroke()
        panel.fill("white")
        let text_x_pos = this.symmetry_slider.x * 2 + this.symmetry_slider.width
        panel.text("symmetry", text_x_pos, this.symmetry_slider.y + 15)
        panel.text("ring width", text_x_pos, this.ring_width_slider.y + 15)
        panel.text("border width", text_x_pos, this.border_width_slider.y + 15)
        panel.text("vertices", text_x_pos, this.vertices_slider.y + 15)
        panel.text("ellipseness", text_x_pos, this.ellipseness_slider.y + 15) 
        panel.text("color speed", text_x_pos, this.color_speed_slider.y + 15)
        panel.text("blending mode", text_x_pos, this.blending_mode_select.y + 15)
        this.panel = panel
    }

    show_ui() {
        this.symmetry_slider.show()
        this.ring_width_slider.show()
        this.border_width_slider.show()
        this.vertices_slider.show()
        this.ellipseness_slider.show()
        this.color_speed_slider.show()
        this.blending_mode_select.show()
    }

    hide_ui() {
        this.symmetry_slider.hide()
        this.ring_width_slider.hide()
        this.border_width_slider.hide()
        this.vertices_slider.hide()
        this.ellipseness_slider.hide()
        this.color_speed_slider.hide()
        this.blending_mode_select.hide()
    }

    border_visible() {return this.border_width_slider.value() > -5} // -5 is the minimum value
    if_to_fill() {return this.ring_width_slider.value() == 8}       // 8 is the maximum value

    get symmetry() {return this.symmetry_slider.value()}
    set symmetry(value) {this.symmetry_slider.value(value)}
    get ring_width() {return 2 ** this.ring_width_slider.value()}
    set ring_width(value) {this.ring_width_slider.value(Math.log2(value))}
    get border_width() {return 2 ** this.border_width_slider.value()}
    set border_width(value) {this.border_width_slider.value(Math.log2(value))}
    get n_vertices() {return this.vertices_slider.value()}
    set n_vertices(value) {this.vertices_slider.value(value)}
    get ellipseness() {return this.ellipseness_slider.value()}
    set ellipseness(value) {this.ellipseness_slider.value(value)}
    get color_speed() {return 2 ** this.color_speed_slider.value()}
    set color_speed(value) {this.color_speed_slider.value(Math.log2(value))}
    get blending_mode() {return this.blending_mode_select.value()}
    set blending_mode(value) {this.blending_mode_select.value(value)}
}
