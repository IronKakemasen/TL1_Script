import bpy
import json  # JSONライブラリをインポート
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
    # リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0
        print("頂点を伸ばしました。")
        
        # オペレータの命令終了を通知
        return {'FINISHED'}

# オペレータ ICO球生成
class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_create_object"
    bl_label = "ICO球生成"
    bl_description = "ICO球を生成します"
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるコールバック関数
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
    
    # 拡張子フィルタ
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    
    # ファイルパスを格納する型プロパティ
    filepath: bpy.props.StringProperty(name="File Path", maxlen=1024, default="")

    # メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        print("シーンエクスポートを実行します。")
        print("出力先パス：" + self.filepath)
        
        # 保存するデータ全体の辞書
        data = {}
        data["objects"] = [] # 配列の作成
        
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
            
            # 配列にオブジェクトを1個追加
            data["objects"].append(object_data)
            
        # ファイルを開いてJSONデータを書き込む
        with open(self.filepath, "w", encoding="utf-8") as file:
            # 指定されたインデント数（4）でファイルに辞書を出力
            json.dump(data, file, indent=4)
            
        print("JSONファイルの書き込みが完了しました。")
        # オペレータの命令終了を通知
        return {'FINISHED'}

# トップバーの拡張メニュー
class TOPBAR_MT_my_menu(bpy.types.Menu):
    # Blenderがクラスを識別する為の固有の文字列
    bl_idname = "myaddon.topbar_mt_my_menu"
    # メニューのラベルとして表示される文字列
    bl_label = "MyMenu"
    # 著者表示用の文字列
    bl_description = "拡張メニュー by " + bl_info["author"]

    # サブメニューの描画
    def draw(self, context):
        # 1つ目の項目：「頂点を伸ばす」を追加
        self.layout.operator(MYADDON_OT_stretch_vertex.bl_idname, text=MYADDON_OT_stretch_vertex.bl_label)
        # 2つ目の項目：「ICO球生成」を追加
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname, text=MYADDON_OT_create_ico_sphere.bl_label)
        # 3つ目の項目：「シーンエクスポート」を追加
        self.layout.operator(MYADDON_OT_export_scene.bl_idname, text=MYADDON_OT_export_scene.bl_label)

    # 既存のメニューにサブメニューを追加
    def submenu(self, context):
        # ID指定でサブメニューを追加
        self.layout.menu(TOPBAR_MT_my_menu.bl_idname)


# Blenderに登録するクラスリスト
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
)


# Add-On有効化時コールバック
def register():
    # Blenderにクラスを登録
    for cls in classes:
        bpy.utils.register_class(cls)
        
    # メインメニューバー（画面最上部のバー）の「エディターメニュー」に自作メニューを追加
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)
    print("レベルエディタが有効化されました。")


# Add-On無効化時コールバック
def unregister():
    # メニューから項目を削除
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)
    
    # Blenderからクラスを削除
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    print("レベルエディタが無効化されました。")