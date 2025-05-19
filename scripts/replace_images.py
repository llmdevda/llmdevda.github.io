import re
import sys
import pyperclip
from pathlib import Path

def replace_image_links(text, prefix):
    # 正则匹配 Markdown 图片链接：![](/xxx.png)
    pattern = re.compile(r'!\[\]\((/[^)]+)\)')
    # 替换为 ![](prefix + 路径)
    replaced_text = pattern.sub(lambda m: f"![]({prefix.rstrip('/')}{m.group(1)})", text)
    return replaced_text

def main():
    if len(sys.argv) != 3:
        print("用法: python script.py markdown文件路径 前缀URL")
        print("示例: python script.py README.md https://www.xxx.com")
        sys.exit(1)

    file_path = sys.argv[1]
    prefix = sys.argv[2]

    if not Path(file_path).is_file():
        print(f"文件未找到: {file_path}")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    replaced_content = replace_image_links(content, prefix)

    pyperclip.copy(replaced_content)
    print("✅ 替换完成，内容已复制到剪贴板。")

if __name__ == "__main__":
    main()
