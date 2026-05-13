import os
import json
import uuid
import re
import markdown
from ebooklib import epub
from typing import List, Dict, Optional

class EpubBuilder:
    def __init__(self, title: str, author: str, identifier: str = None, base_dir: str = "output"):
        # Create output structure: base_dir/title/
        # safe title for folder name
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        if not safe_title:
            safe_title = "Document"

        self.workspace_dir = os.path.join(base_dir, safe_title)
        self.images_dir = os.path.join(self.workspace_dir, "images")
        self.md_filepath = os.path.join(self.workspace_dir, f"{safe_title}.md")
        self.meta_filepath = os.path.join(self.workspace_dir, f"{safe_title}_metadata.json")

        os.makedirs(self.workspace_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

        self.title = title
        self.author = author

        # Save metadata
        metadata = {
            "title": title,
            "author": author,
            "identifier": identifier or str(uuid.uuid4())
        }
        with open(self.meta_filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Clear/Create Markdown file
        with open(self.md_filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n*Author: {author}*\n\n---\n\n")

    def add_chapter(self, title: str, markdown_content: str) -> str:
        """
        Append the translated markdown content to the main .md file.
        Returns the workspace directory so AI knows where it's saved.
        """
        try:
            with open(self.md_filepath, "a", encoding="utf-8") as f:
                # Add a marker so we can easily split chapters later when building epub
                f.write(f"\n\n<!-- CHAPTER_BREAK -->\n")
                f.write(f"# {title}\n\n")
                f.write(markdown_content)
                f.write("\n")

            return json.dumps({"status": "success", "message": f"Appended to {self.md_filepath}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def build_epub(self) -> str:
        """
        Read the main .md file, split by chapters, parse markdown to HTML,
        embed local images, and write the final .epub file.
        """
        try:
            with open(self.meta_filepath, "r", encoding="utf-8") as f:
                meta = json.load(f)

            book = epub.EpubBook()
            book.set_identifier(meta["identifier"])
            book.set_title(meta["title"])
            book.set_language('vi')
            book.add_author(meta["author"])

            chapters = []
            toc = []
            spine = ['nav']

            # Read full markdown
            with open(self.md_filepath, "r", encoding="utf-8") as f:
                full_md = f.read()

            # Split by chapter marker
            raw_parts = full_md.split("<!-- CHAPTER_BREAK -->")

            # Add images to epub
            for filename in os.listdir(self.images_dir):
                img_path = os.path.join(self.images_dir, filename)
                if os.path.isfile(img_path):
                    with open(img_path, "rb") as f:
                        epub_img = epub.EpubImage()
                        epub_img.uid = filename
                        epub_img.file_name = f"images/{filename}"
                        epub_img.media_type = "image/jpeg" # simplified
                        epub_img.content = f.read()
                        book.add_item(epub_img)

            # Process chapters
            for i, part in enumerate(raw_parts):
                if not part.strip():
                    continue

                # Try to extract the chapter title from the first # Heading
                match = re.search(r'^#\s+(.+)$', part.strip(), flags=re.MULTILINE)
                chapter_title = match.group(1) if match else f"Chapter {i}"

                # Convert markdown to html (supporting tables, code, and images)
                html_content = markdown.markdown(part, extensions=['tables', 'fenced_code'])

                # Replace markdown image links relative path if needed,
                # Ebooklib expects links like src="images/file.jpg" which markdown renderer usually preserves.

                full_html = f'''
                <html>
                    <head>
                        <title>{chapter_title}</title>
                    </head>
                    <body>
                        {html_content}
                    </body>
                </html>
                '''

                chapter_id = f"chap_{i}"
                chapter = epub.EpubHtml(title=chapter_title, file_name=f'{chapter_id}.xhtml', lang='vi')
                chapter.content = full_html

                book.add_item(chapter)
                chapters.append(chapter)
                toc.append(chapter)
                spine.append(chapter)

            book.toc = tuple(toc)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # Default style
            style = 'BODY {color: black;}'
            nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            book.add_item(nav_css)

            book.spine = spine

            epub_out_path = os.path.join(self.workspace_dir, f"{os.path.basename(self.workspace_dir)}.epub")
            epub.write_epub(epub_out_path, book, {})

            return json.dumps({
                "status": "success",
                "epub_path": epub_out_path,
                "markdown_path": self.md_filepath,
                "images_dir": self.images_dir
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

# Singleton or state manager for tool calling
_global_epub_builder = None

def init_epub(title: str, author: str) -> str:
    global _global_epub_builder
    _global_epub_builder = EpubBuilder(title, author)
    return json.dumps({
        "status": "initialized",
        "workspace": _global_epub_builder.workspace_dir,
        "images_dir": _global_epub_builder.images_dir
    })

def append_chapter_to_epub(title: str, markdown_content: str) -> str:
    global _global_epub_builder
    if not _global_epub_builder:
        init_epub("Translated Book", "AI Translator")
    return _global_epub_builder.add_chapter(title, markdown_content)

def finish_epub_build(output_path: str = None) -> str:
    """
    output_path argument is kept for compatibility with the old tool signature,
    but the epub will automatically be saved in the workspace directory.
    """
    global _global_epub_builder
    if not _global_epub_builder:
        return json.dumps({"error": "Epub builder not initialized"})

    res = _global_epub_builder.build_epub()
    _global_epub_builder = None
    return res
