
In the middle of trying to update the README with a changelog to obtain a list of the new features that I would need to document, I discovered just how awful my git hygiene is. I'm not entirely alone in this, lots of folks are guilty of commit messages of the sort "fix bug" or "correct typo", and many of us have experienced scope creep of the sort where a file you had no intention of changing needs to be changed (say some ancillary infrastructure support file, like maybe a pyproject.toml, or a `.pre-commit-hook.yaml` has to be ad hoc edited in order that you might do the work you planned on.) These out-of-scsope small edits - and sometimes much larger, just unexpected files find their way into my commits, but I'll overlook them in my commit message, sometimes missing concerns under an overly-specific (or completely generic) commit message. It often seems less important than the _real work_ I'm trying to accomplish and I dismiss the bad habit with something like "well, anyone can look at the commit and see what files were included if it becomes of interest", knowing that's not a great justificaation.

Anyway, when I thought I could just create a changelog/release notes from the commits, and barring that, at least the diffs at each stage of the commit, just how awful my commit messagess and grouping of files has been, became more evident. `git log` and such were all but useless for reconstructing what I had added/changed/removed in terms of functionality. Additionally, there were tons of duplicate commits of the sort "Update README", whre I'd find a typo when looking at a repo in the browser on my phone and couldn't resist correcting it in the in-place editor of the github webui. Like a dozen within a few minutes at times; and because it commits directly to main, there's no staging files until you're completely done before pushing to the origin.

Anyway, I am happy to report I have a solution for this.

# The Changeling
**aka `cling`, the changeling cli**

I'm in the process of documenting it and how it works, but for the time being, I'll link you to its output. The tool is completely deterministic in reviewing, grouping, classifying commits. There is a well-documented set of rules that are used for such heuristics.
ANd while I did add an option to send very-explicitly deterministic results in structured JSON, template-driven and normalized to an LLM with a very specific prompt to only "enrich" the text that will be displayed for each commit in the output (*optionally*) and only
after cling has done all of its repeatabe, deterministic, no-creative-writing work on your repo's commit history. It occured to me that it is a good use case for smaller language model 
when presenting release notes, which have a different audience than a git commit message. But you don't have to use it; it does not run by default.

So here is the `cling` github-release style markdown, "enriched" by the LLM pas, and showing receipts. All evidence that was considered by the deterministic rule engine is on a linked separate markdown page, linking to the files, and the changes represented by the commit, right from the realease notes.

[RAW TEXT mode, which will be a combination of commit  messages and rule template text, depnding on if a short/weird/wrong/mismatched message was encountered or not.](https://github.com/scottvr/phart/blob/7521fa87f0dd076a375ec69e300c1a9ba7f8579d/docs/cling/cling.release-notes-raw.md)

and [here is one where the output is finessed by an LLM, but as I said, it has been implemented in a way to all but completely eliminate the risk of losing/changing meaning](https://github.com/scottvr/phart/blob/7521fa87f0dd076a375ec69e300c1a9ba7f8579d/docs/cling/cling.release-notes-enriched.md)
due to creativit inspiration or halllucination. And you don't hae to use it; I just show both ways for demonstration's sake.
