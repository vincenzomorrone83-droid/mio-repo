# Print

Renders the dossier to a paginated A4 PDF with [Paged.js](https://github.com/pagedjs/pagedjs).

```sh
npm install                       # pagedjs-cli
python3 fetch-fonts.py            # faces into ./fonts, once
cp ../build/<paper>/figures/*.png .
python3 build.py                  # screen dossier -> print.html
PUPPETEER_EXECUTABLE_PATH=/path/to/chrome \
  npx pagedjs-cli print.html -o dossier.pdf \
  --browserArgs="--no-sandbox,--disable-dev-shm-usage"
```

`build.py` does two things the screen version does not need. It moves each
margin note to follow the paragraph that cites it — on screen a grid places
them, but in a paginated flow a float lands on whatever page its source
position falls on, so notes left at the end of the markup print a page late.
And it swaps the remote font stylesheet for the local one.

`print.css` holds the paged rules: A4 with a wide outer margin for the notes,
running heads suppressed on the first page, page numbers, and `break-inside:
avoid` on equations, figures and the verification ledger.
