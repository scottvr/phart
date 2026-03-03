
## TL;DR:
I found a way to get colored plain text without html in GitHub-flavored Markdown, by using inline LaTeX math expressions, but it would either put every line on one line, or on multiple lines according to opinionated LaTeX/MathJax formatting, or I could do one per line, but each line was subject to the same (centering, etc) even after I found a way around the fact that the `\mathtt` 'teletype' font was not `monospace` by multiplying by a ratio to the number of space characters surrounded by sentinel characters in  my `plain-text-to-GFM()` routine, and further,  when I entered each inline LaTeX line on its own, a blank line was required between them in order to render a newline, but it added some larger `<P />`- equivalent between successive lines when rendered, so I used the Markdown bullet-point syntax to preface each of my lines of text, because the vertical space between items in a bulleted list is smaller than between two latex lines with a newline between them. *shrug*. 

If you want to skip straight to an example, [you can](https://github.com/scottvr/phart/blob/main/docs/GHM-LATEX.md#narrow-constraints-sub-optimal-conditions) and if you want to read more about how I came to that, you can come back up here to find all the stuff you you skipped by clicking that link. 

# An ASCII-Representation\*\* Experiment 

As I was tossing around some ideas stemming from someone asking for **phart** to add _mermaid script_ to its list of text formats it handles
(and I have to admit, that's another one of those things that sounds ludicrous - a tool that takes graph objects and renders visualizations of them, 
using plain text to illustrate charts and diagrams in a lo-fi way, could output more compact text language describing the graph, that is then 
consumed by another tool that outputs a **Scalable Vector Graphic** - AND, while _ludicrous_, does actually sound useful.) 

Oh, just in case you arrived here by _chance and fortune_ and have no idea what this is about, and should you wish to know whether you will have in any interest in reading this before you do so, this is a **Text Adventure** _(no, sorry. Not that kind)_  with [**Python Hierarchical ASCII [Representation|Rendering] Tool**](https://github.com/scottvr/phart).

## Mermaid in a Manhole

So, I'll get to the mermaid topic later, and I'll skip a lot of the exposition that I want to give, and instead will just say that phart now _can_ output
SVGs - but they're essentially virtual framebuffers for a terminal display, and instead of drawing the text to your tty, it draws them to an **SVG**
of what ***would* be on your screen**. So that's silly and all, but sillier is that the first SVG style it output was really cheating, because it just
captured the text output, and wrapped it in `<PRE>` tags, and embeded the html inside an svg container. Voila! :-)

Cuz then of course, instead of just writing pretty, styled _**HTML** of the Graph_, I wanted to capture the full **ASCII** glory - _and **ANSI** glory too_ - just within a _different_ text presentation system. So... _Yes,_  **phart** now - instead of directly outputting colorful _HTML_ as one might assume the solution _should_ be - captures any **ANSI** _ESC sequences_ along with the text, and then does a little translation to convert the codes from their _ANSI Named Color_ to their _HTML color_ equivalents. 


## OH, YOU SILLY THING

So, not quite through with doing silly things, I also wanted to be able to somehow paste a `<pre>`-tagged, or fenced-block of a diagram straight from my terminal (
without having to take a screenshot of the ones with color), and paste the text right into these _GitHub Markdown pages_. I know I said I'd be skipping a lot of explanation, sorry...
I'm _almost there_.  Long story a little less long than it could be, _**GitHub-Flavored Markdown**_ **(_GFM_)** - ("**GHFM**"? _"**GHFMD**"?_  Something of the sort.) while it does allow embedding of, wouldn't-cha-know, _mermaid syntax_, which then converts your short little text-symbolic description of the flow to an SVG in your markdown using the **mermaidjsAPI**, that is not what I wanted. I wanted the text, as it came out of **phart**. 

So, I also learned that **GHFM** supports a **G**itHub-**F**lavored subset of **M**ath**J**ax while trying to see how I could use **HTML/CSS** or somesuch to add color to text in **GHFM**x (or is that **GHFMDMJ**?)  Having been playing with LaTex for the last year or so, by which for a moment I thought there might be a solution therein - and there sorta was, insofar as it can be exploited for text-colorization, so long as you want to make that text inside of pretty-looking _math-formulas_, centered on the screeen and otherwise styled in ways that you _cannnot control_ - anyway, I decided I wasn't just going to take "no" for an answer.    

## A GLITCH IN THE MATRICE

Fast-foward _a few **hours**_ and here we are, with what I arrived at: a _hacky, glitchy_ method to paste plain **ASCII text** in a GHMD document, and to have it display in a fixed(_ish_)-width font, and **in color**s of _one's own choosing_.  A glimpse inside of the grueling
_frustration that ensued_:  You may notice that the diagram, while it _is_ text and _in color_ and all of the things I described, it is also strangely situated within a Markdown _bullet-list_, one bullet per screen row. The _reason_ for this, not that any of this is justified within _reason_, is that without an extra newline at every row, **GHMD-MathJax Flavors** will either _1)_ display your **LaTex** equation in Math-mode, with automagic _typesetting_ and centering, which works against my goal of a fixed width alignment, or _2)_ it will put a very thick blank line (like a **Paragraph indicator** `<P />`) between every line of **Tex**, or perhaps _Both_,  or _even more_ **unwanted things**. 

## A BULLET TO THE `<HEAD>`

The bulleted list, as it turns out, takes up less vertical space than the blank line between such **GHFMDMJTeXOMGLOL** lines. It all fits very well within the generally unnecessary constraints within which **phart** _deliberately_ does its work, though, _doesn't it_? It's also a little _glitchy and kludgy_; no comment on whether that also correlates to some properties of PHART as well.

Now, if you're still with  me this far.. Here _bear Witness_ to **phart**'s new output target `markdown-latex` as it _was meant to be seen_, which is to say, under very _narrow constraints in suboptimal conditions_:


----

### Narrow Constraints, Sub-optimal Conditions

----


- ${\mathtt{\textbf{\textcolor{#111111}{depth:~~~~5~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{max-depth:~~~~5~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{max-val~~~~32~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~┌─────┐~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~│~~~~001~~~~~│~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~└─────┘~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#00A000}{┌───}}}\mathtt{\textbf{\textcolor{#111111}{┤~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#00A000}{│}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#A00000}{└────┐}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#00A000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#A00000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~┌─────┐~~~~~┌─────┐}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~│~~~~002~~~~~│~~~~~│~~~~-Z1~~~~~│}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~└─────┘~~~~~└─────┘}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#00A000}{┌───}}}\mathtt{\textbf{\textcolor{#111111}{┤~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#00A000}{│}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#A00000}{└────┐}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#00A000}~~~~~{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#A00000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~┌─────┐~~~~~┌─────┐~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~│~~~~004~~~~~│~~~~~│~~~~-F1~~~~~│~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~└─────┘~~~~~└─────┘~~~~~~~~~.}}}}$

----


### Bonus Mini-Game: The Magic Bullet

One unintended side-effect of the **Bullet Magic** to get narrower vertical line-spacing, is that if you view this document on a portrait-oriented phone-screen where the entire diagram does not fit within the screen-space, you can side-swipe each line/row individually to scroll horizontally. I spent more time than I should have briskly swiping the rows of text to the left and watching pieces of the nodes bounce off the edge of the frame. 


### Einstein's Tilde-Space/Narrow-Space Time Conjecture

OK so, the diagram is not perfectly aligned, and I have some tweaking to do on the calculation I came up with to account for the fact that the `teletype` font being used by the **GFM+MJ** backend is _not_ actually a `monospaced` font.  I had to stop-gap for now with an _actual_ **napkin-math** _equation_ (as opposed to just some ascii art that I managed to get colors on in the manner describe by masquerading as several bullet-pointed individual math equations) that alllows the diagram to look _close-ish_ to correct as you see here now, which is to say it has been  long enough since the start of my first attempt at pasting a **phart diagram** in here, just a few - ok **several** - _short, sleepless hours_ overnight. It's not a highly _complex_ "solution", but it did take some tedious, error-filled exploration of a system I knew nothing about, and allowed me to get a bit creative in the process.  


**FWIW**, and utilizing a GHMD feature _as intended_, by just using straight-up markdown fences for a `pre-formatted block` here,  I can show you this:


``` math

_TILDE_SPACE_RATIO = 32.0 / 15.0
run_len = max(4, int(math.ceil((j i) * _TILDE_SPACE_RATIO)))

```


<br />

That's the lilttle equation I'm using to accomplish getting around the many obstacles to having what I wanted from that GH/MD/MJ/Latex/Tex/HTML pipeline you're reading this through.


What's funny - especially in light of the preposterous process I just described for getting that nonsense **phart graph** to display in color, centered, in a `teletype font` on _this_ page without using an embedded graphics file format, and which really, _really_ wanted to collapse any _two-or-more_ consecutive whitespaces down to one, _a la_ **html**, and which, coupled with the bulleted list and what I'm calling here now the **tilde-space narrow-space compensation factor**, along with a judicious application of  `.` as a sentinal character at the beginning and end of each run of such whitespaces  _(Yes, I see now that I should add an exception for the case when the run of spaces entirely completes a row, when it is ok to elide them completely. Then we won't have the distracting dots on the right-hand side to worry about aligning. I digress)_, where they're all working together so that some strange, finicky, not-well-publicized _security and style-compliance policy_ doesn't _suddenly appear 20 rows in_ to wreck it **all to hell** by printing the _raw LaTex math block quoted text_ to the screen like some _explosion in a punctuation factory_... No, that's not what's funny. I mean, it *is* funny, but it's not what I was leading up to when I said **"_what's funny is..._**" 

**_What's funny is_** that the strange, complicated looking math syntax where I pasted the equation I'm using for compensating for the strangely-varying 
_**glyph-widths**_ to get that _almost-"right"_ diagram to display here in **text** and in **color**, **_not_ centered**, and all that other stuff ... No. What's funny is that the strange **_mish-mash_** of mathematical notation above is not the complicated equation it appears to be; but it _is_ a corollary to a theme of this document: _displaying text with non-intuitive or ill-fitting lexical formatting can yield surprising (and sometimes useful) results_. 

That "equation" is actually just _this_, in a _markdown fenced block_. that just happened to appear that way when for grins I thought I'd see what would appear if I typed the word `math` instead of `python` inside the **triple-ticks** for automatic lexxing and syntax highlighting. All I actually pasted in that area above with the _squiggly math letters_ was not complicated math, just code copied straight from my IDE:

``` python
_TILDE_SPACE_RATIO = 32.0 / 15.0
run_len = max(4, int(math.ceil((j - i) * _TILDE_SPACE_RATIO)))
```

Yeah. Its just the ratio describing the width of the whitespace for each tilde character that coerces the LateX renderer behind the **mathjax/ghfm** backend system to actually predictably spit out space characters and respect them (_so long as they are surrounded by **sentinal dots**._) It seems fitting somehow that then I'd paste some straightforward text into a fenced block designed to display it just right, and I'd end up getting properly typeset-as-math **nonsense** out of it. I had to work _so hard_ for the _nonsense **I wanted**_.  That is fittingly _**IRONIC, man**_.  

The obvious finishing move is going to be to make one of those "SPACE_RATIO"s for all characters, and  not just the `-` or whatever I measured, I don't remember now but I do recall there was an even larger discrepency between the displayed letter 'M' and the width of the space and the `-`both, so I'll want to generate a map of all the characters in phart's character set and put each character * 80, one per row, measure that against what's actually displayed on the screen, and auto-generate a mapping, so all images will be square and true instead of slightly disheveled like in this first attempt.

Curious if anyone thinks up any other tricks similar to abusing bullet points to get a better vertical resolution out of **GFM*. Honestly, that was the first thing other than newlines, `<BR />`, div and span that I tried, so there may be a better way than I have found, but, also honestly, this hacky display technique is well-aligned with phart's aesthetica - "part's principles", if you will... so I'm ok with it.


### I AM _IRONIC_ MAN

Anyway, as you see... **Phart is exploring New Media** to express itself through _Math, Science, and Visual Arts_!

We hope you'll join us again _for our next adventure_ through **needless _ASCII Adventures_**! 


**&ast;&ast;** You may be the astute observer who notices that throughout the code and the supporting documentation, I repeatedly swap the words _"Rendering"_ and _"Representation"_ interchangeably as if I don't know the name of my own tool, or that perhaps the name has changed but the documentation updates lag behind the truth. 

So which is the correct word in **phart**'s expanded name? I'm not sure, but at least I've been unsure and _consistent_ about being ambiguous unintentionally, just using whichever word comes to mind at the time of writing since day one. It's obviously less important now that the acronym _is_ for all intents its full name, but it seemed a gift when I asked myself "So, what should I call a [**Python Hierarchical ASCII [Representation|Rendering] Tool**](https://github.com/scottvr/phart), anyway?" and the acronym just came as a freebie.


----
### Epilogue: _Latex Skidmarks_

And just for fun, if you scrolled _this far_:  here is the text inside the Markdown that creates that diagram in the bullet points up above.  
For the sake of not making you read something ludicrous and _silly ;-)_ I only reproduce the bottom layer of nodes here; you can click to view the source of the page if you really gotta see it all:


```
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~┌─────┐~~~~~~~~~~~~~~~~~~~~~~~~┌─────┐~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~│~~~~032~~~~│~~~~~~~~~~~~~~~~~~~~~~~~│~~~~005~~~~│~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~└─────┘~~~~~~~~~~~~~~~~~~~~~~~~└─────┘~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{┌───}}}\mathtt{\textbf{\textcolor{#111111}{┤~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{┌───}}}\mathtt{\textbf{\textcolor{#111111}{┤~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{│}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{└────┐}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{│}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{└────┐}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#008000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~.}}}\mathtt{\textbf{\textcolor{#800000}{v}}}\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{┌─────┐~~~~~┌─────┐~~~~~┌─────┐~~~~~┌─────┐~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{│~~~~-L1~~~~│~~~~~│~~~~-L2~~~~│~~~~~│~~~~-L3~~~~│~~~~~│~~~~-L4~~~~│~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{└─────┘~~~~~└─────┘~~~~~└─────┘~~~~~└─────┘~~~~~~~~~~~~~~~.}}}}$
- ${\mathtt{\textbf{\textcolor{#111111}{.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
```

----
