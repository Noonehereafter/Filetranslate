import os
import json
import uuid
import markdown
from ebooklib import epub
from typing import List, Dict, Optional

class EpubBuilder:
    def __init__(self, title: str, author: str, identifier: str = None):
        self.book = epub.EpubBook()
        self.book.set_identifier(identifier or str(uuid.uuid4()))
        self.book.set_title(title)
        self.book.set_language('vi')
        self.book.add_author(author)

        self.chapters = []
        self.toc = []
        self.spine = ['nav']

    def add_chapter(self, title: str, markdown_content: str, chapter_id: str = None) -> str:
        """
        Convert Markdown to HTML and add it as a chapter to the ePub.
        Returns success or error message.
        """
        try:
            if not chapter_id:
                chapter_id = f"chap_{len(self.chapters) + 1}"

            # Convert markdown to html (supporting tables, etc)
            html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])

            # Wrap in basic HTML structure
            full_html = f'''
            <html>
                <head>
                    <title>{title}</title>
                </head>
                <body>
                    <h1>{title}</h1>
                    {html_content}
                </body>
            </html>
            '''

            chapter = epub.EpubHtml(title=title, file_name=f'{chapter_id}.xhtml', lang='vi')
            chapter.content = full_html

            self.book.add_item(chapter)
            self.chapters.append(chapter)
            self.toc.append(chapter)
            self.spine.append(chapter)

            return json.dumps({"status": "success", "chapter_id": chapter_id, "title": title})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def build(self, output_path: str) -> str:
        """
        Finalize and write the ePub file to disk.
        """
        try:
            self.book.toc = tuple(self.toc)

            # Add default NCX and Nav file
            self.book.add_item(epub.EpubNcx())
            self.book.add_item(epub.EpubNav())

            # Define CSS style
            style = 'BODY {color: white;}'
            nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            self.book.add_item(nav_css)

            # Basic spine
            self.book.spine = self.spine

            # Write epub file
            epub.write_epub(output_path, self.book, {})
            return json.dumps({"status": "success", "output_path": output_path})
        except Exception as e:
            return json.dumps({"error": str(e)})

# Singleton or state manager for tool calling
_global_epub_builder = None

def init_epub(title: str, author: str) -> str:
    global _global_epub_builder
    _global_epub_builder = EpubBuilder(title, author)
    return json.dumps({"status": "initialized", "title": title, "author": author})

def append_chapter_to_epub(title: str, markdown_content: str) -> str:
    """
    Tool for AI to append a translated chapter to the epub.
    AI must provide a logical chapter title and the translated markdown content.
    """
    global _global_epub_builder
    if not _global_epub_builder:
        # Fallback init if AI forgot
        init_epub("Translated Book", "AI Translator")

    return _global_epub_builder.add_chapter(title, markdown_content)

def finish_epub_build(output_path: str) -> str:
    """
    Tool for AI to finish and save the epub.
    """
    global _global_epub_builder
    if not _global_epub_builder:
        return json.dumps({"error": "Epub builder not initialized"})

    res = _global_epub_builder.build(output_path)
    # Reset state after building
    _global_epub_builder = None
    return res
