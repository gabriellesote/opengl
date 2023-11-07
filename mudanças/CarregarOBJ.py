import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from PIL import Image
from io import BytesIO
from ObjLoader import ObjLoader


vertex_src = """
# version 330

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_texture;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 projection;
uniform mat4 view;

out vec2 v_texture;

void main()
{
    gl_Position = projection * view * model * vec4(a_position, 1.0);
    v_texture = a_texture;
}
"""

fragment_src = """
# version 330

in vec2 v_texture;

out vec4 out_color;

uniform sampler2D s_texture;

void main()
{
    out_color = texture(s_texture, v_texture);
}
"""

def load_texture_from_file(file_path):
    img = Image.open(file_path)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)  # Flips the image vertically (if necessary)
    img_data = img.tobytes()

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    glGenerateMipmap(GL_TEXTURE_2D)

    return texture_id

def window_resize(window, width, height):
    glViewport(0, 0, width, height)
    projection = pyrr.matrix44.create_perspective_projection_matrix(45, width / height, 0.1, 100)
    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)

if not glfw.init():
    raise Exception("glfw cannot be initialized!")

window = glfw.create_window(1280, 720, "My OpenGL window", None, None)

if not window:
    glfw.terminate()
    raise Exception("glfw window cannot be created!")

glfw.set_window_pos(window, 400, 200)
glfw.set_window_size_callback(window, window_resize)
glfw.make_context_current(window)

# Load textures directly in the code
textures = [load_texture_from_file("textura/watermelon.jpg"), load_texture_from_file("textura/tijolo.jpg")]

chibi_indices, chibi_buffer = ObjLoader.load_model("modelo/melancia.obj")
monkey_indices, monkey_buffer = ObjLoader.load_model("modelo/tijolo.obj")

shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

VAO = glGenVertexArrays(2)
VBO = glGenBuffers(2)

glBindVertexArray(VAO[0])
glBindBuffer(GL_ARRAY_BUFFER, VBO[0])
glBufferData(GL_ARRAY_BUFFER, chibi_buffer.nbytes, chibi_buffer, GL_STATIC_DRAW)

glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, chibi_buffer.itemsize * 8, ctypes.c_void_p(0))
glEnableVertexAttribArray(1)
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, chibi_buffer.itemsize * 8, ctypes.c_void_p(12))
glEnableVertexAttribArray(2)

glBindVertexArray(VAO[1])
glBindBuffer(GL_ARRAY_BUFFER, VBO[1])
glBufferData(GL_ARRAY_BUFFER, monkey_buffer.nbytes, monkey_buffer, GL_STATIC_DRAW)

glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, monkey_buffer.itemsize * 8, ctypes.c_void_p(0))
glEnableVertexAttribArray(1)
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, monkey_buffer.itemsize * 8, ctypes.c_void_p(12))
glEnableVertexAttribArray(2)

glUseProgram(shader)
glClearColor(0, 0.1, 0.1, 1)
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

projection = pyrr.matrix44.create_perspective_projection_matrix(45, 1280 / 720, 0.1, 100)
chibi_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, -5, -10]))
monkey_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([-4, 0, 0]))

view = pyrr.matrix44.create_look_at(pyrr.Vector3([0, 0, 8]), pyrr.Vector3([0, 0, 0]), pyrr.Vector3([0, 1, 0]))

model_loc = glGetUniformLocation(shader, "model")
proj_loc = glGetUniformLocation(shader, "projection")
view_loc = glGetUniformLocation(shader, "view")

glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)
glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

# Defina uma matriz de translação para mover a textura (exemplo: mover 0.1 na direção X)
texture_translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0.5, 0.5, 0.9]))

while not glfw.window_should_close(window):
    glfw.poll_events()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    rot_y = pyrr.Matrix44.from_y_rotation(0.8 * glfw.get_time())
    model = pyrr.matrix44.multiply(rot_y, chibi_pos)

    # Aplique a matriz de translação à matriz modelo para mover a textura
    model = pyrr.matrix44.multiply(texture_translation, model)

    glBindVertexArray(VAO[0])
    glBindTexture(GL_TEXTURE_2D, textures[0])
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)
    glDrawArrays(GL_TRIANGLES, 0, len(chibi_indices))

    rot_y = pyrr.Matrix44.from_y_rotation(-0.8 * glfw.get_time())
    model = pyrr.matrix44.multiply(rot_y, monkey_pos)

    # Aplique a matriz de translação à matriz modelo para mover a textura
    model = pyrr.matrix44.multiply(texture_translation, model)

    glBindVertexArray(VAO[1])
    glBindTexture(GL_TEXTURE_2D, textures[1])
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)
    glDrawArrays(GL_TRIANGLES, 0, len(monkey_indices))

    glfw.swap_buffers(window)

glfw.terminate()
