import bpy
import math
import gpu
import gpu_extras.batch
import copy
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Level Editor Addon",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > FileName / Topbar > MyMenu",
    "description": "カスタムプロパティ、ファイル出力、3Dコライダー描画に対応したレベルエディタ",
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
# 2. カスタムプロパティ ['file_name'] 追加Operator
# ==========================================
class MYADDON_OT_add_filename(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_filename"
    bl_label = "FileName 追加"
    bl_description = "['file_name']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.object["file_name"] = ""
        return {"FINISHED"}


# ==========================================
# 3. オブジェクトのファイルネームPanelクラス
# ==========================================
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
# 4. 新規：コライダー描画クラス（Blenderクラスは継承しない）
# ==========================================
class DrawCollider:
    # 描画ハンドル
    handle = None

    # 3Dビューに登録する描画関数
    @staticmethod
    def draw_collider():
        # 頂点データ・インデックスデータを動的配列として初期化
        vertices = {"pos": []}
        indices = []

        # 各頂点の、オブジェクト中心からのオフセット（8点分）
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
        # 立方体のX, Y, Z方向サイズ（一律2にする）
        size = [2, 2, 2]

        # 現在シーンのオブジェクトリストを走査
        for object in bpy.context.scene.objects:
            # 追加前の頂点数
            start = len(vertices["pos"])

            # Boxの8頂点分回す
            for offset in offsets:
                # オブジェクトの中心座標をコピー
                pos = copy.copy(object.location)
                # 中心点を基準に各頂点ごとにずらす
                pos[0] += offset[0] * size[0]
                pos[1] += offset[1] * size[1]
                pos[2] += offset[2] * size[2]
                # 頂点データリストに座標を追加
                vertices["pos"].append(pos)

            # 前面を構成する辺の頂点インデックス (12本分を追加)
            indices.append([start + 0, start + 1])
            indices.append([start + 2, start + 3])
            indices.append([start + 0, start + 2])
            indices.append([start + 1, start + 3])
            # 奥面を構成する辺の頂点インデックス
            indices.append([start + 4, start + 5])
            indices.append([start + 6, start + 7])
            indices.append([start + 4, start + 6])
            indices.append([start + 5, start + 7])
            # 手前と奥を繋ぐ辺の頂点インデックス
            indices.append([start + 0, start + 4])
            indices.append([start + 1, start + 5])
            indices.append([start + 2, start + 6])
            indices.append([start + 3, start + 7])

        # 描画すべきデータがなければ何もしない
        if not vertices["pos"]:
            return

        # ビルトインのシェーダを取得（色指定のみの3D描画用）
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        # バッチを作成
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", vertices, indices=indices)

        # シェーダのパラメータ設定（水色: R=0.5, G=1.0, B=1.0, A=1.0）
        color = [0.5, 1.0, 1.0, 1.0]
        shader.bind()
        shader.uniform_float("color", color)
        
        # 描画
        batch.draw(shader)


# ==========================================
# 5. シーン出力エクスポーターOperator
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
# 6. クラスの登録リストと register / unregister
# ==========================================
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
    MYADDON_OT_add_filename,
    OBJECT_PT_file_name,
)

def register():
    # Blenderにクラスを登録
    for cls in classes:
        bpy.utils.register_class(cls)

    # 3Dビューに描画関数を追加（ハンドルを保存）
    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(
        DrawCollider.draw_collider, (), "WINDOW", "POST_VIEW"
    )
    print("レベルエディタが有効化されました。")

def unregister():
    # 3Dビューから描画関数を削除
    if DrawCollider.handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(DrawCollider.handle, "WINDOW")
        DrawCollider.handle = None

    # Blenderからクラスを削除
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("レベルエディタが無効化されました。")

if __name__ == "__main__":
    register()