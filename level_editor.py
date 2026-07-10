import bpy
import math
import gpu
import gpu_extras.batch
import copy
import mathutils
import json  # スクリプトの先頭でインポート
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Level Editor Addon",
    "author": "Your Name",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > FileName / Collider",
    "description": "カスタムプロパティ、動的Boxコライダー描画、および階層構造付きJSONシーンエクスポートに対応したレベルエディタ",
    "category": "Object",
}

# ==========================================
# 1. 既存のオペレータ・メニュー（ダミー）
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
# 2. FileName用プロパティ＆パネル
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
# 3. コライダー用プロパティ＆パネル
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
            self.layout.operator(MYADDON_OT_add_collider.bl_idname)


# ==========================================
# 4. コライダー描画クラス
# ==========================================
class DrawCollider:
    handle = None

    @staticmethod
    def draw_collider():
        vertices = {"pos": []}
        indices = []

        offsets = [
            [-0.5, -0.5, -0.5], [+0.5, -0.5, -0.5],
            [-0.5, +0.5, -0.5], [+0.5, +0.5, -0.5],
            [-0.5, -0.5, +0.5], [+0.5, -0.5, +0.5],
            [-0.5, +0.5, +0.5], [+0.5, +0.5, +0.5],
        ]

        for object in bpy.context.scene.objects:
            if not "collider" in object:
                continue

            center = mathutils.Vector((0.0, 0.0, 0.0))
            size = mathutils.Vector((2.0, 2.0, 2.0))

            center[0] = object["collider_center"][0]
            center[1] = object["collider_center"][1]
            center[2] = object["collider_center"][2]
            size[0] = object["collider_size"][0]
            size[1] = object["collider_size"][1]
            size[2] = object["collider_size"][2]

            start = len(vertices["pos"])

            for offset in offsets:
                pos = copy.copy(center)
                pos[0] += offset[0] * size[0]
                pos[1] += offset[1] * size[1]
                pos[2] += offset[2] * size[2]
                
                pos = object.matrix_world @ pos
                vertices['pos'].append(pos)

            indices.append([start + 0, start + 1])
            indices.append([start + 2, start + 3])
            indices.append([start + 0, start + 2])
            indices.append([start + 1, start + 3])
            indices.append([start + 4, start + 5])
            indices.append([start + 6, start + 7])
            indices.append([start + 4, start + 6])
            indices.append([start + 5, start + 7])
            indices.append([start + 0, start + 4])
            items = [[start + 1, start + 5], [start + 2, start + 6], [start + 3, start + 7]]
            indices.extend(items)

        if not vertices["pos"]:
            return

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", vertices, indices=indices)

        color = [0.5, 1.0, 1.0, 1.0]
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)


# ==========================================
# 5. シーン出力エクスポーターOperator (JSON版)
# ==========================================
class MYADDON_OT_export_scene(bpy.types.Operator, ExportHelper):
    bl_idname = "myaddon.myaddon_ot_export_scene"
    bl_label = "シーン出力"
    bl_description = "シーン情報をExportします"
    bl_options = {'REGISTER', 'UNDO'}

    # 出力するファイルの拡張子設定を ".scene" から ".json" に変更
    filename_ext = ".json"

    def parse_scene_recursive_json(self, data_parent, object, level):
        """オブジェクトを再帰的に走査してディクショナリにパックする関数"""
        # 1個分のjsonオブジェクト(辞書)を生成
        json_object = dict()
        json_object["type"] = object.type
        json_object["name"] = object.name

        # トランスフォーム情報の取得と変換
        trans, rot_quat, scale = object.matrix_local.decompose()
        rot = rot_quat.to_euler()
        
        # ラジアンから度数法に変換
        rot.x = math.degrees(rot.x)
        rot.y = math.degrees(rot.y)
        rot.z = math.degrees(rot.z)

        # トランスフォーム情報を登録
        transform = dict()
        transform["translation"] = (trans.x, trans.y, trans.z)
        transform["rotation"] = (rot.x, rot.y, rot.z)
        transform["scaling"] = (scale.x, scale.y, scale.z)
        json_object["transform"] = transform

        # カスタムプロパティ 'file_name' のパック
        if "file_name" in object:
            json_object["file_name"] = object["file_name"]

        # カスタムプロパティ 'collider' のパック
        if "collider" in object:
            collider = dict()
            collider["type"] = object["collider"]
            collider["center"] = object["collider_center"].to_list() # JSONで扱える配列に変換
            collider["size"] = object["collider_size"].to_list()     # JSONで扱える配列に変換
            json_object["collider"] = collider

        # 親のオブジェクトリストに自分を追加
        data_parent.append(json_object)

        # 子ノードがあれば再帰的に処理（入れ子構造の実現）
        if len(object.children) > 0:
            json_object["children"] = list()
            for child in object.children:
                self.parse_scene_recursive_json(json_object["children"], child, level + 1)

    def export_json(self):
        """JSON形式でファイルに出力"""
        
        # 保存する情報をまとめるdict
        json_object_root = dict()

        # ノード名
        json_object_root["name"] = "scene"
        # オブジェクトリストを作成
        json_object_root["objects"] = list()

        # #Todo: シーン内の全オブジェクト走査してパック
        for object in bpy.context.scene.objects:
            # ルートオブジェクト（親がいないもの）から走査を開始する
            if object.parent:
                continue
            self.parse_scene_recursive_json(json_object_root["objects"], object, 0)

        # #オブジェクトをJSON文字列にエンコード
        # スライドの指定通り json.JSONEncoder().encode() を使用
        # ※もし改行して見やすくしたい場合は、授業後に indent=4 を足すと綺麗になります！
        json_text = json.JSONEncoder().encode(json_object_root)

        # #コンソールに表示してみる
        print(json_text)

        # #ファイルをテキスト形式で書き出し用にオープン
        # #スコープを抜けると自動的にクローズされる
        with open(self.filepath, "wt", encoding="utf-8") as file:
            # #ファイルに文字列を書き込む
            file.write(json_text)

    def execute(self, context):
        print("シーン情報をExportします")
        
        # export() を呼び出していた箇所を export_json() の呼び出しに書き換える
        self.export_json()

        self.report({'INFO'}, "シーン情報をExportしました")
        print("シーン情報をExportしました")

        return {'FINISHED'}


# ==========================================
# 6. レジスト処理
# ==========================================
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
    MYADDON_OT_add_filename,
    OBJECT_PT_file_name,
    MYADDON_OT_add_collider,
    OBJECT_PT_collider,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(
        DrawCollider.draw_collider, (), "WINDOW", "POST_VIEW"
    )
    print("レベルエディタ（JSON完全準拠版）が有効化されました。")

def unregister():
    if DrawCollider.handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(DrawCollider.handle, "WINDOW")
        DrawCollider.handle = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("レベルエディタ（JSON完全準拠版）が無効化されました。")

if __name__ == "__main__":
    register()