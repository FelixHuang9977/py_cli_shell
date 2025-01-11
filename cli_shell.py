import os
import re
import sys
import readline
import importlib.util
import glob
import argparse
import termios
import tty
import subprocess
from typing import Dict, List

class CommandShell:
    def __init__(self, batch_command=None):
        self.commands: Dict[str, tuple] = {}  # 存儲命令名稱和對應的模組
        self.current_path = 'cmd'  # 當前目錄路徑
        self.batch_command = batch_command  # 批次模式的命令
        # 添加內建命令
        self.add_builtin_commands()
        self.load_commands()
        self.setup_readline()
        # 保存原始的終端設置
        self.old_settings = termios.tcgetattr(sys.stdin)
        # 當前的輸入緩衝
        self.current_buffer = ""
        self.going_quit=False
        self.max_size_to_clear_in_a_line=1
        # 命令歷史
        self.history = []
        self.history_index = 0
        # flags
        self.is_batch_mode=False
        self.is_show_builtin_command_in_help=False

    def add_builtin_commands(self):
        """添加內建命令"""
        # 添加 info 命令
        info_parser = argparse.ArgumentParser(description='(built-in) Show information about commands in current directory')
        info_parser.add_argument('-a', '--all', action='store_true',
                            help='Show full path and description')
        info_parser.add_argument('-p', '--path', action='store_true',
                            help='Show command path')
        self.commands['info'] = (None, info_parser)


    def find_commands_in_current_dir(self, base_path=None, prefix=''):
        """搜尋當前目錄及其子目錄中的所有命令"""
        if base_path is None:
            base_path = self.current_path
            
        commands = []
        
        try:
            items = [item for item in os.listdir(base_path) 
                    if item != '__pycache__']
        except OSError:
            return commands

        # 使用正則表達式匹配 cmd_xxx.py 格式的檔案
        cmd_pattern = re.compile(r'^cmd_[a-zA-Z0-9_]+\.py$')

        for item in sorted(items):
            full_path = os.path.join(base_path, item)
            
            if os.path.isdir(full_path):
                sub_commands = self.find_commands_in_current_dir(full_path, f"{prefix}{item}/")
                commands.extend(sub_commands)
                
            # 使用正則表達式檢查檔案名
            elif os.path.isfile(full_path) and cmd_pattern.match(item):
                command_name = item[4:-3]
                if prefix:
                    commands.append((f"{prefix}{command_name}", full_path))
                else:
                    commands.append((command_name, full_path))
                
        return commands

    def execute_info(self, args):
        """執行 info 命令"""
        commands = self.find_commands_in_current_dir()
        
        # 添加內建命令（如果在當前目錄可用）
        if 'info' in self.commands:
            commands.append(('info', 'Built-in command'))
        if 'cd' in self.commands:
            commands.append(('cd', 'Built-in command'))
        if 'list' in self.commands:
            commands.append(('list', 'Built-in command'))
        
        if not commands:
            print("\nNo commands available in current directory")
            return
            
        # 計算最長命令名稱的長度
        max_cmd_length = max(len(cmd[0]) for cmd in commands) if commands else 30
        
        # 獲取當前目錄的相對路徑
        current_rel_path = os.path.relpath(self.current_path, 'cmd')
        if current_rel_path == '.':
            current_rel_path = 'cmd'
        else:
            current_rel_path = f'cmd/{current_rel_path}'
        
        print(f"\nUser Commands in [{current_rel_path}] folder:")
        
        if args.all:
            # 顯示完整資訊
            for cmd_name, cmd_path in sorted(commands):
                if cmd_path == 'Built-in command':
                    pass
                    #desc = "Built-in command"
                    #print(f"  {cmd_name:<{max_cmd_length}} - {desc}")
                    #print(f"    Path: Built-in")
                    #print()
                else:
                    desc = self.get_command_description(cmd_path)
                    print(f"  {cmd_name:<{max_cmd_length}} - {desc}")
                    print(f"    Path: {cmd_path}")
                    print()
        elif args.path:
            # 顯示命令和路徑
            for cmd_name, cmd_path in sorted(commands):
                print(f"  {cmd_name:<{max_cmd_length}} - {cmd_path}")
        else:
            # 簡單列表
            for cmd_name, cmd_path in sorted(commands):
                if cmd_path == 'Built-in command':
                    desc = "Built-in command"
                    #print(f"  {cmd_name:<{max_cmd_length}} - {desc}")
                    pass
                else:
                    desc = self.get_command_description(cmd_path)
                    print(f"  {cmd_name:<{max_cmd_length}} - {desc}")

    def find_all_commands(self, base_path='cmd', prefix=''):
        """遞迴搜尋所有命令"""
        commands = []
    
        try:
            # 獲取目錄下的所有項目（排除 __pycache__）
            items = [item for item in os.listdir(base_path) 
                    if item != '__pycache__']
        except OSError:
            return commands

        # 使用正則表達式匹配 cmd_xxx.py 格式的檔案
        cmd_pattern = re.compile(r'^cmd_[a-zA-Z0-9_]+\.py$')

        # 遍歷所有項目
        for item in sorted(items):
            full_path = os.path.join(base_path, item)
        
            # 如果是目錄，遞迴搜尋
            if os.path.isdir(full_path):
                sub_commands = self.find_all_commands(full_path, f"{prefix}{item}/")
                commands.extend(sub_commands)
            
            # 如果是命令檔案
            elif os.path.isfile(full_path) and cmd_pattern.match(item):
                command_name = item[4:-3]  # 移除 'cmd_' 前綴和 '.py' 後綴
                if prefix:
                    commands.append((f"{prefix}{command_name}", full_path))
                else:
                    commands.append((command_name, full_path))
            
        return commands

    def get_command_description(self, filepath):
        """從命令檔案中獲取描述"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # 尋找 description 參數
                import re
                match = re.search(r'description=[\'"]([^\'"]+)[\'"]', content)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return "No description available"

    def execute_list(self, args):
        """執行 list 命令"""
        commands = self.find_all_commands()
        
        # 添加內建命令
        commands.append(('list', 'Built-in command'))
        if any(os.path.isdir(os.path.join(self.current_path, item)) 
            for item in os.listdir(self.current_path) 
            if item != '__pycache__'):
            commands.append(('cd', 'Built-in command'))
        
        # 計算最長命令名稱的長度
        max_cmd_length = max(len(cmd[0]) for cmd in commands) if commands else 30
    
        if args.all:
            # 顯示完整資訊
            print("\nAvailable commands: (help.a)")
            for cmd_name, cmd_path in sorted(commands):
                if cmd_path == 'Built-in command':
                    if self.is_show_builtin_command_in_help:
                        desc = "Built-in command"
                        print(f"  {cmd_name:<{max_cmd_length}} - {desc}")
                        print(f"    Path: Built-in")
                        print()
                else:
                    desc = self.get_command_description(cmd_path)
                    print(f"  {cmd_name:<{max_cmd_length}} - {desc}")
                    print(f"    Path: {cmd_path}")
                    print()
        elif args.path:
            # 顯示命令和路徑
            print("\nAvailable commands: (help.b)")
            for cmd_name, cmd_path in sorted(commands):
                print(f"  {cmd_name:<{max_cmd_length}} - {cmd_path}")
        else:
            # 簡單列表
            print("\nAvailable commands: (help.c)")
            for cmd_name, cmd_path in sorted(commands):
                if cmd_path == 'Built-in command':
                    desc = "Built-in command"
                else:
                    desc = self.get_command_description(cmd_path)
                print(f"  {cmd_name:<{max_cmd_length}} - {desc}")			


    def add_to_history(self, command: str):
        """添加命令到歷史記錄"""
        if command.strip():  # 只保存非空命令
            self.history.append(command)

    def get_prompt(self):
        """生成提示符號"""
        # 將完整路徑轉換為相對於 cmd 目錄的路徑
        rel_path = os.path.relpath(self.current_path, 'cmd')
        if rel_path == '.':
            return 'cmd> '
        else:
            return f'cmd/{rel_path}> '
    def load_commands(self):
        """載入當前目錄下的命令模組"""
        # 保存內建命令
        builtin_commands = {
            'info': self.commands.get('info')
        }
        
        # 清除命令
        self.commands.clear()
        
        # 恢復內建命令
        self.commands.update({k: v for k, v in builtin_commands.items() if v is not None})
        
        # 獲取當前目錄下的所有項目
        items = [item for item in os.listdir(self.current_path) 
            if item != '__pycache__']  # 排除 __pycache__ 目錄
        
        # 檢查是否有子目錄
        has_subdirs = any(os.path.isdir(os.path.join(self.current_path, item)) for item in items)
        
        # 只有在有子目錄的情況下才添加 cd 命令
        if has_subdirs:
            self.commands['cd'] = (None, self.create_cd_parser())
        
        # 使用正則表達式匹配 cmd_xxx.py 格式的檔案
        cmd_pattern = re.compile(r'^cmd_[a-zA-Z0-9_]+\.py$')
            
        # 載入命令模組
        for item in items:
            full_path = os.path.join(self.current_path, item)
            
            # 如果是 Python 檔案且以 cmd_ 開頭
            if os.path.isfile(full_path) and cmd_pattern.match(item):
                module_name = os.path.splitext(item)[0]
                command_name = module_name[4:]  # 移除 'cmd_' 前綴

                # 動態載入模組
                spec = importlib.util.spec_from_file_location(module_name, full_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 確保模組有必要的函數
                if hasattr(module, 'setup_parser') and hasattr(module, 'execute'):
                    parser = module.setup_parser()
                    self.commands[command_name] = (module, parser)

    def create_cd_parser(self):
        """創建 cd 命令的解析器"""
        parser = argparse.ArgumentParser(description='Change current directory')
        parser.add_argument('path', nargs='?', default='..',
                          help='Directory to change to (.. for parent directory)')
        return parser

    def execute_cd(self, args):
        """執行 cd 命令"""
        target_path = args.path
        
        if target_path == '..':
            # 移動到上層目錄，但不能超過 cmd 目錄
            if os.path.abspath(self.current_path) != os.path.abspath('cmd'):
                self.current_path = os.path.dirname(self.current_path)
        else:
            # 嘗試進入子目錄
            new_path = os.path.join(self.current_path, target_path)
            if os.path.isdir(new_path):
                self.current_path = new_path
            else:
                print(f"Directory not found: {target_path}")
                return

        if not self.is_batch_mode:
            print(f"Current directory: {self.current_path}")
        self.load_commands()  # 重新載入當前目錄的命令

    def get_available_dirs(self) -> List[str]:
        """獲取當前目錄下的子目錄"""
        dirs = []
        for item in os.listdir(self.current_path):
            if item == '__pycache__':  # 跳過 __pycache__ 目錄
                continue
            full_path = os.path.join(self.current_path, item)
            if os.path.isdir(full_path):
                dirs.append(item)
        return dirs

    def get_command_names(self) -> List[str]:
        """獲取所有可用的命令名稱"""
        return list(self.commands.keys())

    def get_command_options(self, command_name: str) -> List[str]:
        """獲取指定命令的所有可用選項"""
        if command_name not in self.commands:
            return []
        
        _, parser = self.commands[command_name]
        options = []
        for action in parser._actions:
            if action.option_strings:  # 只獲取選項參數
                options.extend(action.option_strings)
        return options

    def get_partial_matches(self, text: str) -> List[str]:
        """獲取部分匹配的命令或目錄"""
        if not text:
            return self.get_command_names() + self.get_available_dirs()

        matches = []
        # 匹配命令
        for cmd in self.get_command_names():
            if cmd.startswith(text):
                matches.append(cmd)
        # 匹配目錄
        for dir_name in self.get_available_dirs():
            if dir_name.startswith(text):
                matches.append(dir_name)
        return sorted(matches)

    def setup_readline(self):
        """設置 readline 的自動完成功能"""
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self.completer)
        readline.set_completer_delims(' \t\n')

    def show_help_for_current_input(self, buffer: str):
        """顯示當前輸入的幫助信息"""
        tokens = buffer.strip().split()
        current_token = tokens[-1] if tokens else ""
        
        print('\n')  # 新增一個空行，使輸出更清晰
        
        # 如果沒有輸入，顯示所有可用命令和目錄
        if not tokens:
            print("Available commands:")
            for cmd in sorted(self.commands.keys()):
                if cmd == 'cd':
                    pass
                    #print(f"  {cmd:<30} - Change directory")
                else:
                    _, parser = self.commands[cmd]
                    if not self.is_show_builtin_command_in_help and parser.description.startswith("(built-in)"):
                        pass
                    else:
                        print(f"  {cmd:<30} - {parser.description}")
            
            dirs = self.get_available_dirs()
            if dirs:
                print("\nSubdirectories:")
                for dir_name in sorted(dirs):
                    print(f"  {dir_name:<30} - Use 'cd {dir_name}' or '{dir_name}' to enter cmd folder")
            return
        # 如果有部分輸入，顯示匹配的命令和目錄
        matching_commands = []
        matching_dirs = []
        
        # 檢查命令匹配
        for cmd in sorted(self.commands.keys()):
            if cmd.startswith(current_token):
                if cmd == 'cd':
                    matching_commands.append((cmd, "Change directory"))
                else:
                    _, parser = self.commands[cmd]
                    matching_commands.append((cmd, parser.description))

        # 檢查目錄匹配
        for dir_name in sorted(self.get_available_dirs()):
            if dir_name.startswith(current_token):
                matching_dirs.append(dir_name)

        # 顯示匹配結果
        if matching_commands:
            if len(matching_commands) ==1:
                 #print("\nFull Matched commands:")
                 self.execute_command(f"{buffer} -h")
            else:
                print("\nMatching commands:")
                for cmd, desc in matching_commands:
                    print(f"  {cmd:<30} - {desc}")

        if matching_dirs:
            print("\nMatching directories:")
            for dir_name in matching_dirs:
                print(f"  {dir_name}/")

        if not matching_commands and not matching_dirs:
            print("No matches found")


    def completer(self, text: str, state: int) -> str:
        """實作自動完成功能"""
        buffer = self.current_buffer
        line = buffer.lstrip()
        tokens = line.split()

        # 如果正在輸入第一個詞
        if not tokens or (len(tokens) == 1 and not buffer.endswith(' ')):
            matches = self.get_partial_matches(text)
            if state < len(matches):
                return matches[state]
            return None

        # 如果是 cd 命令，自動完成目錄
        if tokens[0] == 'cd' and len(tokens) <= 2:
            matches = [d for d in self.get_available_dirs() if d.startswith(text)]
            if state < len(matches):
                return matches[state]
            return None

        # 如果正在輸入選項
        if len(tokens) >= 1:
            cmd = tokens[0]
            if cmd in self.commands:
                options = self.get_command_options(cmd)
                matches = [opt for opt in options if opt.startswith(text)]
                if state < len(matches):
                    return matches[state]
        return None

    def handle_tab(self, line: str) -> str:
        """處理 Tab 鍵自動完成"""
        self.current_buffer = line
        # 獲取當前單詞
        tokens = line.split()
        if not line or line[-1].isspace():
            current_word = ""
        else:
            current_word = tokens[-1] if tokens else ""

        # 使用 readline 的完成器獲取可能的完成項
        completions = []
        i = 0
        while True:
            completion = self.completer(current_word, i)
            if completion is None:
                break
            completions.append(completion)
            i += 1

        if not completions:
            return line

        # 如果只有一個完成選項，直接使用它
        if len(completions) == 1:
            if tokens:
                return ' '.join(tokens[:-1] + [completions[0]]) + ' '
            return completions[0] + ' '

        # 如果有多個完成選項，顯示它們
        print('\nPossible completions:')
        for comp in completions:
            print(f"  {comp}")
        
        # 找到共同前綴
        common_prefix = os.path.commonprefix(completions)
        if common_prefix:
            if tokens:
                return ' '.join(tokens[:-1] + [common_prefix])
            return common_prefix

        return line

    def get_input_with_immediate_help(self, prompt=""):
        """獲取輸入，同時處理即時幫助和自動完成"""
        line = []
        pos = 0
        sys.stdout.write(prompt)
        sys.stdout.flush()
        self.history_index = len(self.history)  # 重置歷史索引

        def refresh_line():
            self.max_size_to_clear_in_a_line=max((len(prompt) + len(line) + 1), self.max_size_to_clear_in_a_line)
            self.max_size_to_clear_in_a_line=min(255, self.max_size_to_clear_in_a_line)
                
            """重新顯示當前行，保持游標位置"""
            # 先回到行首
            sys.stdout.write('\r')
            # 清除整行
            sys.stdout.write(' ' * self.max_size_to_clear_in_a_line)
            # 回到行首並顯示提示符和當前行內容
            sys.stdout.write('\r' + prompt + ''.join(line))
            # 將游標移動到正確位置
            if pos < len(line):
                sys.stdout.write('\b' * (len(line) - pos))
            sys.stdout.flush()

        while True:
            try:
                c = self.getch()
                
                # 處理特殊鍵
                if c == '\x1b':  # ESC 序列
                    next1 = self.getch()
                    if next1 == '[':  # 方向鍵
                        next2 = self.getch()
                        if next2 == 'A':  # 上方向鍵
                            if self.history_index > 0:
                                self.history_index -= 1
                                line = list(self.history[self.history_index])
                                pos = len(line)
                                refresh_line()
                        elif next2 == 'B':  # 下方向鍵
                            if self.history_index < len(self.history):
                                self.history_index += 1
                                if self.history_index < len(self.history):
                                    line = list(self.history[self.history_index])
                                else:
                                    line = []
                                pos = len(line)
                                refresh_line()
                        elif next2 == 'C':  # 右方向鍵
                            if pos < len(line):
                                pos += 1
                                sys.stdout.write('\x1b[C')  # 向右移動游標
                                sys.stdout.flush()
                        elif next2 == 'D':  # 左方向鍵
                            if pos > 0:
                                pos -= 1
                                sys.stdout.write('\x1b[D')  # 向左移動游標
                                sys.stdout.flush()
                        elif next2 == 'H':  # Home 鍵
                            pos = 0
                            sys.stdout.write('\r' + prompt)
                            sys.stdout.flush()
                        elif next2 == 'F':  # End 鍵
                            pos = len(line)
                            refresh_line()
                        continue

                elif c == '\x03':  # Ctrl+C
                    line = []
                    raise KeyboardInterrupt
                elif c == '\x04':  # Ctrl+D
                    if not line:
                        print()
                        return None
                elif c == '\x7f':  # Backspace
                    if pos > 0:
                        line.pop(pos-1)
                        pos -= 1
                        refresh_line()
                elif c == '?':  # 問號鍵
                    # 顯示幫助
                    current_input = ''.join(line)
                    self.show_help_for_current_input(current_input)
                    # 重新顯示提示符和當前輸入
                    print(f"\n{prompt}{''.join(line)}", end='', flush=True)
                    # 將游標移動到正確位置
                    if pos < len(line):
                        sys.stdout.write('\b' * (len(line) - pos))
                    sys.stdout.flush()
                elif c == '\t':  # Tab
                    # 處理自動完成
                    current_input = ''.join(line)
                    new_input = self.handle_tab(current_input)
                    if new_input != current_input:
                        line = list(new_input)
                        pos = len(line)
                    refresh_line()
                elif c == '\r' or c == '\n':  # Enter
                    print()
                    command = ''.join(line)
                    self.add_to_history(command)  # 添加到歷史記錄
                    return command
                else:  # 一般字符
                    if ord(c) >= 32:  # 可印字符
                        # 在游標位置插入字符
                        line.insert(pos, c)
                        pos += 1
                        refresh_line()
            except KeyboardInterrupt:
                raise
        return ''.join(line)

    def getch(self):
        """獲取單個字符輸入"""
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            return ch

    def execute_command(self, command_line: str):
        """執行命令"""
        if not command_line.strip():
            return

        tokens = command_line.split()
        command_name = tokens[0]

        # 處理 ".." 作為特殊的返回上層目錄命令
        if command_name == "..":
            try:
                args = argparse.Namespace()
                args.path = ".."  # 明確設置 path 屬性
                self.execute_cd(args)
            except Exception as e:
                print(f"Error changing directory: {e}")
            return

        # 檢查是否是目錄名稱
        available_dirs = self.get_available_dirs()
        if command_name in available_dirs:
            # 如果輸入的是目錄名稱，自動使用 cd 命令
            try:
                args = argparse.Namespace()
                args.path = command_name  # 明確設置 path 屬性
                self.execute_cd(args)
            except Exception as e:
                print(f"Error changing directory: {e}")
            return

        if command_name not in self.commands:
            print(f"Unknown command: {command_name}")
            return

        if command_name == 'cd':
            parser = self.commands['cd'][1]
            try:
                args = parser.parse_args(tokens[1:])
                self.execute_cd(args)
            except SystemExit:
                pass
            return
        elif command_name == 'info':
            parser = self.commands['info'][1]
            try:
                args = parser.parse_args(tokens[1:])
                self.execute_info(args)
            except SystemExit:
                pass
            return

        # 處理一般命令
        module, parser = self.commands[command_name]
        try:
            parser.prog=tokens[0]
            args = parser.parse_args(tokens[1:])
            module.execute(args)
        except SystemExit:
            # 捕獲 argparse 的 exit
            pass
        except Exception as e:
            print(f"Error executing command: {e}")

    def execute_batch_command(self, command_line: str) -> bool:
        """執行批次命令
        
        Returns:
            bool: 命令執行是否成功
        """
        # 分割命令
        parts = command_line.strip().split()
        if not parts:
            return False

        current = 0
        while current < len(parts):
            # 檢查是否是目錄
            if os.path.isdir(os.path.join(self.current_path, parts[current])):
                # 嘗試進入目錄
                try:
                    args = argparse.Namespace()
                    args.path = parts[current]
                    self.execute_cd(args)
                    current += 1
                    continue
                except Exception as e:
                    print(f"Error changing directory: {e}")
                    return False

            # 構建剩餘的命令
            remaining_command = ' '.join(parts[current:])
            try:
                self.execute_command(remaining_command)
                return True
            except Exception as e:
                print(f"Error executing command: {e}")
                return False

        return True


    def reset_vt100(self):
        command = ['reset']
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def run(self):
        """運行命令列介面"""

        # 如果是批次模式
        if self.batch_command:
            self.is_batch_mode=True
            success = self.execute_batch_command(self.batch_command)
            # 恢復終端設置
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            # 根據執行結果設置退出碼
            sys.exit(0 if success else 1)
            return
        else:
            self.is_batch_mode=False
            self.reset_vt100()

        # 互動模式
        print(f"Welcome to CLI Shell: CWD:{self.current_path}")
        print(f"  Press '?' for help")
        print(f"  Use TAB for auto-completion")
        print(f"  Built-in commands: cd, exit, info")
        
        
        try:
            while True:
                try:
                    prompt = self.get_prompt()
                    command = self.get_input_with_immediate_help(prompt)
                    
                    if command is None:  # Ctrl+D
                        break
                        
                    if command.strip() == 'exit':
                        break
                    
                    if command.strip():
                        self.execute_command(command)
                        
                except KeyboardInterrupt:
                    if self.going_quit: 
                        print("\n")
                        break
                    print("\nPress Ctrl-C again or Use 'exit' to quit")
                    self.going_quit=True
                    # 給使用者一個短暫的時間來按第二次 Ctrl-C
                    try:
                        self.getch()
                    except KeyboardInterrupt:
                        print("\nExiting...")
                        break
                except Exception as e:
                    print(f"Error: {e}")
        finally:
            # 恢復終端設置
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
def reset_vt100():
    command = ['reset']
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {str(e)}")
                   
if __name__ == '__main__':
    bBatch=False
    for v in sys.argv:
        if v == "-c":
            bBatch=True
            
    if not bBatch:
        reset_vt100()
    
     # 添加命令行參數解析
    parser = argparse.ArgumentParser(description='CLI Shell')
    parser.add_argument('-c', '--command', 
                    help='Execute command in batch mode and exit')
    
    args = parser.parse_args()
    
    # 創建 shell 實例，傳入批次命令（如果有）
    shell = CommandShell(batch_command=args.command)
    shell.run()

