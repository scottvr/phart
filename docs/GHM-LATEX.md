# An ASCII-Representation* Experiment 

As I was tossing around some ideas stemming from someone asking or phart to add mermaid script to its list of text formats it handles
(and I have to admit, that's another one of those things that sounds ludicrous - a tool that takes graph objects and renders digrams of them, 
using plain text to illustrate charts and diagrams in a lo-fi way, could output more compact text language describing the graph, that is then 
consumed by another tool that outputs a **Scalable Vector Graphic** - AND, while _ludicrous_, does actually sound useful. 

So, I'll get to the mermaid topic later, and I'll skip a lot of the explanation I want to give, and instead will just say that phart now can output
SVGs - but they're essentially virtual framebuffers for a terminal display, and instead of drawing the text to your tty, it draws them to an SVG
of what ***would* be on your screen**. So that' silly and all, but siller is that the first SVG style it output was really cheating, because it just
captured the text output, and wrapped it in `<PRE>` tags, and embeded the html inside an svg container. Voila! :-)

Cuz then of course, instead of just writing pretty styled **HTML of the Graph,** I wanted to capture the full ASCII glory - and ANSI glory too - 
just in different text presentation systems. SO... Yes, phart now - instead of directly outputting colorful HTML, it captures any ANSI ESC sequences along with the text, and  does a little translation to convert the codes from their Named Color to the HTML named color equivalent. 

## OH, YOU SILLY THING

So, not quite through doing silly things, I wanted to be able to somehow paste a `<pre>`-tagged, or fence-block of a diagram straigh from my terminal
without having to take a screenshot of the ones with color, and paste the text right into theae GitHub Markdown pages. I know I said I'd be quick;
I'm almost there... Long story a little less long that it could be, ** GitHub-Flavored Markdown **__ - while it does allow embedding of, yup, _mermaid syntax_,
which it will then convert to an SVG in your markdown using the **mermaidjsAPI**, and it's not what I wanted. I wanted the text, as it came out. 

So, I also learned that **GHFM **supports a GitHub-Flavored subset of MathJax. Having been playing with LaTex for the last year or so, I though there might
be a solution there (which itself could make this go on way longer if I tried to document it all.) Fast-fowarding to now, what I arrived at is a
hacky, glitchy way so that I can paste plain **ASCII text** in here, and have it display in a fixed(ish)-width font, and in color. One hint at the grueling
frtustration that ensued: Yo may notice that the diagram, while it is text and in color and all of the things I described, it is also strangely situated
in a Markdown bullet-list, one bullet per row. (The reason for this, not that any of this is justified, is that without an extra newline at every row,
GHM-MathJax will either 1) display your **LaTex** equation in Math-mode, with automagic setting and centering, which works against my goal of a fixed witdth
alignment, or 2) it will but a very thick blank line (like a **Paragraph indicator**) between every line of text. The bulleted list takes up less vertical 
space than a blank line does. It all fits very well within the generally unnecessary constraints within phart voluntarily works, though doesn't it?

Now, if you're still with  me this far.. Witness phart's new output target `markdown-latex` as it was meant to be seen, under very narrow suboptimal conditions:

----

${\mathtt{\textbf{\textcolor{#111111}{depth:~~~~5~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{max-depth:~~~~5~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{max-val~~~~32~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~┌─────┐~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~│~~~~001~~~~│~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~└─────┘~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{┌───}}}\mathtt{\textbf{\textcolor{#111111}{┤~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{│}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{└────┐}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~┌─────┐~~~~~┌─────┐}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~│~~~~002~~~~│~~~~~│~~~~-Z1~~~~│}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~└─────┘~~~~~└─────┘}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{┌───}}}\mathtt{\textbf{\textcolor{#111111}{┤~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{│}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{└────┐}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~┌─────┐~~~~~┌─────┐~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~│~~~~004~~~~│~~~~~│~~~~-F1~~~~│~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~└─────┘~~~~~└─────┘~~~~~~~~~.}}}}$

{----


Lol, it's not perfectly aligned, and I've put the puzzle of the non-fixed-width-but-superficially-resmbling-one-font that is used to display my 
GHFMD-MathJax-Latex "equation", and just stop-gapped for now with a napkin-math equation that alllows it to look as close to correct as it does now, which is
to say it came a long way since my first attempt at pasting a phart diagram in here. FWIW, just using straight-up markdown fences for a pre-formatted block:


``` math
_TILDE_SPACE_RATIO = 32.0 / 15.0
run_len = max(4, int(math.ceil((j i) * _TILDE_SPACE_RATIO)))
```

----

That's the lilttle equation I'm using to accomplish getting around every piece of that GH/MD/MJ/Latex/Tex/HTML pipeline you're reading this through.
What's funny, especially in light of the preposterous process I just described tfor getting that nonsense graph to display in color, centered, in 
teletype font on this page without using an embedded graphics file format, which _really _wanted to collapse any two-or-more consecutive spaces down 
to one. That, coupled with the bullet list, the tilde-space narrow-space compensation, and `.` as sentinal characters at the end of each run of spaces
so that some other strange, finicky, not-well-publicized security and style-compliance policy doesn't suddenly appear 20 rows in to wreck it all to 
hell printing to the screen an explosion in a punctuation factory. No, that's not what's funny. I mean, yeah.. it *is* funny, but it's not what i was 
leading up to when I said **"what's funny is...**__" 

What's funny is that that strange, complicated looking math syntax where I pasted the equation I'm using for compensating for strangely-varying 
glyph-widths to get that almost-"right" diagram to displaay here in test and in color, not centered, and all that stuff ...What's funny us that strangfe
mish-mash of mathematical notation under the image is actully just this, in a markdown fenced block that for grins I thought I'd see wht happened if I 
typed the word `math` inside the triple-tickls. All I acually wrote in that area above with the dquiggly math letters was:

```
_TILDE_SPACE_RATIO = 32.0 / 15.0
run_len = max(4, int(math.ceil((j - i) * _TILDE_SPACE_RATIO)))
```

Yeah. Its the ratio describfing the tilde character which coerces the LateX renderer behind the mathjax/ghfm backend system to actually 
predictably spit out space characters and respect them (so long as they are surrounded by sentiual dots. It seems fitting somehow that then I'd paste some straightforward  text into a rfened block designed to display it just right, and I'd end up getting properly ty[eset and renderer-as-math nonsense out of it. 
Some sort of ironic coincidence.  Anyway, as you see... **Phart is exploring New Media **to express itself through Math, Science, and Visual Arts.

We hope you'll join us again _Next Time_! 

****
----

*****You may notice that throught the code and the supporting documentaion I interchangeably swap in and out thte words _"Rendering"_ and _"Representation". _
So which is it? I'm not sure, but I've been unsure and consistent about mixing it up unintentionally, just using whichever word comes to mind at
the time of writing. It's obviously less important now that the acronym, but it seem a gift when I asked myself "So, what should I call a [**Python ASCII [Representation|Rendering] Tool**](https://github.com/scottvr/phart), anyway?" and noticed the freebie acronym.
__
