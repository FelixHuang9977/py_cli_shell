import os
import sys
import readline
import importlib.util
import glob
import argparse
import termios
import tty
from typing import Dict, List

class CommandShell:
    def __init__(self):
        self.commands: Dict[str, tuple] = {}  # 存儲命令名稱和對應的模組
        self.load_commands()
        self.setup_readline()
        # 保存原始的終端設置
        self.old_settings = termios.tcgetattr(sys.stdin)
        # 當前的輸入緩衝
        self.current_buffer = ""

    def load_commands(self):
        """遞迴載入 cmd 目錄及其子目錄下所有的命令模組"""
        for root, _, files in os.walk('cmd'):
            for file in files:
                if file.startswith('cmd_') and file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    # 計算相對路徑作為命令名稱
                    rel_path = os.path.relpath(full_path, 'cmd')
                    dir_path = os.path.dirname(rel_path)
                    module_name = os.path.splitext(os.path.basename(file))[0]
                    command_name = module_name[4:]  # 移除 'cmd_' 前綴

                    # 如果在子目錄中，將目錄名加入命令名稱
                    if dir_path and dir_path != '.':
                        command_name = f"{dir_path.replace(os.sep, '.')}.{command_name}"

                    # 動態載入模組
            spec = importlib.util.spec_from_file_location(module_name, full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 確保模組有必要的函數
            if hasattr(module, 'setup_parser') and hasattr(module, 'execute'):
                parser = module.setup_parser()
                self.commands[command_name] = (module, parser)

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
        """獲取部分匹配的命令或子目錄"""
        if not text:
            return self.get_command_names()

        # 取得所有命令名稱的唯一前綴（目錄）
        all_prefixes = set()
        for cmd in self.get_command_names():
            parts = cmd.split('.')
            for i in range(len(parts)):
                all_prefixes.add('.'.join(parts[:i+1]))

        # 找出匹配的命令和前綴
        matches = []
        for item in all_prefixes:
            if item.startswith(text):
                matches.append(item)
        return sorted(matches)

    def setup_readline(self):
        """設置 readline 的自動完成功能"""
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self.completer)
        readline.set_completer_delims(' \t\n')

    def show_help_for_current_input(self, buffer: str):
        """顯示當前輸入的幫助信息"""
        tokens = buffer.strip().split()
        
        print('\n')  # 新增一個空行，使輸出更清晰
        
        # 如果沒有輸入，顯示所有可用命令
        if not tokens:
            print("Available commands:")
            for cmd in sorted(self.commands.keys()):
                _, parser = self.commands[cmd]
                print(f"  {cmd:<30} - {parser.description}")
            return

        # 如果只輸入了部分命令名稱
        if len(tokens) == 1 and not buffer.endswith(' '):
            matches = self.get_partial_matches(tokens[0])
            if matches:
                print("Matching commands:")
                for cmd in matches:
                    if cmd in self.commands:
                        _, parser = self.commands[cmd]
                        print(f"  {cmd:<30} - {parser.description}")
                    else:
                        print(f"  {cmd}.*")
            return

        # 如果輸入了完整的命令，顯示該命令的幫助
        command_name = tokens[0]
        if command_name in self.commands:
            _, parser = self.commands[command_name]
            print("Command help:")
            parser.print_help()
            return

        print("Unknown command")

    def completer(self, text: str, state: int) -> str:
        """實作自動完成功能"""
        buffer = self.current_buffer
        line = buffer.lstrip()
        tokens = line.split()

        # 如果正在輸入命令或子目錄
        if not tokens or (len(tokens) == 1 and not buffer.endswith(' ')):
            matches = self.get_partial_matches(text)
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

        while True:
            c = self.getch()
            # 處理特殊鍵
            if c == '\x03':  # Ctrl+C
                print('^C')
                line = []
                break
            elif c == '\x04':  # Ctrl+D
                if not line:
                    print()
                    return None
            elif c == '\x7f':  # Backspace
                if pos > 0:
                    line.pop(pos-1)
                    pos -= 1
                    # 重新顯示行
                    sys.stdout.write('\r' + ' ' * (len(prompt) + len(line) + 1))
                    sys.stdout.write('\r' + prompt + ''.join(line))
                    sys.stdout.flush()
            elif c == '?':  # 問號鍵
                # 顯示幫助
                current_input = ''.join(line)
                self.show_help_for_current_input(current_input)
                # 重新顯示提示符和當前輸入
                print(f"\n{prompt}{''.join(line)}", end='', flush=True)
            elif c == '\t':  # Tab
                # 處理自動完成
                current_input = ''.join(line)
                new_input = self.handle_tab(current_input)
                if new_input != current_input:
                    # 清除當前行
                    sys.stdout.write('\r' + ' ' * (len(prompt) + len(line) + 1))
                    sys.stdout.write('\r' + prompt + new_input)
                    line = list(new_input)
                    pos = len(line)
                sys.stdout.write('\r' + prompt + ''.join(line))
                sys.stdout.flush()
            elif c == '\r' or c == '\n':  # Enter
                print()
                return ''.join(line)
            else:  # 一般字符
                if ord(c) >= 32:  # 可印字符
                    line.insert(pos, c)
                    pos += 1
                    # 重新顯示整行
                    sys.stdout.write('\r' + prompt + ''.join(line))
                    sys.stdout.flush()

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

        if command_name not in self.commands:
            print(f"Unknown command: {command_name}")
            return

        module, parser = self.commands[command_name]
        try:
            args = parser.parse_args(tokens[1:])
            module.execute(args)
        except SystemExit:
            # 捕獲 argparse 的 exit
            pass
        except Exception as e:
            print(f"Error executing command: {e}")

    def run(self):
        """運行命令列介面"""
        print("Welcome to CLI Shell")
        print("Type 'exit' to quit")
        print("Press '?' for help")
        print("Use TAB for auto-completion")
        
        while True:
            try:
                command = self.get_input_with_immediate_help('> ')
                
                if command is None:  # Ctrl+D
                    break
                    
                if command.strip() == 'exit':
                    break
                
                if command.strip():
                    self.execute_command(command)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")

        # 恢復終端設置
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

if __name__ == '__main__':
    shell = CommandShell()
    shell.run()