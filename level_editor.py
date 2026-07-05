import bpy
import json
from bpy_extras.io_utils import ImportHelper

# ブレンダーに登録するアドオン情報
bl_info = {
    "name": "レベルエディタ",
    "author": "Taro Kamata",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "location": "",
    "description": "レベルエディタ",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"
}

# オペレータ 頂点を伸ばす
class MYADDON_OT_stretch_vertex(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_stretch_vertex"
    bl_label = "頂点を伸ばす"
    bl_description = "頂点座標を引っ張って伸ばします"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0
        print("頂点を伸ばしました。")
        return {'FINISHED'}

# オペレータ ICO球生成
class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_create_object"
    bl_label = "ICO球生成"
    bl_description = "ICO球を生成します"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add()
        print("ICO球を生成しました。")
        return {'FINISHED'}

# オペレータ シーンエクスポート
class MYADDON_OT_export_scene(bpy.types.Operator, ImportHelper):
    bl_idname = "myaddon.myaddon_ot_export_scene"
    bl_label = "シーンエクスポート"
    bl_description = "シーンの情報をエクスポートします"
    bl_options = {'REGISTER', 'UNDO'}
    
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    filepath: bpy.props.StringProperty(name="File Path", maxlen=1024, default="")

    def execute(self, context):
        print("シーンエクスポートを実行します。")
        print("出力先パス：" + self.filepath)
        
        # 保存するデータ全体の辞書
        data = {}
        data["objects"] = []
        
        # 全オブジェクトを走査する
        for object in bpy.context.scene.objects:
            # オブジェクト1個分の辞書
            object_data = {}
            object_data["name"] = object.name
            object_data["type"] = object.type
            
            # 位置
            object_data["location"] = [
                object.location.x,
                object.location.y,
                object.location.z
            ]
            
            # 回転（オイラー角）
            object_data["rotation"] = [
                object.rotation_euler.x,
                object.rotation_euler.y,
                object.rotation_euler.z
            ]
            
            # スケール
            object_data["scale"] = [
                object.scale.x,
                object.scale.y,
                object.scale.z
            ]
            
            # カスタムプロパティの辞書を初期化（新規追加箇所）
            object_data["custom_properties"] = {}
            
            # オブジェクト内の全プロパティのキーをループ処理
            for key in object.keys():
                # Blender内部用の管理データ（_RNA_UIなど）を除外する
                if key == "_RNA_UI":
                    continue
                # キーに対応する値をカスタムプロパティ用の辞書に格納
                object_data["custom_properties"][key] = object[key]
            
            # 配列にオブジェクトを1個追加
            data["objects"].append(object_data)
            
        # ファイルを開いてJSONデータを書き込む
        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
            
        print("JSONファイルの書き込みが完了しました。")
        return {'FINISHED'}

# トップバーの拡張メニュー
class TOPBAR_MT_my_menu(bpy.types.Menu):
    bl_idname = "myaddon.topbar_mt_my_menu"
    bl_label = "MyMenu"
    bl_description = "拡張メニュー by " + bl_info["author"]

    def draw(self, context):
        self.layout.operator(MYADDON_OT_stretch_vertex.bl_idname, text=MYADDON_OT_stretch_vertex.bl_label)
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname, text=MYADDON_OT_create_ico_sphere.bl_label)
        self.layout.operator(MYADDON_OT_export_scene.bl_idname, text=MYADDON_OT_export_scene.bl_label)

    def submenu(self, context):
        self.layout.menu(TOPBAR_MT_my_menu.bl_idname)

# Blenderに登録するクラスリスト
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)
    print("レベルエディタが有効化されました。")

def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    print("レベルエディタが無効化されました。")