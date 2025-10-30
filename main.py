#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import glob
import shutil
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# ============================================================================
# 定数と設定
# ============================================================================

# 🎨 カラーパレット
COLORS = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'reset': '\033[0m',
}

# 📁 ディレクトリ設定
DEFAULT_DIRS = {
    'src': 'src',
    'dist': 'dist',
    'libs': 'libs',
}

# 🔤 フォント拡張子
FONT_EXTENSIONS = ["*.ttf", "*.TTF", "*.otf", "*.OTF", "*.woff", "*.WOFF", "*.woff2", "*.WOFF2"]

# 🎯 バリアブルフォント検出キーワード
VARIABLE_FONT_INDICATORS = [
    'variable', 'var', 'vf',  # 基本的なキーワード
    'wght', 'wdth', 'slnt', 'ital', 'opsz',  # 標準軸
    'crsv', 'shrp', 'mono', 'casl'  # 特殊軸
]

# 📝 文字セットファイル名
CHARSET_FILES = {
    'option': 'オプション.txt',
    'ascii': '半角英数字.txt',
    'symbol': '半角記号.txt',
    'hiragana': 'ひらがな.txt',
    'katakana': 'カタカナ.txt',
    'half_katakana': '半角カタカナ.txt',
    'full_ascii': '全角英数字.txt',
    'full_symbol': '全角記号.txt',
    'jis_level1': 'JIS第一水準漢字.txt',
    'jis_level2': 'JIS第二水準漢字.txt',
    'jis_level3': 'JIS第三水準漢字.txt',
    'jis_level4': 'JIS第四水準漢字.txt',
    'common_kanji': '第一水準漢字に含まれない常用漢字.txt',
    'name_kanji': '第一水準漢字に含まれない人名漢字.txt',
}

# 🔧 pyftsubset オプション
PYFTSUBSET_OPTIONS = {
    'layout_features': '--layout-features=*',
    'flavor_woff2': '--flavor=woff2',
    'glyph_names': '--glyph-names',
    'name_ids': '--name-IDs=*',
    'hinting_tables': '--hinting-tables=*',
}

# ============================================================================
# ユーティリティ関数
# ============================================================================

def colorize(text: str, color: str) -> str:
    """テキストに色を付ける"""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def print_header(text: str) -> None:
    """ヘッダー風の表示"""
    print(f"\n{'=' * 50}")
    print(f"  {text}")
    print(f"{'=' * 50}\n")

def ask_yes_no(question: str) -> bool:
    """y/n の質問をして結果を返す"""
    while True:
        response = input(f"📝 {question} {colorize('(y/n)', 'yellow')}: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print(colorize("⚠️  y または n で答えてください", 'red'))

def ensure_directory(directory: str) -> bool:
    """ディレクトリが存在しない場合は作成する"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        print(colorize(f"❌ {directory} ディレクトリの作成に失敗: {e}", 'red'))
        return False

def cleanup_temp_files(*file_paths: str) -> None:
    """一時ファイルを削除する"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(colorize(f"⚠️ {file_path} の削除に失敗: {e}", 'yellow'))

# ============================================================================
# フォント処理クラス
# ============================================================================

class FontProcessor:
    """フォント処理を担当するクラス"""
    
    def __init__(self, src_dir: str = DEFAULT_DIRS['src'], dist_dir: str = DEFAULT_DIRS['dist']):
        self.src_dir = src_dir
        self.dist_dir = dist_dir
        self.font_files = []
        self.variable_fonts = []
    
    def detect_font_files(self) -> List[str]:
        """フォントファイルを検出する"""
        font_files = []
        for extension in FONT_EXTENSIONS:
            pattern = os.path.join(self.src_dir, extension)
            font_files.extend(glob.glob(pattern))
        
        # 重複を除去してソート
        self.font_files = sorted(list(set(font_files)))
        return self.font_files
    
    def is_variable_font(self, font_path: str) -> bool:
        """バリアブルフォントかどうかを判定する"""
        font_name = os.path.basename(font_path).lower()
        return any(indicator in font_name for indicator in VARIABLE_FONT_INDICATORS)
    
    def get_variable_axes(self, font_path: str) -> List[str]:
        """バリアブルフォントの軸情報を取得する"""
        font_name = os.path.basename(font_path).lower()
        axes = []
        
        # 軸マッピング
        axis_mapping = {
            'wght': 'Weight (太さ)',
            'wdth': 'Width (幅)',
            'slnt': 'Slant (斜体)',
            'ital': 'Italic (イタリック)',
            'opsz': 'Optical Size (光学サイズ)',
            'crsv': 'Cursive (筆記体)',
            'shrp': 'Sharp (シャープ)',
            'mono': 'Monospace (等幅)',
            'casl': 'Casual (カジュアル)',
        }
        
        for key, description in axis_mapping.items():
            if key in font_name:
                axes.append(description)
        
        return axes
    
    def create_dummy_charset_file(self, file_path: str) -> bool:
        """全文字を含むダミーの文字セットファイルを作成する"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 基本的な文字範囲を追加
                char_ranges = [
                    (0x20, 0x7F),      # ASCII
                    (0x3040, 0x309F),  # ひらがな
                    (0x30A0, 0x30FF),  # カタカナ
                    (0x4E00, 0x9FAF),  # CJK統合漢字
                    (0x2000, 0x206F),  # 一般句読点
                    (0xFF00, 0xFFEF),  # 全角ASCII
                ]
                
                for start, end in char_ranges:
                    for i in range(start, end + 1):
                        try:
                            f.write(chr(i))
                        except ValueError:
                            continue
            return True
        except Exception as e:
            print(colorize(f"⚠️ ダミーファイル作成エラー: {e}", 'yellow'))
            return False
    
    def build_pyftsubset_command(self, font_path: str, text_file: str, 
                                is_subset_mode: bool, is_variable: bool) -> List[str]:
        """pyftsubsetコマンドを構築する"""
        font_name = os.path.basename(font_path)
        base_name = os.path.splitext(font_name)[0]
        output_name = f"{base_name}.woff2"
        output_path = os.path.join(self.dist_dir, output_name)
        
        if is_subset_mode:
            # サブセット化ありの場合
            cmd = [
                "pyftsubset",
                font_path,
                f"--text-file={text_file}",
                PYFTSUBSET_OPTIONS['layout_features'],
                PYFTSUBSET_OPTIONS['flavor_woff2'],
                f"--output-file={output_path}"
            ]
        else:
            # WOFF2変換のみの場合
            cmd = [
                "pyftsubset",
                font_path,
                f"--text-file={text_file}",
                PYFTSUBSET_OPTIONS['layout_features'],
                PYFTSUBSET_OPTIONS['flavor_woff2'],
                f"--output-file={output_path}"
            ]
        
        # バリアブルフォント用の追加オプション
        if is_variable:
            cmd.extend([
                PYFTSUBSET_OPTIONS['glyph_names'],
                PYFTSUBSET_OPTIONS['name_ids'],
                PYFTSUBSET_OPTIONS['hinting_tables'],
            ])
        
        return cmd
    
    def process_font(self, font_path: str, text_file: str, is_subset_mode: bool) -> bool:
        """単一フォントを処理する"""
        is_variable = self.is_variable_font(font_path)
        mode_text = "WOFF2変換のみ" if not is_subset_mode else "サブセット化"
        
        # コマンドを構築
        cmd = self.build_pyftsubset_command(font_path, text_file, is_subset_mode, is_variable)
        
        try:
            # 処理開始メッセージ
            font_name = os.path.basename(font_path)
            if is_variable:
                axes = self.get_variable_axes(font_path)
                axes_text = f"({', '.join(axes)})" if axes else ""
                print(f"🔄 処理中: {font_name} -> {font_name.replace('.ttf', '.woff2')} {colorize('(バリアブルフォント)', 'cyan')} {colorize(f'({mode_text})', 'yellow')} {colorize(axes_text, 'yellow')}")
            else:
                print(f"🔄 処理中: {font_name} -> {font_name.replace('.ttf', '.woff2')} {colorize(f'({mode_text})', 'yellow')}")
            
            # コマンド実行
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                if is_variable:
                    print(colorize(f"✅ 完了: {font_name.replace('.ttf', '.woff2')} (バリアブルフォント) ({mode_text})", 'green'))
                else:
                    print(colorize(f"✅ 完了: {font_name.replace('.ttf', '.woff2')} ({mode_text})", 'green'))
                return True
            else:
                print(colorize(f"❌ エラー: {font_name}", 'red'))
                print(colorize(f"エラー内容: {result.stderr}", 'red'))
                return False
        except Exception as e:
            print(colorize(f"❌ 実行エラー: {font_name} -> {e}", 'red'))
            return False

# ============================================================================
# レポート生成クラス
# ============================================================================

class ReportGenerator:
    """レポート生成を担当するクラス"""
    
    def __init__(self, dist_dir: str = DEFAULT_DIRS['dist']):
        self.dist_dir = dist_dir
    
    def generate_report(self, font_files: List[str], used_charsets: List[str], 
                       charset_contents: Dict[str, str], processor: FontProcessor) -> bool:
        """レポートを生成する"""
        try:
            now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
            report_path = os.path.join(self.dist_dir, "report.md")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                self._write_header(f, now)
                self._write_statistics(f, font_files, used_charsets, processor)
                self._write_font_list(f, font_files, processor)
                self._write_charset_info(f, used_charsets, charset_contents)
            
            return True
        except Exception as e:
            print(colorize(f"⚠️ report.md の生成に失敗: {e}", 'yellow'))
            return False
    
    def _write_header(self, f, timestamp: str) -> None:
        """ヘッダー部分を書き込む"""
        f.write("# サブセット化フォント\n\n")
        f.write(f"生成日時: {timestamp}\n\n")
    
    def _write_statistics(self, f, font_files: List[str], used_charsets: List[str], 
                         processor: FontProcessor) -> None:
        """統計情報を書き込む"""
        variable_count = len([f for f in font_files if processor.is_variable_font(f)])
        regular_count = len(font_files) - variable_count
        is_subset_mode = "サブセット化なし" not in used_charsets
        mode_text = "WOFF2変換のみ" if not is_subset_mode else "サブセット化"
        
        f.write("## 処理統計\n\n")
        f.write(f"- 処理モード: {mode_text}\n")
        f.write(f"- 通常フォント: {regular_count}個\n")
        f.write(f"- バリアブルフォント: {variable_count}個\n")
        f.write(f"- 合計: {len(font_files)}個\n\n")
    
    def _write_font_list(self, f, font_files: List[str], processor: FontProcessor) -> None:
        """フォントリストを書き込む"""
        f.write("## 生成されたフォントファイル\n\n")
        for font_path in font_files:
            font_name = os.path.basename(font_path)
            base_name = os.path.splitext(font_name)[0]
            output_name = f"{base_name}.woff2"
            is_variable = processor.is_variable_font(font_path)
            
            if is_variable:
                axes = processor.get_variable_axes(font_path)
                axes_text = f" ({', '.join(axes)})" if axes else ""
                f.write(f"- {output_name} (バリアブルフォント{axes_text})\n")
            else:
                f.write(f"- {output_name}\n")
        f.write("\n")
    
    def _write_charset_info(self, f, used_charsets: List[str], charset_contents: Dict[str, str]) -> None:
        """文字セット情報を書き込む"""
        f.write("## 使用できる文字\n\n")
        
        if used_charsets:
            for charset in used_charsets:
                if charset == "サブセット化なし":
                    f.write("### サブセット化なし\n\n")
                    f.write("全文字が含まれています\n\n")
                    continue
                
                section_name = charset.replace('.txt', '')
                f.write(f"### {section_name}\n\n")
                
                if charset in charset_contents and charset_contents[charset]:
                    content = charset_contents[charset]
                    f.write(f"{content}\n\n")
                else:
                    f.write("(内容なし)\n\n")
        else:
            f.write("- デフォルトの chars.txt を使用\n\n")

# ============================================================================
# 文字セット管理クラス
# ============================================================================

class CharsetManager:
    """文字セット管理を担当するクラス"""
    
    def __init__(self, libs_dir: str = DEFAULT_DIRS['libs']):
        self.libs_dir = libs_dir
        self.selected_content = []
        self.used_charsets = []
        self.charset_contents = {}
    
    def load_charset_file(self, filename: str, silent_if_empty: bool = False) -> str:
        """文字セットファイルを読み込む"""
        filepath = os.path.join(self.libs_dir, filename)
        
        if not os.path.exists(filepath):
            print(colorize(f"⚠️  {filename}が見つかりません", 'red'))
            return ""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 2行目以降を結合（1行目は説明なのでスキップ）
                if len(lines) > 1:
                    content = ''.join(line.strip() for line in lines[1:])
                else:
                    content = ''.join(line.strip() for line in lines)
                
                if content:
                    print(colorize(f"✅ {filename.replace('.txt', '')}を追加しました", 'green'))
                    return content
                else:
                    if not silent_if_empty:
                        print(colorize(f"⚠️  {filename}にデータがありません", 'yellow'))
                    return ""
        except Exception as e:
            print(colorize(f"❌ {filename}の読み込みエラー: {e}", 'red'))
            return ""
    
    def get_charset_description(self, filename: str) -> str:
        """文字セットファイルの1行目（説明）を取得する"""
        filepath = os.path.join(self.libs_dir, filename)
        if not os.path.exists(filepath):
            return filename.replace('.txt', '')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                return first_line if first_line else filename.replace('.txt', '')
        except Exception:
            return filename.replace('.txt', '')
    
    def add_charset_file(self, filename: str) -> None:
        """文字セットファイルを追加する"""
        content = self.load_charset_file(filename)
        if content:
            self.selected_content.append(content)
            self.used_charsets.append(filename)
            self.charset_contents[filename] = content
    
    def select_charsets(self) -> Tuple[bool, List[str], Dict[str, str]]:
        """文字セットファイルを選択する"""
        if not os.path.exists(self.libs_dir):
            print(colorize(f"⚠️  {self.libs_dir}ディレクトリが見つかりません", 'red'))
            print(colorize("デフォルトの chars.txt を使用します", 'yellow'))
            return True, [], {}
        
        print_header("⚙️ フォントサブセット化設定")
        
        # 0. サブセット化の有無を選択
        print(colorize("🔧 サブセット化の設定を選択してください", 'blue'))
        print()
        if ask_yes_no("サブセット化はせずにWOFF2変換のみを行いますか？"):
            print(colorize("✅ WOFF2変換のみを実行します（サブセット化なし）", 'green'))
            print()
            return True, ["サブセット化なし"], {"サブセット化なし": ""}
        else:
            print(colorize("✅ サブセット化を実行します", 'green'))
            print()
        
        # 文字セット選択処理
        self._select_basic_charsets()
        self._select_advanced_charsets()
        
        # 空のコンテンツを除去
        self.selected_content = [content for content in self.selected_content if content]
        
        if not self.selected_content:
            print(colorize("⚠️  文字セットが選択されませんでした", 'yellow'))
            print(colorize("デフォルトの chars.txt を使用します", 'blue'))
            return True, ["サブセット化なし"], {"サブセット化なし": ""}
        
        # 選択された文字セットを chars.txt に書き込み
        return self._write_charset_file()
    
    def _select_basic_charsets(self) -> None:
        """基本文字セットを選択する"""
        # オプション（必ず追加）
        option_content = self.load_charset_file(CHARSET_FILES['option'], silent_if_empty=True)
        if option_content:
            self.selected_content.append(option_content)
            print(colorize("🔧 オプション（基本文字）を自動追加しました", 'blue'))
            print()
        self.used_charsets.append(CHARSET_FILES['option'])
        self.charset_contents[CHARSET_FILES['option']] = option_content
        
        # 半角英数字
        if ask_yes_no("半角英数字を使用しますか？"):
            self.add_charset_file(CHARSET_FILES['ascii'])
        else:
            print(colorize("☑️ 半角英数字は追加されませんでした", 'magenta'))
        print()
        
        # 半角記号
        if ask_yes_no("半角記号を使用しますか？"):
            self.add_charset_file(CHARSET_FILES['symbol'])
        else:
            print(colorize("☑️ 半角記号は追加されませんでした", 'magenta'))
        print()
        
        # ひらがな
        if ask_yes_no("ひらがなを使用しますか？"):
            self.add_charset_file(CHARSET_FILES['hiragana'])
            print()
        else:
            print(colorize("☑️ ひらがなは追加されませんでした", 'magenta'))
            print()
            print("🔚 設問を終了します")
            print()
            print()
            return
    
    def _select_advanced_charsets(self) -> None:
        """高度な文字セットを選択する"""
        # カタカナ
        if ask_yes_no("カタカナを使用しますか？"):
            self.add_charset_file(CHARSET_FILES['katakana'])
            print()
            if ask_yes_no("半角カタカナを使用しますか？"):
                self.add_charset_file(CHARSET_FILES['half_katakana'])
            else:
                print(colorize("☑️ 半角カタカナは追加されませんでした", 'magenta'))
            print()
        else:
            print(colorize("☑️ カタカナは追加されませんでした", 'magenta'))
            print()
        
        # 全角英数字
        if ask_yes_no("全角英数字を使用しますか？"):
            self.add_charset_file(CHARSET_FILES['full_ascii'])
        else:
            print(colorize("☑️ 全角英数字は追加されませんでした", 'magenta'))
        print()
        
        # 全角記号
        if ask_yes_no("全角記号を使用しますか？"):
            self.add_charset_file(CHARSET_FILES['full_symbol'])
        else:
            print(colorize("☑️ 全角記号は追加されませんでした", 'magenta'))
        print()
        
        # JIS第一水準漢字
        if ask_yes_no("JIS第一水準漢字を使用しますか？"):
            self.add_charset_file(CHARSET_FILES['jis_level1'])
            self.add_charset_file(CHARSET_FILES['common_kanji'])
            self.add_charset_file(CHARSET_FILES['name_kanji'])
            print()
            
            # JIS第二水準漢字
            if ask_yes_no("JIS第二水準漢字を使用しますか？"):
                self.add_charset_file(CHARSET_FILES['jis_level2'])
                print()
                
                # JIS第三水準漢字
                if ask_yes_no("JIS第三水準漢字を使用しますか？"):
                    self.add_charset_file(CHARSET_FILES['jis_level3'])
                    print()
                    
                    # JIS第四水準漢字
                    if ask_yes_no("JIS第四水準漢字を使用しますか？"):
                        self.add_charset_file(CHARSET_FILES['jis_level4'])
                    else:
                        print(colorize("☑️ JIS第四水準漢字は追加されませんでした", 'magenta'))
                    print()
                    print("設問を終了します")
                    print()
                    print()
                else:
                    print(colorize("☑️ JIS第三水準漢字は追加されませんでした", 'magenta'))
                    print()
                    print("設問を終了します")
                    print()
                    print()
            else:
                print(colorize("☑️ JIS第二水準漢字は追加されませんでした", 'magenta'))
                print()
                print(colorize("設問を終了します", 'cyan'))
                print()
                print()
        else:
            print(colorize("☑️ JIS第一水準漢字は追加されませんでした", 'magenta'))
            print()
            print(colorize("設問を終了します", 'cyan'))
            print()
            print()
    
    def _write_charset_file(self) -> Tuple[bool, List[str], Dict[str, str]]:
        """文字セットファイルを書き込む"""
        try:
            # 重複を削除して結合
            all_chars = ''.join(self.selected_content)
            unique_chars = ''.join(sorted(set(all_chars)))
            
            with open('temp-chars.txt', 'w', encoding='utf-8') as f:
                f.write(unique_chars)
            return True, self.used_charsets, self.charset_contents
            
        except Exception as e:
            print(colorize(f"❌ temp-chars.txt の生成エラー: {e}", 'red'))
            return False, [], {}

# ============================================================================
# メイン処理
# ============================================================================

def main():
    """メイン処理"""
    # 文字セット選択
    charset_manager = CharsetManager()
    success, used_charsets, charset_contents = charset_manager.select_charsets()
    if not success:
        print(colorize("❌ 文字セット選択でエラーが発生しました。処理を終了します。", 'red'))
        return
    
    # フォント処理
    processor = FontProcessor()
    font_files = processor.detect_font_files()
    
    if not font_files:
        print(colorize(f"❌ エラー: {processor.src_dir} ディレクトリにフォントファイルが見つかりません", 'red'))
        print(colorize("サポート形式: .ttf, .otf, .woff, .woff2", 'yellow'))
        return
    
    # フォント情報表示
    print_header("🔍 サブセット化対象ファイル")
    variable_fonts = []
    for font_file in font_files:
        font_name = os.path.basename(font_file)
        is_variable = processor.is_variable_font(font_file)
        if is_variable:
            axes = processor.get_variable_axes(font_file)
            axes_text = f"({', '.join(axes)})" if axes else ""
            print(f"  • {font_name} {colorize('(バリアブルフォント)', 'cyan')} {colorize(axes_text, 'yellow')}")
            variable_fonts.append(font_file)
        else:
            print(f"  • {font_name}")
    print()
    
    if variable_fonts:
        print(colorize(f"📊 バリアブルフォント: {len(variable_fonts)}個検出", 'blue'))
        print()
    
    # 出力ディレクトリの準備
    if not ensure_directory(processor.dist_dir):
        return
    
    # 文字セットファイルの準備
    text_file = "temp-chars.txt"
    is_subset_mode = "サブセット化なし" not in used_charsets
    
    if not is_subset_mode:
        # WOFF2変換のみの場合、全文字を含むダミーファイルを作成
        dummy_chars_file = "temp-all-chars.txt"
        if not processor.create_dummy_charset_file(dummy_chars_file):
            print(colorize("⚠️ ダミーファイルの作成に失敗しました", 'yellow'))
            dummy_chars_file = text_file
        text_file = dummy_chars_file
    
    # フォント処理実行
    success_count = 0
    total_count = len(font_files)
    
    for font_path in font_files:
        if processor.process_font(font_path, text_file, is_subset_mode):
            success_count += 1
        print()
    
    # レポート生成
    report_generator = ReportGenerator(processor.dist_dir)
    report_generator.generate_report(font_files, used_charsets, charset_contents, processor)
    
    # 一時ファイルのクリーンアップ
    cleanup_temp_files(text_file, "temp-all-chars.txt")
    
    # 完了メッセージ
    print_header(f"✨ サブセット化完了! ({success_count}/{total_count} 成功)")

# ============================================================================
# 既存の関数（後方互換性のため）
# ============================================================================

if __name__ == "__main__":
    main()