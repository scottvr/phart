# An ASCII-Representation* Experiment 

As I was tossing around some ideas stemming from someone asking for phart to add _mermaid script_ to its list of text formats it handles
(and I have to admit, that's another one of those things that sounds ludicrous - a tool that takes graph objects and renders visualizations of them, 
using plain text to illustrate charts and diagrams in a lo-fi way, could output more compact text language describing the graph, that is then 
consumed by another tool that outputs a **Scalable Vector Graphic** - AND, while _ludicrous_, does actually sound useful. 

So, I'll get to the mermaid topic later, and I'll skip a lot of the explanation I want to give, and instead will just say that phart now can output
SVGs - but they're essentially virtual framebuffers for a terminal display, and instead of drawing the text to your tty, it draws them to an **SVG**
of what ***would* be on your screen**. So that's silly and all, but sillier is that the first SVG style it output was really cheating, because it just
captured the text output, and wrapped it in `<PRE>` tags, and embeded the html inside an svg container. Voila! :-)

Cuz then of course, instead of just writing pretty, styled _**HTML** of the Graph_, I wanted to capture the full **ASCII** glory - _and **ANSI** glory too_ - just within a _different_ text presentation system. So... _Yes,_  **phart** now - instead of directly outputting colorful _HTML_ as one might assume the solution shoudld be - captures any **ANSI** _ESC sequences_ along with the text, and then does a little translation to convert the codes from their _ANSI Named Color_ to their _HTML named color_ equivalents. 


## OH, YOU SILLY THING

So, not quite through with doing silly things, I also wanted to be able to somehow paste a `<pre>`-tagged, or fenced-block of a diagram straight from my terminal (
without having to take a screenshot of the ones with color), and paste the text right into these _GitHub Markdown pages_. I know I said I'd be skipping a lot of explanation, sorry...
I'm _almost there_.  Long story a little less long that it could be, _**GitHub-Flavored Markdown**_ **(_GHFM_)** - while it does allow embedding of, wouldn't-cha-know, _mermaid syntax_, which then converts your short little text-symbolic description of the flow to an SVG in your markdown using the **mermaidjsAPI**, but it's not what I wanted. I wanted the text, as it came out of **phart**. 

So, I also learned that **GHFM** supports a **G**itHub-**F**lavored subset of **M**ath**J**ax while trying to see how I could use **HTML/CSS** or somesuch to add color to text in **GHFM**x (or is that **GHMD**? It's got some common abbreviation I'm sure,)  Having been playing with LaTex for the last year or so, by which for a momeent I thought there might be a solution therein. And there sorta was, insofar as it can be exploited for text-colorization, so long as you want to make that text inside of pretty-looking _math-formulas_, centered on the screeen and otherwise styled in ways that you _cannnot control_.    

## A GLITCH IN THE MATRICE

Fast-foward _a few **hours**_ and here we are, with what I arrived at: a _hacky, glitchy_ method to paste plain **ASCII text** in a GHMD document, and to have it display in a fixed(_ish_)-width font, and in colors of _one's own choosing_.  A glimpse inside of the grueling
_frustration that ensued_:  You may notice that the diagram, while it _is_ text and _in color_ and all of the things I described, it is also strangely situated within a Markdown _bullet-list_, one bullet per screen row. (The _reason_ for this, not that any of this is justified within _reason_, is that without an extra newline at every row, **GHMD-MathJax Flavors** will either _1)_ display your **LaTex** equation in Math-mode, with automagic _typesetting_ and centering, which works against my goal of a fixed witdth alignment, or _2)_ it will put a very thick blank line (like a **Paragraph indicator** `<P />`) between every line of **Tex**, or perhaps _Both_,  or _even more_ **unwanted things**. 

## A BULLET TO THE `<HEAD>`

The bulleted list, as it turns out, takes up less vertical space than the blank line between such **GHFMDMJ**L_OMG_ lines. It all fits very well within the generally unnecessary constraints within which **phart** _voluntarily_ does its work, though, _doesn't it_?

Now, if you're still with  me this far.. Here _bear Witness_ to **phart**'s new output target `markdown-latex` as it was meant to be seen, under very _narrow constraints in suboptimal conditions_:


----

### Narrow Constraints, Sub-optimal Conditions

----


- ${\mathtt{\textbf{\textcolor{#111111}{depth:~~~~5~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.}}}}$
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

----


### Einstein's Tilde-Space/Narrow-Space Time Conjecture

_Lol_. It's not perfectly aligned, but I have for the time being postponed my quest for the full solution to the puzzle of the _non-fixed-width-but-superficially-resembling-one font_ that is used to display my GHFMD-MathJax-Latex _text-diagram-posing-as-equation_, and just stop-gapped it for now with an _actual_ **napkin-math** _equation_ that alllows the diagram to look _close-ish_ to correct as you see here now, which is to say it has been  long enough since the start of my first attempt at pasting a **phart diagram** in here, just a few - ok **several** - _short, sleepless hours_ ago. It's not a highly _complex_ "solution", but it did take some tedious, error-filled exploration of a system I knew nothing about, and allowed me to get a bit creative in the process. 

**FWIW**, and utilizing a GHMD feature _as intended_, by just using straight-up markdown fences for a `pre-formatted block` here,  I can show you this:


``` math

_TILDE_SPACE_RATIO = 32.0 / 15.0
run_len = max(4, int(math.ceil((j i) * _TILDE_SPACE_RATIO)))

```


<br />

That's the lilttle equation I'm using to accomplish getting around the many obstacles to having what I wanted from that GH/MD/MJ/Latex/Tex/HTML pipeline you're reading this through.


What's funny, especially in light of the preposterous process I just described for getting that nonsense **phart graph** to display in color, centered, in a `teletype font` on _this_ page without using an embedded graphics file format, and which really, _really_ wanted to collapse any _two-or-more_ consecutive whitespaces down to one, a la **html**. That utimately, coupled with the bulleted list, and what I'm calling here now the **tilde-space narrow-space compensation factor**, along with a judicious application of  `.` as a sentinal character at the beginning and end of each run of such whitespaces  _(Yes, I see now that I should add an exception for the case when the run of spaces entirely completes a row, when it is ok to elide them completely. Then we won't have the distracting dots on the right hand side to worry about having aligned. I digress)_ so that some other strange, finicky, not-well-publicized security and style-compliance policy doesn't _suddenly appear 20 rows in_ to wreck it **all to hell** by printing my text to the screen like some _explosion in a punctuation factory_... No, that's not what's funny. I mean, yeah.. it *is* funny, but it's not what i was leading up to when I said **"what's funny is...**__" 

What's funny is that that strange, complicated looking math syntax where I pasted the equation I'm using for compensating for strangely-varying 
**glyph-widths**__ to get that _almost-"right"_ diagram to displaay here in **text** and in **color**, **_not_ centered**, and all that other stuff ... No. What's funny us that the strange
**mish-mash**__ of mathematical notation above is actually just this, in a _markdown fenced block_. that appeared when for grins I thought I'd see what happened if I typed the word `math` inside the **triple-ticks**__ for automatic lexxing and syntax highlighting. All I actually typed in that area above with the _squiggly math letters_ was:

```
_TILDE_SPACE_RATIO = 32.0 / 15.0
run_len = max(4, int(math.ceil((j - i) * _TILDE_SPACE_RATIO)))
```

Yeah. Its just the ratio describfing the tilde character which coerces the LateX renderer behind the **mathjax/ghfm** backend system to actually 
predictably spit out space characters and respect them (_so long as they are surrounded by **sentinal dots**._) It seems fitting somehow that then I'd paste some straightforward text into a fenced block designed to display it just right, and I'd end up getting properly typeset and renderer-as-math **nonsense** out of it. I had to work so hard for the _nonsense **I wanted**_.  That is clearly some sort of _ironic coincidence_.  


### I AM _IRONIC_ MAN

Anyway, as you see... **Phart is exploring New Media** to express itself through _Math, Science, and Visual Arts_!

We hope you'll join us again _for our next adventure_ through needless _**ASCII** Adventures_! 


\*\*You may notice that through the code and the supporting documentation I interchangeably swap in and out the words _"Rendering"_ and _"Representation". _
So which is it? I'm not sure, but I've been unsure and consistent about mixing it up unintentionally, just using whichever word comes to mind at
the time of writing. It's obviously less important now that the acronym, but it seem a gift when I asked myself "So, what should I call a [**Python Hierarchical ASCII [Representation|Rendering] Tool**](https://github.com/scottvr/phart), anyway?" and noticed the freebie acronym.


----
### Epilogue: _Latex Skidmarks_

And just for fun, if you scrolled _this far_,  Here's the text that creates that diagram with the _I-swear-they're=-there_ colors. For the sake of not making you read something ludicrous anad silly, I only reproduce the bottom row of nodes here; you can click to view the source of the page if you really gotta see it all:


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
