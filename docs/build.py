#!/usr/bin/env python3
"""
Static site builder for redshiftzero.github.io
Converts Markdown posts to HTML and builds the static site structure.
"""

import os
import re
import shutil
import frontmatter
import markdown
from pathlib import Path
from datetime import datetime

class StaticSiteBuilder:
    def __init__(self, source_dir="../content", output_dir="."):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.posts = []

    def build(self):
        """Build the complete static site"""
        print("Building static site...")

        # Copy static assets
        self.copy_assets()

        # Convert posts
        self.convert_posts()

        # Generate index pages
        self.generate_index_pages()

        print("Static site built successfully!")

    def copy_assets(self):
        """Copy CSS, JS, images, and other static assets"""
        print("Copying static assets...")

        # Copy from current Hugo site
        assets_to_copy = [
            ("../css", "css"),
            ("../js", "js"),
            ("../img", "img"),
            ("../fonts", "fonts"),
            ("../icons", "icons"),
            ("../favicon.ico", "favicon.ico"),
            ("../manifest.json", "manifest.json"),
            ("../robots.txt", "robots.txt")
        ]

        for src, dst in assets_to_copy:
            src_path = Path(src)
            dst_path = self.output_dir / dst

            if src_path.exists():
                if src_path.is_file():
                    shutil.copy2(src_path, dst_path)
                else:
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                print(f"  Copied {src} -> {dst}")

    def convert_posts(self):
        """Convert Markdown posts to HTML"""
        print("Converting posts...")

        posts_dir = self.source_dir / "post"
        if not posts_dir.exists():
            print(f"Posts directory not found: {posts_dir}")
            return

        for md_file in posts_dir.glob("*.md"):
            self.convert_post(md_file)

    def convert_post(self, md_file):
        """Convert a single Markdown post to HTML"""
        print(f"  Converting {md_file.name}")

        # Parse frontmatter and content
        with open(md_file, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Handle Hugo-style +++ frontmatter
        if file_content.startswith('+++'):
            # Extract frontmatter between +++ markers
            frontmatter_match = re.match(r'^\+\+\+(.*?)\+\+\+\s*(.*)', file_content, re.DOTALL)
            if frontmatter_match:
                frontmatter_text = frontmatter_match.group(1)
                content_text = frontmatter_match.group(2)

                # Parse frontmatter manually
                post_metadata = {}
                for line in frontmatter_text.strip().split('\n'):
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                                                # Handle arrays
                        if value.startswith('[') and value.endswith(']'):
                            value = [item.strip().strip('"').strip("'") for item in value[1:-1].split(',')]

                        # Handle date conversion
                        if key == 'date':
                            try:
                                # Try to import dateutil, fallback to basic parsing if not available
                                try:
                                    from dateutil import parser
                                    value = parser.parse(value).replace(tzinfo=None)
                                except ImportError:
                                    # Fallback to basic datetime parsing
                                    value = datetime.strptime(value, "%Y-%m-%d")
                            except:
                                value = datetime.now()

                        post_metadata[key] = value

                # Create a post object similar to frontmatter
                class Post:
                    def __init__(self, metadata, content):
                        self.metadata = metadata
                        self.content = content

                    def get(self, key, default=None):
                        return self.metadata.get(key, default)

                post = Post(post_metadata, content_text)
            else:
                # Fallback to frontmatter library
                post = frontmatter.loads(file_content)
        else:
            # Use standard frontmatter library for YAML/TOML
            post = frontmatter.loads(file_content)

                # Extract metadata
        title = post.get('title', md_file.stem)
        date = post.get('date', datetime.now())

        # Handle date formatting - ensure it's timezone-naive for comparison
        if hasattr(date, 'replace'):
            # If it's a datetime object, make it timezone-naive
            if hasattr(date, 'tzinfo') and date.tzinfo is not None:
                date = date.replace(tzinfo=None)
        elif isinstance(date, str):
            # If it's a string, try to parse it
            try:
                # Try to import dateutil, fallback to basic parsing if not available
                try:
                    from dateutil import parser
                    date = parser.parse(date).replace(tzinfo=None)
                except ImportError:
                    # Fallback to basic datetime parsing
                    date = datetime.strptime(date, "%Y-%m-%d")
            except:
                date = datetime.now()

        slug = post.get('slug', md_file.stem)

                # Convert Markdown to HTML with improved line break handling
        md = markdown.Markdown(extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.footnotes',
            'markdown.extensions.def_list'
            # Removed nl2br to prevent weird line breaks
        ])

        # Clean up the content - remove any remaining frontmatter artifacts
        content = post.content.strip()

        # Remove any remaining frontmatter markers that might have been missed
        content = re.sub(r'^\+\+\+.*?\+\+\+\s*', '', content, flags=re.DOTALL)
        content = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)

                # Process reference links before Markdown conversion
        # Extract reference links and store them
        ref_links = {}
        ref_pattern = r'^\[([^\]]+)\]:\s*(.+)$'

        # Split content into lines and process reference links
        lines = content.split('\n')
        processed_lines = []
        in_code_block = False
        code_block_delimiter = None

        for line in lines:
            # Check if we're entering or exiting a code block
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_delimiter = line.strip()
                elif line.strip() == code_block_delimiter:
                    in_code_block = False
                    code_block_delimiter = None

            # Only process reference links when not in a code block
            if not in_code_block:
                match = re.match(ref_pattern, line.strip())
                if match:
                    # Store the reference link
                    ref_name = match.group(1)
                    ref_url = match.group(2).strip()
                    ref_links[ref_name] = ref_url
                    continue  # Skip this line in the content

            # Keep all other lines
            processed_lines.append(line)

        # Rejoin the content without reference links
        content = '\n'.join(processed_lines)

        # Normalize line breaks - but be more careful with code blocks
        # Only normalize outside of code blocks
        lines = content.split('\n')
        normalized_lines = []
        in_code_block = False
        code_block_delimiter = None

        for line in lines:
            # Check if we're entering or exiting a code block
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_delimiter = line.strip()
                elif line.strip() == code_block_delimiter:
                    in_code_block = False
                    code_block_delimiter = None
                normalized_lines.append(line)
            elif in_code_block:
                # Preserve all line breaks in code blocks
                normalized_lines.append(line)
            else:
                # Outside code blocks, normalize line breaks
                if line.strip() == '':
                    # Empty line - keep as paragraph break
                    normalized_lines.append('')
                else:
                    # Non-empty line - keep as is
                    normalized_lines.append(line)

        content = '\n'.join(normalized_lines)

        # Convert Markdown to HTML
        html_content = md.convert(content)

        # Replace reference link placeholders with actual links
        for ref_name, ref_url in ref_links.items():
            # Replace [ref_name] with actual links
            link_pattern = rf'\[{re.escape(ref_name)}\]'
            replacement = f'<a href="{ref_url}">{ref_name}</a>'
            html_content = re.sub(link_pattern, replacement, html_content)

        # Create post HTML
        post_html = self.create_post_html(title, date, html_content, slug)

        # Save to output directory - create both URL structures for compatibility
        # New structure: /posts/slug.html
        posts_dir = self.output_dir / "posts"
        posts_dir.mkdir(exist_ok=True)
        output_path = posts_dir / f"{slug}.html"

        # Old Hugo structure: /post/slug/index.html
        post_dir = self.output_dir / "post" / slug
        post_dir.mkdir(parents=True, exist_ok=True)
        hugo_output_path = post_dir / "index.html"

        # Write to both locations for URL compatibility
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(post_html)

        with open(hugo_output_path, 'w', encoding='utf-8') as f:
            f.write(post_html)

        # Store post info for index generation
        self.posts.append({
            'title': title,
            'date': date,
            'slug': slug,
            'summary': self.extract_summary(post.content)
        })

    def extract_summary(self, content, max_length=200):
        """Extract a summary from post content"""
        # Remove markdown formatting
        text = re.sub(r'[#*`]', '', content)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Remove links

        # Get first paragraph
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            summary = paragraphs[0]
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            return summary
        return ""

    def format_date(self, date):
        """Safely format a date object to string"""
        try:
            if hasattr(date, 'strftime'):
                return date.strftime('%Y.%m.%d')
            elif isinstance(date, str):
                return date
            else:
                return str(date)
        except:
            return str(date)

    def create_post_html(self, title, date, content, slug):
        """Create HTML for a single post"""
        # Use the base template and replace placeholders
        template_path = self.output_dir / "base-template.html"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # Replace placeholders
            html = template.replace("{{PAGE_TITLE}}", f"{title} | redshiftzero")
            html = html.replace("{{PAGE_DESCRIPTION}}", title)
            html = html.replace("{{CANONICAL_URL}}", f"https://www.redshiftzero.com/post/{slug}/")
            html = html.replace("{{OG_TYPE}}", "article")
            html = html.replace("{{TWITTER_CARD}}", "summary")
            html = html.replace("{{SCHEMA_TYPE}}", "Article")
            # Handle date formatting safely
            if hasattr(date, 'isoformat'):
                date_iso = date.isoformat()
            elif isinstance(date, str):
                date_iso = date
            else:
                date_iso = datetime.now().isoformat()

            html = html.replace("{{PUBLISH_DATE}}", date_iso)
            html = html.replace("{{MODIFIED_DATE}}", date_iso)
            html = html.replace("{{MAIN_CONTENT}}", f"""
                <article class="content post h-entry">
                    <h1 class="post-title p-name">{title}</h1>

                    <div class="post-meta">
                        <time datetime="{date_iso}" class="post-meta-item published dt-published">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" class="icon post-meta-icon">
                                <path d="M148 288h-40c-6.6 0-12-5.4-12-12v-40c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12zm108-12v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm96 0v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm-96 96v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm-96 0v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm192 0v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm96-260v352c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V112c0-26.5 21.5-48 48-48h48V12c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v52h128V12c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v52h48c26.5 0 48 21.5 48 48zm-48 346V160H48v298c0 3.3 2.7 6 6 6h340c3.3 0 6-2.7 6-6z"/>
                            </svg> {self.format_date(date)}
                        </time>
                    </div>

                    <div class="post-body e-content">
                        {content}
                    </div>
                </article>
            """)

            return html
        else:
            # Fallback to simple template if base-template.html doesn't exist
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | redshiftzero</title>
    <link rel="stylesheet" href="/css/meme.min.0c24096f9051894f1547a4f579eebdb58f9b546189c9b7bfe789edf9d4be9a9a.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="site-brand">
                <a href="/" class="brand">redshiftzero</a>
            </div>
        </header>

        <main class="main">
            <article class="content post">
                <h1 class="post-title">{title}</h1>
                <div class="post-meta">
                    <time datetime="{date.isoformat()}">{date.strftime('%Y.%m.%d')}</time>
                </div>
                <div class="post-body">
                    {content}
                </div>
            </article>
        </main>

        <footer class="footer">
            <div class="site-info">© 1969–2025 redshiftzero</div>
        </footer>
    </div>
</body>
</html>"""

    def generate_index_pages(self):
        """Generate index pages for categories and tags"""
        print("Generating index pages...")

        # Sort posts by date
        self.posts.sort(key=lambda x: x['date'], reverse=True)

        # Generate main index
        self.generate_main_index()



    def generate_main_index(self):
        """Generate the main index page with pagination"""
        print("  Generating main index with pagination...")

        # Sort posts by date (newest first)
        self.posts.sort(key=lambda x: x['date'], reverse=True)

        # Create pagination - show 5 posts per page
        posts_per_page = 5
        total_posts = len(self.posts)
        total_pages = (total_posts + posts_per_page - 1) // posts_per_page

        # Generate each page
        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * posts_per_page
            end_idx = min(start_idx + posts_per_page, total_posts)
            page_posts = self.posts[start_idx:end_idx]

            # Create page content
            posts_html = ""
            for post in page_posts:
                posts_html += f"""
                <article class="content post home h-entry">
                    <h2 class="post-title p-name">
                        <a href="/post/{post['slug']}/" class="summary-title-link u-url">{post['title']}</a>
                    </h2>

                    <div class="post-meta">
                        <time datetime="{post['date'].isoformat() if hasattr(post['date'], 'isoformat') else post['date']}" class="post-meta-item published dt-published">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" class="icon post-meta-icon">
                                <path d="M148 288h-40c-6.6 0-12-5.4-12-12v-40c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12zm108-12v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm96 0v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm-96 96v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm-96 0v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm192 0v-40c0-6.6-5.4-12-12-12h-40c-6.6 0-12 5.4-12 12v40c0 6.6 5.4 12 12 12h40c6.6 0 12-5.4 12-12zm96-260v352c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V112c0-26.5 21.5-48 48-48h48V12c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v52h128V12c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v52h48c26.5 0 48 21.5 48 48zm-48 346V160H48v298c0 3.3 2.7 6 6 6h340c3.3 0 6-2.7 6-6z"/>
                            </svg> {self.format_date(post['date'])}
                        </time>
                    </div>

                    <summary class="summary p-summary">
                        <p>{post['summary']}</p>
                    </summary>

                    <div class="read-more-container">
                        <a href="/post/{post['slug']}/" class="read-more-link">Read More »</a>
                    </div>
                </article>
                """

            # Create pagination links
            pagination_html = ""
            if total_pages > 1:
                pagination_html = '<ul class="pagination">'

                # Previous page
                if page_num > 1:
                    prev_page = page_num - 1
                    if prev_page == 1:
                        pagination_html += f'<li class="pagination-prev"><a href="/" rel="prev">&lt; Newer</a></li>'
                    else:
                        pagination_html += f'<li class="pagination-prev"><a href="/page/{prev_page}/" rel="prev">&lt; Newer</a></li>'

                # Page numbers
                for p in range(1, total_pages + 1):
                    if p == page_num:
                        pagination_html += f'<li class="pagination-item current"><span>{p}</span></li>'
                    elif p == 1:
                        pagination_html += f'<li class="pagination-item"><a href="/">{p}</a></li>'
                    else:
                        pagination_html += f'<li class="pagination-item"><a href="/page/{p}/">{p}</a></li>'

                # Next page
                if page_num < total_pages:
                    pagination_html += f'<li class="pagination-next"><a href="/page/{page_num + 1}/" rel="next">Older &gt;</a></li>'

                pagination_html += '</ul>'

            # Create the page HTML
            if page_num == 1:
                # Homepage
                page_html = self.create_homepage_html(posts_html, pagination_html)
                with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
                    f.write(page_html)
            else:
                # Other pages
                page_html = self.create_homepage_html(posts_html, pagination_html, page_num)
                page_dir = self.output_dir / "page" / str(page_num)
                page_dir.mkdir(parents=True, exist_ok=True)
                with open(page_dir / "index.html", 'w', encoding='utf-8') as f:
                    f.write(page_html)

        print(f"    Generated {total_pages} pages with {total_posts} posts total")

        # Also generate archive page
        self.generate_archive_page()

        # Generate about page
        self.generate_about_page()

    def create_homepage_html(self, posts_html, pagination_html, page_num=None):
        """Create homepage HTML with posts and pagination"""
        # Use the base template
        template_path = self.output_dir / "base-template.html"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # Replace placeholders
            title = "redshiftzero"
            if page_num and page_num > 1:
                title = f"redshiftzero - Page {page_num}"

            html = template.replace("{{PAGE_TITLE}}", title)
            html = html.replace("{{PAGE_DESCRIPTION}}", "Personal blog about cryptography, security, privacy, and technology.")
            html = html.replace("{{CANONICAL_URL}}", "https://www.redshiftzero.com/")
            html = html.replace("{{OG_TYPE}}", "website")
            html = html.replace("{{TWITTER_CARD}}", "summary")
            html = html.replace("{{SCHEMA_TYPE}}", "WebSite")
            html = html.replace("{{PUBLISH_DATE}}", "2025-02-15T00:00:00+00:00")
            html = html.replace("{{MODIFIED_DATE}}", "2025-03-09T11:04:37-04:00")
            html = html.replace("{{MAIN_CONTENT}}", f"""
                {posts_html}
                {pagination_html}
            """)

            return html
        else:
            # Fallback template
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="/css/meme.min.0c24096f9051894f1547a4f579eebdb58f9b546189c9b7bfe789edf9d4be9a9a.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="site-brand">
                <a href="/" class="brand">redshiftzero</a>
            </div>
        </header>

        <main class="main">
            {posts_html}
            {pagination_html}
        </main>

        <footer class="footer">
            <div class="site-info">© 1969–2025 redshiftzero</div>
        </footer>
    </div>
</body>
</html>"""

    def generate_archive_page(self):
        """Generate an archive page with all post titles"""
        print("  Generating archive page...")

        # Sort posts by date (newest first)
        self.posts.sort(key=lambda x: x['date'], reverse=True)

        # Create archive content
        archive_html = '<div class="archive-list">'
        for post in self.posts:
            date_str = post['date'].strftime('%Y.%m.%d') if hasattr(post['date'], 'strftime') else str(post['date'])
            archive_html += f"""
            <div class="archive-item">
                <time class="archive-date">{date_str}</time>
                <a href="/post/{post['slug']}/" class="archive-title">{post['title']}</a>
            </div>
            """
        archive_html += '</div>'

        # Create archive page HTML
        template_path = self.output_dir / "base-template.html"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            html = template.replace("{{PAGE_TITLE}}", "Archive | redshiftzero")
            html = html.replace("{{PAGE_DESCRIPTION}}", "Complete archive of all blog posts")
            html = html.replace("{{CANONICAL_URL}}", "https://www.redshiftzero.com/archive/")
            html = html.replace("{{OG_TYPE}}", "website")
            html = html.replace("{{TWITTER_CARD}}", "summary")
            html = html.replace("{{SCHEMA_TYPE}}", "WebPage")
            html = html.replace("{{PUBLISH_DATE}}", "2025-02-15T00:00:00+00:00")
            html = html.replace("{{MODIFIED_DATE}}", "2025-03-09T11:04:37-04:00")
            html = html.replace("{{MAIN_CONTENT}}", f"""
                <article class="content page">
                    <h1 class="page-title">Archive</h1>
                    <p>Complete list of all {len(self.posts)} blog posts:</p>
                    {archive_html}
                </article>
            """)

            # Save archive page
            archive_dir = self.output_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            with open(archive_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(html)
        else:
            # Fallback template
            archive_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive | redshiftzero</title>
    <link rel="stylesheet" href="/css/meme.min.0c24096f9051894f1547a4f579eebdb58f9b546189c9b7bfe789edf9d4be9a9a.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="site-brand">
                <a href="/" class="brand">redshiftzero</a>
            </div>
        </header>

        <main class="main">
            <article class="content page">
                <h1 class="page-title">Archive</h1>
                <p>Complete list of all {len(self.posts)} blog posts:</p>
                {archive_html}
            </article>
        </main>

        <footer class="footer">
            <div class="site-info">© 1969–2025 redshiftzero</div>
        </footer>
    </div>
</body>
</html>"""

            archive_dir = self.output_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            with open(archive_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(archive_html)

    def generate_about_page(self):
        """Generate an about page from Markdown content"""
        print("  Generating about page...")

        # Check if there's a Markdown about page
        about_md_path = Path("../content/about/index.md")
        if about_md_path.exists():
            # Convert Markdown to HTML
            with open(about_md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # Parse frontmatter and content
            if md_content.startswith('---'):
                # Extract frontmatter and content (YAML format)
                parts = md_content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    content_text = parts[2]
                else:
                    content_text = md_content
            elif md_content.startswith('+++'):
                # Extract frontmatter and content (Hugo format)
                parts = md_content.split('+++', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    content_text = parts[2]
                else:
                    content_text = md_content
            else:
                content_text = md_content

            # Convert Markdown to HTML
            import markdown
            md = markdown.Markdown(extensions=['fenced_code', 'tables', 'codehilite', 'toc', 'nl2br'])
            html_content = md.convert(content_text)

            # Use the base template
            template_path = self.output_dir / "base-template.html"
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()

                html = template.replace("{{PAGE_TITLE}}", "About | redshiftzero")
                html = html.replace("{{PAGE_DESCRIPTION}}", "About redshiftzero")
                html = html.replace("{{CANONICAL_URL}}", "https://www.redshiftzero.com/about/")
                html = html.replace("{{OG_TYPE}}", "website")
                html = html.replace("{{TWITTER_CARD}}", "summary")
                html = html.replace("{{SCHEMA_TYPE}}", "WebPage")
                html = html.replace("{{PUBLISH_DATE}}", "2025-02-15T00:00:00+00:00")
                html = html.replace("{{MODIFIED_DATE}}", "2025-03-09T11:04:37-04:00")
                html = html.replace("{{MAIN_CONTENT}}", f"""
                <article class="content page">
                    <h1 class="page-title">About</h1>
                    <div class="page-body">
                        {html_content}
                    </div>
                </article>
                """)

                about_dir = self.output_dir / "about"
                about_dir.mkdir(exist_ok=True)
                with open(about_dir / "index.html", 'w', encoding='utf-8') as f:
                    f.write(html)
                print("    Created about page from Markdown content")
            else:
                print("    Error: base template not found")
        else:
            print("    Warning: No about/index.md found, using placeholder")
            # Fallback to placeholder content
            template_path = self.output_dir / "base-template.html"
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()

                html = template.replace("{{PAGE_TITLE}}", "About | redshiftzero")
                html = html.replace("{{PAGE_DESCRIPTION}}", "About redshiftzero")
                html = html.replace("{{CANONICAL_URL}}", "https://www.redshiftzero.com/about/")
                html = html.replace("{{OG_TYPE}}", "website")
                html = html.replace("{{TWITTER_CARD}}", "summary")
                html = html.replace("{{SCHEMA_TYPE}}", "WebPage")
                html = html.replace("{{PUBLISH_DATE}}", "2025-02-15T00:00:00+00:00")
                html = html.replace("{{MODIFIED_DATE}}", "2025-03-09T11:04:37-04:00")
                html = html.replace("{{MAIN_CONTENT}}", """
                <article class="content page">
                    <h1 class="page-title">About</h1>
                    <div class="page-body">
                        <p>Welcome to my blog! I write about cryptography, security, privacy, and technology.</p>
                        <p>This is a placeholder about page. Create a <code>content/about/index.md</code> file to add your content.</p>
                    </div>
                </article>
                """)

                about_dir = self.output_dir / "about"
                about_dir.mkdir(exist_ok=True)
                with open(about_dir / "index.html", 'w', encoding='utf-8') as f:
                    f.write(html)
                print("    Created placeholder about page")

if __name__ == "__main__":
    builder = StaticSiteBuilder()
    builder.build()
