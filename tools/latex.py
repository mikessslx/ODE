import sys
import os

"""
LaTeX formatter

Usage:
    python latex.py [file1] [file2] ...

Description:
    Replaces $...$ with \\(...\\) for inline math and preserves \\$ and $$
"""

def replace_math_delimiters(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found!")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = []
        i = 0
        length = len(content)
        in_math = False
        
        # Parse content
        while i < length:
            # Check for escaped dollar \$
            if content[i] == '\\' and i + 1 < length and content[i+1] == '$':
                new_content.append('\\$')
                i += 2
                continue
            
            # Check for double dollar $$
            if content[i] == '$' and i + 1 < length and content[i+1] == '$':
                new_content.append('$$')
                i += 2
                continue
                
            # Check for single dollar $
            if content[i] == '$':
                if not in_math:
                    new_content.append('\\(')
                    in_math = True
                else:
                    new_content.append('\\)')
                    in_math = False
                i += 1
                continue
                
            new_content.append(content[i])
            i += 1

        final_content = "".join(new_content)
        
        # Save changes if any
        if content != final_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            print(f"  + Updated: {file_path}")
        else:
            print(f"  = No changes: {file_path}")

    except Exception as e:
        print(f"  ! Error processing {file_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python latex.py [file1] [file2] ...")
    else:
        print(f"Processing: {len(sys.argv)-1}")
        for arg in sys.argv[1:]:
            replace_math_delimiters(arg)
