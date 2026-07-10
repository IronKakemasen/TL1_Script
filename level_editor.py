import bpy
import math
import gpu
import gpu_extras.batch
import copy
import mathutils
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Level Editor Addon",
    "author": "Your Name",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > FileName / Collider",
    "description": "カスタムプロパティ、ファイル出力、ローカル/ワールド行列対応の動的コライダー描画に対応したレベルエディタ",
    "category": "Object",
}

# ==========================================
# 1. 既存のオペレータ・メニュー
# ==========================================
class MYADDON_OT_stretch_vertex(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_stretch_vertex"
    bl_label = "頂点を伸ばす"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        return {'FINISHED'}

class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_create_ico_sphere"
    bl_label = "ICO球生成"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        return {'FINISHED'}

class TOPBAR_MT_my_menu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_my_menu"
    bl_label = "MyMenu"
    def draw(self, context):
        pass


# ==========================================
# 2. FileName用：プロパティ追加＆Panelクラス
# ==========================================
class MYADDON_OT_add_filename(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_filename"
    bl_label = "FileName 追加"
    bl_description = "['file_name']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.object["file_name"] = ""
        return {"FINISHED"}

class OBJECT_PT_file_name(bpy.types.Panel):
    bl_idname = "OBJECT_PT_file_name"
    bl_label = "FileName"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        if "file_name" in context.object:
            self.layout.prop(context.object, '["file_name"]', text=self.bl_label)
        else:
            self.layout.operator(MYADDON_OT_add_filename.bl_idname)


# ==========================================
# 3. コライダー用カスタムプロパティ追加Operator
# ==========================================
class MYADDON_OT_add_collider(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_collider"
    bl_label = "コライダー 追加"
    bl_description = "['collider']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.object["collider"] = "BOX"
        context.object["collider_center"] = mathutils.Vector((0.0, 0.0, 0.0))
        context.object["collider_size"] = mathutils.Vector((2.0, 2.0, 2.0))
        return {"FINISHED"}


# ==========================================
# 4. コライダー設定Panelクラス
# ==========================================
class OBJECT_PT_collider(bpy.types.Panel):
    bl_idname = "OBJECT_PT_collider"
    bl_label = "Collider"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        if "collider" in context.object:
            self.layout.prop(context.object, '["collider"]', text="Type")
            self.layout.prop(context.object, '["collider_center"]', text="Center")
            self.layout.prop(context.object, '["collider_size"]', text="Size")
        else:
            # 自分で考えよう穴埋め：プロパティがない場合は追加Operatorのボタンを表示
            self.layout.operator(MYADDON_OT_add_collider.bl_idname)


# ==========================================
# 5. コライダー描画クラス（スライド準拠・行列掛け算対応版）
# ==========================================
class DrawCollider:
    handle = None

    @staticmethod
    def draw_collider():
        vertices = {"pos": []}
        indices = []

        offsets = [
            [-0.5, -0.5, -0.5], # 左手前
            [+0.5, -0.5, -0.5], # 右手前
            [-0.5, +0.5, -0.5], # 左上前
            [+0.5, +0.5, -0.5], # 右上前
            [-0.5, -0.5, +0.5], # 左手奥
            [+0.5, -0.5, +0.5], # 右手奥
            [-0.5, +0.5, +0.5], # 左上奥
            [+0.5, +0.5, +0.5], # 右上奥
        ]

        # 現在シーンのオブジェクトリストを走査
        for object in bpy.context.scene.objects:
            # 描画スキップ：コライダープロパティがなければ飛ばす
            if not "collider" in object:
                continue

            # 中心点、サイズの変数を宣言
            center = mathutils.Vector((0.0, 0.0, 0.0))
            size = mathutils.Vector((2.0, 2.0, 2.0))

            # プロパティから値を取得
            center[0] = object["collider_center"][0]
            center[1] = object["collider_center"][1]
            center[2] = object["collider_center"][2]
            size[0] = object["collider_size"][0]
            size[1] = object["collider_size"][1]
            size[2] = object["collider_size"][2]

            # 追加前の頂点数
            start = len(vertices["pos"])

            # Boxの8頂点分回す
            for offset in offsets:
                # オブジェクトの中心座標の代わりにコライダーの中心点を使う
                pos = copy.copy(center)
                
                # 中心点を基準に各頂点ごとにずらす
                pos[0] += offset[0] * size[0]
                pos[1] += offset[1] * size[1]
                pos[2] += offset[2] * size[2]
                
                # ローカル座標からワールド座標に変換（@演算子でワールド行列を掛ける）
                pos = object.matrix_world @ pos
                
                # 頂点データリストに座標を追加
                vertices['pos'].append(pos)

            # 12本の辺のインデックス登録
            indices.append([start + 0, start + 1])
            indices.append([start + 2, start + 3])
            indices.append([start + 0, start + 2])
            indices.append([start + 1, start + 3])
            indices.append([start + 4, start + 5])
            indices.append([start + 6, start + 7])
            indices.append([start + 4, start + 6])
            indices.append([start + 5, start + 7])
            indices.append([start + 0, start + 4])
            indices.append([start + 1, start + 5])
            indices.append([start + 2, start + 6])
            indices.append([start + 3, start + 7])

        if not vertices["pos"]:
            return

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", vertices, indices=indices)

        color = [0.5, 1.0, 1.0, 1.0] # 水色
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)


# ==========================================
# 6. シーン出力エクスポーターOperator（綺麗に整理版）
# ==========================================
class MYADDON_OT_export_scene(bpy.types.Operator, ExportHelper):
    bl_idname = "myaddon.myaddon_ot_export_scene"
    bl_label = "シーン出力"
    bl_description = "シーンの階層構造をテキストファイルに書き出します"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".txt"

    def write_and_print(self, file, text):
        file.write(text + "\n")
        print(text)

    def parse_scene_recursive(self, file, object, level):
        indent = '\t' * level
        self.write_and_print(file, indent + object.type)
        
        trans = object.location
        rot = [math.degrees(a) for a in object.rotation_euler]
        scale = object.scale
        
        self.write_and_print(file, indent + "T %f %f %f" % (trans.x, trans.y, trans.z))
        self.write_and_print(file, indent + "R %f %f %f" % (rot[0], rot[1], rot[2]))
        self.write_and_print(file, indent + "S %f %f %f" % (scale.x, scale.y, scale.z))
        
        if "file_name" in object:
            self.write_and_print(file, indent + "N %s" % object["file_name"])

        # カスタムプロパティ 'collider' の出力処理（自分で整理した綺麗な記述）
        if "collider" in object:
            self.write_and_print(file, indent + "C %s" % object["collider"])
            
            cc = object["collider_center"]
            self.write_and_print(file, indent + "CC %f %f %f" % (cc[0], cc[1], cc[2]))
            
            cs = object["collider_size"]
            self.write_and_print(file, indent + "CS %f %f %f" % (cs[0], cs[1], cs[2]))
            
        self.write_and_print(file, indent + 'END')
        self.write_and_print(file, '')

        for child in object.children:
            self.parse_scene_recursive(file, child, level + 1)

    def execute(self, context):
        with open(self.filepath, "w", encoding="utf-8") as file:
            self.write_and_print(file, "SCENE")
            root_objects = [obj for obj in context.scene.objects if obj.parent is None]
            for obj in root_objects:
                self.parse_scene_recursive(file, obj, 0)
        return {'FINISHED'}


# ==========================================
# 7. クラスの登録リストと register / unregister
# ==========================================
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
    MYADDON_OT_add_filename,
    OBJECT_PT_file_name,
    MYADDON_OT_add_collider,  # クラスリストに登録
    OBJECT_PT_collider,      # クラスリストに登録
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(
        DrawCollider.draw_collider, (), "WINDOW", "POST_VIEW"
    )
    print("レベルエディタ（Boxコライダー完全版）が有効化されました。")

def unregister():
    if DrawCollider.handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(DrawCollider.handle, "WINDOW")
        DrawCollider.handle = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("レベルエディタ（Boxコライダー完全版）が無効化されました。")

if __name__ == "__main__":
    register()