# Static Site for redshiftzero.github.io

### Prerequisites

Install the required Python packages:

```bash
pip install python-frontmatter markdown
```

### Build Process

1. **Run the build script**:
   ```make
   ```

2. **The script will**:
   - Copy all static assets (CSS, JS, images, etc.)
   - Convert your Markdown posts to HTML
   - Generate index pages with pagination
   - Create archive page with all posts

3. Look at the site:
`make serve`

### Adding Posts

1. Create a new Markdown file in `../content/post/`
2. Add frontmatter with title, date, slug
3. Run the build script to convert to HTML
