import bpy
import math
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Level Editor Addon",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > FileName / Topbar > MyMenu",
    "description": "カスタムプロパティとファイル出力に対応したレベルエディタ",
    "category": "Object",
}

# ==========================================
# 1. 既存のオペレータ・メニュー（ダミー含む）
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
# 2. 新規：カスタムプロパティ ['file_name'] 追加Operator
# ==========================================
class MYADDON_OT_add_filename(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_filename"
    bl_label = "FileName 追加"
    bl_description = "['file_name']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # 今選択中のオブジェクトにカスタムプロパティを追加
        context.object["file_name"] = ""
        return {"FINISHED"}


# ==========================================
# 3. 新規：オブジェクトのファイルネームPanelクラス
# ==========================================
class OBJECT_PT_file_name(bpy.types.Panel):
    """オブジェクトのファイルネームパネル"""
    bl_idname = "OBJECT_PT_file_name"
    bl_label = "FileName"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    # サブメニューの描画
    def draw(self, context):
        # 今選択中のオブジェクトに 'file_name' があるかで分岐
        if "file_name" in context.object:
            # 既にプロパティがあれば、入力用のUI項目として表示
            self.layout.prop(context.object, '["file_name"]', text=self.bl_label)
        else:
            # プロパティがなければ、追加用ボタンを表示
            self.layout.operator(MYADDON_OT_add_filename.bl_idname)


# ==========================================
# 4. 強化：シーン出力エクスコーターOperator
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

    # 再帰的にシーンを解析して整形出力する関数
    def parse_scene_recursive(self, file, object, level):
        # 階層の深さに応じてタブインデントを作成
        indent = '\t' * level
        
        # オブジェクトタイプの出力
        self.write_and_print(file, indent + object.type)
        
        # トランスフォーム情報の取得と出力（ラジアンから度数法に変換）
        trans = object.location
        rot = [math.degrees(a) for a in object.rotation_euler]
        scale = object.scale
        
        self.write_and_print(file, indent + "T %f %f %f" % (trans.x, trans.y, trans.z))
        self.write_and_print(file, indent + "R %f %f %f" % (rot[0], rot[1], rot[2]))
        self.write_and_print(file, indent + "S %f %f %f" % (scale.x, scale.y, scale.z))
        
        # カスタムプロパティ 'file_name' があれば 'N' として出力
        if "file_name" in object:
            self.write_and_print(file, indent + "N %s" % object["file_name"])
            
        self.write_and_print(file, indent + 'END')
        self.write_and_print(file, '')

        # 子ノードへ進む（深さが1上がる）
        for child in object.children:
            self.parse_scene_recursive(file, child, level + 1)

    def execute(self, context):
        # ファイルオープン処理
        with open(self.filepath, "w", encoding="utf-8") as file:
            self.write_and_print(file, "SCENE")
            
            # 親のいない最上位のオブジェクトから順に解析スタート
            root_objects = [obj for obj in context.scene.objects if obj.parent is None]
            for obj in root_objects:
                self.parse_scene_recursive(file, obj, 0)
                
        return {'FINISHED'}


# ==========================================
# 5. クラスの登録リストと register / unregister
# ==========================================
# Blenderに登録するクラスリスト（スライドの指定通りの順番）
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
    MYADDON_OT_add_filename,
    OBJECT_PT_file_name,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()