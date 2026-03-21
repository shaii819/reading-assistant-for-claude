#!/usr/bin/env python3
"""Generate a minimal test EPUB fixture."""

from ebooklib import epub


def create_sample_epub(output_path: str):
    book = epub.EpubBook()
    book.set_identifier("test-book-001")
    book.set_title("The Art of Testing")
    book.set_language("en")
    book.add_author("Test Author")
    book.add_metadata("DC", "subject", "non-fiction")

    chapters = []
    contents = [
        ("Introduction", "This book explores the fundamentals of software testing. "
         "Testing is not just about finding bugs; it is about building confidence in code. "
         "As Dijkstra said, 'Testing shows the presence, not the absence, of bugs.' " * 20),
        ("Unit Testing", "Unit tests verify individual components in isolation. "
         "A good unit test is fast, isolated, and repeatable. "
         "The metaphor of a safety net captures the essence of unit testing — "
         "just as acrobats rely on nets to catch them, developers rely on tests. " * 20),
        ("Integration Testing", "Integration tests verify that components work together. "
         "For example, consider a payment system that must communicate with a bank API. "
         "The fact is that 70% of production bugs are found at integration boundaries. " * 20),
        ("Test Design", "Good test design follows the Arrange-Act-Assert pattern. "
         "This is analogous to the scientific method: set up conditions, run the experiment, observe results. "
         "The key insight is that tests are documentation — they describe what the code should do. " * 20),
        ("Conclusion", "Testing is an investment in software quality. "
         "The data shows that teams with comprehensive test suites ship 40% fewer bugs. "
         "Remember: 'The best time to write a test was before writing the code. "
         "The second best time is now.' " * 20),
    ]

    for i, (title, content) in enumerate(contents):
        ch = epub.EpubHtml(title=title, file_name=f"ch{i+1}.xhtml", lang="en")
        ch.content = f"<h1>{title}</h1><p>{content}</p>"
        book.add_item(ch)
        chapters.append(ch)

    book.toc = [(ch, ch.title) for ch in chapters]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    epub.write_epub(output_path, book)
    print(f"Created {output_path}")


if __name__ == "__main__":
    import os
    output = os.path.join(os.path.dirname(__file__), "fixtures", "sample.epub")
    os.makedirs(os.path.dirname(output), exist_ok=True)
    create_sample_epub(output)
